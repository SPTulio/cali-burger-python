from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.auth.dependencies import DbSession, ManagerUser, OptionalSession
from app.modules.orders.models import Fulfillment
from app.modules.store import delivery, service
from app.modules.store.schemas import (
    HoursIn,
    PauseIn,
    QuoteOut,
    StoreSettingsIn,
    StoreStatusOut,
    ZoneOut,
    ZonesIn,
)
from app.modules.users.models import Role

router = APIRouter(prefix="/store", tags=["Loja"])


@router.get("", response_model=StoreStatusOut, summary="Aberta ou fechada, horários e avisos")
def get_status(db: DbSession) -> StoreStatusOut:
    return service.get_status(db)


@router.put(
    "/hours", response_model=StoreStatusOut, summary="Substituir o horário de funcionamento"
)
def replace_hours(data: HoursIn, _: ManagerUser, db: DbSession) -> StoreStatusOut:
    return service.replace_hours(db, data.hours)


@router.put("/pause", response_model=StoreStatusOut, summary="Pausar ou retomar os pedidos")
def set_pause(data: PauseIn, _: ManagerUser, db: DbSession) -> StoreStatusOut:
    return service.set_pause(db, data)


@router.put("/settings", response_model=StoreStatusOut, summary="Configurações da loja")
def update_settings(data: StoreSettingsIn, _: ManagerUser, db: DbSession) -> StoreStatusOut:
    return service.update_settings(db, data)


@router.get(
    "/quote",
    response_model=QuoteOut,
    summary="Taxa de entrega e tempo estimado (usa o bairro do cliente logado)",
)
def get_quote(
    db: DbSession,
    session: OptionalSession,
    fulfillment: Fulfillment = Fulfillment.DELIVERY,
    subtotal: Annotated[Decimal, Query(ge=0, le=99999)] = Decimal("0"),
) -> QuoteOut:
    user = session.user if session else None
    district = (
        user.address.district
        if user and user.role == Role.CUSTOMER and user.address is not None
        else None
    )
    result = delivery.quote(db, fulfillment, district, subtotal)
    return delivery.to_quote_out(fulfillment, result, db)


@router.get("/zones", response_model=list[ZoneOut], summary="Bairros atendidos")
def list_zones(_: ManagerUser, db: DbSession) -> list[ZoneOut]:
    return delivery.list_zones(db)


@router.put("/zones", response_model=list[ZoneOut], summary="Substituir os bairros atendidos")
def replace_zones(data: ZonesIn, _: ManagerUser, db: DbSession) -> list[ZoneOut]:
    return delivery.replace_zones(db, data.zones)
