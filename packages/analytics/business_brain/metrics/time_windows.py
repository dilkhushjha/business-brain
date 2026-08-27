from dataclasses import dataclass
from datetime import date, timedelta


@dataclass(frozen=True)
class DateWindow:
    start: date
    end: date


def current_month(as_of: date) -> DateWindow:
    return DateWindow(as_of.replace(day=1), as_of)


def previous_month(as_of: date) -> DateWindow:
    first = as_of.replace(day=1)
    previous_end = first - timedelta(days=1)
    return DateWindow(previous_end.replace(day=1), previous_end)


def trailing_days(as_of: date, days: int) -> DateWindow:
    if days < 1:
        raise ValueError("days must be positive")
    return DateWindow(as_of - timedelta(days=days - 1), as_of)
