"""Registro do aceite da Política de Privacidade no cadastro do cliente.

Contas existentes ficam sem aceite registrado (nulo).

Revision ID: 797844a5a4d5
Revises: 3ea5d59ad102
Create Date: 2026-10-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "797844a5a4d5"
down_revision: str | None = "3ea5d59ad102"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("privacy_version", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("privacy_accepted_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "privacy_accepted_at")
    op.drop_column("users", "privacy_version")
