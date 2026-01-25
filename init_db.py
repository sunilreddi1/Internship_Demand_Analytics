import psycopg2
import sqlite3
import os
from sqlalchemy import create_engine, text

def init_db():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                # USERS TABLE
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT UNIQUE,
                    password BYTEA,
                    role TEXT
                );
                """))

                # APPLICATIONS TABLE
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    job_title TEXT,
                    company TEXT,
                    location TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """))

                # SEARCH_HISTORY TABLE
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    skill TEXT,
                    city TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """))

                # RECOMMENDATION_HISTORY TABLE
                conn.execute(text("""
                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id SERIAL PRIMARY KEY,
                    username TEXT,
                    pref_location TEXT,
                    pref_domain TEXT,
                    min_stipend INTEGER,
                    remote_pref BOOLEAN,
                    experience_level TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """))

                conn.commit()
            print("✅ PostgreSQL database initialized successfully")
            return
        except Exception as e:
            print(f"❌ PostgreSQL connection failed: {e}")
            print("🔄 Falling back to SQLite...")

    # SQLite fallback
    engine = create_engine("sqlite:///users.db")
    with engine.connect() as conn:
        # USERS TABLE
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            email TEXT UNIQUE,
            password BLOB,
            role TEXT
        );
        """))

        # APPLICATIONS TABLE
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            job_title TEXT,
            company TEXT,
            location TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        # SEARCH_HISTORY TABLE
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            skill TEXT,
            city TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        # RECOMMENDATION_HISTORY TABLE
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS recommendation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            pref_location TEXT,
            pref_domain TEXT,
            min_stipend INTEGER,
            remote_pref BOOLEAN,
            experience_level TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        conn.commit()
    print("✅ SQLite database initialized successfully")

if __name__ == "__main__":
    init_db()
