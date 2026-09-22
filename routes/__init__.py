"""
Routes package for College Laboratory Equipment Booking Portal.
Provides reusable authentication and role authorization decorators.
"""
from functools import wraps
from flask import session, redirect, url_for, flash, request

def login_required(f):
    """Ensure user is logged in before accessing the view."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Ensure current user is authenticated with 'admin' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Administrator login required.", "warning")
            return redirect(url_for("auth.admin_login", next=request.url))
        if session.get("role") != "admin":
            flash("Access denied. Administrator privileges required.", "danger")
            return redirect(url_for("student.dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    """Ensure current user is authenticated with 'student' role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access the student portal.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        if session.get("role") != "student":
            flash("Access restricted to student accounts.", "warning")
            return redirect(url_for("admin.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
