"""Taxa de entrega por bairro, frete grátis e tempo estimado do pedido.

Pedidos existentes: subtotal = total e taxa = 0 (não havia taxa de entrega).

Revision ID: 3ea5d59ad102
Revises: 75c401dd69cb
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3ea5d59ad102"
down_revision: str | None = "75c401dd69cb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "delivery_zones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("fee", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("extra_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.CheckConstraint("extra_minutes >= 0", name=op.f("ck_delivery_zones_extra_minutes_non_negative")),
        sa.CheckConstraint("fee >= 0", name=op.f("ck_delivery_zones_fee_non_negative")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_zones")),
        sa.UniqueConstraint("name", name=op.f("uq_delivery_zones_name")),
    )

    # Colunas novas do pedido: criadas aceitando nulo, preenchidas e então obrigatórias.
    op.add_column("orders", sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column("orders", sa.Column("delivery_fee", sa.Numeric(precision=10, scale=2), nullable=True))
    op.execute("UPDATE orders SET subtotal = total, delivery_fee = 0")
    op.alter_column("orders", "subtotal", existing_type=sa.Numeric(10, 2), nullable=False)
    op.alter_column("orders", "delivery_fee", existing_type=sa.Numeric(10, 2), nullable=False)
    op.add_column("orders", sa.Column("eta_min_minutes", sa.Integer(), nullable=True))
    op.add_column("orders", sa.Column("eta_max_minutes", sa.Integer(), nullable=True))

    op.add_column(
        "store_settings",
        sa.Column("delivery_time_minutes", sa.Integer(), server_default="15", nullable=False),
    )
    op.add_column(
        "store_settings",
        sa.Column("default_delivery_fee", sa.Numeric(precision=10, scale=2), nullable=True),
    )
    op.add_column(
        "store_settings",
        sa.Column("free_delivery_above", sa.Numeric(precision=10, scale=2), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("store_settings", "free_delivery_above")
    op.drop_column("store_settings", "default_delivery_fee")
    op.drop_column("store_settings", "delivery_time_minutes")
    op.drop_column("orders", "eta_max_minutes")
    op.drop_column("orders", "eta_min_minutes")
    op.drop_column("orders", "delivery_fee")
    op.drop_column("orders", "subtotal")
    op.drop_table("delivery_zones")
