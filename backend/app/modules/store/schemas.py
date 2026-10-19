from datetime import time
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.core.validators import OptionalNote, Strip, UtcDateTime
from app.modules.orders.models import Fulfillment

Fee = Annotated[Decimal, Field(ge=0, le=999, decimal_places=2)]


class HourIn(BaseModel):
    weekday: int = Field(ge=0, le=6, description="0 = segunda … 6 = domingo")
    opens_at: time
    closes_at: time = Field(description="Se for menor ou igual à abertura, fecha no dia seguinte")

    @model_validator(mode="after")
    def not_empty(self) -> Self:
        if self.opens_at == self.closes_at:
            raise ValueError("O horário de fechamento deve ser diferente do de abertura.")
        return self


class HoursIn(BaseModel):
    hours: list[HourIn] = Field(max_length=50)


class HourOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int
    opens_at: time
    closes_at: time


class PauseIn(BaseModel):
    paused: bool
    message: OptionalNote = Field(
        default=None, description='Aviso mostrado aos clientes, ex.: "Voltamos às 20h"'
    )


class StoreSettingsIn(BaseModel):
    prep_time_minutes: int = Field(ge=1, le=240)
    pickup_address: OptionalNote = Field(
        default=None, description="Endereço para retirada no balcão (vazio = retirada desativada)"
    )
    delivery_time_minutes: int = Field(default=15, ge=0, le=180)
    default_delivery_fee: Fee | None = Field(
        default=None, description="Taxa para bairros fora da lista (vazio = só os bairros listados)"
    )
    free_delivery_above: Annotated[Decimal, Field(gt=0, le=99999, decimal_places=2)] | None = None


class StoreStatusOut(BaseModel):
    accepting_orders: bool = Field(description="Aberta pelo horário e sem pausa")
    within_hours: bool
    is_paused: bool
    pause_message: str | None
    message: str | None = Field(description="Aviso pronto para exibir quando não aceita pedidos")
    next_opening_at: UtcDateTime | None
    hours: list[HourOut]
    prep_time_minutes: int
    pickup_address: str | None = Field(description="Retirada no balcão disponível se preenchido")
    delivery_time_minutes: int
    default_delivery_fee: Decimal | None
    free_delivery_above: Decimal | None


class ZoneIn(BaseModel):
    name: Annotated[str, Strip, StringConstraints(min_length=1, max_length=100)]
    fee: Fee
    extra_minutes: int = Field(default=0, ge=0, le=180)
    is_active: bool = True


class ZonesIn(BaseModel):
    zones: list[ZoneIn] = Field(max_length=200)


class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    fee: Decimal
    extra_minutes: int
    is_active: bool


class QuoteOut(BaseModel):
    fulfillment: Fulfillment
    served: bool = Field(description="A loja entrega no bairro do cliente")
    message: str | None
    zone_name: str | None
    delivery_fee: Decimal | None = Field(description="None enquanto o bairro não é conhecido")
    free_delivery_above: Decimal | None
    eta_min_minutes: int
    eta_max_minutes: int
