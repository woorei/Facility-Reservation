from datetime import date, datetime

from .core import get_connection
from .config import SLOT_MINUTES
from .time_utils import minutes_between, to_12h
from .schedule import conflicting_reservation


def create_reservation(
    facility_id,
    teacher_id,
    day_of_week,
    start_time,
    end_time,
    purpose="",
    reservation_date=None,
):
    duration = minutes_between(start_time, end_time)
    if duration <= 0:
        raise ValueError("The end time must be later than the start time.")
    if duration % SLOT_MINUTES != 0:
        raise ValueError(f"Bookings must be in {SLOT_MINUTES}-minute increments.")

    normalized_date = None
    if reservation_date not in (None, ""):
        try:
            normalized_date = date.fromisoformat(str(reservation_date)).isoformat()
        except ValueError as error:
            raise ValueError("Please choose a valid reservation date.") from error
        if date.fromisoformat(normalized_date) < date.today():
            raise ValueError("Reservations are only allowed for today or a future date.")
        if date.fromisoformat(normalized_date).strftime("%A") != day_of_week:
            raise ValueError("The selected date does not match the chosen day.")

    clash = conflicting_reservation(
        facility_id,
        day_of_week,
        start_time,
        end_time,
        reservation_date=normalized_date,
    )
    if clash:
        existing_date = clash.get("reservation_date")
        date_label = f" on {existing_date}" if existing_date else ""
        raise ValueError(
            "That time clashes with an existing booking"
            f"{date_label}:\n"
            f"{to_12h(clash['start_time'])} - {to_12h(clash['end_time'])} "
            f"({clash['teacher_name']})"
        )

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO reservations
            (
                facility_id, teacher_id, day_of_week, start_time, end_time,
                purpose, status, created_at, reservation_date
            )
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?)
            """,
            (
                facility_id,
                teacher_id,
                day_of_week,
                start_time,
                end_time,
                purpose,
                datetime.now().isoformat(timespec="seconds"),
                normalized_date,
            ),
        )


def cancel_reservation(reservation_id, teacher_id=None):
    """Cancel a booking, optionally requiring the current teacher to own it."""
    with get_connection() as conn:
        if teacher_id is not None:
            row = conn.execute(
                "SELECT teacher_id FROM reservations WHERE reservation_id = ?",
                (reservation_id,),
            ).fetchone()
            if not row:
                raise ValueError("Reservation not found.")
            if row["teacher_id"] != teacher_id:
                raise ValueError("You can only cancel reservations you made yourself.")

        result = conn.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE reservation_id = ?",
            (reservation_id,),
        )
        if result.rowcount == 0:
            raise ValueError("Reservation not found.")
