"""Importa os dados do sistema PHP original (banco `db_caliburger`) para o novo esquema.

    python -m scripts.import_legacy --legacy-url "mysql+pymysql://user:senha@host:3306/db_caliburger"
    python -m scripts.import_legacy --legacy-url ... --images-dir <php>/public/imagens/lanches
    python -m scripts.import_legacy --legacy-url ... --dry-run

- O banco legado é apenas LIDO (transação somente leitura); nada é alterado nele.
- O banco de destino (DATABASE_URL) precisa estar migrado (`alembic upgrade head`) e sem dados.
- Tudo é gravado em uma única transação: se algo falhar, nada é importado.
- Mapeamento completo em docs/06-migracao-dados.md.
"""

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import bcrypt
from sqlalchemy import Connection, create_engine, func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.core.validators import only_digits
from app.db.session import get_sessionmaker
from app.modules.catalog.models import Category, MenuItem, RecipeItem
from app.modules.inventory.models import Ingredient
from app.modules.orders.models import (
    Order,
    OrderConsumption,
    OrderItem,
    OrderStatus,
    OrderStatusEvent,
    Payment,
    PaymentMethod,
)
from app.modules.users.models import CustomerAddress, Role, Sex, User

STATUS_MAP = {
    "Aguardando aceitação": OrderStatus.AWAITING_ACCEPTANCE,
    "Em preparação": OrderStatus.IN_PREPARATION,
    "A caminho": OrderStatus.OUT_FOR_DELIVERY,
    "Concluído": OrderStatus.COMPLETED,
    # O sistema antigo não distinguia cancelado (cliente) de recusado (loja).
    "Cancelado/recusado": OrderStatus.CANCELLED,
}
SEX_MAP = {"Masculino": Sex.MALE, "Feminino": Sex.FEMALE, "Outro": Sex.OTHER}
CENT = Decimal("0.01")


@dataclass
class ImportReport:
    counts: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def add(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount


def to_utc(value: datetime | None, legacy_tz: ZoneInfo) -> datetime | None:
    """O PHP gravava a hora local (America/Sao_Paulo); o novo sistema guarda UTC."""
    if value is None:
        return None
    return value.replace(tzinfo=legacy_tz).astimezone(UTC).replace(tzinfo=None)


def legacy_password(stored: str | None) -> str:
    """Hashes bcrypt do PHP ($2y$) são compatíveis; senhas antigas em texto puro viram hash."""
    stored = stored or ""
    if stored.startswith(("$2y$", "$2a$", "$2b$")):
        try:
            bcrypt.checkpw(b"verificacao", stored.encode())
            return stored
        except ValueError:
            pass
    if not stored:
        raise ValueError("senha vazia")
    return hash_password(stored)


def _rows(conn: Connection, sql: str) -> list[dict[str, Any]]:
    return [dict(r) for r in conn.execute(text(sql)).mappings()]


def run_import(
    legacy_url: str, *, images_dir: Path | None = None, dry_run: bool = False
) -> ImportReport:
    report = ImportReport()
    legacy_tz = get_settings().tz
    legacy_engine = create_engine(legacy_url)
    with legacy_engine.connect() as legacy, get_sessionmaker()() as db:
        legacy.execute(text("SET SESSION TRANSACTION READ ONLY"))
        _ensure_target_is_empty(db)
        try:
            ingredient_ids = _import_catalog(db, legacy, report, images_dir)
            customer_ids = _import_people(db, legacy, report)
            _import_orders(db, legacy, report, legacy_tz, customer_ids, ingredient_ids)
            if dry_run:
                db.rollback()
                report.warnings.append("Simulação (--dry-run): nada foi gravado.")
            else:
                db.commit()
        except Exception:
            db.rollback()
            raise
    legacy_engine.dispose()
    return report


def _ensure_target_is_empty(db: Session) -> None:
    for model in (User, MenuItem, Ingredient, Order):
        if db.scalar(select(func.count()).select_from(model)):
            raise SystemExit(
                f"O banco de destino já tem dados em '{model.__tablename__}'. "
                "A importação só roda em um banco recém-migrado."
            )


def _import_catalog(
    db: Session, legacy: Connection, report: ImportReport, images_dir: Path | None
) -> set[int]:
    categories = {c.name.lower(): c for c in db.scalars(select(Category))}
    category_map: dict[int, int] = {}
    for row in _rows(legacy, "SELECT id, nome FROM categoria ORDER BY id"):
        category = categories.get(row["nome"].lower())
        if category is None:
            category = Category(name=row["nome"], position=len(categories) + 1)
            db.add(category)
            db.flush()
            categories[row["nome"].lower()] = category
            report.add("categorias novas")
        category_map[row["id"]] = category.id

    ingredient_ids: set[int] = set()
    for row in _rows(legacy, "SELECT id_ingrediente, nome_ingrediente, quantidade FROM estoque"):
        db.add(
            Ingredient(
                id=row["id_ingrediente"],
                name=row["nome_ingrediente"].strip(),
                quantity=max(0, int(row["quantidade"])),
            )
        )
        ingredient_ids.add(row["id_ingrediente"])
        report.add("ingredientes")
    db.flush()

    media = get_settings().menu_media_dir
    for row in _rows(
        legacy, "SELECT id, nome, descricao, preco, imagem, categoria_id FROM cardapio"
    ):
        image_path = None
        if row["imagem"] and images_dir:
            source = images_dir / Path(row["imagem"]).name
            if source.is_file():
                media.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, media / source.name)
                image_path = f"menu/{source.name}"
            else:
                report.warnings.append(f"Imagem não encontrada: {source}")
        db.add(
            MenuItem(
                id=row["id"],
                name=row["nome"].strip(),
                description=(row["descricao"] or "").strip() or None,
                price=Decimal(row["preco"]),
                category_id=category_map[row["categoria_id"]],
                image_path=image_path,
            )
        )
        report.add("itens do cardápio")
    db.flush()

    for row in _rows(
        legacy, "SELECT id_cardapio, id_ingrediente, quantidade_utilizada FROM cardapio_ingrediente"
    ):
        db.add(
            RecipeItem(
                menu_item_id=row["id_cardapio"],
                ingredient_id=row["id_ingrediente"],
                quantity=row["quantidade_utilizada"],
            )
        )
        report.add("linhas de receita")
    db.flush()
    return ingredient_ids


def _import_people(db: Session, legacy: Connection, report: ImportReport) -> dict[int, int]:
    customer_ids: dict[int, int] = {}
    for row in _rows(legacy, "SELECT * FROM cliente ORDER BY id"):
        user = User(
            role=Role.CUSTOMER,
            username=row["login"],
            name=row["nome"],
            email=row["email"],
            cpf=only_digits(row["cpf"]),
            birth_date=row["data_nasc"],
            password_hash=legacy_password(row["senha"]),
            address=CustomerAddress(
                state=row["end_estado"],
                city=row["end_cidade"],
                district=row["end_bairro"],
                street=row["end_logradouro"],
            ),
        )
        db.add(user)
        db.flush()
        customer_ids[row["id"]] = user.id
        report.add("clientes")

    staff_cpfs: set[str] = set()
    for table, role in (("balconista_dono", Role.MANAGER), ("cozinheiro", Role.COOK)):
        for row in _rows(legacy, f"SELECT * FROM {table} ORDER BY nome"):  # noqa: S608 - tabela fixa
            cpf = only_digits(row["cpf"])
            if cpf in staff_cpfs:
                report.warnings.append(
                    f"CPF {cpf[:3]}.***.***-{cpf[-2:]} está em balconista e cozinheiro; "
                    "mantido apenas como balconista."
                )
                continue
            staff_cpfs.add(cpf)
            db.add(
                User(
                    role=role,
                    name=row["nome"],
                    email=row["email"],
                    cpf=cpf,
                    birth_date=row["data_nasc"],
                    sex=SEX_MAP.get(row["sexo"], Sex.OTHER),
                    password_hash=legacy_password(row["senha"]),
                )
            )
            report.add("balconistas" if role == Role.MANAGER else "cozinheiros")
    db.flush()
    return customer_ids


def _import_orders(
    db: Session,
    legacy: Connection,
    report: ImportReport,
    legacy_tz: ZoneInfo,
    customer_ids: dict[int, int],
    ingredient_ids: set[int],
) -> None:
    items_by_order: dict[int, list[dict[str, Any]]] = {}
    for row in _rows(legacy, "SELECT * FROM itens_pedido ORDER BY id"):
        items_by_order.setdefault(row["numero_do_pedido"], []).append(row)
    consumption_by_order: dict[int, list[dict[str, Any]]] = {}
    for row in _rows(legacy, "SELECT * FROM pedido_estoque"):
        consumption_by_order.setdefault(row["numero_do_pedido"], []).append(row)
    payments: dict[int, dict[str, Any]] = {}
    for row in _rows(legacy, "SELECT * FROM pagamento ORDER BY id_pagamento"):
        payments.setdefault(row["numero_do_pedido"], row)

    for row in _rows(legacy, "SELECT * FROM pedido ORDER BY numero_do_pedido"):
        number = row["numero_do_pedido"]
        status = STATUS_MAP.get(row["status"])
        if status is None:
            report.warnings.append(
                f"Pedido {number}: status desconhecido '{row['status']}', ignorado."
            )
            continue
        created_at = to_utc(row["data_pedido"], legacy_tz)
        items = []
        for item in items_by_order.get(number, []):
            quantity = int(item["quantidade"])
            subtotal = Decimal(item["valor"])
            items.append(
                OrderItem(
                    menu_item_id=item["id_cardapio"],
                    product_name=item["produto"],
                    unit_price=(subtotal / quantity).quantize(CENT),
                    quantity=quantity,
                    subtotal=subtotal,
                    notes=item["observacao"],
                )
            )
        payment_row = payments.get(number)
        db.add(
            Order(
                id=number,
                customer_id=customer_ids.get(row["id_cliente"]) if row["id_cliente"] else None,
                customer_name=row["nome_cliente"],
                delivery_address=None,  # o sistema antigo não guardava o endereço no pedido
                status=status,
                subtotal=Decimal(row["valor"]),
                delivery_fee=Decimal("0.00"),  # o sistema antigo não cobrava taxa de entrega
                total=Decimal(row["valor"]),
                created_at=created_at,
                updated_at=created_at,
                items=items,
                consumptions=[
                    OrderConsumption(ingredient_id=c["id_ingrediente"], quantity=c["quantidade"])
                    for c in consumption_by_order.get(number, [])
                    if c["id_ingrediente"] in ingredient_ids and c["quantidade"] > 0
                ],
                payment=Payment(
                    method=PaymentMethod.PIX,
                    amount=Decimal(payment_row["valor"]),
                    paid_at=to_utc(payment_row["data_hora"], legacy_tz),
                )
                if payment_row
                else None,
                # Sem histórico no sistema antigo: registra só o status atual.
                events=[
                    OrderStatusEvent(
                        from_status=None, to_status=status, actor_name=None, created_at=created_at
                    )
                ],
            )
        )
        report.add("pedidos")
    db.flush()


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--legacy-url", required=True, help="URL SQLAlchemy do banco PHP")
    parser.add_argument("--images-dir", type=Path, help="pasta public/imagens/lanches do PHP")
    parser.add_argument("--dry-run", action="store_true", help="simula sem gravar")
    args = parser.parse_args()

    report = run_import(args.legacy_url, images_dir=args.images_dir, dry_run=args.dry_run)
    for key, value in report.counts.items():
        print(f"{key}: {value}")
    for warning in report.warnings:
        print(f"AVISO: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
