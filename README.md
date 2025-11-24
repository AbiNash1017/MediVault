<div align="center">

# 🚀 Medi‑Vault Pro
Modern medical inventory & expiry tracking powered by **Flask + SQLite + Chart.js**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57.svg?style=for-the-badge&logo=sqlite&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black.svg?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-Frontend-E34F26.svg?style=for-the-badge&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-UI%20Design-1572B6.svg?style=for-the-badge&logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES6+-yellow.svg?style=for-the-badge&logo=javascript&logoColor=black)
![Chart.js](https://img.shields.io/badge/Chart.js-Data%20Viz-f5788d.svg?style=for-the-badge&logo=chartdotjs&logoColor=white)
</div>

Medi‑Vault Pro keeps clinics and labs ahead of expiring stock. It combines a testable Flask backend, SQLite power features (foreign keys, triggers, views, indexes), and a polished responsive UI.

---
## project Screenshot

![Image 1](https://github.com/AbiNash1017/MediVault/blob/master/screenshots/1.png)
![Image 2](https://github.com/AbiNash1017/MediVault/blob/master/screenshots/2.png)
![Image 3](https://github.com/AbiNash1017/MediVault/blob/master/screenshots/3.png)
![Image 4](https://github.com/AbiNash1017/MediVault/blob/master/screenshots/4.png)

---

## 📁 Project Layout

```
medi_vault_pro/
├── app.py              # Flask routes & controllers
├── database/setup.py   # Schema, triggers, seed data
├── models/             # DB helper modules
├── templates/          # Jinja UI
├── static/             # CSS + JS assets
├── requirements.txt
└── README.md
```

---

## ⚙️ Quick Start

```bash
python -m venv venv
venv\Scripts\activate           # Windows (or source venv/bin/activate)
pip install -r requirements.txt
python -m compileall .
python -m database.setup
python app.py                    # visit http://127.0.0.1:5000
```

`database/setup.py` auto-creates `database.db`, seeds default categories, and registers triggers on first boot.

---

## 🧠 Core Logic & Snippets

### SQLite schema + triggers (`database/setup.py`)

```sql
CREATE TABLE IF NOT EXISTS batches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_no TEXT,
    quantity INTEGER DEFAULT 0,
    expiry_date TEXT,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS detect_expiry_on_insert
AFTER INSERT ON batches
WHEN DATE(NEW.expiry_date) <= DATE('now')
BEGIN
    INSERT INTO expired_items(batch_id, expired_on)
    VALUES (NEW.id, DATE('now'));
    INSERT INTO activity_log(action, table_name, record_id, details)
    VALUES ('INSERT_EXPIRED', 'batches', NEW.id, NEW.batch_no);
END;
```

- **Foreign keys** ensure batches follow their parent medicine/category (cascade delete).
- **Triggers** keep `expired_items` & `activity_log` updated automatically.
- **Views + indexes** (`medicine_overview`, `idx_batch_expiry`, etc.) power fast dashboard queries.

### Flask controllers (`app.py`)

```python
@app.route("/")
def home():
    stats = fetch_headline_stats()
    rows = query_overview(search=request.args.get("q", ""))
    medicines = enrich_batches(rows)
    return render_template("index.html", stats=stats, medicines=medicines)

@app.route("/api/upcoming")
def api_upcoming():
    days = int(request.args.get("days", 30))
    cur.execute(
        """
        SELECT b.id, m.name, b.batch_no, b.quantity, b.expiry_date
        FROM batches b JOIN medicines m ON m.id = b.medicine_id
        WHERE DATE(b.expiry_date) BETWEEN DATE('now') AND DATE('now', ?)
        """,
        (f"+{days} day",),
    )
    return jsonify([dict(r) for r in cur.fetchall()])
```

- `/` renders stat pills, medicine cards, inline batch actions, and search results.
- `/api/upcoming` returns JSON used by the dashboard + external consumers.

### Dashboard SQL

```python
cur.execute("SELECT COUNT(*) FROM medicines")
cur.execute("SELECT c.name, COUNT(b.id) FROM categories c ... GROUP BY c.name")
cur.execute("""
    SELECT STRFTIME('%Y-%m', expiry_date) AS month,
           COALESCE(SUM(quantity),0) AS total
    FROM batches
    WHERE expiry_date IS NOT NULL
    GROUP BY month
""")
```

Lightweight aggregates power the Chart.js widgets without ORM overhead.

---

## ✨ Feature Highlights

| Area | Description |
|------|-------------|
| Inventory CRUD | Create medicines, assign categories, optional initial batch |
| Batch Control | Inline list per medicine with quantity, expiry, delete, add form |
| Expiry Intelligence | SQLite triggers populate `expired_items`; soon-to-expire logic (30 days) |
| Analytics | Stat pills, category pie, monthly expiry timeline, upcoming API |
| Activity Log | `activity_log` stores INSERT/UPDATE/DELETE + expiry actions |
| UI/UX | Responsive glass/light theme, search bar, batch badges |

---

## 🗄️ SQLite Techniques

- **Views**: `medicine_overview` denormalizes medicine/category/batch.
- **Triggers**: `log_medicine_*`, `detect_expiry_on_insert/update` maintain logs + expiry table.
- **Foreign Keys**: enforce cascades across medicines, categories, batches.
- **Indexes**: `idx_medicine_name`, `idx_batch_expiry` accelerate lookup + range queries.
- **PRAGMA foreign_keys**: enabled for every connection (`get_conn`).

---

## 🌐 Routes & APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/`                        | Inventory list with search + inline batch controls |
| GET/POST | `/add`                   | Create medicine (optional initial batch) |
| POST   | `/add_batch/<medicine_id>` | Append batch |
| GET    | `/delete_batch/<batch_id>` | Remove batch |
| GET    | `/dashboard`               | Chart.js analytics |
| GET    | `/logs`                    | Activity log view |
| GET    | `/api/upcoming?days=30`    | JSON feed of near-expiry batches |

---

## 🧰 Tech Stack

- **Backend**: Flask 2.3, Python 3.12
- **Database**: SQLite (views, triggers, indexes, FK constraints)
- **Templating**: Jinja2 + responsive CSS/JS
- **Charts**: Chart.js

---

## 🤝 Contributing

1. Fork the repo & create a feature branch.
2. Modify schema/UI/logic as needed.
3. Run `python app.py` and exercise the flows.
4. Submit a PR with screenshots/notes.

Enjoy building with Medi‑Vault Pro! ✨