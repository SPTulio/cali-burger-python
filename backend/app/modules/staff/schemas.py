from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.core.validators import (
    BirthDate,
    Cpf,
    Email,
    Password,
    PersonName,
    UtcDateTime,
    confirmation_matches,
)
from app.modules.users.models import Role, Sex


class StaffCreateIn(BaseModel):
    role: Literal[Role.MANAGER, Role.COOK]
    cpf: Cpf
    name: PersonName
    birth_date: BirthDate
    email: Email
    sex: Sex
    password: Password
    password_confirmation: str

    _check_confirmation = field_validator("password_confirmation")(confirmation_matches("password"))


class StaffOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: Role
    name: str
    cpf: str
    email: str
    birth_date: date
    sex: Sex | None
    created_at: UtcDateTime
