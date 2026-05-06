from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextMetrics:
    """Derived typing metrics with one shared interpretation."""

    typed_total: int
    pasted: int
    keyboard_typed: int
    backspace: int
    kept: int
    accuracy: float


@dataclass(frozen=True)
class ComparisonDelta:
    state: str
    ratio: float | None


@dataclass(frozen=True)
class WeeklyEfficiencyMetrics:
    mode: str
    label: str
    start_date: str
    end_date: str
    output: int
    active_minutes: float
    active_efficiency: float | None
    previous_output: int
    previous_active_minutes: float
    previous_active_efficiency: float | None
    output_vs_previous_week: ComparisonDelta
    active_efficiency_vs_previous_week: ComparisonDelta
    four_week_average_output: float | None
    four_week_average_efficiency: float | None
    output_vs_four_week_average: ComparisonDelta
    active_efficiency_vs_four_week_average: ComparisonDelta
    output_target: int | None
    active_efficiency_target: float | None
    output_vs_target: ComparisonDelta
    active_efficiency_vs_target: ComparisonDelta


def calculate_text_metrics(typed_total: int, pasted: int, backspace: int) -> TextMetrics:
    typed_total = _non_negative_int(typed_total)
    pasted = _non_negative_int(pasted)
    backspace = _non_negative_int(backspace)
    keyboard_typed = max(0, typed_total - pasted)
    kept = max(0, keyboard_typed - backspace)
    accuracy = calculate_accuracy(keyboard_typed, backspace)
    return TextMetrics(
        typed_total=typed_total,
        pasted=pasted,
        keyboard_typed=keyboard_typed,
        backspace=backspace,
        kept=kept,
        accuracy=accuracy,
    )


def calculate_accuracy(keyboard_typed: int, backspace: int) -> float:
    keyboard_typed = _non_negative_int(keyboard_typed)
    backspace = _non_negative_int(backspace)
    if keyboard_typed <= 0:
        return 0.0
    return max(0, keyboard_typed - backspace) / keyboard_typed


def calculate_keyboard_typed(positive_count: int, pasted_count: int) -> int:
    return max(0, _non_negative_int(positive_count) - _non_negative_int(pasted_count))


def calculate_peak_wpm_from_cpm(cpm: int) -> float:
    return _non_negative_int(cpm) / 5.0


def calculate_weekly_output(day_counts: list[int]) -> int:
    return sum(_non_negative_int(value) for value in day_counts)


def calculate_weekly_active_minutes(sessions: list[dict]) -> float:
    seconds = 0
    for session in sessions:
        if not isinstance(session, dict):
            continue
        seconds += _non_negative_int(session.get("duration_seconds", 0))
    return seconds / 60.0


def calculate_weekly_active_efficiency(output: int, active_minutes: float) -> float | None:
    output = _non_negative_int(output)
    try:
        active_minutes = max(0.0, float(active_minutes))
    except (TypeError, ValueError):
        return None
    if active_minutes <= 0:
        return None
    return output / active_minutes


def calculate_week_over_week_change(current: float | int | None, previous: float | int | None) -> ComparisonDelta:
    if current is None or previous is None:
        return ComparisonDelta(state="unavailable", ratio=None)
    current_value = float(current)
    previous_value = float(previous)
    if previous_value == 0:
        if current_value == 0:
            return ComparisonDelta(state="ok", ratio=0.0)
        return ComparisonDelta(state="new", ratio=None)
    return ComparisonDelta(state="ok", ratio=(current_value - previous_value) / previous_value)


def calculate_target_change(current: float | int | None, target: float | int | None) -> ComparisonDelta:
    if current is None or target is None:
        return ComparisonDelta(state="unavailable", ratio=None)
    current_value = float(current)
    target_value = float(target)
    if target_value <= 0:
        return ComparisonDelta(state="unavailable", ratio=None)
    return ComparisonDelta(state="ok", ratio=(current_value - target_value) / target_value)


def calculate_four_week_average(values: list[float | int | None]) -> float | None:
    filtered = [float(value) for value in values if value is not None]
    if not filtered:
        return None
    return sum(filtered) / len(filtered)


def _non_negative_int(value: int | float | str) -> int:
    return max(0, int(value))
