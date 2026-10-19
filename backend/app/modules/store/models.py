from datetime import time

from sqlalchemy import Boolean, CheckConstraint, Integer, SmallInteger, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UpdatedAt


class StoreSettings(Base):
    """Configuração da loja (uma única linha, id = 1, criada pela migração)."""

    __tablename__ = "store_settings"
    __table_args__ = (CheckConstraint("prep_time_minutes > 0", name="prep_time_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_message: Mapped[str | None] = mapped_column(String(255))
    # Meta de preparo: base do tempo estimado e das cores do cronômetro da cozinha.
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=20)
    updated_at: Mapped[UpdatedAt]


class OpeningHour(Base):
    """Faixa de funcionamento em um dia da semana (0 = segunda … 6 = domingo), no fuso
    da loja. Se `closes_at` <= `opens_at`, a faixa termina no dia seguinte (ex.: 18h–2h)."""

    __tablename__ = "opening_hours"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("opens_at <> closes_at", name="non_empty"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    weekday: Mapped[int] = mapped_column(SmallInteger, index=True)
    opens_at: Mapped[time] = mapped_column(Time)
    closes_at: Mapped[time] = mapped_column(Time)
