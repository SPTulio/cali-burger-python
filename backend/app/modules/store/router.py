from fastapi import APIRouter

from app.modules.auth.dependencies import DbSession, ManagerUser
from app.modules.store import service
from app.modules.store.schemas import HoursIn, PauseIn, StoreSettingsIn, StoreStatusOut

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
