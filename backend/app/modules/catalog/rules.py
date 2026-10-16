"""Regras puras do cardápio (sem banco), testadas isoladamente."""

from collections.abc import Iterable

from app.modules.catalog.schemas import Availability

# Até quantas porções o item aparece como "Últimas N" (sistema original).
LOW_PORTIONS = 5


def portions_available(recipe: Iterable[tuple[int, int]]) -> int | None:
    """Quantas unidades o estoque permite fazer. `recipe` = [(em estoque, usado por unidade)].
    Item sem receita não depende do estoque (None)."""
    lines = list(recipe)
    if not lines:
        return None
    return min(stock // used for stock, used in lines)


def availability(portions: int | None) -> Availability:
    if portions is None:
        return Availability.AVAILABLE
    if portions <= 0:
        return Availability.SOLD_OUT
    if portions <= LOW_PORTIONS:
        return Availability.LOW
    return Availability.AVAILABLE
