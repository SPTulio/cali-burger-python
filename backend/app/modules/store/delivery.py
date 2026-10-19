"""Entrega: taxa por bairro, frete grátis e tempo estimado do pedido."""

import math
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import InvalidInput
from app.core.time import utcnow
from app.modules.orders.models import Fulfillment, Order, OrderStatus, OrderStatusEvent
from app.modules.store.models import DeliveryZone, StoreSettings
from app.modules.store.schemas import QuoteOut, ZoneIn, ZoneOut
from app.modules.store.service import get_settings_row

ZERO = Decimal("0.00")
# A cozinha toca dois pedidos ao mesmo tempo; cada pedido além disso na fila soma minutos.
PARALLEL_ORDERS = 2
MINUTES_PER_QUEUED_ORDER = 3
ETA_WINDOW_MINUTES = 10
AVERAGE_WINDOW_DAYS = 14
MIN_SAMPLES = 5


# ---------------------------------------------------------------- regras puras


def fee_for(subtotal: Decimal, base_fee: Decimal, free_above: Decimal | None) -> Decimal:
    """Taxa cobrada: zero a partir do valor de frete grátis."""
    if free_above is not None and subtotal >= free_above:
        return ZERO
    return base_fee


def estimate_minutes(prep: float, queue_ahead: int, travel: int) -> tuple[int, int]:
    """Faixa de previsão em minutos, arredondada para múltiplos de 5."""
    queue = max(0, queue_ahead - PARALLEL_ORDERS + 1) * MINUTES_PER_QUEUED_ORDER
    low = math.ceil((prep + queue + travel) / 5) * 5
    return low, low + ETA_WINDOW_MINUTES


def normalize(name: str) -> str:
    """Nome de bairro para comparar: sem acentos, maiúsculas nem espaços extras."""
    decomposed = unicodedata.normalize("NFKD", name)
    return " ".join(
        "".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split()
    )


# ---------------------------------------------------------------- consultas


def average_prep_minutes(db: Session) -> float | None:
    """Tempo médio entre o aceite e o "pronto" nos últimos dias (None sem amostras)."""
    since = utcnow() - timedelta(days=AVERAGE_WINDOW_DAYS)
    rows = db.execute(
        select(
            OrderStatusEvent.order_id, OrderStatusEvent.to_status, OrderStatusEvent.created_at
        ).where(
            OrderStatusEvent.to_status.in_([OrderStatus.IN_PREPARATION, OrderStatus.READY]),
            OrderStatusEvent.created_at >= since,
        )
    ).all()
    started: dict[int, datetime] = {}
    finished: dict[int, datetime] = {}
    for order_id, status, created_at in rows:
        (started if status == OrderStatus.IN_PREPARATION else finished)[order_id] = created_at
    durations = [(finished[o] - started[o]).total_seconds() / 60 for o in finished if o in started]
    durations = [d for d in durations if d > 0]
    if len(durations) < MIN_SAMPLES:
        return None
    return min(120.0, max(5.0, sum(durations) / len(durations)))


def _queue_ahead(db: Session) -> int:
    return (
        db.scalar(
            select(func.count()).where(
                Order.status.in_([OrderStatus.AWAITING_ACCEPTANCE, OrderStatus.IN_PREPARATION])
            )
        )
        or 0
    )


def find_zone(db: Session, district: str) -> DeliveryZone | None:
    wanted = normalize(district)
    for zone in db.scalars(select(DeliveryZone).where(DeliveryZone.is_active)):
        if normalize(zone.name) == wanted:
            return zone
    return None


@dataclass(frozen=True)
class DeliveryQuote:
    served: bool
    fee: Decimal | None
    zone: DeliveryZone | None
    eta_min: int
    eta_max: int
    message: str | None


def quote(
    db: Session,
    fulfillment: Fulfillment,
    district: str | None,
    subtotal: Decimal,
) -> DeliveryQuote:
    settings: StoreSettings = get_settings_row(db)
    prep = average_prep_minutes(db) or float(settings.prep_time_minutes)
    ahead = _queue_ahead(db)

    if fulfillment == Fulfillment.PICKUP:
        low, high = estimate_minutes(prep, ahead, 0)
        return DeliveryQuote(True, ZERO, None, low, high, None)

    has_zones = db.scalar(select(func.count()).select_from(DeliveryZone)) or 0
    zone = find_zone(db, district) if district else None
    travel = settings.delivery_time_minutes + (zone.extra_minutes if zone else 0)
    low, high = estimate_minutes(prep, ahead, travel)

    if not has_zones and settings.default_delivery_fee is None:
        base: Decimal | None = ZERO  # sem configuração: entrega grátis em qualquer bairro
    elif zone is not None:
        base = zone.fee
    else:
        base = settings.default_delivery_fee

    if district is None:  # visitante: ainda não sabemos o bairro
        return DeliveryQuote(True, None, None, low, high, None)
    if base is None:
        return DeliveryQuote(
            False, None, None, low, high, f"Ainda não entregamos no bairro {district}."
        )
    return DeliveryQuote(
        True, fee_for(subtotal, base, settings.free_delivery_above), zone, low, high, None
    )


def to_quote_out(fulfillment: Fulfillment, result: DeliveryQuote, db: Session) -> QuoteOut:
    settings = get_settings_row(db)
    return QuoteOut(
        fulfillment=fulfillment,
        served=result.served,
        message=result.message,
        zone_name=result.zone.name if result.zone else None,
        delivery_fee=result.fee,
        free_delivery_above=settings.free_delivery_above,
        eta_min_minutes=result.eta_min,
        eta_max_minutes=result.eta_max,
    )


# ---------------------------------------------------------------- bairros (gestão)


def list_zones(db: Session) -> list[ZoneOut]:
    return [
        ZoneOut.model_validate(z)
        for z in db.scalars(select(DeliveryZone).order_by(DeliveryZone.name))
    ]


def replace_zones(db: Session, zones: list[ZoneIn]) -> list[ZoneOut]:
    names = [normalize(z.name) for z in zones]
    if len(names) != len(set(names)):
        raise InvalidInput(
            "Há bairros repetidos na lista.", fields={"zones": "Há bairros repetidos na lista."}
        )
    db.execute(delete(DeliveryZone))
    db.flush()
    db.add_all(
        DeliveryZone(name=z.name, fee=z.fee, extra_minutes=z.extra_minutes, is_active=z.is_active)
        for z in zones
    )
    db.commit()
    return list_zones(db)
