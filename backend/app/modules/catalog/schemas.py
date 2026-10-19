from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
)

from app.core.validators import OptionalNote, Strip


def _decimal_comma(value: object) -> object:
    """Aceita "22,90" além de "22.90" (como o formulário do sistema original)."""
    if isinstance(value, str):
        return value.strip().replace("R$", "").replace(" ", "").replace(",", ".")
    return value


ItemName = Annotated[str, Strip, StringConstraints(min_length=1, max_length=100)]
Price = Annotated[Decimal, BeforeValidator(_decimal_comma), Field(gt=0, le=9999, decimal_places=2)]


class Availability(StrEnum):
    AVAILABLE = "available"
    LOW = "low"  # "Últimas N"
    SOLD_OUT = "sold_out"
    PAUSED = "paused"  # tirado de venda pela loja, independente do estoque


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RecipeLineIn(BaseModel):
    ingredient_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=1000, description="Quanto uma unidade do item consome.")


class MenuItemIn(BaseModel):
    name: ItemName
    description: OptionalNote = None
    price: Price
    category_id: int = Field(ge=1)
    recipe: list[RecipeLineIn] = Field(default_factory=list, max_length=100)

    @field_validator("recipe")
    @classmethod
    def unique_ingredients(cls, value: list[RecipeLineIn]) -> list[RecipeLineIn]:
        ids = [line.ingredient_id for line in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada ingrediente pode aparecer só uma vez na receita.")
        return value


class RecipeLineOut(BaseModel):
    ingredient_id: int
    ingredient_name: str
    quantity: int
    in_stock: int


class MenuItemOut(BaseModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    image_url: str | None
    category: CategoryOut
    is_paused: bool
    portions: int | None = Field(
        description="Quantas unidades o estoque atual permite fazer (null = item sem receita)."
    )
    availability: Availability
    recipe: list[RecipeLineOut] | None = Field(
        default=None, description="Receita (somente para funcionários)."
    )


class PauseItemIn(BaseModel):
    paused: bool
