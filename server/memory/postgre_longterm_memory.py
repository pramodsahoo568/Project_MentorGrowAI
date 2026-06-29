import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime


class PostgresChatStore:

    def __init__(self):
        dsn = (
            os.getenv("POSTGRES_CONNECTION")
            or os.getenv("POSTGRES_DSN")
            or os.getenv("DATABASE_URL")
        )

        if not dsn:
            raise ValueError("PostgreSQL connection string not configured")

        self.conn = psycopg2.connect(
            dsn,
            cursor_factory=RealDictCursor
        )

        self.conn.autocommit = True

        print("✅ Connected to PostgreSQL")

    def close(self):
        if self.conn:
            self.conn.close()

    # =========================================================
    # USERS
    # =========================================================

    def get_or_create_user(
        self,
        external_user_id: str,
        email: str | None = None,
        display_name: str | None = None,
        auth_provider: str = "clerk"
    ):

        query = """
        INSERT INTO users (
            clerk_user_id,
            email,
            name
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (clerk_user_id)
        DO UPDATE SET
            email = EXCLUDED.email,
            name = EXCLUDED.name,
            last_login_at = CURRENT_TIMESTAMP

        RETURNING *;
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    external_user_id,
                    email,
                    display_name
                )
            )

            user = cur.fetchone()

        return user

    # =========================================================
    # CHAT SESSION
    # =========================================================

    def create_chat_session(
        self,
        user_id: int,
        title: str = "New Chat",
        session_type: str = "open_chat"
    ):

        query = """
        INSERT INTO chat_sessions (
            user_id,
            title,
            session_type
        )
        VALUES (%s, %s, %s)
        RETURNING *;
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    user_id,
                    title,
                    session_type
                )
            )

            session = cur.fetchone()

        return session

    # =========================================================
    # STORE MESSAGE
    # =========================================================

    def store_message(
        self,
        session_id: int,
        role: str,
        message: str,
        metadata: dict | None = None
    ):

        query = """
        INSERT INTO chat_messages (
            session_id,
            role,
            message,
            metadata
        )
        VALUES (%s, %s, %s, %s)
        RETURNING *;
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    session_id,
                    role,
                    message,
                    metadata
                )
            )

            row = cur.fetchone()

        return row

    # =========================================================
    # GET RECENT MESSAGES
    # =========================================================

    def get_recent_messages(
        self,
        session_id: int,
        limit: int = 10
    ):

        query = """
        SELECT
            id,
            role,
            message,
            metadata,
            created_at
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY created_at DESC
        LIMIT %s;
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (session_id, limit))

            rows = cur.fetchall()

        return list(reversed(rows))

    # =========================================================
    # UPDATE SESSION SUMMARY
    # =========================================================

    def update_session_summary(
        self,
        session_id: int,
        summary: str
    ):

        query = """
        UPDATE chat_sessions
        SET
            latest_summary = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = %s;
        """

        with self.conn.cursor() as cur:
            cur.execute(
                query,
                (
                    summary,
                    session_id
                )
            )

    # =========================================================
    # GET SESSION SUMMARY
    # =========================================================

    def get_session_summary(
        self,
        session_id: int
    ):

        query = """
        SELECT latest_summary
        FROM chat_sessions
        WHERE id = %s;
        """

        with self.conn.cursor() as cur:
            cur.execute(query, (session_id,))

            row = cur.fetchone()

        return row["latest_summary"] if row else None
