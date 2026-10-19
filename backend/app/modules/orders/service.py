"""Pedidos: criação com baixa de estoque, mudanças de status e consultas."""

import math
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import BusinessRuleError, Forbidden, InvalidInput, NotFound
from app.core.time import local_day_end_utc, local_day_start_utc
from app.modules.catalog.service import load_items_for_order
from app.modules.inventory.models import Ingredient
from app.modules.orders.models import (
    VOIDED_STATUSES,
    Fulfillment,
    Order,
    OrderConsumption,
    OrderItem,
    OrderStatus,
    OrderStatusEvent,
    Payment,
    PaymentMethod,
)
from app.modules.orders.schemas import (
    OrderCreateIn,
    OrderEventOut,
    OrderFilters,
    OrderItemOut,
    OrderOut,
    OrderPage,
    OrderSort,
    PaymentOut,
)
from app.modules.orders.state_machine import OrderAction, available_actions, resolve
from app.modules.store import delivery
from app.modules.store import service as store
from app.modules.users.models import Role, User

CENT = Decimal("0.01")

# Carregamento dos relacionamentos em consultas separadas (sem N+1).
ORDER_LOAD_OPTIONS = (
    selectinload(Order.items),
    selectinload(Order.payment),
    selectinload(Order.events),
)


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------- serialização


def to_out(order: Order, user: User, *, with_events: bool = False) -> OrderOut:
    last_event = order.events[-1] if order.events else None
    return OrderOut(
        id=order.id,
        status=order.status,
        fulfillment=order.fulfillment,
        status_since=last_event.created_at if last_event else order.created_at,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        delivery_address=order.delivery_address,
        subtotal=order.subtotal,
        delivery_fee=order.delivery_fee,
        total=order.total,
        eta_min_minutes=order.eta_min_minutes,
        eta_max_minutes=order.eta_max_minutes,
        created_at=order.created_at,
        updated_at=order.updated_at,
        items=[OrderItemOut.model_validate(i) for i in order.items],
        payment=PaymentOut.model_validate(order.payment) if order.payment else None,
        status_reason=last_event.note if last_event and order.status in VOIDED_STATUSES else None,
        events=[OrderEventOut.model_validate(e) for e in order.events] if with_events else None,
        available_actions=available_actions(
            order.status, user.role, order.fulfillment, is_owner=order.customer_id == user.id
        ),
    )


def _load_order(db: Session, order_id: int) -> Order | None:
    return db.scalars(
        select(Order)
        .options(*ORDER_LOAD_OPTIONS)
        .where(Order.id == order_id)
        .execution_options(populate_existing=True)
    ).first()


# ---------------------------------------------------------------- criação


def create_order(
    db: Session, customer: User, data: OrderCreateIn, idempotency_key: str | None
) -> tuple[Order, bool]:
    """Cria o pedido a partir do carrinho. Tudo em uma transação: confere o estoque com as
    linhas travadas, grava pedido, itens, consumo, pagamento e histórico e dá baixa nos
    ingredientes. Se faltar algo, nada é gravado.

    Retorna (pedido, criado). Com a mesma chave de idempotência, devolve o pedido já criado.
    """
    if idempotency_key:
        existing = _find_by_idempotency_key(db, customer.id, idempotency_key)
        if existing:
            return existing, False

    store.ensure_accepting_orders(db)

    pickup = data.fulfillment == Fulfillment.PICKUP
    if pickup and not store.get_settings_row(db).pickup_address:
        raise BusinessRuleError(
            "A retirada no balcão não está disponível. Escolha a entrega.",
            code="pickup_unavailable",
        )
    if not pickup and customer.address is None:
        raise BusinessRuleError(
            "Cadastre um endereço de entrega antes de finalizar o pedido.",
            code="missing_address",
        )

    lines = {line.menu_item_id: line for line in data.items}
    products = load_items_for_order(db, set(lines))
    if len(products) != len(lines):
        raise BusinessRuleError(
            "Um dos itens do carrinho não está mais no cardápio. Revise o carrinho.",
            code="item_unavailable",
        )
    paused = [p.name for p in products.values() if p.is_paused]
    if paused:
        raise BusinessRuleError(
            f"Indisponível no momento: {', '.join(paused)}. Retire do carrinho para continuar.",
            code="item_unavailable",
        )

    # Taxa e previsão antes de travar o estoque: fora da área, nada é reservado.
    items_total = sum(
        (money(products[m].price * line.quantity) for m, line in lines.items()), Decimal("0")
    )
    district = None if pickup or customer.address is None else customer.address.district
    shipping = delivery.quote(db, data.fulfillment, district, items_total)
    if not shipping.served or shipping.fee is None:
        raise BusinessRuleError(
            shipping.message or "Ainda não entregamos neste endereço.",
            code="outside_delivery_area",
        )

    # Quanto de cada ingrediente o pedido inteiro consome.
    needed: dict[int, int] = defaultdict(int)
    used_by: dict[int, list[str]] = defaultdict(list)
    for menu_item_id, line in lines.items():
        product = products[menu_item_id]
        for recipe_line in product.recipe:
            needed[recipe_line.ingredient_id] += recipe_line.quantity * line.quantity
            used_by[recipe_line.ingredient_id].append(product.name)

    # Trava as linhas em ordem de id (evita deadlock entre pedidos simultâneos).
    stock = (
        {
            ingredient.id: ingredient
            for ingredient in db.scalars(
                select(Ingredient)
                .where(Ingredient.id.in_(needed))
                .order_by(Ingredient.id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        }
        if needed
        else {}
    )

    lacking: list[str] = []
    for ingredient_id, quantity in needed.items():
        available = stock[ingredient_id].quantity if ingredient_id in stock else 0
        if available < quantity:
            lacking.extend(n for n in used_by[ingredient_id] if n not in lacking)
    if lacking:
        raise BusinessRuleError(
            f"Não há estoque suficiente para: {', '.join(lacking)}. "
            "Diminua a quantidade ou escolha outro item.",
            code="insufficient_stock",
        )

    items: list[OrderItem] = []
    total = Decimal("0")
    for menu_item_id, line in lines.items():
        product = products[menu_item_id]
        subtotal = money(product.price * line.quantity)
        total += subtotal
        items.append(
            OrderItem(
                menu_item_id=menu_item_id,
                product_name=product.name,
                unit_price=product.price,
                quantity=line.quantity,
                subtotal=subtotal,
                notes=line.notes,
            )
        )

    for ingredient_id, quantity in needed.items():
        stock[ingredient_id].quantity -= quantity

    order = Order(
        customer_id=customer.id,
        customer_name=customer.name,
        fulfillment=data.fulfillment,
        delivery_address=None
        if pickup or customer.address is None
        else customer.address.one_line(),
        status=OrderStatus.AWAITING_ACCEPTANCE,
        subtotal=money(total),
        delivery_fee=shipping.fee,
        total=money(total + shipping.fee),
        eta_min_minutes=shipping.eta_min,
        eta_max_minutes=shipping.eta_max,
        idempotency_key=idempotency_key,
        items=items,
        consumptions=[OrderConsumption(ingredient_id=i, quantity=q) for i, q in needed.items()],
        payment=Payment(method=PaymentMethod.PIX, amount=money(total + shipping.fee)),
        events=[
            OrderStatusEvent(
                from_status=None,
                to_status=OrderStatus.AWAITING_ACCEPTANCE,
                actor_id=customer.id,
                actor_name=customer.name,
            )
        ],
    )
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Duas requisições com a mesma chave ao mesmo tempo: a outra venceu.
        if idempotency_key:
            existing = _find_by_idempotency_key(db, customer.id, idempotency_key)
            if existing:
                return existing, False
        raise

    created = _load_order(db, order.id)
    if created is None:  # pragma: no cover - acabou de ser gravado
        raise NotFound("Pedido não encontrado.")
    return created, True


def _find_by_idempotency_key(db: Session, customer_id: int, key: str) -> Order | None:
    order_id = db.scalar(
        select(Order.id).where(Order.customer_id == customer_id, Order.idempotency_key == key)
    )
    return _load_order(db, order_id) if order_id else None


# ---------------------------------------------------------------- mudanças de status


def apply_action(
    db: Session, order_id: int, action: OrderAction, user: User, reason: str | None = None
) -> tuple[Order, str]:
    # A linha do pedido fica travada: dois cliques simultâneos não aplicam a ação duas vezes.
    order = db.scalars(
        select(Order)
        .where(Order.id == order_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()
    if order is None or (user.role == Role.CUSTOMER and order.customer_id != user.id):
        raise NotFound("Pedido não encontrado.")

    transition = resolve(
        action, order.status, user.role, order.fulfillment, is_owner=order.customer_id == user.id
    )
    if transition.requires_reason and not reason:
        raise InvalidInput(
            "Informe o motivo para o cliente.", fields={"reason": "Informe o motivo."}
        )
    previous = order.status
    order.status = transition.to_status
    db.add(
        OrderStatusEvent(
            order_id=order.id,
            from_status=previous,
            to_status=transition.to_status,
            actor_id=user.id,
            actor_name=user.name,
            # Motivo só faz sentido (e só é exibido) em recusas e cancelamentos.
            note=reason if transition.to_status in VOIDED_STATUSES else None,
        )
    )
    if transition.restock:
        _restock(db, order.id)
    db.commit()

    updated = _load_order(db, order_id)
    if updated is None:  # pragma: no cover
        raise NotFound("Pedido não encontrado.")
    return updated, transition.message.format(id=order_id)


def _restock(db: Session, order_id: int) -> None:
    """Devolve ao estoque exatamente o que o pedido consumiu."""
    consumptions = db.scalars(
        select(OrderConsumption).where(OrderConsumption.order_id == order_id)
    ).all()
    if not consumptions:
        return
    by_ingredient = {c.ingredient_id: c.quantity for c in consumptions}
    ingredients = db.scalars(
        select(Ingredient)
        .where(Ingredient.id.in_(by_ingredient))
        .order_by(Ingredient.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    for ingredient in ingredients:
        ingredient.quantity += by_ingredient[ingredient.id]
    for consumption in consumptions:
        db.delete(consumption)


# ---------------------------------------------------------------- consultas


def _can_view(order: Order, user: User) -> bool:
    if user.role == Role.MANAGER:
        return True
    if user.role == Role.COOK:
        return order.status == OrderStatus.IN_PREPARATION
    return order.customer_id == user.id


def get_order(db: Session, order_id: int, user: User) -> Order:
    order = _load_order(db, order_id)
    if order is None or not _can_view(order, user):
        # 404 também para pedidos de outros clientes: não revela que o número existe.
        raise NotFound("Pedido não encontrado.")
    return order


def _scoped_query(user: User, filters: OrderFilters) -> Select[Order]:
    stmt = select(Order)
    statuses = list(filters.status)
    if user.role == Role.CUSTOMER:
        stmt = stmt.where(Order.customer_id == user.id)
    elif user.role == Role.COOK:
        # A cozinha só trabalha com a fila de preparo.
        statuses = [OrderStatus.IN_PREPARATION]
    if statuses:
        stmt = stmt.where(Order.status.in_(statuses))
    if filters.start:
        stmt = stmt.where(Order.created_at >= local_day_start_utc(filters.start))
    if filters.end:
        stmt = stmt.where(Order.created_at < local_day_end_utc(filters.end))
    if filters.q:
        term = filters.q.strip().lstrip("#")
        conditions = [Order.customer_name.contains(term, autoescape=True)]
        if term.isdigit():
            conditions.append(Order.id == int(term))
        stmt = stmt.where(or_(*conditions))
    return stmt


def list_orders(db: Session, user: User, filters: OrderFilters) -> OrderPage:
    base = _scoped_query(user, filters)
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    order_by = (
        (Order.created_at.asc(), Order.id.asc())
        if filters.sort == OrderSort.OLDEST
        else (Order.created_at.desc(), Order.id.desc())
    )
    orders = db.scalars(
        base.options(*ORDER_LOAD_OPTIONS)
        .order_by(*order_by)
        .offset((filters.page - 1) * filters.page_size)
        .limit(filters.page_size)
    ).all()
    return OrderPage(
        items=[to_out(o, user) for o in orders],
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=max(1, math.ceil(total / filters.page_size)),
    )


def status_counts(db: Session, user: User) -> dict[OrderStatus, int]:
    if user.role not in (Role.MANAGER, Role.COOK):
        raise Forbidden("Você não tem permissão para esta ação.")
    rows = db.execute(select(Order.status, func.count()).group_by(Order.status)).all()
    counts = dict.fromkeys(OrderStatus, 0)
    counts.update(dict(rows))
    if user.role == Role.COOK:
        return {OrderStatus.IN_PREPARATION: counts[OrderStatus.IN_PREPARATION]}
    return counts
