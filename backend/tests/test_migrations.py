"""As migrações criam exatamente o esquema descrito pelos modelos e podem ser desfeitas."""

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import inspect, text

from alembic import command
from app.db.base import Base
from app.db.session import get_engine
from tests.conftest import alembic_config


def test_models_and_migrations_are_in_sync():
    with get_engine().connect() as connection:
        context = MigrationContext.configure(connection, opts={"compare_type": True})
        assert compare_metadata(context, Base.metadata) == []


def test_downgrade_and_upgrade_again():
    config = alembic_config()
    command.downgrade(config, "base")
    assert set(inspect(get_engine()).get_table_names()) == {"alembic_version"}

    command.upgrade(config, "head")
    tables = set(inspect(get_engine()).get_table_names())
    assert {"users", "orders", "menu_items", "ingredients", "order_status_events"} <= tables
    with get_engine().connect() as connection:
        names = connection.execute(text("SELECT name FROM categories ORDER BY position")).scalars()
        assert list(names) == ["Lanches", "Acompanhamentos", "Bebidas"]
