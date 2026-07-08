from __future__ import annotations

import asyncio
import logging
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

FRAME_WEBM = 0x01
FRAME_PCM = 0x00

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


@lru_cache
def resolve_ffmpeg() -> str | None:
    found = shutil.which("ffmpeg")
    if found:
        return found
    for candidate in (
        _PROJECT_ROOT / ".tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
        _PROJECT_ROOT / ".tools" / "ffmpeg" / "bin" / "ffmpeg",
    ):
        if candidate.exists():
            return str(candidate)
    return None


def ffmpeg_available() -> bool:
    return resolve_ffmpeg() is not None


class WebmPcmDecoder:
    """Decode MediaRecorder webm/opus chunks to linear16 PCM at 16 kHz mono."""

    def __init__(self) -> None:
        self._init_segment: bytes | None = None
        self._pending = bytearray()
        self._warned_missing_ffmpeg = False

    async def feed(self, chunk: bytes) -> list[bytes]:
        if not chunk:
            return []
        if chunk[0] == FRAME_PCM:
            return [chunk[1:]]
        if chunk[0] != FRAME_WEBM:
            return [chunk]
        webm = chunk[1:]
        if not webm:
            return []
        if self._init_segment is None:
            self._init_segment = webm
        self._pending.extend(webm)
        if len(self._pending) < 2000:
            return []
        return await self._flush()

    async def flush(self) -> list[bytes]:
        if not self._pending:
            return []
        return await self._flush()

    async def _flush(self) -> list[bytes]:
        data = bytes(self._pending)
        self._pending.clear()
        if not data:
            return []
        if self._init_segment and not data.startswith(b"\x1a\x45\xdf\xa3"):
            data = self._init_segment + data
        pcm = await asyncio.to_thread(self._decode_webm, data)
        return [pcm] if pcm else []

    def _decode_webm(self, webm_data: bytes) -> bytes | None:
        ffmpeg = resolve_ffmpeg()
        if not ffmpeg:
            if not self._warned_missing_ffmpeg:
                self._warned_missing_ffmpeg = True
                logger.error(
                    "ffmpeg not found; cannot decode webm audio. "
                    "Run dimgaai go to download portable ffmpeg."
                )
            return None
        with tempfile.TemporaryDirectory() as tmp:
            inp = Path(tmp) / "chunk.webm"
            out = Path(tmp) / "chunk.pcm"
            inp.write_bytes(webm_data)
            cmd = [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(inp),
                "-f",
                "s16le",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                str(out),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=5)
                return out.read_bytes()
            except Exception:
                logger.debug("webm decode failed for chunk", exc_info=True)
                return None
