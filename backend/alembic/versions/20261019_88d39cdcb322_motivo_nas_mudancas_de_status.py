"""Motivo (recusa/cancelamento) registrado na linha do tempo do pedido.

Revision ID: 88d39cdcb322
Revises: 99a6f2fd0386
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "88d39cdcb322"
down_revision: str | None = "99a6f2fd0386"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("order_status_events", sa.Column("note", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("order_status_events", "note")
