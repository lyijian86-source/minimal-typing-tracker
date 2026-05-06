from __future__ import annotations

import json

from type_record.config import AppConfig


def test_config_load_normalizes_invalid_settings(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    settings_path = tmp_path / "TypeRecord" / "config" / "settings.json"
    settings_path.parent.mkdir(parents=True)
    settings_path.write_text(
        json.dumps(
            {
                "app_name": "",
                "count_space": "false",
                "count_enter": "yes",
                "backspace_decrements": "not-a-bool",
                "refresh_interval_ms": 1,
                "session_timeout_seconds": 999999,
                "start_hidden_to_tray": "off",
                "language": "fr",
                "weekly_output_target": "-20",
                "weekly_active_efficiency_target": "bad",
            }
        ),
        encoding="utf-8",
    )

    config = AppConfig.load()

    assert config.app_name == "Type Record"
    assert config.count_space is False
    assert config.count_enter is True
    assert config.backspace_decrements is True
    assert config.refresh_interval_ms == 100
    assert config.session_timeout_seconds == 86400
    assert config.start_hidden_to_tray is False
    assert config.language == "en"
    assert config.weekly_output_target == 0
    assert config.weekly_active_efficiency_target == 35.0


def test_config_save_writes_primary_and_backup(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("APPDATA", str(tmp_path))
    config = AppConfig.load()
    config.language = "zh"
    config.count_enter = True
    config.weekly_output_target = 12345
    config.weekly_active_efficiency_target = 42.5

    config.save()

    saved = json.loads(config.settings_file.read_text(encoding="utf-8"))
    backup = json.loads(config.settings_backup_file.read_text(encoding="utf-8"))
    assert saved["language"] == "zh"
    assert saved["count_enter"] is True
    assert saved["weekly_output_target"] == 12345
    assert saved["weekly_active_efficiency_target"] == 42.5
    assert backup == saved
