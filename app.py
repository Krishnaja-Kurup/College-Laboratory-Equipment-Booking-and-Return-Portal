"""
College Laboratory Equipment Booking and Return Portal.
Main Flask Application Factory and Entry Point.
"""
import os
from datetime import date
from flask import Flask, render_template, session
from sqlalchemy import create_engine, text
from config import Config
from models import db
from routes.auth import auth_bp
from routes.student import student_bp
from routes.admin import admin_bp

def verify_and_resolve_db_uri(target_uri):
    """
    Checks if configured target database (e.g. PostgreSQL) is reachable.
    If PostgreSQL is unreachable or credentials are unconfigured,
    gracefully returns local SQLite URI fallback so the application
    runs seamlessly out-of-the-box.
    """
    if not target_uri or not target_uri.startswith("postgresql"):
        return target_uri

    try:
        engine = create_engine(target_uri, connect_args={"connect_timeout": 2})
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine.dispose()
        return target_uri
    except Exception as e:
        print("\n" + "=" * 65)
        print("[NOTICE] PostgreSQL is not yet configured or credentials in .env failed:")
        print(f"         {e.args[0] if e.args else e}")
        print("[INFO]   To use PostgreSQL:")
        print("         1. Ensure PostgreSQL is running on port 5432.")
        print("         2. Create database: CREATE DATABASE college_lab_portal;")
        print("         3. Set DATABASE_URL=postgresql://<user>:<password>@localhost:5432/college_lab_portal in .env")
        print("[INFO]   --> Activating SQLite ('college_lab_portal.db') fallback for this run.")
        print("=" * 65 + "\n")
        return "sqlite:///college_lab_portal.db"

def create_app(config_class=Config):
    """Factory to create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Automatically resolve working database URI (PostgreSQL or SQLite fallback)
    resolved_uri = verify_and_resolve_db_uri(app.config.get("SQLALCHEMY_DATABASE_URI"))
    app.config["SQLALCHEMY_DATABASE_URI"] = resolved_uri

    # Initialize SQLAlchemy with application
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # Context processor to inject global variables into all templates
    @app.context_processor
    def inject_globals():
        return {
            "current_year": date.today().year,
            "session_user_name": session.get("user_name"),
            "session_role": session.get("role"),
            "is_logged_in": "user_id" in session
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app

app = create_app()

def initialize_database():
    """Create tables and auto-seed if database is empty."""
    with app.app_context():
        db.create_all()
        from models.user import User
        if User.query.count() == 0:
            print("[INFO] Database is empty. Seeding sample users, equipment, and bookings...")
            from database.seed import seed_database
            use_sqlite = "sqlite" in app.config["SQLALCHEMY_DATABASE_URI"]
            seed_database(use_sqlite=use_sqlite)

if __name__ == "__main__":
    initialize_database()

    # Run Flask development server
    print("\n========================================================")
    print(" College Laboratory Equipment Booking & Return Portal")
    print(f" Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(" Server running at: http://127.0.0.1:5000")
    print(" Student Login:     http://127.0.0.1:5000/login")
    print(" Admin Login:       http://127.0.0.1:5000/admin/login")
    print("========================================================\n")
    app.run(debug=True, host="127.0.0.1", port=5000)
