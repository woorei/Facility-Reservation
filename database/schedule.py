from .core import get_connection
from .time_utils import _overlaps, generate_time_slots


def get_facilities():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM facilities ORDER BY facility_id"
        ).fetchall()
    return [dict(row) for row in rows]


def get_reservations(facility_id, day_of_week, reservation_date=None):
    """Get active bookings for a weekday.

    When a date is supplied, include old recurring weekly bookings and bookings
    assigned to that exact date. Without a date, preserve the original API and
    return every booking associated with that weekday.
    """
    query = """
        SELECT r.*, t.name AS teacher_name, f.name AS facility_name
        FROM reservations r
        JOIN teachers t ON t.teacher_id = r.teacher_id
        JOIN facilities f ON f.facility_id = r.facility_id
        WHERE r.facility_id = ?
          AND r.day_of_week = ?
          AND r.status = 'ACTIVE'
    """
    params = [facility_id, day_of_week]
    if reservation_date is not None:
        query += " AND (r.reservation_date IS NULL OR r.reservation_date = ?)"
        params.append(str(reservation_date))
    query += " ORDER BY r.start_time ASC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def get_teacher_reservations(teacher_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.*, f.name AS facility_name, t.name AS teacher_name
            FROM reservations r
            JOIN facilities f ON f.facility_id = r.facility_id
            JOIN teachers t ON t.teacher_id = r.teacher_id
            WHERE r.teacher_id = ? AND r.status = 'ACTIVE'
            ORDER BY COALESCE(r.reservation_date, r.created_at) DESC,
                     r.start_time DESC
            """,
            (teacher_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_all_reservations():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.*, f.name AS facility_name, t.name AS teacher_name
            FROM reservations r
            JOIN facilities f ON f.facility_id = r.facility_id
            JOIN teachers t ON t.teacher_id = r.teacher_id
            WHERE r.status = 'ACTIVE'
            ORDER BY r.day_of_week, r.reservation_date, r.start_time
            """
        ).fetchall()
    return [dict(row) for row in rows]


def taken_time_points(facility_id, day_of_week, reservation_date=None):
    reservations = get_reservations(facility_id, day_of_week, reservation_date)
    taken = set()
    for start, end in generate_time_slots():
        if any(
            _overlaps(start, end, row["start_time"], row["end_time"])
            for row in reservations
        ):
            taken.add((start, end))
    return taken


def is_range_free(
    facility_id,
    day_of_week,
    start_time,
    end_time,
    ignore_reservation_id=None,
    reservation_date=None,
):
    for row in get_reservations(facility_id, day_of_week, reservation_date):
        if (
            ignore_reservation_id is not None
            and row["reservation_id"] == ignore_reservation_id
        ):
            continue
        if _overlaps(start_time, end_time, row["start_time"], row["end_time"]):
            return False
    return True


def conflicting_reservation(
    facility_id,
    day_of_week,
    start_time,
    end_time,
    reservation_date=None,
):
    for row in get_reservations(facility_id, day_of_week, reservation_date):
        if _overlaps(start_time, end_time, row["start_time"], row["end_time"]):
            return row
    return None
