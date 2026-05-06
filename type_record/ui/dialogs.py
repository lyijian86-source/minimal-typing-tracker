from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from type_record.i18n import tr

from .formatting import format_axis_value, format_weekly_delta
from .theme import (
    ACCENT,
    ACCENT_DEEP,
    ACCENT_LIGHT,
    BG,
    CARD,
    CARD_ACCENT,
    CARD_INNER,
    CHART_BG,
    CHART_GRID,
    FONT_UI,
    HOURLY_TYPED,
    TEXT_PRIMARY,
    TEXT_QUATERNARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
)


class DialogMixin:
    def open_settings_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(tr(self.config.language, "settings_title"))
        dialog.geometry("560x700")
        dialog.minsize(540, 640)
        dialog.resizable(True, True)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        dialog.grab_set()
        shell = tk.Frame(dialog, bg=BG, padx=18, pady=18)
        shell.pack(fill=tk.BOTH, expand=True)
        footer = tk.Frame(shell, bg=BG)
        footer.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))
        card = self._card(shell)
        card.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self._dialog_header(card, tr(self.config.language, "settings_title"), tr(self.config.language, "settings_desc"))
        settings_viewport = tk.Frame(card, bg=CARD)
        settings_viewport.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        settings_viewport.grid_columnconfigure(0, weight=1)
        settings_viewport.grid_rowconfigure(0, weight=1)
        settings_canvas = tk.Canvas(settings_viewport, bg=CARD, highlightthickness=0)
        settings_canvas.grid(row=0, column=0, sticky="nsew")
        settings_scrollbar = ttk.Scrollbar(settings_viewport, orient=tk.VERTICAL, command=settings_canvas.yview, style="Vertical.TScrollbar")
        settings_scrollbar.grid(row=0, column=1, sticky="ns")
        settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        settings_content = tk.Frame(settings_canvas, bg=CARD)
        settings_window = settings_canvas.create_window((0, 0), window=settings_content, anchor="nw")
        settings_content.bind("<Configure>", lambda _e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all")))
        settings_canvas.bind("<Configure>", lambda e: settings_canvas.itemconfigure(settings_window, width=e.width))

        def on_settings_mousewheel(event) -> str:
            if event.delta > 0:
                settings_canvas.yview_scroll(-3, "units")
            elif event.delta < 0:
                settings_canvas.yview_scroll(3, "units")
            return "break"

        def bind_settings_mousewheel(widget: tk.Widget) -> None:
            widget.bind("<MouseWheel>", on_settings_mousewheel, add="+")
            for child in widget.winfo_children():
                bind_settings_mousewheel(child)

        count_space = tk.BooleanVar(value=self.config.count_space)
        count_enter = tk.BooleanVar(value=self.config.count_enter)
        backspace_decrements = tk.BooleanVar(value=self.config.backspace_decrements)
        start_hidden = tk.BooleanVar(value=self.config.start_hidden_to_tray)
        language_mode = tk.StringVar(value=self.config.language)
        weekly_output_target = tk.StringVar(value=str(self.config.weekly_output_target))
        weekly_efficiency_target = tk.StringVar(value=f"{self.config.weekly_active_efficiency_target:g}")
        tk.Label(settings_content, text=tr(self.config.language, "counting_rules"), bg=CARD, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W, pady=(0, 8))
        box = self._subcard(settings_content)
        box.pack(fill=tk.X)
        for text, var in [
            (tr(self.config.language, "count_space"), count_space),
            (tr(self.config.language, "count_enter"), count_enter),
            (tr(self.config.language, "backspace_subtracts"), backspace_decrements),
        ]:
            tk.Checkbutton(box, text=text, variable=var, bg=CARD_INNER, activebackground=CARD_INNER, fg=TEXT_SECONDARY, activeforeground=TEXT_SECONDARY, selectcolor=CARD, font=(FONT_UI, 10), anchor="w", padx=2, pady=4, relief=tk.FLAT).pack(fill=tk.X)
        tk.Label(settings_content, text=tr(self.config.language, "app_preferences"), bg=CARD, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W, pady=(14, 8))
        lang = self._subcard(settings_content)
        lang.pack(fill=tk.X)
        tk.Checkbutton(lang, text=tr(self.config.language, "start_hidden"), variable=start_hidden, bg=CARD_INNER, activebackground=CARD_INNER, fg=TEXT_SECONDARY, activeforeground=TEXT_SECONDARY, selectcolor=CARD, font=(FONT_UI, 10), anchor="w", padx=2, pady=4, relief=tk.FLAT).pack(fill=tk.X, pady=(0, 8))
        tk.Label(lang, text=tr(self.config.language, "language_mode"), bg=CARD_INNER, fg=TEXT_TERTIARY, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W, pady=(0, 8))
        tk.Radiobutton(lang, text=tr(self.config.language, "lang_zh"), value="zh", variable=language_mode, bg=CARD_INNER, activebackground=CARD_INNER, fg=TEXT_SECONDARY, activeforeground=TEXT_SECONDARY, selectcolor=CARD, font=(FONT_UI, 10)).pack(anchor=tk.W)
        tk.Radiobutton(lang, text=tr(self.config.language, "lang_en"), value="en", variable=language_mode, bg=CARD_INNER, activebackground=CARD_INNER, fg=TEXT_SECONDARY, activeforeground=TEXT_SECONDARY, selectcolor=CARD, font=(FONT_UI, 10)).pack(anchor=tk.W, pady=(6, 0))
        tk.Label(settings_content, text=tr(self.config.language, "weekly_efficiency"), bg=CARD, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W, pady=(14, 8))
        weekly = self._subcard(settings_content)
        weekly.pack(fill=tk.X)
        tk.Label(weekly, text=tr(self.config.language, "weekly_output_target"), bg=CARD_INNER, fg=TEXT_TERTIARY, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        tk.Entry(weekly, textvariable=weekly_output_target, bg=CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief=tk.FLAT).pack(fill=tk.X, pady=(6, 10))
        tk.Label(weekly, text=tr(self.config.language, "weekly_active_efficiency_target"), bg=CARD_INNER, fg=TEXT_TERTIARY, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        tk.Entry(weekly, textvariable=weekly_efficiency_target, bg=CARD, fg=TEXT_PRIMARY, insertbackground=TEXT_PRIMARY, relief=tk.FLAT).pack(fill=tk.X, pady=(6, 0))
        bind_settings_mousewheel(settings_viewport)

        def save_settings() -> None:
            self.config.count_space = bool(count_space.get())
            self.config.count_enter = bool(count_enter.get())
            self.config.backspace_decrements = bool(backspace_decrements.get())
            self.config.start_hidden_to_tray = bool(start_hidden.get())
            changed = self.config.language != language_mode.get()
            self.config.language = language_mode.get()
            try:
                self.config.weekly_output_target = max(0, int(weekly_output_target.get().strip() or "0"))
            except ValueError:
                self.config.weekly_output_target = 0
            try:
                self.config.weekly_active_efficiency_target = max(0.0, float(weekly_efficiency_target.get().strip() or "0"))
            except ValueError:
                self.config.weekly_active_efficiency_target = 0.0
            self.config.save()
            dialog.destroy()
            if changed:
                self.on_language_changed(self.config.language)
                self.refresh_language()
            self.show()

        self._toolbar_button(footer, tr(self.config.language, "save"), save_settings, True).pack(side=tk.RIGHT)

    def open_history_dialog(self) -> None:
        if self._history_dialog and self._history_dialog.winfo_exists():
            self._history_dialog.deiconify()
            self._history_dialog.lift()
            self._refresh_history_dialog()
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(tr(self.config.language, "full_history"))
        dialog.geometry("860x640")
        dialog.minsize(800, 580)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        self._history_dialog = dialog
        shell = tk.Frame(dialog, bg=BG, padx=18, pady=18)
        shell.pack(fill=tk.BOTH, expand=True)
        card = self._card(shell)
        card.pack(fill=tk.BOTH, expand=True)
        self._dialog_header(card, tr(self.config.language, "full_history"), tr(self.config.language, "full_history_desc"))
        wrap = tk.Frame(card, bg=CARD)
        wrap.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        cols = ("date", "count", "typed", "backspace", "accuracy", "peak_wpm")
        tree = ttk.Treeview(wrap, columns=cols, show="headings", style="TypeRecord.Treeview")
        for col, label in [("date", "history_columns_date"), ("count", "history_columns_count"), ("typed", "history_columns_typed"), ("backspace", "history_columns_backspace"), ("accuracy", "history_columns_accuracy"), ("peak_wpm", "history_columns_peak_wpm")]:
            tree.heading(col, text=tr(self.config.language, label))
        tree.column("date", width=160, anchor=tk.W)
        for col in ("count", "typed", "backspace", "accuracy", "peak_wpm"):
            tree.column(col, width=110, anchor=tk.E)
        sb = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._history_tree = tree
        dialog.protocol("WM_DELETE_WINDOW", self._close_history_dialog)
        self._refresh_history_dialog()

    def open_hourly_dialog(self) -> None:
        if self._hourly_dialog and self._hourly_dialog.winfo_exists():
            self._hourly_dialog.deiconify()
            self._hourly_dialog.lift()
            self._refresh_hourly_dialog()
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(tr(self.config.language, "hourly_today"))
        dialog.geometry("900x660")
        dialog.minsize(840, 600)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        self._hourly_dialog = dialog
        shell = tk.Frame(dialog, bg=BG, padx=18, pady=18)
        shell.pack(fill=tk.BOTH, expand=True)
        card = self._card(shell)
        card.pack(fill=tk.BOTH, expand=True)
        self._dialog_header(card, tr(self.config.language, "hourly_today"), tr(self.config.language, "hourly_today_desc"))
        row = tk.Frame(card, bg=CARD)
        row.pack(fill=tk.X, pady=(14, 10))
        tk.Label(row, text=tr(self.config.language, "hourly_date"), bg=CARD, fg=TEXT_SECONDARY, font=(FONT_UI, 9, "bold")).pack(side=tk.LEFT)
        self._hourly_date_var = tk.StringVar(value=self._today_date_str())
        self._hourly_date_selector = ttk.Combobox(row, textvariable=self._hourly_date_var, state="readonly", width=16, values=self._available_history_dates(), style="TypeRecord.TCombobox")
        self._hourly_date_selector.pack(side=tk.LEFT, padx=(10, 0))
        self._hourly_date_selector.bind("<<ComboboxSelected>>", lambda _e: self._refresh_hourly_dialog())
        self._hourly_peak_var = tk.StringVar(value="")
        tk.Label(card, textvariable=self._hourly_peak_var, bg=CARD, fg=TEXT_SECONDARY, font=(FONT_UI, 9, "bold")).pack(anchor=tk.W, pady=(0, 12))
        graph = self._subcard(card)
        graph.pack(fill=tk.X)
        self._hourly_canvas = tk.Canvas(graph, bg=CHART_BG, highlightthickness=0, height=220)
        self._hourly_canvas.pack(fill=tk.BOTH, expand=True)
        self._hourly_canvas.bind("<Configure>", lambda _e: self._draw_hourly_chart())
        wrap = tk.Frame(card, bg=CARD)
        wrap.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        tree = ttk.Treeview(wrap, columns=("hour", "total"), show="headings", style="TypeRecord.Treeview")
        for col, label in [("hour", "hourly_table_hour"), ("total", "hourly_table_total")]:
            tree.heading(col, text=tr(self.config.language, label))
        tree.column("hour", width=180, anchor=tk.W)
        tree.column("total", width=180, anchor=tk.E)
        sb = ttk.Scrollbar(wrap, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self._hourly_tree = tree
        dialog.protocol("WM_DELETE_WINDOW", self._close_hourly_dialog)
        self._refresh_hourly_dialog()

    def open_weekly_efficiency_dialog(self) -> None:
        if self._weekly_dialog and self._weekly_dialog.winfo_exists():
            self._weekly_dialog.deiconify()
            self._weekly_dialog.lift()
            self._refresh_weekly_efficiency_dialog()
            return
        dialog = tk.Toplevel(self.root)
        dialog.title(tr(self.config.language, "weekly_details"))
        dialog.geometry("960x760")
        dialog.minsize(880, 700)
        dialog.configure(bg=BG)
        dialog.transient(self.root)
        self._weekly_dialog = dialog
        shell = tk.Frame(dialog, bg=BG, padx=18, pady=18)
        shell.pack(fill=tk.BOTH, expand=True)
        card = self._card(shell)
        card.pack(fill=tk.BOTH, expand=True)
        self._dialog_header(card, tr(self.config.language, "weekly_details"), tr(self.config.language, "weekly_details_desc"))
        top = tk.Frame(card, bg=CARD)
        top.pack(fill=tk.X, pady=(14, 0))
        for column in range(4):
            top.grid_columnconfigure(column, weight=1)
        self._weekly_detail_mode_var = tk.StringVar(value="")
        self._weekly_detail_output_var = tk.StringVar(value="")
        self._weekly_detail_time_var = tk.StringVar(value="")
        self._weekly_detail_efficiency_var = tk.StringVar(value="")
        self._tile(top, tr(self.config.language, "rolling_7_days"), self._weekly_detail_mode_var, 0, 0)
        self._tile(top, tr(self.config.language, "weekly_output"), self._weekly_detail_output_var, 0, 1)
        self._tile(top, tr(self.config.language, "weekly_active_time"), self._weekly_detail_time_var, 0, 2)
        self._tile(top, tr(self.config.language, "weekly_active_efficiency"), self._weekly_detail_efficiency_var, 0, 3)

        charts = tk.Frame(card, bg=CARD)
        charts.pack(fill=tk.BOTH, expand=True, pady=(14, 0))
        output_wrap = self._subcard(charts)
        output_wrap.pack(fill=tk.BOTH, expand=True)
        tk.Label(output_wrap, text=tr(self.config.language, "weekly_chart_output"), bg=CARD_INNER, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        self._weekly_output_canvas = tk.Canvas(output_wrap, bg=CHART_BG, highlightthickness=0, height=220)
        self._weekly_output_canvas.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self._weekly_output_canvas.bind("<Configure>", lambda _e: self._refresh_weekly_efficiency_dialog())

        efficiency_wrap = self._subcard(charts)
        efficiency_wrap.pack(fill=tk.BOTH, expand=True, pady=(12, 0))
        tk.Label(efficiency_wrap, text=tr(self.config.language, "weekly_chart_efficiency"), bg=CARD_INNER, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        self._weekly_efficiency_canvas = tk.Canvas(efficiency_wrap, bg=CHART_BG, highlightthickness=0, height=220)
        self._weekly_efficiency_canvas.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        self._weekly_efficiency_canvas.bind("<Configure>", lambda _e: self._refresh_weekly_efficiency_dialog())

        self._weekly_explanation_var = tk.StringVar(value="")
        explanation = self._subcard(card)
        explanation.pack(fill=tk.X, pady=(14, 0))
        tk.Label(explanation, textvariable=self._weekly_explanation_var, bg=CARD_INNER, fg=TEXT_SECONDARY, font=(FONT_UI, 10), wraplength=780, justify=tk.LEFT).pack(anchor=tk.W)
        dialog.protocol("WM_DELETE_WINDOW", self._close_weekly_dialog)
        self._refresh_weekly_efficiency_dialog()

    def _refresh_history_dialog(self) -> None:
        if self._history_tree is None:
            return
        self._history_tree.delete(*self._history_tree.get_children())
        for item in self.store.get_full_history():
            self._history_tree.insert("", tk.END, values=(item["date"], item["count"], item["typed"], item["backspace"], f"{item['accuracy'] * 100:.1f}%", f"{item['peak_wpm']:.1f}"))

    def _refresh_hourly_dialog(self) -> None:
        if self._hourly_tree is None:
            return
        dates = self._available_history_dates()
        selected = self._selected_hourly_date()
        if self._hourly_date_selector is not None:
            self._hourly_date_selector["values"] = dates
        if selected not in dates:
            selected = dates[0]
            if self._hourly_date_var is not None:
                self._hourly_date_var.set(selected)
        data = self.store.get_hourly_distribution(selected)
        self._hourly_tree.delete(*self._hourly_tree.get_children())
        for item in data:
            self._hourly_tree.insert("", tk.END, values=(f"{item['hour']}:00", item["total"]))
        if self._hourly_peak_var is not None:
            peak = max(data, key=lambda item: item["total"], default=None)
            self._hourly_peak_var.set(f"{tr(self.config.language, 'hourly_peak')}: {selected}  {peak['hour']}:00  {peak['total']}" if peak and peak["total"] > 0 else tr(self.config.language, "hourly_empty"))
        self._draw_hourly_chart()

    def _refresh_weekly_efficiency_dialog(self) -> None:
        if not self._weekly_dialog or not self._weekly_dialog.winfo_exists():
            return
        metrics = self.store.get_weekly_efficiency(
            mode=self.weekly_mode_var.get(),
            output_target=self.config.weekly_output_target,
            active_efficiency_target=self.config.weekly_active_efficiency_target,
        )
        history = self.store.get_weekly_efficiency_history(mode=self.weekly_mode_var.get(), weeks=8)
        if self._weekly_detail_mode_var is not None:
            self._weekly_detail_mode_var.set(
                f"{tr(self.config.language, 'rolling_7_days' if self.weekly_mode_var.get() == 'rolling' else 'natural_week')}\n{metrics.label}"
            )
        if self._weekly_detail_output_var is not None:
            self._weekly_detail_output_var.set(tr(self.config.language, "weekly_unit_chars", count=f"{metrics.output:,}"))
        if self._weekly_detail_time_var is not None:
            self._weekly_detail_time_var.set(tr(self.config.language, "weekly_unit_minutes", count=f"{metrics.active_minutes:.1f}"))
        if self._weekly_detail_efficiency_var is not None:
            efficiency_text = tr(self.config.language, "insufficient_history")
            if metrics.active_efficiency is not None:
                efficiency_text = tr(self.config.language, "weekly_unit_chars_per_min", count=f"{metrics.active_efficiency:.1f}")
            self._weekly_detail_efficiency_var.set(efficiency_text)
        if self._weekly_explanation_var is not None:
            explanation = tr(
                self.config.language,
                "weekly_explanation_template",
                output_change=format_weekly_delta(self.config.language, metrics.output_vs_previous_week),
                efficiency_change=format_weekly_delta(self.config.language, metrics.active_efficiency_vs_previous_week),
            )
            self._weekly_explanation_var.set(explanation)
        self._draw_weekly_series_chart(
            self._weekly_output_canvas,
            history,
            value_key="output",
            average_value=metrics.four_week_average_output,
            target_value=float(metrics.output_target) if metrics.output_target is not None else None,
            color=CARD_ACCENT,
        )
        self._draw_weekly_series_chart(
            self._weekly_efficiency_canvas,
            history,
            value_key="active_efficiency",
            average_value=metrics.four_week_average_efficiency,
            target_value=metrics.active_efficiency_target,
            color=ACCENT,
        )

    def _draw_weekly_series_chart(
        self,
        canvas: tk.Canvas | None,
        history: list[dict],
        value_key: str,
        average_value: float | None,
        target_value: float | None,
        color: str,
    ) -> None:
        if canvas is None:
            return
        canvas.delete("all")
        width = canvas.winfo_width() or 760
        height = canvas.winfo_height() or 220
        ml, mr, mt, mb = 34, 20, 18, 24
        cw = max(1, width - ml - mr)
        ch = max(1, height - mt - mb)
        canvas.create_rectangle(0, 0, width, height, fill=CHART_BG, outline="")

        values = [item[value_key] for item in history if item.get(value_key) is not None]
        baseline_candidates = values[:]
        if average_value is not None:
            baseline_candidates.append(average_value)
        if target_value is not None:
            baseline_candidates.append(target_value)
        max_value = max(baseline_candidates, default=0.0)
        if max_value <= 0:
            canvas.create_text(width / 2, height / 2, text=tr(self.config.language, "insufficient_history"), fill=TEXT_TERTIARY, font=(FONT_UI, 10))
            return

        for ratio in (0.0, 0.5, 1.0):
            y = mt + ch * ratio
            value = max_value * (1 - ratio)
            canvas.create_line(ml, y, width - mr, y, fill=CHART_GRID, width=1)
            canvas.create_text(ml - 6, y, text=format_axis_value(int(value)), fill=TEXT_QUATERNARY, font=(FONT_UI, 8), anchor="e")

        if average_value is not None and average_value > 0:
            y = mt + ch - (average_value / max_value) * ch
            canvas.create_line(ml, y, width - mr, y, fill=TEXT_TERTIARY, width=1, dash=(4, 4))
        if target_value is not None and target_value > 0:
            y = mt + ch - (target_value / max_value) * ch
            canvas.create_line(ml, y, width - mr, y, fill=ACCENT_LIGHT, width=2, dash=(6, 4))

        coords: list[tuple[float, float]] = []
        for index, item in enumerate(history):
            value = item.get(value_key)
            if value is None:
                continue
            x = ml if len(history) == 1 else ml + cw * index / (len(history) - 1)
            y = mt + ch - (float(value) / max_value) * ch
            coords.append((x, y))
            canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline="")
            canvas.create_text(x, height - 10, text=item["start_date"][5:], fill=TEXT_QUATERNARY, font=(FONT_UI, 7))
        if len(coords) >= 2:
            flat = [point for coord in coords for point in coord]
            canvas.create_line(*flat, fill=color, width=3, capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def _draw_hourly_chart(self) -> None:
        if self._hourly_canvas is None:
            return
        canvas = self._hourly_canvas
        canvas.delete("all")
        data = self.store.get_hourly_distribution(self._selected_hourly_date())

        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width <= 1:
            width = 620
        if height <= 1:
            height = 220
        ml = min(44, max(34, int(width * 0.07)))
        mr = min(18, max(14, int(width * 0.03)))
        mt = min(24, max(18, int(height * 0.1)))
        mb = min(30, max(24, int(height * 0.13)))
        cw, ch = width - ml - mr, height - mt - mb

        canvas.create_rectangle(0, 0, width, height, fill=CHART_BG, outline="")

        max_total = max((item["total"] for item in data), default=0)
        if max_total <= 0:
            canvas.create_text(width / 2, height / 2, text=tr(self.config.language, "hourly_empty"), fill=TEXT_TERTIARY, font=(FONT_UI, 10))
            return

        num_grid = 3
        for i in range(num_grid + 1):
            ratio = i / num_grid
            y = mt + ch * ratio
            value = int(max_total * (1 - ratio))
            canvas.create_line(ml, y, width - mr, y, fill=CHART_GRID, width=1)
            canvas.create_text(ml - 8, y, text=format_axis_value(value), fill=TEXT_QUATERNARY, font=(FONT_UI, 8), anchor="e")

        slot_width = cw / 24
        bar_width = min(24, max(8, int(slot_width) - 10))
        baseline = mt + ch
        canvas.create_line(ml, baseline, width - mr, baseline, fill=CHART_GRID, width=1)

        for i, item in enumerate(data):
            x = ml + i * slot_width + (slot_width - bar_width) / 2
            total_height = max(4, ch * item["total"] / max_total) if item["total"] > 0 else 0
            if total_height > 0:
                r = min(7, total_height / 2)
                self._rounded_top_bar(canvas, x, baseline - total_height, x + bar_width, baseline, r=r, fill=HOURLY_TYPED, outline="")

            if i % 4 == 0:
                canvas.create_text(x + bar_width / 2, height - 10, text=item["hour"], fill=TEXT_QUATERNARY, font=(FONT_UI, 8))

    def _rounded_top_bar(self, canvas: tk.Canvas, x1: float, y1: float, x2: float, y2: float, r: float = 5, **kwargs) -> int:
        if y2 - y1 < r * 2:
            return canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
        points = [x1, y2, x1, y1 + r, x1 + r, y1, x2 - r, y1, x2, y1 + r, x2, y2]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def _close_history_dialog(self) -> None:
        if self._history_dialog and self._history_dialog.winfo_exists():
            self._history_dialog.destroy()
        self._history_dialog = None
        self._history_tree = None

    def _close_hourly_dialog(self) -> None:
        if self._hourly_dialog and self._hourly_dialog.winfo_exists():
            self._hourly_dialog.destroy()
        self._hourly_dialog = None
        self._hourly_tree = None
        self._hourly_canvas = None
        self._hourly_peak_var = None
        self._hourly_date_var = None
        self._hourly_date_selector = None

    def _close_weekly_dialog(self) -> None:
        if self._weekly_dialog and self._weekly_dialog.winfo_exists():
            self._weekly_dialog.destroy()
        self._weekly_dialog = None
        self._weekly_output_canvas = None
        self._weekly_efficiency_canvas = None
        self._weekly_detail_mode_var = None
        self._weekly_detail_output_var = None
        self._weekly_detail_time_var = None
        self._weekly_detail_efficiency_var = None
        self._weekly_explanation_var = None
