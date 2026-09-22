# College Laboratory Equipment Booking and Return Portal

A web app for managing lab equipment inventory, bookings, and returns.

**Stack:** Flask, HTML/CSS/Bootstrap, JavaScript, SQLite (swappable to MySQL)

## Team

- **Person 1 — Backend Developer, Equipment & Database:** inventory model, CRUD routes, DB schema
- **Person 2 — Backend, Booking & Return System:** booking/return workflow built on the `BookingRecord` table

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

- Person 2 builds booking/return routes on top of `BookingRecord`
- Add login system tied to the `User` model
- Add a dashboard view summarizing bookings, overdue returns, etc.
