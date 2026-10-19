"""Regras puras: sem banco nem HTTP."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.errors import BusinessRuleError, Forbidden
from app.core.validators import format_cpf, is_valid_cpf, looks_like_cpf
from app.modules.catalog.rules import availability, portions_available
from app.modules.catalog.schemas import Availability, MenuItemIn
from app.modules.inventory.schemas import StockLevel
from app.modules.inventory.service import stock_level
from app.modules.orders.models import Fulfillment, OrderStatus
from app.modules.orders.schemas import OrderCreateIn
from app.modules.orders.service import money
from app.modules.orders.state_machine import OrderAction, available_actions, resolve
from app.modules.users.models import Role


@pytest.mark.parametrize("cpf", ["352.658.110-01", "21199625027", "529.982.247-25"])
def test_valid_cpfs(cpf: str) -> None:
    assert is_valid_cpf(cpf)


@pytest.mark.parametrize("cpf", ["111.111.111-11", "123.456.789-00", "1234", "", "abc"])
def test_invalid_cpfs(cpf: str) -> None:
    assert not is_valid_cpf(cpf)


def test_cpf_helpers() -> None:
    assert format_cpf("35265811001") == "352.658.110-01"
    assert looks_like_cpf("352.658.110-01")
    assert looks_like_cpf("35265811001")
    assert not looks_like_cpf("joao")
    assert not looks_like_cpf("joao12345678901")


def test_portions_use_the_scarcest_ingredient() -> None:
    # 10 pães (1 por unidade) e 7 carnes (2 por unidade) -> 3 unidades
    assert portions_available([(10, 1), (7, 2)]) == 3
    assert portions_available([(0, 1), (50, 1)]) == 0
    assert portions_available([]) is None  # sem receita: não depende do estoque


@pytest.mark.parametrize(
    ("portions", "expected"),
    [
        (None, Availability.AVAILABLE),
        (0, Availability.SOLD_OUT),
        (1, Availability.LOW),
        (5, Availability.LOW),
        (6, Availability.AVAILABLE),
    ],
)
def test_availability_labels(portions: int | None, expected: Availability) -> None:
    assert availability(portions) == expected


@pytest.mark.parametrize(
    ("quantity", "level"),
    [(0, StockLevel.OUT), (1, StockLevel.LOW), (10, StockLevel.LOW), (11, StockLevel.OK)],
)
def test_stock_levels(quantity: int, level: StockLevel) -> None:
    assert stock_level(quantity, threshold=10) == level


def test_money_rounds_half_up_to_cents() -> None:
    assert money(Decimal("10.005")) == Decimal("10.01")
    assert money(Decimal("19.90") * 3) == Decimal("59.70")


# ---------------------------------------------------------------- máquina de estados

AWAITING = OrderStatus.AWAITING_ACCEPTANCE
DELIVERY = Fulfillment.DELIVERY
PICKUP = Fulfillment.PICKUP


def actions(status: OrderStatus, role: Role, kind: Fulfillment = DELIVERY, *, owner: bool = False):
    return available_actions(status, role, kind, is_owner=owner)


def test_actions_available_per_role_and_status() -> None:
    assert actions(AWAITING, Role.MANAGER) == [OrderAction.ACCEPT, OrderAction.REJECT]
    assert actions(AWAITING, Role.CUSTOMER, owner=True) == [OrderAction.CANCEL]
    assert actions(AWAITING, Role.CUSTOMER) == []
    assert actions(AWAITING, Role.COOK) == []
    # A cozinha (ou o balcão) marca como pronto.
    assert actions(OrderStatus.IN_PREPARATION, Role.COOK) == [OrderAction.READY]
    assert actions(OrderStatus.IN_PREPARATION, Role.MANAGER) == [OrderAction.READY]
    assert actions(OrderStatus.OUT_FOR_DELIVERY, Role.CUSTOMER, owner=True) == [
        OrderAction.COMPLETE
    ]
    for final in (OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
        for role in Role:
            for kind in Fulfillment:
                assert actions(final, role, kind, owner=True) == []


def test_ready_order_depends_on_the_fulfillment() -> None:
    ready = OrderStatus.READY
    assert actions(ready, Role.MANAGER, DELIVERY) == [OrderAction.DISPATCH]
    assert actions(ready, Role.MANAGER, PICKUP) == [OrderAction.PICK_UP]
    assert actions(ready, Role.COOK, DELIVERY) == []
    assert actions(ready, Role.CUSTOMER, PICKUP, owner=True) == []
    with pytest.raises(BusinessRuleError):
        resolve(OrderAction.DISPATCH, ready, Role.MANAGER, PICKUP, is_owner=False)
    with pytest.raises(BusinessRuleError):
        resolve(OrderAction.PICK_UP, ready, Role.MANAGER, DELIVERY, is_owner=False)
    assert resolve(OrderAction.PICK_UP, ready, Role.MANAGER, PICKUP, is_owner=False).to_status == (
        OrderStatus.COMPLETED
    )


def test_transitions_that_return_stock() -> None:
    reject = resolve(OrderAction.REJECT, AWAITING, Role.MANAGER, DELIVERY, is_owner=False)
    cancel = resolve(OrderAction.CANCEL, AWAITING, Role.CUSTOMER, DELIVERY, is_owner=True)
    accept = resolve(OrderAction.ACCEPT, AWAITING, Role.MANAGER, DELIVERY, is_owner=False)
    assert reject.restock
    assert reject.requires_reason
    assert reject.to_status == OrderStatus.REJECTED
    assert cancel.restock
    assert cancel.to_status == OrderStatus.CANCELLED
    assert not accept.restock


def test_wrong_role_is_forbidden_and_wrong_status_is_a_conflict() -> None:
    with pytest.raises(Forbidden):
        resolve(OrderAction.ACCEPT, AWAITING, Role.COOK, DELIVERY, is_owner=False)
    with pytest.raises(Forbidden):
        resolve(OrderAction.CANCEL, AWAITING, Role.CUSTOMER, DELIVERY, is_owner=False)
    with pytest.raises(Forbidden):
        resolve(OrderAction.DISPATCH, OrderStatus.READY, Role.COOK, DELIVERY, is_owner=False)
    with pytest.raises(BusinessRuleError):
        resolve(
            OrderAction.CANCEL, OrderStatus.IN_PREPARATION, Role.CUSTOMER, DELIVERY, is_owner=True
        )


# ---------------------------------------------------------------- validação de entrada


def test_cart_limits() -> None:
    OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 20}])
    with pytest.raises(ValidationError):
        OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 21}])
    with pytest.raises(ValidationError):
        OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 0}])
    with pytest.raises(ValidationError):
        OrderCreateIn(items=[])
    with pytest.raises(ValidationError):
        OrderCreateIn(
            items=[{"menu_item_id": 1, "quantity": 1}, {"menu_item_id": 1, "quantity": 2}]
        )


def test_notes_are_trimmed_and_limited() -> None:
    order = OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 1, "notes": "  sem cebola  "}])
    assert order.items[0].notes == "sem cebola"
    blank = OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 1, "notes": "   "}])
    assert blank.items[0].notes is None
    with pytest.raises(ValidationError):
        OrderCreateIn(items=[{"menu_item_id": 1, "quantity": 1, "notes": "x" * 256}])


def test_price_accepts_brazilian_format() -> None:
    item = MenuItemIn(name="X", price="22,90", category_id=1)
    assert item.price == Decimal("22.90")
    for bad in ("0", "-1", "10000", "1,999", "abc"):
        with pytest.raises(ValidationError):
            MenuItemIn(name="X", price=bad, category_id=1)
