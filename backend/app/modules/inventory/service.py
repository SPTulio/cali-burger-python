"""Estoque de ingredientes."""

from sqlalchemy import Select, func, select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import InvalidInput, NotFound
from app.modules.catalog.models import RecipeItem
from app.modules.inventory.models import Ingredient
from app.modules.inventory.schemas import (
    IngredientAddIn,
    IngredientAddOut,
    IngredientOut,
    IngredientUpdateIn,
    StockLevel,
)


def stock_level(quantity: int, threshold: int | None = None) -> StockLevel:
    threshold = get_settings().low_stock_threshold if threshold is None else threshold
    if quantity <= 0:
        return StockLevel.OUT
    if quantity <= threshold:
        return StockLevel.LOW
    return StockLevel.OK


def _query_with_usage(search: str | None = None) -> Select[Ingredient, int]:
    used_in = (
        select(func.count())
        .where(RecipeItem.ingredient_id == Ingredient.id)
        .correlate(Ingredient)
        .scalar_subquery()
    )
    stmt = (
        select(Ingredient, used_in.label("used_in"))
        .order_by(Ingredient.name)
        .execution_options(populate_existing=True)
    )
    if search:
        stmt = stmt.where(Ingredient.name.contains(search, autoescape=True))
    return stmt


def _to_out(ingredient: Ingredient, used_in: int) -> IngredientOut:
    return IngredientOut(
        id=ingredient.id,
        name=ingredient.name,
        quantity=ingredient.quantity,
        used_in=used_in,
        level=stock_level(ingredient.quantity),
        updated_at=ingredient.updated_at,
    )


def list_ingredients(db: Session, search: str | None = None) -> list[IngredientOut]:
    return [_to_out(ing, used) for ing, used in db.execute(_query_with_usage(search)).all()]


def get_ingredient(db: Session, ingredient_id: int) -> IngredientOut:
    row = db.execute(_query_with_usage().where(Ingredient.id == ingredient_id)).first()
    if row is None:
        raise NotFound("Ingrediente não encontrado.")
    return _to_out(row[0], row[1])


def add_stock(db: Session, data: IngredientAddIn) -> IngredientAddOut:
    """Cria o ingrediente ou soma a quantidade em uma única instrução atômica
    (INSERT ... ON DUPLICATE KEY UPDATE), sem corrida entre duas entradas simultâneas."""
    existed = db.scalar(select(Ingredient.id).where(Ingredient.name == data.name))
    stmt = insert(Ingredient).values(name=data.name, quantity=data.quantity)
    stmt = stmt.on_duplicate_key_update(quantity=Ingredient.quantity + stmt.inserted.quantity)
    db.execute(stmt)
    db.commit()
    ingredient_id = db.scalar(select(Ingredient.id).where(Ingredient.name == data.name))
    if ingredient_id is None:  # pragma: no cover - acabou de ser gravado
        raise NotFound("Ingrediente não encontrado.")
    return IngredientAddOut(
        ingredient=get_ingredient(db, ingredient_id),
        created=existed is None,
        added=data.quantity,
    )


def update_ingredient(db: Session, ingredient_id: int, data: IngredientUpdateIn) -> IngredientOut:
    ingredient = db.get(Ingredient, ingredient_id, with_for_update=True)
    if ingredient is None:
        raise NotFound("Ingrediente não encontrado.")
    duplicate = db.scalar(
        select(Ingredient.id).where(Ingredient.name == data.name, Ingredient.id != ingredient_id)
    )
    if duplicate:
        raise InvalidInput(
            "Revise os campos destacados.",
            fields={"name": "Já existe outro ingrediente com esse nome."},
        )
    ingredient.name = data.name
    ingredient.quantity = data.quantity
    db.commit()
    return get_ingredient(db, ingredient_id)


def delete_ingredient(db: Session, ingredient_id: int) -> None:
    """Remove o ingrediente e, por CASCADE, as linhas de receita que o usavam."""
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise NotFound("Ingrediente não encontrado.")
    db.delete(ingredient)
    db.commit()
