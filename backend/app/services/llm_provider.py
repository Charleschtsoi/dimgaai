from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.config import Settings, get_settings
from app.models.session_store import SessionContext


def get_chat_model(ctx: SessionContext, settings: Settings | None = None) -> BaseChatModel:
    settings = settings or get_settings()
    provider = ctx.resolve_llm_provider(settings).lower()

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = ctx.resolve_anthropic_key(settings)
        if not api_key:
            raise ValueError("Anthropic API key is required")
        return ChatAnthropic(
            model=settings.anthropic_model,
            api_key=api_key,
            temperature=0,
        )

    api_key = ctx.resolve_openai_key(settings)
    if not api_key:
        raise ValueError("OpenAI API key is required")
    return ChatOpenAI(
        model=settings.openai_model,
        api_key=api_key,
        temperature=0,
    )


def get_embeddings(ctx: SessionContext, settings: Settings | None = None) -> OpenAIEmbeddings:
    settings = settings or get_settings()
    api_key = ctx.resolve_openai_key(settings)
    if not api_key:
        raise ValueError("OpenAI API key is required for embeddings")
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=api_key)
