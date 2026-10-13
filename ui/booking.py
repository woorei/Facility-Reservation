import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime

import database as db
from .constants import FONT_TITLE, FONT_HEADER, FONT_NORMAL, FONT_PICKER, FONT_SMALL


class TimePicker(tk.Frame):
    """Scrollable time wheel with unavailable options visibly disabled."""
    def __init__(self, parent, title, values, on_select, colors, height=11):
        self.colors = colors
        super().__init__(parent, bg=colors["panel"])
        self.values = values
        self.on_select = on_select
        self.disabled = set()

        tk.Label(
            self, text=title, font=FONT_HEADER,
            bg=colors["panel"], fg=colors["text"],
        ).pack(pady=(0, 6))
        box = tk.Frame(
            self, bg=colors["panel"], bd=1, relief="solid",
            highlightbackground=colors["border"],
        )
        box.pack()
        self.listbox = tk.Listbox(
            box, font=FONT_PICKER, height=height, width=14,
            activestyle="none", selectbackground=colors["selection"],
            selectforeground="#ffffff", highlightthickness=0, bd=0,
            justify="center", exportselection=False,
            bg=colors["input"], fg=colors["input_text"],
        )
        self.listbox.pack(side="left", fill="y")
        scrollbar = ttk.Scrollbar(box, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")
        self.listbox.bind("<<ListboxSelect>>", self._handle_select)
        self.refresh(values)

    def refresh(self, values, disabled=None):
        self.values = values
        self.disabled = set(disabled or [])
        self.listbox.delete(0, "end")
        for value in values:
            label = db.to_12h(value)
            if value in self.disabled:
                self.listbox.insert("end", f"{label}  ×")
                self.listbox.itemconfig("end", fg=self.colors["taken"])
            else:
                self.listbox.insert("end", label)

    def _handle_select(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        value = self.values[selection[0]]
        if value in self.disabled:
            self.listbox.selection_clear(0, "end")
            return
        self.on_select(value)

    def set_value(self, value):
        if value in self.values and value not in self.disabled:
            index = self.values.index(value)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(index)
            self.listbox.see(index)

    def clear(self):
        self.listbox.selection_clear(0, "end")


class BookingWindow(tk.Toplevel):
    def __init__(
        self, app, teacher, facility, day, on_close,
        reservation_date=None, initial_start=None,
    ):
        super().__init__(app)
        self.app = app
        self.teacher = teacher
        self.facility = facility
        self.day = day
        self.on_close = on_close
        self.reservation_date = reservation_date
        self.initial_start = initial_start
        self.colors = app.colors
        self.start_value = None
        self.end_value = None
        self.time_points = db.generate_time_points()
        c = self.colors

        date_title = (
            datetime.fromisoformat(reservation_date).strftime("%A, %B %d, %Y")
            if reservation_date else day
        )
        self.title(f"{facility['name']} — {date_title}")
        self.geometry("850x600")
        self.minsize(810, 550)
        self.configure(bg=c["bg"])
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        tk.Label(
            self, text=f"{facility['name']}  ·  {date_title}",
            font=FONT_TITLE, bg=c["bg"], fg=c["header"],
        ).pack(pady=(16, 2))
        tk.Label(
            self,
            text=(
                f"Open {db.to_12h(f'{db.OPEN_HOUR:02d}:00')} to "
                f"{db.to_12h(f'{db.CLOSE_HOUR:02d}:00')}  ·  "
                f"{db.SLOT_MINUTES}-minute steps"
            ),
            font=FONT_SMALL, bg=c["bg"], fg=c["muted"],
        ).pack(pady=(0, 12))

        body = tk.Frame(self, bg=c["bg"])
        body.pack(fill="both", expand=True, padx=18)
        self._build_pickers(body)
        self._build_side_panel(body)
        self._build_bottom_bar()
        self._refresh_taken()

        if self.initial_start and self.initial_start in self.time_points[:-1]:
            if self.initial_start not in self.start_picker.disabled:
                self.start_picker.set_value(self.initial_start)
                self._on_start_selected(self.initial_start)
                self.start_picker.set_value(self.initial_start)

    def _build_pickers(self, parent):
        c = self.colors
        pickers = tk.Frame(parent, bg=c["bg"])
        pickers.pack(side="left", padx=(0, 18), anchor="n")
        wheels = tk.Frame(pickers, bg=c["bg"])
        wheels.pack()
        self.start_picker = TimePicker(
            wheels, "Start Time", self.time_points,
            self._on_start_selected, c,
        )
        self.start_picker.pack(side="left", padx=6)
        tk.Label(
            wheels, text="→", font=("Segoe UI", 20),
            bg=c["bg"], fg=c["muted"],
        ).pack(side="left", padx=4, pady=(40, 0))
        self.end_picker = TimePicker(
            wheels, "End Time", [], self._on_end_selected, c,
        )
        self.end_picker.pack(side="left", padx=6)
        tk.Label(
            pickers,
            text="Choose a start time. The end-time wheel will show\n"
                 "only end times that fit the available schedule.",
            font=FONT_SMALL, bg=c["bg"], fg=c["muted"], justify="center",
        ).pack(pady=(10, 0))

    def _build_side_panel(self, parent):
        c = self.colors
        side = tk.Frame(
            parent, bg=c["muted_panel"], bd=1, relief="solid",
            highlightbackground=c["border"], width=335,
        )
        side.pack(side="left", fill="both", expand=True, anchor="n")
        side.pack_propagate(False)
        tk.Label(
            side, text="Your Selection", font=FONT_HEADER,
            bg=c["muted_panel"], fg=c["header"],
        ).pack(pady=(14, 6))
        self.selection_label = tk.Label(
            side, text="No time selected yet.", font=FONT_NORMAL,
            bg=c["muted_panel"], fg=c["text"], wraplength=295, justify="center",
        )
        self.selection_label.pack(pady=(0, 4))
        self.duration_label = tk.Label(
            side, text="", font=FONT_SMALL,
            bg=c["muted_panel"], fg=c["muted"],
        )
        self.duration_label.pack(pady=(0, 12))
        ttk.Separator(side, orient="horizontal").pack(fill="x", padx=14)
        tk.Label(
            side, text="Already Reserved", font=FONT_HEADER,
            bg=c["muted_panel"], fg=c["header"],
        ).pack(pady=(12, 6))
        frame = tk.Frame(side, bg=c["muted_panel"])
        frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))
        self.taken_list = tk.Listbox(
            frame, font=FONT_SMALL, bd=1, relief="solid", highlightthickness=0,
            activestyle="none", bg=c["input"], fg=c["input_text"],
        )
        self.taken_list.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.taken_list.yview)
        self.taken_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="left", fill="y")

    def _build_bottom_bar(self):
        c = self.colors
        bottom = tk.Frame(self, bg=c["bg"])
        bottom.pack(fill="x", padx=18, pady=14)
        tk.Label(
            bottom, text="Purpose (optional):", font=FONT_NORMAL,
            bg=c["bg"], fg=c["text"],
        ).pack(side="left")
        self.purpose_entry = tk.Entry(
            bottom, font=FONT_NORMAL, width=30,
            bg=c["input"], fg=c["input_text"],
            insertbackground=c["input_text"], relief="solid", bd=1,
        )
        self.purpose_entry.pack(side="left", padx=8)
        tk.Button(
            bottom, text="Reserve", bg=c["success"], fg="#ffffff",
            activebackground=c["accent"], activeforeground="#ffffff",
            relief="flat", font=FONT_HEADER, padx=20, pady=6,
            command=self._reserve,
        ).pack(side="right")
        tk.Button(
            bottom, text="Clear", bg=c["panel"], fg=c["text"],
            activebackground=c["muted_panel"], activeforeground=c["text"],
            relief="flat", padx=16, pady=6, command=self._clear_selection,
        ).pack(side="right", padx=8)

    def _on_start_selected(self, value):
        self.start_value = value
        self.end_value = None
        options = self._valid_end_times(value)
        self.end_picker.refresh(options, self._disabled_end_times(value, options))
        self.end_picker.clear()
        self._update_selection_label()

    def _on_end_selected(self, value):
        self.end_value = value
        self._update_selection_label()

    def _valid_end_times(self, start):
        return [time_point for time_point in self.time_points if db.minutes_between(start, time_point) > 0]

    def _disabled_end_times(self, start, options):
        return {
            time_point for time_point in options
            if not db.is_range_free(
                self.facility["facility_id"], self.day, start, time_point,
                reservation_date=self.reservation_date,
            )
        }

    def _update_selection_label(self):
        c = self.colors
        if self.start_value and self.end_value:
            self.selection_label.config(
                text=f"{db.to_12h(self.start_value)}  →  {db.to_12h(self.end_value)}",
                fg=c["header"], font=("Segoe UI", 13, "bold"),
            )
            minutes = db.minutes_between(self.start_value, self.end_value)
            hours, remainder = divmod(minutes, 60)
            parts = []
            if hours:
                parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
            if remainder:
                parts.append(f"{remainder} minutes")
            self.duration_label.config(text="Duration: " + " ".join(parts))
        elif self.start_value:
            self.selection_label.config(
                text=f"Start: {db.to_12h(self.start_value)}\nNow choose an end time.",
                fg=c["text"], font=FONT_NORMAL,
            )
            self.duration_label.config(text="")
        else:
            self.selection_label.config(
                text="No time selected yet.", fg=c["text"], font=FONT_NORMAL,
            )
            self.duration_label.config(text="")

    def _clear_selection(self):
        self.start_value = None
        self.end_value = None
        self.start_picker.clear()
        self.end_picker.refresh([])
        self._update_selection_label()

    def _refresh_taken(self):
        reservations = db.get_reservations(
            self.facility["facility_id"], self.day, self.reservation_date,
        )
        c = self.colors
        self.taken_list.delete(0, "end")
        if not reservations:
            self.taken_list.insert("end", "  Nothing reserved yet. This day is open.")
            self.taken_list.itemconfig("end", fg=c["success"])
        else:
            for row in reservations:
                mine = row["teacher_id"] == self.teacher["teacher_id"]
                who = "You" if mine else row["teacher_name"]
                self.taken_list.insert(
                    "end", f"  {db.to_12h(row['start_time'])} - {db.to_12h(row['end_time'])}  ·  {who}"
                )
                self.taken_list.itemconfig("end", fg=c["selection"] if mine else c["warning"])
                if row["purpose"]:
                    self.taken_list.insert("end", f"      {row['purpose']}")
                    self.taken_list.itemconfig("end", fg=c["muted"])

        taken_blocks = db.taken_time_points(
            self.facility["facility_id"], self.day, self.reservation_date,
        )
        disabled_starts = {start for start, _end in taken_blocks}
        disabled_starts.add(self.time_points[-1])
        self.start_picker.refresh(self.time_points, disabled_starts)
        if self.start_value and self.start_value not in disabled_starts:
            self.start_picker.set_value(self.start_value)

    def _reserve(self):
        if not self.start_value or not self.end_value:
            messagebox.showwarning(
                "Incomplete selection", "Please choose both a start time and an end time.", parent=self,
            )
            return
        try:
            db.create_reservation(
                self.facility["facility_id"], self.teacher["teacher_id"], self.day,
                self.start_value, self.end_value, self.purpose_entry.get().strip(),
                reservation_date=self.reservation_date,
            )
        except ValueError as error:
            messagebox.showerror("Cannot reserve", str(error), parent=self)
            return

        display_date = (
            datetime.fromisoformat(self.reservation_date).strftime("%A, %B %d, %Y")
            if self.reservation_date else self.day
        )
        messagebox.showinfo(
            "Reserved",
            f"{self.facility['name']} reserved for {display_date},\n"
            f"{db.to_12h(self.start_value)} - {db.to_12h(self.end_value)}.",
            parent=self,
        )
        self.purpose_entry.delete(0, "end")
        self._clear_selection()
        self._refresh_taken()
        self.on_close()

    def _close(self):
        self.destroy()
        self.on_close()
