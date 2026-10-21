# Facility Reservation System

A modular Python Tkinter and SQLite facility booking app.

## Run the application

From this project folder, run:

```bash
python main.py
```

The project uses the Python standard library only. No extra packages are required.

## Project structure

```text
Facility-Reservation-main/
├── main.py                   # Application entry point
├── app.py                    # App window and screen switching
├── settings.json             # Created automatically after changing the theme
├── database/
│   ├── __init__.py            # Public database API
│   ├── core.py                # Connections, tables, and safe schema migration
│   ├── auth.py                # Staff authentication
│   ├── schedule.py            # Reservation queries and conflict checks
│   ├── booking.py             # Create/cancel reservation operations
│   ├── time_utils.py          # Time calculations and formatting
│   └── reservation_system.db  # Existing SQLite database
└── ui/
    ├── constants.py           # Shared fonts and compatibility constants
    ├── theme.py               # Light/dark themes and saved preference
    ├── login.py               # Login screen
    ├── dashboard.py           # Dashboard and reservation tables
    ├── calendar_view.py       # Interactive weekly calendar
    └── booking.py              # Booking window and time picker
```

## Features

- Light and dark themes, with the selected theme saved in `settings.json`.
- Weekly calendar with Previous week, Today, Next week, and a Choose date calendar popup for direct navigation.
- Filter the calendar by facility, or display all facilities.
- Click a blank half-hour slot to submit a reservation request.
- Staff requests begin as Pending and need administrator approval before they become approved reservations.
- Administrators have a separate login and dashboard for approving or rejecting pending requests.
- Pending requests are shown on the calendar and temporarily block conflicting requests.
- Click an existing booking to view details. Staff can cancel their own reservations.
- My Reservations and All Reservations tables show the reservation date or weekly recurrence.
- Reservation creation still checks for time conflicts in the database layer.

## Existing data and dates

The original database saved reservations by weekday, without a specific calendar date. The app preserves those existing records as recurring weekly reservations. The database setup adds a nullable `reservation_date` field without deleting existing records.

New bookings made from the calendar are saved against the selected date. Those bookings appear only on the chosen date. Existing recurring reservations are still included when checking availability for a date, so a date-specific booking cannot overlap an existing recurring reservation for the same facility and weekday.

## Starter accounts

The existing seed data includes staff IDs `T-0001`, `T-0002`, and `T-0003`, each with the original placeholder password `teacher123`. Replace these credentials before real deployment.
## Recent fixes

- Switching themes on the login screen preserves the Staff ID and password in memory. Credentials clear after a successful login.
- Past calendar dates are shown with muted styling and cannot open a new booking window. Existing reservation blocks remain clickable for viewing or cancellation.
- The database rejects date-specific reservations before the current date, even if a booking request bypasses the calendar UI.


## Administrator login

Choose `Administrator` in the account-type selector on the login screen.

- Administrator ID: `A-0001`
- Password: `admin123`

This is a starter account for the school project. Change the password before using the system with real accounts. Existing staff IDs and passwords remain unchanged.

## Approval workflow

1. Staff select a date and time and submit a request.
2. The request appears with `Pending approval` in My Reservations and in the administrator approval queue.
3. An administrator approves or rejects the request.
4. Approved requests become active reservations. Rejected requests remain visible to the staff member as history.
5. Approval checks for conflicts with already approved reservations before confirming a request.
