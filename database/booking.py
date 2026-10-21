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
            VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
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


def approve_reservation(reservation_id):
    """Approve a pending request after checking for an active conflict."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM reservations WHERE reservation_id = ? AND status = 'PENDING'",
            (reservation_id,),
        ).fetchone()
        if not row:
            raise ValueError("This request no longer exists or has already been reviewed.")
        reservation = dict(row)

    if reservation.get("reservation_date"):
        request_date = date.fromisoformat(reservation["reservation_date"])
        if request_date < date.today():
            raise ValueError("This request is for a past date and cannot be approved.")

    clash = conflicting_reservation(
        reservation["facility_id"],
        reservation["day_of_week"],
        reservation["start_time"],
        reservation["end_time"],
        reservation_date=reservation.get("reservation_date"),
        include_pending=False,
    )
    if clash:
        date_label = f" on {clash.get('reservation_date')}" if clash.get("reservation_date") else ""
        raise ValueError(
            "Cannot approve this request because it conflicts with an approved reservation"
            f"{date_label}:\n{to_12h(clash['start_time'])} - "
            f"{to_12h(clash['end_time'])} ({clash['teacher_name']})."
        )

    with get_connection() as conn:
        result = conn.execute(
            "UPDATE reservations SET status = 'ACTIVE' WHERE reservation_id = ? AND status = 'PENDING'",
            (reservation_id,),
        )
        if result.rowcount == 0:
            raise ValueError("This request was already reviewed by another administrator.")


def reject_reservation(reservation_id):
    """Reject a pending request."""
    with get_connection() as conn:
        result = conn.execute(
            "UPDATE reservations SET status = 'REJECTED' WHERE reservation_id = ? AND status = 'PENDING'",
            (reservation_id,),
        )
        if result.rowcount == 0:
            raise ValueError("This request no longer exists or has already been reviewed.")


def cancel_reservation(reservation_id, teacher_id=None):
    """Cancel an active reservation or pending request."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT teacher_id, status FROM reservations WHERE reservation_id = ?",
            (reservation_id,),
        ).fetchone()
        if not row:
            raise ValueError("Reservation not found.")
        if row["status"] not in ("ACTIVE", "PENDING"):
            raise ValueError("Only active reservations and pending requests can be cancelled.")
        if teacher_id is not None and row["teacher_id"] != teacher_id:
            raise ValueError("You can only cancel reservations you made yourself.")

        result = conn.execute(
            "UPDATE reservations SET status = 'CANCELLED' WHERE reservation_id = ? AND status IN ('ACTIVE', 'PENDING')",
            (reservation_id,),
        )
        if result.rowcount == 0:
            raise ValueError("Reservation could not be cancelled because its status changed.")
