from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.events import TranscriptSegment
from app.models.session_store import SessionContext
from app.services.llm_provider import get_chat_model

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位香港會議轉錄校正員。
輸入係語音辨識（ASR）輸出嘅口語粵語，可能有：
- 同音錯字（例如「係/系」「佢/距」）
- 斷句錯誤、漏字
- 中英夾雜（code-mixing）

任務：
1. 根據上文語境，修正明顯 ASR 錯誤
2. 轉為清晰易讀嘅繁體中文書面語
3. 必須保留原意、數字、百分比、日期、專有名詞、英文縮寫
4. 若提供參考詞彙表，優先採用詞彙表寫法
5. 唔好憑空加內容，唔好改變講者立場

只輸出校正後文字，不要加解釋。"""


def _format_recent(history: list[TranscriptSegment], limit: int = 3) -> str:
    lines = [
        f"講者{s.speaker}: {s.text or s.raw_text}"
        for s in history[-limit:]
        if s.is_final and (s.text or s.raw_text)
    ]
    return "\n".join(lines) if lines else "（無）"


def _format_glossary(terms: list[str]) -> str:
    if not terms:
        return "（無）"
    return "、".join(terms[:30])


class TranscriptNormalizer:
    async def normalize(
        self,
        ctx: SessionContext,
        raw_text: str,
        history: list[TranscriptSegment] | None = None,
    ) -> str:
        text = raw_text.strip()
        if not text:
            return text
        history = history or []
        try:
            llm = get_chat_model(ctx)
            user = (
                f"參考詞彙：{_format_glossary(ctx.glossary)}\n"
                f"上文：\n{_format_recent(history)}\n\n"
                f"ASR原文：\n{text}"
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
            normalized = str(content).strip()
            return normalized or text
        except Exception:
            logger.exception("Transcript normalization failed")
            return text
