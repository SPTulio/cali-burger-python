from fastapi import APIRouter, Response, status

from app.modules.accounts import service
from app.modules.accounts.schemas import AccountDeleteIn, PasswordChangeIn, ProfileUpdateIn
from app.modules.auth.dependencies import (
    CurrentSession,
    CurrentUser,
    CustomerUser,
    DbSession,
    clear_session_cookies,
)
from app.modules.users.schemas import AddressIn, AddressOut, ProfileOut

router = APIRouter(prefix="/me", tags=["Minha conta"])


@router.get("/profile", response_model=ProfileOut, summary="Meus dados")
def get_profile(user: CurrentUser) -> ProfileOut:
    return ProfileOut.model_validate(user)


@router.put("/profile", response_model=ProfileOut, summary="Editar meus dados")
def update_profile(data: ProfileUpdateIn, user: CurrentUser, db: DbSession) -> ProfileOut:
    return ProfileOut.model_validate(service.update_profile(db, user, data))


@router.put("/address", response_model=AddressOut, summary="Endereço de entrega")
def update_address(data: AddressIn, user: CustomerUser, db: DbSession) -> AddressOut:
    return AddressOut.model_validate(service.update_address(db, user, data))


@router.post(
    "/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trocar senha (encerra as outras sessões)",
)
def change_password(data: PasswordChangeIn, session: CurrentSession, db: DbSession) -> Response:
    service.change_password(db, session.user, session, data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir minha conta")
def delete_account(data: AccountDeleteIn, user: CurrentUser, db: DbSession) -> Response:
    service.delete_account(db, user, data.password)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookies(response)
    return response
