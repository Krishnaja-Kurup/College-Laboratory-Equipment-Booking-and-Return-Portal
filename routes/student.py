"""
Student Blueprint.
Handles equipment browsing, searching, booking creation, return actions,
and student dashboard & profile views.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db
from models.equipment import Equipment
from models.booking import Booking
from models.user import User
from routes import login_required, student_required

student_bp = Blueprint("student", __name__, url_prefix="/student")

@student_bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    """
    Student Dashboard.
    Displays summary counts (Total Equipment, Available, My Bookings)
    and quick action navigation buttons.
    """
    user_id = session.get("user_id")

    # Metrics
    total_equipment = Equipment.query.count()
    available_equipment = Equipment.query.filter(Equipment.available_quantity > 0).count()
    
    # Active bookings for this student (Pending, Approved, Booked)
    active_bookings_count = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.status.in_(["Pending", "Approved", "Booked"])
    ).count()

    # Recent bookings for quick glance
    recent_bookings = Booking.query.filter_by(user_id=user_id)\
        .order_by(Booking.created_at.desc())\
        .limit(5).all()

    return render_template(
        "student/dashboard.html",
        total_equipment=total_equipment,
        available_equipment=available_equipment,
        active_bookings_count=active_bookings_count,
        recent_bookings=recent_bookings
    )

@student_bp.route("/equipment")
@login_required
@student_required
def equipment():
    """
    Equipment Catalog.
    Displays equipment in responsive Bootstrap cards with live search
    and category filtering.
    """
    category = request.args.get("category", "").strip()
    search = request.args.get("search", "").strip()

    query = Equipment.query

    if category and category != "All":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            (Equipment.name.ilike(f"%{search}%")) |
            (Equipment.description.ilike(f"%{search}%"))
        )

    equipment_list = query.order_by(Equipment.name.asc()).all()

    # Fetch distinct categories for the dropdown
    categories = [cat[0] for cat in db.session.query(Equipment.category).distinct().all()]

    return render_template(
        "student/equipment.html",
        equipment_list=equipment_list,
        categories=categories,
        selected_category=category,
        search_query=search
    )

@student_bp.route("/equipment/<int:id>")
@login_required
@student_required
def equipment_details(id):
    """
    Equipment Details Page.
    Shows comprehensive specifications and booking form.
    """
    item = db.get_or_404(Equipment, id)
    today_str = date.today().isoformat()
    return render_template("student/equipment_details.html", equipment=item, today=today_str)

@student_bp.route("/book", methods=["POST"])
@login_required
@student_required
def book():
    """
    Process laboratory equipment booking request.
    Deducts available quantity, updates status, and stores booking.
    """
    user_id = session.get("user_id")
    equipment_id = request.form.get("equipment_id", type=int)
    quantity = request.form.get("quantity", type=int)
    due_date_str = request.form.get("due_date", "").strip()

    # Basic validations
    if not equipment_id or not quantity or not due_date_str:
        flash("All booking fields are required.", "danger")
        return redirect(url_for("student.equipment"))

    item = db.get_or_404(Equipment, equipment_id)

    # Quantity validations
    if quantity <= 0:
        flash("Booking quantity must be at least 1.", "danger")
        return redirect(url_for("student.equipment_details", id=equipment_id))

    if quantity > item.available_quantity:
        flash(f"Only {item.available_quantity} unit(s) are currently available.", "danger")
        return redirect(url_for("student.equipment_details", id=equipment_id))

    # Due date validation
    try:
        due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid due date format. Please use YYYY-MM-DD.", "danger")
        return redirect(url_for("student.equipment_details", id=equipment_id))

    if due_date < date.today():
        flash("Due date cannot be before today's date.", "danger")
        return redirect(url_for("student.equipment_details", id=equipment_id))

    try:
        # Deduct available quantity immediately to prevent overbooking
        item.available_quantity -= quantity
        item.update_status()

        # Create booking record (initial status is 'Pending' for admin review)
        booking = Booking(
            user_id=user_id,
            equipment_id=equipment_id,
            quantity=quantity,
            booking_date=date.today(),
            due_date=due_date,
            status="Pending"
        )

        db.session.add(booking)
        db.session.commit()

        flash(f"Successfully submitted booking for {quantity} unit(s) of {item.name}! Awaiting lab admin confirmation.", "success")
        return redirect(url_for("student.bookings"))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while placing the booking: {str(e)}", "danger")
        return redirect(url_for("student.equipment_details", id=equipment_id))

@student_bp.route("/bookings")
@login_required
@student_required
def bookings():
    """
    My Bookings.
    Lists all past and active bookings for the logged-in student.
    """
    user_id = session.get("user_id")
    student_bookings = Booking.query.filter_by(user_id=user_id)\
        .order_by(Booking.created_at.desc()).all()

    return render_template("student/bookings.html", bookings=student_bookings)

@student_bp.route("/return/<int:booking_id>", methods=["POST"])
@login_required
@student_required
def return_equipment(booking_id):
    """
    Return booked equipment.
    Restores available quantity, recalculates status, and timestamps return.
    """
    user_id = session.get("user_id")
    booking = db.get_or_404(Booking, booking_id)

    # Authorization & validation checks
    if booking.user_id != user_id:
        flash("You are not authorized to return this equipment.", "danger")
        return redirect(url_for("student.bookings"))

    if booking.status == "Returned":
        flash("This equipment has already been returned.", "warning")
        return redirect(url_for("student.bookings"))

    if booking.status == "Rejected":
        flash("This booking was rejected.", "warning")
        return redirect(url_for("student.bookings"))

    try:
        # Return equipment
        booking.status = "Returned"
        booking.returned_date = date.today()

        # Restore inventory
        item = booking.equipment
        item.available_quantity += booking.quantity
        item.update_status()

        db.session.commit()
        flash(f"Successfully returned {booking.quantity} unit(s) of {item.name}. Thank you!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error returning equipment: {str(e)}", "danger")

    return redirect(url_for("student.bookings"))

@student_bp.route("/profile")
@login_required
@student_required
def profile():
    """
    Student Profile.
    Displays student account details and booking statistics.
    """
    user_id = session.get("user_id")
    user = db.get_or_404(User, user_id)

    total_bookings = Booking.query.filter_by(user_id=user_id).count()
    active_bookings = Booking.query.filter(
        Booking.user_id == user_id,
        Booking.status.in_(["Pending", "Approved", "Booked"])
    ).count()
    returned_bookings = Booking.query.filter_by(user_id=user_id, status="Returned").count()

    return render_template(
        "student/profile.html",
        user=user,
        total_bookings=total_bookings,
        active_bookings=active_bookings,
        returned_bookings=returned_bookings
    )
