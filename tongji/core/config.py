from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    iam_username: str | None = None
    iam_password: str | None = None
    sessionid: str | None = None
    jsessionid: str | None = None
    session_store_path: Path = Path("./data/session.json")
    one_base_url: str = "https://1.tongji.edu.cn"
    request_timeout_seconds: float = Field(default=15, gt=0)
    login_expires_seconds: int = Field(default=600, gt=0)
    log_level: str = "INFO"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    # IMAP config for MFA auto-fetch (XiaLing233 alignment)
    imap_email: str | None = None
    imap_grantcode: str | None = None
    imap_server: str = "imap.qq.com"
    imap_port: int = 993

    model_config = SettingsConfigDict(
        env_prefix="TJ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def normalized_one_base_url(self) -> str:
        return self.one_base_url.rstrip("/")

    def require_iam_credentials(self) -> None:
        if not self.iam_username or not self.iam_password:
            raise RuntimeError(
                "TJ_IAM_USERNAME and TJ_IAM_PASSWORD are required for programmatic login"
            )

    @property
    def is_loopback_host(self) -> bool:
        return self.host.strip().lower() in {"127.0.0.1", "::1", "localhost"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
