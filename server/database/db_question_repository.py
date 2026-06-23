
import psycopg2
import json
from server.database.db_connection import get_connection

def save_question_set(response):
    try:
        conn = get_connection()
        print("PostgreSQL connection successful...")
        cursor = conn.cursor()

        # Extract domain
        domain = response.questions[0].domain

        # 1️⃣ Create question set
        cursor.execute("""
            INSERT INTO question_sets (domain, question_count)
            VALUES (%s, %s)
            RETURNING set_id
        """, (domain, response.count))

        set_id = cursor.fetchone()[0]

        # 2️⃣ Insert each question
        for q in response.questions:

            cursor.execute("""
                INSERT INTO questions
                (set_id, question, options, correct_answers, type, domain)
                VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                set_id,
                q.question,
                json.dumps(q.options),
                json.dumps(q.correct_answers),
                q.type,
                q.domain
            ))

        conn.commit()
        cursor.close()
        conn.close()

        print("Questions stored successfully with set_id:", set_id)
    except psycopg2.Error as e:
        print("Database connection failed")
        print("Error:", e)
