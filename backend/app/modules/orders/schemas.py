from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.validators import OptionalNote, UtcDateTime
from app.modules.orders.models import OrderStatus, PaymentMethod
from app.modules.orders.state_machine import OrderAction

# Limite por item no carrinho (sistema original: MAX_QUANTIDADE_ITEM = 20).
MAX_ITEM_QUANTITY = 20


class OrderItemIn(BaseModel):
    menu_item_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=MAX_ITEM_QUANTITY)
    notes: OptionalNote = Field(default=None, description='Ex.: "sem cebola"')


class OrderCreateIn(BaseModel):
    items: list[OrderItemIn] = Field(min_length=1, max_length=50)

    @field_validator("items")
    @classmethod
    def unique_items(cls, value: list[OrderItemIn]) -> list[OrderItemIn]:
        ids = [line.menu_item_id for line in value]
        if len(ids) != len(set(ids)):
            raise ValueError("Cada item do cardápio pode aparecer só uma vez no pedido.")
        return value


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    menu_item_id: int | None
    product_name: str
    unit_price: Decimal
    quantity: int
    subtotal: Decimal
    notes: str | None


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    method: PaymentMethod
    amount: Decimal
    paid_at: UtcDateTime


class OrderEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    from_status: OrderStatus | None
    to_status: OrderStatus
    actor_name: str | None
    note: str | None
    created_at: UtcDateTime


class OrderOut(BaseModel):
    id: int
    status: OrderStatus
    customer_id: int | None
    customer_name: str
    delivery_address: str | None
    total: Decimal
    created_at: UtcDateTime
    updated_at: UtcDateTime
    items: list[OrderItemOut]
    payment: PaymentOut | None
    status_reason: str | None = Field(
        default=None, description="Motivo da recusa ou do cancelamento, quando informado."
    )
    events: list[OrderEventOut] | None = Field(
        default=None, description="Linha do tempo (somente no detalhe do pedido)."
    )
    available_actions: list[OrderAction]


class OrderPage(BaseModel):
    items: list[OrderOut]
    total: int
    page: int
    page_size: int
    pages: int


class OrderActionIn(BaseModel):
    reason: OptionalNote = Field(
        default=None, description="Motivo (obrigatório para recusar, opcional para cancelar)"
    )


class OrderActionOut(BaseModel):
    order: OrderOut
    message: str


class OrderSummaryOut(BaseModel):
    counts: dict[OrderStatus, int]


class OrderSort(StrEnum):
    NEWEST = "newest"
    OLDEST = "oldest"


class OrderFilters(BaseModel):
    """Filtros da listagem (query string)."""

    status: list[OrderStatus] = Field(default_factory=list)
    start: date | None = Field(default=None, description="Data inicial (inclusive)")
    end: date | None = Field(default=None, description="Data final (inclusive)")
    q: Annotated[str | None, Field(max_length=100)] = Field(
        default=None, description="Nº do pedido ou nome do cliente"
    )
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort: OrderSort = OrderSort.NEWEST

    @model_validator(mode="after")
    def valid_period(self) -> "OrderFilters":
        if self.start and self.end and self.end < self.start:
            raise ValueError("A data final deve ser igual ou posterior à inicial.")
        return self
