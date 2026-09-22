from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import database as db
from .constants import *

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import ReservationApp

# LOGIN ==================================================================

class LoginFrame(tk.Frame):
    def __init__(self, parent, app: ReservationApp):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app

        card = tk.Frame(self, bg=COLOR_WHITE, bd=1, relief="solid")
        card.place(relx=0.5, rely=0.45, anchor="center", width=400, height=330)

        tk.Label(card, text="Facility Reservation System", font=FONT_TITLE, bg=COLOR_WHITE,
                 fg=COLOR_HEADER, wraplength=360, justify="center").pack(pady=(26, 4))
        tk.Label(card, text="Teacher Login", font=FONT_NORMAL, bg=COLOR_WHITE,
                 fg="#666").pack(pady=(0, 20))

        form = tk.Frame(card, bg=COLOR_WHITE)
        form.pack()

        tk.Label(form, text="Teacher ID", font=FONT_NORMAL, bg=COLOR_WHITE).grid(
            row=0, column=0, sticky="w", pady=8)
        self.id_entry = tk.Entry(form, font=FONT_NORMAL, width=24)
        self.id_entry.grid(row=0, column=1, pady=8, padx=8)
        self.id_entry.focus_set()

        tk.Label(form, text="Password", font=FONT_NORMAL, bg=COLOR_WHITE).grid(
            row=1, column=0, sticky="w", pady=8)

        pw_frame = tk.Frame(form, bg=COLOR_WHITE)
        pw_frame.grid(row=1, column=1, pady=8, padx=8, sticky="w")

        self.pw_entry = tk.Entry(pw_frame, font=FONT_NORMAL, width=20, show="*")
        self.pw_entry.pack(side="left")

        self.show_password = False
        self.toggle_pw_btn = tk.Button(
        pw_frame, text="\U0001F441", font=FONT_NORMAL, bg=COLOR_WHITE, bd=0,
        fg="#888", activeforeground=COLOR_HEADER, cursor="hand2",
        command=self.toggle_password_visibility,
)
        self.toggle_pw_btn.pack(side="left", padx=(4, 0))

        tk.Button(card, text="Log In", font=FONT_HEADER, bg=COLOR_HEADER, fg="white",
                  activebackground="#324a68", activeforeground="white", relief="flat",
                  padx=24, pady=7, command=self.attempt_login).pack(pady=22)

        self.bind_all("<Return>", lambda e: self.attempt_login())

    def attempt_login(self):
        tid = self.id_entry.get().strip()
        pw = self.pw_entry.get().strip()
        if not tid or not pw:
            messagebox.showwarning("Missing info", "Please enter both Teacher ID and Password.")
            return
        teacher = db.authenticate_teacher(tid, pw)
        if teacher:
            self.unbind_all("<Return>")
            self.app.show_dashboard(teacher)
        else:
            messagebox.showerror("Login failed", "Invalid Teacher ID or Password.")
        
    def toggle_password_visibility(self):
        self.show_password = not self.show_password
        self.pw_entry.config(show="" if self.show_password else "*")
        self.toggle_pw_btn.config(fg=COLOR_HEADER if self.show_password else "#888")