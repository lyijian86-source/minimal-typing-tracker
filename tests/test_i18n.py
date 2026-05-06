from __future__ import annotations

from type_record.i18n import TRANSLATIONS, tr


def test_translation_keys_match_between_languages() -> None:
    assert set(TRANSLATIONS["en"]) == set(TRANSLATIONS["zh"])


def test_metric_explanation_texts_format_correctly() -> None:
    assert "90" in tr("en", "accuracy_hint", kept=90, typed=100)
    assert "100" in tr("zh", "accuracy_hint", kept=90, typed=100)
    assert tr("en", "metric_guide")
    assert tr("zh", "metric_guide")


def test_zh_primary_ui_labels_avoid_unnecessary_english() -> None:
    primary_keys = [
        "app_label",
        "export_csv",
        "last_minute",
        "peak_wpm_today",
        "history_columns_peak_wpm",
        "cpm_hint",
        "wpm_hint",
        "speed_hint",
        "lang_en",
        "lang_zh",
        "already_running",
    ]
    forbidden = ("CPM", "WPM", "CSV", "TYPE RECORD", "English", "Chinese")

    for key in primary_keys:
        text = tr("zh", key)
        assert not any(term in text for term in forbidden), key
