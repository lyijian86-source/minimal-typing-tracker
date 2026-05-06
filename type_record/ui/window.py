from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Callable

from type_record.charting import flatten_coords, smooth_trend_points, trend_coords, trend_geometry
from type_record.config import AppConfig
from type_record.counter import KeyboardCounter
from type_record.i18n import tr
from type_record.storage import DailyCountStore
from .dialogs import DialogMixin
from .formatting import format_duration, format_last_input, format_weekly_delta, today_date_str
from .theme import (
    ACCENT as _ACCENT,
    ACCENT_DEEP as _ACCENT_DEEP,
    ACCENT_SOFT as _ACCENT_SOFT,
    BG as _BG,
    BORDER as _BORDER,
    BORDER_INNER as _BORDER_INNER,
    CARD as _CARD,
    CARD_ACCENT as _CARD_ACCENT,
    CARD_ACCENT_SOFT as _CARD_ACCENT_SOFT,
    CARD_INNER as _CARD_INNER,
    CHART_BG as _CHART_BG,
    CHART_FILL as _CHART_FILL,
    CHART_GRID as _CHART_GRID,
    CHART_LINE_SOFT as _CHART_LINE_SOFT,
    FONT_DISPLAY as _FONT_DISPLAY,
    FONT_NUMERIC as _FONT_NUMERIC,
    FONT_UI as _FONT_UI,
    SUCCESS as _SUCCESS,
    TEXT_ON_ACCENT as _TEXT_ON_ACCENT,
    TEXT_PRIMARY as _TEXT_PRIMARY,
    TEXT_QUATERNARY as _TEXT_QUATERNARY,
    TEXT_SECONDARY as _TEXT_SECONDARY,
    TEXT_TERTIARY as _TEXT_TERTIARY,
)
from .widgets import WidgetFactoryMixin

# ---------------------------------------------------------------------------
# Design system — colour tokens
# ---------------------------------------------------------------------------


class CounterWindow(DialogMixin, WidgetFactoryMixin):
    def __init__(self, config: AppConfig, store: DailyCountStore, counter: KeyboardCounter, on_export_csv: Callable[[], None], on_language_changed: Callable[[str], None]) -> None:
        self.config, self.store, self.counter = config, store, counter
        self.on_export_csv, self.on_language_changed = on_export_csv, on_language_changed
        self.root = tk.Tk()
        self._update_window_title()
        self.root.geometry("1240x820")
        self.root.minsize(1120, 740)
        self.root.configure(bg=_BG)
        self._window_icon: tk.PhotoImage | None = None
        self._set_window_icon()
        self._configure_ttk()

        self.count_var = tk.StringVar(value="0")
        self.detail_var = tk.StringVar(value="0")
        self.session_var = tk.StringVar(value="")
        self.session_length_var = tk.StringVar(value="00:00")
        self.session_typed_var = tk.StringVar(value="0")
        self.session_accuracy_var = tk.StringVar(value="0%")
        self.typed_today_var = tk.StringVar(value="0")
        self.accuracy_var = tk.StringVar(value="0%")
        self.cpm_var = tk.StringVar(value="0")
        self.peak_wpm_var = tk.StringVar(value="0.0")
        self.yesterday_var = tk.StringVar(value="0")
        self.week_var = tk.StringVar(value="0")
        self.last_input_var = tk.StringVar(value=tr(config.language, "no_input"))
        self.export_var = tk.StringVar(value="")
        self.accuracy_hint_var = tk.StringVar(value="")
        self.count_mode_var = tk.StringVar(value="")
        self.settings_var = tk.StringVar(value="")
        self.history_footer_var = tk.StringVar(value="")
        self.trend_meta_var = tk.StringVar(value="")
        self.trend_peak_var = tk.StringVar(value="0")
        self.trend_latest_var = tk.StringVar(value="0")
        self.weekly_mode_var = tk.StringVar(value="rolling")
        self.weekly_range_var = tk.StringVar(value="")
        self.weekly_output_var = tk.StringVar(value="")
        self.weekly_active_time_var = tk.StringVar(value="")
        self.weekly_efficiency_var = tk.StringVar(value="")
        self.weekly_previous_var = tk.StringVar(value="")
        self.weekly_secondary_var = tk.StringVar(value="")

        self.history_vars: list[dict[str, tk.StringVar]] = []
        self._latest_trend_history: list[dict] = []
        self._latest_weekly_history: list[dict] = []
        self._latest_weekly_metrics = None
        self._history_dialog: tk.Toplevel | None = None
        self._history_tree: ttk.Treeview | None = None
        self._page_canvas: tk.Canvas | None = None
        self._history_preview_canvas: tk.Canvas | None = None
        self._history_preview_inner: tk.Frame | None = None
        self._hourly_dialog: tk.Toplevel | None = None
        self._hourly_tree: ttk.Treeview | None = None
        self._hourly_canvas: tk.Canvas | None = None
        self._hourly_peak_var: tk.StringVar | None = None
        self._hourly_date_var: tk.StringVar | None = None
        self._hourly_date_selector: ttk.Combobox | None = None
        self._weekly_dialog: tk.Toplevel | None = None
        self._weekly_output_canvas: tk.Canvas | None = None
        self._weekly_efficiency_canvas: tk.Canvas | None = None
        self._weekly_detail_mode_var: tk.StringVar | None = None
        self._weekly_detail_output_var: tk.StringVar | None = None
        self._weekly_detail_time_var: tk.StringVar | None = None
        self._weekly_detail_efficiency_var: tk.StringVar | None = None
        self._weekly_explanation_var: tk.StringVar | None = None
        self._refresh_after_id: str | None = None
        self._trend_tooltip_items: list[int] = []

        self._build_layout()
        self._schedule_refresh()

    def set_on_close(self, callback) -> None:
        self.root.protocol("WM_DELETE_WINDOW", callback)

    def show(self) -> None:
        self.root.deiconify()
        try:
            self.root.state("zoomed")
        except tk.TclError:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        self.root.lift()
        self.root.focus_force()

    def hide(self) -> None:
        self.root.withdraw()

    def call_in_main_thread(self, callback) -> None:
        self.root.after(0, callback)

    def run(self) -> None:
        self.root.mainloop()

    def destroy(self) -> None:
        self._cancel_refresh()
        if self._history_dialog and self._history_dialog.winfo_exists():
            self._history_dialog.destroy()
        if self._hourly_dialog and self._hourly_dialog.winfo_exists():
            self._hourly_dialog.destroy()
        if self._weekly_dialog and self._weekly_dialog.winfo_exists():
            self._weekly_dialog.destroy()
        self.root.destroy()

    def _set_window_icon(self) -> None:
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        for asset_name in ("app_icon.png", "tray_icon.png"):
            asset_path = assets_dir / asset_name
            if not asset_path.exists():
                continue
            try:
                self._window_icon = tk.PhotoImage(file=str(asset_path))
                self.root.iconphoto(True, self._window_icon)
                return
            except tk.TclError:
                continue

    def refresh_language(self) -> None:
        self._update_window_title()
        self._cancel_refresh()
        if self._history_dialog and self._history_dialog.winfo_exists():
            self._history_dialog.destroy()
        if self._hourly_dialog and self._hourly_dialog.winfo_exists():
            self._hourly_dialog.destroy()
        if self._weekly_dialog and self._weekly_dialog.winfo_exists():
            self._weekly_dialog.destroy()
        for child in self.root.winfo_children():
            child.destroy()
        self.history_vars.clear()
        self._history_dialog = self._hourly_dialog = self._weekly_dialog = None
        self._history_tree = self._hourly_tree = None
        self._page_canvas = None
        self._history_preview_canvas = None
        self._history_preview_inner = None
        self._hourly_canvas = None
        self._hourly_peak_var = self._hourly_date_var = None
        self._hourly_date_selector = None
        self._weekly_output_canvas = self._weekly_efficiency_canvas = None
        self._weekly_detail_mode_var = None
        self._weekly_detail_output_var = None
        self._weekly_detail_time_var = None
        self._weekly_detail_efficiency_var = None
        self._weekly_explanation_var = None
        self._trend_tooltip_items.clear()
        self._configure_ttk()
        self._build_layout()
        self._schedule_refresh()

    def _update_window_title(self) -> None:
        self.root.title(tr(self.config.language, "app_label"))

    def show_export_message(self, text: str) -> None:
        self.export_var.set(text)
        self.root.after(5000, lambda: self.export_var.set(""))

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        shell = tk.Frame(self.root, bg=_BG, padx=34, pady=26)
        shell.pack(fill=tk.BOTH, expand=True)
        shell.grid_columnconfigure(0, weight=1)
        shell.grid_rowconfigure(1, weight=1)

        top = tk.Frame(shell, bg=_BG)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        top.grid_columnconfigure(0, weight=1)
        title = tk.Frame(top, bg=_BG)
        title.grid(row=0, column=0, sticky="w")
        tk.Label(title, text=tr(self.config.language, "app_label"), bg=_BG, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8, "bold")).pack(anchor=tk.W)
        tk.Label(title, text=tr(self.config.language, "typing_count"), bg=_BG, fg=_TEXT_PRIMARY, font=(_FONT_DISPLAY, 30)).pack(anchor=tk.W, pady=(2, 0))
        actions = tk.Frame(top, bg=_BG, padx=0, pady=0)
        actions.grid(row=0, column=1, sticky="e")
        for text, callback, primary in [(tr(self.config.language, "settings"), self.open_settings_dialog, False), (tr(self.config.language, "export_csv"), self.on_export_csv, False), (tr(self.config.language, "hourly"), self.open_hourly_dialog, False), (tr(self.config.language, "history"), self.open_history_dialog, True)]:
            self._command_button(actions, text, callback, primary).pack(side=tk.RIGHT, padx=(6, 0))

        viewport = tk.Frame(shell, bg=_BG)
        viewport.grid(row=1, column=0, sticky="nsew")
        viewport.grid_columnconfigure(0, weight=1)
        viewport.grid_rowconfigure(0, weight=1)

        page_canvas = tk.Canvas(viewport, bg=_BG, highlightthickness=0)
        self._page_canvas = page_canvas
        page_canvas.grid(row=0, column=0, sticky="nsew")
        page_scrollbar = ttk.Scrollbar(viewport, orient=tk.VERTICAL, command=page_canvas.yview, style="Vertical.TScrollbar")
        page_scrollbar.grid(row=0, column=1, sticky="ns")
        page_canvas.configure(yscrollcommand=page_scrollbar.set)

        page = tk.Frame(page_canvas, bg=_BG)
        page_window = page_canvas.create_window((0, 0), window=page, anchor="nw")
        page.grid_columnconfigure(0, weight=1)
        page.bind("<Configure>", lambda _e: page_canvas.configure(scrollregion=page_canvas.bbox("all")))
        page_canvas.bind("<Configure>", lambda e: page_canvas.itemconfigure(page_window, width=e.width))

        hero_wrap = tk.Frame(page, bg=_BG)
        hero_wrap.grid(row=0, column=0, sticky="ew")
        hero_wrap.grid_columnconfigure(0, weight=1)
        self._build_today_focus(hero_wrap)

        summary = tk.Frame(page, bg=_BG)
        summary.grid(row=1, column=0, sticky="ew", pady=(18, 0))
        summary.grid_columnconfigure(0, weight=1)
        weekly_wrap = tk.Frame(summary, bg=_BG)
        weekly_wrap.grid(row=0, column=0, sticky="ew")
        weekly_wrap.grid_columnconfigure(0, weight=1)
        detail_wrap = tk.Frame(summary, bg=_BG)
        detail_wrap.grid(row=1, column=0, sticky="ew")
        detail_wrap.grid_columnconfigure(0, weight=1)
        self._build_weekly_summary(weekly_wrap)
        self._build_today_detail(detail_wrap)

        trend = self._card(page)
        trend.grid(row=2, column=0, sticky="ew", pady=(18, 0))
        trend_header = tk.Frame(trend, bg=_CARD)
        trend_header.pack(fill=tk.X)
        tk.Label(trend_header, text=tr(self.config.language, "trend_30_days"), bg=_CARD, fg=_TEXT_PRIMARY, font=(_FONT_DISPLAY, 21)).pack(anchor=tk.W)
        tk.Label(trend_header, text=tr(self.config.language, "recent_days_desc"), bg=_CARD, fg=_TEXT_TERTIARY, font=(_FONT_UI, 9), wraplength=620, justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))
        trend_summary = tk.Frame(trend, bg=_CARD)
        trend_summary.pack(fill=tk.X, pady=(12, 0))
        for label_key, var in (("trend_peak_label", self.trend_peak_var), ("trend_latest_label", self.trend_latest_var)):
            cell = tk.Frame(trend_summary, bg=_CARD)
            cell.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 24))
            tk.Label(cell, text=tr(self.config.language, label_key), bg=_CARD, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8, "bold")).pack(anchor=tk.W)
            tk.Label(cell, textvariable=var, bg=_CARD, fg=_TEXT_SECONDARY, font=(_FONT_UI, 10, "bold")).pack(anchor=tk.W, pady=(4, 0))
        trend_visual = self._subcard(trend)
        trend_visual.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        self.trend_canvas = tk.Canvas(trend_visual, bg=_CHART_BG, highlightthickness=0, height=360)
        self.trend_canvas.pack(fill=tk.BOTH, expand=True)
        trend_meta = tk.Frame(trend_visual, bg=_CARD_INNER)
        trend_meta.pack(fill=tk.X, pady=(10, 0))
        tk.Label(trend_meta, textvariable=self.trend_meta_var, bg=_CARD_INNER, fg=_TEXT_TERTIARY, font=(_FONT_UI, 9), justify=tk.LEFT, wraplength=660).pack(anchor=tk.W)
        self.trend_canvas.bind("<Configure>", lambda _e: self._draw_trend_chart())
        self.trend_canvas.bind("<Motion>", self._on_trend_hover)
        self.trend_canvas.bind("<Leave>", self._on_trend_leave)

        history = self._card(page)
        history.grid(row=3, column=0, sticky="ew", pady=(18, 0))
        htop = tk.Frame(history, bg=_CARD)
        htop.pack(fill=tk.X)
        htitle = tk.Frame(htop, bg=_CARD)
        htitle.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(htitle, text=tr(self.config.language, "history"), bg=_CARD, fg=_TEXT_PRIMARY, font=(_FONT_DISPLAY, 18)).pack(anchor=tk.W)
        tk.Label(htitle, text=tr(self.config.language, "full_history_desc"), bg=_CARD, fg=_TEXT_TERTIARY, font=(_FONT_UI, 8)).pack(anchor=tk.W, pady=(5, 0))
        self._command_button(htop, tr(self.config.language, "open_history"), self.open_history_dialog, False).pack(side=tk.RIGHT)
        preview_wrap = tk.Frame(history, bg=_CARD)
        preview_wrap.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        self._history_preview_canvas = tk.Canvas(preview_wrap, bg=_CARD, highlightthickness=0, height=220)
        self._history_preview_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._history_preview_inner = tk.Frame(self._history_preview_canvas, bg=_CARD)
        self._history_preview_canvas.create_window((0, 0), window=self._history_preview_inner, anchor="nw")
        self._history_preview_inner.bind("<Configure>", lambda _e: self._sync_history_preview_scrollregion())
        self._history_preview_canvas.bind("<Configure>", lambda e: self._resize_history_preview_inner(e.width))
        tk.Label(history, textvariable=self.history_footer_var, bg=_CARD, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8)).pack(anchor=tk.W, pady=(14, 0))
        self._bind_page_mousewheel(viewport)

    def _build_today_focus(self, parent: tk.Widget) -> None:
        hero = tk.Frame(parent, bg=_CARD_ACCENT, highlightthickness=1, highlightbackground=_CARD_ACCENT_SOFT, padx=32, pady=28)
        hero.grid(row=0, column=0, sticky="ew")

        hero_top = tk.Frame(hero, bg=_CARD_ACCENT)
        hero_top.pack(fill=tk.X)
        tk.Label(hero_top, text=tr(self.config.language, "today"), bg=_CARD_ACCENT, fg=_ACCENT_SOFT, font=(_FONT_UI, 8, "bold")).pack(side=tk.LEFT)
        tk.Label(hero_top, textvariable=self.session_var, bg=_CARD_ACCENT, fg="#A9B4A8", font=(_FONT_UI, 9)).pack(side=tk.RIGHT)

        number_row = tk.Frame(hero, bg=_CARD_ACCENT)
        number_row.pack(fill=tk.X, pady=(12, 0))
        tk.Label(number_row, textvariable=self.count_var, bg=_CARD_ACCENT, fg=_TEXT_ON_ACCENT, font=(_FONT_NUMERIC, 92)).pack(side=tk.LEFT)
        tk.Label(number_row, textvariable=self.detail_var, bg=_CARD_ACCENT, fg="#C8CDBF", font=(_FONT_UI, 10), justify=tk.LEFT, wraplength=280).pack(side=tk.LEFT, padx=(22, 0), anchor=tk.S)

        session_meta = tk.Frame(hero, bg=_CARD_ACCENT)
        session_meta.pack(fill=tk.X, pady=(18, 0))
        for column in range(3):
            session_meta.grid_columnconfigure(column, weight=1)
        for column, (label, var) in enumerate(
            (
                (tr(self.config.language, "session_length"), self.session_length_var),
                (tr(self.config.language, "session_typed"), self.session_typed_var),
                (tr(self.config.language, "session_accuracy"), self.session_accuracy_var),
            )
        ):
            self._hero_chip(session_meta, label, var).grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 8, 0))

    def _build_weekly_summary(self, parent: tk.Widget) -> None:
        weekly = tk.Frame(parent, bg=_CARD, highlightthickness=1, highlightbackground=_BORDER, padx=26, pady=24)
        weekly.grid(row=0, column=0, sticky="ew")

        weekly_header = tk.Frame(weekly, bg=_CARD)
        weekly_header.pack(fill=tk.X)
        weekly_title = tk.Frame(weekly_header, bg=_CARD)
        weekly_title.pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(weekly_title, text=tr(self.config.language, "weekly_efficiency"), bg=_CARD, fg=_TEXT_PRIMARY, font=(_FONT_DISPLAY, 19)).pack(anchor=tk.W)
        tk.Label(weekly_title, textvariable=self.weekly_secondary_var, bg=_CARD, fg=_TEXT_SECONDARY, font=(_FONT_UI, 10, "bold")).pack(anchor=tk.W, pady=(5, 0))
        tk.Label(weekly_title, textvariable=self.weekly_range_var, bg=_CARD, fg=_TEXT_TERTIARY, font=(_FONT_UI, 8)).pack(anchor=tk.W, pady=(3, 0))
        self._command_button(weekly_header, tr(self.config.language, "weekly_open_detail"), self.open_weekly_efficiency_dialog, True).pack(side=tk.RIGHT, anchor=tk.N)

        weekly_actions = tk.Frame(weekly_header, bg=_CARD)
        weekly_actions.pack(anchor=tk.W, pady=(10, 0))
        self._command_button(weekly_actions, tr(self.config.language, "weekly_mode_short_rolling"), lambda: self._set_weekly_mode("rolling"), False).pack(side=tk.LEFT, padx=(0, 6))
        self._command_button(weekly_actions, tr(self.config.language, "weekly_mode_short_calendar"), lambda: self._set_weekly_mode("calendar"), False).pack(side=tk.LEFT, padx=(0, 6))

        weekly_grid = tk.Frame(weekly, bg=_CARD)
        weekly_grid.pack(fill=tk.X, pady=(16, 0))
        for column in range(3):
            weekly_grid.grid_columnconfigure(column, weight=1)
        for column, (label, var) in enumerate(
            (
                (tr(self.config.language, "weekly_output"), self.weekly_output_var),
                (tr(self.config.language, "weekly_active_time"), self.weekly_active_time_var),
                (tr(self.config.language, "weekly_active_efficiency"), self.weekly_efficiency_var),
            )
        ):
            cell = tk.Frame(weekly_grid, bg=_CARD)
            cell.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 14, 0))
            tk.Label(cell, text=label, bg=_CARD, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8, "bold"), wraplength=100, justify=tk.LEFT).pack(anchor=tk.W)
            tk.Label(cell, textvariable=var, bg=_CARD, fg=_TEXT_PRIMARY, font=(_FONT_UI, 11, "bold"), wraplength=118, justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 0))

        tk.Label(weekly, textvariable=self.weekly_previous_var, bg=_CARD, fg=_TEXT_TERTIARY, font=(_FONT_UI, 8), wraplength=620, justify=tk.LEFT).pack(anchor=tk.W, pady=(14, 0))

    def _build_system_summary(self, parent: tk.Widget) -> None:
        system = tk.Frame(parent, bg=_CARD, highlightthickness=1, highlightbackground=_BORDER, padx=18, pady=14)
        system.grid(row=0, column=2, sticky="nsew")
        tk.Label(system, text=tr(self.config.language, "metric_guide"), bg=_CARD, fg=_ACCENT_DEEP, font=(_FONT_UI, 8, "bold")).pack(anchor=tk.W)

        guide_stack = tk.Frame(system, bg=_CARD_INNER, highlightthickness=1, highlightbackground=_BORDER_INNER, padx=14, pady=12)
        guide_stack.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        self._status_line(guide_stack, tr(self.config.language, "last_input"), self.last_input_var, _TEXT_SECONDARY).pack(fill=tk.X)
        self._status_line(guide_stack, tr(self.config.language, "settings"), self.count_mode_var, _TEXT_TERTIARY).pack(fill=tk.X, pady=(8, 0))
        self._status_line(guide_stack, tr(self.config.language, "export_csv"), self.export_var, _SUCCESS).pack(fill=tk.X, pady=(8, 0))
        tk.Label(guide_stack, textvariable=self.settings_var, bg=_CARD_INNER, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8), wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=(10, 0))

    def _build_today_detail(self, parent: tk.Widget) -> None:
        today_stats = self._card(parent)
        today_stats.grid(row=0, column=0, sticky="ew", pady=(14, 0))
        self._metric_block(
            today_stats,
            tr(self.config.language, "group_today"),
            [
                (tr(self.config.language, "typed_today"), self.typed_today_var),
                (tr(self.config.language, "accuracy"), self.accuracy_var),
                (tr(self.config.language, "last_minute"), self.cpm_var),
                (tr(self.config.language, "peak_wpm_today"), self.peak_wpm_var),
            ],
            columns=2,
        ).pack(fill=tk.X)

    # ------------------------------------------------------------------
    # Periodic refresh
    # ------------------------------------------------------------------
    def _set_weekly_mode(self, mode: str) -> None:
        self.weekly_mode_var.set(mode if mode in {"rolling", "calendar"} else "rolling")
        self._refresh_weekly_state()
        self._refresh_weekly_efficiency_dialog()

    def _refresh_weekly_state(self) -> None:
        metrics = self.store.get_weekly_efficiency(
            mode=self.weekly_mode_var.get(),
            output_target=self.config.weekly_output_target,
            active_efficiency_target=self.config.weekly_active_efficiency_target,
        )
        self._latest_weekly_metrics = metrics
        self._latest_weekly_history = self.store.get_weekly_efficiency_history(mode=self.weekly_mode_var.get(), weeks=8)
        self.weekly_range_var.set(
            f"{tr(self.config.language, 'rolling_7_days' if self.weekly_mode_var.get() == 'rolling' else 'natural_week')}  {metrics.label}"
        )
        self.weekly_output_var.set(tr(self.config.language, "weekly_unit_chars", count=f"{metrics.output:,}"))
        self.weekly_active_time_var.set(tr(self.config.language, "weekly_unit_minutes", count=f"{metrics.active_minutes:.1f}"))
        if metrics.active_efficiency is None:
            self.weekly_efficiency_var.set(tr(self.config.language, "insufficient_history"))
        else:
            self.weekly_efficiency_var.set(tr(self.config.language, "weekly_unit_chars_per_min", count=f"{metrics.active_efficiency:.1f}"))
        self.weekly_previous_var.set(
            tr(
                self.config.language,
                "weekly_comparison_brief",
                output_change=format_weekly_delta(self.config.language, metrics.output_vs_previous_week),
                efficiency_change=format_weekly_delta(self.config.language, metrics.active_efficiency_vs_previous_week),
            )
        )
        self.weekly_secondary_var.set(self._weekly_insight_text(metrics.active_efficiency_vs_previous_week))

    def _weekly_insight_text(self, delta) -> str:
        if delta.state == "new":
            return tr(self.config.language, "weekly_insight_new")
        if delta.state == "unavailable" or delta.ratio is None:
            return tr(self.config.language, "weekly_insight_insufficient")
        if delta.ratio > 0.05:
            return tr(self.config.language, "weekly_insight_up")
        if delta.ratio < -0.05:
            return tr(self.config.language, "weekly_insight_down")
        return tr(self.config.language, "weekly_insight_flat")

    def _schedule_refresh(self) -> None:
        summary, live = self.store.get_summary(), self.counter.get_live_stats()
        full_history = self.store.get_full_history()
        preview_history = full_history[:5]
        self._latest_trend_history = self.store.get_trend_history(days=30)
        self.count_var.set(str(summary["today_count"]))
        self.detail_var.set(tr(self.config.language, "today_detail", count=summary["today_count"]))
        delta = live["session_delta"]
        prefix = "+" if delta >= 0 else ""
        if live["session_duration_seconds"] > 0 or delta != 0:
            self.session_var.set(tr(self.config.language, "session_current" if live["session_is_active"] else "session_last", value=f"{prefix}{delta}"))
        else:
            self.session_var.set(tr(self.config.language, "session_none"))
        self.session_length_var.set(self._format_duration(live["session_duration_seconds"]))
        self.session_typed_var.set(str(live["session_positive_count"]))
        self.session_accuracy_var.set(f"{live['session_accuracy'] * 100:.1f}%")
        self.typed_today_var.set(str(summary["typed_today"]))
        self.accuracy_var.set(f"{summary['accuracy'] * 100:.1f}%")
        self.cpm_var.set(tr(self.config.language, "cpm", count=live["recent_cpm"]))
        self.peak_wpm_var.set(f"{summary['peak_wpm_today']:.1f}")
        self.yesterday_var.set(str(summary["yesterday_count"]))
        self.week_var.set(str(summary["last_7_days_total"]))
        self.last_input_var.set(self._format_last_input(summary["last_input_at"] or live["last_input_at"]))
        self.count_mode_var.set(tr(self.config.language, "net_count_hint_subtracts" if self.config.backspace_decrements else "net_count_hint_ignored"))
        self.accuracy_hint_var.set(tr(self.config.language, "accuracy_hint", kept=summary["kept_today"], typed=summary["typed_today"]))
        self.settings_var.set(tr(self.config.language, "stored_settings", space=tr(self.config.language, "on") if self.config.count_space else tr(self.config.language, "off"), enter=tr(self.config.language, "on") if self.config.count_enter else tr(self.config.language, "off"), backspace=tr(self.config.language, "subtracts") if self.config.backspace_decrements else tr(self.config.language, "ignored"), hidden=tr(self.config.language, "on") if self.config.start_hidden_to_tray else tr(self.config.language, "off"), lang_name=tr(self.config.language, "language_name")))
        self.history_footer_var.set(tr(self.config.language, "days_recorded", count=len(full_history)))
        self._refresh_weekly_state()
        self._update_trend_meta()
        self._ensure_history_preview_rows(len(preview_history))
        for i, row in enumerate(self.history_vars):
            if i < len(preview_history):
                day = preview_history[i]
                row["date"].set(day["date"])
                row["count"].set(str(day["count"]))
                row["meta"].set(
                    tr(
                        self.config.language,
                        "history_preview_meta",
                        typed=day["typed"],
                        pasted=day["pasted"],
                        accuracy=f"{day['accuracy'] * 100:.1f}%",
                    )
                )
            else:
                row["date"].set("-")
                row["count"].set("0")
                row["meta"].set("")
        self._sync_history_preview_scrollregion()
        self._draw_trend_chart()
        self._refresh_history_dialog()
        self._refresh_hourly_dialog()
        self._refresh_weekly_efficiency_dialog()
        self._refresh_after_id = self.root.after(self.config.refresh_interval_ms, self._schedule_refresh)

    def _update_trend_meta(self) -> None:
        non_zero = [item for item in self._latest_trend_history if item["count"] > 0]
        if not non_zero:
            self.trend_meta_var.set(tr(self.config.language, "trend_empty"))
            self.trend_peak_var.set(tr(self.config.language, "trend_empty"))
            self.trend_latest_var.set(tr(self.config.language, "trend_empty"))
            return
        peak = max(non_zero, key=lambda item: item["count"])
        latest = self._latest_trend_history[-1]
        self.trend_peak_var.set(f"{peak['count']}  /  {peak['date'][5:]}")
        self.trend_latest_var.set(f"{latest['count']}  /  {latest['date'][5:]}")
        self.trend_meta_var.set(
            tr(
                self.config.language,
                "trend_meta",
                peak=peak["count"],
                peak_date=peak["date"],
                latest=latest["count"],
                latest_date=latest["date"],
            )
        )

    # ------------------------------------------------------------------
    # Trend chart
    # ------------------------------------------------------------------
    def _draw_trend_chart(self) -> None:
        canvas = self.trend_canvas
        canvas.delete("all")
        data = self._latest_trend_history
        if not data:
            return

        width, height, ml, mr, mt, mb, cw, ch = self._trend_geometry(canvas)
        canvas.create_rectangle(0, 0, width, height, fill=_CHART_BG, outline="")

        max_count = self._trend_max_count(data)
        if max_count <= 0:
            canvas.create_text(
                width / 2, height / 2,
                text=tr(self.config.language, "trend_empty"),
                fill=_TEXT_TERTIARY, font=(_FONT_UI, 11),
            )
            return

        for ratio in (0.34, 0.68):
            y = mt + ch * ratio
            canvas.create_line(ml, y, width - mr, y, fill=_CHART_GRID, width=1)

        coords = self._trend_coords(data, ml, mt, cw, ch, max_count)
        line_points = self._smooth_trend_points(coords, mt, mt + ch)

        area_coords: list[float] = [ml, mt + ch] + line_points + [width - mr, mt + ch]
        canvas.create_polygon(*area_coords, fill=_CHART_FILL, outline="")

        if len(line_points) >= 4:
            canvas.create_line(
                *line_points, fill=_CHART_LINE_SOFT, width=8,
                capstyle=tk.ROUND, joinstyle=tk.ROUND,
            )
            canvas.create_line(
                *line_points, fill=_ACCENT_DEEP, width=3,
                capstyle=tk.ROUND, joinstyle=tk.ROUND,
            )
        elif len(line_points) >= 2:
            canvas.create_line(*line_points, fill=_ACCENT_DEEP, width=3, capstyle=tk.ROUND)

        canvas.create_line(ml, mt + ch, width - mr, mt + ch, fill=_CHART_GRID, width=1)
        self._draw_x_axis_labels(canvas, data, ml, mr, width, height)

        peak_coord = max(coords, key=lambda c: c[2]["count"])
        if peak_coord[2]["count"] > 0:
            self._draw_peak_annotation(canvas, peak_coord, mt)

        latest = coords[-1]
        if latest[2]["count"] > 0:
            lx, ly = latest[0], latest[1]
            canvas.create_oval(lx - 9, ly - 9, lx + 9, ly + 9, fill=_CHART_BG, outline=_ACCENT_SOFT, width=1)
            canvas.create_oval(lx - 4, ly - 4, lx + 4, ly + 4, fill=_ACCENT_DEEP, outline="")

    def _trend_geometry(self, canvas: tk.Canvas) -> tuple[int, int, int, int, int, int, int, int]:
        # Use the real widget size. Drawing against a larger virtual height
        # causes the lower part of the chart to be clipped by the canvas.
        return trend_geometry(canvas.winfo_width(), canvas.winfo_height())

    def _trend_max_count(self, data: list[dict]) -> int:
        return max((item["count"] for item in data), default=0)

    def _trend_coords(self, data: list[dict], ml: int, mt: int, cw: int, ch: int, max_count: int) -> list[tuple[float, float, dict]]:
        return trend_coords(data, ml, mt, cw, ch, max_count)

    def _flatten_coords(self, coords: list[tuple[float, float, dict]]) -> list[float]:
        return flatten_coords(coords)

    def _smooth_trend_points(self, coords: list[tuple[float, float, dict]], min_y: float, max_y: float) -> list[float]:
        return smooth_trend_points(coords, min_y, max_y)

    def _draw_x_axis_labels(self, canvas: tk.Canvas, data: list[dict], ml: int, mr: int, width: int, height: int) -> None:
        n = len(data)
        if n == 0:
            return
        if n == 1:
            canvas.create_text(ml, height - 14, text=data[0]["date"][5:], fill=_TEXT_QUATERNARY, font=(_FONT_UI, 8), anchor="n")
            return
        cw = width - ml - mr
        label_indexes = sorted({0, n // 3, (n * 2) // 3, n - 1})
        for i in label_indexes:
            x = ml + cw * i / (n - 1)
            date_str = data[i]["date"][5:]
            anchor = "n"
            if i == 0:
                anchor = "nw"
            elif i == n - 1:
                anchor = "ne"
            canvas.create_text(x, height - 14, text=date_str, fill=_TEXT_QUATERNARY, font=(_FONT_UI, 8), anchor=anchor)

    def _draw_peak_annotation(self, canvas: tk.Canvas, coord: tuple[float, float, dict], mt: int) -> None:
        px, py, item = coord
        peak_value = item["count"]
        label = f"{tr(self.config.language, 'trend_peak_label')} {peak_value:,}"
        label_y = py - 22 if py - 32 > mt else py + 24
        canvas.create_text(px, label_y, text=label, fill=_ACCENT_DEEP, font=(_FONT_UI, 9, "bold"))
        canvas.create_oval(px - 7, py - 7, px + 7, py + 7, fill=_CHART_BG, outline=_ACCENT_SOFT, width=1)
        canvas.create_oval(px - 3.5, py - 3.5, px + 3.5, py + 3.5, fill=_ACCENT_DEEP, outline="")

    # ------------------------------------------------------------------
    # Trend chart hover tooltip
    # ------------------------------------------------------------------
    def _on_trend_hover(self, event: tk.Event) -> None:
        canvas = self.trend_canvas
        data = self._latest_trend_history
        if not data:
            return

        # Remove previous tooltip
        for item_id in self._trend_tooltip_items:
            canvas.delete(item_id)
        self._trend_tooltip_items.clear()

        width, height, ml, mr, mt, mb, cw, ch = self._trend_geometry(canvas)

        mouse_x = event.x
        if mouse_x < ml - 10 or mouse_x > width - mr + 10:
            return

        n = len(data)
        if n == 0:
            return
        max_count = self._trend_max_count(data)
        if max_count <= 0:
            return
        coords = self._trend_coords(data, ml, mt, cw, ch, max_count)

        index = round((mouse_x - ml) / cw * (n - 1)) if n > 1 else 0
        index = max(0, min(n - 1, index))
        x, y, item = coords[index]

        # Vertical crosshair
        line_id = canvas.create_line(x, mt, x, mt + ch, fill=_BORDER, width=1, dash=(3, 6))
        self._trend_tooltip_items.append(line_id)

        # Highlighted data point
        marker_outer = canvas.create_oval(x - 8, y - 8, x + 8, y + 8, fill=_CHART_BG, outline=_ACCENT_SOFT, width=1)
        marker_inner = canvas.create_oval(x - 3.5, y - 3.5, x + 3.5, y + 3.5, fill=_ACCENT_DEEP, outline="")
        self._trend_tooltip_items.extend([marker_outer, marker_inner])

        # Tooltip box
        date_str = item["date"]
        count_str = f"{item['count']:,}"
        tooltip_text = f"{count_str}\n{date_str}"
        approx_tip_w = max(len(count_str), len(date_str)) * 8 + 26
        approx_tip_h = 42

        # Position: prefer above the point
        if y > mt + 60:
            tip_y = y - 38
            pointer_tip = y - 10
            pointer_base = tip_y + approx_tip_h / 2
        else:
            tip_y = y + 38
            pointer_tip = y + 10
            pointer_base = tip_y - approx_tip_h / 2

        tip_x = max(ml + approx_tip_w / 2, min(width - mr - approx_tip_w / 2, x))

        # Shadow
        bg_shadow = canvas.create_rectangle(
            tip_x - approx_tip_w / 2 + 2, tip_y - approx_tip_h / 2 + 2,
            tip_x + approx_tip_w / 2 + 2, tip_y + approx_tip_h / 2 + 2,
            fill="#DADCCF", outline="",
        )
        # Background
        bg = canvas.create_rectangle(
            tip_x - approx_tip_w / 2, tip_y - approx_tip_h / 2,
            tip_x + approx_tip_w / 2, tip_y + approx_tip_h / 2,
            fill=_CARD, outline=_BORDER,
        )
        # Triangle pointer
        if tip_y < y:
            pointer = canvas.create_polygon(
                tip_x - 5, pointer_base, tip_x + 5, pointer_base, tip_x, pointer_tip,
                fill=_CARD, outline=_BORDER,
            )
        else:
            pointer = canvas.create_polygon(
                tip_x - 5, pointer_base, tip_x + 5, pointer_base, tip_x, pointer_tip,
                fill=_CARD, outline=_BORDER,
            )
        # Text
        text = canvas.create_text(tip_x, tip_y, text=tooltip_text, fill=_TEXT_SECONDARY, font=(_FONT_UI, 9, "bold"), justify=tk.CENTER)
        self._trend_tooltip_items.extend([bg_shadow, bg, pointer, text])

    def _on_trend_leave(self, event: tk.Event) -> None:
        for item_id in self._trend_tooltip_items:
            self.trend_canvas.delete(item_id)
        self._trend_tooltip_items.clear()

    # ------------------------------------------------------------------
    # History preview rows
    # ------------------------------------------------------------------
    def _ensure_history_preview_rows(self, count: int) -> None:
        if self._history_preview_inner is None:
            return
        while len(self.history_vars) < count:
            row_vars = {
                "date": tk.StringVar(value="-"),
                "count": tk.StringVar(value="0"),
                "meta": tk.StringVar(value=""),
            }
            self.history_vars.append(row_vars)
            row_wrap = tk.Frame(self._history_preview_inner, bg=_CARD, padx=0, pady=0)
            row_wrap.pack(fill=tk.X, pady=(0, 12))
            row_body = tk.Frame(row_wrap, bg=_CARD, highlightthickness=0, padx=0, pady=0)
            row_body.pack(fill=tk.X, expand=True)
            row_head = tk.Frame(row_body, bg=_CARD)
            row_head.pack(fill=tk.X)
            tk.Label(row_head, textvariable=row_vars["date"], bg=_CARD, fg=_TEXT_TERTIARY, font=(_FONT_UI, 9, "bold")).pack(side=tk.LEFT)
            tk.Label(row_head, textvariable=row_vars["count"], bg=_CARD, fg=_TEXT_PRIMARY, font=(_FONT_NUMERIC, 20)).pack(side=tk.RIGHT)
            tk.Label(row_body, textvariable=row_vars["meta"], bg=_CARD, fg=_TEXT_QUATERNARY, font=(_FONT_UI, 8), justify=tk.LEFT, wraplength=620).pack(anchor=tk.W, pady=(4, 0))
            divider = tk.Frame(row_body, bg=_BORDER_INNER, height=1)
            divider.pack(fill=tk.X, pady=(8, 0))
            self._bind_page_mousewheel(row_wrap)

        while len(self.history_vars) > count:
            row_vars = self.history_vars.pop()
            last_child = self._history_preview_inner.winfo_children()[-1]
            last_child.destroy()

    def _sync_history_preview_scrollregion(self) -> None:
        if self._history_preview_canvas is None or self._history_preview_inner is None:
            return
        self._history_preview_canvas.configure(scrollregion=self._history_preview_canvas.bbox("all"))

    def _resize_history_preview_inner(self, width: int) -> None:
        if self._history_preview_canvas is None or self._history_preview_inner is None:
            return
        items = self._history_preview_canvas.find_all()
        if items:
            self._history_preview_canvas.itemconfigure(items[0], width=width)

    def _bind_page_mousewheel(self, widget: tk.Widget) -> None:
        widget.bind("<MouseWheel>", self._on_page_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_page_mousewheel(child)

    def _on_page_mousewheel(self, event) -> str:
        if self._page_canvas is not None:
            if event.delta > 0:
                self._page_canvas.yview_scroll(-3, "units")
            elif event.delta < 0:
                self._page_canvas.yview_scroll(3, "units")
        return "break"

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _cancel_refresh(self) -> None:
        if self._refresh_after_id is not None:
            try:
                self.root.after_cancel(self._refresh_after_id)
            except tk.TclError:
                pass
            self._refresh_after_id = None

    def _available_history_dates(self) -> list[str]:
        dates = [item["date"] for item in self.store.get_full_history()]
        return dates or [self._today_date_str()]

    def _selected_hourly_date(self) -> str:
        return self._hourly_date_var.get().strip() if self._hourly_date_var and self._hourly_date_var.get().strip() else self._today_date_str()

    def _today_date_str(self) -> str:
        return today_date_str()

    def _format_last_input(self, last_input_at: str | None) -> str:
        return format_last_input(self.config.language, last_input_at)

    def _format_duration(self, seconds: int) -> str:
        return format_duration(seconds)
