from __future__ import annotations

from langchain_core.embeddings import Embeddings
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

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = ctx.resolve_google_key(settings)
        if not api_key:
            raise ValueError("Google API key is required")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=api_key,
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


def get_embeddings(ctx: SessionContext, settings: Settings | None = None) -> Embeddings:
    settings = settings or get_settings()
    provider = ctx.resolve_llm_provider(settings).lower()
    embed_provider = ctx.resolve_embedding_provider(settings)

    use_google = provider == "gemini" or (
        provider == "anthropic" and embed_provider == "google"
    )

    if use_google:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings

        api_key = ctx.resolve_google_key(settings)
        if not api_key:
            raise ValueError("Google API key is required for embeddings")
        return GoogleGenerativeAIEmbeddings(
            model=settings.gemini_embedding_model,
            google_api_key=api_key,
        )

    api_key = ctx.resolve_openai_key(settings)
    if not api_key:
        raise ValueError("OpenAI API key is required for embeddings")
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=api_key)
