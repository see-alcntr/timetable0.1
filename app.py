from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from reportlab.pdfgen import canvas
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secretkey123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS schedules (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        subject TEXT,
        day TEXT,
        time TEXT,
        color TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- AUTH ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[3]
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users(username,password,role) VALUES (?,?,?)",
                  (request.form["username"], request.form["password"], "student"))
        conn.commit()
        conn.close()
        return redirect("/")

    return render_template("register.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM schedules WHERE user_id=?", (session["user_id"],))
    data = c.fetchall()
    conn.close()

    return render_template("dashboard.html", data=data)


# ---------------- ADD ----------------
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("""
        INSERT INTO schedules(user_id,subject,day,time,color)
        VALUES (?,?,?,?,?)
        """, (
            session["user_id"],
            request.form["subject"],
            request.form["day"],
            request.form["time"],
            request.form["color"]
        ))
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add.html")


# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM schedules WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/dashboard")


# ---------------- CALENDAR ----------------
@app.route("/calendar")
def calendar():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT subject, day, time, color FROM schedules WHERE user_id=?", (session["user_id"],))
    data = c.fetchall()
    conn.close()

    events = [
        {
            "title": d[0],
            "start": f"{d[1]}T{d[2]}",
            "color": d[3]
        } for d in data
    ]

    return render_template("calendar.html", events=events)


# ---------------- PDF EXPORT ----------------
@app.route("/export_pdf")
def export_pdf():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT subject, day, time FROM schedules WHERE user_id=?", (session["user_id"],))
    data = c.fetchall()
    conn.close()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)

    pdf.setFont("Helvetica", 12)
    pdf.drawString(200, 800, "Student Timetable")

    y = 750
    for row in data:
        pdf.drawString(100, y, f"{row[0]} - {row[1]} - {row[2]}")
        y -= 20

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="timetable.pdf")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
