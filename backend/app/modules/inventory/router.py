from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.core.config import get_settings
from app.modules.auth.dependencies import DbSession, ManagerUser
from app.modules.inventory import service
from app.modules.inventory.schemas import (
    IngredientAddIn,
    IngredientAddOut,
    IngredientOut,
    IngredientUpdateIn,
    InventoryOut,
)

router = APIRouter(prefix="/ingredients", tags=["Estoque"])


@router.get("", response_model=InventoryOut, summary="Listar ingredientes")
def list_ingredients(
    _: ManagerUser,
    db: DbSession,
    q: Annotated[str | None, Query(max_length=50, description="Busca pelo nome")] = None,
) -> InventoryOut:
    return InventoryOut(
        items=service.list_ingredients(db, q.strip() if q else None),
        low_stock_threshold=get_settings().low_stock_threshold,
    )


@router.post(
    "",
    response_model=IngredientAddOut,
    summary="Adicionar ao estoque (soma se o ingrediente já existir)",
)
def add_stock(data: IngredientAddIn, _: ManagerUser, db: DbSession) -> IngredientAddOut:
    return service.add_stock(db, data)


@router.put("/{ingredient_id}", response_model=IngredientOut, summary="Editar ingrediente")
def update_ingredient(
    ingredient_id: int, data: IngredientUpdateIn, _: ManagerUser, db: DbSession
) -> IngredientOut:
    return service.update_ingredient(db, ingredient_id, data)


@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir ingrediente (é retirado das receitas)",
)
def delete_ingredient(ingredient_id: int, _: ManagerUser, db: DbSession) -> Response:
    service.delete_ingredient(db, ingredient_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
