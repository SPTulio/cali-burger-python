from datetime import datetime, timedelta

import pytest

from app.core.time import local_today
from app.modules.orders.models import Order
from app.modules.users.models import Role
from tests.helpers import fresh, make_customer, make_staff


@pytest.fixture
def clients(make_api, db):
    make_customer(db, username="joao")
    manager = make_staff(db, Role.MANAGER)
    return make_api().login("joao"), make_api().login(manager.cpf)


def place(client, *lines):
    items = [{"menu_item_id": item.id, "quantity": qty} for item, qty in lines]
    return client.post("/api/v1/orders", json={"items": items}).json()["id"]


def test_report_excludes_cancelled_and_rejected_orders(clients, menu):
    customer, manager = clients
    place(customer, (menu.classic, 2), (menu.water, 1))  # 49,00
    place(customer, (menu.double, 1))  # 28,00
    cancelled = place(customer, (menu.classic, 3))
    rejected = place(customer, (menu.soda_item, 2))
    customer.post(f"/api/v1/orders/{cancelled}/actions/cancel")
    manager.post(f"/api/v1/orders/{rejected}/actions/reject")

    report = manager.get("/api/v1/reports/sales").json()

    assert report["summary"] == {
        "revenue": "77.00",
        "orders": 2,
        "items_sold": 4,
        "average_ticket": "38.50",
    }
    products = {p["product_name"]: (p["quantity"], p["total"]) for p in report["top_products"]}
    assert products == {
        "Cali Clássico": (2, "44.00"),
        "Cali Duplo": (1, "28.00"),
        "Água": (1, "5.00"),
    }
    used = {i["name"]: i["quantity"] for i in report["ingredients_used"]}
    assert used == {"Pão Brioche": 3, "Hambúrguer 180 g": 4, "Queijo Cheddar": 4}
    assert report["daily"] == [{"date": local_today().isoformat(), "orders": 2, "revenue": "77.00"}]
    by_day = report["sales_by_day"][0]
    assert by_day["date"] == local_today().isoformat()


def test_ingredients_to_buy_use_the_low_stock_threshold(clients, menu):
    _, manager = clients
    to_buy = {
        i["name"]: i["quantity"]
        for i in manager.get("/api/v1/reports/sales").json()["ingredients_to_buy"]
    }
    # Limite padrão = 10: todos os ingredientes do cardápio de teste estão no limite.
    assert to_buy == {
        "Refrigerante lata": 5,
        "Hambúrguer 180 g": 10,
        "Pão Brioche": 10,
        "Queijo Cheddar": 10,
    }


def test_period_filter_uses_local_days_and_includes_the_end_date(clients, db, menu):
    customer, manager = clients
    first = place(customer, (menu.water, 1))
    second = place(customer, (menu.water, 2))

    # 23h30 de 01/03 em São Paulo (UTC-3) = 02h30 de 02/03 em UTC.
    db.get(Order, first).created_at = datetime(2026, 3, 2, 2, 30)
    db.get(Order, second).created_at = datetime(2026, 3, 2, 12, 0)
    fresh(db)

    only_first = manager.get(
        "/api/v1/reports/sales", params={"start": "2026-03-01", "end": "2026-03-01"}
    ).json()
    assert only_first["summary"]["orders"] == 1
    assert only_first["daily"] == [{"date": "2026-03-01", "orders": 1, "revenue": "5.00"}]

    both = manager.get(
        "/api/v1/reports/sales", params={"start": "2026-03-01", "end": "2026-03-02"}
    ).json()
    assert both["summary"]["orders"] == 2

    future = (local_today() + timedelta(days=1)).isoformat()
    assert (
        manager.get("/api/v1/reports/sales", params={"start": future}).json()["summary"]["orders"]
        == 0
    )


def test_report_validation_and_permissions(clients):
    customer, manager = clients
    bad = manager.get("/api/v1/reports/sales", params={"start": "2026-03-10", "end": "2026-03-01"})
    assert bad.status_code == 422
    assert customer.get("/api/v1/reports/sales").status_code == 403


def test_empty_report(clients):
    _, manager = clients
    report = manager.get("/api/v1/reports/sales").json()
    assert report["summary"] == {
        "revenue": "0.00",
        "orders": 0,
        "items_sold": 0,
        "average_ticket": "0.00",
    }
    assert report["daily"] == report["sales_by_day"] == report["ingredients_used"] == []
