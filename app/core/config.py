from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_token: str | None = None
    sessionid: str | None = None
    session_store_path: Path = Path("./data/session.json")
    one_base_url: str = "https://1.tongji.edu.cn"
    request_timeout_seconds: float = Field(default=15, gt=0)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="TJ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def normalized_one_base_url(self) -> str:
        return self.one_base_url.rstrip("/")

    def require_api_token(self) -> None:
        if not self.api_token:
            raise RuntimeError("TJ_API_TOKEN is required before starting one-dot-tongji-api")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()

