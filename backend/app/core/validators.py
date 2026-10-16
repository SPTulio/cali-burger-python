"""Validações de formato reutilizadas pelos schemas (CPF, usuário, senha, datas)."""

import re
from collections.abc import Callable
from datetime import UTC, date, datetime
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, EmailStr, StringConstraints, ValidationInfo

USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{3,30}$")
PASSWORD_MIN = 6
PASSWORD_MAX = 72  # limite do bcrypt


def only_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def is_valid_cpf(value: str) -> bool:
    cpf = only_digits(value)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    for size in (9, 10):
        total = sum(int(cpf[i]) * (size + 1 - i) for i in range(size))
        if int(cpf[size]) != (total * 10 % 11) % 10:
            return False
    return True


def looks_like_cpf(value: str) -> bool:
    """O identificador de login é um CPF (com ou sem pontuação)?"""
    return bool(re.fullmatch(r"[\d.\-\s]+", value)) and len(only_digits(value)) == 11


def _cpf(value: str) -> str:
    if not isinstance(value, str) or not is_valid_cpf(value):
        raise ValueError("CPF inválido.")
    return only_digits(value)


def _username(value: str) -> str:
    if not USERNAME_RE.fullmatch(value):
        raise ValueError("Use de 3 a 30 caracteres: letras, números, ponto, hífen ou sublinhado.")
    return value


def _password(value: str) -> str:
    if not PASSWORD_MIN <= len(value) <= PASSWORD_MAX:
        raise ValueError(f"A senha deve ter de {PASSWORD_MIN} a {PASSWORD_MAX} caracteres.")
    return value


def _birth_date(value: date) -> date:
    if not date(1900, 1, 1) <= value <= date.today():
        raise ValueError("Informe uma data de nascimento válida.")
    return value


def _max_255(value: str | None) -> str | None:
    if value is not None and len(value) > 255:
        raise ValueError("Use no máximo 255 caracteres.")
    return value


def _as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _blank_to_none(value: object) -> object:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


Strip = BeforeValidator(_strip)
BlankToNone = BeforeValidator(_blank_to_none)

Cpf = Annotated[str, AfterValidator(_cpf)]
Username = Annotated[str, Strip, AfterValidator(_username)]
Password = Annotated[str, AfterValidator(_password)]
BirthDate = Annotated[date, AfterValidator(_birth_date)]

# Datas gravadas em UTC sem fuso: na resposta saem com "Z" para o navegador converter.
UtcDateTime = Annotated[datetime, AfterValidator(_as_utc)]

# Textos obrigatórios (sem espaços nas pontas) e opcionais (vazio vira None).
PersonName = Annotated[str, Strip, StringConstraints(min_length=1, max_length=100)]
AddressLine = Annotated[str, Strip, StringConstraints(min_length=1, max_length=255)]
Email = Annotated[EmailStr, Strip, AfterValidator(_max_255)]
OptionalNote = Annotated[str | None, BlankToNone, AfterValidator(_max_255)]


def format_cpf(cpf: str) -> str:
    d = only_digits(cpf)
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}" if len(d) == 11 else cpf


def confirmation_matches(field: str) -> Callable[[type, str, ValidationInfo], str]:
    """Validador de campo de confirmação: o erro aparece no próprio campo de confirmação."""

    def check(_cls: type, value: str, info: ValidationInfo) -> str:
        if field in info.data and value != info.data[field]:
            raise ValueError("As senhas não coincidem.")
        return value

    return classmethod(check)  # type: ignore[return-value]
