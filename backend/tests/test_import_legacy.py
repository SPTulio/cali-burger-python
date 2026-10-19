"""Importação do banco do sistema PHP: carrega o esquema e os dados originais (arquivos SQL do
repositório PHP) no banco temporário `caliburger_legacy_test` e importa para o banco de teste."""

import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, make_url, select, text

from app.core.config import get_settings
from app.modules.catalog.models import MenuItem
from app.modules.inventory.models import Ingredient
from app.modules.orders.models import Order, OrderConsumption, OrderStatus
from app.modules.users.models import Role, User
from scripts.import_legacy import run_import
from tests.helpers import fresh

FIXTURES = Path(__file__).parent / "fixtures" / "legacy"
LEGACY_DB = "caliburger_legacy_test"


def _statements(sql: str) -> list[str]:
    without_comments = "\n".join(
        line for line in sql.splitlines() if not line.strip().startswith("--")
    )
    return [s.strip() for s in without_comments.split(";\n") if s.strip()]


@pytest.fixture
def legacy_url() -> Iterator[str]:
    url = make_url(get_settings().database_url)
    server = create_engine(url.set(database=None))
    with server.begin() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {LEGACY_DB}"))
        for name in ("01_schema.sql", "02_dados_exemplo.sql"):
            sql = (FIXTURES / name).read_text(encoding="utf-8")
            sql = re.sub(r"\bdb_caliburger\b", LEGACY_DB, sql)
            for statement in _statements(sql):
                # O PHP gravava a hora local; simula isso para conferir a conversão para UTC.
                conn.execute(
                    text(statement.replace("NOW()", "CONVERT_TZ(NOW(), '+00:00', '-03:00')"))
                )
    yield url.set(database=LEGACY_DB).render_as_string(hide_password=False)
    with server.begin() as conn:
        conn.execute(text(f"DROP DATABASE IF EXISTS {LEGACY_DB}"))
    server.dispose()


def test_import_from_the_php_database(legacy_url, db, make_api):
    report = run_import(legacy_url)

    assert report.counts == {
        "ingredientes": 10,
        "itens do cardápio": 8,
        "linhas de receita": 16,
        "clientes": 2,
        "balconistas": 1,
        "cozinheiros": 2,
        "pedidos": 9,
    }
    fresh(db)
    assert db.scalar(select(func.count()).select_from(MenuItem)) == 8
    assert db.scalar(select(Ingredient.quantity).where(Ingredient.name == "Pão Brioche")) == 110

    statuses = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    assert statuses == {
        OrderStatus.COMPLETED: 4,
        OrderStatus.CANCELLED: 1,
        OrderStatus.OUT_FOR_DELIVERY: 1,
        OrderStatus.IN_PREPARATION: 1,
        OrderStatus.AWAITING_ACCEPTANCE: 2,
    }
    order_8 = db.get(Order, 8)  # números dos pedidos são preservados
    assert order_8.customer_name == "João Silva"
    assert [(i.product_name, i.notes) for i in order_8.items] == [
        ("Cali Clássico", "Carne bem passada"),
        ("Água", None),
    ]
    assert order_8.items[0].unit_price == order_8.items[0].subtotal
    assert db.scalar(select(func.count()).where(OrderConsumption.order_id == 8)) == 6

    joao = db.scalar(select(User).where(User.username == "joao"))
    assert joao.address.city == "Curitiba"
    assert {
        o.customer_id for o in db.scalars(select(Order).where(Order.customer_name == "João Silva"))
    } == {joao.id}

    # As senhas do PHP ($2y$) continuam funcionando no novo sistema.
    make_api().login("joao", "123456")
    manager = make_api().login("352.658.110-01", "123456")
    assert manager.get("/api/v1/auth/me").json()["user"]["role"] == Role.MANAGER

    # Pedido pendente importado segue o fluxo normal (recusar devolve o estoque consumido).
    before = db.scalar(select(Ingredient.quantity).where(Ingredient.name == "Pão Brioche"))
    assert (
        manager.post(
            "/api/v1/orders/8/actions/reject", json={"reason": "Item em falta"}
        ).status_code
        == 200
    )
    fresh(db)
    after = db.scalar(select(Ingredient.quantity).where(Ingredient.name == "Pão Brioche"))
    assert after == before + 1


def test_import_converts_local_time_to_utc(legacy_url, db):
    run_import(legacy_url)
    fresh(db)
    with create_engine(legacy_url).connect() as legacy:
        local = legacy.execute(
            text("SELECT data_pedido FROM pedido WHERE numero_do_pedido = 9")
        ).scalar_one()
    imported = db.get(Order, 9).created_at
    hours = (imported - local).total_seconds() / 3600
    assert hours == pytest.approx(3, abs=0.01)  # São Paulo = UTC-3


def test_dry_run_writes_nothing(legacy_url, db):
    report = run_import(legacy_url, dry_run=True)
    assert report.counts["pedidos"] == 9
    fresh(db)
    assert db.scalar(select(func.count()).select_from(Order)) == 0


def test_refuses_to_import_into_a_database_with_data(legacy_url, db):
    from tests.helpers import make_customer

    make_customer(db)
    with pytest.raises(SystemExit):
        run_import(legacy_url)
