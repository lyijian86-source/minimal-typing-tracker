from __future__ import annotations

from type_record.metrics import (
    calculate_accuracy,
    calculate_four_week_average,
    calculate_keyboard_typed,
    calculate_peak_wpm_from_cpm,
    calculate_target_change,
    calculate_text_metrics,
    calculate_week_over_week_change,
    calculate_weekly_active_efficiency,
    calculate_weekly_active_minutes,
    calculate_weekly_output,
)


def test_text_metrics_exclude_paste_from_keyboard_accuracy() -> None:
    metrics = calculate_text_metrics(typed_total=120, pasted=20, backspace=10)

    assert metrics.typed_total == 120
    assert metrics.pasted == 20
    assert metrics.keyboard_typed == 100
    assert metrics.backspace == 10
    assert metrics.kept == 90
    assert metrics.accuracy == 0.9


def test_accuracy_is_clamped_when_backspace_exceeds_keyboard_typed() -> None:
    assert calculate_accuracy(keyboard_typed=5, backspace=10) == 0.0


def test_keyboard_typed_and_peak_wpm_helpers() -> None:
    assert calculate_keyboard_typed(positive_count=30, pasted_count=8) == 22
    assert calculate_keyboard_typed(positive_count=4, pasted_count=10) == 0
    assert calculate_peak_wpm_from_cpm(80) == 16.0


def test_weekly_output_active_time_and_efficiency_helpers() -> None:
    sessions = [{"duration_seconds": 120}, {"duration_seconds": 180}]

    assert calculate_weekly_output([100, 200, 50]) == 350
    assert calculate_weekly_active_minutes(sessions) == 5.0
    assert calculate_weekly_active_efficiency(350, 5.0) == 70.0
    assert calculate_weekly_active_efficiency(350, 0.0) is None


def test_weekly_comparison_helpers_cover_zero_baselines() -> None:
    zero_delta = calculate_week_over_week_change(0, 0)
    new_delta = calculate_week_over_week_change(10, 0)
    target_delta = calculate_target_change(80, 100)

    assert zero_delta.state == "ok"
    assert zero_delta.ratio == 0.0
    assert new_delta.state == "new"
    assert new_delta.ratio is None
    assert target_delta.state == "ok"
    assert target_delta.ratio == -0.2


def test_four_week_average_ignores_missing_values() -> None:
    assert calculate_four_week_average([10, None, 20, 30]) == 20.0
    assert calculate_four_week_average([None, None]) is None
