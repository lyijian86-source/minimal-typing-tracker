from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import (
    ACCENT_DEEP,
    ACCENT_LIGHT,
    BORDER,
    BORDER_INNER,
    BG,
    CARD,
    CARD_ACCENT,
    CARD_ACCENT_SOFT,
    CARD_INNER,
    FONT_DISPLAY,
    FONT_NUMERIC,
    FONT_UI,
    TEXT_ON_ACCENT,
    TEXT_PRIMARY,
    TEXT_QUATERNARY,
    TEXT_SECONDARY,
    TEXT_TERTIARY,
)


class WidgetFactoryMixin:
    def _button(self, parent: tk.Widget, text: str, command, primary: bool) -> tk.Button:
        if primary:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=CARD_ACCENT,
                fg=TEXT_ON_ACCENT,
                activebackground=ACCENT_DEEP,
                activeforeground=TEXT_ON_ACCENT,
                relief=tk.FLAT,
                padx=18,
                pady=8,
                font=(FONT_UI, 9, "bold"),
                highlightthickness=1,
                highlightbackground=CARD_ACCENT,
                bd=0,
            )
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=CARD,
            fg=TEXT_SECONDARY,
            activebackground=ACCENT_LIGHT,
            activeforeground=ACCENT_DEEP,
            relief=tk.FLAT,
            padx=18,
            pady=8,
            font=(FONT_UI, 9, "bold"),
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )

    def _toolbar_button(self, parent: tk.Widget, text: str, command, primary: bool) -> tk.Button:
        if primary:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=CARD_ACCENT,
                fg=TEXT_ON_ACCENT,
                activebackground=ACCENT_DEEP,
                activeforeground=TEXT_ON_ACCENT,
                relief=tk.FLAT,
                padx=16,
                pady=7,
                font=(FONT_UI, 9, "bold"),
                highlightthickness=1,
                highlightbackground=CARD_ACCENT,
                bd=0,
            )
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=BG,
            fg=TEXT_SECONDARY,
            activebackground=CARD,
            activeforeground=ACCENT_DEEP,
            relief=tk.FLAT,
            padx=16,
            pady=7,
            font=(FONT_UI, 9, "bold"),
            highlightthickness=1,
            highlightbackground=BORDER,
            bd=0,
        )

    def _command_button(self, parent: tk.Widget, text: str, command, primary: bool) -> tk.Button:
        if primary:
            return tk.Button(
                parent,
                text=text,
                command=command,
                bg=CARD,
                fg=ACCENT_DEEP,
                activebackground=CARD_INNER,
                activeforeground=TEXT_SECONDARY,
                relief=tk.FLAT,
                padx=12,
                pady=5,
                font=(FONT_UI, 8, "bold"),
                highlightthickness=0,
                bd=0,
            )
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=CARD,
            fg=TEXT_TERTIARY,
            activebackground=CARD_INNER,
            activeforeground=ACCENT_DEEP,
            relief=tk.FLAT,
            padx=10,
            pady=5,
            font=(FONT_UI, 8, "bold"),
            highlightthickness=0,
            bd=0,
        )

    def _card(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground=BORDER, padx=26, pady=24)

    def _subcard(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=CARD_INNER, highlightthickness=0, padx=18, pady=16)

    def _dialog_header(self, parent: tk.Widget, title: str, description: str) -> tk.Frame:
        header = tk.Frame(parent, bg=CARD_ACCENT, highlightthickness=1, highlightbackground=CARD_ACCENT_SOFT, padx=24, pady=22)
        header.pack(fill=tk.X)
        tk.Label(header, text=title, bg=CARD_ACCENT, fg=TEXT_ON_ACCENT, font=(FONT_DISPLAY, 20)).pack(anchor=tk.W)
        tk.Label(header, text=description, bg=CARD_ACCENT, fg="#BBC4B8", font=(FONT_UI, 8), wraplength=660, justify=tk.LEFT).pack(anchor=tk.W, pady=(8, 0))
        return header

    def _hero_chip(self, parent: tk.Widget, title: str, var: tk.StringVar, wraplength: int = 140) -> tk.Frame:
        chip = tk.Frame(parent, bg=CARD_ACCENT_SOFT, highlightthickness=0, padx=14, pady=11)
        tk.Label(chip, text=title, bg=CARD_ACCENT_SOFT, fg="#929A8E", font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        tk.Label(chip, textvariable=var, bg=CARD_ACCENT_SOFT, fg=TEXT_ON_ACCENT, font=(FONT_UI, 12, "bold"), wraplength=wraplength, justify=tk.LEFT).pack(anchor=tk.W, pady=(5, 0))
        return chip

    def _status_line(
        self,
        parent: tk.Widget,
        label: str,
        var: tk.StringVar | None = None,
        color: str = TEXT_TERTIARY,
        static_text: str | None = None,
    ) -> tk.Frame:
        row = tk.Frame(parent, bg=CARD_INNER)
        tk.Label(row, text=label, bg=CARD_INNER, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold"), width=8, anchor="w").pack(side=tk.LEFT)
        if var is not None:
            tk.Label(row, textvariable=var, bg=CARD_INNER, fg=color, font=(FONT_UI, 8), wraplength=320, justify=tk.LEFT, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        else:
            tk.Label(row, text=static_text or "", bg=CARD_INNER, fg=color, font=(FONT_UI, 8), wraplength=320, justify=tk.LEFT, anchor="w").pack(side=tk.LEFT, fill=tk.X, expand=True)
        return row

    def _tile(self, parent: tk.Frame, title: str, var: tk.StringVar, row: int, col: int) -> None:
        tile = tk.Frame(parent, bg=CARD_INNER, highlightthickness=1, highlightbackground=BORDER_INNER, padx=16, pady=14)
        tile.grid(row=row, column=col, sticky="nsew", padx=4, pady=4)
        tk.Label(tile, text=title, bg=CARD_INNER, fg=TEXT_TERTIARY, font=(FONT_UI, 9)).pack(anchor=tk.W)
        tk.Label(tile, textvariable=var, bg=CARD_INNER, fg=TEXT_PRIMARY, font=(FONT_UI, 11, "bold"), wraplength=210, justify=tk.LEFT).pack(anchor=tk.W, pady=(7, 0))

    def _metric_block(self, parent: tk.Widget, title: str, items: list[tuple[str, tk.StringVar]], columns: int = 2) -> tk.Frame:
        block = tk.Frame(parent, bg=CARD)
        tk.Label(block, text=title, bg=CARD, fg=ACCENT_DEEP, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        grid = tk.Frame(block, bg=CARD)
        grid.pack(fill=tk.X, pady=(14, 0))
        for column in range(columns):
            grid.grid_columnconfigure(column, weight=1)

        for index, (label, var) in enumerate(items):
            row = index // columns
            column = index % columns
            cell = tk.Frame(grid, bg=CARD, padx=0, pady=0)
            cell.grid(row=row, column=column, sticky="nsew", padx=(0 if column == 0 else 16, 0), pady=(0 if row == 0 else 14, 0))
            tk.Label(cell, text=label, bg=CARD, fg=TEXT_QUATERNARY, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
            tk.Label(cell, textvariable=var, bg=CARD, fg=TEXT_PRIMARY, font=(FONT_NUMERIC, 22), wraplength=210, justify=tk.LEFT).pack(anchor=tk.W, pady=(6, 0))

        return block

    def _trend_stat(self, parent: tk.Widget, title: str, var: tk.StringVar) -> tk.Frame:
        stat = tk.Frame(parent, bg=CARD_INNER, highlightthickness=1, highlightbackground=BORDER_INNER, padx=14, pady=12)
        tk.Label(stat, text=title, bg=CARD_INNER, fg=TEXT_TERTIARY, font=(FONT_UI, 8, "bold")).pack(anchor=tk.W)
        tk.Label(stat, textvariable=var, bg=CARD_INNER, fg=TEXT_SECONDARY, font=(FONT_UI, 10, "bold")).pack(anchor=tk.W, pady=(6, 0))
        return stat

    def _configure_ttk(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TypeRecord.Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT_PRIMARY, rowheight=38, borderwidth=0, relief="flat", font=(FONT_UI, 10))
        style.configure("TypeRecord.Treeview.Heading", background=CARD_INNER, foreground=TEXT_TERTIARY, relief="flat", font=(FONT_UI, 9, "bold"))
        style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=BG, bordercolor=BG, arrowcolor=TEXT_QUATERNARY, relief="flat", width=8)
        style.map("TypeRecord.Treeview", background=[("selected", ACCENT_LIGHT)], foreground=[("selected", TEXT_PRIMARY)])
        style.configure("TypeRecord.TCombobox", fieldbackground=CARD, background=CARD, foreground=TEXT_SECONDARY, arrowcolor=TEXT_TERTIARY, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
