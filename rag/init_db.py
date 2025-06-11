from dotenv import load_dotenv
import os, psycopg2

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("PG_DB", "dental_rag"),
    user=os.getenv("PG_USER", "dental_user"),
    password=os.getenv("PG_PASS", "dental_pass"),
    host=os.getenv("PG_HOST", "127.0.0.1"),
    port=int(os.getenv("PG_PORT", 5432)),
)

cur = conn.cursor()

# ✅ Remove the extension creation — done manually already
# cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

cur.execute("""
CREATE TABLE IF NOT EXISTS dental_services (
    id SERIAL PRIMARY KEY,
    category TEXT,
    name TEXT,
    description TEXT,
    price TEXT,
    duration TEXT,
    insurance TEXT,
    embedding vector(1536)
);
""")

conn.commit()
cur.close()
conn.close()
print("✅ Database initialized.")
