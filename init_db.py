import sqlite3

conn = sqlite3.connect("users.db")
cur = conn.cursor()

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

# APPLICATIONS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    job_id TEXT,
    status TEXT
)
""")

# SEARCH LOGS TABLE (ADMIN ANALYTICS)
cur.execute("""
CREATE TABLE IF NOT EXISTS search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    skill TEXT,
    location TEXT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ Database initialized successfully")
