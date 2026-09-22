"""
Booking Model for College Laboratory Equipment Booking Portal.
Tracks reservation lifecycle, quantities, due dates, and return status.
"""
from datetime import datetime, date, timezone
from models import db

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey("equipment.id"), nullable=False, index=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    booking_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    returned_date = db.Column(db.Date, nullable=True)
    
    # Status can be: 'Pending', 'Approved', 'Booked', 'Returned', 'Rejected', 'Overdue'
    status = db.Column(db.String(50), nullable=False, default="Booked")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = db.relationship("User", back_populates="bookings")
    equipment = db.relationship("Equipment", back_populates="bookings")

    @property
    def is_overdue(self):
        """Check if active booking is past its due date."""
        if self.status in ["Booked", "Approved", "Pending"] and self.due_date < date.today():
            return True
        return self.status == "Overdue"

    @property
    def display_status(self):
        """Dynamic display status factoring in overdue check."""
        if self.is_overdue and self.status in ["Booked", "Approved"]:
            return "Overdue"
        return self.status

    @property
    def status_badge_class(self):
        """Bootstrap badge CSS class helper."""
        current = self.display_status
        if current in ["Approved", "Booked"]:
            return "bg-primary"
        elif current == "Pending":
            return "bg-warning text-dark"
        elif current == "Returned":
            return "bg-success"
        elif current == "Overdue":
            return "bg-danger"
        elif current == "Rejected":
            return "bg-secondary"
        return "bg-dark"

    def __repr__(self):
        return f"<Booking {self.id}: User {self.user_id} -> Equip {self.equipment_id} ({self.status})>"
