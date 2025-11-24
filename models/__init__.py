from pathlib import Path
import sqlite3
from database.setup import DB_PATH

DB = DB_PATH

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
