import redis
from typing import Dict
from src.chat.RedisMemory import RedisMemory

class SessionStore:
    """
    세션 스토어 (Redis 전용)
    """
    REDIS_URL = "redis://localhost:6379/0"

    def __init__(self, system_prompt: str, window_pairs: int = 6, max_chars: int = 8000):
        self.system_prompt = system_prompt
        self.window_pairs = window_pairs
        self.max_chars = max_chars
        self._pool: Dict[str, object] = {}

        self._redis = redis.from_url(self.REDIS_URL, decode_responses=False)

    def get(self, user_id: str):
        if user_id in self._pool:
            return self._pool[user_id]

        mem = RedisMemory(
            r=self._redis,
            key_prefix=f"chat:{user_id}",
            system=self.system_prompt,
            window_pairs=self.window_pairs,
            max_chars=self.max_chars,
        )
        self._pool[user_id] = mem
        return mem
    

