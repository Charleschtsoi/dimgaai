from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.events import TranscriptSegment
from app.models.session_store import session_store
from app.services.claim_detector import ClaimDetector
from app.services.deepgram_stream import DeepgramStream
from app.services.question_gen import QuestionGenerator
from app.services.rag_factcheck import RAGFactChecker

logger = logging.getLogger(__name__)
router = APIRouter()

claim_detector = ClaimDetector()
fact_checker = RAGFactChecker()
question_gen = QuestionGenerator()


async def _send_json(ws: WebSocket, payload: dict[str, Any]) -> None:
    await ws.send_text(json.dumps(payload, ensure_ascii=False))


@router.websocket("/ws/meeting/{session_id}")
async def meeting_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()
    ctx = session_store.get_or_create(session_id)

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

    async def emit(payload: dict[str, Any]) -> None:
        await outbound.put(payload)

    async def on_transcript(segment: TranscriptSegment) -> None:
        await emit(
            {
                "type": "transcript",
                "speaker": segment.speaker,
                "text": segment.text,
                "is_final": segment.is_final,
                "timestamp_ms": segment.timestamp_ms,
            }
        )
        if segment.is_final:
            ctx.state.transcript.append(segment)
            asyncio.create_task(_process_final_segment(ctx, segment, emit))

    async def sender() -> None:
        while True:
            item = await outbound.get()
            if item is None:
                break
            await _send_json(websocket, item)

    sender_task = asyncio.create_task(sender())

    try:
        stream = DeepgramStream(deepgram_key, on_transcript)
        await stream.start()
        await emit({"type": "status", "message": "connected"})

        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            if "bytes" in message and message["bytes"]:
                await stream.send_audio(message["bytes"])
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
        if stream:
            await stream.finish()
        await outbound.put(None)
        await sender_task


async def _process_final_segment(ctx, segment: TranscriptSegment, emit) -> None:
    history = [s for s in ctx.state.transcript if s.is_final]

    async def run_questions(verdict=None):
        try:
            result = await question_gen.generate(ctx, segment, history, verdict)
            if result.questions:
                ctx.state.questions.append(result)
                await emit(
                    {
                        "type": "questions",
                        "segment": result.segment,
                        "questions": result.questions,
                    }
                )
        except Exception:
            logger.exception("Question generation failed for segment")

    try:
        claim = await claim_detector.detect(ctx, segment.text)
    except Exception:
        logger.exception("Claim detection failed")
        await run_questions()
        return

    if not claim.is_claim or not claim.claim_text:
        await run_questions()
        return

    try:
        verdict = await fact_checker.verify(ctx, claim.claim_text)
        ctx.state.verdicts.append(verdict)
        await emit(
            {
                "type": "verdict",
                "claim": verdict.claim,
                "verdict": verdict.verdict.value,
                "confidence": verdict.confidence,
                "rationale": verdict.rationale,
                "sources": [s.model_dump() for s in verdict.sources],
                "latency_ms": verdict.latency_ms,
                "used_web_search": verdict.used_web_search,
            }
        )
        await run_questions(verdict)
    except Exception:
        logger.exception("Fact check failed")
        await emit({"type": "error", "message": "事實核查失敗，請檢查 LLM API key。"})
        await run_questions()
