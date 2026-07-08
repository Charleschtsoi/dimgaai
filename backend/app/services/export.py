from __future__ import annotations

from datetime import datetime, timezone

from app.models.events import MeetingState


def _format_duration(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    if minutes:
        return f"{minutes} 分 {secs} 秒"
    return f"{secs} 秒"


def render_markdown(state: MeetingState) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# 會議摘要 — {state.session_id}",
        "",
        f"**匯出時間:** {now}",
        f"**會議時長:** {_format_duration(state.duration_seconds)}",
        f"**參與人數:** {state.participant_count}",
        f"**核查陳述數:** {state.claims_checked}",
        f"**參考文件數:** {state.document_count}",
        "",
        "## 完整轉錄",
        "",
    ]

    for seg in state.transcript:
        if not seg.is_final:
            continue
        claim_mark = " [事實陳述]" if seg.is_factual_claim else ""
        lines.append(f"**Speaker {seg.speaker}:** {seg.text}{claim_mark}")
        if seg.raw_text and seg.raw_text != seg.text:
            lines.append(f"  _（原文：{seg.raw_text}）_")
        lines.append("")

    lines.extend(["## 事實核查", ""])
    if not state.verdicts:
        lines.append("_未偵測到可核實陳述。_")
    else:
        lines.append("| 陳述 | 判定 | 信心 | 來源 |")
        lines.append("| --- | --- | --- | --- |")
        for v in state.verdicts:
            source = (
                (v.source_quote or (v.sources[0].text[:80] + "..."))
                if v.sources or v.source_quote
                else "—"
            )
            lines.append(
                f"| {v.claim} | {v.verdict.value} | {v.confidence:.0%} | {source} |"
            )
        lines.append("")
        for v in state.verdicts:
            lines.append(f"### {v.claim}")
            lines.append(f"- **判定:** {v.verdict.value}")
            lines.append(f"- **說明:** {v.rationale}")
            if v.source_quote:
                lines.append(f"- **引用:** {v.source_quote}")
            elif v.sources:
                lines.append(f"- **來源:** {v.sources[0].text[:200]}")
            lines.append("")

    lines.extend(["## 追問問題", ""])
    if not state.questions:
        lines.append("_未生成問題。_")
    else:
        for q in state.questions:
            lines.append(f"**片段:** {q.segment}")
            for i, question in enumerate(q.questions, 1):
                lines.append(f"{i}. {question}")
            lines.append("")

    return "\n".join(lines)


def render_pdf_bytes(markdown_text: str) -> bytes:
    import markdown as md
    from weasyprint import HTML

    html_body = md.markdown(markdown_text, extensions=["tables"])
    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
body {{ font-family: "Noto Sans TC", sans-serif; margin: 2cm; font-size: 11pt; }}
h1,h2,h3 {{ color: #1a1a1a; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 6px; text-align: left; }}
</style></head><body>{html_body}</body></html>"""
    return HTML(string=html).write_pdf()
