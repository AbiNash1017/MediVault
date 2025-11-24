from . import get_conn

def add_batch(medicine_id, batch_no, quantity, expiry_date):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO batches(medicine_id, batch_no, quantity, expiry_date) VALUES (?, ?, ?, ?)",
                (medicine_id, batch_no, quantity, expiry_date))
    conn.commit()
    bid = cur.lastrowid
    conn.close()
    return bid

def delete_batch(batch_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM batches WHERE id=?", (batch_id,))
    conn.commit()
    conn.close()

def get_batches_for_medicine(mid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM batches WHERE medicine_id=? ORDER BY expiry_date", (mid,))
    data = cur.fetchall()
    conn.close()
    return data

def soon_to_expire(days=30):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.*, m.name as med_name
        FROM batches b
        JOIN medicines m ON m.id = b.medicine_id
        WHERE DATE(b.expiry_date) BETWEEN DATE('now') AND DATE('now', ?)
        ORDER BY b.expiry_date
    """, (f"+{days} day",))
    data = cur.fetchall()
    conn.close()
    return data

def get_expired():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.*, m.name as med_name
        FROM batches b
        JOIN medicines m ON m.id = b.medicine_id
        WHERE DATE(b.expiry_date) < DATE('now')
        ORDER BY b.expiry_date
    """)
    data = cur.fetchall()
    conn.close()
    return data

def get_expiry_timeline():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT STRFTIME('%Y-%m', expiry_date) AS month, COALESCE(SUM(quantity),0) AS total
        FROM batches
        WHERE expiry_date IS NOT NULL
        GROUP BY month
        ORDER BY month
    """)
    data = cur.fetchall()
    conn.close()
    return data
