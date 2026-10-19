from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAt, Money, UpdatedAt, str_enum
from app.modules.inventory.models import Ingredient


class OrderStatus(StrEnum):
    AWAITING_ACCEPTANCE = "awaiting_acceptance"
    IN_PREPARATION = "in_preparation"
    OUT_FOR_DELIVERY = "out_for_delivery"
    COMPLETED = "completed"
    CANCELLED = "cancelled"  # pelo cliente
    REJECTED = "rejected"  # pela lanchonete


# Pedidos que não contam como venda (relatório) e cujo estoque foi devolvido.
VOIDED_STATUSES = frozenset({OrderStatus.CANCELLED, OrderStatus.REJECTED})


class PaymentMethod(StrEnum):
    PIX = "pix"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("customer_id", "idempotency_key"),
        Index("ix_orders_status_created_at", "status", "created_at"),
        Index("ix_orders_customer_id_created_at", "customer_id", "created_at"),
        Index("ix_orders_created_at", "created_at"),
        CheckConstraint("total > 0", name="total_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    customer_name: Mapped[str] = mapped_column(String(100))
    delivery_address: Mapped[str | None] = mapped_column(String(1100))
    status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus, "order_status"))
    total: Mapped[Money]
    idempotency_key: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[CreatedAt]
    updated_at: Mapped[UpdatedAt]

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OrderItem.id",
    )
    consumptions: Mapped[list["OrderConsumption"]] = relationship(
        cascade="all, delete-orphan", passive_deletes=True
    )
    payment: Mapped["Payment | None"] = relationship(
        back_populates="order", cascade="all, delete-orphan", passive_deletes=True
    )
    events: Mapped[list["OrderStatusEvent"]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="OrderStatusEvent.id",
    )


class OrderItem(Base):
    """Nome, preço e subtotal ficam gravados: mudar o cardápio não altera pedidos antigos."""

    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    menu_item_id: Mapped[int | None] = mapped_column(
        ForeignKey("menu_items.id", ondelete="SET NULL"), index=True
    )
    product_name: Mapped[str] = mapped_column(String(100))
    unit_price: Mapped[Money]
    quantity: Mapped[int] = mapped_column(Integer)
    subtotal: Mapped[Money]
    notes: Mapped[str | None] = mapped_column(String(255))

    order: Mapped[Order] = relationship(back_populates="items")


class OrderConsumption(Base):
    """Ingredientes consumidos pelo pedido (devolvidos ao estoque se for cancelado/recusado)."""

    __tablename__ = "order_consumptions"
    __table_args__ = (CheckConstraint("quantity > 0", name="quantity_positive"),)

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredients.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer)

    ingredient: Mapped[Ingredient] = relationship()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), unique=True)
    method: Mapped[PaymentMethod] = mapped_column(str_enum(PaymentMethod, "payment_method"))
    amount: Mapped[Money]
    paid_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    order: Mapped[Order] = relationship(back_populates="payment")


class OrderStatusEvent(Base):
    """Linha do tempo do pedido: cada mudança de status, com autor e horário."""

    __tablename__ = "order_status_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    from_status: Mapped[OrderStatus | None] = mapped_column(str_enum(OrderStatus, "order_status"))
    to_status: Mapped[OrderStatus] = mapped_column(str_enum(OrderStatus, "order_status"))
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    actor_name: Mapped[str | None] = mapped_column(String(100))
    # Motivo informado na recusa ou no cancelamento (mostrado ao cliente).
    note: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[CreatedAt]

    order: Mapped[Order] = relationship(back_populates="events")
