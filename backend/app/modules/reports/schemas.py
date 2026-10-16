from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator


class ReportQuery(BaseModel):
    start: date | None = Field(default=None, description="De (inclusive)")
    end: date | None = Field(default=None, description="Até (inclusive)")

    @model_validator(mode="after")
    def valid_period(self) -> "ReportQuery":
        if self.start and self.end and self.end < self.start:
            raise ValueError("A data final deve ser igual ou posterior à inicial.")
        return self


class SalesSummary(BaseModel):
    revenue: Decimal
    orders: int
    items_sold: int
    average_ticket: Decimal


class DailySales(BaseModel):
    date: date
    orders: int
    revenue: Decimal


class ProductDailySales(BaseModel):
    date: date
    product_name: str
    quantity: int
    unit_price: Decimal = Field(description="Valor médio por unidade no dia")
    total: Decimal


class ProductTotals(BaseModel):
    product_name: str
    quantity: int
    total: Decimal


class IngredientUsage(BaseModel):
    ingredient_id: int
    name: str
    quantity: int


class IngredientToBuy(BaseModel):
    ingredient_id: int
    name: str
    quantity: int


class SalesReport(BaseModel):
    start: date | None
    end: date | None
    low_stock_threshold: int
    summary: SalesSummary
    daily: list[DailySales]
    top_products: list[ProductTotals]
    sales_by_day: list[ProductDailySales]
    ingredients_used: list[IngredientUsage]
    ingredients_to_buy: list[IngredientToBuy]
