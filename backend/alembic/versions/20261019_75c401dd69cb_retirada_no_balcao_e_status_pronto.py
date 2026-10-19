"""Retirada no balcão (tipo do pedido), status "Pronto" e endereço de retirada da loja.

Pedidos existentes passam a ser do tipo "delivery" (o único que existia).

Revision ID: 75c401dd69cb
Revises: 88d39cdcb322
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "75c401dd69cb"
down_revision: str | None = "88d39cdcb322"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

OLD = ("awaiting_acceptance", "in_preparation", "out_for_delivery", "completed", "cancelled", "rejected")
NEW = ("awaiting_acceptance", "in_preparation", "ready", "out_for_delivery", "completed", "cancelled", "rejected")
STATUS_COLUMNS = (
    ("orders", "status", False),
    ("order_status_events", "from_status", True),
    ("order_status_events", "to_status", False),
)


def _alter_status(values: tuple[str, ...], previous: tuple[str, ...]) -> None:
    for table, column, nullable in STATUS_COLUMNS:
        op.alter_column(
            table,
            column,
            existing_type=sa.Enum(*previous, name="order_status"),
            type_=sa.Enum(*values, name="order_status"),
            existing_nullable=nullable,
        )


def upgrade() -> None:
    _alter_status(NEW, OLD)
    op.add_column(
        "orders",
        sa.Column(
            "fulfillment",
            sa.Enum("delivery", "pickup", name="order_fulfillment"),
            server_default="delivery",
            nullable=False,
        ),
    )
    op.add_column("store_settings", sa.Column("pickup_address", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("store_settings", "pickup_address")
    op.drop_column("orders", "fulfillment")
    # "Pronto" não existia: volta a "Em preparação" antes de reduzir o ENUM.
    op.execute("UPDATE orders SET status = 'in_preparation' WHERE status = 'ready'")
    op.execute("UPDATE order_status_events SET to_status = 'in_preparation' WHERE to_status = 'ready'")
    op.execute(
        "UPDATE order_status_events SET from_status = 'in_preparation' WHERE from_status = 'ready'"
    )
    _alter_status(OLD, NEW)
