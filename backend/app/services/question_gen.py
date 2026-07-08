from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.events import QuestionResult, TranscriptSegment, VerdictResult
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model

logger = logging.getLogger(__name__)


class QuestionGenerator:
    async def generate(
        self,
        ctx: SessionContext,
        segment: TranscriptSegment,
        history: list[TranscriptSegment],
        verdict: VerdictResult | None = None,
    ) -> QuestionResult:
        recent = history[-3:]
        context_lines = [
            f"Speaker {s.speaker}: {s.text}" for s in recent if s.is_final
        ]
        verdict_line = ""
        if verdict:
            verdict_line = (
                f"\nFact-check: {verdict.verdict.value} — {verdict.rationale}"
            )

        system = """Generate 1-2 concise follow-up questions for a meeting assistant.
Write questions in Traditional Chinese (香港繁體).
Return ONLY JSON: {"questions": ["question1", "question2?"]}
Questions should clarify ambiguity, probe evidence, or deepen discussion."""

        user = (
            f"Recent transcript:\n"
            + "\n".join(context_lines)
            + f"\n\nCurrent segment (Speaker {segment.speaker}): {segment.text}"
            + verdict_line
        )

        try:
            llm = get_chat_model(ctx)
            response = await llm.ainvoke(
                [SystemMessage(content=system), HumanMessage(content=user)]
            )
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in content
                )
            parsed = self._parse_json(str(content))
            questions = [q for q in parsed.get("questions", []) if q][:2]
            return QuestionResult(segment=segment.text, questions=questions)
        except Exception:
            logger.exception("Question generation failed")
            return QuestionResult(segment=segment.text, questions=[])

    def _parse_json(self, text: str) -> dict:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        return json.loads(text)
