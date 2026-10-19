"""Importa todos os modelos para registrar as tabelas no metadata (usado pelo Alembic)."""

from app.modules.auth.models import AuthSession, LoginAttempt
from app.modules.catalog.models import Category, MenuItem, RecipeItem
from app.modules.inventory.models import Ingredient
from app.modules.orders.models import (
    Order,
    OrderConsumption,
    OrderItem,
    OrderStatusEvent,
    Payment,
)
from app.modules.store.models import OpeningHour, StoreSettings
from app.modules.users.models import CustomerAddress, User

__all__ = [
    "AuthSession",
    "Category",
    "CustomerAddress",
    "Ingredient",
    "LoginAttempt",
    "MenuItem",
    "OpeningHour",
    "Order",
    "OrderConsumption",
    "OrderItem",
    "OrderStatusEvent",
    "Payment",
    "RecipeItem",
    "StoreSettings",
    "User",
]
