import sqlite3

from .config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables and safely add the date field to existing databases."""
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                password TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS facilities (
                facility_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reservations (
                reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                teacher_id TEXT NOT NULL,
                day_of_week TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                purpose TEXT,
                status TEXT NOT NULL DEFAULT 'ACTIVE',
                created_at TEXT NOT NULL,
                reservation_date TEXT,
                FOREIGN KEY (facility_id) REFERENCES facilities (facility_id),
                FOREIGN KEY (teacher_id) REFERENCES teachers (teacher_id)
            );
        """)

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(reservations)").fetchall()
        }
        if "reservation_date" not in columns:
            conn.execute(
                "ALTER TABLE reservations ADD COLUMN reservation_date TEXT"
            )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_reservations_date_facility "
            "ON reservations (reservation_date, facility_id, status)"
        )


def seed_data():
    """Insert the starter teachers and facilities without duplicating rows."""
    teachers = [
        ("T-0001", "Jhervin Cabato", "teacher123"),
        ("T-0002", "Maria Santos", "teacher123"),
        ("T-0003", "Ramon Dela Cruz", "teacher123"),
    ]
    facilities = ["Gym", "AVR", "Covered Court", "Function Hall"]

    with get_connection() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO teachers (teacher_id, name, password) VALUES (?, ?, ?)",
            teachers,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO facilities (name) VALUES (?)",
            [(facility,) for facility in facilities],
        )
