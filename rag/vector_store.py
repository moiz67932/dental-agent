# import os, psycopg2, json
# from dotenv import load_dotenv
# from openai import OpenAI

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# def embed(text: str):
#     """Return a 1536-dim vector as Python list (new OpenAI SDK)."""
#     resp = client.embeddings.create(
#         model="text-embedding-3-small",
#         input=[text.replace("\n", " ")]
#     )
#     return resp.data[0].embedding          # list[float]

# def search(query: str, k: int = 3):
#     vec = embed(query)

#     # ---- convert list → pgvector literal "[v1,v2,…]"
#     vec_literal = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

#     conn = psycopg2.connect(
#         dbname=os.getenv("PG_DB"),
#         user=os.getenv("PG_USER"),
#         password=os.getenv("PG_PASS"),
#         host=os.getenv("PG_HOST"),
#         port=os.getenv("PG_PORT"),
#     )
#     cur = conn.cursor()
#     cur.execute(
#         """
#         SELECT name, description, price
#         FROM dental_services
#         ORDER BY embedding <-> %s::vector
#         LIMIT %s
#         """,
#         (vec_literal, k)
#     )
#     rows = cur.fetchall()
#     cur.close(); conn.close()
#     return rows


# if __name__ == "__main__":
#     for r in search("How much is whitening?"):
#         print(r)



"""
vector_store.py – embedding search helper
(adds Duration column to results)
"""
import os, psycopg2
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def embed(text: str):
    """Return a 1536-dim OpenAI embedding as list[float]."""
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=[text.replace("\n", " ")]
    )
    return resp.data[0].embedding

def search(query: str, k: int = 3):
    """
    Return up to *k* rows sorted by cosine distance to the query.
    Fields: name, description, price, duration
    """
    vec = embed(query)
    vec_literal = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"

    conn = psycopg2.connect(
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASS"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT"),
    )
    cur = conn.cursor()
    cur.execute(
        """
        SELECT name, description, price, duration
        FROM dental_services
        ORDER BY embedding <-> %s::vector
        LIMIT %s
        """,
        (vec_literal, k),
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows
