
import json
from datetime import datetime

import redis
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
)

# ----------------------------------
# Redis Connection
# ----------------------------------

try:
    r = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        decode_responses=True,
    )

    r.ping()

    print("✅ Redis connected")

    REDIS_AVAILABLE = True

except Exception:

    print(
        "⚠️ Redis not available - using in-memory fallback"
    )

    REDIS_AVAILABLE = False

    r = {}


# ----------------------------------
# Redis Session Manager
# ----------------------------------

class RedisSessionManager:

    SESSION_PREFIX = "session:"
    SESSION_TTL = 60 * 60 * 24

    MOCKTEST_PREFIX = "mocktest:"
    MOCKTEST_TTL = 60 * 60 * 24

    def __init__(self, redis_client):

        self.redis = redis_client

        self.sessions_in_memory = {}

    # ==================================================
    # CHAT SESSION METHODS
    # ==================================================

    def _session_key(self, session_id: str) -> str:

        return f"{self.SESSION_PREFIX}{session_id}"

    def save_session(
        self,
        session_id: str,
        messages: list
    ):

        serialized = [
            {
                "type": m.__class__.__name__,
                "content": m.content,
            }
            for m in messages
        ]

        if REDIS_AVAILABLE:

            self.redis.setex(
                self._session_key(session_id),
                self.SESSION_TTL,
                json.dumps(serialized),
            )

        else:

            self.sessions_in_memory[
                self._session_key(session_id)
            ] = serialized

        print(
            f"[Redis] Saved chat session "
            f"{session_id}"
        )

    def load_session(
        self,
        session_id: str
    ):

        if REDIS_AVAILABLE:

            data = self.redis.get(
                self._session_key(session_id)
            )

        else:

            data = self.sessions_in_memory.get(
                self._session_key(session_id)
            )

            if data:
                data = json.dumps(data)

        if not data:

            print(
                f"[Redis] No chat session "
                f"found for {session_id}"
            )

            return []

        serialized = json.loads(data)

        type_map = {
            "HumanMessage": HumanMessage,
            "AIMessage": AIMessage,
            "SystemMessage": SystemMessage,
        }

        messages = [
            type_map[m["type"]](
                content=m["content"]
            )
            for m in serialized
        ]

        return messages

    def delete_session(
        self,
        session_id: str
    ):

        if REDIS_AVAILABLE:

            self.redis.delete(
                self._session_key(session_id)
            )

        else:

            self.sessions_in_memory.pop(
                self._session_key(session_id),
                None,
            )

    # ==================================================
    # MOCK TEST METHODS
    # ==================================================

    def _mocktest_key(
        self,
        session_id: str
    ) -> str:

        return (
            f"{self.MOCKTEST_PREFIX}"
            f"{session_id}"
        )

    def save_mocktest(
        self,
        user_id: str,
        session_id: str,
        domain: str,
        questions: list,
    ):
        """
        Save generated mock test questions.

        questions format:

        [
            {
                "question": "...",
                "options": [...],
                "correct_answers": [...],
                "type": "...",
                "domain": "..."
            }
        ]
        """

        payload = {
            "userId": user_id,
            "sessionId": session_id,
            "examName":
                f"AWS AI Practitioner {domain}",
            "generatedAt":
                datetime.utcnow().isoformat(),
            "questions": [],
        }

        for idx, q in enumerate(
            questions,
            start=1
        ):

            payload["questions"].append(
                {
                    "questionId": idx,

                    "question":
                        q["question"],

                    "options":
                        q["options"],

                    "correct_answers":
                        q["correct_answers"],

                    "type":
                        q["type"],

                    "domain":
                        q["domain"],
                }
            )

        if REDIS_AVAILABLE:

            self.redis.setex(
                self._mocktest_key(session_id),
                self.MOCKTEST_TTL,
                json.dumps(payload),
            )

        else:

            self.sessions_in_memory[
                self._mocktest_key(session_id)
            ] = payload

        print(
            f"[Redis] Saved mock test "
            f"{session_id} "
            f"with "
            f"{len(questions)} questions"
        )

        return payload

    def load_mocktest(
        self,
        session_id: str
    ):

        if REDIS_AVAILABLE:

            data = self.redis.get(
                self._mocktest_key(session_id)
            )

        else:

            data = self.sessions_in_memory.get(
                self._mocktest_key(session_id)
            )

            if data:
                return data

        if not data:

            print(
                f"[Redis] No mock test found "
                f"for {session_id}"
            )

            return None

        return json.loads(data)

    def delete_mocktest(
        self,
        session_id: str
    ):

        if REDIS_AVAILABLE:

            self.redis.delete(
                self._mocktest_key(session_id)
            )

        else:

            self.sessions_in_memory.pop(
                self._mocktest_key(session_id),
                None,
            )

    def extend_mocktest(
        self,
        session_id: str
    ):

        if REDIS_AVAILABLE:

            self.redis.expire(
                self._mocktest_key(session_id),
                self.MOCKTEST_TTL,
            )


# ----------------------------------
# Singleton Instance
# ----------------------------------

session_manager = RedisSessionManager(r)