from flask import Flask, render_template, request, redirect 
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS trips(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        trip_date TEXT,
        pickup TEXT,
        drop_location TEXT,
        km INTEGER,
        fare INTEGER,
        fuel INTEGER
    )
    """)

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(fare) FROM trips")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MAX(fare) FROM trips")
    highest_fare = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(km) FROM trips")
    total_km = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(fuel) FROM trips")
    total_fuel = cursor.fetchone()[0] or 0

    profit = total_income - total_fuel

    cursor.execute("SELECT * FROM trips ORDER BY id DESC LIMIT 5")
    recent_trips = cursor.fetchall()

    average_fare=total_income/total_trips if total_trips > 0 else 0


    conn.close()

    return render_template("dashboard.html", total_trips=total_trips,total_income=total_income,total_km=total_km,profit=profit,total_fuel=total_fuel,average_fare=average_fare,recent_trips=recent_trips,highest_fare=highest_fare)

@app.route("/add_trip", methods=["GET", "POST"])
def add_trip():

    if request.method == "POST":
        trip_date = request.form["trip_date"]
        pickup = request.form["pickup"]
        drop = request.form["drop"]
        km = request.form["km"]
        fare = request.form["fare"]
        fuel = request.form["fuel"]

        conn = sqlite3.connect("trips.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO trips (trip_date, pickup, drop_location, km, fare, fuel) VALUES (?, ?, ?, ?, ?, ?)",
            (trip_date, pickup, drop, km, fare, fuel)
        )

        conn.commit()
        conn.close()

    return render_template("add_trip.html")

@app.route("/history")
def history():

    search = request.args.get("search", "")

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    if search:
        cursor.execute(
            "SELECT * FROM trips WHERE pickup LIKE ?",
            ('%' + search + '%',)
        )
    else:
        cursor.execute("SELECT * FROM trips")

    trips = cursor.fetchall()

    conn.close()

    return render_template("trip_history.html", trips=trips)
    
@app.route("/reports")
def reports():

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    # Overall Report
    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(fare) FROM trips")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(km) FROM trips")
    total_km = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(fuel) FROM trips")
    total_fuel = cursor.fetchone()[0] or 0

    profit = total_income - total_fuel


    # Weekly Income Report (Last 7 days)
    cursor.execute("""
        SELECT 
        COUNT(*),
        SUM(fare),
        SUM(fuel),
        SUM(km)
        FROM trips
        WHERE trip_date >= date('now','-7 day')
    """)

    weekly = cursor.fetchone()

    weekly_trips = weekly[0] or 0
    weekly_income = weekly[1] or 0
    weekly_fuel = weekly[2] or 0
    weekly_km = weekly[3] or 0
    weekly_profit = weekly_income - weekly_fuel


    # Monthly Income Report
    cursor.execute("""
        SELECT 
        COUNT(*),
        SUM(fare),
        SUM(fuel),
        SUM(km)
        FROM trips
        WHERE strftime('%Y-%m', trip_date) = strftime('%Y-%m','now')
    """)

    monthly = cursor.fetchone()

    monthly_trips = monthly[0] or 0
    monthly_income = monthly[1] or 0
    monthly_fuel = monthly[2] or 0
    monthly_km = monthly[3] or 0
    monthly_profit = monthly_income - monthly_fuel


    cursor.execute("SELECT * FROM trips ORDER BY trip_date DESC")
    trips = cursor.fetchall()

    conn.close()


    return render_template(
        "reports.html",

        total_trips=total_trips,
        total_income=total_income,
        total_km=total_km,
        total_fuel=total_fuel,
        profit=profit,

        weekly_trips=weekly_trips,
        weekly_income=weekly_income,
        weekly_fuel=weekly_fuel,
        weekly_km=weekly_km,
        weekly_profit=weekly_profit,

        monthly_trips=monthly_trips,
        monthly_income=monthly_income,
        monthly_fuel=monthly_fuel,
        monthly_km=monthly_km,
        monthly_profit=monthly_profit,

        trips=trips
    )

@app.route("/download_report")
def download_report():

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM trips")
    total_trips = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(fare) FROM trips")
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(fuel) FROM trips")
    total_fuel = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(km) FROM trips")
    total_km = cursor.fetchone()[0] or 0

    profit = total_income - total_fuel

    conn.close()

    doc = SimpleDocTemplate("Driver_Report.pdf")
    styles = getSampleStyleSheet()

    story = [
        Paragraph("<b>DinoSingh Log Report</b>", styles["Heading1"]),
        Paragraph(f"Total Trips : {total_trips}", styles["Normal"]),
        Paragraph(f"Total Income : ₹{total_income}", styles["Normal"]),
        Paragraph(f"Total Fuel : ₹{total_fuel}", styles["Normal"]),
        Paragraph(f"Total KM : {total_km}", styles["Normal"]),
        Paragraph(f"Profit : ₹{profit}", styles["Normal"]),
    ]

    doc.build(story)

    return "✅ PDF created successfully! Check your project folder."

@app.route("/delete/<int:id>")
def delete_trip(id):

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM trips WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/history")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_trip(id):

    conn = sqlite3.connect("trips.db")
    cursor = conn.cursor()

    if request.method == "POST":

        pickup = request.form["pickup"]
        drop = request.form["drop"]
        km = request.form["km"]
        fare = request.form["fare"]
        fuel = request.form["fuel"]

        cursor.execute(
            "UPDATE trips SET pickup=?, drop_location=?, km=?, fare=?, fuel=? WHERE id=?",
            (pickup, drop, km, fare, fuel, id)
        )

        conn.commit()
        conn.close()

        return redirect("/history")

    cursor.execute("SELECT * FROM trips WHERE id=?", (id,))
    trip = cursor.fetchone()

    conn.close()

    return render_template("edit_trip.html", trip=trip)

if __name__ == "__main__":
    app.run(debug=True)