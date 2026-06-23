
```bash

docker compose up -d

# Exploration of pgvector-container
## connect to db
docker exec -it pgvector-container psql -U aws_user -d aws_rag_db
## You only need to do this once per database.
CREATE EXTENSION IF NOT EXISTS pgcrypto;
## verify extension
\dx

aws_rag_db=# \dx
                              List of installed extensions
   Name   | Version |   Schema   |                     Description                      
----------+---------+------------+------------------------------------------------------
 pgcrypto | 1.3     | public     | cryptographic functions
 plpgsql  | 1.0     | pg_catalog | PL/pgSQL procedural language
 vector   | 0.8.2   | public     | vector data type and ivfflat and hnsw access methods
 
 ## create table
 CREATE TABLE question_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    question_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
 
 
 CREATE TABLE questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID REFERENCES question_sets(set_id),
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answers JSONB NOT NULL,
    type VARCHAR(30) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
  
  
 ## check for tables

 ## Insert data from code 
 
 ## view  row counts;
SELECT count(*) FROM questions;

##  add more tables for user session management and exam progress tracking

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE exam_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id),
    exam_type VARCHAR(50),
    total_questions INT,
    score FLOAT,
    readiness_score FLOAT,
    domain_scores JSONB,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP
);

CREATE TABLE exam_question_answers (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES exam_sessions(session_id),
    question_id UUID REFERENCES questions(question_id),
    user_answer JSONB,
    is_correct BOOLEAN,
    answered_at TIMESTAMP
);

CREATE TABLE weak_concepts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    concept VARCHAR(255),
    domain VARCHAR(50),
    occurrence_count INT DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);



------------ for mock test tracking---------
CREATE TABLE mock_test_attempts (
    attempt_id SERIAL PRIMARY KEY,
                                  
    user_id VARCHAR(255) NOT NULL,
                                  
    session_id VARCHAR(255) NOT NULL,
                                     
    exam_name VARCHAR(255),
                           
    total_questions INTEGER,
                            
    correct_answers INTEGER,
                            
    wrong_answers INTEGER,
                          
    percentage NUMERIC(5,2),
                            
    duration_seconds INTEGER,
                             
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE mock_test_question_results (

    id SERIAL PRIMARY KEY,

    attempt_id INTEGER
        REFERENCES mock_test_attempts(attempt_id),

    user_id VARCHAR(255),

    question_id INTEGER,

    domain VARCHAR(100),

    question_text TEXT,

    question_type VARCHAR(50),

    selected_answers JSONB,

    correct_answers JSONB,

    is_correct BOOLEAN,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```


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