import tkinter as tk
from tkinter import ttk, messagebox
import database as db
from .constants import *

# BOOKING WINDOW ==================================================================

class TimePicker(tk.Frame):
    """A single scrollable column of times, like the 'choose your age' wheel.
    Unavailable entries are shown grayed out and cannot be selected."""

    def __init__(self, parent, title, values, on_select, height=11):
        super().__init__(parent, bg=COLOR_WHITE)
        self.values = values
        self.on_select = on_select
        self.disabled = set()

        tk.Label(self, text=title, font=FONT_HEADER, bg=COLOR_WHITE,
                 fg=COLOR_HEADER).pack(pady=(0, 6))

        box = tk.Frame(self, bg=COLOR_WHITE, bd=1, relief="solid")
        box.pack()

        self.listbox = tk.Listbox(
            box, font=FONT_PICKER, height=height, width=14, activestyle="none",
            selectbackground=COLOR_SELECTED, selectforeground="white",
            highlightthickness=0, bd=0, justify="center", exportselection=False,
        )
        self.listbox.pack(side="left", fill="y")

        sb = ttk.Scrollbar(box, orient="vertical", command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")

        self.listbox.bind("<<ListboxSelect>>", self._handle_select)
        self.refresh(values)

    def refresh(self, values, disabled=None):
        """Repopulate the wheel. `disabled` is a set of values that should be
        visible but unselectable (already booked / invalid)."""
        self.values = values
        self.disabled = set(disabled or [])
        self.listbox.delete(0, "end")
        for v in values:
            label = db.to_12h(v)
            if v in self.disabled:
                self.listbox.insert("end", f"{label}  \u00d7")
                self.listbox.itemconfig("end", fg=COLOR_TAKEN)
            else:
                self.listbox.insert("end", label)

    def _handle_select(self, event):
        sel = self.listbox.curselection()
        if not sel:
            return
        value = self.values[sel[0]]
        if value in self.disabled:
            self.listbox.selection_clear(0, "end")
            return
        self.on_select(value)

    def set_value(self, value):
        if value in self.values:
            idx = self.values.index(value)
            self.listbox.selection_clear(0, "end")
            self.listbox.selection_set(idx)
            self.listbox.see(idx)

    def clear(self):
        self.listbox.selection_clear(0, "end")

class BookingWindow(tk.Toplevel):

    def __init__(self, app, teacher, facility, day, on_close):
        super().__init__(app)
        self.app = app
        self.teacher = teacher
        self.facility = facility
        self.day = day
        self.on_close = on_close

        self.start_value = None
        self.end_value = None
        self.time_points = db.generate_time_points()

        self.title(f"{facility['name']} \u2014 {day}")
        self.geometry("820x580")
        self.minsize(780, 540)
        self.configure(bg=COLOR_WHITE)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._close)

        tk.Label(self, text=f"{facility['name']}  \u2014  {day}", font=FONT_TITLE,
                 bg=COLOR_WHITE, fg=COLOR_HEADER).pack(pady=(16, 2))
        tk.Label(self,
                 text=f"Open {db.to_12h('%02d:00' % db.OPEN_HOUR)} to {db.to_12h('%02d:00' % db.CLOSE_HOUR)}"
                      f"  \u2022  {db.SLOT_MINUTES}-minute steps",
                 font=FONT_SMALL, bg=COLOR_WHITE, fg="#666").pack(pady=(0, 12))

        body = tk.Frame(self, bg=COLOR_WHITE)
        body.pack(fill="both", expand=True, padx=18)

        # --- Left: two picker wheels ---
        pickers = tk.Frame(body, bg=COLOR_WHITE)
        pickers.pack(side="left", padx=(0, 20), anchor="n")

        wheels = tk.Frame(pickers, bg=COLOR_WHITE)
        wheels.pack()

        self.start_picker = TimePicker(wheels, "Start Time", self.time_points, self._on_start_selected)
        self.start_picker.pack(side="left", padx=8)

        tk.Label(wheels, text="\u2192", font=("Segoe UI", 20), bg=COLOR_WHITE,
                 fg="#999").pack(side="left", padx=4, pady=(40, 0))

        self.end_picker = TimePicker(wheels, "End Time", [], self._on_end_selected)
        self.end_picker.pack(side="left", padx=8)

        tk.Label(pickers, text="Pick a start time first \u2014 the end-time wheel then shows\n"
                                "only the valid options for that start.",
                 font=FONT_SMALL, bg=COLOR_WHITE, fg="#777", justify="center").pack(pady=(10, 0))

        # --- Right: live selection + already-taken list ---
        side = tk.Frame(body, bg="#eef2f6", bd=1, relief="solid", width=330)
        side.pack(side="left", fill="both", expand=True, anchor="n")
        side.pack_propagate(False)

        tk.Label(side, text="Your Selection", font=FONT_HEADER, bg="#eef2f6",
                 fg=COLOR_HEADER).pack(pady=(14, 6))
        self.selection_label = tk.Label(side, text="No time selected yet.", font=FONT_NORMAL,
                                         bg="#eef2f6", fg="#333", wraplength=290, justify="center")
        self.selection_label.pack(pady=(0, 4))
        self.duration_label = tk.Label(side, text="", font=FONT_SMALL, bg="#eef2f6", fg="#666")
        self.duration_label.pack(pady=(0, 12))

        ttk.Separator(side, orient="horizontal").pack(fill="x", padx=14)

        tk.Label(side, text="Already Reserved on this Day", font=FONT_HEADER, bg="#eef2f6",
                 fg=COLOR_HEADER).pack(pady=(12, 6))

        taken_frame = tk.Frame(side, bg="#eef2f6")
        taken_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.taken_list = tk.Listbox(taken_frame, font=FONT_SMALL, bd=1, relief="solid",
                                      highlightthickness=0, activestyle="none")
        self.taken_list.pack(side="left", fill="both", expand=True)
        tsb = ttk.Scrollbar(taken_frame, orient="vertical", command=self.taken_list.yview)
        self.taken_list.configure(yscrollcommand=tsb.set)
        tsb.pack(side="left", fill="y")

        # --- Bottom: purpose + actions ---
        bottom = tk.Frame(self, bg=COLOR_WHITE)
        bottom.pack(fill="x", padx=18, pady=14)

        tk.Label(bottom, text="Purpose (optional):", font=FONT_NORMAL,
                 bg=COLOR_WHITE).pack(side="left")
        self.purpose_entry = tk.Entry(bottom, font=FONT_NORMAL, width=34)
        self.purpose_entry.pack(side="left", padx=8)

        tk.Button(bottom, text="Reserve", bg="#2e7d32", fg="white", relief="flat",
                  font=FONT_HEADER, padx=20, pady=5, command=self._reserve).pack(side="right")
        tk.Button(bottom, text="Clear", bg="#607d8b", fg="white", relief="flat",
                  padx=16, pady=5, command=self._clear_selection).pack(side="right", padx=8)

        self._refresh_taken()

    # ---- picker callbacks -------------------------------------------------
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
        options = []
        for t in self.time_points:
            mins = db.minutes_between(start, t)
            if mins > 0:
                options.append(t)
        return options

    def _disabled_end_times(self, start, options):
        return {t for t in options if not db.is_range_free(
            self.facility["facility_id"], self.day, start, t)}

    def _update_selection_label(self):
        if self.start_value and self.end_value:
            self.selection_label.config(
                text=f"{db.to_12h(self.start_value)}  \u2192  {db.to_12h(self.end_value)}",
                fg=COLOR_HEADER, font=("Segoe UI", 13, "bold"))
            mins = db.minutes_between(self.start_value, self.end_value)
            hours = mins // 60
            rem = mins % 60
            parts = []
            if hours:
                parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
            if rem:
                parts.append(f"{rem} minutes")
            self.duration_label.config(text="Duration: " + " ".join(parts))
        elif self.start_value:
            self.selection_label.config(
                text=f"Start: {db.to_12h(self.start_value)}\nNow choose an end time.",
                fg="#333", font=FONT_NORMAL)
            self.duration_label.config(text="")
        else:
            self.selection_label.config(text="No time selected yet.", fg="#333", font=FONT_NORMAL)
            self.duration_label.config(text="")

    def _clear_selection(self):
        self.start_value = None
        self.end_value = None
        self.start_picker.clear()
        self.end_picker.refresh([])
        self._update_selection_label()

    # ---- side panel --------------------------------------------------------
    def _refresh_taken(self):
        reservations = db.get_reservations(self.facility["facility_id"], self.day)

        self.taken_list.delete(0, "end")
        if not reservations:
            self.taken_list.insert("end", "  Nothing reserved yet \u2014 the whole day is open.")
            self.taken_list.itemconfig("end", fg="#2e7d32")
        else:
            for r in reservations:
                mine = r["teacher_id"] == self.teacher["teacher_id"]
                who = "You" if mine else r["teacher_name"]
                self.taken_list.insert(
                    "end", f"  {db.to_12h(r['start_time'])} - {db.to_12h(r['end_time'])}   \u2014   {who}")
                self.taken_list.itemconfig("end", fg=COLOR_SELECTED if mine else "#b34700")
                if r["purpose"]:
                    self.taken_list.insert("end", f"        {r['purpose']}")
                    self.taken_list.itemconfig("end", fg="#777")

        # Gray out start times already covered by a booking.
        taken_blocks = db.taken_time_points(self.facility["facility_id"], self.day)
        disabled_starts = set()
        slots = db.generate_time_slots()
        for s, e in slots:
            if (s, e) in taken_blocks:
                disabled_starts.add(s)
        # The closing time can never be a start time.
        disabled_starts.add(self.time_points[-1])

        self.start_picker.refresh(self.time_points, disabled_starts)
        if self.start_value and self.start_value not in disabled_starts:
            self.start_picker.set_value(self.start_value)

    # ---- actions ------------------------------------------------------------
    def _reserve(self):
        if not self.start_value or not self.end_value:
            messagebox.showwarning("Incomplete selection",
                                    "Please choose both a start time and an end time.", parent=self)
            return
        try:
            db.create_reservation(
                self.facility["facility_id"], self.teacher["teacher_id"], self.day,
                self.start_value, self.end_value, self.purpose_entry.get().strip(),
            )
        except ValueError as e:
            messagebox.showerror("Cannot reserve", str(e), parent=self)
            return

        messagebox.showinfo(
            "Reserved",
            f"{self.facility['name']} reserved for {self.day},\n"
            f"{db.to_12h(self.start_value)} - {db.to_12h(self.end_value)}.",
            parent=self,
        )
        self.purpose_entry.delete(0, "end")
        self._clear_selection()
        self._refresh_taken()

    def _close(self):
        self.destroy()
        self.on_close()