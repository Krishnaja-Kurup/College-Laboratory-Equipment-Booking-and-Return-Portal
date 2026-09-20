"""Booking & Return API (Person 2). Register with:  app.register_blueprint(booking_bp)"""
from flask import Blueprint, jsonify, request

import booking_service as svc

booking_bp = Blueprint("booking_api", __name__, url_prefix="/api/bookings")


@booking_bp.errorhandler(svc.ServiceError)
def handle_service_error(err):
    return jsonify(error=err.message), err.status


def _json_body(required=True):
    data = request.get_json(silent=True)
    if data is None and not required:
        return {}
    if not isinstance(data, dict):
        raise svc.ValidationError("Request body must be a JSON object")
    return data


@booking_bp.get("/availability/<int:equipment_id>")
def availability(equipment_id):
    return jsonify(svc.check_availability(equipment_id, request.args.get("quantity")))


@booking_bp.post("")
def create():
    data = _json_body()
    booking = svc.create_booking(
        data.get("equipment_id"),
        data.get("user_id"),
        data.get("quantity"),
        data.get("due_date"),
    )
    return jsonify(message="Booking confirmed", booking=booking), 201


@booking_bp.get("")
def history():
    return jsonify(
        svc.list_bookings(
            user_id=request.args.get("user_id"),
            equipment_id=request.args.get("equipment_id"),
            status=request.args.get("status"),
        )
    )


@booking_bp.get("/overdue")
def overdue():
    return jsonify(svc.list_bookings(status="Overdue"))


@booking_bp.get("/<int:booking_id>")
def detail(booking_id):
    return jsonify(svc.get_booking(booking_id))


@booking_bp.post("/<int:booking_id>/cancel")
def cancel(booking_id):
    return jsonify(message="Booking cancelled", booking=svc.cancel_booking(booking_id))


@booking_bp.post("/<int:booking_id>/issue")
def issue(booking_id):
    return jsonify(message="Equipment issued", booking=svc.issue_booking(booking_id))


@booking_bp.post("/<int:booking_id>/return")
def return_item(booking_id):
    data = _json_body(required=False)
    booking = svc.return_booking(booking_id, data.get("returned_on"))
    if booking["late_days"]:
        msg = f"Returned {booking['late_days']} day(s) late - fine: {booking['fine']}"
    else:
        msg = "Returned on time"
    return jsonify(message=msg, booking=booking)