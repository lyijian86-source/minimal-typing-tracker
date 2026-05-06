from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from type_record.storage import DailyCountStore


def test_record_key_updates_today_summary_and_hourly_distribution(tmp_path) -> None:
    store = DailyCountStore(tmp_path / "daily_counts.json")
    event_time = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)

    store.record_key(delta=5, positive_count=5, backspace_count=0, event_time=event_time)
    store.record_key(delta=-1, positive_count=0, backspace_count=1, event_time=event_time)

    summary = store.get_summary()
    hourly = store.get_hourly_distribution()

    assert summary["today_count"] == 4
    assert summary["typed_today"] == 5
    assert summary["backspace_today"] == 1
    assert summary["kept_today"] == 4
    assert summary["accuracy"] == 0.8
    assert hourly[9]["typed"] == 5
    assert hourly[9]["total"] == 5


def test_pasted_input_is_counted_but_excluded_from_keyboard_typed(tmp_path) -> None:
    store = DailyCountStore(tmp_path / "daily_counts.json")
    event_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)

    store.record_key(delta=6, positive_count=6, pasted_count=6, backspace_count=0, event_time=event_time)

    summary = store.get_summary()
    hourly = store.get_hourly_distribution()

    assert summary["today_count"] == 6
    assert summary["typed_total_today"] == 6
    assert summary["typed_today"] == 0
    assert summary["pasted_today"] == 6
    assert hourly[10]["typed"] == 0
    assert hourly[10]["pasted"] == 6
    assert hourly[10]["total"] == 6


def test_corrupt_primary_json_loads_backup_and_sanitizes_values(tmp_path) -> None:
    data_path = tmp_path / "daily_counts.json"
    today = date.today().isoformat()
    data_path.write_text("{broken-json", encoding="utf-8")
    data_path.with_suffix(".json.bak").write_text(
        json.dumps(
            {
                "counts_by_date": {today: "12"},
                "typed_by_date": {today: "-3"},
                "pasted_by_date": {today: "bad"},
                "backspace_by_date": {today: "2"},
                "peak_wpm_by_date": {today: "80.5"},
                "hourly_typed_by_date": {today: {"09": "7"}},
                "hourly_pasted_by_date": {today: {"09": "1"}},
                "sessions_by_date": {today: []},
                "last_input_at": "2026-04-23T09:00:00",
            }
        ),
        encoding="utf-8",
    )

    store = DailyCountStore(data_path)
    summary = store.get_summary()
    hourly = store.get_hourly_distribution()
    health_report = json.loads(store.health_report_file_path.read_text(encoding="utf-8"))

    assert summary["today_count"] == 12
    assert summary["typed_today"] == 0
    assert summary["backspace_today"] == 2
    assert summary["peak_wpm_today"] == 80.5
    assert hourly[9]["typed"] == 7
    assert hourly[9]["pasted"] == 1
    assert health_report["source"] == "backup"
    assert health_report["primary_file_status"] == "invalid"
    assert health_report["backup_file_status"] == "ok"
    assert health_report["invalid_day_keys"] == 0


def test_load_filters_malformed_dates_hours_and_sessions(tmp_path) -> None:
    data_path = tmp_path / "daily_counts.json"
    valid_day = "2026-04-01"
    data_path.write_text(
        json.dumps(
            {
                "counts_by_date": {
                    valid_day: "20",
                    "not-a-date": "999",
                },
                "typed_by_date": {
                    valid_day: "25",
                    "2026-99-99": "999",
                },
                "pasted_by_date": {
                    valid_day: "5",
                    "bad": "999",
                },
                "backspace_by_date": {
                    valid_day: "3",
                    "2026-13-01": "999",
                },
                "peak_wpm_by_date": {
                    valid_day: "42.5",
                    "broken": "999",
                },
                "hourly_typed_by_date": {
                    valid_day: {
                        "09": "7",
                        "9": "2",
                        "24": "100",
                        "x": "100",
                    },
                    "invalid": {"09": "100"},
                },
                "hourly_pasted_by_date": {
                    valid_day: {
                        "10": "4",
                        "-1": "100",
                    },
                },
                "sessions_by_date": {
                    valid_day: [
                        {
                            "started_at": "2026-04-01T09:00:00",
                            "ended_at": "2026-04-01T09:05:00",
                            "duration_seconds": "300",
                            "delta": "10",
                            "typed": "12",
                            "pasted": "2",
                            "backspace": "1",
                            "accuracy": "0.9",
                        },
                        {
                            "started_at": "bad",
                            "ended_at": "2026-04-01T09:05:00",
                        },
                        {
                            "started_at": "2026-04-01T10:00:00",
                            "ended_at": "2026-04-01T09:00:00",
                        },
                    ],
                    "not-a-date": [
                        {
                            "started_at": "2026-04-01T09:00:00",
                            "ended_at": "2026-04-01T09:05:00",
                        }
                    ],
                },
                "last_input_at": "not-a-datetime",
            }
        ),
        encoding="utf-8",
    )

    store = DailyCountStore(data_path)
    history = store.get_full_history()
    hourly = store.get_hourly_distribution(valid_day)
    sessions = store.get_recent_sessions()
    health_report = json.loads(store.health_report_file_path.read_text(encoding="utf-8"))

    assert [item["date"] for item in history] == [date.today().isoformat(), valid_day]
    valid_history = next(item for item in history if item["date"] == valid_day)
    assert valid_history["count"] == 20
    assert valid_history["typed"] == 20
    assert valid_history["backspace"] == 3
    assert hourly[9]["typed"] == 9
    assert hourly[10]["pasted"] == 4
    assert hourly[23]["total"] == 0
    assert len(sessions) == 1
    assert sessions[0]["date"] == valid_day
    assert sessions[0]["duration_seconds"] == 300
    assert store.get_summary()["last_input_at"] is None
    assert health_report["source"] == "primary"
    assert health_report["primary_file_status"] == "ok"
    assert health_report["invalid_day_keys"] == 7
    assert health_report["invalid_hour_keys"] == 3
    assert health_report["invalid_session_items"] == 2
    assert health_report["invalid_timestamps"] == 1
    assert health_report["generated_at"]


def test_weekly_efficiency_rolling_window_aggregates_output_sessions_and_targets(tmp_path) -> None:
    data_path = tmp_path / "daily_counts.json"
    today = date.today()
    counts = {}
    typed = {}
    pasted = {}
    backspace = {}
    peak = {}
    hourly_typed = {}
    hourly_pasted = {}
    sessions = {}
    for offset in range(14):
        day_key = (today - timedelta(days=offset)).isoformat()
        counts[day_key] = offset + 1
        typed[day_key] = offset + 1
        pasted[day_key] = 0
        backspace[day_key] = 0
        peak[day_key] = 0.0
        hourly_typed[day_key] = {}
        hourly_pasted[day_key] = {}
        sessions[day_key] = [
            {
                "started_at": f"{day_key}T09:00:00",
                "ended_at": f"{day_key}T09:05:00",
                "duration_seconds": 300,
                "delta": offset + 1,
                "typed": offset + 1,
                "pasted": 0,
                "backspace": 0,
                "accuracy": 1.0,
            }
        ]
    data_path.write_text(
        json.dumps(
            {
                "counts_by_date": counts,
                "typed_by_date": typed,
                "pasted_by_date": pasted,
                "backspace_by_date": backspace,
                "peak_wpm_by_date": peak,
                "hourly_typed_by_date": hourly_typed,
                "hourly_pasted_by_date": hourly_pasted,
                "sessions_by_date": sessions,
                "last_input_at": None,
            }
        ),
        encoding="utf-8",
    )

    store = DailyCountStore(data_path)
    weekly = store.get_weekly_efficiency(mode="rolling", output_target=30, active_efficiency_target=5.0)
    history = store.get_weekly_efficiency_history(mode="rolling", weeks=4)

    assert weekly.output == sum(range(1, 8))
    assert weekly.active_minutes == 35.0
    assert weekly.active_efficiency == weekly.output / 35.0
    assert weekly.output_vs_target.ratio is not None
    assert len(history) == 4
    assert history[-1]["output"] == weekly.output


def test_weekly_efficiency_calendar_mode_uses_natural_week_boundaries(tmp_path) -> None:
    data_path = tmp_path / "daily_counts.json"
    reference = date(2026, 4, 26)
    monday = reference - timedelta(days=reference.weekday())
    counts = {}
    typed = {}
    pasted = {}
    backspace = {}
    peak = {}
    hourly_typed = {}
    hourly_pasted = {}
    sessions = {}
    for offset in range(21):
        day_key = (monday - timedelta(days=14) + timedelta(days=offset)).isoformat()
        counts[day_key] = 10
        typed[day_key] = 10
        pasted[day_key] = 0
        backspace[day_key] = 0
        peak[day_key] = 0.0
        hourly_typed[day_key] = {}
        hourly_pasted[day_key] = {}
        sessions[day_key] = [
            {
                "started_at": f"{day_key}T10:00:00",
                "ended_at": f"{day_key}T10:10:00",
                "duration_seconds": 600,
                "delta": 10,
                "typed": 10,
                "pasted": 0,
                "backspace": 0,
                "accuracy": 1.0,
            }
        ]
    data_path.write_text(
        json.dumps(
            {
                "counts_by_date": counts,
                "typed_by_date": typed,
                "pasted_by_date": pasted,
                "backspace_by_date": backspace,
                "peak_wpm_by_date": peak,
                "hourly_typed_by_date": hourly_typed,
                "hourly_pasted_by_date": hourly_pasted,
                "sessions_by_date": sessions,
                "last_input_at": None,
            }
        ),
        encoding="utf-8",
    )
    store = DailyCountStore(data_path)

    weekly = store.get_weekly_efficiency(mode="calendar", reference_date=reference.isoformat())

    assert weekly.start_date == monday.isoformat()
    assert weekly.end_date == (monday + timedelta(days=6)).isoformat()
    assert weekly.output == 70
    assert weekly.active_minutes == 70.0
