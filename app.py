from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from database.setup import init_db, DB_PATH
import sqlite3
from datetime import datetime, timedelta

# --------------------------------------------------------
# Initialize DB on app start
# --------------------------------------------------------
init_db()

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --------------------------------------------------------
# DB Connection Helper
# --------------------------------------------------------

@app.context_processor
def inject_now():
    return {"now": datetime.utcnow}

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# --------------------------------------------------------
# HOME PAGE – LIST MEDICINES + BATCHES
# --------------------------------------------------------
@app.route("/")
def home():
    search_query = request.args.get("q", "").strip()

    conn = get_conn()
    cur = conn.cursor()

    # headline stats
    cur.execute("SELECT COUNT(*) FROM medicines")
    total_medicines = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM batches")
    total_batches = cur.fetchone()[0]
    cur.execute(
        """
        SELECT COUNT(*) FROM batches
        WHERE expiry_date IS NOT NULL
          AND DATE(expiry_date) BETWEEN DATE('now') AND DATE('now', '+30 day')
        """
    )
    upcoming_expiries = cur.fetchone()[0]
    cur.execute(
        """
        SELECT COUNT(*) FROM batches
        WHERE expiry_date IS NOT NULL AND DATE(expiry_date) < DATE('now')
        """
    )
    expired_batches = cur.fetchone()[0]

    # overview query with optional search
    base_query = "SELECT * FROM medicine_overview"
    params = []
    if search_query:
        base_query += " WHERE medicine_name LIKE ? OR IFNULL(batch_no, '') LIKE ?"
        like = f"%{search_query}%"
        params = [like, like]
    base_query += " ORDER BY medicine_name COLLATE NOCASE"
    cur.execute(base_query, params)
    rows = cur.fetchall()

    today = datetime.utcnow().date()
    soon_threshold = today + timedelta(days=30)

    medicines = {}
    for r in rows:
        mid = r["medicine_id"]

        if mid not in medicines:
            medicines[mid] = {
                "id": mid,
                "name": r["medicine_name"],
                "category": r["category"],
                "batches": [],
                "total_qty": 0,
                "next_expiry": None,
            }

        if r["batch_id"]:
            qty = int(r["quantity"] or 0)
            expiry_text = r["expiry_date"]
            expiry_obj = None
            expiry_display = expiry_text or "No expiry"
            status = "no-date"
            status_label = "No expiry"

            if expiry_text:
                try:
                    expiry_obj = datetime.strptime(expiry_text, "%Y-%m-%d").date()
                    expiry_display = expiry_obj.strftime("%d %b %Y")
                except ValueError:
                    expiry_obj = None
                    expiry_display = expiry_text

            if expiry_obj:
                if expiry_obj < today:
                    status = "expired"
                    status_label = "Expired"
                elif expiry_obj <= soon_threshold:
                    status = "soon"
                    status_label = "Expiring soon"
                else:
                    status = "healthy"
                    status_label = "Fresh"

                current_next = medicines[mid]["next_expiry"]
                if not current_next or expiry_obj < current_next:
                    medicines[mid]["next_expiry"] = expiry_obj

            medicines[mid]["batches"].append(
                {
                    "batch_id": r["batch_id"],
                    "batch_no": r["batch_no"],
                    "qty": qty,
                    "expiry": expiry_text,
                    "expiry_display": expiry_display,
                    "status": status,
                    "status_label": status_label,
                }
            )
            medicines[mid]["total_qty"] += qty

    # format next expiry for template consumption
    med_cards = []
    for med in medicines.values():
        next_expiry = med["next_expiry"]
        med["next_expiry_display"] = (
            next_expiry.strftime("%d %b %Y") if next_expiry else "—"
        )
        med_cards.append(med)

    conn.close()

    stats = {
        "total_medicines": total_medicines,
        "total_batches": total_batches,
        "upcoming_expiries": upcoming_expiries,
        "expired_batches": expired_batches,
    }

    return render_template(
        "index.html",
        medicines=med_cards,
        stats=stats,
        search_query=search_query,
    )

# --------------------------------------------------------
# ADD MEDICINE PAGE (GET + POST)
# --------------------------------------------------------
@app.route("/add", methods=["GET", "POST"])
def add_medicine():
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        name = request.form["name"].strip()
        category = request.form.get("category") or None
        description = request.form.get("description") or ""

        # Insert medicine
        cur.execute(
            "INSERT INTO medicines (name, category_id, description) VALUES (?, ?, ?)",
            (name, category, description)
        )
        mid = cur.lastrowid

        # Optional initial batch
        batch_no = request.form.get("batch_no")
        qty = request.form.get("quantity") or 0
        expiry = request.form.get("expiry") or None

        if batch_no or qty or expiry:
            cur.execute("""
                INSERT INTO batches (medicine_id, batch_no, quantity, expiry_date)
                VALUES (?, ?, ?, ?)
            """, (mid, batch_no, qty, expiry))

        conn.commit()
        conn.close()

        flash("Medicine added successfully!", "success")
        return redirect(url_for("home"))

    # GET request → load categories
    cur.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cur.fetchall()
    conn.close()

    return render_template("add_medicine.html", categories=categories)

# --------------------------------------------------------
# ADD BATCH TO EXISTING MEDICINE
# --------------------------------------------------------
@app.route("/add_batch/<int:medicine_id>", methods=["POST"])
def add_batch(medicine_id):
    batch_no = request.form.get("batch_no")
    quantity = request.form.get("quantity") or 0
    expiry = request.form.get("expiry") or None

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO batches (medicine_id, batch_no, quantity, expiry_date)
        VALUES (?, ?, ?, ?)
    """, (medicine_id, batch_no, quantity, expiry))

    conn.commit()
    conn.close()

    flash("Batch added.", "success")
    return redirect(url_for("home"))

# --------------------------------------------------------
# DELETE BATCH
# --------------------------------------------------------
@app.route("/delete_batch/<int:batch_id>")
def delete_batch(batch_id):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM batches WHERE id=?", (batch_id,))
    conn.commit()
    conn.close()

    flash("Batch deleted.", "warning")
    return redirect(url_for("home"))

# --------------------------------------------------------
# EDIT BATCH
# --------------------------------------------------------
@app.route("/edit_batch/<int:batch_id>", methods=["GET", "POST"])
def edit_batch(batch_id):
    conn = get_conn()
    cur = conn.cursor()

    if request.method == "POST":
        batch_no = request.form.get("batch_no") or None
        quantity = int(request.form.get("quantity") or 0)
        expiry = request.form.get("expiry") or None

        cur.execute(
            "UPDATE batches SET batch_no=?, quantity=?, expiry_date=? WHERE id=?",
            (batch_no, quantity, expiry, batch_id),
        )
        conn.commit()
        conn.close()
        flash("Batch updated", "success")
        return redirect(url_for("home"))

    cur.execute(
        """
        SELECT b.id, b.batch_no, b.quantity, b.expiry_date, m.name AS medicine_name
        FROM batches b JOIN medicines m ON m.id = b.medicine_id
        WHERE b.id = ?
        """,
        (batch_id,),
    )
    batch = cur.fetchone()
    conn.close()

    if not batch:
        flash("Batch not found", "danger")
        return redirect(url_for("home"))

    return render_template("edit_batch.html", batch=batch)

# --------------------------------------------------------
# DASHBOARD ANALYTICS
# --------------------------------------------------------
@app.route("/dashboard")
def dashboard():
    conn = get_conn()
    cur = conn.cursor()

    # Totals
    cur.execute("SELECT COUNT(*) FROM medicines")
    total_medicines = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM batches")
    total_batches = cur.fetchone()[0]

    # Expiring soon (30 days)
    cur.execute("""
        SELECT COUNT(*) FROM batches
        WHERE DATE(expiry_date) BETWEEN DATE('now') AND DATE('now', '+30 day')
    """)
    soon_expire = cur.fetchone()[0]

    # Expired count
    cur.execute("SELECT COUNT(*) FROM expired_items")
    expired_count = cur.fetchone()[0]

    # Category distribution
    cur.execute("""
        SELECT c.name AS label, COUNT(b.id) AS count
        FROM categories c
        LEFT JOIN medicines m ON m.category_id = c.id
        LEFT JOIN batches b ON b.medicine_id = m.id
        GROUP BY label
    """)
    category_rows = cur.fetchall()
    category_labels = [row["label"] or "Uncategorized" for row in category_rows]
    category_counts = [row["count"] for row in category_rows]

    # Expiry timeline (per month)
    cur.execute("""
        SELECT STRFTIME('%Y-%m', expiry_date) AS month, COALESCE(SUM(quantity), 0) AS total
        FROM batches
        WHERE expiry_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """)
    timeline_rows = cur.fetchall()
    time_labels = [row["month"] for row in timeline_rows]
    time_totals = [row["total"] for row in timeline_rows]

    conn.close()

    return render_template(
        "dashboard.html",
        total_medicines=total_medicines,
        total_batches=total_batches,
        soon_expire=soon_expire,
        expired_count=expired_count,
        category_labels=category_labels,
        category_counts=category_counts,
        time_labels=time_labels,
        time_totals=time_totals
    )

# --------------------------------------------------------
# ACTIVITY LOGS PAGE
# --------------------------------------------------------
@app.route("/logs")
def logs():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT 200")
    log_rows = cur.fetchall()

    conn.close()
    return render_template("logs.html", logs=log_rows)

# --------------------------------------------------------
# JSON API - UPCOMING EXPIRY
# --------------------------------------------------------
@app.route("/api/upcoming")
def api_upcoming():
    days = int(request.args.get("days", 30))

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT b.id, m.name AS medicine_name, b.batch_no, b.quantity, b.expiry_date
        FROM batches b
        JOIN medicines m ON m.id = b.medicine_id
        WHERE DATE(b.expiry_date) BETWEEN DATE('now')
        AND DATE('now', ?)
    """, (f"+{days} day",))

    data = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify(data)

# --------------------------------------------------------
# START FLASK SERVER
# --------------------------------------------------------
if __name__ == "__main__":
    print("🔥 Medi-Vault Pro is starting...")
    print(f"📁 Using Database: {DB_PATH}")
    app.run(debug=True)
