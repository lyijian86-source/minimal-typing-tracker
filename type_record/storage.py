from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from threading import Lock

from type_record.metrics import (
    WeeklyEfficiencyMetrics,
    calculate_four_week_average,
    calculate_keyboard_typed,
    calculate_target_change,
    calculate_text_metrics,
    calculate_week_over_week_change,
    calculate_weekly_active_efficiency,
    calculate_weekly_active_minutes,
    calculate_weekly_output,
)


@dataclass
class DailyCountStore:
    file_path: Path

    def __post_init__(self) -> None:
        self._lock = Lock()
        self.file_path = self._resolve_writable_path(self.file_path)
        self._load_health = self._empty_health_report()
        self._state = self._load()
        self._ensure_today_record()
        self._write_health_report()

    @property
    def data_dir(self) -> Path:
        return self.file_path.parent

    @property
    def backup_file_path(self) -> Path:
        return self.file_path.with_suffix(f"{self.file_path.suffix}.bak")

    @property
    def health_report_file_path(self) -> Path:
        return self.data_dir / "health_report.json"

    def get_today_count(self) -> int:
        with self._lock:
            self._ensure_today_record()
            return int(self._state["counts_by_date"][self._today_str()])

    def record_session(
        self,
        started_at: datetime,
        ended_at: datetime,
        delta: int,
        positive_count: int,
        pasted_count: int,
        backspace_count: int,
    ) -> None:
        with self._lock:
            self._ensure_today_record()
            day_key = started_at.date().isoformat()
            keyboard_typed = calculate_keyboard_typed(positive_count, pasted_count)
            duration_seconds = max(0, int((ended_at - started_at).total_seconds()))
            if keyboard_typed <= 0 and pasted_count <= 0 and backspace_count <= 0 and delta == 0:
                return

            sessions = self._state["sessions_by_date"].setdefault(day_key, [])
            metrics = calculate_text_metrics(positive_count, pasted_count, backspace_count)

            sessions.append(
                {
                    "started_at": started_at.isoformat(timespec="seconds"),
                    "ended_at": ended_at.isoformat(timespec="seconds"),
                    "duration_seconds": duration_seconds,
                    "delta": delta,
                    "typed": keyboard_typed,
                    "pasted": max(0, int(pasted_count)),
                    "backspace": max(0, int(backspace_count)),
                    "accuracy": metrics.accuracy,
                }
            )
            self._save()

    def record_key(
        self,
        delta: int,
        positive_count: int,
        backspace_count: int,
        pasted_count: int = 0,
        event_time: datetime | None = None,
        peak_wpm: float | None = None,
    ) -> int:
        with self._lock:
            self._ensure_today_record()
            today = self._today_str()
            current_value = int(self._state["counts_by_date"].get(today, 0))
            next_value = max(0, current_value + delta)
            self._state["counts_by_date"][today] = next_value

            if positive_count > 0:
                self._state["typed_by_date"][today] = int(self._state["typed_by_date"].get(today, 0)) + positive_count
            if pasted_count > 0:
                self._state["pasted_by_date"][today] = int(self._state["pasted_by_date"].get(today, 0)) + pasted_count
            if event_time is not None and positive_count > 0:
                hour_key = event_time.strftime("%H")
                keyboard_typed_count = calculate_keyboard_typed(positive_count, pasted_count)
                if keyboard_typed_count > 0:
                    self._increment_hour_bucket("hourly_typed_by_date", today, hour_key, keyboard_typed_count)
                if pasted_count > 0:
                    self._increment_hour_bucket("hourly_pasted_by_date", today, hour_key, pasted_count)
            if backspace_count > 0:
                self._state["backspace_by_date"][today] = int(self._state["backspace_by_date"].get(today, 0)) + backspace_count
            if peak_wpm is not None:
                current_peak = float(self._state["peak_wpm_by_date"].get(today, 0.0))
                self._state["peak_wpm_by_date"][today] = max(current_peak, float(peak_wpm))

            if event_time is not None:
                self._state["last_input_at"] = event_time.isoformat(timespec="seconds")
            self._save()
            return next_value

    def reset_today(self) -> None:
        with self._lock:
            self._ensure_today_record()
            today = self._today_str()
            self._state["counts_by_date"][today] = 0
            self._state["typed_by_date"][today] = 0
            self._state["pasted_by_date"][today] = 0
            self._state["backspace_by_date"][today] = 0
            self._state["peak_wpm_by_date"][today] = 0.0
            self._state["hourly_typed_by_date"][today] = {}
            self._state["hourly_pasted_by_date"][today] = {}
            self._state["sessions_by_date"][today] = []
            self._save()

    def get_recent_sessions(self, limit: int = 20) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            sessions: list[dict] = []
            raw_sessions = self._state.get("sessions_by_date", {})
            if isinstance(raw_sessions, dict):
                for day_key, items in raw_sessions.items():
                    if not isinstance(items, list):
                        continue
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        sessions.append(
                            {
                                "date": str(day_key),
                                "started_at": str(item.get("started_at", "")),
                                "ended_at": str(item.get("ended_at", "")),
                                "duration_seconds": max(0, int(item.get("duration_seconds", 0))),
                                "delta": int(item.get("delta", 0)),
                                "typed": max(0, int(item.get("typed", 0))),
                                "pasted": max(0, int(item.get("pasted", 0))),
                                "backspace": max(0, int(item.get("backspace", 0))),
                                "accuracy": max(0.0, float(item.get("accuracy", 0.0))),
                            }
                        )
            sessions.sort(key=lambda item: item["ended_at"], reverse=True)
            return sessions[:limit]

    def get_summary(self) -> dict:
        with self._lock:
            self._ensure_today_record()
            today = date.today()
            today_str = today.isoformat()
            yesterday_str = (today - timedelta(days=1)).isoformat()
            last_7_days_total = 0

            for offset in range(7):
                day_key = (today - timedelta(days=offset)).isoformat()
                last_7_days_total += int(self._state["counts_by_date"].get(day_key, 0))

            metrics = self._calculate_day_metrics(today_str)
            peak_wpm_today = float(self._state["peak_wpm_by_date"].get(today_str, 0.0))

            return {
                "today_count": int(self._state["counts_by_date"].get(today_str, 0)),
                "yesterday_count": int(self._state["counts_by_date"].get(yesterday_str, 0)),
                "last_7_days_total": last_7_days_total,
                "last_input_at": self._state.get("last_input_at"),
                "typed_today": metrics.keyboard_typed,
                "typed_total_today": metrics.typed_total,
                "pasted_today": metrics.pasted,
                "backspace_today": metrics.backspace,
                "kept_today": metrics.kept,
                "peak_wpm_today": peak_wpm_today,
                "accuracy": metrics.accuracy,
            }

    def get_weekly_efficiency(
        self,
        mode: str = "rolling",
        reference_date: str | None = None,
        output_target: int | None = None,
        active_efficiency_target: float | None = None,
    ) -> WeeklyEfficiencyMetrics:
        with self._lock:
            self._ensure_today_record()
            target_date = self._coerce_reference_date(reference_date)
            current_start, current_end = self._window_bounds(mode, target_date)
            previous_start, previous_end = self._previous_window_bounds(mode, current_start, current_end)
            baseline_windows = self._complete_calendar_baseline_windows(target_date, limit=4)

            current_metrics = self._aggregate_window(current_start, current_end)
            previous_metrics = self._aggregate_window(previous_start, previous_end)
            baseline_metrics = [self._aggregate_window(start, end) for start, end in baseline_windows]

            average_output = calculate_four_week_average([item["output"] for item in baseline_metrics])
            average_efficiency = calculate_four_week_average([item["active_efficiency"] for item in baseline_metrics])
            label = f"{current_start.isoformat()[5:]} - {current_end.isoformat()[5:]}"

            return WeeklyEfficiencyMetrics(
                mode=mode,
                label=label,
                start_date=current_start.isoformat(),
                end_date=current_end.isoformat(),
                output=current_metrics["output"],
                active_minutes=current_metrics["active_minutes"],
                active_efficiency=current_metrics["active_efficiency"],
                previous_output=previous_metrics["output"],
                previous_active_minutes=previous_metrics["active_minutes"],
                previous_active_efficiency=previous_metrics["active_efficiency"],
                output_vs_previous_week=calculate_week_over_week_change(current_metrics["output"], previous_metrics["output"]),
                active_efficiency_vs_previous_week=calculate_week_over_week_change(current_metrics["active_efficiency"], previous_metrics["active_efficiency"]),
                four_week_average_output=average_output,
                four_week_average_efficiency=average_efficiency,
                output_vs_four_week_average=calculate_week_over_week_change(current_metrics["output"], average_output),
                active_efficiency_vs_four_week_average=calculate_week_over_week_change(current_metrics["active_efficiency"], average_efficiency),
                output_target=output_target,
                active_efficiency_target=active_efficiency_target,
                output_vs_target=calculate_target_change(current_metrics["output"], output_target),
                active_efficiency_vs_target=calculate_target_change(current_metrics["active_efficiency"], active_efficiency_target),
            )

    def get_weekly_efficiency_history(
        self,
        mode: str = "rolling",
        weeks: int = 8,
        reference_date: str | None = None,
    ) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            target_date = self._coerce_reference_date(reference_date)
            history = []
            start_date, end_date = self._window_bounds(mode, target_date)
            for _ in range(max(1, weeks)):
                aggregate = self._aggregate_window(start_date, end_date)
                history.append(
                    {
                        "mode": mode,
                        "label": f"{start_date.isoformat()[5:]} - {end_date.isoformat()[5:]}",
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "output": aggregate["output"],
                        "active_minutes": aggregate["active_minutes"],
                        "active_efficiency": aggregate["active_efficiency"],
                    }
                )
                start_date, end_date = self._previous_window_bounds(mode, start_date, end_date)
            history.reverse()
            return history

    def get_recent_history(self, limit: int = 7) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            items = sorted(self._state["counts_by_date"].items(), reverse=True)
            history = []
            for day_key, count in items[:limit]:
                history.append(self._build_history_item(day_key, count))
            return history

    def get_trend_history(self, days: int = 30) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            today = date.today()
            history = []
            for offset in range(days - 1, -1, -1):
                day = today - timedelta(days=offset)
                day_key = day.isoformat()
                history.append(self._build_history_item(day_key, self._state["counts_by_date"].get(day_key, 0)))
            return history

    def get_full_history(self) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            history = []
            for day_key, count in sorted(self._state["counts_by_date"].items(), reverse=True):
                history.append(self._build_history_item(day_key, count))
            return history

    def get_hourly_distribution(self, day_key: str | None = None) -> list[dict]:
        with self._lock:
            self._ensure_today_record()
            target_day = day_key or self._today_str()
            typed_hours = self._state["hourly_typed_by_date"].get(target_day, {})
            pasted_hours = self._state["hourly_pasted_by_date"].get(target_day, {})
            distribution = []
            for hour in range(24):
                hour_key = f"{hour:02d}"
                typed = int(typed_hours.get(hour_key, 0))
                pasted = int(pasted_hours.get(hour_key, 0))
                distribution.append({
                    "hour": hour_key,
                    "typed": typed,
                    "pasted": pasted,
                    "total": typed + pasted,
                })
            return distribution

    def export_history_csv(self) -> Path:
        with self._lock:
            self._ensure_today_record()
            export_dir = self.data_dir / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = export_dir / f"typing_history_{timestamp}.csv"
            with export_path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["date", "count", "typed", "pasted", "backspace", "peak_wpm", "accuracy"])
                for day_key, count in sorted(self._state["counts_by_date"].items()):
                    metrics = self._calculate_day_metrics(day_key)
                    peak_wpm = float(self._state["peak_wpm_by_date"].get(day_key, 0.0))
                    writer.writerow([
                        day_key,
                        int(count),
                        metrics.keyboard_typed,
                        metrics.pasted,
                        metrics.backspace,
                        round(peak_wpm, 1),
                        round(metrics.accuracy, 4),
                    ])
            return export_path

    def _build_history_item(self, day_key: str, count: int) -> dict:
        metrics = self._calculate_day_metrics(day_key)
        return {
            "date": day_key,
            "count": int(count),
            "typed": metrics.keyboard_typed,
            "pasted": metrics.pasted,
            "backspace": metrics.backspace,
            "peak_wpm": float(self._state["peak_wpm_by_date"].get(day_key, 0.0)),
            "accuracy": metrics.accuracy,
        }

    def _aggregate_window(self, start_day: date, end_day: date) -> dict:
        day_counts = []
        sessions = []
        current_day = start_day
        while current_day <= end_day:
            day_key = current_day.isoformat()
            day_counts.append(int(self._state["counts_by_date"].get(day_key, 0)))
            sessions.extend(self._collect_sessions_for_day(day_key))
            current_day += timedelta(days=1)
        output = calculate_weekly_output(day_counts)
        active_minutes = calculate_weekly_active_minutes(sessions)
        active_efficiency = calculate_weekly_active_efficiency(output, active_minutes)
        return {
            "output": output,
            "active_minutes": active_minutes,
            "active_efficiency": active_efficiency,
        }

    def _window_bounds(self, mode: str, reference_day: date) -> tuple[date, date]:
        if mode == "calendar":
            start_day = reference_day - timedelta(days=reference_day.weekday())
            end_day = start_day + timedelta(days=6)
            return start_day, end_day
        end_day = reference_day
        start_day = end_day - timedelta(days=6)
        return start_day, end_day

    def _previous_window_bounds(self, mode: str, start_day: date, end_day: date) -> tuple[date, date]:
        if mode == "calendar":
            previous_end = start_day - timedelta(days=1)
            previous_start = previous_end - timedelta(days=6)
            return previous_start, previous_end
        previous_end = start_day - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)
        return previous_start, previous_end

    def _complete_calendar_baseline_windows(self, reference_day: date, limit: int) -> list[tuple[date, date]]:
        current_week_start = reference_day - timedelta(days=reference_day.weekday())
        baseline_end = current_week_start - timedelta(days=1)
        windows = []
        for _ in range(limit):
            start_day = baseline_end - timedelta(days=6)
            windows.append((start_day, baseline_end))
            baseline_end = start_day - timedelta(days=1)
        return windows

    def _collect_sessions_for_day(self, day_key: str) -> list[dict]:
        sessions = self._state.get("sessions_by_date", {}).get(day_key, [])
        return [item for item in sessions if isinstance(item, dict)]

    def _coerce_reference_date(self, reference_date: str | None) -> date:
        if not reference_date:
            return date.today()
        try:
            return date.fromisoformat(reference_date)
        except ValueError:
            return date.today()

    def _calculate_day_metrics(self, day_key: str):
        return calculate_text_metrics(
            typed_total=int(self._state["typed_by_date"].get(day_key, 0)),
            pasted=int(self._state["pasted_by_date"].get(day_key, 0)),
            backspace=int(self._state["backspace_by_date"].get(day_key, 0)),
        )

    def _today_str(self) -> str:
        return date.today().isoformat()

    def _resolve_writable_path(self, preferred_path: Path) -> Path:
        try:
            preferred_path.parent.mkdir(parents=True, exist_ok=True)
            return preferred_path
        except OSError:
            fallback_path = Path.cwd() / "data" / "daily_counts.json"
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            return fallback_path

    def _ensure_today_record(self) -> None:
        today = self._today_str()
        self._state.setdefault("counts_by_date", {})
        self._state.setdefault("typed_by_date", {})
        self._state.setdefault("pasted_by_date", {})
        self._state.setdefault("backspace_by_date", {})
        self._state.setdefault("peak_wpm_by_date", {})
        self._state.setdefault("hourly_typed_by_date", {})
        self._state.setdefault("hourly_pasted_by_date", {})
        self._state.setdefault("sessions_by_date", {})
        self._state["counts_by_date"].setdefault(today, 0)
        self._state["typed_by_date"].setdefault(today, 0)
        self._state["pasted_by_date"].setdefault(today, 0)
        self._state["backspace_by_date"].setdefault(today, 0)
        self._state["peak_wpm_by_date"].setdefault(today, 0.0)
        self._state["hourly_typed_by_date"].setdefault(today, {})
        self._state["hourly_pasted_by_date"].setdefault(today, {})
        self._state["sessions_by_date"].setdefault(today, [])

    def _load(self) -> dict:
        primary_status, data = self._read_json_source(self.file_path)
        backup_status = "not_used"
        self._load_health["source"] = "primary"
        self._load_health["primary_file_status"] = primary_status
        self._load_health["backup_file_status"] = backup_status

        if data is None:
            self._load_health["source"] = "backup"
            backup_status, data = self._read_json_source(self.backup_file_path)
            self._load_health["backup_file_status"] = backup_status

        if data is None:
            self._load_health["source"] = "empty"
            return self._empty_state()

        if "counts_by_date" not in data:
            self._load_health["source"] = "legacy"
            legacy_date = self._valid_day_key(data.get("date")) or self._today_str()
            legacy_count = self._safe_int(data.get("count", 0))
            return {
                "counts_by_date": {legacy_date: legacy_count},
                "typed_by_date": {legacy_date: legacy_count},
                "pasted_by_date": {legacy_date: 0},
                "backspace_by_date": {legacy_date: 0},
                "peak_wpm_by_date": {legacy_date: 0.0},
                "hourly_typed_by_date": {legacy_date: {}},
                "hourly_pasted_by_date": {legacy_date: {}},
                "sessions_by_date": {legacy_date: []},
                "last_input_at": None,
            }

        counts_by_date = {}
        typed_by_date = {}
        pasted_by_date = {}
        backspace_by_date = {}
        peak_wpm_by_date = {}
        hourly_typed_by_date = {}
        hourly_pasted_by_date = {}
        sessions_by_date = {}

        raw_counts = data.get("counts_by_date", {})
        if isinstance(raw_counts, dict):
            for day_key, value in raw_counts.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None:
                    counts_by_date[normalized_day] = self._safe_int(value)
                else:
                    self._increment_health("invalid_day_keys")

        raw_typed = data.get("typed_by_date", {})
        if isinstance(raw_typed, dict):
            for day_key, value in raw_typed.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None:
                    typed_by_date[normalized_day] = self._safe_int(value)
                else:
                    self._increment_health("invalid_day_keys")

        raw_pasted = data.get("pasted_by_date", {})
        if isinstance(raw_pasted, dict):
            for day_key, value in raw_pasted.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None:
                    pasted_by_date[normalized_day] = self._safe_int(value)
                else:
                    self._increment_health("invalid_day_keys")

        raw_backspace = data.get("backspace_by_date", {})
        if isinstance(raw_backspace, dict):
            for day_key, value in raw_backspace.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None:
                    backspace_by_date[normalized_day] = self._safe_int(value)
                else:
                    self._increment_health("invalid_day_keys")

        raw_peak_wpm = data.get("peak_wpm_by_date", {})
        if isinstance(raw_peak_wpm, dict):
            for day_key, value in raw_peak_wpm.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None:
                    peak_wpm_by_date[normalized_day] = self._safe_float(value)
                else:
                    self._increment_health("invalid_day_keys")

        raw_hourly_typed = data.get("hourly_typed_by_date", {})
        if isinstance(raw_hourly_typed, dict):
            for day_key, hours in raw_hourly_typed.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None and isinstance(hours, dict):
                    hourly_typed_by_date[normalized_day] = self._sanitize_hour_map(hours)
                elif normalized_day is None:
                    self._increment_health("invalid_day_keys")

        raw_hourly_pasted = data.get("hourly_pasted_by_date", {})
        if isinstance(raw_hourly_pasted, dict):
            for day_key, hours in raw_hourly_pasted.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is not None and isinstance(hours, dict):
                    hourly_pasted_by_date[normalized_day] = self._sanitize_hour_map(hours)
                elif normalized_day is None:
                    self._increment_health("invalid_day_keys")

        raw_sessions = data.get("sessions_by_date", {})
        if isinstance(raw_sessions, dict):
            for day_key, items in raw_sessions.items():
                normalized_day = self._valid_day_key(day_key)
                if normalized_day is None:
                    self._increment_health("invalid_day_keys")
                    continue
                if not isinstance(items, list):
                    self._increment_health("invalid_session_items")
                    continue
                sessions_by_date[normalized_day] = []
                for item in items:
                    session = self._sanitize_session_item(item)
                    if session is None:
                        self._increment_health("invalid_session_items")
                        continue
                    sessions_by_date[normalized_day].append(session)

        return {
            "counts_by_date": counts_by_date,
            "typed_by_date": typed_by_date,
            "pasted_by_date": pasted_by_date,
            "backspace_by_date": backspace_by_date,
            "peak_wpm_by_date": peak_wpm_by_date,
            "hourly_typed_by_date": hourly_typed_by_date,
            "hourly_pasted_by_date": hourly_pasted_by_date,
            "sessions_by_date": sessions_by_date,
            "last_input_at": self._load_last_input_at(data.get("last_input_at")),
        }

    def _empty_state(self) -> dict:
        return {
            "counts_by_date": {},
            "typed_by_date": {},
            "pasted_by_date": {},
            "backspace_by_date": {},
            "peak_wpm_by_date": {},
            "hourly_typed_by_date": {},
            "hourly_pasted_by_date": {},
            "sessions_by_date": {},
            "last_input_at": None,
        }

    def _increment_hour_bucket(self, state_key: str, day_key: str, hour_key: str, amount: int) -> None:
        day_hours = self._state[state_key].setdefault(day_key, {})
        day_hours[hour_key] = int(day_hours.get(hour_key, 0)) + amount

    def _valid_day_key(self, value: object) -> str | None:
        try:
            return date.fromisoformat(str(value)).isoformat()
        except (TypeError, ValueError):
            return None

    def _valid_hour_key(self, value: object) -> str | None:
        try:
            hour = int(value)
        except (TypeError, ValueError):
            return None
        if 0 <= hour <= 23:
            return f"{hour:02d}"
        return None

    def _sanitize_hour_map(self, hours: dict) -> dict:
        sanitized = {}
        for hour_key, value in hours.items():
            normalized_hour = self._valid_hour_key(hour_key)
            if normalized_hour is not None:
                sanitized[normalized_hour] = sanitized.get(normalized_hour, 0) + self._safe_int(value)
            else:
                self._increment_health("invalid_hour_keys")
        return sanitized

    def _safe_iso_datetime_text(self, value: object) -> str | None:
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            return datetime.fromisoformat(value).isoformat(timespec="seconds")
        except ValueError:
            return None

    def _sanitize_session_item(self, item: object) -> dict | None:
        if not isinstance(item, dict):
            return None
        started_at = self._safe_iso_datetime_text(item.get("started_at"))
        ended_at = self._safe_iso_datetime_text(item.get("ended_at"))
        if started_at is None or ended_at is None:
            return None
        if datetime.fromisoformat(ended_at) < datetime.fromisoformat(started_at):
            return None
        return {
            "started_at": started_at,
            "ended_at": ended_at,
            "duration_seconds": self._safe_int(item.get("duration_seconds", 0)),
            "delta": self._safe_signed_int(item.get("delta", 0)),
            "typed": self._safe_int(item.get("typed", 0)),
            "pasted": self._safe_int(item.get("pasted", 0)),
            "backspace": self._safe_int(item.get("backspace", 0)),
            "accuracy": self._safe_float(item.get("accuracy", 0.0), maximum=1.0),
        }

    def _load_last_input_at(self, value: object) -> str | None:
        normalized = self._safe_iso_datetime_text(value)
        if value is not None and normalized is None:
            self._increment_health("invalid_timestamps")
        return normalized

    def _empty_health_report(self) -> dict:
        return {
            "generated_at": None,
            "source": "primary",
            "primary_file_status": "not_checked",
            "backup_file_status": "not_checked",
            "invalid_day_keys": 0,
            "invalid_hour_keys": 0,
            "invalid_session_items": 0,
            "invalid_timestamps": 0,
        }

    def _increment_health(self, key: str, amount: int = 1) -> None:
        self._load_health[key] = int(self._load_health.get(key, 0)) + amount

    def _read_json_source(self, target: Path) -> tuple[str, dict | None]:
        if not target.exists():
            return "missing", None
        try:
            with target.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return "invalid", None
        if not isinstance(data, dict):
            return "invalid", None
        return "ok", data

    def _write_health_report(self) -> None:
        report = dict(self._load_health)
        report["generated_at"] = datetime.now().isoformat(timespec="seconds")
        payload = json.dumps(report, ensure_ascii=False, indent=2)
        self.health_report_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._write_json_atomic(self.health_report_file_path, payload)

    def _safe_int(self, value: object, default: int = 0) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    def _safe_signed_int(self, value: object, default: int = 0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _safe_float(self, value: object, default: float = 0.0, maximum: float | None = None) -> float:
        try:
            parsed = max(0.0, float(value))
        except (TypeError, ValueError):
            return default
        return min(maximum, parsed) if maximum is not None else parsed

    def _save(self) -> None:
        payload = json.dumps(self._state, ensure_ascii=False, indent=2)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to a temp file and atomically replace the target so an
        # interrupted save does not leave behind a truncated JSON file.
        self._write_json_atomic(self.file_path, payload)
        self._write_json_atomic(self.backup_file_path, payload)

    def _write_json_atomic(self, target: Path, payload: str) -> None:
        temp_path = target.with_suffix(f"{target.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8", newline="") as file:
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target)
