"""Infraestrutura dos testes.

Os testes usam um MySQL de verdade, em um banco separado (TEST_DATABASE_URL, cujo nome
precisa terminar em "_test"). O esquema é criado pelas migrações do Alembic no início
da sessão e as tabelas são esvaziadas antes de cada teste.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import make_url, text
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, Settings, get_settings


def _configure_test_environment() -> None:
    url = os.environ.get("TEST_DATABASE_URL") or Settings().test_database_url  # type: ignore[call-arg]
    if not url:
        pytest.exit("Defina TEST_DATABASE_URL (veja backend/.env.example).", returncode=2)
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        pytest.exit(
            f"Por segurança, o banco de testes precisa terminar em '_test' (recebido: {database}).",
            returncode=2,
        )
    os.environ.update(
        {
            "DATABASE_URL": url,
            "ENVIRONMENT": "test",
            "BCRYPT_ROUNDS": "4",
            "MEDIA_DIR": tempfile.mkdtemp(prefix="caliburger-media-"),
            "LOG_LEVEL": "WARNING",
            "LOW_STOCK_THRESHOLD": "10",
            "CORS_ORIGINS": "",
        }
    )
    get_settings.cache_clear()


_configure_test_environment()

from app.db.session import get_engine, get_sessionmaker  # noqa: E402
from tests.helpers import Api  # noqa: E402

# Tabelas de referência criadas pela migração (store_settings é reiniciada, não apagada).
KEEP_TABLES = {"alembic_version", "categories", "store_settings"}


def alembic_config():  # type: ignore[no-untyped-def]
    from alembic.config import Config

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", get_settings().database_url.replace("%", "%%"))
    config.attributes["configure_logger"] = False
    return config


@pytest.fixture(scope="session", autouse=True)
def database_schema() -> Iterator[None]:
    from alembic import command

    config = alembic_config()
    command.downgrade(config, "base")
    command.upgrade(config, "head")
    yield
    shutil.rmtree(get_settings().media_dir, ignore_errors=True)


@pytest.fixture(autouse=True)
def clean_tables(database_schema: None) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        tables = [
            row[0]
            for row in conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = DATABASE()"
                )
            )
        ]
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in tables:
            if table not in KEEP_TABLES:
                conn.execute(text(f"DELETE FROM `{table}`"))  # noqa: S608 - nomes vindos do information_schema
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        conn.execute(
            text(
                "UPDATE store_settings SET is_paused = 0, pause_message = NULL, "
                "prep_time_minutes = 20"
            )
        )


@pytest.fixture
def db() -> Iterator[Session]:
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def media_dir() -> Path:
    return get_settings().media_dir


@pytest.fixture
def api() -> Iterator[Api]:
    from app.main import app

    with Api(app) as client:
        yield client


@pytest.fixture
def make_api() -> Iterator:  # type: ignore[type-arg]
    """Cria clientes HTTP independentes (cada um com seus cookies)."""
    from app.main import app

    clients: list[Api] = []

    def factory() -> Api:
        client = Api(app)
        client.__enter__()
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)


class Menu:
    """Cardápio pequeno usado pelos testes de pedidos e relatórios."""

    def __init__(self, db: Session) -> None:
        from tests.helpers import make_ingredient, make_item

        self.bread = make_ingredient(db, "Pão Brioche", 10)
        self.patty = make_ingredient(db, "Hambúrguer 180 g", 10)
        self.cheese = make_ingredient(db, "Queijo Cheddar", 10)
        self.soda = make_ingredient(db, "Refrigerante lata", 5)
        self.classic = make_item(
            db, "Cali Clássico", "22.00", {self.bread: 1, self.patty: 1, self.cheese: 1}
        )
        self.double = make_item(
            db, "Cali Duplo", "28.00", {self.bread: 1, self.patty: 2, self.cheese: 2}
        )
        self.soda_item = make_item(db, "Refrigerante", "8.00", {self.soda: 1}, category_id=3)
        self.water = make_item(db, "Água", "5.00", category_id=3)  # sem receita


@pytest.fixture
def menu(db: Session) -> Menu:
    return Menu(db)
