from . import get_conn

def create_medicine(name, category_id=None, description=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO medicines(name, category_id, description) VALUES (?, ?, ?)",
                (name, category_id, description))
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return mid

def get_all_medicines():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT m.*, c.name AS category_name
        FROM medicines m
        LEFT JOIN categories c ON m.category_id = c.id
        ORDER BY m.name COLLATE NOCASE
    """)
    data = cur.fetchall()
    conn.close()
    return data

def get_medicine(mid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medicines WHERE id=?", (mid,))
    data = cur.fetchone()
    conn.close()
    return data

def update_medicine(mid, name=None, category_id=None, description=None):
    conn = get_conn()
    cur = conn.cursor()
    fields = []
    vals = []
    if name is not None:
        fields.append("name=?"); vals.append(name)
    if category_id is not None:
        fields.append("category_id=?"); vals.append(category_id)
    if description is not None:
        fields.append("description=?"); vals.append(description)
    if not fields:
        conn.close(); return
    vals.append(mid)
    cur.execute(f"UPDATE medicines SET {', '.join(fields)} WHERE id=?", vals)
    conn.commit()
    conn.close()

def delete_medicine(mid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM medicines WHERE id=?", (mid,))
    conn.commit()
    conn.close()
