from datetime import datetime

from .core import get_connection


def _require_admin(conn, admin_id):
    row = conn.execute(
        "SELECT admin_id FROM administrators WHERE admin_id = ?", (admin_id,)
    ).fetchone()
    if not row:
        raise ValueError("An authenticated administrator account is required for this action.")


def add_teacher(teacher_id, name, password, admin_id):
    """Create an active teacher account and record the action."""
    teacher_id = (teacher_id or "").strip()
    name = (name or "").strip()
    password = password or ""
    if not teacher_id or not name or not password.strip():
        raise ValueError("Enter a staff ID, full name, and password.")
    if len(teacher_id) > 50:
        raise ValueError("Staff ID must be 50 characters or fewer.")
    if len(name) > 150:
        raise ValueError("Name must be 150 characters or fewer.")
    if len(password) < 6:
        raise ValueError("Password must contain at least 6 characters.")
    if len(password) > 200:
        raise ValueError("Password must be 200 characters or fewer.")

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        _require_admin(conn, admin_id)
        exists = conn.execute(
            "SELECT 1 FROM teachers WHERE teacher_id = ?", (teacher_id,)
        ).fetchone()
        if exists:
            raise ValueError(f"Staff ID '{teacher_id}' already exists.")
        conn.execute(
            "INSERT INTO teachers (teacher_id, name, password, is_active) VALUES (?, ?, ?, 1)",
            (teacher_id, name, password),
        )
        conn.execute(
            """INSERT INTO admin_audit_log
               (admin_id, action, target_type, target_id, reason, created_at)
               VALUES (?, 'ADD_TEACHER', 'teacher', ?, ?, ?)""",
            (admin_id, teacher_id, f"Added staff account for {name}", now),
        )


def get_admin_facilities():
    """Return facilities and their reservation counts for the admin panel."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT f.facility_id, f.name,
                      COUNT(r.reservation_id) AS reservation_count
               FROM facilities AS f
               LEFT JOIN reservations AS r ON r.facility_id = f.facility_id
               GROUP BY f.facility_id, f.name
               ORDER BY f.name COLLATE NOCASE"""
        ).fetchall()
    return [dict(row) for row in rows]


def add_facility(name, admin_id):
    """Create a facility and record the action in the admin audit log."""
    name = (name or "").strip()
    if not name:
        raise ValueError("Enter a facility name.")
    if len(name) > 120:
        raise ValueError("Facility name must be 120 characters or fewer.")

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        _require_admin(conn, admin_id)
        exists = conn.execute(
            "SELECT 1 FROM facilities WHERE name = ? COLLATE NOCASE", (name,)
        ).fetchone()
        if exists:
            raise ValueError(f"A facility named '{name}' already exists.")
        cursor = conn.execute(
            "INSERT INTO facilities (name) VALUES (?)", (name,)
        )
        facility_id = cursor.lastrowid
        conn.execute(
            """INSERT INTO admin_audit_log
               (admin_id, action, target_type, target_id, reason, created_at)
               VALUES (?, 'ADD_FACILITY', 'facility', ?, ?, ?)""",
            (admin_id, str(facility_id), f"Added facility: {name}", now),
        )


def get_admin_teachers():
    """Return staff accounts, their active state, and reservation count."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT t.teacher_id, t.name, t.is_active,
                   COUNT(r.reservation_id) AS reservation_count
            FROM teachers AS t
            LEFT JOIN reservations AS r ON r.teacher_id = t.teacher_id
            GROUP BY t.teacher_id, t.name, t.is_active
            ORDER BY t.name COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_admin_reservations():
    """Return reservation history, including pending and terminal statuses."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.*, t.name AS teacher_name, f.name AS facility_name
            FROM reservations AS r
            JOIN teachers AS t ON t.teacher_id = r.teacher_id
            JOIN facilities AS f ON f.facility_id = r.facility_id
            ORDER BY
                COALESCE(r.reservation_date, substr(r.created_at, 1, 10)) DESC,
                r.start_time DESC,
                r.reservation_id DESC
            """
        ).fetchall()
    return [dict(row) for row in rows]


def set_teacher_active(teacher_id, is_active, admin_id):
    """Deactivate or reactivate a teacher without deleting their history."""
    active_value = 1 if is_active else 0
    action = "REACTIVATE_TEACHER" if active_value else "DEACTIVATE_TEACHER"
    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        _require_admin(conn, admin_id)
        teacher = conn.execute(
            "SELECT teacher_id, name, is_active FROM teachers WHERE teacher_id = ?",
            (teacher_id,),
        ).fetchone()
        if not teacher:
            raise ValueError("Staff account was not found.")
        if int(teacher["is_active"]) == active_value:
            state = "active" if active_value else "deactivated"
            raise ValueError(f"This staff account is already {state}.")

        conn.execute(
            "UPDATE teachers SET is_active = ? WHERE teacher_id = ?",
            (active_value, teacher_id),
        )
        conn.execute(
            """INSERT INTO admin_audit_log
               (admin_id, action, target_type, target_id, reason, created_at)
               VALUES (?, ?, 'teacher', ?, ?, ?)""",
            (
                admin_id,
                action,
                teacher_id,
                "Account reactivated by administrator" if active_value
                else "Account deactivated by administrator",
                now,
            ),
        )


def force_cancel_reservation(reservation_id, admin_id, reason):
    """Cancel a pending/active booking and record who cancelled it and why."""
    reason = (reason or "").strip()
    if not reason:
        raise ValueError("Enter a reason for the forced cancellation.")
    if len(reason) > 500:
        raise ValueError("The cancellation reason must be 500 characters or fewer.")

    now = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        _require_admin(conn, admin_id)
        reservation = conn.execute(
            "SELECT reservation_id, status FROM reservations WHERE reservation_id = ?",
            (reservation_id,),
        ).fetchone()
        if not reservation:
            raise ValueError("Reservation was not found.")
        if reservation["status"] not in ("ACTIVE", "PENDING"):
            raise ValueError(
                "Only active reservations or pending requests can be force-cancelled."
            )

        result = conn.execute(
            """UPDATE reservations
               SET status = 'CANCELLED', cancellation_reason = ?,
                   cancelled_by_admin = ?, cancelled_at = ?
               WHERE reservation_id = ? AND status IN ('ACTIVE', 'PENDING')""",
            (reason, admin_id, now, reservation_id),
        )
        if result.rowcount != 1:
            raise ValueError("The reservation status changed. Refresh and try again.")

        conn.execute(
            """INSERT INTO admin_audit_log
               (admin_id, action, target_type, target_id, reason, created_at)
               VALUES (?, 'FORCE_CANCEL_RESERVATION', 'reservation', ?, ?, ?)""",
            (admin_id, str(reservation_id), reason, now),
        )
