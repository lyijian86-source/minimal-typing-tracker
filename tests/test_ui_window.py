from __future__ import annotations

import tkinter as tk

import pytest

from type_record.config import AppConfig
from type_record.counter import KeyboardCounter
from type_record.i18n import tr
from type_record.storage import DailyCountStore
from type_record.ui.window import CounterWindow


def test_counter_window_builds_dashboard_layout(tmp_path) -> None:
    config = AppConfig(language="zh", refresh_interval_ms=5000)
    store = DailyCountStore(tmp_path / "daily_counts.json")
    counter = KeyboardCounter(config=config, store=store)
    window: CounterWindow | None = None

    try:
        window = CounterWindow(config, store, counter, lambda: None, lambda _language: None)
        window.root.withdraw()
        window.root.update_idletasks()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")

    try:
        assert window.root.title() == tr("zh", "app_label")
        assert window.root.winfo_width() >= 1120
        assert window.trend_canvas.winfo_exists()
        assert window._history_preview_canvas is not None
        assert window._history_preview_inner is not None
        assert window.weekly_output_var.get()
        assert window.weekly_efficiency_var.get()
    finally:
        window.destroy()


def test_settings_dialog_keeps_save_button_visible(tmp_path) -> None:
    config = AppConfig(language="zh", refresh_interval_ms=5000)
    store = DailyCountStore(tmp_path / "daily_counts.json")
    counter = KeyboardCounter(config=config, store=store)
    window: CounterWindow | None = None

    try:
        window = CounterWindow(config, store, counter, lambda: None, lambda _language: None)
        window.root.withdraw()
        window.open_settings_dialog()
        window.root.update_idletasks()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")

    try:
        dialogs = [child for child in window.root.winfo_children() if isinstance(child, tk.Toplevel)]
        assert dialogs
        dialog = dialogs[-1]
        save_buttons = _find_buttons_with_text(dialog, tr("zh", "save"))
        assert save_buttons
        assert _find_labels_with_text(dialog, tr("zh", "weekly_efficiency"))
        assert _find_labels_with_text(dialog, tr("zh", "weekly_output_target"))
        dialog_height = dialog.winfo_height()
        button = save_buttons[0]
        button_y = button.winfo_rooty() - dialog.winfo_rooty()
        assert 0 <= button_y < dialog_height
    finally:
        window.destroy()


def test_refresh_language_updates_window_title(tmp_path) -> None:
    config = AppConfig(language="en", refresh_interval_ms=5000)
    store = DailyCountStore(tmp_path / "daily_counts.json")
    counter = KeyboardCounter(config=config, store=store)
    window: CounterWindow | None = None

    try:
        window = CounterWindow(config, store, counter, lambda: None, lambda _language: None)
        window.root.withdraw()
        window.root.update_idletasks()
    except tk.TclError as exc:
        pytest.skip(f"Tk is not available in this environment: {exc}")

    try:
        assert window.root.title() == tr("en", "app_label")
        config.language = "zh"
        window.refresh_language()
        window.root.update_idletasks()
        assert window.root.title() == tr("zh", "app_label")
    finally:
        window.destroy()


def _find_buttons_with_text(widget: tk.Widget, text: str) -> list[tk.Button]:
    matches: list[tk.Button] = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Button) and child.cget("text") == text:
            matches.append(child)
        matches.extend(_find_buttons_with_text(child, text))
    return matches


def _find_labels_with_text(widget: tk.Widget, text: str) -> list[tk.Label]:
    matches: list[tk.Label] = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Label) and child.cget("text") == text:
            matches.append(child)
        matches.extend(_find_labels_with_text(child, text))
    return matches
