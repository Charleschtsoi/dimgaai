from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field


class Verdict(str, Enum):
    TRUE = "TRUE"
    FALSE = "FALSE"
    UNCERTAIN = "UNCERTAIN"


ClaimClassification = Literal["factual_claim", "non_claim"]


class SessionConfig(BaseModel):
    deepgram_api_key: str | None = None
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    tavily_api_key: str | None = None

    def normalized(self) -> "SessionConfig":
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
    raw_text: str = ""
    is_final: bool = True
    timestamp_ms: int = 0
    is_factual_claim: bool = False


class ClaimResult(BaseModel):
    classification: ClaimClassification = "non_claim"
    claim_text: str | None = None

    @property
    def is_claim(self) -> bool:
        return self.classification == "factual_claim"


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
    source_quote: str = ""
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
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def duration_seconds(self) -> int:
        if not self.started_at:
            return 0
        end = self.ended_at or datetime.now(self.started_at.tzinfo)
        return max(0, int((end - self.started_at).total_seconds()))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def participant_count(self) -> int:
        speakers = {s.speaker for s in self.transcript if s.is_final}
        return len(speakers)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def claims_checked(self) -> int:
        return len(self.verdicts)

    def to_export_dict(self) -> dict[str, Any]:
        return self.model_dump()
