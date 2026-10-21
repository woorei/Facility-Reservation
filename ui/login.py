import tkinter as tk
from tkinter import ttk, messagebox

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
        card.place(relx=0.5, rely=0.48, anchor="center", width=450, height=410)

        tk.Label(
            card, text="Facility Reservation System", font=FONT_TITLE,
            bg=c["panel"], fg=c["header"], wraplength=390, justify="center",
        ).pack(pady=(24, 4))
        self.login_title = tk.Label(
            card, text="Staff Login", font=FONT_NORMAL,
            bg=c["panel"], fg=c["muted"],
        )
        self.login_title.pack(pady=(0, 14))

        form = tk.Frame(card, bg=c["panel"])
        form.pack()
        tk.Label(
            form, text="Account type", font=FONT_NORMAL,
            bg=c["panel"], fg=c["text"],
        ).grid(row=0, column=0, sticky="w", pady=8)
        saved_login = getattr(app, "login_form_values", {})
        self.role_var = tk.StringVar(value=saved_login.get("role", "Staff"))
        self.role_combo = ttk.Combobox(
            form, textvariable=self.role_var,
            values=("Staff", "Administrator"), state="readonly", width=21,
        )
        self.role_combo.grid(row=0, column=1, pady=8, padx=8, sticky="ew")
        self.role_combo.bind("<<ComboboxSelected>>", self._on_role_change)

        self.id_label = tk.Label(
            form, text="Staff ID", font=FONT_NORMAL,
            bg=c["panel"], fg=c["text"],
        )
        self.id_label.grid(row=1, column=0, sticky="w", pady=8)
        self.id_entry = tk.Entry(
            form, font=FONT_NORMAL, width=24, bg=c["input"], fg=c["input_text"],
            insertbackground=c["input_text"], relief="solid", bd=1,
        )
        self.id_entry.grid(row=1, column=1, pady=8, padx=8)
        self.id_entry.insert(0, saved_login.get("teacher_id", ""))

        tk.Label(
            form, text="Password", font=FONT_NORMAL,
            bg=c["panel"], fg=c["text"],
        ).grid(row=2, column=0, sticky="w", pady=8)
        password_frame = tk.Frame(form, bg=c["panel"])
        password_frame.grid(row=2, column=1, pady=8, padx=8, sticky="w")
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
        ).pack(pady=22)

        self._on_role_change()
        self.unbind_all("<Return>")
        self.bind_all("<Return>", lambda _event: self.attempt_login())

    def _on_role_change(self, _event=None):
        role = self.role_var.get()
        is_admin = role == "Administrator"
        self.login_title.config(text=f"{role} Login")
        self.id_label.config(text="Administrator ID" if is_admin else "Staff ID")

    def _toggle_theme(self):
        self.app.login_form_values = {
            "teacher_id": self.id_entry.get(),
            "password": self.password_entry.get(),
            "show_password": self.show_password,
            "role": self.role_var.get(),
        }
        self.app.toggle_theme()

    def attempt_login(self):
        account_id = self.id_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()
        if not account_id or not password:
            messagebox.showwarning(
                "Missing info", f"Please enter your {role.lower()} ID and password.", parent=self
            )
            return

        if role == "Administrator":
            administrator = db.authenticate_admin(account_id, password)
            if administrator:
                self.unbind_all("<Return>")
                self.app.show_admin_dashboard(administrator)
                return
        else:
            staff = db.authenticate_teacher(account_id, password)
            if staff:
                self.unbind_all("<Return>")
                self.app.show_dashboard(staff)
                return

        messagebox.showerror(
            "Login failed", f"Invalid {role.lower()} ID or password.", parent=self
        )

    def toggle_password_visibility(self):
        self.show_password = not self.show_password
        self.password_entry.config(show="" if self.show_password else "*")
        self.toggle_pw_btn.config(
            fg=self.app.colors["header"] if self.show_password else self.app.colors["muted"]
        )
