-- =========================================================
-- MentorGrowAI DB Schema Setup
-- Database    : mentorgrowai_db
-- DB User     : mg_user
-- Container   : mentorgrowai-pgvector-container
-- Purpose     : Recreate MentorGrowAI tables in a new pgvector DB
-- =========================================================

-- Required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- 1. Question Set Master
-- =========================================================
CREATE TABLE IF NOT EXISTS question_sets (
    set_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain VARCHAR(50) NOT NULL,
    question_count INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 2. Questions
-- =========================================================
CREATE TABLE IF NOT EXISTS questions (
    question_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID REFERENCES question_sets(set_id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    options JSONB NOT NULL,
    correct_answers JSONB NOT NULL,
    type VARCHAR(30) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 3. Users
-- =========================================================
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 4. Exam Sessions
-- =========================================================
CREATE TABLE IF NOT EXISTS exam_sessions (
    session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    exam_type VARCHAR(50),
    total_questions INT,
    score FLOAT,
    readiness_score FLOAT,
    domain_scores JSONB,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP
);

-- =========================================================
-- 5. Exam Question Answers
-- =========================================================
CREATE TABLE IF NOT EXISTS exam_question_answers (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES exam_sessions(session_id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(question_id) ON DELETE SET NULL,
    user_answer JSONB,
    is_correct BOOLEAN,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 6. Weak Concepts
-- =========================================================
CREATE TABLE IF NOT EXISTS weak_concepts (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
    concept VARCHAR(255),
    domain VARCHAR(50),
    occurrence_count INT DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 7. Mock Test Attempts
-- Note: user_id/session_id are VARCHAR because your existing code
-- appears to use app/session string IDs for mock test flow.
-- =========================================================
CREATE TABLE IF NOT EXISTS mock_test_attempts (
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

-- =========================================================
-- 8. Mock Test Question Results
-- =========================================================
CREATE TABLE IF NOT EXISTS mock_test_question_results (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER REFERENCES mock_test_attempts(attempt_id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    question_id INTEGER,
    domain VARCHAR(100),
    question_text TEXT,
    question_type VARCHAR(50),
    selected_answers JSONB,
    correct_answers JSONB,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 9. Documents Table
-- For MentorGrowAI document/RAG metadata.
-- LangChain may separately create langchain_pg_collection and
-- langchain_pg_embedding automatically when PGVector is used.
-- =========================================================
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name TEXT,
    file_path TEXT,
    source_file TEXT,
    document_type VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================================
-- 10. Helpful Indexes
-- =========================================================
CREATE INDEX IF NOT EXISTS idx_questions_set_id
    ON questions(set_id);

CREATE INDEX IF NOT EXISTS idx_questions_domain
    ON questions(domain);

CREATE INDEX IF NOT EXISTS idx_exam_sessions_user_id
    ON exam_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_exam_question_answers_session_id
    ON exam_question_answers(session_id);

CREATE INDEX IF NOT EXISTS idx_weak_concepts_user_id
    ON weak_concepts(user_id);

CREATE INDEX IF NOT EXISTS idx_mock_test_attempts_user_id
    ON mock_test_attempts(user_id);

CREATE INDEX IF NOT EXISTS idx_mock_test_attempts_session_id
    ON mock_test_attempts(session_id);

CREATE INDEX IF NOT EXISTS idx_mock_test_question_results_attempt_id
    ON mock_test_question_results(attempt_id);

CREATE INDEX IF NOT EXISTS idx_documents_metadata_gin
    ON documents USING GIN(metadata);

-- =========================================================
-- Verification Queries
-- =========================================================
\echo 'Extensions installed:'
\dx

\echo 'Tables created:'
\dt

\echo 'MentorGrowAI schema setup completed successfully.'
