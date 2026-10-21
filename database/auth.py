from .core import get_connection


def authenticate_teacher(teacher_id, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM teachers WHERE teacher_id = ? AND password = ?",
            (teacher_id, password),
        ).fetchone()
    return dict(row) if row else None


def get_teacher(teacher_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM teachers WHERE teacher_id = ?", (teacher_id,)
        ).fetchone()
    return dict(row) if row else None


def get_teachers():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    return [dict(row) for row in rows]


def authenticate_admin(admin_id, password):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM administrators WHERE admin_id = ? AND password = ?",
            (admin_id, password),
        ).fetchone()
    return dict(row) if row else None
