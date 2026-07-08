from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class SegmentBatcher:
    """Accumulate interim ASR text; flush on final or speaker change after silence."""

    silence_gap_ms: int = 1000
    _speaker: int = 0
    _parts: list[str] = field(default_factory=list)
    _last_update: float = field(default_factory=time.monotonic)

    def push(self, speaker: int, text: str, is_final: bool) -> str | None:
        text = text.strip()
        if not text:
            return None
        now = time.monotonic()
        gap_ms = (now - self._last_update) * 1000

        flushed: str | None = None
        if self._parts and (self._speaker != speaker or gap_ms > self.silence_gap_ms):
            flushed = self.flush()

        self._speaker = speaker
        if not self._parts or self._parts[-1] != text:
            self._parts.append(text)
        self._last_update = now

        if is_final:
            final_flush = self.flush()
            return final_flush or flushed
        return flushed

    def flush(self) -> str | None:
        if not self._parts:
            return None
        combined = " ".join(self._parts).strip()
        self._parts.clear()
        return combined or None
