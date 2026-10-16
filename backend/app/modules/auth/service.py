"""Autenticação: login, cadastro de clientes, sessões e limite de tentativas."""

import hashlib
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import InvalidInput, RateLimited, Unauthorized
from app.core.security import (
    hash_password,
    hash_token,
    new_token,
    password_needs_rehash,
    verify_password,
)
from app.core.time import utcnow
from app.core.validators import looks_like_cpf, only_digits
from app.modules.auth.models import AuthSession, LoginAttempt
from app.modules.auth.schemas import RegisterIn
from app.modules.users.models import STAFF_ROLES, CustomerAddress, Role, User

INVALID_CREDENTIALS = "Usuário/CPF ou senha inválidos."
TOO_MANY_ATTEMPTS = "Muitas tentativas de login. Aguarde alguns minutos e tente novamente."


@dataclass(frozen=True)
class NewSession:
    token: str
    csrf_token: str
    session: AuthSession


# ---------------------------------------------------------------- login


def find_user_for_login(db: Session, identifier: str) -> User | None:
    """Clientes entram pelo usuário; funcionários pelo CPF (como no sistema original)."""
    identifier = identifier.strip()
    if looks_like_cpf(identifier):
        return db.scalar(
            select(User).where(User.cpf == only_digits(identifier), User.role.in_(STAFF_ROLES))
        )
    return db.scalar(select(User).where(User.username == identifier, User.role == Role.CUSTOMER))


def authenticate(db: Session, identifier: str, password: str, ip: str | None) -> User:
    key = _attempt_key(ip, identifier)
    _ensure_not_locked(db, key)

    user = find_user_for_login(db, identifier)
    # verify_password roda o bcrypt mesmo sem usuário: o tempo não revela se a conta existe.
    if not verify_password(password, user.password_hash if user else None) or user is None:
        _register_failure(db, key)
        db.commit()
        raise Unauthorized(INVALID_CREDENTIALS, code="invalid_credentials")

    db.execute(delete(LoginAttempt).where(LoginAttempt.key_hash == key))
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    return user


def _attempt_key(ip: str | None, identifier: str) -> str:
    raw = f"{ip or '-'}|{identifier.strip().lower()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _ensure_not_locked(db: Session, key: str) -> None:
    attempt = db.get(LoginAttempt, key)
    now = utcnow()
    if attempt and attempt.locked_until and attempt.locked_until > now:
        retry_after = int((attempt.locked_until - now).total_seconds()) + 1
        raise RateLimited(TOO_MANY_ATTEMPTS, retry_after=retry_after)


def _register_failure(db: Session, key: str) -> None:
    settings = get_settings()
    now = utcnow()
    attempt = db.get(LoginAttempt, key, with_for_update=True)
    if attempt is None:
        attempt = LoginAttempt(key_hash=key, failures=0, window_started_at=now)
        db.add(attempt)
    elif now - attempt.window_started_at > timedelta(seconds=settings.login_window_seconds):
        attempt.failures = 0
        attempt.window_started_at = now
        attempt.locked_until = None
    attempt.failures += 1
    if attempt.failures >= settings.login_max_failures:
        attempt.locked_until = now + timedelta(seconds=settings.login_lock_seconds)
    try:
        db.flush()
    except IntegrityError:
        # Outra requisição criou o registro ao mesmo tempo; a falha dela já conta.
        db.rollback()


# ---------------------------------------------------------------- sessões


def create_session(db: Session, user: User, ip: str | None, user_agent: str | None) -> NewSession:
    settings = get_settings()
    now = utcnow()
    token, csrf_token = new_token(), new_token()
    session = AuthSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_hash=hash_token(csrf_token),
        last_seen_at=now,
        expires_at=now + timedelta(hours=settings.session_idle_hours),
        ip_address=ip,
        user_agent=(user_agent or "")[:255] or None,
    )
    db.add(session)
    # Aproveita o login para limpar sessões vencidas.
    db.execute(delete(AuthSession).where(AuthSession.expires_at < now))
    db.flush()
    return NewSession(token=token, csrf_token=csrf_token, session=session)


def resolve_session(db: Session, token: str) -> AuthSession | None:
    """Sessão válida para o token do cookie, renovando a expiração por inatividade."""
    session = db.scalar(
        select(AuthSession)
        .options(joinedload(AuthSession.user).joinedload(User.address))
        .where(AuthSession.token_hash == hash_token(token))
    )
    now = utcnow()
    if session is None or session.expires_at <= now:
        return None

    settings = get_settings()
    # Grava no máximo uma vez por minuto, para não escrever no banco a cada requisição.
    if now - session.last_seen_at >= timedelta(minutes=1):
        hard_limit = session.created_at + timedelta(days=settings.session_max_days)
        session.last_seen_at = now
        session.expires_at = min(now + timedelta(hours=settings.session_idle_hours), hard_limit)
        db.commit()
    return session


def revoke_session(db: Session, session: AuthSession) -> None:
    db.execute(delete(AuthSession).where(AuthSession.id == session.id))


def revoke_user_sessions(db: Session, user_id: int, *, keep_session_id: int | None = None) -> None:
    stmt = delete(AuthSession).where(AuthSession.user_id == user_id)
    if keep_session_id is not None:
        stmt = stmt.where(AuthSession.id != keep_session_id)
    db.execute(stmt)


# ---------------------------------------------------------------- cadastro


def register_customer(db: Session, data: RegisterIn) -> User:
    ensure_customer_unique(db, username=data.username, cpf=data.cpf)
    user = User(
        role=Role.CUSTOMER,
        username=data.username,
        name=data.name,
        email=data.email,
        cpf=data.cpf,
        birth_date=data.birth_date,
        password_hash=hash_password(data.password),
        address=CustomerAddress(**data.address.model_dump()),
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise InvalidInput("Usuário ou CPF já cadastrado.") from exc
    return user


def ensure_customer_unique(
    db: Session, *, username: str, cpf: str, exclude_user_id: int | None = None
) -> None:
    fields: dict[str, str] = {}
    base = select(User.id).where(User.role == Role.CUSTOMER)
    if exclude_user_id is not None:
        base = base.where(User.id != exclude_user_id)
    if db.scalar(base.where(User.username == username)):
        fields["username"] = "Este usuário já está em uso."
    if db.scalar(base.where(User.cpf == cpf)):
        fields["cpf"] = "Já existe uma conta de cliente com este CPF."
    if fields:
        raise InvalidInput("Revise os campos destacados.", fields=fields)
