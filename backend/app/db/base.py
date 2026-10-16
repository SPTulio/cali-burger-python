from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from sqlalchemy import DateTime, Enum, MetaData, Numeric, func, text
from sqlalchemy.orm import DeclarativeBase, mapped_column

# Nomes previsíveis para constraints, para que as migrações sejam estáveis.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


Money = Annotated[Decimal, mapped_column(Numeric(10, 2))]
CreatedAt = Annotated[datetime, mapped_column(DateTime, server_default=func.now())]
# Atualizado pelo próprio MySQL, inclusive em UPDATEs feitos por expressão SQL.
UpdatedAt = Annotated[
    datetime,
    mapped_column(DateTime, server_default=text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
]


def str_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """ENUM do MySQL que guarda os valores (não os nomes) do StrEnum."""
    return Enum(
        enum_cls,
        name=name,
        values_callable=lambda e: [m.value for m in e],
        validate_strings=True,
    )
