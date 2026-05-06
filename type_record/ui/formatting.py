from __future__ import annotations

from datetime import datetime

from type_record.i18n import tr
from type_record.metrics import ComparisonDelta


def today_date_str() -> str:
    return datetime.now().date().isoformat()


def format_last_input(language: str, last_input_at: str | None) -> str:
    if not last_input_at:
        return tr(language, "no_input")
    try:
        return datetime.fromisoformat(last_input_at).strftime("%H:%M:%S")
    except ValueError:
        return tr(language, "unknown")


def format_duration(seconds: int) -> str:
    seconds = max(0, seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours > 0 else f"{minutes:02d}:{secs:02d}"


def format_axis_value(value: int) -> str:
    if value >= 10000:
        return f"{value / 1000:.0f}k"
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)


def format_weekly_delta(language: str, delta: ComparisonDelta) -> str:
    if delta.state == "new":
        return tr(language, "weekly_new")
    if delta.ratio is None:
        return tr(language, "insufficient_history")
    sign = "+" if delta.ratio > 0 else ""
    return f"{sign}{delta.ratio * 100:.0f}%"
