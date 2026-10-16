"""Equipe: balconistas/donos e cozinheiros."""

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import BusinessRuleError, InvalidInput, NotFound
from app.core.security import hash_password
from app.modules.staff.schemas import StaffCreateIn
from app.modules.users.models import STAFF_ROLES, Role, User


def list_staff(db: Session) -> Sequence[User]:
    return db.scalars(
        select(User).where(User.role.in_(STAFF_ROLES)).order_by(User.role, User.name)
    ).all()


def create_staff(db: Session, data: StaffCreateIn) -> User:
    if db.scalar(select(User.id).where(User.cpf == data.cpf, User.role.in_(STAFF_ROLES))):
        raise InvalidInput(
            "Revise os campos destacados.",
            fields={"cpf": "Já existe um funcionário com este CPF."},
        )
    user = User(
        role=data.role,
        cpf=data.cpf,
        name=data.name,
        birth_date=data.birth_date,
        email=data.email,
        sex=data.sex,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise InvalidInput(
            "Revise os campos destacados.",
            fields={"cpf": "Já existe um funcionário com este CPF."},
        ) from exc
    return user


def ensure_not_last_manager(db: Session) -> None:
    """Trava os balconistas para que duas exclusões simultâneas não deixem o sistema sem
    nenhum (regra do sistema original)."""
    manager_ids = db.scalars(
        select(User.id).where(User.role == Role.MANAGER).with_for_update()
    ).all()
    if len(manager_ids) <= 1:
        raise BusinessRuleError(
            "Não é possível excluir o último balconista: o sistema ficaria sem ninguém "
            "para gerenciá-lo.",
            code="last_manager",
        )


def delete_staff(db: Session, staff_id: int) -> User:
    user = db.get(User, staff_id)
    if user is None or user.role not in STAFF_ROLES:
        raise NotFound("Funcionário não encontrado.")
    if user.role == Role.MANAGER:
        ensure_not_last_manager(db)
    db.delete(user)
    db.commit()
    return user


def count_managers(db: Session) -> int:
    return db.scalar(select(func.count()).where(User.role == Role.MANAGER)) or 0
