from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.events import ClaimResult, TranscriptSegment
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You classify spoken meeting utterances for fact-checking.
Identify whether the utterance contains a factual claim that can be verified against reference documents.

Return ONLY valid JSON:
{"classification": "factual_claim" or "non_claim", "claim_text": "extracted claim or null"}

Rules:
- factual_claim: verifiable statements about numbers, dates, policies, events, statistics, definitions.
- non_claim: greetings, opinions, questions, procedural talk, vague statements.
- Handle Cantonese (粵語), Traditional Chinese, and English code-mixing (e.g. "GDP growth 係 3.5%").
- You receive both ASR raw text and a corrected transcript. Prefer corrected text; use raw text to recover numbers/names if correction looks wrong.
- Use recent conversation context to resolve pronouns and incomplete sentences.
- If mixed languages, keep claim_text in the original wording.
- Extract the core verifiable claim when possible."""


def _format_recent(history: list[TranscriptSegment], limit: int = 3) -> str:
    lines = [
        f"Speaker {s.speaker}: {s.text or s.raw_text}"
        for s in history[-limit:]
        if s.is_final and (s.text or s.raw_text)
    ]
    return "\n".join(lines) if lines else "(none)"


class ClaimDetector:
    async def detect(
        self,
        ctx: SessionContext,
        normalized_text: str,
        raw_text: str = "",
        history: list[TranscriptSegment] | None = None,
    ) -> ClaimResult:
        normalized_text = normalized_text.strip()
        raw_text = (raw_text or normalized_text).strip()
        if not normalized_text and not raw_text:
            return ClaimResult(classification="non_claim")
        history = history or []

        try:
            llm = get_chat_model(ctx)
            user = (
                f"Recent context:\n{_format_recent(history)}\n\n"
                f"ASR raw:\n{raw_text}\n\n"
                f"Corrected transcript:\n{normalized_text}"
            )
            response = await llm.ainvoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=user),
                ]
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            parsed = self._parse_json(str(content))
            classification = parsed.get("classification", "non_claim")
            if classification not in ("factual_claim", "non_claim"):
                classification = (
                    "factual_claim" if parsed.get("is_claim") else "non_claim"
                )
            claim_text = parsed.get("claim_text")
            if classification != "factual_claim":
                claim_text = None
            return ClaimResult(classification=classification, claim_text=claim_text)
        except Exception:
            logger.exception("Claim detection failed")
            return ClaimResult(classification="non_claim")

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return json.loads(text)
