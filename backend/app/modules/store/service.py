"""Loja: horário de funcionamento, pausa de pedidos e configurações gerais."""

from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, InvalidInput
from app.core.time import local_now
from app.modules.store.models import OpeningHour, StoreSettings
from app.modules.store.rules import Interval, is_open, next_opening, overlaps
from app.modules.store.schemas import (
    HourIn,
    HourOut,
    PauseIn,
    StoreSettingsIn,
    StoreStatusOut,
)

WEEKDAYS = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


def get_settings_row(db: Session, *, lock: bool = False) -> StoreSettings:
    settings = db.get(StoreSettings, 1, with_for_update=lock)
    if settings is None:  # a migração cria a linha; isto só protege bancos montados à mão
        settings = StoreSettings(id=1, is_paused=False, prep_time_minutes=20)
        db.add(settings)
        db.flush()
    return settings


def _hours(db: Session) -> list[OpeningHour]:
    return list(db.scalars(select(OpeningHour).order_by(OpeningHour.weekday, OpeningHour.opens_at)))


def _when(opening: datetime, now: datetime) -> str:
    days = (opening.date() - now.date()).days
    hour = opening.strftime("%H:%M")
    if days == 0:
        return f"hoje às {hour}"
    if days == 1:
        return f"amanhã às {hour}"
    return f"{WEEKDAYS[opening.weekday()]} às {hour}"


def get_status(db: Session) -> StoreStatusOut:
    settings = get_settings_row(db)
    hours = _hours(db)
    intervals = [Interval(h.weekday, h.opens_at, h.closes_at) for h in hours]
    now = local_now()
    within = is_open(now, intervals)
    upcoming = None if within else next_opening(now, intervals)

    message = None
    if settings.is_paused:
        message = settings.pause_message or (
            "A loja pausou os pedidos por alguns instantes. Tente novamente em breve."
        )
    elif not within:
        message = (
            f"Estamos fechados agora. Abrimos {_when(upcoming, now)}."
            if upcoming
            else "Estamos fechados agora."
        )

    return StoreStatusOut(
        accepting_orders=within and not settings.is_paused,
        within_hours=within,
        is_paused=settings.is_paused,
        pause_message=settings.pause_message,
        message=message,
        next_opening_at=upcoming.astimezone(UTC) if upcoming else None,
        hours=[HourOut.model_validate(h) for h in hours],
        prep_time_minutes=settings.prep_time_minutes,
        pickup_address=settings.pickup_address,
    )


def ensure_accepting_orders(db: Session) -> None:
    status = get_status(db)
    if not status.accepting_orders:
        raise BusinessRuleError(
            status.message or "A loja não está aceitando pedidos agora.",
            code="store_paused" if status.is_paused else "store_closed",
        )


def replace_hours(db: Session, hours: list[HourIn]) -> StoreStatusOut:
    intervals = [Interval(h.weekday, h.opens_at, h.closes_at) for h in hours]
    if overlaps(intervals):
        raise InvalidInput(
            "Há faixas de horário sobrepostas no mesmo dia.",
            fields={"hours": "Há faixas de horário sobrepostas no mesmo dia."},
        )
    db.execute(delete(OpeningHour))
    db.add_all(
        OpeningHour(weekday=h.weekday, opens_at=h.opens_at, closes_at=h.closes_at) for h in hours
    )
    db.commit()
    return get_status(db)


def set_pause(db: Session, data: PauseIn) -> StoreStatusOut:
    settings = get_settings_row(db, lock=True)
    settings.is_paused = data.paused
    settings.pause_message = data.message if data.paused else None
    db.commit()
    return get_status(db)


def update_settings(db: Session, data: StoreSettingsIn) -> StoreStatusOut:
    settings = get_settings_row(db, lock=True)
    settings.prep_time_minutes = data.prep_time_minutes
    settings.pickup_address = data.pickup_address
    db.commit()
    return get_status(db)
