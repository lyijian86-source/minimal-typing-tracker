from __future__ import annotations

import ctypes
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
import tkinter.messagebox as messagebox
from pathlib import Path

from type_record.config import AppConfig
from type_record.counter import KeyboardCounter
from type_record.i18n import tr
from type_record.storage import DailyCountStore
from type_record.tray import TrayController
from type_record.ui import CounterWindow


def main() -> None:
    config = AppConfig.load()
    app_name = tr(config.language, "app_label")
    instance_guard = _SingleInstanceGuard.acquire("Local\\MinimalTypingTracker.TypeRecord")
    if instance_guard is None:
        messagebox.showinfo(app_name, tr(config.language, "already_running"))
        return

    store = DailyCountStore(config.data_file)
    logger = _configure_logging(store.data_dir)
    logger.info("Type Record starting")
    counter = KeyboardCounter(config=config, store=store)
    tray: TrayController | None = None

    def export_csv() -> None:
        try:
            export_path = store.export_history_csv()
            window.call_in_main_thread(lambda: window.show_export_message(tr(config.language, "exported", name=export_path.name)))
            _open_folder(str(export_path.parent))
        except Exception as exc:
            logger.exception("Failed to export history CSV")
            _show_error(tr(config.language, "export_failed", error=exc))

    try:
        counter.start()
    except Exception as exc:
        logger.exception("Failed to start keyboard listener")
        message = tr(config.language, "error_start_listener", error=exc)
        try:
            messagebox.showerror(app_name, message)
        finally:
            raise SystemExit(1) from exc

    def handle_language_changed(language: str) -> None:
        if tray is not None:
            tray.refresh_language(language)

    window = CounterWindow(
        config=config,
        store=store,
        counter=counter,
        on_export_csv=export_csv,
        on_language_changed=handle_language_changed,
    )

    def report_callback_exception(exc_type, exc_value, exc_traceback) -> None:
        logger.error("Unhandled Tkinter callback error", exc_info=(exc_type, exc_value, exc_traceback))

    window.root.report_callback_exception = report_callback_exception
    is_exiting = False

    def show_window() -> None:
        window.call_in_main_thread(window.show)

    def open_settings() -> None:
        window.call_in_main_thread(window.open_settings_dialog)

    def open_history() -> None:
        window.call_in_main_thread(window.open_history_dialog)

    def reset_today() -> None:
        def confirm_and_reset() -> None:
            should_reset = messagebox.askyesno(tr(config.language, "reset_title"), tr(config.language, "reset_confirm"))
            if not should_reset:
                return
            store.reset_today()
            counter.reset_session_stats()
            window.show()

        window.call_in_main_thread(confirm_and_reset)

    def open_data_folder() -> None:
        try:
            _open_folder(str(store.data_dir))
        except Exception as exc:
            logger.exception("Failed to open data folder")
            _show_error(tr(config.language, "open_folder_failed", path=store.data_dir, error=exc))

    def _open_folder(path: str) -> None:
        os.startfile(path)

    def _show_error(message: str) -> None:
        window.call_in_main_thread(lambda: messagebox.showerror(tr(config.language, "action_failed_title"), message))

    def exit_app() -> None:
        nonlocal is_exiting
        if is_exiting:
            return
        is_exiting = True
        logger.info("Type Record exiting")
        counter.stop()
        if tray is not None:
            tray.stop()
        instance_guard.close()
        window.call_in_main_thread(window.destroy)

    tray = TrayController(
        tooltip=tr(config.language, "app_label"),
        language=config.language,
        on_show=show_window,
        on_open_history=open_history,
        on_open_settings=open_settings,
        on_export_csv=export_csv,
        on_reset_today=reset_today,
        on_open_data_folder=open_data_folder,
        on_exit=exit_app,
    )
    tray.start()

    if config.start_hidden_to_tray:
        window.hide()

    def close_to_tray() -> None:
        window.hide()

    window.set_on_close(close_to_tray)

    try:
        window.run()
    except KeyboardInterrupt:
        exit_app()
        sys.exit(0)
    except Exception:
        logger.exception("Unexpected application error")
        exit_app()
        raise


def _configure_logging(data_dir: Path) -> logging.Logger:
    logger = logging.getLogger("type_record")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        log_dir = _resolve_log_dir(data_dir)
        try:
            handler = RotatingFileHandler(
                log_dir / "type_record.log",
                maxBytes=512 * 1024,
                backupCount=3,
                encoding="utf-8",
            )
        except OSError:
            # Logging should never prevent the tracker from starting.
            handler = logging.NullHandler()
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)

    return logger


def _resolve_log_dir(data_dir: Path) -> Path:
    preferred = data_dir / "logs"
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        return preferred
    except OSError:
        fallback = Path.cwd() / "data" / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


class _SingleInstanceGuard:
    _ERROR_ALREADY_EXISTS = 183

    def __init__(self, kernel32, handle: int) -> None:
        self._kernel32 = kernel32
        self._handle = handle

    @classmethod
    def acquire(cls, name: str) -> _SingleInstanceGuard | None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        handle = kernel32.CreateMutexW(None, False, name)
        if not handle:
            raise OSError(ctypes.get_last_error(), "CreateMutexW failed")
        if ctypes.get_last_error() == cls._ERROR_ALREADY_EXISTS:
            kernel32.CloseHandle(handle)
            return None
        return cls(kernel32, handle)

    def close(self) -> None:
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = 0
