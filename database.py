import sqlite3

conn = sqlite3.connect(
    "fitness.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT,
    messages INTEGER,
    streak INTEGER,
    completed_today INTEGER,
    weight REAL,
    water INTEGER
)
""")

conn.commit()

def create_user(user_id, name):

    cursor.execute("""
    INSERT OR IGNORE INTO users
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        name,
        0,
        0,
        0,
        0,
        0
    ))

    conn.commit()

def get_user(user_id):

    cursor.execute("""
    SELECT * FROM users
    WHERE user_id = ?
    """, (user_id,))

    return cursor.fetchone()