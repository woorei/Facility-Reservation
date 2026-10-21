import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reservation_system.db")

OPEN_HOUR = 6
CLOSE_HOUR = 18
SLOT_MINUTES = 30

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]