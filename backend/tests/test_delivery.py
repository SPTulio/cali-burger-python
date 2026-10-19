from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select, text

from app.core.time import utcnow
from app.modules.orders.models import Order, OrderStatus, OrderStatusEvent
from app.modules.store.delivery import estimate_minutes, fee_for, normalize
from app.modules.users.models import Role
from tests.helpers import fresh, make_customer, make_staff, stock

# ---------------------------------------------------------------- regras puras


def test_free_delivery_threshold():
    assert fee_for(Decimal("79.99"), Decimal("6.00"), Decimal("80.00")) == Decimal("6.00")
    assert fee_for(Decimal("80.00"), Decimal("6.00"), Decimal("80.00")) == Decimal("0.00")
    assert fee_for(Decimal("500"), Decimal("6.00"), None) == Decimal("6.00")


def test_estimate_rounds_and_adds_queue():
    assert estimate_minutes(20, 0, 15) == (35, 45)
    assert estimate_minutes(20, 1, 15) == (35, 45)  # a cozinha toca 2 pedidos ao mesmo tempo
    assert estimate_minutes(20, 3, 15) == (45, 55)  # 2 pedidos além da capacidade: +6 min
    assert estimate_minutes(18, 0, 0) == (20, 30)


def test_district_names_ignore_accents_case_and_spaces():
    assert normalize("  Água   Verde ") == normalize("agua verde")
    assert normalize("Centro") != normalize("Centro Cívico")


# ---------------------------------------------------------------- API


@pytest.fixture
def manager(make_api, db):
    return make_api().login(make_staff(db, Role.MANAGER).cpf)


@pytest.fixture
def customer(make_api, db):
    make_customer(db, username="joao")  # bairro "Centro"
    return make_api().login("joao")


def zones(*items):
    return {
        "zones": [{"name": name, "fee": fee, "extra_minutes": extra} for name, fee, extra in items]
    }


def buy(client, menu, **extra):
    return client.post(
        "/api/v1/orders",
        json={"items": [{"menu_item_id": menu.classic.id, "quantity": 1}], **extra},
    )


def test_without_configuration_delivery_is_free_everywhere(customer, menu):
    created = buy(customer, menu).json()
    assert (created["subtotal"], created["delivery_fee"], created["total"]) == (
        "22.00",
        "0.00",
        "22.00",
    )


def test_zone_fee_is_charged_and_matched_without_accents(manager, customer, db, menu):
    assert manager.put("/api/v1/store/zones", json=zones(("centro", "6.50", 5))).status_code == 200
    created = buy(customer, menu).json()
    assert created["delivery_fee"] == "6.50"
    assert created["total"] == "28.50"
    assert created["payment"]["amount"] == "28.50"


def test_outside_the_area_is_refused_before_touching_stock(manager, customer, db, menu):
    manager.put("/api/v1/store/zones", json=zones(("Batel", "6.00", 0)))
    before = stock(db)
    response = buy(customer, menu)
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "outside_delivery_area",
        "message": "Ainda não entregamos no bairro Centro.",
        "fields": {},
    }
    assert stock(db) == before
    # Retirada continua possível para quem está fora da área.
    db.execute(text("UPDATE store_settings SET pickup_address = 'Balcão'"))
    fresh(db)
    assert buy(customer, menu, fulfillment="pickup").status_code == 201


def test_default_fee_and_free_delivery(manager, customer, menu):
    manager.put("/api/v1/store/zones", json=zones(("Batel", "6.00", 0)))
    manager.put(
        "/api/v1/store/settings",
        json={"prep_time_minutes": 20, "default_delivery_fee": "9.90", "free_delivery_above": "40"},
    )
    assert buy(customer, menu).json()["delivery_fee"] == "9.90"
    big = customer.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.double.id, "quantity": 2}]}
    ).json()
    assert big["subtotal"] == "56.00"
    assert big["delivery_fee"] == "0.00"


def test_pickup_has_no_fee(manager, customer, db, menu):
    manager.put("/api/v1/store/zones", json=zones(("Centro", "6.00", 0)))
    db.execute(text("UPDATE store_settings SET pickup_address = 'Balcão'"))
    fresh(db)
    created = buy(customer, menu, fulfillment="pickup").json()
    assert created["delivery_fee"] == "0.00"
    assert created["total"] == "22.00"


def test_quote_for_customer_and_visitor(manager, customer, api, menu):
    manager.put("/api/v1/store/zones", json=zones(("Centro", "5.00", 10)))
    mine = customer.get("/api/v1/store/quote", params={"subtotal": "30"}).json()
    assert mine["served"] is True
    assert mine["zone_name"] == "Centro"
    assert mine["delivery_fee"] == "5.00"
    # meta 20 + base 15 + 10 do bairro = 45
    assert (mine["eta_min_minutes"], mine["eta_max_minutes"]) == (45, 55)

    visitor = api.get("/api/v1/store/quote").json()
    assert visitor["served"] is True
    assert visitor["delivery_fee"] is None  # bairro ainda desconhecido

    pickup = customer.get("/api/v1/store/quote", params={"fulfillment": "pickup"}).json()
    assert (pickup["delivery_fee"], pickup["eta_min_minutes"]) == ("0.00", 20)


def test_order_stores_the_estimate(customer, menu):
    created = buy(customer, menu).json()
    assert (created["eta_min_minutes"], created["eta_max_minutes"]) == (35, 45)


def test_average_preparation_time_replaces_the_target(customer, db, menu):
    """Com 5+ pedidos medidos (aceite → pronto), a previsão usa a média real."""
    now = utcnow()
    ids = [buy(customer, menu).json()["id"] for _ in range(5)]
    fresh(db)
    for i, order_id in enumerate(ids):
        db.add_all(
            [
                OrderStatusEvent(
                    order_id=order_id,
                    from_status=OrderStatus.AWAITING_ACCEPTANCE,
                    to_status=OrderStatus.IN_PREPARATION,
                    created_at=now - timedelta(minutes=60 + i),
                ),
                OrderStatusEvent(
                    order_id=order_id,
                    from_status=OrderStatus.IN_PREPARATION,
                    to_status=OrderStatus.READY,
                    created_at=now - timedelta(minutes=50 + i),
                ),
            ]
        )
        # Concluídos: não contam na fila da cozinha.
        db.get(Order, order_id).status = OrderStatus.COMPLETED
    fresh(db)
    quote = customer.get("/api/v1/store/quote").json()
    # média de 10 min de preparo + 15 de deslocamento = 25
    assert quote["eta_min_minutes"] == 25


def test_zones_management(manager, make_api, db):
    duplicated = manager.put(
        "/api/v1/store/zones", json=zones(("Água Verde", "5", 0), ("agua verde", "6", 0))
    )
    assert duplicated.status_code == 422
    assert "zones" in duplicated.json()["error"]["fields"]
    invalid = manager.put("/api/v1/store/zones", json=zones(("Batel", "-1", 0)))
    assert invalid.status_code == 422

    saved = manager.put("/api/v1/store/zones", json=zones(("Batel", "6", 5), ("Centro", "4.5", 0)))
    assert [z["name"] for z in saved.json()] == ["Batel", "Centro"]
    assert manager.get("/api/v1/store/zones").json()[1]["fee"] == "4.50"

    make_customer(db, username="maria")
    customer = make_api().login("maria")
    assert customer.get("/api/v1/store/zones").status_code == 403
    assert customer.put("/api/v1/store/zones", json={"zones": []}).status_code == 403
    assert db.scalar(select(Order.id)) is None
