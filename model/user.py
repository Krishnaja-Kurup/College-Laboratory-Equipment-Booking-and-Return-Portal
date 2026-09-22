"""
User Model for College Laboratory Equipment Booking Portal.
Supports both 'student' and 'admin' roles with secure password hashing.
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # 'student' or 'admin'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to bookings made by this user
    bookings = db.relationship("Booking", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and store the user's password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the provided plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Helper to quickly check if user has admin privileges."""
        return self.role == "admin"

    @property
    def is_student(self):
        """Helper to quickly check if user is a student."""
        return self.role == "student"

    def __repr__(self):
        return f"<User {self.id}: {self.name} ({self.role})>"
