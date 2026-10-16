from sqlalchemy import CheckConstraint, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, Money, UpdatedAt
from app.modules.inventory.models import Ingredient


class Category(Base):
    """Dado de referência (Lanches, Acompanhamentos, Bebidas), criado pela migração."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    position: Mapped[int] = mapped_column(Integer, default=0)


class MenuItem(Base):
    __tablename__ = "menu_items"
    __table_args__ = (CheckConstraint("price > 0", name="price_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(String(255))
    price: Mapped[Money]
    image_path: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True
    )
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    category: Mapped[Category] = relationship()
    recipe: Mapped[list["RecipeItem"]] = relationship(
        back_populates="menu_item",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RecipeItem.ingredient_id",
    )


class RecipeItem(Base):
    """Quanto de cada ingrediente uma unidade do item consome."""

    __tablename__ = "recipe_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)

    menu_item: Mapped[MenuItem] = relationship(back_populates="recipe")
    ingredient: Mapped[Ingredient] = relationship()
