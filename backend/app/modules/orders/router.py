from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.modules.auth.dependencies import CurrentUser, CustomerUser, DbSession, StaffUser
from app.modules.orders import service
from app.modules.orders.schemas import (
    OrderActionOut,
    OrderCreateIn,
    OrderFilters,
    OrderOut,
    OrderPage,
    OrderSummaryOut,
)
from app.modules.orders.state_machine import OrderAction

router = APIRouter(prefix="/orders", tags=["Pedidos"])

IdempotencyKey = Annotated[
    str | None,
    Header(
        alias="Idempotency-Key",
        min_length=8,
        max_length=64,
        pattern=r"^[A-Za-z0-9_-]+$",
        description="Identificador único da tentativa de compra; reenvios devolvem o mesmo pedido.",
    ),
]


@router.post(
    "",
    response_model=OrderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Finalizar pedido (pagamento PIX simulado)",
    responses={200: {"description": "Pedido já criado com a mesma Idempotency-Key"}},
)
def create_order(
    data: OrderCreateIn,
    customer: CustomerUser,
    db: DbSession,
    response: Response,
    idempotency_key: IdempotencyKey = None,
) -> OrderOut:
    order, created = service.create_order(db, customer, data, idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK
    return service.to_out(order, customer, with_events=True)


@router.get("", response_model=OrderPage, summary="Listar pedidos (escopo conforme o perfil)")
def list_orders(
    user: CurrentUser, db: DbSession, filters: Annotated[OrderFilters, Query()]
) -> OrderPage:
    return service.list_orders(db, user, filters)


@router.get("/summary", response_model=OrderSummaryOut, summary="Quantidade de pedidos por status")
def summary(user: StaffUser, db: DbSession) -> OrderSummaryOut:
    return OrderSummaryOut(counts=service.status_counts(db, user))


@router.get("/{order_id}", response_model=OrderOut, summary="Detalhe do pedido com linha do tempo")
def get_order(order_id: int, user: CurrentUser, db: DbSession) -> OrderOut:
    return service.to_out(service.get_order(db, order_id, user), user, with_events=True)


@router.post(
    "/{order_id}/actions/{action}",
    response_model=OrderActionOut,
    summary="Aceitar, recusar, enviar para entrega, cancelar ou confirmar recebimento",
)
def apply_action(
    order_id: int, action: OrderAction, user: CurrentUser, db: DbSession
) -> OrderActionOut:
    order, message = service.apply_action(db, order_id, action, user)
    return OrderActionOut(order=service.to_out(order, user, with_events=True), message=message)
