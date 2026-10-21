from datetime import datetime, timedelta
from .config import OPEN_HOUR, CLOSE_HOUR, SLOT_MINUTES

# Time helpers ==================================================================

def generate_time_points():
    points = []
    t = datetime(2000, 1, 1, OPEN_HOUR, 0)
    end_of_day = datetime(2000, 1, 1, CLOSE_HOUR, 0)
    while t <= end_of_day:
        points.append(t.strftime("%H:%M"))
        t += timedelta(minutes=SLOT_MINUTES)
    return points

def generate_time_slots():
    points = generate_time_points()
    return list(zip(points[:-1], points[1:]))

def to_12h(hhmm):
    dt = datetime.strptime(hhmm, "%H:%M")
    return dt.strftime("%I:%M %p").lstrip("0")

def _time_to_dt(hhmm):
    h, m = map(int, hhmm.split(":"))
    return datetime(2000, 1, 1, h, m)

def minutes_between(start, end):
    return int((_time_to_dt(end) - _time_to_dt(start)).total_seconds() / 60)

def _overlaps(start_a, end_a, start_b, end_b):
    return _time_to_dt(start_a) < _time_to_dt(end_b) and _time_to_dt(end_a) > _time_to_dt(start_b)