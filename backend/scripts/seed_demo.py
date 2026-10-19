"""Carrega DADOS DE DEMONSTRAÇÃO (cardápio, estoque, contas e pedidos fictícios).

    python -m scripts.seed_demo            # banco vazio
    python -m scripts.seed_demo --reset    # APAGA os dados atuais e recarrega a demonstração

Os pedidos são criados pelas mesmas regras da API (baixa de estoque, máquina de estados) e
depois têm as datas espalhadas pelos últimos dias, para o relatório ter o que mostrar.
Nunca roda com ENVIRONMENT=production.
"""

import argparse
import random
import shutil
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.core.time import utcnow
from app.db.session import get_engine, get_sessionmaker
from app.modules.catalog.models import Category, MenuItem, RecipeItem
from app.modules.inventory.models import Ingredient
from app.modules.orders import service as orders
from app.modules.orders.models import Fulfillment, Order
from app.modules.orders.schemas import OrderCreateIn
from app.modules.orders.state_machine import OrderAction
from app.modules.store.models import DeliveryZone, StoreSettings
from app.modules.users.models import CustomerAddress, Role, Sex, User

DEMO_PASSWORD = "cali1234"
ASSETS = Path(__file__).parent / "demo_assets" / "menu"

INGREDIENTS = {
    "Pão Brioche": 160,
    "Hambúrguer 180 g": 180,
    "Queijo Cheddar": 180,
    "Alface": 40,
    "Tomate": 70,
    "Bacon": 60,
    "Molho especial": 90,
    "Batata frita (porção)": 90,
    "Nugget de frango": 300,
    "Suco de uva (copo)": 25,
    "Refrigerante (copo)": 120,
    "Água mineral": 80,
}

# nome, descrição, preço, categoria, imagem, receita
MENU = [
    ("Cali Clássico", "Hambúrguer 180 g, cheddar, alface e tomate no pão brioche", "22.00",
     "Lanches", "cali_classico.webp",
     {"Pão Brioche": 1, "Hambúrguer 180 g": 1, "Queijo Cheddar": 1, "Alface": 1, "Tomate": 1}),
    ("Cali Duplo", "Dois hambúrgueres 180 g, cheddar duplo e pão brioche", "28.00",
     "Lanches", "cali_duplo.webp",
     {"Pão Brioche": 1, "Hambúrguer 180 g": 2, "Queijo Cheddar": 2}),
    ("X-Burger", "Hambúrguer 180 g com cheddar e molho especial", "20.00",
     "Lanches", "x_burger.webp",
     {"Pão Brioche": 1, "Hambúrguer 180 g": 1, "Queijo Cheddar": 1, "Molho especial": 1}),
    ("Cali Bacon", "Hambúrguer 180 g, cheddar, bacon crocante e molho especial", "31.00",
     "Lanches", "cali_bacon.webp",  # usada se o arquivo existir em demo_assets/menu
     {"Pão Brioche": 1, "Hambúrguer 180 g": 1, "Queijo Cheddar": 1, "Bacon": 2,
      "Molho especial": 1}),
    ("Cali Fritas", "Porção de batata frita (180 g)", "15.00",
     "Acompanhamentos", "cali_fritas.webp", {"Batata frita (porção)": 1}),
    ("Cali Nuggets", "10 nuggets de frango", "12.00",
     "Acompanhamentos", "cali_nugget.webp", {"Nugget de frango": 10}),
    ("Suco de Uva", "Copo de suco de uva (400 ml)", "8.00",
     "Bebidas", "suco_uva.webp", {"Suco de uva (copo)": 1}),
    ("Refrigerante", "Copo de refrigerante (400 ml)", "8.00",
     "Bebidas", "refrigerante.webp", {"Refrigerante (copo)": 1}),
    ("Água", "Garrafa de água mineral (500 ml)", "5.00",
     "Bebidas", "agua.webp", {"Água mineral": 1}),
]  # fmt: skip

CUSTOMERS = [
    ("joao", "João Silva", "28962080036", ("PR", "Curitiba", "Centro", "Rua XV de Novembro, 100")),
    ("maria", "Maria Souza", "10106081004", ("PR", "Curitiba", "Batel", "Avenida do Batel, 321")),
    ("pedro", "Pedro Lima", "52998224725", ("PR", "Curitiba", "Água Verde", "Rua Itiberê, 45")),
]  # fmt: skip

STAFF = [
    (Role.MANAGER, "Ana Ribeiro", "35265811001", Sex.FEMALE),
    (Role.COOK, "Carlos Souza", "21199625027", Sex.MALE),
    (Role.COOK, "Juliana Alves", "41368460020", Sex.FEMALE),
]

KEEP_TABLES = {"alembic_version", "categories", "store_settings"}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--reset", action="store_true", help="apaga os dados atuais antes")
    args = parser.parse_args()

    settings = get_settings()
    if settings.environment == "production":
        sys.exit("Recusado: ENVIRONMENT=production. Dados de demonstração não vão para produção.")

    with get_sessionmaker()() as db:
        has_data = db.scalar(select(func.count()).select_from(User)) or db.scalar(
            select(func.count()).select_from(MenuItem)
        )
        if has_data and not args.reset:
            sys.exit(
                "O banco já tem dados. Use --reset para apagar tudo e recarregar a demonstração."
            )

    if args.reset:
        _wipe()

    random.seed(2026)
    with get_sessionmaker()() as db:
        ingredients = _ingredients(db)
        items = _menu(db, ingredients)
        customers, manager, cooks = _people(db)
        _delivery(db)
        total = _orders(db, items, customers, manager, cooks)
        _adjust_stock_for_demo(db)
    print(
        f"Demonstração carregada: {len(items)} itens, {len(ingredients)} ingredientes, "
        f"{total} pedidos."
    )
    print(f"Senha de todas as contas: {DEMO_PASSWORD}")


def _wipe() -> None:
    with get_engine().begin() as conn:
        tables = conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()")
        ).scalars()
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in tables:
            if table not in KEEP_TABLES:
                conn.execute(text(f"DELETE FROM `{table}`"))  # noqa: S608 - nomes do information_schema
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        # Demonstração sem horário cadastrado: a loja fica aberta a qualquer hora.
        conn.execute(
            text(
                "UPDATE store_settings SET is_paused = 0, pause_message = NULL, "
                "prep_time_minutes = 20, "
                "pickup_address = 'Av. Sete de Setembro, 2775 - Rebouças, Curitiba (balcão)'"
            )
        )
    media = get_settings().menu_media_dir
    if media.exists():
        shutil.rmtree(media)


# Bairros atendidos: taxa e minutos extras de deslocamento. Fora deles, só retirada.
ZONES = [
    ("Centro", "5.00", 0),
    ("Rebouças", "5.00", 0),
    ("Batel", "6.50", 5),
    ("Água Verde", "7.00", 10),
]


def _delivery(db: Session) -> None:
    db.add_all(
        DeliveryZone(name=name, fee=Decimal(fee), extra_minutes=extra) for name, fee, extra in ZONES
    )
    settings = db.get(StoreSettings, 1)
    if settings:
        settings.free_delivery_above = Decimal("90.00")
    db.commit()


def _ingredients(db: Session) -> dict[str, Ingredient]:
    result = {name: Ingredient(name=name, quantity=qty) for name, qty in INGREDIENTS.items()}
    db.add_all(result.values())
    db.commit()
    return result


def _menu(db: Session, ingredients: dict[str, Ingredient]) -> list[MenuItem]:
    categories = {c.name: c.id for c in db.scalars(select(Category))}
    media = get_settings().menu_media_dir
    media.mkdir(parents=True, exist_ok=True)
    items = []
    for name, description, price, category, image, recipe in MENU:
        image_path = None
        if image and (ASSETS / image).exists():
            shutil.copyfile(ASSETS / image, media / image)
            image_path = f"menu/{image}"
        items.append(
            MenuItem(
                name=name,
                description=description,
                price=Decimal(price),
                category_id=categories[category],
                image_path=image_path,
                recipe=[
                    RecipeItem(ingredient_id=ingredients[i].id, quantity=q)
                    for i, q in recipe.items()
                ],
            )
        )
    db.add_all(items)
    db.commit()
    return items


def _people(db: Session) -> tuple[list[User], User, list[User]]:
    password = hash_password(DEMO_PASSWORD)
    customers = [
        User(
            role=Role.CUSTOMER,
            username=username,
            name=name,
            email=f"{username}@exemplo.com",
            cpf=cpf,
            birth_date=date(1990 + i * 3, 1 + i, 10),
            password_hash=password,
            address=CustomerAddress(state=a[0], city=a[1], district=a[2], street=a[3]),
        )
        for i, (username, name, cpf, a) in enumerate(CUSTOMERS)
    ]
    staff = [
        User(
            role=role,
            name=name,
            email=f"{name.split()[0].lower()}@caliburger.com",
            cpf=cpf,
            birth_date=date(1985 + i, 5, 10),
            sex=sex,
            password_hash=password,
        )
        for i, (role, name, cpf, sex) in enumerate(STAFF)
    ]
    db.add_all(customers + staff)
    db.commit()
    return customers, staff[0], staff[1:]


# Status final dos pedidos antigos (a maioria concluída).
HISTORY_OUTCOMES = ["completed"] * 8 + ["cancelled", "rejected"]
REJECT_REASONS = ["Item em falta", "Endereço fora da área de entrega", "Loja fechando"]
NOTES = [None, None, None, "Sem cebola", "Carne bem passada", "Sem tomate", "Molho à parte"]


def _orders(
    db: Session, items: list[MenuItem], customers: list[User], manager: User, cooks: list[User]
) -> int:
    burgers = [i for i in items if i.category_id == 1]
    sides_and_drinks = [i for i in items if i.category_id != 1]
    now = utcnow()
    plan: list[tuple[timedelta, str]] = []
    for days_ago in range(13, 0, -1):
        for _ in range(random.randint(2, 4)):
            moment = timedelta(
                days=days_ago, hours=random.randint(-2, 9), minutes=random.randint(0, 59)
            )
            plan.append((moment, random.choice(HISTORY_OUTCOMES)))
    # Pedidos de hoje em andamento, para as telas de operação.
    plan += [
        (timedelta(minutes=95), "completed"),
        (timedelta(minutes=50), "out_for_delivery"),
        (timedelta(minutes=40), "ready"),
        (timedelta(minutes=28), "in_preparation"),
        (timedelta(minutes=17), "in_preparation"),
        (timedelta(minutes=6), "awaiting_acceptance"),
        (timedelta(minutes=2), "awaiting_acceptance"),
    ]

    for ago, outcome in plan:
        customer = random.choice(customers)
        # Cerca de 1 em cada 4 pedidos é para retirada no balcão.
        pickup = outcome != "out_for_delivery" and random.random() < 0.25
        chosen = random.sample(burgers, k=random.randint(1, 2)) + random.sample(
            sides_and_drinks, k=random.randint(0, 2)
        )
        cart = OrderCreateIn(
            fulfillment=Fulfillment.PICKUP if pickup else Fulfillment.DELIVERY,
            items=[
                {
                    "menu_item_id": i.id,
                    "quantity": random.randint(1, 2),
                    "notes": random.choice(NOTES),
                }
                for i in chosen
            ],
        )
        order, _ = orders.create_order(db, customer, cart, None)
        cook = random.choice(cooks)
        prepared = [(OrderAction.ACCEPT, manager), (OrderAction.READY, cook)]
        finish = (
            [(OrderAction.PICK_UP, manager)]
            if pickup
            else [(OrderAction.DISPATCH, manager), (OrderAction.COMPLETE, customer)]
        )
        steps = {
            "awaiting_acceptance": [],
            "in_preparation": prepared[:1],
            "ready": prepared,
            "out_for_delivery": [*prepared, (OrderAction.DISPATCH, manager)],
            "completed": [*prepared, *finish],
            "cancelled": [(OrderAction.CANCEL, customer)],
            "rejected": [(OrderAction.REJECT, manager)],
        }[outcome]
        for action, actor in steps:
            reason = random.choice(REJECT_REASONS) if action == OrderAction.REJECT else None
            orders.apply_action(db, order.id, action, actor, reason)
        _backdate(db, order.id, now - ago)
    return len(plan)


def _backdate(db: Session, order_id: int, created_at: datetime) -> None:
    """Espalha as datas: cada mudança de status alguns minutos depois da anterior."""
    order = db.get(Order, order_id)
    if order is None:
        return
    order.created_at = created_at
    if order.payment:
        order.payment.paid_at = created_at
    # Nenhuma etapa pode ficar no futuro (pedidos recentes têm pouco tempo entre etapas).
    latest = utcnow() - timedelta(minutes=1)
    moment = created_at
    for event in order.events:
        event.created_at = min(moment, latest)
        moment += timedelta(minutes=random.randint(3, 25))
    order.updated_at = min(order.events[-1].created_at if order.events else created_at, latest)
    db.commit()


def _adjust_stock_for_demo(db: Session) -> None:
    """Deixa alguns ingredientes baixos/em falta, para a demonstração mostrar esses estados."""
    for name, quantity in {"Suco de uva (copo)": 0, "Alface": 6, "Bacon": 9}.items():
        ingredient = db.scalar(select(Ingredient).where(Ingredient.name == name))
        if ingredient:
            ingredient.quantity = quantity
    db.commit()


if __name__ == "__main__":
    main()
