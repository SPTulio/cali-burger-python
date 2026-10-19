from typing import Annotated

from fastapi import APIRouter, File, Query, Response, UploadFile, status

from app.core.config import get_settings
from app.modules.auth.dependencies import DbSession, ManagerUser, OptionalSession, StaffUser
from app.modules.catalog import service
from app.modules.catalog.schemas import CategoryOut, MenuItemIn, MenuItemOut, PauseItemIn

router = APIRouter(tags=["Cardápio"])


@router.get("/categories", response_model=list[CategoryOut], summary="Categorias")
def list_categories(db: DbSession) -> list[CategoryOut]:
    return [CategoryOut.model_validate(c) for c in service.list_categories(db)]


@router.get(
    "/menu-items",
    response_model=list[MenuItemOut],
    summary="Cardápio com disponibilidade (receitas apenas para funcionários)",
)
def list_menu_items(
    db: DbSession,
    session: OptionalSession,
    category_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[MenuItemOut]:
    is_staff = session is not None and session.user.is_staff
    return service.list_menu_items(db, category_id=category_id, include_recipe=is_staff)


@router.get("/menu-items/{item_id}", response_model=MenuItemOut, summary="Item com receita")
def get_menu_item(item_id: int, _: StaffUser, db: DbSession) -> MenuItemOut:
    return service.get_menu_item(db, item_id)


@router.post(
    "/menu-items",
    response_model=MenuItemOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar item com receita",
)
def create_menu_item(data: MenuItemIn, _: ManagerUser, db: DbSession) -> MenuItemOut:
    return service.create_menu_item(db, data)


@router.put("/menu-items/{item_id}", response_model=MenuItemOut, summary="Editar item")
def update_menu_item(item_id: int, data: MenuItemIn, _: ManagerUser, db: DbSession) -> MenuItemOut:
    return service.update_menu_item(db, item_id, data)


@router.delete(
    "/menu-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Excluir item"
)
def delete_menu_item(item_id: int, _: ManagerUser, db: DbSession) -> Response:
    service.delete_menu_item(db, item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put(
    "/menu-items/{item_id}/image",
    response_model=MenuItemOut,
    summary="Enviar/substituir imagem (PNG, JPG ou WebP, até 2 MB)",
)
def upload_image(
    item_id: int,
    _: ManagerUser,
    db: DbSession,
    image: Annotated[UploadFile, File(description="Arquivo de imagem")],
) -> MenuItemOut:
    # Lê no máximo o limite + 1 byte: arquivos maiores são recusados sem carregar tudo.
    content = image.file.read(get_settings().max_image_bytes + 1)
    return service.set_image(db, item_id, content)


@router.delete("/menu-items/{item_id}/image", response_model=MenuItemOut, summary="Remover imagem")
def remove_image(item_id: int, _: ManagerUser, db: DbSession) -> MenuItemOut:
    return service.remove_image(db, item_id)


@router.put(
    "/menu-items/{item_id}/pause",
    response_model=MenuItemOut,
    summary="Pausar ou reativar a venda do item (sem mexer no estoque)",
)
def set_paused(item_id: int, data: PauseItemIn, _: ManagerUser, db: DbSession) -> MenuItemOut:
    return service.set_paused(db, item_id, data.paused)
