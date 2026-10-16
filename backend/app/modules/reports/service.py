"""Relatório de vendas por período. Pedidos cancelados ou recusados não entram."""

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import ColumnElement, Date, cast, func, literal_column, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import local_day_end_utc, local_day_start_utc, local_utc_offset_minutes
from app.modules.inventory.models import Ingredient
from app.modules.orders.models import VOIDED_STATUSES, Order, OrderConsumption, OrderItem
from app.modules.orders.service import money
from app.modules.reports.schemas import (
    DailySales,
    IngredientToBuy,
    IngredientUsage,
    ProductDailySales,
    ProductTotals,
    ReportQuery,
    SalesReport,
    SalesSummary,
)


def _order_filters(query: ReportQuery) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = [Order.status.not_in(VOIDED_STATUSES)]
    if query.start:
        conditions.append(Order.created_at >= local_day_start_utc(query.start))
    if query.end:
        # "Até" inclui o dia inteiro.
        conditions.append(Order.created_at < local_day_end_utc(query.end))
    return conditions


def _local_date() -> Any:
    """Data do pedido no fuso da lanchonete (o banco guarda UTC)."""
    offset = local_utc_offset_minutes()
    shifted = func.date_add(Order.created_at, literal_column(f"INTERVAL {int(offset)} MINUTE"))
    return cast(shifted, Date)


def sales_report(db: Session, query: ReportQuery) -> SalesReport:
    where = _order_filters(query)
    day = _local_date().label("day")

    orders_count, revenue = db.execute(
        select(func.count(Order.id), func.coalesce(func.sum(Order.total), 0)).where(*where)
    ).one()
    revenue = Decimal(revenue)

    daily_rows = db.execute(
        select(day, func.count(Order.id), func.sum(Order.total))
        .where(*where)
        .group_by(day)
        .order_by(day)
    ).all()

    by_day_rows = db.execute(
        select(
            day, OrderItem.product_name, func.sum(OrderItem.quantity), func.sum(OrderItem.subtotal)
        )
        .join(Order, Order.id == OrderItem.order_id)
        .where(*where)
        .group_by(day, OrderItem.product_name)
        .order_by(day.desc(), OrderItem.product_name)
    ).all()

    top_rows = db.execute(
        select(OrderItem.product_name, func.sum(OrderItem.quantity), func.sum(OrderItem.subtotal))
        .join(Order, Order.id == OrderItem.order_id)
        .where(*where)
        .group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.subtotal).desc(), OrderItem.product_name)
    ).all()

    # Consumo real registrado na hora do pedido.
    used_rows = db.execute(
        select(Ingredient.id, Ingredient.name, func.sum(OrderConsumption.quantity))
        .join(OrderConsumption, OrderConsumption.ingredient_id == Ingredient.id)
        .join(Order, Order.id == OrderConsumption.order_id)
        .where(*where)
        .group_by(Ingredient.id, Ingredient.name)
        .order_by(func.sum(OrderConsumption.quantity).desc(), Ingredient.name)
    ).all()

    threshold = get_settings().low_stock_threshold
    to_buy = db.scalars(
        select(Ingredient)
        .where(Ingredient.quantity <= threshold)
        .order_by(Ingredient.quantity, Ingredient.name)
    ).all()

    items_sold = sum(int(row[1]) for row in top_rows)
    return SalesReport(
        start=query.start,
        end=query.end,
        low_stock_threshold=threshold,
        summary=SalesSummary(
            revenue=money(revenue),
            orders=orders_count,
            items_sold=items_sold,
            average_ticket=money(revenue / orders_count) if orders_count else Decimal("0.00"),
        ),
        daily=[
            DailySales(date=_as_date(d), orders=n, revenue=money(Decimal(total)))
            for d, n, total in daily_rows
        ],
        top_products=[
            ProductTotals(product_name=name, quantity=int(qty), total=money(Decimal(total)))
            for name, qty, total in top_rows
        ],
        sales_by_day=[
            ProductDailySales(
                date=_as_date(d),
                product_name=name,
                quantity=int(qty),
                unit_price=money(Decimal(total) / int(qty)),
                total=money(Decimal(total)),
            )
            for d, name, qty, total in by_day_rows
        ],
        ingredients_used=[
            IngredientUsage(ingredient_id=i, name=name, quantity=int(qty))
            for i, name, qty in used_rows
        ],
        ingredients_to_buy=[
            IngredientToBuy(ingredient_id=i.id, name=i.name, quantity=i.quantity) for i in to_buy
        ],
    )


def _as_date(value: Any) -> date:
    return value if isinstance(value, date) else date.fromisoformat(str(value))
