from .core import get_connection

def authenticate_teacher(teacher_id, password):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM teachers WHERE teacher_id = ? AND password = ?",
        (teacher_id, password),
    ).fetchone()
    conn.close()
    return dict(row) if row else None

def get_teacher(teacher_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM teachers WHERE teacher_id = ?", (teacher_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_teachers():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM teachers ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]