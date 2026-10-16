"""Dados do próprio usuário. O id sempre vem da sessão, nunca da requisição."""

from sqlalchemy.orm import Session

from app.core.errors import Forbidden, InvalidInput
from app.core.security import hash_password, verify_password
from app.core.time import utcnow
from app.modules.accounts.schemas import PasswordChangeIn, ProfileUpdateIn
from app.modules.auth.models import AuthSession
from app.modules.auth.service import ensure_customer_unique, revoke_user_sessions
from app.modules.staff.service import ensure_not_last_manager
from app.modules.users.models import CustomerAddress, Role, User
from app.modules.users.schemas import AddressIn


def update_profile(db: Session, user: User, data: ProfileUpdateIn) -> User:
    if user.role == Role.CUSTOMER:
        if data.username is None or data.cpf is None:
            missing = {
                f: "Campo obrigatório." for f in ("username", "cpf") if getattr(data, f) is None
            }
            raise InvalidInput("Revise os campos destacados.", fields=missing)
        ensure_customer_unique(db, username=data.username, cpf=data.cpf, exclude_user_id=user.id)
        user.username = data.username
        user.cpf = data.cpf
    else:
        if data.sex is None:
            raise InvalidInput("Revise os campos destacados.", fields={"sex": "Selecione o sexo."})
        user.sex = data.sex

    user.name = data.name
    user.email = data.email
    user.birth_date = data.birth_date
    db.commit()
    return user


def update_address(db: Session, user: User, data: AddressIn) -> CustomerAddress:
    if user.role != Role.CUSTOMER:
        raise Forbidden("Somente clientes têm endereço de entrega.")
    if user.address is None:
        user.address = CustomerAddress(**data.model_dump())
    else:
        for field, value in data.model_dump().items():
            setattr(user.address, field, value)
    db.commit()
    return user.address


def change_password(db: Session, user: User, session: AuthSession, data: PasswordChangeIn) -> None:
    if not verify_password(data.current_password, user.password_hash):
        raise InvalidInput(
            "A senha atual está incorreta.",
            fields={"current_password": "A senha atual está incorreta."},
        )
    user.password_hash = hash_password(data.new_password)
    user.password_changed_at = utcnow()
    # Quem souber a senha antiga perde o acesso em outros dispositivos.
    revoke_user_sessions(db, user.id, keep_session_id=session.id)
    db.commit()


def delete_account(db: Session, user: User, password: str) -> None:
    """Clientes e balconistas podem excluir a própria conta; cozinheiros não (como no original).
    Os pedidos do cliente continuam no histórico, com o nome gravado no pedido."""
    if user.role == Role.COOK:
        raise Forbidden("Peça a um balconista para remover seu cadastro.")
    if not verify_password(password, user.password_hash):
        raise InvalidInput("Senha incorreta.", fields={"password": "Senha incorreta."})
    if user.role == Role.MANAGER:
        ensure_not_last_manager(db)
    db.delete(user)
    db.commit()
