import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reservation_system.db")

# ---- Configurable business rules ------------------------------------------
OPEN_HOUR = 6              # 6 AM
CLOSE_HOUR = 18            # 6 PM
SLOT_MINUTES = 30          # granularity of the schedule

DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]