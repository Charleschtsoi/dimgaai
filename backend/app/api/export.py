from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.session_store import session_store
from app.services.export import render_markdown, render_pdf_bytes

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/{session_id}")
async def export_meeting(session_id: str, format: str = "md"):
    ctx = session_store.get(session_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Session not found")

    markdown = render_markdown(ctx.state)
    if format == "pdf":
        try:
            pdf_bytes = render_pdf_bytes(markdown)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"PDF export failed: {exc}. Try format=md instead.",
            ) from exc
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="meeting-{session_id}.pdf"'
            },
        )

    return Response(
        content=markdown,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="meeting-{session_id}.md"'
        },
    )
