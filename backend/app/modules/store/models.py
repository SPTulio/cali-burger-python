from datetime import time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Integer, Numeric, SmallInteger, String, Time, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Money, UpdatedAt


class StoreSettings(Base):
    """Configuração da loja (uma única linha, id = 1, criada pela migração)."""

    __tablename__ = "store_settings"
    __table_args__ = (CheckConstraint("prep_time_minutes > 0", name="prep_time_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    is_paused: Mapped[bool] = mapped_column(Boolean, default=False)
    pause_message: Mapped[str | None] = mapped_column(String(255))
    # Meta de preparo: base do tempo estimado e das cores do cronômetro da cozinha.
    prep_time_minutes: Mapped[int] = mapped_column(Integer, default=20)
    # Onde o cliente retira os pedidos "para retirada".
    pickup_address: Mapped[str | None] = mapped_column(String(255))
    # Entrega: tempo base de deslocamento, taxa para bairros fora da lista (None = não
    # atende) e valor a partir do qual a entrega é grátis (None = nunca).
    delivery_time_minutes: Mapped[int] = mapped_column(Integer, default=15, server_default="15")
    default_delivery_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    free_delivery_above: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
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


class DeliveryZone(Base):
    """Bairro atendido, com taxa e tempo extra de deslocamento. A comparação com o bairro
    do cliente ignora maiúsculas e acentos (collation utf8mb4_unicode_ci)."""

    __tablename__ = "delivery_zones"
    __table_args__ = (
        CheckConstraint("fee >= 0", name="fee_non_negative"),
        CheckConstraint("extra_minutes >= 0", name="extra_minutes_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    fee: Mapped[Money]
    extra_minutes: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
