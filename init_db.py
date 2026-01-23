import psycopg2
import os

def init_db():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ Please set DATABASE_URL environment variable")
        return

    conn = psycopg2.connect(db_url, sslmode="require")
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        email TEXT UNIQUE,
        password BYTEA,
        role TEXT
    );
    """)

    # APPLICATIONS TABLE
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id SERIAL PRIMARY KEY,
        username TEXT,
        job_title TEXT,
        company TEXT,
        location TEXT,
        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized successfully")
