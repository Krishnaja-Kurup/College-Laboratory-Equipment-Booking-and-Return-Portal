from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)


@app.route("/")
def home():
    return redirect(url_for("student_login"))


@app.route("/student/login")
def student_login():
    return render_template("student_login.html")


@app.route("/student/dashboard")
def student_dashboard():
    return render_template("student_dashboard.html")


if __name__ == "__main__":
    app.run(debug=True)