import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import database as db
from .calendar_view import CalendarView
from .constants import FONT_HEADER, FONT_NORMAL, FONT_SMALL


class TeacherDashboard(tk.Frame):
    def __init__(self, parent, app, teacher):
        self.app = app
        self.teacher = teacher
        self.colors = app.colors
        super().__init__(parent, bg=self.colors["bg"])
        self.facilities = db.get_facilities()
        self._build_header()
        self._build_tabs()
        self.calendar_view = CalendarView(
            self.schedule_tab, app, teacher, self.facilities, self.refresh_all,
        )
        self.calendar_view.pack(fill="both", expand=True)
        self.build_my_reservations()
        self.build_all_reservations()

    def _build_header(self):
        c = self.colors
        header = tk.Frame(self, bg=c["header"], height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text=f"{self.teacher['name']}  ({self.teacher['teacher_id']})",
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
            relief="flat", padx=14, pady=6,
            command=self.app.show_login, cursor="hand2",
        ).pack(side="right", pady=13)

    def _build_tabs(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=(10, 14))
        self.notebook = notebook
        self.schedule_tab = tk.Frame(notebook, bg=self.colors["bg"])
        self.myres_tab = tk.Frame(notebook, bg=self.colors["bg"])
        self.all_tab = tk.Frame(notebook, bg=self.colors["bg"])
        notebook.add(self.schedule_tab, text="Weekly Calendar")
        notebook.add(self.myres_tab, text="My Reservations")
        notebook.add(self.all_tab, text="All Reservations")

    def refresh_all(self):
        self.calendar_view.refresh()
        self.build_my_reservations()
        self.build_all_reservations()

    def build_my_reservations(self):
        self._clear_frame(self.myres_tab)
        c = self.colors
        tk.Label(
            self.myres_tab, text="Reservations you made", font=FONT_HEADER,
            bg=c["bg"], fg=c["header"],
        ).pack(anchor="w", padx=8, pady=(10, 4))

        tree_frame = tk.Frame(self.myres_tab, bg=c["bg"])
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)
        columns = ("date", "facility", "time", "purpose")
        self.my_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=13)
        for column, label, width, anchor in [
            ("date", "Date", 175, "w"),
            ("facility", "Facility", 150, "w"),
            ("time", "Time Frame", 190, "center"),
            ("purpose", "Purpose", 380, "w"),
        ]:
            self.my_tree.heading(column, text=label)
            self.my_tree.column(column, width=width, anchor=anchor)
        self.my_tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.my_tree.yview)
        self.my_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        self._my_rows = {}
        for row in db.get_teacher_reservations(self.teacher["teacher_id"]):
            row_id = self.my_tree.insert(
                "", "end",
                values=(
                    self._date_label(row),
                    row["facility_name"],
                    f"{db.to_12h(row['start_time'])} – {db.to_12h(row['end_time'])}",
                    row["purpose"] or "–",
                ),
            )
            self._my_rows[row_id] = row

        actions = tk.Frame(self.myres_tab, bg=c["bg"])
        actions.pack(fill="x", padx=8, pady=8)
        tk.Button(
            actions, text="Cancel selected", bg=c["danger"], fg="#ffffff",
            activebackground=c["warning"], activeforeground="#ffffff",
            relief="flat", padx=14, pady=6, command=self._cancel_selected,
        ).pack(side="left")
        tk.Button(
            actions, text="Refresh", bg=c["panel"], fg=c["text"],
            activebackground=c["muted_panel"], activeforeground=c["text"],
            relief="flat", padx=14, pady=6, command=self.refresh_all,
        ).pack(side="left", padx=8)

    def _cancel_selected(self):
        selected = self.my_tree.selection()
        if not selected:
            messagebox.showinfo("Select a reservation", "Please select a reservation row first.", parent=self)
            return
        row = self._my_rows[selected[0]]
        if not messagebox.askyesno(
            "Cancel reservation",
            f"Cancel {row['facility_name']} on {self._date_label(row)}, "
            f"{db.to_12h(row['start_time'])} – {db.to_12h(row['end_time'])}?",
            parent=self,
        ):
            return
        try:
            db.cancel_reservation(row["reservation_id"], self.teacher["teacher_id"])
        except ValueError as error:
            messagebox.showerror("Cannot cancel", str(error), parent=self)
            return
        self.refresh_all()

    def build_all_reservations(self):
        self._clear_frame(self.all_tab)
        c = self.colors
        tk.Label(
            self.all_tab, text="All active reservations", font=FONT_HEADER,
            bg=c["bg"], fg=c["header"],
        ).pack(anchor="w", padx=8, pady=(10, 4))
        tree_frame = tk.Frame(self.all_tab, bg=c["bg"])
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        columns = ("date", "teacher", "facility", "time", "purpose")
        tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=14)
        for column, label, width, anchor in [
            ("date", "Date", 165, "w"),
            ("teacher", "Staff", 170, "w"),
            ("facility", "Facility", 145, "w"),
            ("time", "Time Frame", 175, "center"),
            ("purpose", "Purpose", 300, "w"),
        ]:
            tree.heading(column, text=label)
            tree.column(column, width=width, anchor=anchor)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

        day_order = {day: index for index, day in enumerate(db.DAYS_OF_WEEK)}
        rows = sorted(
            db.get_all_reservations(),
            key=lambda row: (
                row.get("reservation_date") or "9999-99-99",
                day_order.get(row["day_of_week"], 99),
                row["start_time"],
            ),
        )
        for row in rows:
            tree.insert(
                "", "end",
                values=(
                    self._date_label(row), row["teacher_name"], row["facility_name"],
                    f"{db.to_12h(row['start_time'])} – {db.to_12h(row['end_time'])}",
                    row["purpose"] or "–",
                ),
            )

    @staticmethod
    def _date_label(row):
        reservation_date = row.get("reservation_date")
        if reservation_date:
            return datetime.fromisoformat(reservation_date).strftime("%b %d, %Y")
        return f"Weekly · {row['day_of_week']}"

    @staticmethod
    def _clear_frame(frame):
        for widget in frame.winfo_children():
            widget.destroy()
