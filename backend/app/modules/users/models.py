from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import CHAR, Computed, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, UpdatedAt, str_enum


class Role(StrEnum):
    CUSTOMER = "customer"
    MANAGER = "manager"  # balconista / dono
    COOK = "cook"


STAFF_ROLES = frozenset({Role.MANAGER, Role.COOK})


class Sex(StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base):
    """Clientes e funcionários em uma única tabela.

    O CPF é único por tipo de conta: a mesma pessoa pode ser cliente e funcionária,
    mas não pode ter duas contas de cliente nem dois cadastros de funcionário.
    """

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("cpf", "account_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[Role] = mapped_column(str_enum(Role, "user_role"), index=True)
    account_type: Mapped[str] = mapped_column(
        String(8),
        Computed(
            "(case when `role` = 'customer' then 'customer' else 'staff' end)", persisted=True
        ),
    )
    username: Mapped[str | None] = mapped_column(String(30), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    cpf: Mapped[str] = mapped_column(CHAR(11))
    birth_date: Mapped[date] = mapped_column(Date)
    sex: Mapped[Sex | None] = mapped_column(str_enum(Sex, "user_sex"))
    password_hash: Mapped[str] = mapped_column(String(255))
    password_changed_at: Mapped[datetime | None]
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    address: Mapped["CustomerAddress | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF_ROLES

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name.strip() else self.name


class CustomerAddress(Base):
    """Endereço de entrega do cliente (um por cliente, como no sistema original)."""

    __tablename__ = "customer_addresses"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    state: Mapped[str] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(255))
    district: Mapped[str] = mapped_column(String(255))
    street: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[UpdatedAt]

    user: Mapped[User] = relationship(back_populates="address")

    def one_line(self) -> str:
        return f"{self.street}, {self.district}, {self.city} - {self.state}"
