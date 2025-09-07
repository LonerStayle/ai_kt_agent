from typing import List, Dict
import redis
from src.chat.RedisMemory import RedisMemory
from src.chat.SimpleMemory import SimpleMemory
import os,json

# ------------------------------------------------------------
# C. 세션 스토어(하이브리드): Redis or SimpleMemory(+파일)
# ------------------------------------------------------------
class SessionStore:
    USE_REDIS = True
    REDIS_URL = "redis://localhost:6379/0"         
    """
    - USE_REDIS=True  → RedisMemory 사용
    - USE_REDIS=False → SimpleMemory + 파일 스냅샷
    """
    def __init__(self, system_prompt: str, window_pairs: int = 6, max_chars: int = 8000):
        self.system_prompt = system_prompt
        self.window_pairs = window_pairs
        self.max_chars = max_chars
        self._pool: Dict[str, object] = {}

        self._redis = None
        if self.USE_REDIS:
            if redis is None:
                raise RuntimeError("redis 패키지가 필요합니다: pip install redis")
            self._redis = redis.from_url(self.REDIS_URL, decode_responses=False)


    def get(self, user_id: str):
        uid = user_id
        if uid in self._pool:
            return self._pool[uid]

        if self.USE_REDIS:
            mem = RedisMemory(
                r=self._redis,
                key_prefix=f"chat:{uid}",
                system=self.system_prompt,
                window_pairs=self.window_pairs,
                max_chars=self.max_chars,
            )
            # (선택) 로컬 스냅샷이 있고 Redis가 비어있으면 1회 마이그레이션
            try:
                _, latest, _ = self._session_paths(uid)
                if os.path.exists(latest) and self._redis.llen(f"chat:{uid}:messages") == 0:
                    with open(latest, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for m in data.get("messages", []):
                        if m.get("role") in ("user", "assistant"):
                            self._redis.rpush(f"chat:{uid}:messages", json.dumps(m, ensure_ascii=False))
            except Exception:
                pass
        else:
            # 로컬 스냅샷에서 복구하거나 새로 생성
            _, latest, _ = self._session_paths(uid)
            if os.path.exists(latest):
                mem = SimpleMemory.load_json(latest)
                mem.system = mem.system or self.system_prompt
                mem.window_pairs = self.window_pairs
                mem.max_chars = self.max_chars
            else:
                mem = SimpleMemory(system=self.system_prompt,
                                   window_pairs=self.window_pairs,
                                   max_chars=self.max_chars)

        self._pool[uid] = mem
        return mem



