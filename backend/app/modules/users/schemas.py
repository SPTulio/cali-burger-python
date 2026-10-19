from datetime import date

from pydantic import BaseModel, ConfigDict

from app.core.validators import AddressLine, UtcDateTime
from app.modules.users.models import Role, Sex


class AddressIn(BaseModel):
    state: AddressLine
    city: AddressLine
    district: AddressLine
    street: AddressLine


class AddressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: str
    city: str
    district: str
    street: str


class UserOut(BaseModel):
    """Usuário da sessão (dados mínimos para a interface)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Role
    name: str
    first_name: str
    username: str | None
    email: str


class ProfileOut(UserOut):
    cpf: str
    birth_date: date
    sex: Sex | None
    address: AddressOut | None
    privacy_version: str | None
    privacy_accepted_at: UtcDateTime | None
