from __future__ import annotations

import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

SETTINGS_PATH = Path(__file__).resolve().parents[1] / "settings.json"

THEMES = {
    "light": {
        "name": "Light",
        "bg": "#f4f6f8",
        "panel": "#ffffff",
        "header": "#20344c",
        "text": "#202938",
        "muted": "#667085",
        "border": "#d0d7e2",
        "accent": "#2b6cb0",
        "success": "#2f855a",
        "warning": "#b7791f",
        "danger": "#c0392b",
        "grid": "#d9e0e8",
        "grid_minor": "#e9edf2",
        "day_header": "#e4eaf1",
        "event_text": "#ffffff",
        "selection": "#2b6cb0",
        "input": "#ffffff",
        "input_text": "#202938",
        "muted_panel": "#eef2f6",
        "taken": "#a0a7b2",
        "events": ["#2878a5", "#33845c", "#a36523", "#8255a1", "#b64e58"],
    },
    "dark": {
        "name": "Dark",
        "bg": "#171a21",
        "panel": "#222733",
        "header": "#11151d",
        "text": "#e6eaf0",
        "muted": "#a0a9b8",
        "border": "#394150",
        "accent": "#60a5fa",
        "success": "#3f9d70",
        "warning": "#c58a3b",
        "danger": "#d45a5a",
        "grid": "#3b4351",
        "grid_minor": "#2b313d",
        "day_header": "#2c3442",
        "event_text": "#ffffff",
        "selection": "#2563eb",
        "input": "#191e27",
        "input_text": "#e6eaf0",
        "muted_panel": "#282f3b",
        "taken": "#687386",
        "events": ["#245f83", "#276746", "#795020", "#65417f", "#873c45"],
    },
}


class ThemeManager:
    """Loads, stores, and applies the active application theme."""

    def __init__(self, settings_path: Path | None = None):
        self.settings_path = settings_path or SETTINGS_PATH
        self.mode = self._load_mode()

    @property
    def colors(self) -> dict:
        return THEMES[self.mode]

    def _load_mode(self) -> str:
        try:
            settings = json.loads(self.settings_path.read_text(encoding="utf-8"))
            mode = settings.get("theme", "light")
            return mode if mode in THEMES else "light"
        except (OSError, json.JSONDecodeError, AttributeError):
            return "light"

    def set_mode(self, mode: str) -> None:
        if mode not in THEMES:
            raise ValueError(f"Unknown theme: {mode}")
        self.mode = mode
        self.save()

    def toggle(self) -> str:
        self.set_mode("dark" if self.mode == "light" else "light")
        return self.mode

    def save(self) -> None:
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = self.settings_path.with_suffix(".tmp")
        temporary_path.write_text(
            json.dumps({"theme": self.mode}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.settings_path)

    def apply_ttk(self, style: ttk.Style) -> None:
        c = self.colors
        try:
            style.theme_use("clam")
        except tk.TclError:  # pragma: no cover, defensive fallback for unusual Tk builds
            pass

        style.configure(
            ".",
            background=c["bg"],
            foreground=c["text"],
            fieldbackground=c["input"],
            bordercolor=c["border"],
            lightcolor=c["border"],
            darkcolor=c["border"],
            troughcolor=c["bg"],
            font=("Segoe UI", 10),
        )
        style.configure("TFrame", background=c["bg"])
        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure(
            "TButton",
            background=c["panel"],
            foreground=c["text"],
            bordercolor=c["border"],
            padding=(9, 5),
        )
        style.map(
            "TButton",
            background=[("active", c["day_header"]), ("pressed", c["border"])],
            foreground=[("disabled", c["muted"])],
        )
        style.configure(
            "TNotebook",
            background=c["bg"],
            bordercolor=c["border"],
            tabmargins=(2, 4, 2, 0),
        )
        style.configure(
            "TNotebook.Tab",
            background=c["day_header"],
            foreground=c["text"],
            padding=(12, 7),
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", c["panel"]), ("active", c["muted_panel"])],
            foreground=[("selected", c["text"])],
        )
        style.configure(
            "Treeview",
            background=c["panel"],
            fieldbackground=c["panel"],
            foreground=c["text"],
            bordercolor=c["border"],
            rowheight=27,
        )
        style.map(
            "Treeview",
            background=[("selected", c["selection"])],
            foreground=[("selected", "#ffffff")],
        )
        style.configure(
            "Treeview.Heading",
            background=c["day_header"],
            foreground=c["text"],
            relief="flat",
            padding=(6, 5),
        )
        style.map("Treeview.Heading", background=[("active", c["muted_panel"])])
        style.configure(
            "TCombobox",
            fieldbackground=c["input"],
            background=c["panel"],
            foreground=c["input_text"],
            arrowcolor=c["text"],
            bordercolor=c["border"],
            padding=5,
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", c["input"])],
            foreground=[("readonly", c["input_text"])],
            selectbackground=[("readonly", c["input"])],
            selectforeground=[("readonly", c["input_text"])],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=c["day_header"],
            troughcolor=c["bg"],
            bordercolor=c["border"],
            arrowcolor=c["text"],
        )
        style.configure(
            "Horizontal.TScrollbar",
            background=c["day_header"],
            troughcolor=c["bg"],
            bordercolor=c["border"],
            arrowcolor=c["text"],
        )

