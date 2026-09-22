from datetime import datetime
from .core import get_connection
from .config import SLOT_MINUTES
from .time_utils import minutes_between, to_12h
from .schedule import conflicting_reservation

# Booking

def create_reservation(facility_id, teacher_id, day_of_week, start_time, end_time, purpose=""):
    """Validate and save a reservation. Raises ValueError with a readable
    message if the request breaks a rule or clashes with an existing booking."""
    duration = minutes_between(start_time, end_time)

    if duration <= 0:
        raise ValueError("The end time must be later than the start time.")
    if duration % SLOT_MINUTES != 0:
        raise ValueError(f"Bookings must be in {SLOT_MINUTES}-minute increments.")

    clash = conflicting_reservation(facility_id, day_of_week, start_time, end_time)
    if clash:
        raise ValueError(
            f"That time clashes with an existing booking:\n"
            f"{to_12h(clash['start_time'])} - {to_12h(clash['end_time'])} "
            f"({clash['teacher_name']})"
        )

    conn = get_connection()
    conn.execute(
        """INSERT INTO reservations
           (facility_id, teacher_id, day_of_week, start_time, end_time, purpose, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)""",
        (facility_id, teacher_id, day_of_week, start_time, end_time,
         purpose, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()

def cancel_reservation(reservation_id, teacher_id=None):
    """Cancel a reservation. If teacher_id is given, only that teacher's own
    reservation can be cancelled."""
    conn = get_connection()
    if teacher_id is not None:
        row = conn.execute(
            "SELECT teacher_id FROM reservations WHERE reservation_id = ?", (reservation_id,)
        ).fetchone()
        if not row:
            conn.close()
            raise ValueError("Reservation not found.")
        if row["teacher_id"] != teacher_id:
            conn.close()
            raise ValueError("You can only cancel reservations you made yourself.")
    conn.execute(
        "UPDATE reservations SET status = 'CANCELLED' WHERE reservation_id = ?", (reservation_id,)
    )
    conn.commit()
    conn.close()