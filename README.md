# College Laboratory Equipment Booking and Return Portal

A web app for managing lab equipment inventory, bookings, and returns.

**Stack:** Flask, HTML/CSS/Bootstrap, JavaScript, SQLite (swappable to MySQL)

## Team

## Team

A 4-member team building this as a college project, covering backend (equipment database, booking/return system), frontend, and integration. 

## Setup

```bash
python -m venv venv
source venv/bin/activate      # venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py
```

Visit `http://127.0.0.1:5000` — it redirects to the equipment inventory page.

## What's implemented so far (Equipment & Database side)

- `Equipment`, `User`, `BookingRecord` models (`models.py`)
- Full CRUD for equipment: list, add, edit, delete (`app.py`, `templates/`)
- JSON API endpoints for the booking side to check availability:
  - `GET /api/equipment` — all equipment
  - `GET /api/equipment/<id>/availability` — one item's live availability

## Next steps

- Build booking/return routes on top of the `BookingRecord` table
- Add a login system tied to the `User` model
- Build out the frontend pages and connect them to the backend routes
- Add a dashboard view summarizing bookings and overdue returns
- Test the full flow end-to-end as a team before final submission
