import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "database.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS medicines(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category_id INTEGER,
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS batches(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medicine_id INTEGER NOT NULL,
    batch_no TEXT,
    quantity INTEGER DEFAULT 0,
    expiry_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(medicine_id) REFERENCES medicines(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS expired_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id INTEGER,
    expired_on TEXT DEFAULT CURRENT_DATE,
    processed INTEGER DEFAULT 0,
    FOREIGN KEY(batch_id) REFERENCES batches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT,
    table_name TEXT,
    record_id INTEGER,
    details TEXT,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW IF NOT EXISTS medicine_overview AS
SELECT 
    m.id as medicine_id,
    m.name as medicine_name,
    c.name AS category,
    b.id AS batch_id,
    b.batch_no,
    b.quantity,
    b.expiry_date
FROM medicines m
LEFT JOIN categories c ON m.category_id = c.id
LEFT JOIN batches b ON m.id = b.medicine_id;

CREATE INDEX IF NOT EXISTS idx_medicine_name ON medicines(name);
CREATE INDEX IF NOT EXISTS idx_batch_expiry ON batches(expiry_date);

CREATE TRIGGER IF NOT EXISTS log_medicine_insert
AFTER INSERT ON medicines
BEGIN
  INSERT INTO activity_log(action, table_name, record_id, details)
  VALUES ('INSERT', 'medicines', NEW.id, NEW.name);
END;

CREATE TRIGGER IF NOT EXISTS log_medicine_update
AFTER UPDATE ON medicines
BEGIN
  INSERT INTO activity_log(action, table_name, record_id, details)
  VALUES ('UPDATE', 'medicines', NEW.id, COALESCE(NEW.name, ''));
END;

CREATE TRIGGER IF NOT EXISTS log_medicine_delete
AFTER DELETE ON medicines
BEGIN
  INSERT INTO activity_log(action, table_name, record_id, details)
  VALUES ('DELETE', 'medicines', OLD.id, OLD.name);
END;

-- Triggers for batches CRUD activity
CREATE TRIGGER IF NOT EXISTS log_batch_insert
AFTER INSERT ON batches
BEGIN
INSERT INTO activity_log(action, table_name, record_id, details)
VALUES ('INSERT', 'batches', NEW.id, COALESCE(NEW.batch_no, ''));
END;

CREATE TRIGGER IF NOT EXISTS log_batch_update
AFTER UPDATE ON batches
BEGIN
INSERT INTO activity_log(action, table_name, record_id, details)
VALUES ('UPDATE', 'batches', NEW.id, printf('qty:%s expiry:%s', COALESCE(NEW.quantity,''), COALESCE(NEW.expiry_date,'')));
END;

CREATE TRIGGER IF NOT EXISTS log_batch_delete
AFTER DELETE ON batches
BEGIN
INSERT INTO activity_log(action, table_name, record_id, details)
VALUES ('DELETE', 'batches', OLD.id, COALESCE(OLD.batch_no, ''));
END;

CREATE TRIGGER IF NOT EXISTS detect_expiry_on_insert
AFTER INSERT ON batches
WHEN DATE(NEW.expiry_date) <= DATE('now')
BEGIN
  INSERT INTO expired_items(batch_id, expired_on)
  VALUES (NEW.id, DATE('now'));
END;

CREATE TRIGGER IF NOT EXISTS detect_expiry_on_update
AFTER UPDATE ON batches
WHEN DATE(NEW.expiry_date) <= DATE('now')
BEGIN
  INSERT INTO expired_items(batch_id, expired_on)
  VALUES (NEW.id, DATE('now'));
END;
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    # Seed default categories if empty
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [
                ("Tablet",),
                ("Syrup",),
                ("Injection",),
                ("Ointment",)
            ]
        )

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at: {DB_PATH}")
