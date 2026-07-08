from __future__ import annotations

from datetime import datetime, timezone

from app.models.events import MeetingState


def render_markdown(state: MeetingState) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# 會議摘要 — {state.session_id}",
        "",
        f"**匯出時間:** {now}",
        f"**參考文件數:** {state.document_count}",
        "",
        "## 完整轉錄",
        "",
    ]

    for seg in state.transcript:
        if not seg.is_final:
            continue
        lines.append(f"**Speaker {seg.speaker}:** {seg.text}")
        lines.append("")

    lines.extend(["## 事實核查", ""])
    if not state.verdicts:
        lines.append("_未偵測到可核實陳述。_")
    else:
        lines.append("| 陳述 | 判定 | 信心 | 來源 |")
        lines.append("| --- | --- | --- | --- |")
        for v in state.verdicts:
            source = v.sources[0].text[:80] + "..." if v.sources else "—"
            lines.append(
                f"| {v.claim} | {v.verdict.value} | {v.confidence:.0%} | {source} |"
            )
        lines.append("")
        for v in state.verdicts:
            lines.append(f"### {v.claim}")
            lines.append(f"- **判定:** {v.verdict.value}")
            lines.append(f"- **說明:** {v.rationale}")
            if v.sources:
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
