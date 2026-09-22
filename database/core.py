import sqlite3
from .config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            teacher_id  TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            password    TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS facilities (
            facility_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            reservation_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            facility_id     INTEGER NOT NULL,
            teacher_id      TEXT NOT NULL,
            day_of_week     TEXT NOT NULL,
            start_time      TEXT NOT NULL,   -- 'HH:MM' 24-hour
            end_time        TEXT NOT NULL,   -- 'HH:MM' 24-hour
            purpose         TEXT,
            status          TEXT NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE | CANCELLED
            created_at      TEXT NOT NULL,
            FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
            FOREIGN KEY (teacher_id)  REFERENCES teachers (teacher_id)
        )
    """)

    conn.commit()
    conn.close()

def seed_data():
    """Populate the database with starting teachers and facilities.
    Safe to call repeatedly (uses INSERT OR IGNORE)."""
    conn = get_connection()
    cur = conn.cursor()

    # NOTE: the spec did not provide passwords, so placeholders are used.
    # Change them in the DB before real use.
    teachers = [
        ("T-0001", "Jhervin Cabato", "teacher123"),
        ("T-0002", "Maria Santos", "teacher123"),
        ("T-0003", "Ramon Dela Cruz", "teacher123"),
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO teachers (teacher_id, name, password) VALUES (?, ?, ?)",
        teachers,
    )

    facilities = ["Gym", "AVR", "Covered Court", "Function Hall"]
    cur.executemany(
        "INSERT OR IGNORE INTO facilities (name) VALUES (?)",
        [(f,) for f in facilities],
    )

    conn.commit()
    conn.close()