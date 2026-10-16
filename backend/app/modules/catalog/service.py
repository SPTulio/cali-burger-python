"""Cardápio: categorias, itens, receitas, disponibilidade e imagens."""

from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.core.errors import InvalidInput, NotFound
from app.modules.catalog import images
from app.modules.catalog.models import Category, MenuItem, RecipeItem
from app.modules.catalog.rules import availability, portions_available
from app.modules.catalog.schemas import CategoryOut, MenuItemIn, MenuItemOut, RecipeLineOut
from app.modules.inventory.models import Ingredient


def list_categories(db: Session) -> Sequence[Category]:
    return db.scalars(select(Category).order_by(Category.position, Category.id)).all()


def _base_query() -> Select[MenuItem]:
    # 3 consultas no total (itens+categoria, receitas, ingredientes), sem N+1.
    return (
        select(MenuItem)
        .join(MenuItem.category)
        .options(
            contains_eager(MenuItem.category),
            selectinload(MenuItem.recipe).joinedload(RecipeItem.ingredient),
        )
        .execution_options(populate_existing=True)
    )


def to_out(item: MenuItem, *, include_recipe: bool) -> MenuItemOut:
    portions = portions_available((line.ingredient.quantity, line.quantity) for line in item.recipe)
    return MenuItemOut(
        id=item.id,
        name=item.name,
        description=item.description,
        price=item.price,
        image_url=images.media_url(item.image_path),
        category=CategoryOut.model_validate(item.category),
        portions=portions,
        availability=availability(portions),
        recipe=[
            RecipeLineOut(
                ingredient_id=line.ingredient_id,
                ingredient_name=line.ingredient.name,
                quantity=line.quantity,
                in_stock=line.ingredient.quantity,
            )
            for line in sorted(item.recipe, key=lambda r: r.ingredient.name.lower())
        ]
        if include_recipe
        else None,
    )


def list_menu_items(
    db: Session, *, category_id: int | None = None, include_recipe: bool = False
) -> list[MenuItemOut]:
    stmt = _base_query().order_by(Category.position, Category.id, MenuItem.name)
    if category_id is not None:
        stmt = stmt.where(MenuItem.category_id == category_id)
    return [to_out(item, include_recipe=include_recipe) for item in db.scalars(stmt).unique()]


def _load(db: Session, item_id: int) -> MenuItem:
    item = db.scalars(_base_query().where(MenuItem.id == item_id)).unique().first()
    if item is None:
        raise NotFound("Item do cardápio não encontrado.")
    return item


def get_menu_item(db: Session, item_id: int) -> MenuItemOut:
    return to_out(_load(db, item_id), include_recipe=True)


def _validate_references(db: Session, data: MenuItemIn) -> None:
    if db.get(Category, data.category_id) is None:
        raise InvalidInput(
            "Revise os campos destacados.", fields={"category_id": "Selecione uma categoria."}
        )
    ids = {line.ingredient_id for line in data.recipe}
    if ids:
        found = set(db.scalars(select(Ingredient.id).where(Ingredient.id.in_(ids))))
        if found != ids:
            raise InvalidInput(
                "Revise os campos destacados.",
                fields={"recipe": "Um dos ingredientes não existe mais. Atualize a página."},
            )


def create_menu_item(db: Session, data: MenuItemIn) -> MenuItemOut:
    _validate_references(db, data)
    item = MenuItem(
        name=data.name,
        description=data.description,
        price=data.price,
        category_id=data.category_id,
        recipe=[
            RecipeItem(ingredient_id=line.ingredient_id, quantity=line.quantity)
            for line in data.recipe
        ],
    )
    db.add(item)
    db.commit()
    return get_menu_item(db, item.id)


def update_menu_item(db: Session, item_id: int, data: MenuItemIn) -> MenuItemOut:
    item = db.scalars(
        select(MenuItem).options(selectinload(MenuItem.recipe)).where(MenuItem.id == item_id)
    ).first()
    if item is None:
        raise NotFound("Item do cardápio não encontrado.")
    _validate_references(db, data)

    item.name = data.name
    item.description = data.description
    item.price = data.price
    item.category_id = data.category_id

    # A receita é substituída pela enviada. Atualiza no lugar para não apagar e
    # reinserir a mesma chave (menu_item_id, ingredient_id) no mesmo flush.
    wanted = {line.ingredient_id: line.quantity for line in data.recipe}
    for line in list(item.recipe):
        if line.ingredient_id in wanted:
            line.quantity = wanted.pop(line.ingredient_id)
        else:
            item.recipe.remove(line)
    item.recipe.extend(RecipeItem(ingredient_id=i, quantity=q) for i, q in wanted.items())
    db.commit()
    return get_menu_item(db, item_id)


def delete_menu_item(db: Session, item_id: int) -> None:
    """A receita sai junto (CASCADE); pedidos antigos mantêm nome e preço gravados."""
    item = db.get(MenuItem, item_id)
    if item is None:
        raise NotFound("Item do cardápio não encontrado.")
    image_path = item.image_path
    db.delete(item)
    db.commit()
    images.delete_media_file(image_path)


def set_image(db: Session, item_id: int, content: bytes) -> MenuItemOut:
    item = db.get(MenuItem, item_id)
    if item is None:
        raise NotFound("Item do cardápio não encontrado.")
    new_path = images.save_menu_image(content)
    old_path = item.image_path
    item.image_path = new_path
    try:
        db.commit()
    except Exception:
        images.delete_media_file(new_path)
        raise
    images.delete_media_file(old_path)
    return get_menu_item(db, item_id)


def remove_image(db: Session, item_id: int) -> MenuItemOut:
    item = db.get(MenuItem, item_id)
    if item is None:
        raise NotFound("Item do cardápio não encontrado.")
    old_path = item.image_path
    item.image_path = None
    db.commit()
    images.delete_media_file(old_path)
    return get_menu_item(db, item_id)


def load_items_for_order(db: Session, ids: set[int]) -> dict[int, MenuItem]:
    items = db.scalars(
        select(MenuItem).options(joinedload(MenuItem.recipe)).where(MenuItem.id.in_(ids))
    ).unique()
    return {item.id: item for item in items}
