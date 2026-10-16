"""Dependências de autenticação/autorização usadas pelas rotas."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import Forbidden, Unauthorized
from app.core.security import tokens_match
from app.db.session import get_db
from app.modules.auth.models import AuthSession
from app.modules.auth.service import NewSession, resolve_session
from app.modules.users.models import Role, User

DbSession = Annotated[Session, Depends(get_db)]

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})


def client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


def get_optional_session(request: Request, db: DbSession) -> AuthSession | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    return resolve_session(db, token) if token else None


def get_current_session(
    request: Request,
    session: Annotated[AuthSession | None, Depends(get_optional_session)],
) -> AuthSession:
    if session is None:
        raise Unauthorized("Faça login para continuar.", code="not_authenticated")
    # CSRF: requisições que alteram dados precisam repetir o token no cabeçalho.
    # Um site externo não consegue ler o cookie para montar esse cabeçalho.
    if request.method not in SAFE_METHODS:
        header = request.headers.get("X-CSRF-Token", "")
        if not header or not tokens_match(header, session.csrf_hash):
            raise Forbidden(
                "Sua sessão expirou ou a requisição é inválida. Recarregue a página.",
                code="csrf_failed",
            )
    return session


CurrentSession = Annotated[AuthSession, Depends(get_current_session)]


def get_current_user(session: CurrentSession) -> User:
    return session.user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[[User], User]:
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise Forbidden("Você não tem permissão para esta ação.")
        return user

    return dependency


CustomerUser = Annotated[User, Depends(require_roles(Role.CUSTOMER))]
ManagerUser = Annotated[User, Depends(require_roles(Role.MANAGER))]
StaffUser = Annotated[User, Depends(require_roles(Role.MANAGER, Role.COOK))]
OptionalSession = Annotated[AuthSession | None, Depends(get_optional_session)]


# ---------------------------------------------------------------- cookies


def set_session_cookies(response: Response, new_session: NewSession) -> None:
    settings = get_settings()
    max_age = settings.session_max_days * 24 * 3600
    response.set_cookie(
        settings.session_cookie_name,
        new_session.token,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )
    # Legível pelo JavaScript do próprio site, que o reenvia no cabeçalho X-CSRF-Token.
    response.set_cookie(
        settings.csrf_cookie_name,
        new_session.csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookies(response: Response) -> None:
    settings = get_settings()
    for name in (settings.session_cookie_name, settings.csrf_cookie_name):
        response.delete_cookie(name, path="/", secure=settings.cookie_secure, samesite="lax")
