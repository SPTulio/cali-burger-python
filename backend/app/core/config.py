"""Configuração da aplicação, lida de variáveis de ambiente (ou do arquivo .env)."""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = Field(
        description="URL SQLAlchemy do MySQL, ex.: mysql+pymysql://user:senha@localhost:3306/caliburger"
    )
    test_database_url: str | None = None
    db_echo: bool = False

    # Separados por vírgula. Vazio = API usada no mesmo domínio do frontend (proxy).
    cors_origins: str = ""

    session_cookie_name: str = "cb_session"
    csrf_cookie_name: str = "cb_csrf"
    cookie_secure: bool = False
    session_idle_hours: int = 12
    session_max_days: int = 7

    bcrypt_rounds: int = 12
    login_max_failures: int = 5
    login_window_seconds: int = 300
    login_lock_seconds: int = 300

    low_stock_threshold: int = 10
    timezone: str = "America/Sao_Paulo"

    media_dir: Path = BACKEND_DIR / "media"
    max_image_bytes: int = 2 * 1024 * 1024

    log_level: str = "INFO"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def menu_media_dir(self) -> Path:
        return self.media_dir / "menu"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # database_url vem do ambiente
