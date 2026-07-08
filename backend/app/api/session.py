from fastapi import APIRouter, HTTPException

from app.models.events import SessionConfig
from app.models.session_store import session_store

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/{session_id}/configure")
async def configure_session(session_id: str, config: SessionConfig):
    config = config.normalized()
    ctx = session_store.configure(session_id, config)

    missing = []
    if not ctx.resolve_deepgram_key():
        missing.append("deepgram_api_key")
    provider = ctx.resolve_llm_provider().lower()
    if provider == "anthropic" and not ctx.resolve_anthropic_key():
        missing.append("anthropic_api_key")
    elif provider == "gemini" and not ctx.resolve_google_key():
        missing.append("google_api_key")
    elif provider == "openai" and not ctx.resolve_openai_key():
        missing.append("openai_api_key")

    if provider == "anthropic":
        embed = ctx.resolve_embedding_provider().lower()
        if embed == "google" and not ctx.resolve_google_key():
            missing.append("google_api_key (embeddings)")
        elif embed == "openai" and not ctx.resolve_openai_key():
            missing.append("openai_api_key (embeddings)")

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required keys: {', '.join(missing)}",
        )

    return {"session_id": session_id, "configured": True}


@router.get("/{session_id}")
async def get_session(session_id: str):
    ctx = session_store.get(session_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Session not found")
    return ctx.state
