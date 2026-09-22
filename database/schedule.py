from .core import get_connection
from .time_utils import _overlaps, generate_time_slots

# Facilities & schedule

def get_facilities():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM facilities ORDER BY facility_id").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_reservations(facility_id, day_of_week):
    """All active reservations for one facility on one day, earliest first,
    each joined with the booking teacher's name."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.*, t.name AS teacher_name
           FROM reservations r
           JOIN teachers t ON t.teacher_id = r.teacher_id
           WHERE r.facility_id = ? AND r.day_of_week = ? AND r.status = 'ACTIVE'
           ORDER BY r.start_time ASC""",
        (facility_id, day_of_week),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_teacher_reservations(teacher_id):
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.*, f.name AS facility_name, t.name AS teacher_name
           FROM reservations r
           JOIN facilities f ON f.facility_id = r.facility_id
           JOIN teachers t   ON t.teacher_id  = r.teacher_id
           WHERE r.teacher_id = ? AND r.status = 'ACTIVE'
           ORDER BY r.created_at DESC""",
        (teacher_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_all_reservations():
    conn = get_connection()
    rows = conn.execute(
        """SELECT r.*, f.name AS facility_name, t.name AS teacher_name
           FROM reservations r
           JOIN facilities f ON f.facility_id = r.facility_id
           JOIN teachers t   ON t.teacher_id  = r.teacher_id
           WHERE r.status = 'ACTIVE'
           ORDER BY r.day_of_week, r.start_time""",
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def taken_time_points(facility_id, day_of_week):
    """Set of individual 30-minute blocks already covered by a reservation,
    as (start, end) tuples. Used to gray out unavailable picker entries."""
    reservations = get_reservations(facility_id, day_of_week)
    taken = set()
    for s, e in generate_time_slots():
        if any(_overlaps(s, e, r["start_time"], r["end_time"]) for r in reservations):
            taken.add((s, e))
    return taken

def is_range_free(facility_id, day_of_week, start_time, end_time, ignore_reservation_id=None):
    """True if no existing active reservation overlaps the proposed range."""
    for r in get_reservations(facility_id, day_of_week):
        if ignore_reservation_id is not None and r["reservation_id"] == ignore_reservation_id:
            continue
        if _overlaps(start_time, end_time, r["start_time"], r["end_time"]):
            return False
    return True

def conflicting_reservation(facility_id, day_of_week, start_time, end_time):
    """Return the first reservation that clashes with the given range, or None."""
    for r in get_reservations(facility_id, day_of_week):
        if _overlaps(start_time, end_time, r["start_time"], r["end_time"]):
            return r
    return None