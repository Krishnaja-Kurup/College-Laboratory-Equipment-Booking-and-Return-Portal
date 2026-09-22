"""
Admin Blueprint.
Handles equipment management (CRUD), booking approvals/rejections,
user overview, and administrative dashboard statistics.
"""
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.equipment import Equipment
from models.booking import Booking
from models.user import User
from routes import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    """
    Admin Dashboard.
    Provides system-wide overview metrics:
    - Total equipment
    - Available equipment
    - Total students
    - Total bookings
    - Pending bookings
    - Returned equipment
    """
    total_equipment = Equipment.query.count()
    available_equipment = Equipment.query.filter(Equipment.available_quantity > 0).count()
    total_students = User.query.filter_by(role="student").count()
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(status="Pending").count()
    returned_equipment = Booking.query.filter_by(status="Returned").count()

    # Get recent pending bookings that require action
    pending_list = Booking.query.filter_by(status="Pending")\
        .order_by(Booking.created_at.desc()).limit(5).all()

    # Get recent overall bookings
    recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

    return render_template(
        "admin/dashboard.html",
        total_equipment=total_equipment,
        available_equipment=available_equipment,
        total_students=total_students,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        returned_equipment=returned_equipment,
        pending_list=pending_list,
        recent_bookings=recent_bookings
    )

@admin_bp.route("/equipment")
@admin_required
def equipment():
    """
    Admin Equipment Inventory.
    Lists all laboratory items in a table with stock levels, status,
    and Edit / Delete actions.
    """
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = Equipment.query

    if category and category != "All":
        query = query.filter_by(category=category)

    if search:
        query = query.filter(
            (Equipment.name.ilike(f"%{search}%")) |
            (Equipment.description.ilike(f"%{search}%"))
        )

    equipment_list = query.order_by(Equipment.id.asc()).all()
    categories = [cat[0] for cat in db.session.query(Equipment.category).distinct().all()]

    return render_template(
        "admin/equipment.html",
        equipment_list=equipment_list,
        categories=categories,
        selected_category=category,
        search_query=search
    )

@admin_bp.route("/equipment/add", methods=["GET", "POST"])
@admin_required
def add_equipment():
    """
    Add New Laboratory Equipment.
    Initializes available_quantity = total_quantity and auto-sets status.
    """
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        total_quantity = request.form.get("total_quantity", type=int)

        # Validation
        if not name or not category or total_quantity is None:
            flash("Equipment Name, Category, and Total Quantity are required.", "danger")
            return render_template("admin/add_equipment.html")

        if total_quantity < 0:
            flash("Total quantity cannot be negative.", "danger")
            return render_template("admin/add_equipment.html")

        try:
            item = Equipment(
                name=name,
                category=category,
                description=description,
                total_quantity=total_quantity,
                available_quantity=total_quantity
            )
            item.update_status()

            db.session.add(item)
            db.session.commit()

            flash(f"Equipment '{item.name}' added successfully!", "success")
            return redirect(url_for("admin.equipment"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding equipment: {str(e)}", "danger")

    return render_template("admin/add_equipment.html")

@admin_bp.route("/equipment/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_equipment(id):
    """
    Edit Equipment Details.
    Maintains inventory integrity and recalculates status.
    """
    item = db.get_or_404(Equipment, id)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        total_quantity = request.form.get("total_quantity", type=int)
        available_quantity = request.form.get("available_quantity", type=int)

        if not name or not category or total_quantity is None or available_quantity is None:
            flash("All fields except description are required.", "danger")
            return render_template("admin/edit_equipment.html", equipment=item)

        if total_quantity < 0 or available_quantity < 0:
            flash("Quantities cannot be negative numbers.", "danger")
            return render_template("admin/edit_equipment.html", equipment=item)

        if available_quantity > total_quantity:
            flash("Available quantity cannot exceed total quantity.", "danger")
            return render_template("admin/edit_equipment.html", equipment=item)

        try:
            item.name = name
            item.category = category
            item.description = description
            item.total_quantity = total_quantity
            item.available_quantity = available_quantity
            item.update_status()

            db.session.commit()
            flash(f"Equipment '{item.name}' updated successfully!", "success")
            return redirect(url_for("admin.equipment"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating equipment: {str(e)}", "danger")

    return render_template("admin/edit_equipment.html", equipment=item)

@admin_bp.route("/equipment/delete/<int:id>", methods=["POST"])
@admin_required
def delete_equipment(id):
    """
    Delete Equipment Item.
    Guards against deleting equipment with active ongoing bookings.
    """
    item = db.get_or_404(Equipment, id)

    # Check for active bookings
    active_count = Booking.query.filter(
        Booking.equipment_id == id,
        Booking.status.in_(["Pending", "Approved", "Booked"])
    ).count()

    if active_count > 0:
        flash(f"Cannot delete '{item.name}' because it currently has {active_count} active booking(s).", "danger")
        return redirect(url_for("admin.equipment"))

    try:
        db.session.delete(item)
        db.session.commit()
        flash(f"Equipment '{item.name}' has been deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting equipment: {str(e)}", "danger")

    return redirect(url_for("admin.equipment"))

@admin_bp.route("/bookings")
@admin_required
def bookings():
    """
    Admin Bookings Overview.
    Displays all student bookings with filtering by status.
    """
    status_filter = request.args.get("status", "all").strip()

    query = Booking.query

    if status_filter != "all" and status_filter:
        query = query.filter(Booking.status == status_filter)

    all_bookings = query.order_by(Booking.created_at.desc()).all()

    # Status count metrics for filter pill tabs
    counts = {
        "all": Booking.query.count(),
        "pending": Booking.query.filter_by(status="Pending").count(),
        "approved": Booking.query.filter_by(status="Approved").count(),
        "returned": Booking.query.filter_by(status="Returned").count(),
        "rejected": Booking.query.filter_by(status="Rejected").count(),
    }

    return render_template(
        "admin/bookings.html",
        bookings=all_bookings,
        counts=counts,
        current_filter=status_filter
    )

@admin_bp.route("/bookings/<int:id>/approve", methods=["POST"])
@admin_required
def approve_booking(id):
    """Approve a pending student booking."""
    booking = db.get_or_404(Booking, id)

    if booking.status != "Pending":
        flash(f"Booking is already in '{booking.status}' status.", "warning")
        return redirect(url_for("admin.bookings"))

    booking.status = "Approved"
    db.session.commit()
    flash(f"Booking #{booking.id} for {booking.user.name} approved successfully!", "success")
    return redirect(url_for("admin.bookings"))

@admin_bp.route("/bookings/<int:id>/reject", methods=["POST"])
@admin_required
def reject_booking(id):
    """
    Reject a booking.
    Restores the reserved equipment quantity back to inventory.
    """
    booking = db.get_or_404(Booking, id)

    if booking.status in ["Returned", "Rejected"]:
        flash("This booking is already closed.", "warning")
        return redirect(url_for("admin.bookings"))

    try:
        # If the booking was pending or approved, restore the quantity
        item = booking.equipment
        item.available_quantity += booking.quantity
        item.update_status()

        booking.status = "Rejected"
        db.session.commit()

        flash(f"Booking #{booking.id} rejected. {booking.quantity} unit(s) returned to available inventory.", "info")
    except Exception as e:
        db.session.rollback()
        flash(f"Error rejecting booking: {str(e)}", "danger")

    return redirect(url_for("admin.bookings"))

@admin_bp.route("/bookings/<int:id>/return", methods=["POST"])
@admin_required
def return_booking(id):
    """
    Admin action to mark equipment returned if student returns to lab desk.
    """
    booking = db.get_or_404(Booking, id)

    if booking.status == "Returned":
        flash("Booking already marked as returned.", "info")
        return redirect(url_for("admin.bookings"))

    try:
        booking.status = "Returned"
        booking.returned_date = date.today()

        item = booking.equipment
        item.available_quantity += booking.quantity
        item.update_status()

        db.session.commit()
        flash(f"Booking #{booking.id} marked as Returned.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error marking booking as returned: {str(e)}", "danger")

    return redirect(url_for("admin.bookings"))

@admin_bp.route("/users")
@admin_required
def users():
    """
    Manage Student Users.
    Lists all student accounts, email, registration date, and booking stats.
    """
    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()

    # Pre-calculate counts per student for display
    student_data = []
    for s in students:
        total = len(s.bookings)
        active = sum(1 for b in s.bookings if b.status in ["Pending", "Approved", "Booked"])
        student_data.append({
            "user": s,
            "total_bookings": total,
            "active_bookings": active
        })

    return render_template("admin/users.html", student_data=student_data)
