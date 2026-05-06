from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    app_name: str = "Type Record"
    count_space: bool = True
    count_enter: bool = False
    backspace_decrements: bool = True
    refresh_interval_ms: int = 300
    session_timeout_seconds: int = 300
    tray_tooltip: str = "Type Record"
    start_hidden_to_tray: bool = True
    language: str = "en"
    weekly_output_target: int = 10000
    weekly_active_efficiency_target: float = 35.0

    @property
    def data_file(self) -> Path:
        appdata = os.environ.get("APPDATA")
        base_dir = Path(appdata) if appdata else Path.cwd()
        return base_dir / "TypeRecord" / "data" / "daily_counts.json"

    @property
    def settings_file(self) -> Path:
        appdata = os.environ.get("APPDATA")
        base_dir = Path(appdata) if appdata else Path.cwd()
        return base_dir / "TypeRecord" / "config" / "settings.json"

    @property
    def settings_backup_file(self) -> Path:
        return self.settings_file.with_suffix(f"{self.settings_file.suffix}.bak")

    @classmethod
    def load(cls) -> AppConfig:
        instance = cls()
        settings_path = instance._resolve_settings_path(instance.settings_file)
        backup_path = settings_path.with_suffix(f"{settings_path.suffix}.bak")
        data = instance._load_settings_json(settings_path)
        if data is None:
            data = instance._load_settings_json(backup_path)

        if isinstance(data, dict):
            for field_name in asdict(instance):
                if field_name in data:
                    setattr(instance, field_name, data[field_name])

        instance._normalize()
        instance._settings_path = settings_path
        instance._settings_backup_path = backup_path
        return instance

    def save(self) -> None:
        settings_path = self._resolve_settings_path(getattr(self, "_settings_path", self.settings_file))
        backup_path = getattr(self, "_settings_backup_path", settings_path.with_suffix(f"{settings_path.suffix}.bak"))
        payload = asdict(self)
        self._write_json_atomic(settings_path, payload)
        self._write_json_atomic(backup_path, payload)
        self._settings_path = settings_path
        self._settings_backup_path = backup_path

    def _resolve_settings_path(self, preferred_path: Path) -> Path:
        try:
            preferred_path.parent.mkdir(parents=True, exist_ok=True)
            test_file = preferred_path.parent / ".write_test.tmp"
            test_file.write_text("ok", encoding="utf-8")
            test_file.unlink(missing_ok=True)
            return preferred_path
        except OSError:
            fallback_path = Path.cwd() / "data" / "settings.json"
            fallback_path.parent.mkdir(parents=True, exist_ok=True)
            return fallback_path

    def _load_settings_json(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return None
        return data if isinstance(data, dict) else None

    def _normalize(self) -> None:
        defaults = type(self)()
        self.app_name = self._coerce_text(self.app_name, defaults.app_name)
        self.tray_tooltip = self._coerce_text(self.tray_tooltip, defaults.tray_tooltip)
        self.count_space = self._coerce_bool(self.count_space, defaults.count_space)
        self.count_enter = self._coerce_bool(self.count_enter, defaults.count_enter)
        self.backspace_decrements = self._coerce_bool(self.backspace_decrements, defaults.backspace_decrements)
        self.start_hidden_to_tray = self._coerce_bool(self.start_hidden_to_tray, defaults.start_hidden_to_tray)
        self.refresh_interval_ms = self._coerce_int(self.refresh_interval_ms, defaults.refresh_interval_ms, minimum=100, maximum=5000)
        self.session_timeout_seconds = self._coerce_int(self.session_timeout_seconds, defaults.session_timeout_seconds, minimum=60, maximum=86400)
        self.language = self.language if self.language in {"en", "zh"} else defaults.language
        self.weekly_output_target = self._coerce_int(self.weekly_output_target, defaults.weekly_output_target, minimum=0, maximum=1_000_000_000)
        self.weekly_active_efficiency_target = self._coerce_float(self.weekly_active_efficiency_target, defaults.weekly_active_efficiency_target, minimum=0.0, maximum=100000.0)

    def _coerce_text(self, value: object, default: str) -> str:
        return value if isinstance(value, str) and value.strip() else default

    def _coerce_bool(self, value: object, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"true", "1", "yes", "on"}:
                return True
            if normalized in {"false", "0", "no", "off"}:
                return False
        return default

    def _coerce_int(self, value: object, default: int, minimum: int, maximum: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    def _coerce_float(self, value: object, default: float, minimum: float, maximum: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    def _write_json_atomic(self, target: Path, payload: dict) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path = target.with_suffix(f"{target.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8", newline="") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, target)
