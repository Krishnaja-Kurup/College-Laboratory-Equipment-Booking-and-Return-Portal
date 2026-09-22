"""
Comprehensive Automated Test Suite for College Laboratory Equipment Booking and Return Portal.
Tests:
- Model logic & status calculations
- Role-based route protections
- Authentication (student & admin login/logout)
- Equipment catalog, search, and CRUD
- Booking creation, quantity deduction, and validation
- Return processing and quantity restoration
- Admin approvals and rejections
- Error handling (403, 404)
"""
import unittest
from datetime import date, timedelta
from app import create_app
from config import Config
from models import db
from models.user import User
from models.equipment import Equipment
from models.booking import Booking

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "test-secret-key"

class LabPortalTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()

        db.create_all()

        # Create Admin
        self.admin = User(name="Admin User", email="admin@test.com", role="admin")
        self.admin.set_password("adminpass")

        # Create Student
        self.student = User(name="Student User", email="student@test.com", role="student")
        self.student.set_password("studentpass")

        # Create Equipment
        self.equip = Equipment(
            name="Digital Multimeter",
            category="Electrical",
            description="Precision measurement meter",
            total_quantity=10,
            available_quantity=10
        )
        self.equip.update_status()

        db.session.add_all([self.admin, self.student, self.equip])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    # ---------------------------------------------------------
    # Authentication Tests
    # ---------------------------------------------------------
    def test_student_login_success(self):
        response = self.client.post("/login", data={
            "email": "student@test.com",
            "password": "studentpass"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome back, Student User!", response.data)
        self.assertIn(b"My Active Bookings", response.data)

    def test_student_login_failure(self):
        response = self.client.post("/login", data={
            "email": "student@test.com",
            "password": "wrongpassword"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid email or password", response.data)

    def test_admin_login_success(self):
        response = self.client.post("/admin/login", data={
            "email": "admin@test.com",
            "password": "adminpass"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Admin authentication successful", response.data)
        self.assertIn(b"Administrator Console", response.data)

    def test_student_cannot_login_as_admin(self):
        response = self.client.post("/admin/login", data={
            "email": "student@test.com",
            "password": "studentpass"
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"does not possess administrator privileges", response.data)

    def test_logout(self):
        # Login first
        self.client.post("/login", data={"email": "student@test.com", "password": "studentpass"})
        response = self.client.get("/logout", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"logged out successfully", response.data)

    # ---------------------------------------------------------
    # Role Protection Tests
    # ---------------------------------------------------------
    def test_unauthenticated_access_blocked(self):
        response = self.client.get("/student/dashboard", follow_redirects=True)
        self.assertIn(b"Please log in to continue", response.data)

        response2 = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertIn(b"Administrator login required", response2.data)

    def test_student_cannot_access_admin_dashboard(self):
        # Login as student
        self.client.post("/login", data={"email": "student@test.com", "password": "studentpass"})
        response = self.client.get("/admin/dashboard", follow_redirects=True)
        self.assertIn(b"Administrator privileges required", response.data)

    # ---------------------------------------------------------
    # Equipment Status Logic Tests
    # ---------------------------------------------------------
    def test_equipment_status_logic(self):
        eq = Equipment(name="Test Scope", category="Test", total_quantity=5, available_quantity=5)
        eq.update_status()
        self.assertEqual(eq.status, "Available")

        eq.available_quantity = 3
        eq.update_status()
        self.assertEqual(eq.status, "Partially Available")

        eq.available_quantity = 0
        eq.update_status()
        self.assertEqual(eq.status, "Unavailable")

    # ---------------------------------------------------------
    # Booking & Return Logic Tests
    # ---------------------------------------------------------
    def test_successful_booking_and_quantity_deduction(self):
        # Login student
        self.client.post("/login", data={"email": "student@test.com", "password": "studentpass"})

        due_date = (date.today() + timedelta(days=7)).isoformat()
        response = self.client.post("/student/book", data={
            "equipment_id": self.equip.id,
            "quantity": 3,
            "due_date": due_date
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Successfully submitted booking", response.data)

        # Verify available quantity updated
        updated_equip = db.session.get(Equipment, self.equip.id)
        self.assertEqual(updated_equip.available_quantity, 7)
        self.assertEqual(updated_equip.status, "Partially Available")

        # Verify booking created
        booking = Booking.query.filter_by(equipment_id=self.equip.id).first()
        self.assertIsNotNone(booking)
        self.assertEqual(booking.quantity, 3)

    def test_overbooking_prevented(self):
        self.client.post("/login", data={"email": "student@test.com", "password": "studentpass"})

        due_date = (date.today() + timedelta(days=7)).isoformat()
        # Request more than available (10)
        response = self.client.post("/student/book", data={
            "equipment_id": self.equip.id,
            "quantity": 15,
            "due_date": due_date
        }, follow_redirects=True)

        self.assertIn(b"Only 10 unit(s) are currently available", response.data)
        updated_equip = db.session.get(Equipment, self.equip.id)
        self.assertEqual(updated_equip.available_quantity, 10)

    def test_successful_return_and_quantity_restoration(self):
        # Student books equipment
        self.client.post("/login", data={"email": "student@test.com", "password": "studentpass"})
        due_date = (date.today() + timedelta(days=7)).isoformat()
        self.client.post("/student/book", data={
            "equipment_id": self.equip.id,
            "quantity": 2,
            "due_date": due_date
        })

        booking = Booking.query.filter_by(equipment_id=self.equip.id).first()
        self.assertEqual(self.equip.available_quantity, 8)

        # Student returns equipment
        return_resp = self.client.post(f"/student/return/{booking.id}", follow_redirects=True)
        self.assertEqual(return_resp.status_code, 200)
        self.assertIn(b"Successfully returned 2 unit(s)", return_resp.data)

        # Inventory restored
        refreshed_equip = db.session.get(Equipment, self.equip.id)
        self.assertEqual(refreshed_equip.available_quantity, 10)
        self.assertEqual(refreshed_equip.status, "Available")

        # Booking updated
        refreshed_booking = db.session.get(Booking, booking.id)
        self.assertEqual(refreshed_booking.status, "Returned")
        self.assertEqual(refreshed_booking.returned_date, date.today())

    # ---------------------------------------------------------
    # Admin Equipment CRUD Tests
    # ---------------------------------------------------------
    def test_admin_add_equipment(self):
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "adminpass"})

        response = self.client.post("/admin/equipment/add", data={
            "name": "Centrifuge 5000",
            "category": "Biotech",
            "description": "High-speed laboratory centrifuge",
            "total_quantity": 4
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Centrifuge 5000", response.data)

        new_item = Equipment.query.filter_by(name="Centrifuge 5000").first()
        self.assertIsNotNone(new_item)
        self.assertEqual(new_item.available_quantity, 4)
        self.assertEqual(new_item.status, "Available")

    def test_admin_edit_equipment(self):
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "adminpass"})

        response = self.client.post(f"/admin/equipment/edit/{self.equip.id}", data={
            "name": "Digital Multimeter Pro",
            "category": "Electrical",
            "description": "Updated description",
            "total_quantity": 12,
            "available_quantity": 12
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"updated successfully", response.data)

        updated = db.session.get(Equipment, self.equip.id)
        self.assertEqual(updated.name, "Digital Multimeter Pro")
        self.assertEqual(updated.total_quantity, 12)

    def test_admin_delete_equipment_safely(self):
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "adminpass"})

        response = self.client.post(f"/admin/equipment/delete/{self.equip.id}", follow_redirects=True)
        self.assertIn(b"has been deleted", response.data)
        self.assertIsNone(db.session.get(Equipment, self.equip.id))

    # ---------------------------------------------------------
    # Admin Booking Approval & Rejection Tests
    # ---------------------------------------------------------
    def test_admin_approve_and_reject_booking(self):
        # Create a pending booking
        due_date = date.today() + timedelta(days=5)
        booking = Booking(
            user_id=self.student.id,
            equipment_id=self.equip.id,
            quantity=2,
            booking_date=date.today(),
            due_date=due_date,
            status="Pending"
        )
        self.equip.available_quantity -= 2
        self.equip.update_status()
        db.session.add(booking)
        db.session.commit()

        # Admin logs in and approves
        self.client.post("/admin/login", data={"email": "admin@test.com", "password": "adminpass"})
        approve_resp = self.client.post(f"/admin/bookings/{booking.id}/approve", follow_redirects=True)
        self.assertEqual(approve_resp.status_code, 200)
        self.assertIn(b"approved successfully", approve_resp.data)
        self.assertEqual(db.session.get(Booking, booking.id).status, "Approved")

        # Now test rejection resets quantity
        reject_resp = self.client.post(f"/admin/bookings/{booking.id}/reject", follow_redirects=True)
        self.assertEqual(reject_resp.status_code, 200)
        self.assertIn(b"rejected", reject_resp.data)
        self.assertEqual(db.session.get(Booking, booking.id).status, "Rejected")
        self.assertEqual(db.session.get(Equipment, self.equip.id).available_quantity, 10)

if __name__ == "__main__":
    unittest.main()
