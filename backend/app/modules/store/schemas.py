from datetime import time
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.validators import OptionalNote, UtcDateTime


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
