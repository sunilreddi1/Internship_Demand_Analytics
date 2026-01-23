import psycopg2

DATABASE_URL = (
    "postgresql://neondb_owner:npg_Oigm2nBb0Jqk"
    "@ep-orange-band-ah7k9fu3-pooler.c-3.us-east-1.aws.neon.tech:5432"
    "/neondb?sslmode=require"
)

conn = psycopg2.connect(DATABASE_URL)
print("✅ CONNECTED TO NEON SUCCESSFULLY")
conn.close()
