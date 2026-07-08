from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepgram_api_key: str = ""
    llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    tavily_api_key: str = ""

    chroma_persist_dir: str = "./data/chroma"
    upload_dir: str = "./data/uploads"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    static_dir: str = "./static"
    host: str = "0.0.0.0"
    port: int = 8000

    rag_similarity_threshold: float = 0.55
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-haiku-latest"
    embedding_model: str = "text-embedding-3-small"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def chroma_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def upload_path(self) -> Path:
        return Path(self.upload_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
