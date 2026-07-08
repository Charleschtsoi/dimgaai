from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.events import ClaimResult
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You classify spoken meeting utterances for fact-checking.
Identify whether the utterance contains a factual claim that can be verified against reference documents.

Return ONLY valid JSON:
{"is_claim": true/false, "claim_text": "extracted claim or null"}

Rules:
- Factual claims: verifiable statements about numbers, dates, policies, events, statistics, definitions.
- NOT claims: greetings, opinions, questions, procedural talk, vague statements.
- Handle Cantonese (粵語), Traditional Chinese, and English code-mixing.
- If mixed languages, keep claim_text in the original wording.
- Extract the core verifiable claim when possible."""


class ClaimDetector:
    async def detect(self, ctx: SessionContext, text: str) -> ClaimResult:
        text = text.strip()
        if not text:
            return ClaimResult(is_claim=False)

        try:
            llm = get_chat_model(ctx)
            response = await llm.ainvoke(
                [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=f"Utterance:\n{text}"),
                ]
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            parsed = self._parse_json(str(content))
            return ClaimResult(
                is_claim=bool(parsed.get("is_claim")),
                claim_text=parsed.get("claim_text") if parsed.get("is_claim") else None,
            )
        except Exception:
            logger.exception("Claim detection failed")
            return ClaimResult(is_claim=False)

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return json.loads(text)
