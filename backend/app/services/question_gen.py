from __future__ import annotations

import json
import logging
import re

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.events import QuestionResult, TranscriptSegment, VerdictResult
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一位香港會議助手。根據以下會議內容，提出 1-2 條跟進問題。"
    "用繁體中文回答。"
    "問題應針對：推理漏洞、未證實假設、缺失數據、矛盾之處。"
    "若提供事實核查結果，可針對不確定或錯誤之處追問。"
    'Return ONLY JSON: {"questions": ["問題一", "問題二"]}'
)


class QuestionGenerator:
    async def generate(
        self,
        ctx: SessionContext,
        segment: TranscriptSegment,
        history: list[TranscriptSegment],
        verdict: VerdictResult | None = None,
    ) -> QuestionResult:
        recent = history[-5:]
        context_lines = []
        for s in recent:
            if not s.is_final:
                continue
            line = f"Speaker {s.speaker}: {s.text}"
            if s.raw_text and s.raw_text != s.text:
                line += f" (ASR: {s.raw_text})"
            context_lines.append(line)
        verdict_line = ""
        if verdict:
            verdict_line = (
                f"\nFact-check ({verdict.verdict.value}, "
                f"confidence {verdict.confidence:.0%}): {verdict.rationale}"
            )
            if verdict.source_quote:
                verdict_line += f"\nSource: {verdict.source_quote}"

        user = (
            f"Recent transcript:\n"
            + "\n".join(context_lines)
            + f"\n\nCurrent segment (Speaker {segment.speaker}): {segment.text}"
            + (f"\nASR raw: {segment.raw_text}" if segment.raw_text else "")
            + verdict_line
        )

        try:
            llm = get_chat_model(ctx)
            response = await llm.ainvoke(
                [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user)]
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
