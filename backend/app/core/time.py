"""Datas: o banco guarda UTC (sem fuso); a apresentação usa o fuso configurado."""

from datetime import UTC, date, datetime, time, timedelta

from app.core.config import get_settings


def utcnow() -> datetime:
    """Agora em UTC, sem tzinfo (formato das colunas DATETIME)."""
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)


def local_day_start_utc(day: date) -> datetime:
    """Início (00:00) do dia no fuso da lanchonete, convertido para UTC sem tzinfo."""
    local = datetime.combine(day, time.min, tzinfo=get_settings().tz)
    return local.astimezone(UTC).replace(tzinfo=None)


def local_day_end_utc(day: date) -> datetime:
    """Início do dia seguinte (limite exclusivo) em UTC."""
    return local_day_start_utc(day + timedelta(days=1))


def local_utc_offset_minutes() -> int:
    """Deslocamento atual do fuso local em relação ao UTC (ex.: -180 em São Paulo)."""
    offset = datetime.now(get_settings().tz).utcoffset()
    return int(offset.total_seconds() // 60) if offset else 0


def local_today() -> date:
    return datetime.now(get_settings().tz).date()
