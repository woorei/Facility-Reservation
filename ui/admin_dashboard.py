import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import database as db
from .constants import FONT_TITLE, FONT_HEADER, FONT_NORMAL, FONT_SMALL


class AdminDashboard(tk.Frame):

    def __init__(self, parent, app, administrator):
        self.app = app
        self.administrator = administrator
        self.colors = app.colors
        super().__init__(parent, bg=self.colors["bg"])
        self._build_header()
        self._build_content()
        self.refresh_requests()

    def _build_header(self):
        c = self.colors
        header = tk.Frame(self, bg=c["header"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{self.administrator['name']}  ({self.administrator['admin_id']})",
            font=FONT_HEADER, bg=c["header"], fg="#ffffff",
        ).pack(side="left", padx=20)

        tk.Button(
            header,
            text="☀ Light mode" if self.app.theme_manager.mode == "dark" else "☾ Dark mode",
            bg=c["panel"], fg=c["text"], activebackground=c["muted_panel"],
            activeforeground=c["text"], relief="flat", padx=12, pady=6,
            command=self.app.toggle_theme, cursor="hand2",
        ).pack(side="right", padx=(8, 18), pady=13)
        tk.Button(
            header, text="Log Out", bg=c["danger"], fg="#ffffff",
            activebackground=c["warning"], activeforeground="#ffffff",
            relief="flat", padx=14, pady=6, command=self.app.show_login,
            cursor="hand2",
        ).pack(side="right", pady=13)

    def _build_content(self):
        c = self.colors
        top = tk.Frame(self, bg=c["bg"])
        top.pack(fill="x", padx=18, pady=(18, 8))
        tk.Label(
            top, text="Reservation Approval Queue", font=FONT_TITLE,
            bg=c["bg"], fg=c["header"],
        ).pack(anchor="w")
        tk.Label(
            top,
            text="Review pending requests. Approved bookings appear on the staff calendar.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"],
        ).pack(anchor="w", pady=(3, 0))

        tree_frame = tk.Frame(self, bg=c["bg"])
        tree_frame.pack(fill="both", expand=True, padx=18, pady=8)
        columns = ("date", "staff", "facility", "time", "purpose", "requested")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=16)
        definitions = [
            ("date", "Reservation Date", 165, "w"),
            ("staff", "Staff", 180, "w"),
            ("facility", "Facility", 145, "w"),
            ("time", "Time Frame", 185, "center"),
            ("purpose", "Purpose", 280, "w"),
            ("requested", "Requested At", 165, "center"),
        ]
        for column, label, width, anchor in definitions:
            self.tree.heading(column, text=label)
            self.tree.column(column, width=width, anchor=anchor)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        footer = tk.Frame(self, bg=c["bg"])
        footer.pack(fill="x", padx=18, pady=(2, 18))
        tk.Button(
            footer, text="Approve selected", bg=c["success"], fg="#ffffff",
            activebackground=c["accent"], activeforeground="#ffffff", relief="flat",
            padx=16, pady=8, command=self.approve_selected,
        ).pack(side="left")
        tk.Button(
            footer, text="Reject selected", bg=c["danger"], fg="#ffffff",
            activebackground=c["warning"], activeforeground="#ffffff", relief="flat",
            padx=16, pady=8, command=self.reject_selected,
        ).pack(side="left", padx=8)
        tk.Button(
            footer, text="Refresh", bg=c["panel"], fg=c["text"],
            activebackground=c["muted_panel"], activeforeground=c["text"], relief="flat",
            padx=16, pady=8, command=self.refresh_requests,
        ).pack(side="right")

    def refresh_requests(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.rows = {}
        for row in db.get_pending_reservations():
            reservation_date = row.get("reservation_date")
            if reservation_date:
                date_label = datetime.fromisoformat(reservation_date).strftime("%a, %b %d, %Y")
            else:
                date_label = f"Weekly · {row['day_of_week']}"
            created_at = row.get("created_at", "")
            try:
                requested_label = datetime.fromisoformat(created_at).strftime("%b %d, %I:%M %p")
            except ValueError:
                requested_label = created_at
            item = self.tree.insert(
                "", "end",
                values=(
                    date_label,
                    row["teacher_name"],
                    row["facility_name"],
                    f"{db.to_12h(row['start_time'])} – {db.to_12h(row['end_time'])}",
                    row.get("purpose") or "–",
                    requested_label,
                ),
            )
            self.rows[item] = row

    def _selected_row(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo(
                "Select a request", "Select a pending reservation request first.", parent=self
            )
            return None
        return self.rows.get(selection[0])

    def approve_selected(self):
        row = self._selected_row()
        if not row:
            return
        try:
            db.approve_reservation(row["reservation_id"])
        except ValueError as error:
            messagebox.showerror("Cannot approve request", str(error), parent=self)
            self.refresh_requests()
            return
        messagebox.showinfo(
            "Request approved",
            f"{row['facility_name']} has been approved for {row.get('reservation_date') or row['day_of_week']}.",
            parent=self,
        )
        self.refresh_requests()

    def reject_selected(self):
        row = self._selected_row()
        if not row:
            return
        if not messagebox.askyesno(
            "Reject request",
            f"Reject {row['teacher_name']}'s request for {row['facility_name']}?",
            parent=self,
        ):
            return
        try:
            db.reject_reservation(row["reservation_id"])
        except ValueError as error:
            messagebox.showerror("Cannot reject request", str(error), parent=self)
            self.refresh_requests()
            return
        self.refresh_requests()
