from app import app
from models import db, User

with app.app_context():

    users = [
        User(name="Student", email="student@gmail.com",
             password="Student@123", role="student"),

        User(name="Rahul", email="rahul@gmail.com",
             password="Rahul@123", role="student"),

        User(name="Neha", email="neha@gmail.com",
             password="Neha@123", role="student"),

        User(name="Faculty", email="faculty@gmail.com",
             password="Faculty@123", role="faculty")
    ]

    db.session.add_all(users)
    db.session.commit()

    print("Sample users added successfully!")