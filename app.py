"""
BloodLink — Blood Donation & Emergency Finder
Backend: Python 3 + Flask + mysql-connector-python
Run locally:  python app.py
Deploy:       Render / Railway / any Python host
"""

import os
from datetime import date, datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests

# ── DB config — reads env vars on deployment, falls back to local ──
DB_CONFIG = {
    "host":     os.environ.get("MYSQLHOST",     "localhost"),
    "user":     os.environ.get("MYSQLUSER",     "root"),
    "password": os.environ.get("MYSQLPASSWORD", "mysql123"),
    "database": os.environ.get("MYSQLDATABASE", "blood_donation"),
    "port":     int(os.environ.get("MYSQLPORT", 3306)),
}


def get_db():
    """Return a new MySQL connection."""
    return mysql.connector.connect(**DB_CONFIG)


def fmt(val):
    """Format a date/datetime to YYYY-MM-DD string."""
    if val is None:
        return None
    if isinstance(val, (date, datetime)):
        return val.strftime("%Y-%m-%d")
    return str(val).split("T")[0]


def fail(msg, code=200):
    return jsonify({"status": "error", "message": msg}), code


# ══════════════════════════════════════════════════════════════
#  PAGE
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ══════════════════════════════════════════════════════════════
#  DONOR ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/add_donor", methods=["POST"])
def add_donor():
    data = request.form
    name          = (data.get("name") or "").strip()
    blood_group   = (data.get("blood_group") or "").strip()
    gender        = (data.get("gender") or "").strip()
    dob           = (data.get("dob") or "").strip()
    city          = (data.get("city") or "").strip()
    phone         = (data.get("phone") or "").strip()
    last_donation = (data.get("last_donation") or "").strip()

    if not all([name, blood_group, city, phone, last_donation]):
        return fail("All fields are required.")
    if not phone.isdigit() or len(phone) != 10:
        return fail("Phone must be exactly 10 digits.")

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Check duplicate phone
        cur.execute("SELECT donor_id FROM donors WHERE phone = %s", (phone,))
        if cur.fetchone():
            return fail("A donor with this phone number already exists.")

        cur.execute(
            """INSERT INTO donors (name, blood_group, city, phone, gender, date_of_birth, last_donation)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (name, blood_group, city, phone,
             gender or None, dob or None, last_donation or None)
        )
        conn.commit()
        return jsonify({"status": "success", "message": "✅ Donor registered successfully!"})
    except Error as e:
        return fail("Database error: " + str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass


@app.route("/search")
def search():
    blood_group = (request.args.get("blood_group") or "").strip()
    city        = (request.args.get("city") or "").strip()
    if not blood_group or not city:
        return jsonify([])

    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.callproc("find_donors", (blood_group, city))
        rows = []
        for result in cur.stored_results():
            rows = result.fetchall()
        for r in rows:
            r["last_donation"] = fmt(r.get("last_donation"))
        return jsonify(rows)
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass


@app.route("/all_donors")
def all_donors():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM donors ORDER BY donor_id DESC")
        rows = cur.fetchall()
        for r in rows:
            r["last_donation"] = fmt(r.get("last_donation"))
            r["date_of_birth"] = fmt(r.get("date_of_birth"))
        return jsonify(rows)
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass


@app.route("/delete_donor/<int:donor_id>", methods=["DELETE"])
def delete_donor(donor_id):
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM donors WHERE donor_id = %s", (donor_id,))
        conn.commit()
        return jsonify({"status": "success", "message": "Donor deleted successfully."})
    except Error as e:
        return fail("Cannot delete donor: " + str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass


# ══════════════════════════════════════════════════════════════
#  EMERGENCY ROUTES
# ══════════════════════════════════════════════════════════════

@app.route("/emergency", methods=["POST"])
def emergency():
    data         = request.form
    patient_name = (data.get("patient_name") or "").strip()
    blood_group  = (data.get("blood_group") or "").strip()
    hospital     = (data.get("hospital_name") or "").strip()
    city         = (data.get("city") or "").strip()
    phone        = (data.get("phone") or "").strip()
    units        = data.get("units_required", 1)
    urgency      = data.get("urgency", "Normal")

    if not all([patient_name, blood_group, city, phone]):
        return fail("All fields are required.")
    if not phone.isdigit() or len(phone) != 10:
        return fail("Phone must be exactly 10 digits.")

    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            """INSERT INTO requests
               (patient_name, blood_group, city, phone, hospital_name, units_required, urgency)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (patient_name, blood_group, city, phone,
             hospital or None, int(units) if units else 1, urgency)
        )
        conn.commit()
        return jsonify({
            "status": "success",
            "message": "🚨 Emergency request submitted! Donors will be contacted shortly."
        })
    except Error as e:
        return fail("Database error: " + str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass


@app.route("/all_requests")
def all_requests():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM requests ORDER BY request_id DESC")
        rows = cur.fetchall()
        for r in rows:
            r["request_date"] = fmt(r.get("request_date"))
        return jsonify(rows)
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass


# ══════════════════════════════════════════════════════════════
#  STATS
# ══════════════════════════════════════════════════════════════

@app.route("/stats")
def stats():
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        cur.execute("""
            SELECT blood_group,
                   COUNT(*) AS total,
                   SUM(availability = 'Available') AS available
            FROM donors
            GROUP BY blood_group
            ORDER BY blood_group
        """)
        by_blood_group = cur.fetchall()
        # Convert Decimal to int for JSON
        for r in by_blood_group:
            r["total"]     = int(r["total"])
            r["available"] = int(r["available"] or 0)

        cur.execute("SELECT COUNT(*) AS n FROM donors")
        total_donors = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM donors WHERE availability = 'Available'")
        available_donors = cur.fetchone()["n"]

        cur.execute("SELECT COUNT(*) AS n FROM requests")
        total_requests = cur.fetchone()["n"]

        return jsonify({
            "total_donors":     int(total_donors),
            "available_donors": int(available_donors),
            "total_requests":   int(total_requests),
            "by_blood_group":   by_blood_group,
        })
    except Error as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        try: cur.close(); conn.close()
        except: pass


# ══════════════════════════════════════════════════════════════
#  START
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)