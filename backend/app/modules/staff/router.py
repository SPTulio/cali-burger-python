from fastapi import APIRouter, Response, status

from app.modules.auth.dependencies import DbSession, ManagerUser, clear_session_cookies
from app.modules.staff import service
from app.modules.staff.schemas import StaffCreateIn, StaffOut

router = APIRouter(prefix="/staff", tags=["Equipe"])


@router.get("", response_model=list[StaffOut], summary="Listar balconistas e cozinheiros")
def list_staff(_: ManagerUser, db: DbSession) -> list[StaffOut]:
    return [StaffOut.model_validate(u) for u in service.list_staff(db)]


@router.post("", response_model=StaffOut, status_code=status.HTTP_201_CREATED, summary="Cadastrar")
def create_staff(data: StaffCreateIn, _: ManagerUser, db: DbSession) -> StaffOut:
    return StaffOut.model_validate(service.create_staff(db, data))


@router.delete(
    "/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir (não permite excluir o último balconista)",
)
def delete_staff(staff_id: int, manager: ManagerUser, db: DbSession) -> Response:
    manager_id = manager.id
    service.delete_staff(db, staff_id)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    if staff_id == manager_id:
        # Excluiu o próprio cadastro: a sessão já foi apagada junto (CASCADE).
        clear_session_cookies(response)
    return response
