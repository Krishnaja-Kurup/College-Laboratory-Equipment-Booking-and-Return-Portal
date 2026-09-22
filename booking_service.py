"""Booking & Return logic (Person 2), built on the team's models.py.

Equipment.available_quantity is "how many are free right now".
  booking -> goes DOWN, cancel -> goes back UP, return -> goes back UP
BookingRecord.status: Booked -> Issued -> Returned
                      Booked -> Cancelled
                      Issued -> Overdue (automatic, once past due_date)
Late days and fines are calculated from due_date / returned_date.
Stock is reduced with ONE conditional UPDATE, so two people can never
both take the last unit.
"""
from datetime import date, datetime, time, timezone

from flask import current_app

from models import BookingRecord, Equipment, User, db

BOOKED = "Booked"
ISSUED = "Issued"
RETURNED = "Returned"
OVERDUE = "Overdue"
CANCELLED = "Cancelled"
ALL_STATUSES = (BOOKED, ISSUED, RETURNED, OVERDUE, CANCELLED)
_STATUS_LOOKUP = {s.lower(): s for s in ALL_STATUSES}

EQ_AVAILABLE = "Available"
EQ_MAINTENANCE = "Under Maintenance"
EQ_OUT_OF_STOCK = "Out of Stock"


class ServiceError(Exception):
    status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(ServiceError):
    status = 400


class NotFound(ServiceError):
    status = 404


class Conflict(ServiceError):
    status = 409


def _now():
    """Naive UTC time - same convention as datetime.utcnow() used in models.py."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _fine_per_day():
    return int(current_app.config.get("FINE_PER_DAY", 10))


def _max_booking_days():
    return int(current_app.config.get("MAX_BOOKING_DAYS", 14))


def _to_int(value, field):
    if isinstance(value, bool):
        raise ValidationError(f"'{field}' must be a whole number")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    raise ValidationError(f"'{field}' must be a whole number")


def _parse_date(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"'{field}' is required (format YYYY-MM-DD)")
    try:
        return date.fromisoformat(value.strip()[:10])
    except ValueError:
        raise ValidationError(f"'{field}' must be a valid date in YYYY-MM-DD format")


def _parse_due(value):
    """Due date is the LAST day the item may be kept (end of that day)."""
    due = _parse_date(value, "due_date")
    today = _now().date()
    if due < today:
        raise ValidationError("due_date cannot be in the past")
    if (due - today).days > _max_booking_days():
        raise ValidationError(f"due_date can be at most {_max_booking_days()} days from today")
    return datetime.combine(due, time(23, 59, 59))


def _iso(dt):
    return dt.isoformat(timespec="seconds") if dt else None


def _sync_equipment_status(equipment):
    """Keep Available <-> Out of Stock in step with the stock count.

    'Under Maintenance' is never touched - that is Person 1's decision.
    """
    if equipment.status == EQ_AVAILABLE and equipment.available_quantity <= 0:
        equipment.status = EQ_OUT_OF_STOCK
    elif equipment.status == EQ_OUT_OF_STOCK and equipment.available_quantity > 0:
        equipment.status = EQ_AVAILABLE


def _release_stock(equipment_id, quantity):
    """Give units back (used by cancel and return). Caller commits."""
    Equipment.query.filter(Equipment.id == equipment_id).update(
        {"available_quantity": Equipment.available_quantity + quantity},
        synchronize_session=False,
    )
    equipment = db.session.get(Equipment, equipment_id)
    if equipment is not None:
        db.session.refresh(equipment)
        if equipment.available_quantity > equipment.total_quantity:
            equipment.available_quantity = equipment.total_quantity
        _sync_equipment_status(equipment)


def refresh_overdue():
    """Mark issued items whose due date has passed as 'Overdue'."""
    changed = BookingRecord.query.filter(
        BookingRecord.status == ISSUED, BookingRecord.due_date < _now()
    ).update({"status": OVERDUE}, synchronize_session=False)
    if changed:
        db.session.commit()


def booking_to_dict(b, now=None):
    now = now or _now()
    fine_per_day = _fine_per_day()

    late_days = 0
    days_overdue = 0
    if b.due_date is not None:
        if b.returned_date is not None:
            late_days = max(0, (b.returned_date.date() - b.due_date.date()).days)
        elif b.status in (ISSUED, OVERDUE):
            days_overdue = max(0, (now.date() - b.due_date.date()).days)

    if b.status == RETURNED:
        return_status = "returned_late" if late_days else "returned_on_time"
    elif b.status in (ISSUED, OVERDUE):
        return_status = "not_returned"
    else:
        return_status = "not_issued"

    return {
        "id": b.id,
        "confirmation_code": f"BK-{b.id:05d}",
        "equipment_id": b.equipment_id,
        "equipment_name": b.equipment.name if b.equipment else None,
        "user_id": b.user_id,
        "user_name": b.user.name if b.user else None,
        "quantity": b.quantity,
        "status": b.status,
        "booked_date": _iso(b.booked_date),
        "due_date": _iso(b.due_date),
        "returned_date": _iso(b.returned_date),
        "return_status": return_status,
        "overdue": days_overdue > 0 or b.status == OVERDUE,
        "days_overdue": days_overdue,
        "late_days": late_days,
        # final fine once returned; fine accrued so far while still out
        "fine": (late_days if b.returned_date else days_overdue) * fine_per_day,
    }


def _get_booking(booking_id):
    booking = db.session.get(BookingRecord, booking_id)
    if booking is None:
        raise NotFound(f"Booking {booking_id} not found")
    return booking


def check_availability(equipment_id, quantity=1):
    equipment_id = _to_int(equipment_id, "equipment_id")
    quantity = 1 if quantity in (None, "") else _to_int(quantity, "quantity")
    if quantity < 1:
        raise ValidationError("'quantity' must be at least 1")

    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        raise NotFound(f"Equipment {equipment_id} not found")

    if equipment.status == EQ_MAINTENANCE:
        available, reason = False, "Under maintenance"
    elif equipment.available_quantity < quantity:
        available, reason = False, f"Only {equipment.available_quantity} available"
    else:
        available, reason = True, None

    return {
        "equipment_id": equipment.id,
        "name": equipment.name,
        "status": equipment.status,
        "total_quantity": equipment.total_quantity,
        "available_quantity": equipment.available_quantity,
        "requested_quantity": quantity,
        "available": available,
        "reason": reason,
    }


def create_booking(equipment_id, user_id, quantity, due_raw):
    equipment_id = _to_int(equipment_id, "equipment_id")
    user_id = _to_int(user_id, "user_id")
    quantity = 1 if quantity in (None, "") else _to_int(quantity, "quantity")
    if quantity < 1:
        raise ValidationError("'quantity' must be at least 1")
    due_date = _parse_due(due_raw)

    if db.session.get(User, user_id) is None:
        raise NotFound(f"User {user_id} not found")
    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        raise NotFound(f"Equipment {equipment_id} not found")
    if equipment.status == EQ_MAINTENANCE:
        raise Conflict(f"'{equipment.name}' is under maintenance")

    try:
        # Atomic check-and-take: only succeeds if enough units are still free.
        taken = Equipment.query.filter(
            Equipment.id == equipment_id,
            Equipment.available_quantity >= quantity,
            Equipment.status != EQ_MAINTENANCE,
        ).update(
            {"available_quantity": Equipment.available_quantity - quantity},
            synchronize_session=False,
        )
        if not taken:
            db.session.refresh(equipment)
            raise Conflict(
                f"Not enough '{equipment.name}' available "
                f"(requested {quantity}, available {equipment.available_quantity})"
            )

        db.session.refresh(equipment)
        _sync_equipment_status(equipment)

        record = BookingRecord(
            equipment_id=equipment_id,
            user_id=user_id,
            quantity=quantity,
            booked_date=_now(),
            due_date=due_date,
            status=BOOKED,
        )
        db.session.add(record)
        db.session.commit()
    except BaseException:
        db.session.rollback()
        raise
    return booking_to_dict(record)


def cancel_booking(booking_id):
    booking = _get_booking(booking_id)
    if booking.status != BOOKED:
        raise Conflict(
            f"Only bookings with status 'Booked' can be cancelled (this one is '{booking.status}')"
        )
    try:
        booking.status = CANCELLED
        _release_stock(booking.equipment_id, booking.quantity)
        db.session.commit()
    except BaseException:
        db.session.rollback()
        raise
    return booking_to_dict(booking)


def issue_booking(booking_id):
    """Checkout: the student physically collects the equipment."""
    booking = _get_booking(booking_id)
    if booking.status != BOOKED:
        raise Conflict(
            f"Only bookings with status 'Booked' can be issued (this one is '{booking.status}')"
        )
    if booking.due_date is not None and booking.due_date < _now():
        raise Conflict("This booking's due date has passed - cancel it and book again")
    try:
        booking.status = ISSUED
        db.session.commit()
    except BaseException:
        db.session.rollback()
        raise
    return booking_to_dict(booking)


def return_booking(booking_id, returned_on_raw=None):
    """Mark as returned; late days and fine are derived from due_date.

    `returned_on` (YYYY-MM-DD) is optional - it records a return on another day
    and makes late fines easy to demo/test.
    """
    refresh_overdue()
    booking = _get_booking(booking_id)
    if booking.status not in (ISSUED, OVERDUE):
        raise Conflict(
            f"Only issued bookings can be returned (this one is '{booking.status}')"
        )

    now = _now()
    returned_at = now
    if returned_on_raw:
        returned_at = datetime.combine(_parse_date(returned_on_raw, "returned_on"), now.time())
    if booking.booked_date is not None and returned_at.date() < booking.booked_date.date():
        raise ValidationError("returned_on cannot be before the booking date")

    try:
        booking.returned_date = returned_at
        booking.status = RETURNED
        _release_stock(booking.equipment_id, booking.quantity)
        db.session.commit()
    except BaseException:
        db.session.rollback()
        raise
    return booking_to_dict(booking)


def get_booking(booking_id):
    refresh_overdue()
    return booking_to_dict(_get_booking(booking_id))


def list_bookings(user_id=None, equipment_id=None, status=None):
    refresh_overdue()
    query = BookingRecord.query
    if user_id not in (None, ""):
        query = query.filter(BookingRecord.user_id == _to_int(user_id, "user_id"))
    if equipment_id not in (None, ""):
        query = query.filter(BookingRecord.equipment_id == _to_int(equipment_id, "equipment_id"))
    if status:
        canonical = _STATUS_LOOKUP.get(status.strip().lower())
        if canonical is None:
            raise ValidationError(f"'status' must be one of: {', '.join(ALL_STATUSES)}")
        query = query.filter(BookingRecord.status == canonical)
    rows = query.order_by(BookingRecord.id.desc()).all()
    now = _now()
    return [booking_to_dict(b, now) for b in rows]