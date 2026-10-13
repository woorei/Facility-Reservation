import tkinter as tk
from tkinter import messagebox

import database as db
from .constants import FONT_TITLE, FONT_HEADER, FONT_NORMAL


class LoginFrame(tk.Frame):
    def __init__(self, parent, app):
        self.app = app
        c = app.colors
        super().__init__(parent, bg=c["bg"])

        toolbar = tk.Frame(self, bg=c["bg"])
        toolbar.pack(fill="x", padx=18, pady=14)
        tk.Button(
            toolbar,
            text="☀ Light mode" if app.theme_manager.mode == "dark" else "☾ Dark mode",
            command=self._toggle_theme,
            bg=c["panel"], fg=c["text"], activebackground=c["muted_panel"],
            activeforeground=c["text"], relief="flat", padx=12, pady=7,
            cursor="hand2",
        ).pack(side="right")

        card = tk.Frame(self, bg=c["panel"], bd=1, relief="solid", highlightbackground=c["border"])
        card.place(relx=0.5, rely=0.48, anchor="center", width=430, height=355)

        tk.Label(
            card, text="Facility Reservation System", font=FONT_TITLE,
            bg=c["panel"], fg=c["header"], wraplength=380, justify="center",
        ).pack(pady=(28, 4))
        tk.Label(
            card, text="Staff Login", font=FONT_NORMAL,
            bg=c["panel"], fg=c["muted"],
        ).pack(pady=(0, 22))

        form = tk.Frame(card, bg=c["panel"])
        form.pack()
        tk.Label(form, text="Staff ID", font=FONT_NORMAL, bg=c["panel"], fg=c["text"]).grid(
            row=0, column=0, sticky="w", pady=8
        )
        self.id_entry = tk.Entry(
            form, font=FONT_NORMAL, width=24, bg=c["input"], fg=c["input_text"],
            insertbackground=c["input_text"], relief="solid", bd=1,
        )
        self.id_entry.grid(row=0, column=1, pady=8, padx=8)
        saved_login = getattr(app, "login_form_values", {})
        self.id_entry.insert(0, saved_login.get("teacher_id", ""))

        tk.Label(form, text="Password", font=FONT_NORMAL, bg=c["panel"], fg=c["text"]).grid(
            row=1, column=0, sticky="w", pady=8
        )
        password_frame = tk.Frame(form, bg=c["panel"])
        password_frame.grid(row=1, column=1, pady=8, padx=8, sticky="w")
        self.password_entry = tk.Entry(
            password_frame, font=FONT_NORMAL, width=20, show="*", bg=c["input"],
            fg=c["input_text"], insertbackground=c["input_text"], relief="solid", bd=1,
        )
        self.password_entry.pack(side="left")
        self.password_entry.insert(0, saved_login.get("password", ""))
        self.show_password = bool(saved_login.get("show_password", False))
        self.password_entry.config(show="" if self.show_password else "*")
        self.toggle_pw_btn = tk.Button(
            password_frame, text="◉", font=FONT_NORMAL, bg=c["panel"], bd=0,
            fg=c["muted"], activeforeground=c["header"], cursor="hand2",
            command=self.toggle_password_visibility,
        )
        self.toggle_pw_btn.pack(side="left", padx=(5, 0))

        tk.Button(
            card, text="Log In", font=FONT_HEADER, bg=c["header"], fg="#ffffff",
            activebackground=c["accent"], activeforeground="#ffffff", relief="flat",
            padx=28, pady=8, cursor="hand2", command=self.attempt_login,
        ).pack(pady=23)

        # Remove the prior login screen's global binding before adding this one.
        self.unbind_all("<Return>")
        self._return_binding = self.bind_all("<Return>", lambda _event: self.attempt_login())

    def _toggle_theme(self):
        # The theme switch rebuilds the current screen. Save its values first.
        self.app.login_form_values = {
            "teacher_id": self.id_entry.get(),
            "password": self.password_entry.get(),
            "show_password": self.show_password,
        }
        self.app.toggle_theme()

    def attempt_login(self):
        teacher_id = self.id_entry.get().strip()
        password = self.password_entry.get().strip()
        if not teacher_id or not password:
            messagebox.showwarning("Missing info", "Please enter both Staff ID and Password.", parent=self)
            return
        teacher = db.authenticate_teacher(teacher_id, password)
        if teacher:
            self.unbind_all("<Return>")
            self.app.show_dashboard(teacher)
        else:
            messagebox.showerror("Login failed", "Invalid Staff ID or Password.", parent=self)

    def toggle_password_visibility(self):
        self.show_password = not self.show_password
        self.password_entry.config(show="" if self.show_password else "*")
        self.toggle_pw_btn.config(fg=self.app.colors["header"] if self.show_password else self.app.colors["muted"])
