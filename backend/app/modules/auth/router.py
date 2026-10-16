from fastapi import APIRouter, Request, Response, status

from app.core.errors import Unauthorized
from app.modules.auth import service
from app.modules.auth.dependencies import (
    CurrentSession,
    DbSession,
    OptionalSession,
    clear_session_cookies,
    client_ip,
    set_session_cookies,
)
from app.modules.auth.schemas import LoginIn, RegisterIn, SessionOut
from app.modules.users.schemas import UserOut

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=SessionOut, summary="Entrar (cliente ou funcionário)")
def login(data: LoginIn, request: Request, response: Response, db: DbSession) -> SessionOut:
    ip = client_ip(request)
    user = service.authenticate(db, data.identifier, data.password, ip)
    new_session = service.create_session(db, user, ip, request.headers.get("user-agent"))
    db.commit()
    set_session_cookies(response, new_session)
    return SessionOut(user=UserOut.model_validate(user))


@router.post(
    "/register",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastro de cliente (já entra na conta)",
)
def register(data: RegisterIn, request: Request, response: Response, db: DbSession) -> SessionOut:
    user = service.register_customer(db, data)
    ip = client_ip(request)
    new_session = service.create_session(db, user, ip, request.headers.get("user-agent"))
    db.commit()
    set_session_cookies(response, new_session)
    return SessionOut(user=UserOut.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sair")
def logout(session: CurrentSession, response: Response, db: DbSession) -> Response:
    service.revoke_session(db, session)
    db.commit()
    clear_session_cookies(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=SessionOut, summary="Usuário da sessão atual")
def me(session: OptionalSession) -> SessionOut:
    if session is None:
        raise Unauthorized("Faça login para continuar.", code="not_authenticated")
    return SessionOut(user=UserOut.model_validate(session.user))
