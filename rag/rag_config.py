"""
Initialize Embedding Model
Configure PGVector Database Connection
"""

import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

# ---------------------------------------------------
# Embedding Model
# ---------------------------------------------------

embeddings_model = OpenAIEmbeddings(
    model="text-embedding-3-small"
)

# ---------------------------------------------------
# PostgreSQL / PGVector Configuration
# ---------------------------------------------------

connection = os.getenv(
    "POSTGRES_DSN",
    "postgresql+psycopg://mg_user:mg_pass@localhost:5433/mentorgrowai_db"
)

collection_name = "aws_ai_practitioner_rag"

print("=" * 80)
print(f"PGVector Collection : {collection_name}")
print(f"PGVector Connection : {connection}")
print("=" * 80)