
import json
import psycopg2
from pandas.core.computation.expressions import get_test_result

from server.database.db_connection import get_connection


def save_test_attempt(
    user_id,
    session_id,
    exam_name,
    total_questions,
    correct_answers,
    wrong_answers,
    percentage
):
    """
    Save one mock test attempt and return attempt_id.
    """

    conn = None
    cursor = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO mock_test_attempts (
            user_id,
            session_id,
            exam_name,
            total_questions,
            correct_answers,
            wrong_answers,
            percentage
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        RETURNING attempt_id
        """

        cursor.execute(
            query,
            (
                user_id,
                session_id,
                exam_name,
                total_questions,
                correct_answers,
                wrong_answers,
                percentage,
            ),
        )

        attempt_id = cursor.fetchone()[0]

        conn.commit()

        print(
            f"Saved mock test attempt "
            f"Attempt ID={attempt_id}"
        )

        return attempt_id

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"Error saving mock test attempt: {e}"
        )

        raise

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


def save_question_result(
    attempt_id,
    user_id,
    session_id,
    question_id,
    domain,
    question_text,
    question_type,
    selected_answers,
    correct_answers,
    is_correct
):
    """
    Save individual question result.
    """

    conn = None
    cursor = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        query = """
        INSERT INTO mock_test_question_results (
            attempt_id,
            user_id,
            session_id,
            question_id,
            domain,
            question_text,
            question_type,
            selected_answers,
            correct_answers,
            is_correct
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """

        cursor.execute(
            query,
            (
                attempt_id,
                user_id,
                session_id,
                question_id,
                domain,
                question_text,
                question_type,
                json.dumps(selected_answers),
                json.dumps(correct_answers),
                is_correct,
            ),
        )

        conn.commit()

    except Exception as e:

        if conn:
            conn.rollback()

        print(
            f"Error saving question result: {e}"
        )

        raise

    finally:

        if cursor:
            cursor.close()

        if conn:
            conn.close()


from server.database.db_connection import get_connection


def get_test_result_data(user_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # ------------------------
        # Overall Statistics
        # ------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(
                    AVG(percentage),
                    0
                ),
                COALESCE(
                    MAX(percentage),
                    0
                )
            FROM mock_test_attempts
            WHERE user_id=%s
            """,
            (user_id,)
        )

        stats = cursor.fetchone()

        tests_taken = stats[0]
        average_score = float(stats[1])
        best_score = float(stats[2])

        # ------------------------
        # Latest Attempt
        # ------------------------

        cursor.execute(
            """
            SELECT
                percentage
            FROM mock_test_attempts
            WHERE user_id=%s
            ORDER BY submitted_at DESC
            LIMIT 1
            """,
            (user_id,)
        )

        latest = cursor.fetchone()

        latest_score = (
            float(latest[0])
            if latest
            else 0
        )

        # ------------------------
        # Weak Domains
        # ------------------------

        cursor.execute(
            """
            SELECT
                domain,
                COUNT(*) AS failures
            FROM
                mock_test_question_results
            WHERE
                user_id=%s
                AND is_correct=false
            GROUP BY domain
            ORDER BY failures DESC
            LIMIT 5
            """,
            (user_id,)
        )

        weak_domains = []

        for row in cursor.fetchall():

            weak_domains.append({
                "domain": row[0],
                "failures": row[1]
            })

        # ------------------------
        # Failed Questions
        # ------------------------

        cursor.execute(
            """
            SELECT
                question_text,
                correct_answers
            FROM
                mock_test_question_results
            WHERE
                user_id=%s
                AND is_correct=false
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (user_id,)
        )

        failed_questions = []

        for row in cursor.fetchall():

            failed_questions.append({

                "question":
                    row[0],

                "correct_answers":
                    row[1]
            })

        return {

            "tests_taken":
                tests_taken,

            "average_score":
                average_score,

            "best_score":
                best_score,

            "latest_score":
                latest_score,

            "weak_domains":
                weak_domains,

            "failed_questions":
                failed_questions
        }

    finally:

        cursor.close()
        conn.close()