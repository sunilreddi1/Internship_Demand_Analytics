import psycopg2
import sqlite3

def db():
    try:
        DATABASE_URL = (
            "postgresql://neondb_owner:npg_Oigm2nBb0Jqk"
            "@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432"
            "/neondb?sslmode=require"
        )
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        print("✅ CONNECTED TO NEON SUCCESSFULLY")
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("🔄 Falling back to SQLite...")
        conn = sqlite3.connect("users.db")
        print("✅ CONNECTED TO SQLITE SUCCESSFULLY")
        return conn

# Test the connection
conn = db()
conn.close()
