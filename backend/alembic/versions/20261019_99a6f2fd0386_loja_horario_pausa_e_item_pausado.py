"""Loja: horário de funcionamento, pausa de pedidos e item pausado.

Sem nenhuma faixa de horário cadastrada, a loja continua aberta o tempo todo (mesmo
comportamento de antes desta migração).

Revision ID: 99a6f2fd0386
Revises: 0c37c2b59602
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "99a6f2fd0386"
down_revision: str | None = "0c37c2b59602"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "opening_hours",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("opens_at", sa.Time(), nullable=False),
        sa.Column("closes_at", sa.Time(), nullable=False),
        sa.CheckConstraint("opens_at <> closes_at", name=op.f("ck_opening_hours_non_empty")),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name=op.f("ck_opening_hours_weekday_range")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_opening_hours")),
    )
    op.create_index(op.f("ix_opening_hours_weekday"), "opening_hours", ["weekday"], unique=False)

    store_settings = op.create_table(
        "store_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("is_paused", sa.Boolean(), nullable=False),
        sa.Column("pause_message", sa.String(length=255), nullable=True),
        sa.Column("prep_time_minutes", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("prep_time_minutes > 0", name=op.f("ck_store_settings_prep_time_positive")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_store_settings")),
    )
    op.bulk_insert(store_settings, [{"id": 1, "is_paused": False, "prep_time_minutes": 20}])

    op.add_column(
        "menu_items",
        sa.Column("is_paused", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("menu_items", "is_paused")
    op.drop_table("store_settings")
    op.drop_table("opening_hours")
