from flask import Flask
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)


@app.route("/")
def home():
    return redirect(url_for("student_login"))


@app.route("/student/login")
def student_login():
    return render_template("student_login.html")


@app.route("/student/dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")
@app.route("/admin/login")
def admin_login():
    return render_template("admin/login.html")


@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/equipment")
def admin_equipment():
    return render_template("admin/equipment.html")


@app.route("/admin/equipment/add")
def add_equipment_page():
    return render_template("admin/add_equipment.html")


@app.route("/admin/equipment/edit/<int:item_id>")
def edit_equipment_page(item_id):
    return render_template(
        "admin/edit_equipment.html",
        item_id=item_id
    )


@app.route("/admin/bookings")
def admin_bookings():
    return render_template("admin/bookings.html")


@app.route("/admin/users")
def admin_users():
    return render_template("admin/users.html")


if __name__ == "__main__":
    app.run(debug=True)