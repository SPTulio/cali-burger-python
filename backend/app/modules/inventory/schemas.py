from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.core.validators import Strip, UtcDateTime

IngredientName = Annotated[str, Strip, StringConstraints(min_length=1, max_length=50)]


class StockLevel(StrEnum):
    OK = "ok"
    LOW = "low"
    OUT = "out"


class IngredientAddIn(BaseModel):
    """Adiciona ao estoque. Se o ingrediente já existir (mesmo nome), a quantidade é somada."""

    name: IngredientName
    quantity: int = Field(ge=1, le=100_000)


class IngredientUpdateIn(BaseModel):
    name: IngredientName
    quantity: int = Field(ge=0, le=100_000)


class IngredientOut(BaseModel):
    id: int
    name: str
    quantity: int
    used_in: int = Field(description="Quantos itens do cardápio usam o ingrediente.")
    level: StockLevel
    updated_at: UtcDateTime


class IngredientAddOut(BaseModel):
    ingredient: IngredientOut
    created: bool
    added: int


class InventoryOut(BaseModel):
    items: list[IngredientOut]
    low_stock_threshold: int
