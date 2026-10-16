"""Cliente HTTP de teste e fábricas de dados."""

import random
from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.modules.catalog.models import MenuItem, RecipeItem
from app.modules.inventory.models import Ingredient
from app.modules.users.models import CustomerAddress, Role, Sex, User

PASSWORD = "segredo123"


class Api(TestClient):
    """TestClient que envia o cabeçalho X-CSRF-Token automaticamente, como o frontend."""

    def __init__(self, app: Any) -> None:
        super().__init__(app, base_url="http://testserver")

    def request(self, method: str, url: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        csrf = self.cookies.get("cb_csrf")
        if csrf and method.upper() not in ("GET", "HEAD", "OPTIONS"):
            headers = dict(kwargs.pop("headers", None) or {})
            headers.setdefault("X-CSRF-Token", csrf)
            kwargs["headers"] = headers
        return super().request(method, url, **kwargs)

    def login(self, identifier: str, password: str = PASSWORD) -> "Api":
        response = self.post(
            "/api/v1/auth/login", json={"identifier": identifier, "password": password}
        )
        assert response.status_code == 200, response.text
        return self


def random_cpf() -> str:
    """CPF fictício que passa na validação dos dígitos verificadores."""
    while True:
        digits = [random.randint(0, 9) for _ in range(9)]
        for size in (9, 10):
            total = sum(d * (size + 1 - i) for i, d in enumerate(digits[:size]))
            digits.append(total * 10 % 11 % 10)
        cpf = "".join(map(str, digits))
        if len(set(cpf)) > 1:
            return cpf


def make_customer(
    db: Session, username: str = "joao", name: str = "João Silva", password: str = PASSWORD
) -> User:
    user = User(
        role=Role.CUSTOMER,
        username=username,
        name=name,
        email=f"{username}@exemplo.com",
        cpf=random_cpf(),
        birth_date=date(1990, 1, 1),
        password_hash=hash_password(password),
        address=CustomerAddress(
            state="PR", city="Curitiba", district="Centro", street="Rua XV de Novembro, 100"
        ),
    )
    db.add(user)
    db.commit()
    return user


def make_staff(
    db: Session, role: Role = Role.MANAGER, name: str = "Ana Ribeiro", cpf: str | None = None
) -> User:
    user = User(
        role=role,
        name=name,
        email="equipe@caliburger.com",
        cpf=cpf or random_cpf(),
        birth_date=date(1985, 1, 1),
        sex=Sex.FEMALE,
        password_hash=hash_password(PASSWORD),
    )
    db.add(user)
    db.commit()
    return user


def make_ingredient(db: Session, name: str, quantity: int) -> Ingredient:
    ingredient = Ingredient(name=name, quantity=quantity)
    db.add(ingredient)
    db.commit()
    return ingredient


def make_item(
    db: Session,
    name: str,
    price: str,
    recipe: dict[Ingredient, int] | None = None,
    category_id: int = 1,
) -> MenuItem:
    item = MenuItem(
        name=name,
        price=price,
        category_id=category_id,
        description=f"Descrição de {name}",
        recipe=[RecipeItem(ingredient_id=i.id, quantity=q) for i, q in (recipe or {}).items()],
    )
    db.add(item)
    db.commit()
    return item


def fresh(db: Session) -> None:
    """Encerra a transação e descarta o cache da sessão de teste: no REPEATABLE READ do
    MySQL, uma transação aberta veria um retrato antigo do banco, sem as mudanças da API."""
    db.commit()
    db.expire_all()


def stock(db: Session) -> dict[str, int]:
    fresh(db)
    return {i.name: i.quantity for i in db.query(Ingredient).all()}
