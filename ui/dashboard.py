from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from .constants import *
from .booking import BookingWindow

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app import ReservationApp

# TEACHER DASHBOARD ==================================================================

class TeacherDashboard(tk.Frame):
    def __init__(self, parent, app: ReservationApp, teacher):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        self.teacher = teacher
        self.facilities = db.get_facilities()

        header = tk.Frame(self, bg=COLOR_HEADER, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=f"{teacher['name']}  ({teacher['teacher_id']})", font=FONT_HEADER,
                 bg=COLOR_HEADER, fg="white").pack(side="left", padx=20)
        tk.Button(header, text="Log Out", bg="#c0392b", fg="white", relief="flat", padx=14,
                  command=self.app.show_login).pack(side="right", padx=20)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=(10, 14))

        self.schedule_tab = tk.Frame(notebook, bg=COLOR_BG)
        self.myres_tab = tk.Frame(notebook, bg=COLOR_BG)
        self.all_tab = tk.Frame(notebook, bg=COLOR_BG)
        notebook.add(self.schedule_tab, text="Facility Schedule")
        notebook.add(self.myres_tab, text="My Reservations")
        notebook.add(self.all_tab, text="All Reservations")

        self.build_schedule_grid()
        self.build_my_reservations()
        self.build_all_reservations()

    def refresh_all(self):
        self.build_schedule_grid()
        self.build_my_reservations()
        self.build_all_reservations()

    # ---- Tab 1: the Days x Facilities grid -------------------------------
    def build_schedule_grid(self):
        for w in self.schedule_tab.winfo_children():
            w.destroy()

        tk.Label(self.schedule_tab,
                 text="Click any cell to see that day's bookings and reserve a time slot.",
                 font=FONT_SMALL, bg=COLOR_BG, fg="#555").pack(anchor="w", pady=(8, 6), padx=6)

        table_frame = tk.Frame(self.schedule_tab, bg=COLOR_BG)
        table_frame.pack(fill="y", expand=True, anchor="n")

        canvas = tk.Canvas(table_frame, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        grid_frame = tk.Frame(canvas, bg=COLOR_BG)

        grid_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="y")
        scrollbar.pack(side="left", fill="y")

        tk.Label(grid_frame, text="Day", font=FONT_HEADER, bg=COLOR_HEADER, fg="white",
                 width=12, height=2).grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        for c, fac in enumerate(self.facilities, start=1):
            tk.Label(grid_frame, text=fac["name"], font=FONT_HEADER, bg=COLOR_HEADER, fg="white",
                     width=18, height=2).grid(row=0, column=c, sticky="nsew", padx=1, pady=1)

        total_slots = len(db.generate_time_slots())
        for r, day in enumerate(db.DAYS_OF_WEEK, start=1):
            tk.Label(grid_frame, text=day, font=FONT_NORMAL, bg="#dfe6ee",
                     width=12, height=3).grid(row=r, column=0, sticky="nsew", padx=1, pady=1)
            for c, fac in enumerate(self.facilities, start=1):
                taken = db.taken_time_points(fac["facility_id"], day)
                booked = len(taken)
                if booked == 0:
                    bg, label = COLOR_GREEN, "Fully available"
                elif booked >= total_slots:
                    bg, label = COLOR_TAKEN, "Fully booked"
                else:
                    bg, label = COLOR_ORANGE, f"{booked}/{total_slots} slots taken"
                tk.Button(grid_frame, text=label, bg=bg, fg="white", font=FONT_SMALL,
                          width=18, height=3, relief="flat", wraplength=120,
                          command=lambda f=fac, d=day: self.open_booking_window(f, d)
                          ).grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                self.update_idletasks()
        canvas.configure(width=grid_frame.winfo_reqwidth())

    def open_booking_window(self, facility, day):
        BookingWindow(self.app, self.teacher, facility, day, on_close=self.refresh_all)

    # ---- Tab 2: teacher's own bookings -------------------------------
    def build_my_reservations(self):
        for w in self.myres_tab.winfo_children():
            w.destroy()

        tk.Label(self.myres_tab, text="Reservations you made", font=FONT_HEADER,
                 bg=COLOR_BG, fg=COLOR_HEADER).pack(anchor="w", padx=8, pady=(10, 4))

        tree_frame = tk.Frame(self.myres_tab, bg=COLOR_BG)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        cols = ("facility", "day", "time", "purpose")
        self.my_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        for c, label, w, anchor in [
            ("facility", "Facility", 150, "w"), ("day", "Day", 110, "center"),
            ("time", "Time Frame", 200, "center"), ("purpose", "Purpose", 380, "w"),
        ]:
            self.my_tree.heading(c, text=label)
            self.my_tree.column(c, width=w, anchor=anchor)
        self.my_tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.my_tree.yview)
        self.my_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="left", fill="y")

        self._my_rows = {}
        for res in db.get_teacher_reservations(self.teacher["teacher_id"]):
            row_id = self.my_tree.insert("", "end", values=(
                res["facility_name"], res["day_of_week"],
                f"{db.to_12h(res['start_time'])} - {db.to_12h(res['end_time'])}",
                res["purpose"] or "-",
            ))
            self._my_rows[row_id] = res

        bar = tk.Frame(self.myres_tab, bg=COLOR_BG)
        bar.pack(fill="x", padx=8, pady=8)
        tk.Button(bar, text="Cancel Selected Reservation", bg="#c62828", fg="white",
                  relief="flat", padx=14, command=self._cancel_selected).pack(side="left")
        tk.Button(bar, text="Refresh", bg="#607d8b", fg="white", relief="flat",
                  padx=14, command=self.refresh_all).pack(side="left", padx=8)

    def _cancel_selected(self):
        sel = self.my_tree.selection()
        if not sel:
            messagebox.showinfo("Select a reservation", "Please select a reservation row first.")
            return
        res = self._my_rows[sel[0]]
        confirm = messagebox.askyesno(
            "Cancel reservation",
            f"Cancel {res['facility_name']} on {res['day_of_week']}, "
            f"{db.to_12h(res['start_time'])} - {db.to_12h(res['end_time'])}?",
        )
        if not confirm:
            return
        try:
            db.cancel_reservation(res["reservation_id"], self.teacher["teacher_id"])
        except ValueError as e:
            messagebox.showerror("Cannot cancel", str(e))
            return
        self.refresh_all()

    # ---- Tab 3: everyone's bookings ---------------------------------------
    def build_all_reservations(self):
        for w in self.all_tab.winfo_children():
            w.destroy()

        tk.Label(self.all_tab, text="All active reservations (all teachers)", font=FONT_HEADER,
                 bg=COLOR_BG, fg=COLOR_HEADER).pack(anchor="w", padx=8, pady=(10, 4))

        tree_frame = tk.Frame(self.all_tab, bg=COLOR_BG)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=4)

        cols = ("teacher", "facility", "day", "time", "purpose")
        tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=14)
        for c, label, w, anchor in [
            ("teacher", "Teacher", 180, "w"), ("facility", "Facility", 140, "w"),
            ("day", "Day", 100, "center"), ("time", "Time Frame", 190, "center"),
            ("purpose", "Purpose", 300, "w"),
        ]:
            tree.heading(c, text=label)
            tree.column(c, width=w, anchor=anchor)
        tree.pack(side="left", fill="both", expand=True)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="left", fill="y")

        order = {d: i for i, d in enumerate(db.DAYS_OF_WEEK)}
        rows = sorted(db.get_all_reservations(), key=lambda r: (order[r["day_of_week"]], r["start_time"]))
        for res in rows:
            tree.insert("", "end", values=(
                res["teacher_name"], res["facility_name"], res["day_of_week"],
                f"{db.to_12h(res['start_time'])} - {db.to_12h(res['end_time'])}",
                res["purpose"] or "-",
            ))