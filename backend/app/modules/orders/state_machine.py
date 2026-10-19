"""Máquina de estados do pedido: quem pode executar cada ação, a partir de quais status,
para qual status vai e para que tipo de pedido (entrega ou retirada). Qualquer outra
combinação é recusada pelo servidor.

Entrega:  aguardando → em preparação → pronto → a caminho → concluído
Retirada: aguardando → em preparação → pronto → concluído (o balcão entrega ao cliente)
"""

from dataclasses import dataclass
from enum import StrEnum

from app.core.errors import BusinessRuleError, Forbidden
from app.modules.orders.models import Fulfillment, OrderStatus
from app.modules.users.models import Role


class OrderAction(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    READY = "ready"  # cozinha terminou o preparo
    DISPATCH = "dispatch"  # "saiu para entrega" (somente entrega)
    PICK_UP = "pick_up"  # cliente retirou no balcão (somente retirada)
    CANCEL = "cancel"
    COMPLETE = "complete"  # "recebi meu pedido" (somente entrega)


ALL_FULFILLMENTS = frozenset(Fulfillment)


@dataclass(frozen=True)
class Transition:
    roles: frozenset[Role]
    from_statuses: frozenset[OrderStatus]
    to_status: OrderStatus
    message: str
    restock: bool = False
    owner_only: bool = False
    requires_reason: bool = False
    fulfillments: frozenset[Fulfillment] = ALL_FULFILLMENTS


TRANSITIONS: dict[OrderAction, Transition] = {
    OrderAction.ACCEPT: Transition(
        roles=frozenset({Role.MANAGER}),
        from_statuses=frozenset({OrderStatus.AWAITING_ACCEPTANCE}),
        to_status=OrderStatus.IN_PREPARATION,
        message="Pedido nº {id} aceito e enviado para a cozinha.",
    ),
    OrderAction.REJECT: Transition(
        roles=frozenset({Role.MANAGER}),
        from_statuses=frozenset({OrderStatus.AWAITING_ACCEPTANCE}),
        to_status=OrderStatus.REJECTED,
        message="Pedido nº {id} recusado. Os ingredientes voltaram para o estoque.",
        restock=True,
        requires_reason=True,
    ),
    OrderAction.READY: Transition(
        roles=frozenset({Role.COOK, Role.MANAGER}),
        from_statuses=frozenset({OrderStatus.IN_PREPARATION}),
        to_status=OrderStatus.READY,
        message="Pedido nº {id} pronto.",
    ),
    OrderAction.DISPATCH: Transition(
        roles=frozenset({Role.MANAGER}),
        from_statuses=frozenset({OrderStatus.READY}),
        to_status=OrderStatus.OUT_FOR_DELIVERY,
        message="Pedido nº {id} saiu para entrega.",
        fulfillments=frozenset({Fulfillment.DELIVERY}),
    ),
    OrderAction.PICK_UP: Transition(
        roles=frozenset({Role.MANAGER}),
        from_statuses=frozenset({OrderStatus.READY}),
        to_status=OrderStatus.COMPLETED,
        message="Pedido nº {id} retirado pelo cliente.",
        fulfillments=frozenset({Fulfillment.PICKUP}),
    ),
    OrderAction.CANCEL: Transition(
        roles=frozenset({Role.CUSTOMER}),
        from_statuses=frozenset({OrderStatus.AWAITING_ACCEPTANCE}),
        to_status=OrderStatus.CANCELLED,
        message="Pedido nº {id} cancelado.",
        restock=True,
        owner_only=True,
    ),
    OrderAction.COMPLETE: Transition(
        roles=frozenset({Role.CUSTOMER}),
        from_statuses=frozenset({OrderStatus.OUT_FOR_DELIVERY}),
        to_status=OrderStatus.COMPLETED,
        message="Obrigado! Pedido nº {id} marcado como recebido.",
        owner_only=True,
        fulfillments=frozenset({Fulfillment.DELIVERY}),
    ),
}


def available_actions(
    status: OrderStatus, role: Role, fulfillment: Fulfillment, *, is_owner: bool
) -> list[OrderAction]:
    return [
        action
        for action, t in TRANSITIONS.items()
        if role in t.roles
        and status in t.from_statuses
        and fulfillment in t.fulfillments
        and (is_owner or not t.owner_only)
    ]


def resolve(
    action: OrderAction,
    status: OrderStatus,
    role: Role,
    fulfillment: Fulfillment,
    *,
    is_owner: bool,
) -> Transition:
    transition = TRANSITIONS[action]
    if role not in transition.roles or (transition.owner_only and not is_owner):
        raise Forbidden("Você não tem permissão para esta ação.")
    if fulfillment not in transition.fulfillments:
        kind = "retirada" if fulfillment == Fulfillment.PICKUP else "entrega"
        raise BusinessRuleError(
            f"Esta ação não se aplica a pedidos para {kind}.", code="invalid_transition"
        )
    if status not in transition.from_statuses:
        raise BusinessRuleError(
            "Este pedido não pode mais ser alterado. Atualize a lista.",
            code="invalid_transition",
        )
    return transition
