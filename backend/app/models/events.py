from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class Verdict(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNCERTAIN = "UNCERTAIN"


class SessionConfig(BaseModel):
    deepgram_api_key: str | None = None
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    tavily_api_key: str | None = None

    def normalized(self) -> "SessionConfig":
        """Map llm_api_key to provider-specific fields."""
        data = self.model_copy()
        if data.llm_api_key:
            if data.llm_provider.lower() == "anthropic":
                data.anthropic_api_key = data.llm_api_key
            else:
                data.openai_api_key = data.llm_api_key
        return data


class TranscriptSegment(BaseModel):
    speaker: int = 0
    text: str
    is_final: bool = True
    timestamp_ms: int = 0


class ClaimResult(BaseModel):
    is_claim: bool
    claim_text: str | None = None


class SourcePassage(BaseModel):
    text: str
    filename: str = ""
    page: int | None = None
    score: float = 0.0


class VerdictResult(BaseModel):
    claim: str
    verdict: Verdict
    confidence: float = 0.0
    rationale: str = ""
    sources: list[SourcePassage] = Field(default_factory=list)
    latency_ms: int = 0
    used_web_search: bool = False


class QuestionResult(BaseModel):
    segment: str
    questions: list[str] = Field(default_factory=list)


class MeetingState(BaseModel):
    session_id: str
    transcript: list[TranscriptSegment] = Field(default_factory=list)
    verdicts: list[VerdictResult] = Field(default_factory=list)
    questions: list[QuestionResult] = Field(default_factory=list)
    document_count: int = 0

    def to_export_dict(self) -> dict[str, Any]:
        return self.model_dump()
