from __future__ import annotations

from dataclasses import dataclass, field

from app.config import Settings, get_settings
from app.models.events import MeetingState, SessionConfig


@dataclass
class SessionContext:
    session_id: str
    config: SessionConfig = field(default_factory=SessionConfig)
    state: MeetingState = field(default_factory=lambda: MeetingState(session_id=""))
    last_question_monotonic: float = 0.0
    glossary: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.state.session_id = self.session_id

    def resolve_deepgram_key(self, settings: Settings | None = None) -> str:
        settings = settings or get_settings()
        return self.config.deepgram_api_key or settings.deepgram_api_key

    def resolve_llm_provider(self, settings: Settings | None = None) -> str:
        settings = settings or get_settings()
        return self.config.llm_provider or settings.llm_provider

    def resolve_openai_key(self, settings: Settings | None = None) -> str:
        settings = settings or get_settings()
        return (
            self.config.openai_api_key
            or self.config.llm_api_key
            or settings.openai_api_key
        )

    def resolve_anthropic_key(self, settings: Settings | None = None) -> str:
        settings = settings or get_settings()
        return (
            self.config.anthropic_api_key
            or self.config.llm_api_key
            or settings.anthropic_api_key
        )

    def resolve_tavily_key(self, settings: Settings | None = None) -> str:
        settings = settings or get_settings()
        return self.config.tavily_api_key or settings.tavily_api_key


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionContext] = {}

    def get_or_create(self, session_id: str) -> SessionContext:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionContext(session_id=session_id)
        return self._sessions[session_id]

    def configure(self, session_id: str, config: SessionConfig) -> SessionContext:
        ctx = self.get_or_create(session_id)
        ctx.config = config
        return ctx

    def get(self, session_id: str) -> SessionContext | None:
        return self._sessions.get(session_id)


session_store = SessionStore()
