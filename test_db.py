import psycopg2
import sqlite3
from sqlalchemy import create_engine, text

def db():
    try:
        DATABASE_URL = "postgresql://neondb_owner:npg_Oigm2nBb0Jqk@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432/neondb?sslmode=require"
        engine = create_engine(DATABASE_URL)
        # Test the connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ CONNECTED TO NEON SUCCESSFULLY")
        return engine
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("🔄 Falling back to SQLite...")
        engine = create_engine("sqlite:///users.db")
        print("✅ CONNECTED TO SQLITE SUCCESSFULLY")
        return engine

# Test the connection
engine = db()
# Test a simple query
with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print("✅ Query executed successfully")
