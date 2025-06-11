import csv, os, psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed(text):
    response = client.embeddings.create(
        input=[text],
        model="text-embedding-3-small"
    )
    return response.data[0].embedding

conn = psycopg2.connect(
    dbname=os.getenv("PG_DB"), user=os.getenv("PG_USER"),
    password=os.getenv("PG_PASS"), host=os.getenv("PG_HOST"),
    port=os.getenv("PG_PORT"),
)
cur = conn.cursor()

with open("rag/dental_services.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        text = (
            f"{row['Name']}. {row['Description']} "
            f"{row['PriceDetails']} {row['Duration']} {row['InsuranceNotes']}"
        )
        cur.execute(
            """
            INSERT INTO dental_services
              (category,name,description,price,duration,insurance,embedding)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                row["Category"], row["Name"], row["Description"],
                row["PriceDetails"], row["Duration"], row["InsuranceNotes"],
                embed(text),
            ),
        )

conn.commit()
cur.close(); conn.close()
print("✅ Embeddings stored")
