from pydantic import BaseModel, Field, field_validator

from app.core.validators import (
    BirthDate,
    Cpf,
    Email,
    Password,
    PersonName,
    Username,
    confirmation_matches,
)
from app.modules.users.models import Sex


class ProfileUpdateIn(BaseModel):
    """Dados pessoais. Clientes informam `username` e `cpf`; funcionários informam `sex`
    (o CPF do funcionário não é editável, como no sistema original)."""

    name: PersonName
    email: Email
    birth_date: BirthDate
    username: Username | None = None
    cpf: Cpf | None = None
    sex: Sex | None = None


class PasswordChangeIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: Password
    new_password_confirmation: str

    _check_confirmation = field_validator("new_password_confirmation")(
        confirmation_matches("new_password")
    )


class AccountDeleteIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)
