import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

from config import Config
from models import db, Equipment, User, BookingRecord 
from booking_routes import booking_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # make sure the instance folder exists (holds the SQLite file)
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)

    db.init_app(app)
    app.register_blueprint(booking_bp)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app):

    @app.route("/")
    def home():
        return redirect(url_for("list_equipment"))

    # ---------- EQUIPMENT: your (Person 1) core routes ----------

    @app.route("/equipment")
    def list_equipment():
        items = Equipment.query.order_by(Equipment.name).all()
        return render_template("equipment_list.html", items=items)

    @app.route("/equipment/add", methods=["GET", "POST"])
    def add_equipment():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "General").strip()
            quantity = int(request.form.get("quantity", 1))

            if not name or quantity < 1:
                flash("Please enter a valid name and quantity.", "danger")
                return redirect(url_for("add_equipment"))

            item = Equipment(
                name=name,
                category=category,
                total_quantity=quantity,
                available_quantity=quantity,
                status="Available",
            )
            db.session.add(item)
            db.session.commit()
            flash(f"{name} added to inventory.", "success")
            return redirect(url_for("list_equipment"))

        return render_template("add_equipment.html")

    @app.route("/equipment/<int:item_id>/edit", methods=["GET", "POST"])
    def edit_equipment(item_id):
        item = Equipment.query.get_or_404(item_id)

        if request.method == "POST":
            item.name = request.form.get("name", item.name).strip()
            item.category = request.form.get("category", item.category).strip()
            item.status = request.form.get("status", item.status)
            new_total = int(request.form.get("quantity", item.total_quantity))

            # keep available_quantity consistent when total changes
            diff = new_total - item.total_quantity
            item.total_quantity = new_total
            item.available_quantity = max(0, item.available_quantity + diff)

            db.session.commit()
            flash(f"{item.name} updated.", "success")
            return redirect(url_for("list_equipment"))

        return render_template("edit_equipment.html", item=item)

    @app.route("/equipment/<int:item_id>/delete", methods=["POST"])
    def delete_equipment(item_id):
        item = Equipment.query.get_or_404(item_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"{item.name} removed.", "info")
        return redirect(url_for("list_equipment"))

    # ---------- Small JSON API so the booking side (Person 2) can use it ----------

    @app.route("/api/equipment", methods=["GET"])
    def api_list_equipment():
        items = Equipment.query.all()
        return jsonify([i.to_dict() for i in items])

    @app.route("/api/equipment/<int:item_id>/availability", methods=["GET"])
    def api_check_availability(item_id):
        item = Equipment.query.get_or_404(item_id)
        return jsonify({"available_quantity": item.available_quantity, "status": item.status})


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
