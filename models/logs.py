from . import get_conn

def get_logs(limit=200):
    conn = get_conn()
    cur = conn.cursor()
    if limit is None:
        cur.execute("SELECT * FROM activity_log ORDER BY timestamp DESC")
    else:
        cur.execute("SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?", (limit,))
    data = cur.fetchall()
    conn.close()
    return data

def get_logs_by_table(table):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_log WHERE table_name=? ORDER BY timestamp DESC", (table,))
    data = cur.fetchall()
    conn.close()
    return data

def get_logs_by_action(action):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activity_log WHERE action=? ORDER BY timestamp DESC", (action,))
    data = cur.fetchall()
    conn.close()
    return data
