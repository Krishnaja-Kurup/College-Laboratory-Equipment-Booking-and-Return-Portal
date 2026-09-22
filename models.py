from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Equipment(db.Model):
    """
    Core table owned by Person 1 (Equipment & Database).
    Tracks each item in the lab inventory and how many are free right now.
    """
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False, default="General")
    total_quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default="Available")
    # Available / Under Maintenance / Out of Stock
    added_date = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship("BookingRecord", backref="equipment", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "total_quantity": self.total_quantity,
            "available_quantity": self.available_quantity,
            "status": self.status,
        }


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    # student / faculty / admin

    bookings = db.relationship("BookingRecord", backref="user", lazy=True)


class BookingRecord(db.Model):
    """
    Shared table — this is the seam between your work (Equipment & Database)
    and your teammate's work (Booking & Return System). Agree on this schema
    together before either of you builds logic on top of it.
    """
    __tablename__ = "booking_records"

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    booked_date = db.Column(db.DateTime, default=datetime.utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    returned_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="Booked")
    # Booked / Returned / Overdue
