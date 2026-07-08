from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from deepgram import AsyncDeepgramClient
from deepgram.listen.v1.types.listen_v1results import ListenV1Results

from app.models.events import TranscriptSegment

logger = logging.getLogger(__name__)


class DeepgramStream:
    """Proxy audio to Deepgram live transcription (SDK v7 async API)."""

    def __init__(
        self,
        api_key: str,
        on_transcript: Callable[[TranscriptSegment], Awaitable[None]],
    ) -> None:
        self.api_key = api_key
        self.on_transcript = on_transcript
        self._client = AsyncDeepgramClient(api_key=api_key)
        self._audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._ready = asyncio.Event()
        self._stop = asyncio.Event()
        self._runner_task: asyncio.Task | None = None

    async def start(self) -> None:
        self._runner_task = asyncio.create_task(self._run())
        await asyncio.wait_for(self._ready.wait(), timeout=15)

    async def _run(self) -> None:
        try:
            async with self._client.listen.v1.connect(
                model="nova-2",
                language="zh-HK",
                diarize=True,
                punctuate=True,
                interim_results=True,
                smart_format=True,
                encoding="linear16",
                sample_rate=16000,
                channels=1,
            ) as connection:
                self._ready.set()
                receiver = asyncio.create_task(self._receive(connection))
                sender = asyncio.create_task(self._send_loop(connection))
                await self._stop.wait()
                await self._audio_queue.put(None)
                sender.cancel()
                receiver.cancel()
                await asyncio.gather(sender, receiver, return_exceptions=True)
                await connection.send_close_stream()
        except Exception:
            logger.exception("Deepgram stream failed")
            self._ready.set()

    async def _receive(self, connection) -> None:
        try:
            async for message in connection:
                if isinstance(message, ListenV1Results):
                    segment = self._parse_result(message)
                    if segment and segment.text.strip():
                        await self.on_transcript(segment)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Deepgram receive loop failed")

    async def _send_loop(self, connection) -> None:
        try:
            while True:
                chunk = await self._audio_queue.get()
                if chunk is None:
                    break
                await connection.send_media(chunk)
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception("Deepgram send loop failed")

    def _parse_result(self, result: ListenV1Results) -> TranscriptSegment | None:
        alternatives = result.channel.alternatives
        if not alternatives:
            return None

        alt = alternatives[0]
        text = (alt.transcript or "").strip()
        if not text:
            return None

        speaker = 0
        if alt.words:
            speakers = [w.speaker for w in alt.words if w.speaker is not None]
            if speakers:
                speaker = max(set(speakers), key=speakers.count)

        return TranscriptSegment(
            speaker=int(speaker),
            text=text,
            is_final=bool(result.is_final),
            timestamp_ms=int(result.start * 1000),
        )

    async def send_audio(self, chunk: bytes) -> None:
        if not self._stop.is_set():
            await self._audio_queue.put(chunk)

    async def finish(self) -> None:
        self._stop.set()
        if self._runner_task:
            await asyncio.gather(self._runner_task, return_exceptions=True)
