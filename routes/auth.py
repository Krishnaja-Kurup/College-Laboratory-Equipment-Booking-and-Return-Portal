"""
Authentication Blueprint.
Handles Student and Admin logins, session management, and logout.
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.user import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def index():
    """Root route: redirects authenticated users to their dashboard, otherwise to login."""
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
@auth_bp.route("/student/login", methods=["GET", "POST"])
def login():
    """
    General / Student Login View.
    Supports email and password login with session initialization.
    """
    # If already logged in, redirect to respective dashboard
    if "user_id" in session:
        if session.get("role") == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Validation
        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/login.html", email=email)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            # Session assignment
            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            session["email"] = user.email

            flash(f"Welcome back, {user.name}!", "success")

            # Redirect based on user role
            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.dashboard"))
        else:
            flash("Invalid email or password. Please try again.", "danger")
            return render_template("auth/login.html", email=email)

    return render_template("auth/login.html")

@auth_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """
    Dedicated Administrator Login View.
    Strictly verifies admin role upon authentication.
    """
    if "user_id" in session and session.get("role") == "admin":
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both administrator email and password.", "danger")
            return render_template("auth/admin_login.html", email=email)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if user.role != "admin":
                flash("Access denied: This account does not possess administrator privileges.", "danger")
                return render_template("auth/admin_login.html", email=email)

            session.clear()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["role"] = user.role
            session["email"] = user.email

            flash(f"Admin authentication successful. Welcome, {user.name}!", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Invalid administrator credentials.", "danger")
            return render_template("auth/admin_login.html", email=email)

    return render_template("auth/admin_login.html")

@auth_bp.route("/logout")
def logout():
    """Log out current user and clear active session."""
    user_name = session.get("user_name")
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
