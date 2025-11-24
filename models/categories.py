from . import get_conn

def get_all_categories():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    data = cur.fetchall()
    conn.close()
    return data

def create_category(name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO categories(name) VALUES(?)", (name,))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return cid

def delete_category(cat_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()

def update_category(cat_id, new_name):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE categories SET name=? WHERE id=?", (new_name, cat_id))
    conn.commit()
    conn.close()
