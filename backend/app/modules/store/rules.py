"""Regras puras de horário de funcionamento (sem banco), testadas isoladamente."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from itertools import pairwise


@dataclass(frozen=True)
class Interval:
    weekday: int  # 0 = segunda … 6 = domingo (datetime.weekday)
    opens_at: time
    closes_at: time

    @property
    def overnight(self) -> bool:
        return self.closes_at <= self.opens_at


def _occurrences(interval: Interval, around: datetime) -> Iterable[tuple[datetime, datetime]]:
    """Ocorrências concretas da faixa na semana anterior, atual e seguinte a `around`."""
    monday = (around - timedelta(days=around.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    for week in (-1, 0, 1):
        day = monday + timedelta(days=interval.weekday + 7 * week)
        start = datetime.combine(day.date(), interval.opens_at, tzinfo=around.tzinfo)
        end_day = day + timedelta(days=1) if interval.overnight else day
        end = datetime.combine(end_day.date(), interval.closes_at, tzinfo=around.tzinfo)
        yield start, end


def is_open(now: datetime, intervals: Iterable[Interval]) -> bool:
    """Sem nenhuma faixa cadastrada, a loja é considerada sempre aberta."""
    intervals = list(intervals)
    if not intervals:
        return True
    return any(
        start <= now < end for interval in intervals for start, end in _occurrences(interval, now)
    )


def next_opening(now: datetime, intervals: Iterable[Interval]) -> datetime | None:
    """Próximo horário de abertura depois de `now` (None se não houver faixas)."""
    starts = [
        start for interval in intervals for start, _ in _occurrences(interval, now) if start > now
    ]
    return min(starts, default=None)


def overlaps(intervals: list[Interval]) -> bool:
    """Faixas do mesmo dia que se sobrepõem (não detecta virada de dia entre dias diferentes)."""
    by_day: dict[int, list[Interval]] = {}
    for interval in intervals:
        by_day.setdefault(interval.weekday, []).append(interval)

    def minutes(t: time) -> int:
        return t.hour * 60 + t.minute

    for day_intervals in by_day.values():
        spans = sorted(
            (minutes(i.opens_at), minutes(i.closes_at) + (1440 if i.overnight else 0))
            for i in day_intervals
        )
        for (_, end), (next_start, _) in pairwise(spans):
            if next_start < end:
                return True
    return False
