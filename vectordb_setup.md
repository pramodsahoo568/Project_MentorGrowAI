
```bash

docker compose up -d

# Exploration of pgvector-container
## connect to db (login)
docker exec -it pgvector-container psql -U aws_user -d aws_rag_db
## add vector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
## verify extension
\dx

output:
---------
---------+---------+------------+------------------------------------------------------
 plpgsql | 1.0     | pg_catalog | PL/pgSQL procedural language
 vector  | 0.8.2   | public     | vector data type and ivfflat and hnsw access methods
 -----------------------------------------------------------------
 ## check for tables
 \dt
 ----output---
 Did not find any relations.
 --------
 ## run the code to store documents into db , vectorstore = PGVector.from_documents()
 ## this will create following tables langchain_pg_embedding, langchain_pg_collection
 
 ## view collections;
 SELECT * FROM langchain_pg_collection;
 
\pset pager off
## The tables langchain_pg_embedding , langchain_pg_collection are automatically created by lanhchain
## get count of vectors
SELECT COUNT(*) FROM langchain_pg_embedding;



#get  size of vectors ( same as embedding sizeof OpenAI in this case-1536)
SELECT vector_dims(embedding)
FROM langchain_pg_embedding
LIMIT 5;

#View Stored Embeddings (Basic)
SELECT id, collection_id FROM langchain_pg_embedding LIMIT 5;

# View Stored text +metadata
SELECT id, left(document, 120) AS preview, cmetadata FROM langchain_pg_embedding LIMIT 5;

#View Actual Embedding Vector
SELECT embedding FROM langchain_pg_embedding LIMIT 1;
```

## to check the columns in langchain_pg_embedding
\d langchain_pg_embedding

## \d langchain_pg_embedding\d langchain_pg_embedding
## View only column names
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'langchain_pg_embedding';


---

## Useful psql commands (inside container)

```sql
-- List databases
\l

-- Use rag_production
\c rag_production

-- List extensions
\dx

-- List tables
\dt

-- List LangChain tables
\dt langchain*

-- Row count
SELECT COUNT(*) FROM langchain_pg_embedding;

-- Sample metadata (JSONB)
SELECT cmetadata->>'source_file', cmetadata->>'department' FROM langchain_pg_embedding LIMIT 3;

-- Quit
\q

docker compose down -v
## delete contaner
docker rm -f pgvector-container
```

---