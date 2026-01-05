import sqlite3
import bcrypt

conn = sqlite3.connect("users.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password BLOB,
    role TEXT,
    college TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS search_logs (
    username TEXT,
    skill TEXT,
    location TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

def add_user(username, password, role, college):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    cur.execute(
        "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?)",
        (username, hashed, role, college)
    )

add_user("student", "student123", "Student", "Engineering College")
add_user("admin", "admin123", "Admin", "Placement Cell")

conn.commit()
conn.close()
print("Database created successfully")
