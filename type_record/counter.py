from __future__ import annotations

import ctypes
from ctypes import wintypes
from collections import deque
from dataclasses import dataclass
from datetime import datetime
from threading import Event, Lock, Thread

import keyboard

from type_record.config import AppConfig
from type_record.metrics import calculate_accuracy, calculate_keyboard_typed, calculate_peak_wpm_from_cpm
from type_record.storage import DailyCountStore

CF_UNICODETEXT = 13
CLIPBOARD_POLL_INTERVAL_SECONDS = 0.2
HWND_MESSAGE = -3
WM_CLIPBOARDUPDATE = 0x031D
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002

LRESULT = ctypes.c_ssize_t
WNDPROC_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
WNDPROC = WNDPROC_FACTORY(LRESULT, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


IGNORED_KEYS = {
    "shift",
    "left shift",
    "right shift",
    "ctrl",
    "left ctrl",
    "right ctrl",
    "alt",
    "left alt",
    "right alt",
    "alt gr",
    "windows",
    "left windows",
    "right windows",
    "caps lock",
    "tab",
    "esc",
    "up",
    "down",
    "left",
    "right",
    "insert",
    "delete",
    "home",
    "end",
    "page up",
    "page down",
    "print screen",
    "menu",
}


@dataclass
class KeyboardCounter:
    config: AppConfig
    store: DailyCountStore

    def __post_init__(self) -> None:
        self._hook = None
        self._clipboard_thread: Thread | None = None
        self._clipboard_stop = Event()
        self._lock = Lock()
        self._session_started_at: datetime | None = None
        self._session_day_key: str | None = None
        self._session_delta = 0
        self._session_positive_count = 0
        self._session_pasted_count = 0
        self._session_backspace_count = 0
        self._last_input_at: datetime | None = None
        self._recent_positive_events: deque[datetime] = deque()
        self._last_clipboard_sequence: int | None = None
        self._last_counted_clipboard_sequence: int | None = None
        self._clipboard_hwnd = None
        self._clipboard_wndproc = None

    def start(self) -> None:
        if self._hook is not None:
            return
        self._hook = keyboard.on_press(self._handle_key_event, suppress=False)
        self._start_clipboard_monitor()

    def stop(self) -> None:
        self._stop_clipboard_monitor()
        if self._hook is None:
            return
        try:
            keyboard.unhook(self._hook)
        except KeyError:
            # The keyboard package may already have dropped the hook reference.
            # Treat stop as best-effort so shutdown can still flush session data.
            pass
        self._hook = None
        snapshot = None
        with self._lock:
            snapshot = self._snapshot_current_session(self._last_input_at or self._now())
            self._clear_session_state()
        if snapshot is not None:
            self.store.record_session(**snapshot)

    def get_live_stats(self) -> dict:
        snapshot = None
        with self._lock:
            now = self._now()
            snapshot = self._reset_session_if_day_changed(now)

            # A session should become durable when it times out, not only when
            # the next key arrives or the app exits. This keeps future session
            # analysis trustworthy during long background runs.
            if snapshot is None and self._is_session_expired(now):
                snapshot = self._snapshot_current_session(self._last_input_at or now)
                self._clear_session_state()

            self._trim_recent_events(now)
            session_typed_count = calculate_keyboard_typed(self._session_positive_count, self._session_pasted_count)
            session_is_active = self._is_session_active(now)
            session_duration_seconds = 0
            if self._session_started_at is not None:
                session_end = now if session_is_active else self._last_input_at
                if session_end is not None:
                    session_duration_seconds = max(0, int((session_end - self._session_started_at).total_seconds()))
            accuracy = calculate_accuracy(session_typed_count, self._session_backspace_count)
            stats = {
                "session_is_active": session_is_active,
                "session_duration_seconds": session_duration_seconds,
                "session_delta": self._session_delta,
                "session_positive_count": session_typed_count,
                "session_pasted_count": self._session_pasted_count,
                "session_backspace_count": self._session_backspace_count,
                "recent_cpm": len(self._recent_positive_events),
                "last_input_at": self._last_input_at.isoformat(timespec="seconds") if self._last_input_at else None,
                "session_accuracy": accuracy,
            }
        if snapshot is not None:
            self.store.record_session(**snapshot)
        return stats

    def reset_session_stats(self) -> None:
        with self._lock:
            self._clear_session_state()

    def _handle_key_event(self, event: keyboard.KeyboardEvent) -> None:
        key_name = (event.name or "").lower()
        if not key_name or key_name in IGNORED_KEYS:
            return

        paste_count = self._resolve_paste_count(key_name)
        if paste_count > 0:
            # Pasted text contributes to total text volume, but it should not
            # inflate typing speed metrics such as CPM or peak WPM.
            self._record_input(delta=paste_count, positive_count=paste_count, pasted_count=paste_count, backspace_count=0, count_for_speed=False)
            return

        delta = self._resolve_delta(key_name)
        is_backspace = key_name == "backspace"
        if delta > 0 and self._has_shortcut_modifier():
            # Ignore text-like keys while Ctrl/Alt/Win shortcuts are active.
            # This prevents combinations such as Ctrl+V/C/A or Win+R from being
            # miscounted as actual typed characters.
            return

        positive_count = delta if delta > 0 else 0
        backspace_count = 1 if is_backspace else 0

        if delta == 0 and backspace_count == 0:
            return

        self._record_input(delta=delta, positive_count=positive_count, pasted_count=0, backspace_count=backspace_count, count_for_speed=positive_count > 0)

    def _record_input(self, delta: int, positive_count: int, pasted_count: int, backspace_count: int, count_for_speed: bool) -> None:
        now = self._now()
        peak_wpm: float | None = None
        snapshot = None

        with self._lock:
            snapshot = self._ensure_active_session(now)
            self._session_delta += delta
            self._last_input_at = now
            if positive_count > 0:
                self._session_positive_count += positive_count
                self._session_pasted_count += pasted_count
                if count_for_speed:
                    for _ in range(positive_count):
                        self._recent_positive_events.append(now)
            if backspace_count > 0:
                self._session_backspace_count += backspace_count
            self._trim_recent_events(now)
            if positive_count > 0 and count_for_speed:
                peak_wpm = calculate_peak_wpm_from_cpm(len(self._recent_positive_events))

        if snapshot is not None:
            self.store.record_session(**snapshot)
        self.store.record_key(
            delta=delta,
            positive_count=positive_count,
            backspace_count=backspace_count,
            pasted_count=pasted_count,
            event_time=now,
            peak_wpm=peak_wpm,
        )

    def _trim_recent_events(self, now: datetime | None = None) -> None:
        now = now or self._now()
        while self._recent_positive_events and (now - self._recent_positive_events[0]).total_seconds() > 60:
            self._recent_positive_events.popleft()

    def _ensure_active_session(self, now: datetime) -> dict | None:
        snapshot = self._reset_session_if_day_changed(now)
        if self._session_started_at is None:
            self._start_new_session(now)
            return snapshot
        if self._is_session_expired(now):
            expired_snapshot = self._snapshot_current_session(self._last_input_at or now)
            self._start_new_session(now)
            return expired_snapshot or snapshot
        return snapshot

    def _start_new_session(self, now: datetime) -> None:
        self._session_started_at = now
        self._session_day_key = now.date().isoformat()
        self._session_delta = 0
        self._session_positive_count = 0
        self._session_pasted_count = 0
        self._session_backspace_count = 0
        self._recent_positive_events.clear()

    def _reset_session_if_day_changed(self, now: datetime) -> dict | None:
        if self._session_day_key is None:
            return None
        if self._session_day_key == now.date().isoformat():
            return None

        # Session metrics are presented as "today/current session" context.
        # Once the day changes, carrying yesterday's runtime session into the
        # new day makes the numbers hard to interpret, so we start fresh.
        snapshot = self._snapshot_current_session(self._last_input_at or now)
        self._clear_session_state()
        return snapshot

    def _is_session_active(self, now: datetime) -> bool:
        return self._session_started_at is not None and not self._is_session_expired(now)

    def _is_session_expired(self, now: datetime) -> bool:
        if self._last_input_at is None:
            return False
        return (now - self._last_input_at).total_seconds() >= self.config.session_timeout_seconds

    def _now(self) -> datetime:
        return datetime.now()

    def _snapshot_current_session(self, ended_at: datetime) -> dict | None:
        if self._session_started_at is None:
            return None
        keyboard_typed = calculate_keyboard_typed(self._session_positive_count, self._session_pasted_count)
        if keyboard_typed <= 0 and self._session_pasted_count <= 0 and self._session_backspace_count <= 0 and self._session_delta == 0:
            return None
        return {
            "started_at": self._session_started_at,
            "ended_at": ended_at,
            "delta": self._session_delta,
            "positive_count": self._session_positive_count,
            "pasted_count": self._session_pasted_count,
            "backspace_count": self._session_backspace_count,
        }

    def _clear_session_state(self) -> None:
        self._session_started_at = None
        self._session_day_key = None
        self._session_delta = 0
        self._session_positive_count = 0
        self._session_pasted_count = 0
        self._session_backspace_count = 0
        self._last_input_at = None
        self._recent_positive_events.clear()

    def _resolve_delta(self, key_name: str) -> int:
        if len(key_name) == 1:
            return 1

        if key_name == "space":
            return 1 if self.config.count_space else 0

        if key_name == "enter":
            return 1 if self.config.count_enter else 0

        if key_name == "backspace":
            return -1 if self.config.backspace_decrements else 0

        return 0

    def _has_shortcut_modifier(self) -> bool:
        ctrl_pressed = self._is_pressed("ctrl", "left ctrl", "right ctrl")
        win_pressed = self._is_pressed("windows", "left windows", "right windows")

        # AltGr is commonly represented as Ctrl+Alt on Windows keyboard hooks.
        # Keep it out of the shortcut filter so layouts that rely on AltGr do
        # not lose valid character counts.
        alt_gr_pressed = self._is_pressed("alt gr")
        alt_pressed = self._is_pressed("alt", "left alt", "right alt")
        pure_alt_pressed = alt_pressed and not alt_gr_pressed and not ctrl_pressed

        return ctrl_pressed or win_pressed or pure_alt_pressed

    def _resolve_paste_count(self, key_name: str) -> int:
        if not self._is_paste_shortcut(key_name):
            return 0

        sequence = self._get_clipboard_sequence_number()
        return self._resolve_clipboard_text_count(sequence)

    def _start_clipboard_monitor(self) -> None:
        if self._clipboard_thread is not None:
            return
        self._clipboard_stop.clear()
        self._last_clipboard_sequence = self._get_clipboard_sequence_number()
        self._clipboard_thread = Thread(target=self._monitor_clipboard_changes, daemon=True)
        self._clipboard_thread.start()

    def _stop_clipboard_monitor(self) -> None:
        if self._clipboard_thread is None:
            return
        self._clipboard_stop.set()
        if self._clipboard_hwnd:
            try:
                user32 = ctypes.windll.user32
                user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                user32.PostMessageW(self._clipboard_hwnd, WM_CLOSE, 0, 0)
            except OSError:
                pass
        self._clipboard_thread.join(timeout=1.0)
        self._clipboard_thread = None

    def _monitor_clipboard_changes(self) -> None:
        try:
            event_monitor_started = self._monitor_clipboard_events()
        except AttributeError:
            event_monitor_started = False
        if event_monitor_started:
            return
        self._monitor_clipboard_polling()

    def _monitor_clipboard_events(self) -> bool:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        user32.DefWindowProcW.restype = LRESULT
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = ctypes.c_ushort
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD,
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.DWORD,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.HWND,
            wintypes.HMENU,
            wintypes.HINSTANCE,
            wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.AddClipboardFormatListener.argtypes = [wintypes.HWND]
        user32.AddClipboardFormatListener.restype = wintypes.BOOL
        user32.RemoveClipboardFormatListener.argtypes = [wintypes.HWND]
        user32.DestroyWindow.argtypes = [wintypes.HWND]
        user32.PostQuitMessage.argtypes = [ctypes.c_int]
        user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
        user32.GetMessageW.restype = wintypes.BOOL
        user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        class_name = f"TypeLedgerClipboardMonitor{hex(id(self))}"

        def window_proc(hwnd, message, wparam, lparam):
            _ = (wparam, lparam)
            if message == WM_CLIPBOARDUPDATE:
                self._handle_clipboard_update()
                return 0
            if message == WM_CLOSE:
                user32.DestroyWindow(hwnd)
                return 0
            if message == WM_DESTROY:
                user32.PostQuitMessage(0)
                return 0
            return user32.DefWindowProcW(hwnd, message, wparam, lparam)

        self._clipboard_wndproc = WNDPROC(window_proc)
        hinstance = kernel32.GetModuleHandleW(None)
        window_class = WNDCLASSW(
            style=0,
            lpfnWndProc=self._clipboard_wndproc,
            cbClsExtra=0,
            cbWndExtra=0,
            hInstance=hinstance,
            hIcon=None,
            hCursor=None,
            hbrBackground=None,
            lpszMenuName=None,
            lpszClassName=class_name,
        )

        try:
            user32.RegisterClassW(ctypes.byref(window_class))
            hwnd = user32.CreateWindowExW(
                0,
                class_name,
                class_name,
                0,
                0,
                0,
                0,
                0,
                wintypes.HWND(HWND_MESSAGE),
                None,
                hinstance,
                None,
            )
            if not hwnd:
                return False
            self._clipboard_hwnd = hwnd
            if not user32.AddClipboardFormatListener(hwnd):
                user32.DestroyWindow(hwnd)
                self._clipboard_hwnd = None
                return False

            message = wintypes.MSG()
            while not self._clipboard_stop.is_set():
                result = user32.GetMessageW(ctypes.byref(message), None, 0, 0)
                if result <= 0:
                    break
                user32.TranslateMessage(ctypes.byref(message))
                user32.DispatchMessageW(ctypes.byref(message))
            return True
        except OSError:
            return False
        finally:
            if self._clipboard_hwnd:
                try:
                    user32.RemoveClipboardFormatListener(self._clipboard_hwnd)
                    user32.DestroyWindow(self._clipboard_hwnd)
                except OSError:
                    pass
                self._clipboard_hwnd = None
            self._clipboard_wndproc = None

    def _monitor_clipboard_polling(self) -> None:
        while not self._clipboard_stop.wait(CLIPBOARD_POLL_INTERVAL_SECONDS):
            self._handle_clipboard_update()

    def _handle_clipboard_update(self) -> None:
        try:
            sequence = self._get_clipboard_sequence_number()
            if sequence is None:
                return
            should_count = False
            with self._lock:
                if sequence != self._last_clipboard_sequence:
                    self._last_clipboard_sequence = sequence
                    should_count = self.config.count_clipboard_changes
            if should_count:
                self._record_clipboard_change(sequence)
        except Exception:
            # Clipboard ownership is inherently racy on Windows. A failed read
            # should never stop keyboard counting or crash the app.
            return

    def _record_clipboard_change(self, sequence: int | None) -> None:
        paste_count = self._resolve_clipboard_text_count(sequence)
        if paste_count <= 0:
            return
        self._record_input(delta=paste_count, positive_count=paste_count, pasted_count=paste_count, backspace_count=0, count_for_speed=False)

    def _resolve_clipboard_text_count(self, sequence: int | None) -> int:
        clipboard_text = self._get_clipboard_text()
        if not clipboard_text:
            return 0
        paste_count = self._count_pasted_characters(clipboard_text)
        if paste_count <= 0:
            return 0
        with self._lock:
            if sequence is not None and sequence == self._last_counted_clipboard_sequence:
                return 0
            self._last_counted_clipboard_sequence = sequence
        return paste_count

    def _is_paste_shortcut(self, key_name: str) -> bool:
        ctrl_pressed = self._is_pressed("ctrl", "left ctrl", "right ctrl")
        shift_pressed = self._is_pressed("shift", "left shift", "right shift")
        alt_pressed = self._is_pressed("alt", "left alt", "right alt")
        win_pressed = self._is_pressed("windows", "left windows", "right windows")

        ctrl_v = key_name == "v" and ctrl_pressed and not alt_pressed and not win_pressed
        shift_insert = key_name == "insert" and shift_pressed and not ctrl_pressed and not alt_pressed and not win_pressed
        return ctrl_v or shift_insert

    def _is_pressed(self, *keys: str) -> bool:
        return any(keyboard.is_pressed(key) for key in keys)

    def _get_clipboard_sequence_number(self) -> int | None:
        try:
            user32 = ctypes.windll.user32
            user32.GetClipboardSequenceNumber.restype = wintypes.DWORD
            sequence = user32.GetClipboardSequenceNumber()
        except AttributeError:
            return None
        return int(sequence) if sequence else None

    def _get_clipboard_text(self) -> str | None:
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
        except AttributeError:
            return None
        user32.IsClipboardFormatAvailable.argtypes = [wintypes.UINT]
        user32.IsClipboardFormatAvailable.restype = wintypes.BOOL
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.GetClipboardData.argtypes = [wintypes.UINT]
        user32.GetClipboardData.restype = wintypes.HGLOBAL
        user32.CloseClipboard.restype = wintypes.BOOL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        if not user32.IsClipboardFormatAvailable(CF_UNICODETEXT):
            return None
        if not user32.OpenClipboard(None):
            return None

        try:
            handle = user32.GetClipboardData(CF_UNICODETEXT)
            if not handle:
                return None

            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                return None

            try:
                return ctypes.wstring_at(pointer)
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()

    def _count_pasted_characters(self, text: str) -> int:
        count = 0
        for char in text:
            if char == "\r":
                continue
            if char == " ":
                count += 1 if self.config.count_space else 0
                continue
            if char == "\n":
                count += 1 if self.config.count_enter else 0
                continue
            if char == "\t":
                continue
            if char.isprintable():
                count += 1
        return count
