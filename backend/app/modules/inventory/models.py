from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, CreatedAt, UpdatedAt


class Ingredient(Base):
    __tablename__ = "ingredients"
    __table_args__ = (CheckConstraint("quantity >= 0", name="quantity_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]
