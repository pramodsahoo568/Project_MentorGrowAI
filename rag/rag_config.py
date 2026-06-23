'''
initialize  Embedding
config pgvector db configuration
'''

from langchain_openai import OpenAIEmbeddings

from dotenv import load_dotenv
load_dotenv()

embeddings_model = OpenAIEmbeddings(model="text-embedding-3-small")

connection = "postgresql+psycopg://aws_user:aws_pass@localhost:5432/aws_rag_db"  # Uses psycopg3!
collection_name = "aws_ai_practitioner_rag"