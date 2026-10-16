import pytest

from app.modules.catalog.models import RecipeItem
from app.modules.users.models import Role
from tests.helpers import make_customer, make_staff, stock


@pytest.fixture
def manager_api(api, db):
    manager = make_staff(db, Role.MANAGER)
    return api.login(manager.cpf)


def test_adding_existing_ingredient_sums_the_quantity(manager_api, db, menu):
    response = manager_api.post("/api/v1/ingredients", json={"name": "Pão Brioche", "quantity": 15})

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is False
    assert body["ingredient"]["quantity"] == 25
    assert stock(db)["Pão Brioche"] == 25


def test_adding_new_ingredient(manager_api, db):
    body = manager_api.post("/api/v1/ingredients", json={"name": " Bacon ", "quantity": 3}).json()
    assert body["created"] is True
    assert body["ingredient"]["name"] == "Bacon"
    assert body["ingredient"]["level"] == "low"


@pytest.mark.parametrize("quantity", [0, -1, 100_001])
def test_add_quantity_limits(manager_api, quantity):
    response = manager_api.post("/api/v1/ingredients", json={"name": "Bacon", "quantity": quantity})
    assert response.status_code == 422
    assert "quantity" in response.json()["error"]["fields"]


def test_list_shows_usage_and_stock_level(manager_api, menu):
    body = manager_api.get("/api/v1/ingredients").json()
    by_name = {i["name"]: i for i in body["items"]}

    assert body["low_stock_threshold"] == 10
    assert by_name["Pão Brioche"]["used_in"] == 2
    assert by_name["Refrigerante lata"]["used_in"] == 1
    assert by_name["Refrigerante lata"]["level"] == "low"
    assert (
        manager_api.get("/api/v1/ingredients", params={"q": "queijo"}).json()["items"][0]["name"]
        == "Queijo Cheddar"
    )


def test_edit_allows_zero_and_rejects_duplicate_names(manager_api, menu):
    url = f"/api/v1/ingredients/{menu.soda.id}"
    ok = manager_api.put(url, json={"name": "Refrigerante lata", "quantity": 0})
    assert ok.status_code == 200
    assert ok.json()["level"] == "out"

    duplicate = manager_api.put(url, json={"name": "Pão Brioche", "quantity": 1})
    assert duplicate.status_code == 422
    assert (
        duplicate.json()["error"]["fields"]["name"] == "Já existe outro ingrediente com esse nome."
    )


def test_deleting_ingredient_removes_it_from_recipes(manager_api, db, menu):
    assert manager_api.delete(f"/api/v1/ingredients/{menu.cheese.id}").status_code == 204
    assert db.query(RecipeItem).filter_by(ingredient_id=menu.cheese.id).count() == 0
    assert manager_api.delete(f"/api/v1/ingredients/{menu.cheese.id}").status_code == 404


def test_inventory_is_manager_only(make_api, db):
    make_customer(db, username="joao")
    cook = make_staff(db, Role.COOK)
    for client in (make_api().login("joao"), make_api().login(cook.cpf)):
        assert client.get("/api/v1/ingredients").status_code == 403
        assert (
            client.post("/api/v1/ingredients", json={"name": "X", "quantity": 1}).status_code == 403
        )
