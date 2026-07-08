from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.events import TranscriptSegment
from app.models.session_store import session_store
from app.services.audio_decode import WebmPcmDecoder
from app.services.claim_detector import ClaimDetector
from app.services.deepgram_stream import DeepgramStream
from app.services.question_gen import QuestionGenerator
from app.services.rag_factcheck import RAGFactChecker
from app.services.transcript_normalize import TranscriptNormalizer
from app.ws.segment_batcher import SegmentBatcher

logger = logging.getLogger(__name__)
router = APIRouter()

claim_detector = ClaimDetector()
fact_checker = RAGFactChecker()
question_gen = QuestionGenerator()
normalizer = TranscriptNormalizer()

QUESTION_INTERVAL_MS = 30_000


async def _send_json(ws: WebSocket, payload: dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


@router.websocket("/ws/meeting/{session_id}")
async def meeting_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    ctx = session_store.get_or_create(session_id)
    ctx.state.started_at = datetime.now(timezone.utc)
    ctx.last_question_monotonic = time.monotonic()

    deepgram_key = ctx.resolve_deepgram_key()
    if not deepgram_key:
        await _send_json(
            websocket,
            {"type": "error", "message": "請設定 Deepgram API key（.env 或設定面板）"},
        )
        await websocket.close(code=1008)
        return

    outbound: asyncio.Queue[dict[str, Any] | None] = asyncio.Queue()
    stream: DeepgramStream | None = None
    decoder = WebmPcmDecoder()
    batcher = SegmentBatcher()

    async def emit(payload: dict[str, Any]) -> None:
        await outbound.put(payload)

    async def on_transcript(segment: TranscriptSegment) -> None:
        if not segment.is_final:
            await emit(
                {
                    "type": "transcript",
                    "speaker": segment.speaker,
                    "text": segment.text,
                    "raw_text": segment.text,
                    "is_final": False,
                    "timestamp_ms": segment.timestamp_ms,
                    "is_factual_claim": False,
                }
            )
            batcher.push(segment.speaker, segment.text, False)
            return

        flushed = batcher.push(segment.speaker, segment.text, True)
        utterance = flushed or segment.text.strip()
        if utterance:
            asyncio.create_task(_process_utterance(ctx, utterance, segment, emit))

    async def sender() -> None:
        while True:
            item = await outbound.get()
            if item is None:
                break
            await _send_json(websocket, item)

    sender_task = asyncio.create_task(sender())

    try:
        stream = DeepgramStream(deepgram_key, on_transcript, keywords=ctx.glossary)
        await stream.start()
        await emit({"type": "status", "message": "connected"})

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "bytes" in message and message["bytes"]:
                pcm_chunks = await decoder.feed(message["bytes"])
                for pcm in pcm_chunks:
                    await stream.send_audio(pcm)
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                except json.JSONDecodeError:
                    continue
                if data.get("type") == "stop":
                    break
    except WebSocketDisconnect:
        logger.info("Client disconnected: %s", session_id)
    except Exception:
        logger.exception("WebSocket session error")
        await emit({"type": "error", "message": "連線發生錯誤，請重試。"})
    finally:
        ctx.state.ended_at = datetime.now(timezone.utc)
        if stream:
            for pcm in await decoder.flush():
                await stream.send_audio(pcm)
            await stream.finish()
        await outbound.put(None)
        await sender_task


async def _process_utterance(
    ctx,
    raw_text: str,
    source_segment: TranscriptSegment,
    emit,
) -> None:
    history = [s for s in ctx.state.transcript if s.is_final]
    normalized = await normalizer.normalize(ctx, raw_text, history)
    segment = TranscriptSegment(
        speaker=source_segment.speaker,
        text=normalized,
        raw_text=raw_text,
        is_final=True,
        timestamp_ms=source_segment.timestamp_ms,
    )

    claim = None
    try:
        claim = await claim_detector.detect(
            ctx,
            normalized_text=segment.text,
            raw_text=segment.raw_text,
            history=history,
        )
    except Exception:
        logger.exception("Claim detection failed")

    if claim and claim.is_claim:
        segment.is_factual_claim = True
        await emit(
            {
                "type": "claim",
                "classification": claim.classification,
                "claim_text": claim.claim_text,
                "segment": segment.text,
            }
        )

    ctx.state.transcript.append(segment)
    await emit(
        {
            "type": "transcript",
            "speaker": segment.speaker,
            "text": segment.text,
            "raw_text": segment.raw_text,
            "is_final": True,
            "timestamp_ms": segment.timestamp_ms,
            "is_factual_claim": segment.is_factual_claim,
        }
    )

    history = [s for s in ctx.state.transcript if s.is_final]
    claim_detected = bool(claim and claim.is_claim and claim.claim_text)
    now = time.monotonic()
    should_question = claim_detected or (
        (now - ctx.last_question_monotonic) * 1000 >= QUESTION_INTERVAL_MS
    )

    verdict = None
    if claim_detected:
        await emit({"type": "status", "message": "checking"})
        try:
            verdict = await fact_checker.verify(ctx, claim.claim_text)  # type: ignore[union-attr]
            ctx.state.verdicts.append(verdict)
            await emit(
                {
                    "type": "verdict",
                    "claim": verdict.claim,
                    "verdict": verdict.verdict.value,
                    "confidence": verdict.confidence,
                    "rationale": verdict.rationale,
                    "source_quote": verdict.source_quote,
                    "sources": [s.model_dump() for s in verdict.sources],
                    "latency_ms": verdict.latency_ms,
                    "used_web_search": verdict.used_web_search,
                }
            )
        except Exception:
            logger.exception("Fact check failed")
            await emit({"type": "error", "message": "事實核查失敗，請檢查 LLM API key。"})

    if should_question:
        try:
            result = await question_gen.generate(ctx, segment, history, verdict=verdict)
            if result.questions:
                ctx.state.questions.append(result)
                ctx.last_question_monotonic = time.monotonic()
                await emit(
                    {
                        "type": "questions",
                        "segment": result.segment,
                        "questions": result.questions,
                    }
                )
        except Exception:
            logger.exception("Question generation failed")
