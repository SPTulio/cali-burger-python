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
from app.modules.users.schemas import AddressIn, UserOut


class LoginIn(BaseModel):
    identifier: str = Field(
        min_length=1,
        max_length=100,
        description="Usuário (clientes) ou CPF (funcionários).",
        examples=["joao", "352.658.110-01"],
    )
    password: str = Field(min_length=1, max_length=200)


class RegisterIn(BaseModel):
    username: Username
    password: Password
    password_confirmation: str
    name: PersonName
    email: Email
    cpf: Cpf
    birth_date: BirthDate
    address: AddressIn

    _check_confirmation = field_validator("password_confirmation")(confirmation_matches("password"))


class SessionOut(BaseModel):
    user: UserOut
