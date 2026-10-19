from datetime import timedelta

import pytest
from sqlalchemy import select, text

from app.core.time import utcnow
from app.modules.orders.models import Order, OrderConsumption, Payment
from app.modules.users.models import Role, User
from tests.helpers import fresh, make_customer, make_staff, stock


@pytest.fixture
def people(make_api, db):
    """Cliente João, cliente Maria, balconista e cozinheiro, cada um com sua sessão."""
    make_customer(db, username="joao", name="João Silva")
    make_customer(db, username="maria", name="Maria Souza")
    manager = make_staff(db, Role.MANAGER, name="Ana Ribeiro")
    cook = make_staff(db, Role.COOK, name="Carlos Souza")

    class People:
        joao = make_api().login("joao")
        maria = make_api().login("maria")
        balcao = make_api().login(manager.cpf)
        cozinha = make_api().login(cook.cpf)

    return People


def order(client, *lines, key=None, fulfillment=None):
    headers = {"Idempotency-Key": key} if key else {}
    items = [
        {"menu_item_id": item.id, "quantity": qty, **({"notes": notes} if notes else {})}
        for item, qty, notes in ((*line, None)[:3] for line in lines)
    ]
    body = {"items": items, **({"fulfillment": fulfillment} if fulfillment else {})}
    return client.post("/api/v1/orders", json=body, headers=headers)


def act(client, order_id, action, reason=None):
    # Recusar exige motivo; nos demais testes o motivo padrão basta.
    if reason is None and action == "reject":
        reason = "Item em falta"
    body = {"reason": reason} if reason is not None else None
    return client.post(f"/api/v1/orders/{order_id}/actions/{action}", json=body)


def test_complete_order_flow_with_exact_stock(people, db, menu):
    before = stock(db)
    response = order(
        people.joao, (menu.classic, 2, "sem tomate"), (menu.double, 1), (menu.water, 3)
    )

    assert response.status_code == 201, response.text
    created = response.json()
    assert created["status"] == "awaiting_acceptance"
    assert created["total"] == "87.00"  # 2×22 + 28 + 3×5
    assert created["delivery_address"] == "Rua XV de Novembro, 100, Centro, Curitiba - PR"
    assert created["payment"]["method"] == "pix"
    assert created["payment"]["amount"] == "87.00"
    assert created["available_actions"] == ["cancel"]
    assert created["fulfillment"] == "delivery"
    assert [i["notes"] for i in created["items"]] == ["sem tomate", None, None]
    assert created["created_at"].endswith("Z")

    after = stock(db)
    assert before["Pão Brioche"] - after["Pão Brioche"] == 3
    assert before["Hambúrguer 180 g"] - after["Hambúrguer 180 g"] == 4
    assert before["Queijo Cheddar"] - after["Queijo Cheddar"] == 4
    assert after["Refrigerante lata"] == before["Refrigerante lata"]

    order_id = created["id"]
    assert act(people.balcao, order_id, "accept").json()["message"] == (
        f"Pedido nº {order_id} aceito e enviado para a cozinha."
    )
    assert act(people.cozinha, order_id, "ready").status_code == 200
    assert act(people.balcao, order_id, "dispatch").status_code == 200
    done = act(people.joao, order_id, "complete")
    assert done.status_code == 200
    assert done.json()["order"]["status"] == "completed"

    events = people.joao.get(f"/api/v1/orders/{order_id}").json()["events"]
    assert [(e["to_status"], e["actor_name"]) for e in events] == [
        ("awaiting_acceptance", "João Silva"),
        ("in_preparation", "Ana Ribeiro"),
        ("ready", "Carlos Souza"),
        ("out_for_delivery", "Ana Ribeiro"),
        ("completed", "João Silva"),
    ]
    assert stock(db) == after  # concluir não mexe no estoque


def test_order_without_enough_stock_is_not_created(people, db, menu):
    before = stock(db)
    response = order(people.joao, (menu.double, 6))  # precisa de 12 carnes, há 10

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "insufficient_stock"
    assert "Cali Duplo" in error["message"]
    assert stock(db) == before
    assert db.scalar(select(Order.id)) is None


def test_stock_is_checked_for_the_whole_order(people, db, menu):
    # Cada item cabe sozinho, mas juntos precisam de 11 carnes.
    response = order(people.joao, (menu.classic, 5), (menu.double, 3))
    assert response.status_code == 409
    assert "Cali Clássico" in response.json()["error"]["message"]


def test_item_removed_from_menu_cannot_be_ordered(people, db, menu):
    people.balcao.delete(f"/api/v1/menu-items/{menu.water.id}")
    response = order(people.joao, (menu.water, 1))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "item_unavailable"


def test_idempotency_key_prevents_duplicate_orders(people, db, menu):
    first = order(people.joao, (menu.classic, 1), key="checkout-abc-123")
    again = order(people.joao, (menu.classic, 1), key="checkout-abc-123")

    assert first.status_code == 201
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert stock(db)["Pão Brioche"] == 9  # baixou uma vez só
    assert len(db.scalars(select(Order.id)).all()) == 1
    # A mesma chave usada por outro cliente gera outro pedido.
    assert order(people.maria, (menu.classic, 1), key="checkout-abc-123").status_code == 201


@pytest.mark.parametrize(
    ("who", "action", "status"), [("balcao", "reject", "rejected"), ("joao", "cancel", "cancelled")]
)
def test_reject_and_cancel_return_ingredients(people, db, menu, who, action, status):
    before = stock(db)
    order_id = order(people.joao, (menu.double, 2), (menu.soda_item, 1)).json()["id"]
    assert stock(db) != before

    response = act(getattr(people, who), order_id, action)

    assert response.status_code == 200
    assert response.json()["order"]["status"] == status
    assert stock(db) == before
    assert db.scalar(select(OrderConsumption).where(OrderConsumption.order_id == order_id)) is None


def test_transitions_are_enforced(people, menu):
    order_id = order(people.joao, (menu.classic, 1)).json()["id"]

    assert act(people.cozinha, order_id, "accept").status_code == 403
    assert act(people.joao, order_id, "accept").status_code == 403
    assert act(people.cozinha, order_id, "ready").status_code == 409  # ainda não aceito
    assert act(people.cozinha, order_id, "dispatch").status_code == 403  # entrega é do balcão
    assert act(people.balcao, order_id, "accept").status_code == 200

    late_cancel = act(people.joao, order_id, "cancel")
    assert late_cancel.status_code == 409
    assert late_cancel.json()["error"]["code"] == "invalid_transition"
    assert act(people.balcao, order_id, "accept").status_code == 409  # duplo clique
    assert act(people.balcao, order_id, "nao-existe").status_code == 422


def test_customers_only_reach_their_own_orders(people, menu):
    order_id = order(people.joao, (menu.classic, 1)).json()["id"]

    assert people.maria.get(f"/api/v1/orders/{order_id}").status_code == 404
    assert act(people.maria, order_id, "cancel").status_code == 404
    assert people.maria.get("/api/v1/orders").json()["total"] == 0
    assert people.joao.get("/api/v1/orders").json()["total"] == 1


def test_only_customers_place_orders(people, menu):
    assert order(people.balcao, (menu.classic, 1)).status_code == 403
    assert order(people.cozinha, (menu.classic, 1)).status_code == 403


def test_kitchen_sees_only_the_preparation_queue_oldest_first(people, menu):
    ids = [order(people.joao, (menu.water, 1)).json()["id"] for _ in range(3)]
    for order_id in ids[:2]:
        act(people.balcao, order_id, "accept")

    queue = people.cozinha.get(
        "/api/v1/orders", params={"status": ["completed", "awaiting_acceptance"], "sort": "oldest"}
    ).json()
    assert [o["id"] for o in queue["items"]] == ids[:2]
    assert all(o["available_actions"] == ["ready"] for o in queue["items"])
    assert people.cozinha.get(f"/api/v1/orders/{ids[2]}").status_code == 404
    assert people.cozinha.get("/api/v1/orders/summary").json()["counts"] == {"in_preparation": 2}


def test_manager_filters_and_paginates(people, db, menu):
    joao_ids = [order(people.joao, (menu.water, 1)).json()["id"] for _ in range(3)]
    maria_id = order(people.maria, (menu.water, 1)).json()["id"]
    act(people.balcao, joao_ids[0], "reject")

    # Um pedido antigo, de 10 dias atrás.
    old = db.get(Order, joao_ids[1])
    old.created_at = utcnow() - timedelta(days=10)
    db.commit()

    page = people.balcao.get("/api/v1/orders", params={"page_size": 2}).json()
    assert (page["total"], page["pages"], len(page["items"])) == (4, 2, 2)
    assert page["items"][0]["id"] == maria_id  # mais recentes primeiro

    pending = people.balcao.get("/api/v1/orders", params={"status": "awaiting_acceptance"}).json()
    assert {o["id"] for o in pending["items"]} == {joao_ids[1], joao_ids[2], maria_id}

    by_name = people.balcao.get("/api/v1/orders", params={"q": "maria"}).json()
    assert [o["id"] for o in by_name["items"]] == [maria_id]
    by_number = people.balcao.get("/api/v1/orders", params={"q": f"#{maria_id}"}).json()
    assert [o["id"] for o in by_number["items"]] == [maria_id]

    today = (utcnow() - timedelta(days=1)).date().isoformat()
    recent = people.balcao.get("/api/v1/orders", params={"start": today}).json()
    assert joao_ids[1] not in {o["id"] for o in recent["items"]}

    invalid = people.balcao.get(
        "/api/v1/orders", params={"start": "2026-02-10", "end": "2026-02-01"}
    )
    assert invalid.status_code == 422

    counts = people.balcao.get("/api/v1/orders/summary").json()["counts"]
    assert counts["awaiting_acceptance"] == 3
    assert counts["rejected"] == 1


def test_notes_with_html_are_stored_as_plain_text(people, menu):
    notes = '<script>alert("x")</script> sem cebola'
    created = order(people.joao, (menu.classic, 1, notes)).json()
    # A API devolve o texto como foi digitado; o React escapa ao exibir.
    assert created["items"][0]["notes"] == notes


def test_customer_without_address_cannot_checkout(people, db, menu):
    from app.modules.users.models import User

    joao = db.scalar(select(User).where(User.username == "joao"))
    db.delete(joao.address)
    db.commit()
    response = order(people.joao, (menu.classic, 1))
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "missing_address"


def test_payment_is_recorded(people, db, menu):
    order_id = order(people.joao, (menu.soda_item, 2)).json()["id"]
    payment = db.scalar(select(Payment).where(Payment.order_id == order_id))
    assert (payment.method, str(payment.amount)) == ("pix", "16.00")


def test_reject_requires_a_reason_that_the_customer_sees(people, menu):
    order_id = order(people.joao, (menu.classic, 1)).json()["id"]

    missing = people.balcao.post(f"/api/v1/orders/{order_id}/actions/reject")
    assert missing.status_code == 422
    assert missing.json()["error"]["fields"] == {"reason": "Informe o motivo."}
    blank = act(people.balcao, order_id, "reject", reason="   ")
    assert blank.status_code == 422

    assert act(people.balcao, order_id, "reject", reason="Endereço fora da área").status_code == 200
    seen = people.joao.get(f"/api/v1/orders/{order_id}").json()
    assert seen["status"] == "rejected"
    assert seen["status_reason"] == "Endereço fora da área"
    assert seen["events"][-1]["note"] == "Endereço fora da área"
    listed = people.joao.get("/api/v1/orders").json()["items"][0]
    assert listed["status_reason"] == "Endereço fora da área"


def test_customer_cancel_reason_is_optional(people, menu):
    first = order(people.joao, (menu.water, 1)).json()["id"]
    second = order(people.joao, (menu.water, 1)).json()["id"]

    assert act(people.joao, first, "cancel").json()["order"]["status_reason"] is None
    with_reason = act(people.joao, second, "cancel", reason="Pedi por engano").json()["order"]
    assert with_reason["status_reason"] == "Pedi por engano"
    # Motivo só aparece em pedidos cancelados/recusados.
    third = order(people.joao, (menu.water, 1)).json()["id"]
    accepted = act(people.balcao, third, "accept", reason="ignorado").json()["order"]
    assert accepted["status_reason"] is None
    assert accepted["events"][-1]["note"] is None


def test_pickup_order_flow(people, db, menu):
    db.execute(text("UPDATE store_settings SET pickup_address = 'Rua do Balcão, 10'"))
    fresh(db)

    created = order(people.joao, (menu.classic, 1), fulfillment="pickup").json()
    assert created["fulfillment"] == "pickup"
    assert created["delivery_address"] is None
    order_id = created["id"]

    act(people.balcao, order_id, "accept")
    ready = act(people.cozinha, order_id, "ready").json()["order"]
    assert ready["status"] == "ready"
    # Retirada: não sai para entrega e quem confirma é o balcão.
    assert ready["available_actions"] == []
    seen_by_manager = people.balcao.get(f"/api/v1/orders/{order_id}").json()
    assert seen_by_manager["available_actions"] == ["pick_up"]
    assert act(people.balcao, order_id, "dispatch").status_code == 409
    assert act(people.joao, order_id, "complete").status_code == 409

    done = act(people.balcao, order_id, "pick_up").json()
    assert done["order"]["status"] == "completed"
    assert done["message"] == f"Pedido nº {order_id} retirado pelo cliente."


def test_pickup_needs_a_store_pickup_address(people, menu):
    response = order(people.joao, (menu.classic, 1), fulfillment="pickup")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "pickup_unavailable"


def test_pickup_does_not_need_a_customer_address(people, db, menu):
    db.execute(text("UPDATE store_settings SET pickup_address = 'Rua do Balcão, 10'"))
    joao = db.scalar(select(User).where(User.username == "joao"))
    db.delete(joao.address)
    fresh(db)
    assert order(people.joao, (menu.water, 1), fulfillment="pickup").status_code == 201
    assert order(people.joao, (menu.water, 1)).status_code == 409  # entrega exige endereço


def test_status_since_is_the_time_of_the_last_change(people, menu):
    order_id = order(people.joao, (menu.water, 1)).json()["id"]
    accepted = act(people.balcao, order_id, "accept").json()["order"]
    assert accepted["status_since"] == accepted["events"][-1]["created_at"]
