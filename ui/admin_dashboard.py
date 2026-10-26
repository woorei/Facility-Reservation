import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

import database as db
from .constants import FONT_TITLE, FONT_HEADER, FONT_NORMAL, FONT_SMALL


class AdminDashboard(tk.Frame):
    """Admin dashboard for approvals, reservation history, and staff accounts."""

    def __init__(self, parent, app, administrator):
        self.app = app
        self.administrator = administrator
        self.colors = app.colors
        super().__init__(parent, bg=self.colors["bg"])

        self.pending_rows = {}
        self.reservation_rows = {}
        self.teacher_rows = {}
        self.facility_rows = {}

        self._build_header()
        self._build_content()
        self.refresh_all()

    def _build_header(self):
        c = self.colors
        header = tk.Frame(self, bg=c["header"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header,
            text=f"{self.administrator['name']}  ({self.administrator['admin_id']})",
            font=FONT_HEADER,
            bg=c["header"],
            fg="#ffffff",
        ).pack(side="left", padx=20)

        tk.Button(
            header,
            text="☀ Light mode" if self.app.theme_manager.mode == "dark" else "☾ Dark mode",
            bg=c["panel"], fg=c["text"],
            activebackground=c["muted_panel"], activeforeground=c["text"],
            relief="flat", padx=12, pady=6,
            command=self.app.toggle_theme, cursor="hand2",
        ).pack(side="right", padx=(8, 18), pady=13)

        tk.Button(
            header, text="Log Out", bg=c["danger"], fg="#ffffff",
            activebackground=c["warning"], activeforeground="#ffffff",
            relief="flat", padx=14, pady=6,
            command=self.app.show_login, cursor="hand2",
        ).pack(side="right", pady=13)

    def _build_content(self):
        c = self.colors
        top = tk.Frame(self, bg=c["bg"])
        top.pack(fill="x", padx=18, pady=(16, 6))
        tk.Label(
            top, text="Administrator Dashboard", font=FONT_TITLE,
            bg=c["bg"], fg=c["header"],
        ).pack(anchor="w")
        tk.Label(
            top,
            text="Review requests, monitor every reservation, and manage staff access.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"],
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=18, pady=(6, 12))

        self.pending_tab = tk.Frame(self.notebook, bg=c["bg"])
        self.reservations_tab = tk.Frame(self.notebook, bg=c["bg"])
        self.teachers_tab = tk.Frame(self.notebook, bg=c["bg"])
        self.facilities_tab = tk.Frame(self.notebook, bg=c["bg"])
        self.notebook.add(self.pending_tab, text="Pending Requests")
        self.notebook.add(self.reservations_tab, text="All Reservations")
        self.notebook.add(self.teachers_tab, text="Staff Accounts")
        self.notebook.add(self.facilities_tab, text="Facilities")

        self._build_pending_tab()
        self._build_reservations_tab()
        self._build_teachers_tab()
        self._build_facilities_tab()

    def _make_tree(self, parent, columns, definitions, height=15):
        outer = tk.Frame(parent, bg=self.colors["bg"])
        outer.pack(fill="both", expand=True, padx=10, pady=10)
        tree = ttk.Treeview(outer, columns=columns, show="headings", height=height)
        for column, title, width, anchor in definitions:
            tree.heading(column, text=title)
            tree.column(column, width=width, anchor=anchor, stretch=True)
        vertical = ttk.Scrollbar(outer, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(outer, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)
        return tree

    def _make_button(self, parent, text, command, color=None, side="left", padx=0):
        c = self.colors
        button = tk.Button(
            parent, text=text, command=command,
            bg=color or c["panel"], fg="#ffffff" if color else c["text"],
            activebackground=c["muted_panel"], activeforeground=c["text"],
            relief="flat", padx=14, pady=7, cursor="hand2",
        )
        button.pack(side=side, padx=padx, pady=8)
        return button

    def _build_pending_tab(self):
        c = self.colors
        tk.Label(
            self.pending_tab,
            text="Requests waiting for administrator review.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"],
        ).pack(anchor="w", padx=12, pady=(10, 0))
        self.pending_tree = self._make_tree(
            self.pending_tab,
            ("id", "date", "staff", "facility", "time", "purpose", "requested"),
            [
                ("id", "ID", 60, "center"),
                ("date", "Reservation Date", 150, "w"),
                ("staff", "Staff", 170, "w"),
                ("facility", "Facility", 140, "w"),
                ("time", "Time Frame", 160, "center"),
                ("purpose", "Purpose", 220, "w"),
                ("requested", "Requested At", 150, "center"),
            ],
        )
        footer = tk.Frame(self.pending_tab, bg=c["bg"])
        footer.pack(fill="x", padx=10, pady=(0, 6))
        self._make_button(footer, "Approve selected", self.approve_selected, c["success"])
        self._make_button(footer, "Reject selected", self.reject_selected, c["danger"], padx=8)
        self._make_button(footer, "Refresh", self.refresh_all, side="right")

    def _build_reservations_tab(self):
        c = self.colors
        tk.Label(
            self.reservations_tab,
            text="View current and past requests. Force cancellation requires a reason and is recorded in the admin log.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"], wraplength=1000,
        ).pack(anchor="w", padx=12, pady=(10, 0))
        self.reservations_tree = self._make_tree(
            self.reservations_tab,
            ("id", "date", "staff_id", "staff", "facility", "time", "purpose", "status", "cancel_reason"),
            [
                ("id", "ID", 55, "center"),
                ("date", "Reservation Date", 140, "w"),
                ("staff_id", "Staff ID", 95, "w"),
                ("staff", "Staff Name", 145, "w"),
                ("facility", "Facility", 130, "w"),
                ("time", "Time", 145, "center"),
                ("purpose", "Purpose", 175, "w"),
                ("status", "Status", 100, "center"),
                ("cancel_reason", "Cancellation Reason", 220, "w"),
            ],
        )
        footer = tk.Frame(self.reservations_tab, bg=c["bg"])
        footer.pack(fill="x", padx=10, pady=(0, 6))
        self._make_button(footer, "Force cancel selected", self.force_cancel_selected, c["danger"])
        self._make_button(footer, "Refresh", self.refresh_all, side="right")

    def _build_teachers_tab(self):
        c = self.colors
        tk.Label(
            self.teachers_tab,
            text="Deactivation blocks future logins but keeps reservation history. Reactivate an account to restore access.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"], wraplength=1000,
        ).pack(anchor="w", padx=12, pady=(10, 0))
        self.teachers_tree = self._make_tree(
            self.teachers_tab,
            ("teacher_id", "name", "account_status", "reservation_count"),
            [
                ("teacher_id", "Staff ID", 140, "w"),
                ("name", "Name", 260, "w"),
                ("account_status", "Account Status", 150, "center"),
                ("reservation_count", "Total Reservations", 150, "center"),
            ],
        )
        footer = tk.Frame(self.teachers_tab, bg=c["bg"])
        footer.pack(fill="x", padx=10, pady=(0, 6))
        self._make_button(footer, "Add Teacher", self.add_teacher_dialog, c["success"])
        self._make_button(footer, "Deactivate / Reactivate selected", self.toggle_teacher_active, c["danger"], padx=8)
        self._make_button(footer, "Refresh", self.refresh_all, side="right")

    def _build_facilities_tab(self):
        c = self.colors
        tk.Label(
            self.facilities_tab,
            text="Manage the facilities available for reservations. New facilities appear in the booking interface when it reloads its facility list.",
            font=FONT_NORMAL, bg=c["bg"], fg=c["muted"], wraplength=1000,
        ).pack(anchor="w", padx=12, pady=(10, 0))
        self.facilities_tree = self._make_tree(
            self.facilities_tab,
            ("facility_id", "name", "reservation_count"),
            [
                ("facility_id", "Facility ID", 120, "center"),
                ("name", "Facility Name", 320, "w"),
                ("reservation_count", "Reservations on Record", 180, "center"),
            ],
        )
        footer = tk.Frame(self.facilities_tab, bg=c["bg"])
        footer.pack(fill="x", padx=10, pady=(0, 6))
        self._make_button(footer, "Add Facility", self.add_facility_dialog, c["success"])
        self._make_button(footer, "Refresh", self.refresh_all, side="right")

    @staticmethod
    def _date_label(row):
        reservation_date = row.get("reservation_date")
        if reservation_date:
            try:
                return datetime.fromisoformat(reservation_date).strftime("%a, %b %d, %Y")
            except (TypeError, ValueError):
                return str(reservation_date)
        return f"Weekly: {row.get('day_of_week', '')}"

    @staticmethod
    def _time_label(row):
        return f"{db.to_12h(row['start_time'])} - {db.to_12h(row['end_time'])}"

    @staticmethod
    def _requested_label(created_at):
        try:
            return datetime.fromisoformat(created_at).strftime("%b %d, %Y %I:%M %p")
        except (TypeError, ValueError):
            return created_at or ""

    def refresh_all(self):
        self.refresh_requests()
        self.refresh_reservations()
        self.refresh_teachers()
        self.refresh_facilities()

    def refresh_requests(self):
        for item in self.pending_tree.get_children():
            self.pending_tree.delete(item)
        self.pending_rows = {}
        for row in db.get_pending_reservations():
            item = self.pending_tree.insert(
                "", "end",
                values=(
                    row["reservation_id"], self._date_label(row), row["teacher_name"],
                    row["facility_name"], self._time_label(row), row.get("purpose") or "",
                    self._requested_label(row.get("created_at", "")),
                ),
            )
            self.pending_rows[item] = row

    def refresh_reservations(self):
        for item in self.reservations_tree.get_children():
            self.reservations_tree.delete(item)
        self.reservation_rows = {}
        for row in db.get_admin_reservations():
            item = self.reservations_tree.insert(
                "", "end",
                values=(
                    row["reservation_id"], self._date_label(row), row["teacher_id"],
                    row["teacher_name"], row["facility_name"], self._time_label(row),
                    row.get("purpose") or "", row["status"],
                    row.get("cancellation_reason") or "",
                ),
            )
            self.reservation_rows[item] = row

    def refresh_teachers(self):
        for item in self.teachers_tree.get_children():
            self.teachers_tree.delete(item)
        self.teacher_rows = {}
        for row in db.get_admin_teachers():
            status = "Active" if row["is_active"] else "Deactivated"
            item = self.teachers_tree.insert(
                "", "end",
                values=(row["teacher_id"], row["name"], status, row["reservation_count"]),
            )
            self.teacher_rows[item] = row

    def refresh_facilities(self):
        for item in self.facilities_tree.get_children():
            self.facilities_tree.delete(item)
        self.facility_rows = {}
        for row in db.get_admin_facilities():
            item = self.facilities_tree.insert(
                "", "end",
                values=(row["facility_id"], row["name"], row["reservation_count"]),
            )
            self.facility_rows[item] = row

    def add_teacher_dialog(self):
        c = self.colors
        dialog = tk.Toplevel(self)
        dialog.title("Add Teacher")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.winfo_toplevel())
        dialog.resizable(False, False)
        dialog.grab_set()

        body = tk.Frame(dialog, bg=c["bg"])
        body.pack(fill="both", expand=True, padx=18, pady=16)
        tk.Label(
            body, text="Create a staff login", font=FONT_HEADER,
            bg=c["bg"], fg=c["header"],
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        fields = [
            ("Staff ID", "teacher_id", "e.g. T-0004", False),
            ("Full name", "name", "Teacher's full name", False),
            ("Initial password", "password", "At least 6 characters", True),
        ]
        entries = {}
        for index, (label, key, placeholder, secret) in enumerate(fields, start=1):
            tk.Label(body, text=label, font=FONT_NORMAL, bg=c["bg"], fg=c["text"]).grid(
                row=index, column=0, sticky="w", padx=(0, 12), pady=5
            )
            entry = tk.Entry(
                body, width=32, font=FONT_NORMAL, show="*" if secret else "",
                relief="solid", bd=1,
            )
            entry.grid(row=index, column=1, sticky="ew", pady=5, ipady=5)
            entry.insert(0, "")
            entries[key] = entry

        tk.Label(
            body,
            text="The teacher will be able to log in with this ID and initial password.",
            font=FONT_SMALL, bg=c["bg"], fg=c["muted"], wraplength=340,
        ).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 4))

        buttons = tk.Frame(body, bg=c["bg"])
        buttons.grid(row=5, column=0, columnspan=2, sticky="e", pady=(10, 0))

        def save():
            try:
                db.add_teacher(
                    entries["teacher_id"].get(),
                    entries["name"].get(),
                    entries["password"].get(),
                    self.administrator["admin_id"],
                )
            except ValueError as error:
                messagebox.showerror("Unable to add teacher", str(error), parent=dialog)
                return
            except Exception as error:
                messagebox.showerror(
                    "Unable to add teacher",
                    f"The staff account was not added. Details: {error}",
                    parent=dialog,
                )
                return
            dialog.destroy()
            self.refresh_all()
            messagebox.showinfo(
                "Teacher added", "The teacher account has been created and is active.", parent=self
            )

        tk.Button(
            buttons, text="Cancel", command=dialog.destroy, bg=c["panel"], fg=c["text"],
            relief="flat", padx=14, pady=7, cursor="hand2",
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            buttons, text="Add Teacher", command=save, bg=c["success"], fg="#ffffff",
            relief="flat", padx=14, pady=7, cursor="hand2",
        ).pack(side="left")
        entries["teacher_id"].focus_set()
        dialog.bind("<Return>", lambda _event: save())
        self.wait_window(dialog)

    def add_facility_dialog(self):
        name = simpledialog.askstring(
            "Add Facility",
            "Enter the new facility name:",
            parent=self,
        )
        if name is None:
            return
        try:
            db.add_facility(name, self.administrator["admin_id"])
        except ValueError as error:
            messagebox.showerror("Unable to add facility", str(error), parent=self)
            return
        except Exception as error:
            messagebox.showerror(
                "Unable to add facility",
                f"The facility was not added. Details: {error}",
                parent=self,
            )
            return
        self.refresh_all()
        messagebox.showinfo(
            "Facility added",
            "The facility has been added to the database.",
            parent=self,
        )

    def _selected_row(self, tree, rows, label):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo("Select a record", f"Select {label} first.", parent=self)
            return None
        return rows.get(selection[0])

    def approve_selected(self):
        row = self._selected_row(self.pending_tree, self.pending_rows, "a pending request")
        if not row:
            return
        try:
            db.approve_reservation(row["reservation_id"])
        except ValueError as error:
            messagebox.showerror("Cannot approve request", str(error), parent=self)
            self.refresh_all()
            return
        messagebox.showinfo("Request approved", "The reservation has been approved.", parent=self)
        self.refresh_all()

    def reject_selected(self):
        row = self._selected_row(self.pending_tree, self.pending_rows, "a pending request")
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
            self.refresh_all()
            return
        self.refresh_all()

    def toggle_teacher_active(self):
        row = self._selected_row(self.teachers_tree, self.teacher_rows, "a staff account")
        if not row:
            return
        currently_active = bool(row["is_active"])
        next_active = not currently_active
        action = "deactivate" if currently_active else "reactivate"
        if not messagebox.askyesno(
            f"{action.title()} staff account",
            f"Do you want to {action} {row['name']} ({row['teacher_id']})?\n\n"
            "Existing reservations and history will be preserved.",
            parent=self,
        ):
            return
        try:
            db.set_teacher_active(
                row["teacher_id"], next_active, self.administrator["admin_id"]
            )
        except ValueError as error:
            messagebox.showerror("Account update failed", str(error), parent=self)
            return
        self.refresh_all()
        state = "reactivated" if next_active else "deactivated"
        messagebox.showinfo("Staff account updated", f"The account was {state}.", parent=self)

    def force_cancel_selected(self):
        row = self._selected_row(
            self.reservations_tree, self.reservation_rows, "a reservation"
        )
        if not row:
            return
        if row["status"] not in ("ACTIVE", "PENDING"):
            messagebox.showinfo(
                "Cannot force-cancel",
                "Only active reservations and pending requests can be force-cancelled.",
                parent=self,
            )
            return

        reason = simpledialog.askstring(
            "Reason for force cancellation",
            "Enter the reason for cancelling this reservation (required):",
            parent=self,
        )
        if reason is None:
            return
        reason = reason.strip()
        if not reason:
            messagebox.showerror(
                "Reason required", "Enter a reason before force-cancelling.", parent=self
            )
            return
        if len(reason) > 500:
            messagebox.showerror(
                "Reason too long", "Use 500 characters or fewer.", parent=self
            )
            return

        confirm = messagebox.askyesno(
            "Confirm force cancellation",
            f"Cancel reservation #{row['reservation_id']} for {row['teacher_name']}?\n\n"
            f"Reason: {reason}\n\nThis action will be recorded in the admin log.",
            parent=self,
        )
        if not confirm:
            return

        try:
            db.force_cancel_reservation(
                row["reservation_id"], self.administrator["admin_id"], reason
            )
        except ValueError as error:
            messagebox.showerror("Cancellation failed", str(error), parent=self)
            self.refresh_all()
            return
        self.refresh_all()
        messagebox.showinfo("Reservation cancelled", "The reservation was cancelled.", parent=self)
