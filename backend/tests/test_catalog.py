import io

import pytest
from PIL import Image

from app.modules.orders.models import OrderItem
from app.modules.users.models import Role
from tests.helpers import fresh, make_customer, make_staff


@pytest.fixture
def manager_api(make_api, db):
    manager = make_staff(db, Role.MANAGER)
    return make_api().login(manager.cpf)


def png_bytes(size: tuple[int, int] = (2, 2), fmt: str = "PNG") -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 80, 20)).save(buffer, format=fmt)
    return buffer.getvalue()


def test_public_menu_has_availability_but_no_recipes(api, menu):
    items = {i["name"]: i for i in api.get("/api/v1/menu-items").json()}

    assert items["Cali Clássico"]["portions"] == 10
    assert items["Cali Clássico"]["availability"] == "available"
    assert items["Cali Duplo"]["portions"] == 5  # 10 carnes / 2 por unidade
    assert items["Cali Duplo"]["availability"] == "low"
    assert items["Água"]["portions"] is None  # sem receita: sempre disponível
    assert items["Água"]["availability"] == "available"
    assert all(i["recipe"] is None for i in items.values())
    assert items["Cali Clássico"]["price"] == "22.00"


def test_menu_filters_by_category_in_menu_order(api, menu):
    drinks = api.get("/api/v1/menu-items", params={"category_id": 3}).json()
    assert [i["name"] for i in drinks] == ["Água", "Refrigerante"]
    assert {i["category"]["name"] for i in drinks} == {"Bebidas"}


def test_sold_out_when_any_ingredient_is_missing(api, db, menu):
    menu.cheese.quantity = 0
    db.commit()
    items = {i["name"]: i for i in api.get("/api/v1/menu-items").json()}
    assert items["Cali Clássico"]["availability"] == "sold_out"
    assert items["Refrigerante"]["availability"] == "low"


def test_staff_see_recipes(make_api, db, menu):
    cook = make_staff(db, Role.COOK)
    client = make_api().login(cook.cpf)
    classic = next(
        i for i in client.get("/api/v1/menu-items").json() if i["name"] == "Cali Clássico"
    )
    assert {line["ingredient_name"] for line in classic["recipe"]} == {
        "Pão Brioche",
        "Hambúrguer 180 g",
        "Queijo Cheddar",
    }
    assert client.get(f"/api/v1/menu-items/{menu.classic.id}").status_code == 200
    # Cozinheiro só consulta: não altera o cardápio.
    assert client.delete(f"/api/v1/menu-items/{menu.classic.id}").status_code == 403


def test_create_item_with_recipe(manager_api, menu):
    response = manager_api.post(
        "/api/v1/menu-items",
        json={
            "name": "Cali Bacon",
            "description": "",
            "price": "31,50",
            "category_id": 1,
            "recipe": [
                {"ingredient_id": menu.bread.id, "quantity": 1},
                {"ingredient_id": menu.patty.id, "quantity": 1},
            ],
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["price"] == "31.50"
    assert body["description"] is None
    assert len(body["recipe"]) == 2


def test_create_item_validation(manager_api, menu):
    response = manager_api.post(
        "/api/v1/menu-items",
        json={
            "name": "",
            "price": "0",
            "category_id": 99,
            "recipe": [
                {"ingredient_id": menu.bread.id, "quantity": 1},
                {"ingredient_id": menu.bread.id, "quantity": 2},
            ],
        },
    )
    assert response.status_code == 422
    assert {"name", "price", "recipe"} <= set(response.json()["error"]["fields"])

    bad_refs = manager_api.post(
        "/api/v1/menu-items",
        json={"name": "X", "price": "10", "category_id": 99, "recipe": []},
    )
    assert bad_refs.json()["error"]["fields"] == {"category_id": "Selecione uma categoria."}

    missing_ingredient = manager_api.post(
        "/api/v1/menu-items",
        json={
            "name": "X",
            "price": "10",
            "category_id": 1,
            "recipe": [{"ingredient_id": 9999, "quantity": 1}],
        },
    )
    assert "recipe" in missing_ingredient.json()["error"]["fields"]


def test_update_replaces_the_recipe(manager_api, menu):
    response = manager_api.put(
        f"/api/v1/menu-items/{menu.classic.id}",
        json={
            "name": "Cali Clássico",
            "description": "Novo",
            "price": "23.00",
            "category_id": 1,
            "recipe": [
                {"ingredient_id": menu.bread.id, "quantity": 2},  # existente, nova quantidade
                {"ingredient_id": menu.soda.id, "quantity": 1},  # novo
            ],  # queijo e carne saem
        },
    )
    assert response.status_code == 200, response.text
    recipe = {line["ingredient_name"]: line["quantity"] for line in response.json()["recipe"]}
    assert recipe == {"Pão Brioche": 2, "Refrigerante lata": 1}


def test_delete_item_keeps_order_history(make_api, db, menu, manager_api):
    make_customer(db, username="joao")
    customer = make_api().login("joao")
    customer.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.classic.id, "quantity": 1}]}
    )

    assert manager_api.delete(f"/api/v1/menu-items/{menu.classic.id}").status_code == 204

    fresh(db)
    item = db.query(OrderItem).one()
    assert item.menu_item_id is None
    assert item.product_name == "Cali Clássico"


def test_image_upload_replace_and_remove(manager_api, media_dir, menu):
    url = f"/api/v1/menu-items/{menu.classic.id}/image"
    first = manager_api.put(url, files={"image": ("foto.png", png_bytes(), "image/png")})
    assert first.status_code == 200, first.text
    first_url = first.json()["image_url"]
    assert first_url.startswith("/media/menu/")
    assert first_url.endswith(".png")
    first_file = media_dir / first_url.removeprefix("/media/")
    assert first_file.exists()
    assert manager_api.get(first_url).status_code == 200

    second = manager_api.put(
        url, files={"image": ("foto.webp", png_bytes(fmt="WEBP"), "image/webp")}
    )
    assert second.json()["image_url"].endswith(".webp")
    assert not first_file.exists()  # a imagem antiga é apagada

    removed = manager_api.delete(url)
    assert removed.json()["image_url"] is None


@pytest.mark.parametrize(
    ("filename", "content"),
    [
        ("shell.php.png", b"<?php system($_GET['c']); ?>"),
        ("vazio.png", b""),
        ("animacao.gif", None),
    ],
)
def test_invalid_images_are_rejected(manager_api, media_dir, menu, filename, content):
    if content is None:
        content = png_bytes(fmt="GIF")
    response = manager_api.put(
        f"/api/v1/menu-items/{menu.classic.id}/image",
        files={"image": (filename, content, "image/png")},
    )
    assert response.status_code == 422
    assert "image" in response.json()["error"]["fields"]


def test_image_size_limit(manager_api, menu):
    too_big = png_bytes() + b"0" * (2 * 1024 * 1024)
    response = manager_api.put(
        f"/api/v1/menu-items/{menu.classic.id}/image",
        files={"image": ("grande.png", too_big, "image/png")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["fields"]["image"] == "A imagem deve ter no máximo 2 MB."
