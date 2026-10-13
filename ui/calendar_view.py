from __future__ import annotations

from datetime import date, datetime, timedelta
import tkinter as tk
from tkinter import ttk, messagebox

import database as db
from .constants import FONT_HEADER, FONT_NORMAL, FONT_SMALL


class CalendarView(tk.Frame):
    TIME_WIDTH = 76
    DAY_WIDTH = 132
    HEADER_HEIGHT = 44
    SLOT_HEIGHT = 25
    SLOT_MINUTES = 30

    def __init__(self, parent, app, teacher, facilities, on_change):
        self.app = app
        self.teacher = teacher
        self.facilities = facilities
        self.on_change = on_change
        self.colors = app.colors
        self.week_start = date.today() - timedelta(days=date.today().weekday())
        self.facility_names = ["All facilities"] + [f["name"] for f in facilities]
        self.facility_by_name = {f["name"]: f for f in facilities}
        self.selected_facility = "All facilities"
        super().__init__(parent, bg=self.colors["bg"])
        self._build_toolbar()
        self._build_canvas()
        self.refresh()

    def _build_toolbar(self):
        c = self.colors
        toolbar = tk.Frame(self, bg=c["bg"])
        toolbar.pack(fill="x", padx=8, pady=(8, 10))

        tk.Button(
            toolbar, text="‹ Previous week", command=self.previous_week,
            bg=c["panel"], fg=c["text"], activebackground=c["muted_panel"],
            activeforeground=c["text"], relief="flat", padx=10, pady=6,
        ).pack(side="left")
        tk.Button(
            toolbar, text="Today", command=self.go_today,
            bg=c["panel"], fg=c["text"], activebackground=c["muted_panel"],
            activeforeground=c["text"], relief="flat", padx=12, pady=6,
        ).pack(side="left", padx=(6, 0))
        tk.Button(
            toolbar, text="Next week ›", command=self.next_week,
            bg=c["panel"], fg=c["text"], activebackground=c["muted_panel"],
            activeforeground=c["text"], relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=(6, 12))

        self.range_label = tk.Label(
            toolbar, text="", font=FONT_HEADER, bg=c["bg"], fg=c["text"]
        )
        self.range_label.pack(side="left", padx=(0, 12))

        tk.Label(
            toolbar, text="Facility", font=FONT_NORMAL,
            bg=c["bg"], fg=c["muted"],
        ).pack(side="right", padx=(8, 5))
        self.facility_var = tk.StringVar(value=self.selected_facility)
        self.facility_combo = ttk.Combobox(
            toolbar, textvariable=self.facility_var,
            values=self.facility_names, state="readonly", width=19,
        )
        self.facility_combo.pack(side="right")
        self.facility_combo.bind("<<ComboboxSelected>>", self._on_facility_change)

    def _build_canvas(self):
        c = self.colors
        holder = tk.Frame(self, bg=c["bg"])
        holder.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.canvas = tk.Canvas(
            holder,
            bg=c["panel"],
            highlightthickness=1,
            highlightbackground=c["border"],
            width=self.TIME_WIDTH + self.DAY_WIDTH * 7,
            height=620,
        )
        vertical = ttk.Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        horizontal = ttk.Scrollbar(holder, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(
            yscrollcommand=vertical.set,
            xscrollcommand=horizontal.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

    def _on_facility_change(self, _event=None):
        self.selected_facility = self.facility_var.get()
        self.refresh()

    def previous_week(self):
        self.week_start -= timedelta(days=7)
        self.refresh()

    def next_week(self):
        self.week_start += timedelta(days=7)
        self.refresh()

    def go_today(self):
        today = date.today()
        self.week_start = today - timedelta(days=today.weekday())
        self.refresh()

    def refresh(self):
        self.colors = self.app.colors
        c = self.colors
        self.range_label.config(
            text=(
                f"{self.week_start.strftime('%b %d')} – "
                f"{(self.week_start + timedelta(days=6)).strftime('%b %d, %Y')}"
            ),
            bg=c["bg"], fg=c["text"],
        )
        self.canvas.configure(bg=c["panel"], highlightbackground=c["border"])
        self._draw_calendar()

    def _draw_calendar(self):
        c = self.colors
        canvas = self.canvas
        canvas.delete("all")
        self.event_records = {}
        width = self.TIME_WIDTH + self.DAY_WIDTH * 7
        height = self.HEADER_HEIGHT + 24 * self.SLOT_HEIGHT + 25
        canvas.configure(scrollregion=(0, 0, width, height))

        # Header cells
        canvas.create_rectangle(
            0, 0, self.TIME_WIDTH, self.HEADER_HEIGHT,
            fill=c["header"], outline=c["border"],
        )
        canvas.create_text(
            self.TIME_WIDTH / 2, self.HEADER_HEIGHT / 2,
            text="Time", fill="#ffffff", font=FONT_HEADER,
        )
        visible_dates = [self.week_start + timedelta(days=i) for i in range(7)]
        for index, day_date in enumerate(visible_dates):
            x1 = self.TIME_WIDTH + index * self.DAY_WIDTH
            x2 = x1 + self.DAY_WIDTH
            is_past_day = day_date < date.today()
            header_fill = c["muted_panel"] if is_past_day else c["header"]
            header_text = c["muted"] if is_past_day else "#ffffff"
            canvas.create_rectangle(
                x1, 0, x2, self.HEADER_HEIGHT,
                fill=header_fill, outline=c["border"],
            )
            day_label = f"{day_date.strftime('%a')}\n{day_date.strftime('%b %d')}"
            canvas.create_text(
                (x1 + x2) / 2, self.HEADER_HEIGHT / 2,
                text=day_label, fill=header_text, font=FONT_HEADER,
                justify="center",
            )

        grid_top = self.HEADER_HEIGHT
        open_minutes = db.OPEN_HOUR * 60
        close_minutes = db.CLOSE_HOUR * 60
        for slot_index in range(25):
            y = grid_top + slot_index * self.SLOT_HEIGHT
            minute = open_minutes + slot_index * self.SLOT_MINUTES
            hour, mins = divmod(minute, 60)
            if hour <= db.CLOSE_HOUR:
                time_text = datetime.strptime(f"{hour:02d}:{mins:02d}", "%H:%M").strftime("%I:%M %p").lstrip("0")
                canvas.create_text(
                    self.TIME_WIDTH - 8, y,
                    text=time_text, anchor="ne", fill=c["muted"], font=FONT_SMALL,
                )

        # Paint day backgrounds before the grid lines so the grid remains visible.
        for day_index, calendar_date in enumerate(visible_dates):
            x1 = self.TIME_WIDTH + day_index * self.DAY_WIDTH
            x2 = x1 + self.DAY_WIDTH
            if calendar_date < date.today():
                fill = c["bg"]
            elif calendar_date == date.today():
                fill = c["muted_panel"]
            else:
                fill = c["panel"]
            canvas.create_rectangle(
                x1, grid_top, x2, height - 25,
                fill=fill, outline="",
            )

        # Draw lines above the backgrounds.
        for slot_index in range(25):
            y = grid_top + slot_index * self.SLOT_HEIGHT
            minute = db.OPEN_HOUR * 60 + slot_index * self.SLOT_MINUTES
            if minute > db.CLOSE_HOUR * 60:
                continue
            is_hour = (minute % 60) == 0
            canvas.create_line(
                self.TIME_WIDTH, y, width, y,
                fill=c["grid"] if is_hour else c["grid_minor"], width=1,
            )
        for index in range(8):
            x = self.TIME_WIDTH + index * self.DAY_WIDTH
            canvas.create_line(x, grid_top, x, height - 25, fill=c["grid"])

        # Date-aware event data. Legacy rows with no exact date remain weekly.
        all_rows = db.get_all_reservations()
        for day_index, calendar_date in enumerate(visible_dates):
            day_name = calendar_date.strftime("%A")
            day_rows = [
                row for row in all_rows
                if row["day_of_week"] == day_name
                and (row.get("reservation_date") is None or row.get("reservation_date") == calendar_date.isoformat())
                and (self.selected_facility == "All facilities" or row["facility_name"] == self.selected_facility)
            ]
            self._draw_day_events(day_index, calendar_date, day_rows, c)

        canvas.tag_raise("reservation")

    def _draw_day_events(self, day_index, calendar_date, rows, colors):
        canvas = self.canvas
        sorted_rows = sorted(rows, key=lambda row: (row["start_time"], row["end_time"]))
        lane_ends = []
        lane_by_id = {}

        for row in sorted_rows:
            start_minutes = self._minutes_from_open(row["start_time"])
            end_minutes = self._minutes_from_open(row["end_time"])
            lane = next((i for i, lane_end in enumerate(lane_ends) if lane_end <= start_minutes), None)
            if lane is None:
                lane = len(lane_ends)
                lane_ends.append(end_minutes)
            else:
                lane_ends[lane] = end_minutes
            lane_by_id[row["reservation_id"]] = lane

        lane_count = max(1, len(lane_ends))
        x_day = self.TIME_WIDTH + day_index * self.DAY_WIDTH
        lane_width = self.DAY_WIDTH / lane_count

        for row in sorted_rows:
            start_minutes = self._minutes_from_open(row["start_time"])
            end_minutes = self._minutes_from_open(row["end_time"])
            y1 = self.HEADER_HEIGHT + (start_minutes / self.SLOT_MINUTES) * self.SLOT_HEIGHT + 2
            y2 = self.HEADER_HEIGHT + (end_minutes / self.SLOT_MINUTES) * self.SLOT_HEIGHT - 2
            if y2 - y1 < 16:
                y2 = y1 + 16
            lane = lane_by_id[row["reservation_id"]]
            x1 = x_day + lane * lane_width + 3
            x2 = x_day + (lane + 1) * lane_width - 3
            palette = colors["events"]
            event_color = palette[(int(row["facility_id"]) - 1) % len(palette)]
            tags = ("reservation", f"reservation-id-{row['reservation_id']}")
            self.event_records[row["reservation_id"]] = row
            canvas.create_rectangle(
                x1, y1, x2, y2, fill=event_color,
                outline=colors["border"], width=1, tags=tags,
            )
            label = f"{row['facility_name']} · {self._short_time(row['start_time'])}"
            if lane_width >= 80 and y2 - y1 >= 38:
                label += f"–{self._short_time(row['end_time'])}"
                label += f"\n{row['teacher_name']}"
            canvas.create_text(
                x1 + 4, (y1 + y2) / 2, anchor="w",
                text=label, fill=colors["event_text"],
                font=("Segoe UI", 8, "bold"), width=max(22, x2 - x1 - 7),
                justify="left", tags=tags,
            )

    @staticmethod
    def _minutes_from_open(hhmm):
        hour, minute = map(int, hhmm.split(":"))
        return hour * 60 + minute - db.OPEN_HOUR * 60

    @staticmethod
    def _short_time(hhmm):
        return datetime.strptime(hhmm, "%H:%M").strftime("%I:%M").lstrip("0")

    def _on_canvas_motion(self, event):
        current = self.canvas.find_withtag("current")
        tags = self.canvas.gettags(current[0]) if current else ()
        self.canvas.configure(cursor="hand2" if any(tag.startswith("reservation-id-") for tag in tags) else "")

    def _on_canvas_click(self, event):
        current = self.canvas.find_withtag("current")
        tags = self.canvas.gettags(current[0]) if current else ()
        reservation_tag = next((tag for tag in tags if tag.startswith("reservation-id-")), None)
        if reservation_tag:
            reservation_id = int(reservation_tag.rsplit("-", 1)[1])
            row = self.event_records.get(reservation_id)
            if row:
                self._show_reservation(row)
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if x < self.TIME_WIDTH or y < self.HEADER_HEIGHT:
            return
        day_index = int((x - self.TIME_WIDTH) // self.DAY_WIDTH)
        slot_index = int((y - self.HEADER_HEIGHT) // self.SLOT_HEIGHT)
        if not 0 <= day_index < 7 or not 0 <= slot_index < 24:
            return

        calendar_date = self.week_start + timedelta(days=day_index)
        if calendar_date < date.today():
            messagebox.showinfo(
                "Past date unavailable",
                "Reservations are only allowed for today or a future date.",
                parent=self,
            )
            return

        start_minutes = db.OPEN_HOUR * 60 + slot_index * self.SLOT_MINUTES
        start_time = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        end_minutes = start_minutes + self.SLOT_MINUTES
        end_time = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

        if self.selected_facility == "All facilities":
            self._choose_facility_for_booking(calendar_date, start_time, end_time)
        else:
            facility = self.facility_by_name.get(self.selected_facility)
            if facility:
                self._open_booking(facility, calendar_date, start_time, end_time)

    def _choose_facility_for_booking(self, calendar_date, start_time, end_time):
        c = self.colors
        dialog = tk.Toplevel(self)
        dialog.title("Choose facility")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(bg=c["bg"])
        dialog.resizable(False, False)
        tk.Label(
            dialog,
            text=f"Choose a facility for {calendar_date:%A, %B %d}\n{start_time}–{end_time}",
            bg=c["bg"], fg=c["text"], font=FONT_NORMAL, justify="center",
        ).pack(padx=20, pady=(18, 10))
        choice = tk.StringVar(value=self.facilities[0]["name"] if self.facilities else "")
        combo = ttk.Combobox(
            dialog, values=[f["name"] for f in self.facilities],
            textvariable=choice, state="readonly", width=24,
        )
        combo.pack(padx=20, pady=4)
        buttons = tk.Frame(dialog, bg=c["bg"])
        buttons.pack(fill="x", padx=20, pady=16)

        def confirm():
            facility = self.facility_by_name.get(choice.get())
            dialog.destroy()
            if facility:
                self._open_booking(facility, calendar_date, start_time, end_time)

        tk.Button(
            buttons, text="Cancel", command=dialog.destroy,
            bg=c["panel"], fg=c["text"], relief="flat", padx=12, pady=6,
        ).pack(side="right")
        tk.Button(
            buttons, text="Continue", command=confirm,
            bg=c["accent"], fg="#ffffff", relief="flat", padx=12, pady=6,
        ).pack(side="right", padx=(0, 8))
        dialog.grab_set()
        dialog.update_idletasks()
        dialog.geometry(f"+{self.winfo_rootx() + 220}+{self.winfo_rooty() + 180}")

    def _open_booking(self, facility, calendar_date, start_time, end_time):
        if calendar_date < date.today():
            messagebox.showinfo(
                "Past date unavailable",
                "Reservations are only allowed for today or a future date.",
                parent=self,
            )
            return

        day_name = calendar_date.strftime("%A")
        if not db.is_range_free(
            facility["facility_id"], day_name, start_time, end_time,
            reservation_date=calendar_date.isoformat(),
        ):
            messagebox.showinfo(
                "Time already reserved",
                f"{facility['name']} is unavailable at {start_time} on {calendar_date:%B %d, %Y}.",
                parent=self,
            )
            return
        from .booking import BookingWindow
        BookingWindow(
            self.winfo_toplevel(), self.teacher, facility, day_name,
            on_close=self.on_change,
            reservation_date=calendar_date.isoformat(),
            initial_start=start_time,
        )

    def _show_reservation(self, row):
        c = self.colors
        reservation_date = row.get("reservation_date")
        if reservation_date:
            date_text = datetime.fromisoformat(reservation_date).strftime("%A, %B %d, %Y")
            recurrence = "This booking is for one specific date."
        else:
            date_text = f"Every {row['day_of_week']}"
            recurrence = "This is an existing weekly recurring booking."

        time_text = f"{db.to_12h(row['start_time'])} – {db.to_12h(row['end_time'])}"
        who_text = row.get("teacher_name", "Unknown staff")
        purpose = row.get("purpose") or "No purpose provided"
        is_owner = row["teacher_id"] == self.teacher["teacher_id"]
        prompt = (
            f"Facility: {row['facility_name']}\n"
            f"Date: {date_text}\n"
            f"Time: {time_text}\n"
            f"Reserved by: {who_text}\n"
            f"Purpose: {purpose}\n\n{recurrence}"
        )

        if not is_owner:
            messagebox.showinfo("Reservation details", prompt, parent=self)
            return

        dialog = tk.Toplevel(self)
        dialog.title("Reservation details")
        dialog.transient(self.winfo_toplevel())
        dialog.configure(bg=c["panel"])
        dialog.resizable(False, False)
        tk.Label(
            dialog, text="Reservation details", font=FONT_HEADER,
            bg=c["panel"], fg=c["text"],
        ).pack(anchor="w", padx=20, pady=(18, 8))
        tk.Label(
            dialog, text=prompt, font=FONT_NORMAL,
            bg=c["panel"], fg=c["text"], justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))
        buttons = tk.Frame(dialog, bg=c["panel"])
        buttons.pack(fill="x", padx=20, pady=(0, 18))

        def cancel_reservation():
            if not messagebox.askyesno(
                "Cancel reservation", "Cancel this reservation?", parent=dialog
            ):
                return
            try:
                db.cancel_reservation(row["reservation_id"], self.teacher["teacher_id"])
            except ValueError as error:
                messagebox.showerror("Cannot cancel", str(error), parent=dialog)
                return
            dialog.destroy()
            self.on_change()

        tk.Button(
            buttons, text="Close", command=dialog.destroy,
            bg=c["muted_panel"], fg=c["text"], relief="flat", padx=12, pady=6,
        ).pack(side="right")
        tk.Button(
            buttons, text="Cancel reservation", command=cancel_reservation,
            bg=c["danger"], fg="#ffffff", relief="flat", padx=12, pady=6,
        ).pack(side="right", padx=(0, 8))
        dialog.grab_set()
        dialog.update_idletasks()
        dialog.geometry(f"+{self.winfo_rootx() + 180}+{self.winfo_rooty() + 120}")
