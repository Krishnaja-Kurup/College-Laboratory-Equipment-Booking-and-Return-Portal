"""
Equipment Model for College Laboratory Equipment Booking Portal.
Tracks equipment details, total stock, available stock, and status.
"""
from datetime import datetime, timezone
from models import db

class Equipment(db.Model):
    __tablename__ = "equipment"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    total_quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(50), nullable=False, default="Available")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship to bookings for this piece of equipment
    bookings = db.relationship("Booking", back_populates="equipment", cascade="all, delete-orphan")

    def update_status(self):
        """
        Automatically calculate and update the equipment availability status
        based on total_quantity and available_quantity.
        """
        if self.available_quantity <= 0:
            self.status = "Unavailable"
        elif self.available_quantity < self.total_quantity:
            self.status = "Partially Available"
        else:
            self.status = "Available"

    @property
    def is_available(self):
        """Check if equipment has units available to book."""
        return self.available_quantity > 0

    @property
    def status_badge_class(self):
        """Bootstrap badge CSS class helper for Jinja templates."""
        if self.status == "Available":
            return "bg-success"
        elif self.status == "Partially Available":
            return "bg-warning text-dark"
        else:
            return "bg-danger"

    def __repr__(self):
        return f"<Equipment {self.id}: {self.name} ({self.available_quantity}/{self.total_quantity})>"
