import redis

import json
from datetime import datetime

import redis
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

## REDIS setup

try:
    r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
    r.ping()
    print("✅ Redis connected")
    REDIS_AVAILABLE = True
except Exception:
    print("⚠️  Redis not available — using in-memory dict as fallback")
    REDIS_AVAILABLE = False
    r = {}  # fallback

# ===== REDIS-BACKED SESSION MANAGER =====
class RedisSessionManager:
    """
    Conversation sessions backed by Redis.
    Sessions expire after TTL seconds of inactivity.
    """

    SESSION_TTL =  60 * 60 * 24 * 1 ## 1 days session memory
    PREFIX = "session:"

    def __init__(self, redis_client):
        self.redis = redis_client
        self.sessions_in_memory = {}  # fallback

    def _key(self, session_id: str) -> str:
        return f"{self.PREFIX}{session_id}"

    def save_session(self, session_id: str, messages: list) -> None:
        """Serialize and save conversation to Redis."""
        print(f"##save_session:{session_id}")
        serialized = [
            {"type": m.__class__.__name__, "content": m.content} for m in messages
        ]
        if REDIS_AVAILABLE:
            self.redis.setex(
                self._key(session_id),
                self.SESSION_TTL,
                json.dumps(serialized),
            )
        else:
            self.sessions_in_memory[session_id] = serialized
        print(f"  [Redis] Saved session {session_id} ({len(messages)} messages)")

    def load_session(self, session_id: str) -> list:
        """Load and deserialize conversation from Redis."""
        print(f"##load_session:{session_id}")
        if REDIS_AVAILABLE:
            data = self.redis.get(self._key(session_id))
        else:
            data = self.sessions_in_memory.get(session_id)
            if data:
                data = json.dumps(data)

        if not data:
            print(f"  [Redis] No session found for {session_id} — starting fresh")
            return []

        serialized = json.loads(data)
        type_map = {
            "HumanMessage": HumanMessage,
            "AIMessage": AIMessage,
            "SystemMessage": SystemMessage,
        }
        messages = [type_map[m["type"]](content=m["content"]) for m in serialized]
        print(f"  [Redis] Loaded session {session_id} ({len(messages)} messages)")
        return messages

    def delete_session(self, session_id: str) -> None:
        if REDIS_AVAILABLE:
            self.redis.delete(self._key(session_id))
        else:
            self.sessions_in_memory.pop(session_id, None)

    def extend_session(self, session_id: str) -> None:
        """Refresh session TTL on activity."""
        if REDIS_AVAILABLE:
            self.redis.expire(self._key(session_id), self.SESSION_TTL)


# ----------------------------------
# Singleton Instance
# ----------------------------------
session_manager = RedisSessionManager(r)