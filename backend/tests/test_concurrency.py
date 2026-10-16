"""Dois pedidos ao mesmo tempo disputando o último ingrediente: só um pode passar."""

import threading

from app.core.errors import BusinessRuleError
from app.db.session import get_sessionmaker
from app.modules.orders import service
from app.modules.orders.schemas import OrderCreateIn
from app.modules.users.models import User
from tests.helpers import make_customer, make_ingredient, make_item, stock


def test_last_unit_is_sold_only_once(db):
    last = make_ingredient(db, "Molho especial", 1)
    item = make_item(db, "Lanche do dia", "30.00", {last: 1})
    customers = [make_customer(db, username=f"cliente{i}").id for i in range(2)]

    barrier = threading.Barrier(len(customers))
    results: list[str] = []

    def buy(customer_id: int) -> None:
        with get_sessionmaker()() as session:
            customer = session.get(User, customer_id)
            barrier.wait()
            try:
                service.create_order(
                    session,
                    customer,
                    OrderCreateIn(items=[{"menu_item_id": item.id, "quantity": 1}]),
                    None,
                )
                results.append("ok")
            except BusinessRuleError as exc:
                results.append(exc.code)

    threads = [threading.Thread(target=buy, args=(cid,)) for cid in customers]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert sorted(results) == ["insufficient_stock", "ok"]
    assert stock(db)["Molho especial"] == 0
