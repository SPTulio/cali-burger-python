from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest

from app.modules.store.rules import Interval, is_open, next_opening, overlaps
from app.modules.users.models import Role
from tests.helpers import make_customer, make_staff, stock

SP = ZoneInfo("America/Sao_Paulo")
# 2026-10-19 é uma segunda-feira (weekday 0).
MONDAY_NOON = datetime(2026, 10, 19, 12, 0, tzinfo=SP)


# ---------------------------------------------------------------- regras puras


def test_no_hours_means_always_open():
    assert is_open(MONDAY_NOON, [])
    assert next_opening(MONDAY_NOON, []) is None


def test_regular_and_overnight_intervals():
    lunch = Interval(0, time(11), time(15))
    night = Interval(0, time(18), time(2))  # segunda 18h até terça 2h
    assert is_open(MONDAY_NOON, [lunch])
    assert not is_open(MONDAY_NOON.replace(hour=16), [lunch, night])
    assert is_open(datetime(2026, 10, 20, 1, 30, tzinfo=SP), [night])  # terça de madrugada
    assert not is_open(datetime(2026, 10, 20, 2, 0, tzinfo=SP), [night])  # fecha às 2h


def test_next_opening_wraps_to_next_week():
    sunday_only = [Interval(6, time(18), time(23))]
    assert next_opening(MONDAY_NOON, sunday_only) == datetime(2026, 10, 25, 18, 0, tzinfo=SP)
    tuesday = [Interval(1, time(11), time(15))]
    assert next_opening(MONDAY_NOON, tuesday) == datetime(2026, 10, 20, 11, 0, tzinfo=SP)


def test_overlap_detection():
    assert overlaps([Interval(0, time(11), time(15)), Interval(0, time(14), time(18))])
    assert overlaps([Interval(0, time(18), time(2)), Interval(0, time(20), time(22))])
    assert not overlaps([Interval(0, time(11), time(15)), Interval(0, time(18), time(23))])
    assert not overlaps([Interval(0, time(11), time(15)), Interval(1, time(11), time(15))])


# ---------------------------------------------------------------- API


@pytest.fixture
def at_monday_noon(monkeypatch):
    monkeypatch.setattr("app.modules.store.service.local_now", lambda: MONDAY_NOON)


@pytest.fixture
def manager(make_api, db):
    return make_api().login(make_staff(db, Role.MANAGER).cpf)


def lunch_hours(*weekdays: int) -> dict:
    return {"hours": [{"weekday": d, "opens_at": "11:00", "closes_at": "15:00"} for d in weekdays]}


def test_store_is_open_by_default(api):
    status = api.get("/api/v1/store").json()
    assert status["accepting_orders"] is True
    assert status["hours"] == []
    assert status["message"] is None


def test_manager_sets_hours_and_store_closes_outside_them(manager, api, at_monday_noon):
    response = manager.put("/api/v1/store/hours", json=lunch_hours(1, 2))  # terça e quarta
    assert response.status_code == 200
    status = api.get("/api/v1/store").json()
    assert status["accepting_orders"] is False
    assert status["within_hours"] is False
    assert status["message"] == "Estamos fechados agora. Abrimos amanhã às 11:00."
    assert status["next_opening_at"].startswith("2026-10-20T14:00:00")  # 11h em SP = 14h UTC

    manager.put("/api/v1/store/hours", json=lunch_hours(0))
    assert api.get("/api/v1/store").json()["accepting_orders"] is True


def test_overlapping_hours_are_rejected(manager):
    response = manager.put(
        "/api/v1/store/hours",
        json={
            "hours": [
                {"weekday": 0, "opens_at": "11:00", "closes_at": "15:00"},
                {"weekday": 0, "opens_at": "14:00", "closes_at": "18:00"},
            ]
        },
    )
    assert response.status_code == 422
    assert "hours" in response.json()["error"]["fields"]
    same = manager.put(
        "/api/v1/store/hours",
        json={"hours": [{"weekday": 0, "opens_at": "11:00", "closes_at": "11:00"}]},
    )
    assert same.status_code == 422


def test_closed_store_does_not_accept_orders(make_api, db, menu, manager, at_monday_noon):
    make_customer(db, username="joao")
    customer = make_api().login("joao")
    manager.put("/api/v1/store/hours", json=lunch_hours(6))  # só domingo
    before = stock(db)

    response = customer.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.classic.id, "quantity": 1}]}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "store_closed"
    assert "domingo às 11:00" in response.json()["error"]["message"]
    assert stock(db) == before


def test_paused_store_shows_message_and_blocks_orders(make_api, db, menu, manager):
    make_customer(db, username="joao")
    customer = make_api().login("joao")

    paused = manager.put("/api/v1/store/pause", json={"paused": True, "message": "Voltamos às 20h"})
    assert paused.json()["accepting_orders"] is False
    response = customer.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.water.id, "quantity": 1}]}
    )
    assert response.status_code == 409
    assert response.json()["error"] == {
        "code": "store_paused",
        "message": "Voltamos às 20h",
        "fields": {},
    }

    resumed = manager.put("/api/v1/store/pause", json={"paused": False, "message": "ignorado"})
    assert resumed.json()["pause_message"] is None
    assert (
        customer.post(
            "/api/v1/orders", json={"items": [{"menu_item_id": menu.water.id, "quantity": 1}]}
        ).status_code
        == 201
    )


def test_paused_item_is_unavailable_without_touching_stock(make_api, db, menu, manager, api):
    make_customer(db, username="joao")
    customer = make_api().login("joao")
    before = stock(db)

    response = manager.put(f"/api/v1/menu-items/{menu.classic.id}/pause", json={"paused": True})
    assert response.json()["availability"] == "paused"
    assert response.json()["is_paused"] is True
    public = {i["name"]: i for i in api.get("/api/v1/menu-items").json()}
    assert public["Cali Clássico"]["availability"] == "paused"
    assert public["Cali Clássico"]["portions"] == 10  # estoque intacto

    blocked = customer.post(
        "/api/v1/orders", json={"items": [{"menu_item_id": menu.classic.id, "quantity": 1}]}
    )
    assert blocked.status_code == 409
    assert "Cali Clássico" in blocked.json()["error"]["message"]
    assert stock(db) == before

    manager.put(f"/api/v1/menu-items/{menu.classic.id}/pause", json={"paused": False})
    assert (
        customer.post(
            "/api/v1/orders", json={"items": [{"menu_item_id": menu.classic.id, "quantity": 1}]}
        ).status_code
        == 201
    )


def test_store_settings_are_manager_only(make_api, db):
    make_customer(db, username="joao")
    cook = make_staff(db, Role.COOK)
    for client in (make_api().login("joao"), make_api().login(cook.cpf)):
        assert client.put("/api/v1/store/hours", json={"hours": []}).status_code == 403
        assert client.put("/api/v1/store/pause", json={"paused": True}).status_code == 403
        assert (
            client.put("/api/v1/store/settings", json={"prep_time_minutes": 10}).status_code == 403
        )


def test_prep_time_setting(manager):
    assert manager.put("/api/v1/store/settings", json={"prep_time_minutes": 0}).status_code == 422
    body = manager.put("/api/v1/store/settings", json={"prep_time_minutes": 25}).json()
    assert body["prep_time_minutes"] == 25
