from datetime import datetime

from sqlalchemy import CHAR, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt
from app.modules.users.models import User


class AuthSession(Base):
    """Sessão de login. Só o hash do token é guardado; o token fica no cookie HttpOnly."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(CHAR(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(CHAR(64))
    created_at: Mapped[CreatedAt]
    last_seen_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(255))

    user: Mapped[User] = relationship()


class LoginAttempt(Base):
    """Falhas de login por IP + identificador (o identificador não é guardado em claro)."""

    __tablename__ = "login_attempts"

    key_hash: Mapped[str] = mapped_column(CHAR(64), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    window_started_at: Mapped[datetime] = mapped_column(DateTime)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime)
