import json as _json
from typing import List, Dict, Optional

class RedisMemory:
    """
    - role 기반 messages를 Redis List에 저장
    - 키: {prefix}:system (String), {prefix}:messages (List)
    - API: add_user / add_assistant / build_messages / messages
    """
    def __init__(self, r, key_prefix: str, system: Optional[str],
                 window_pairs: int = 6, max_chars: Optional[int] = 8000):
        self.r = r
        self.prefix = key_prefix
        self.window_pairs = window_pairs
        self.max_chars = max_chars
        self.sys_key = f"{self.prefix}:system"
        self.msg_key = f"{self.prefix}:messages"

        if system is not None:
            self.r.setnx(self.sys_key, system)
        val = self.r.get(self.sys_key)
        self.system = val.decode() if isinstance(val, (bytes, bytearray)) else val

    # --- SimpleMemory와 동일한 API ---
    def add_user(self, content: str) -> None:
        self.r.rpush(self.msg_key, _json.dumps({"role": "user", "content": content}, ensure_ascii=False))
        self._trim()

    def add_assistant(self, content: str) -> None:
        self.r.rpush(self.msg_key, _json.dumps({"role": "assistant", "content": content}, ensure_ascii=False))
        self._trim()

    def _trim(self):
        # Redis에는 최근 2*N개만 유지(윈도우)
        n = self.window_pairs * 2 if self.window_pairs else None
        if n:
            self.r.ltrim(self.msg_key, -n, -1)

    @property
    def messages(self):
        raw = self.r.lrange(self.msg_key, 0, -1)
        out = []
        for x in raw:
            if isinstance(x, (bytes, bytearray)):
                x = x.decode()
            try:
                out.append(_json.loads(x))
            except Exception:
                pass
        return out

    def build_messages(self):
        msgs = []
        if self.system:
            msgs.append({"role": "system", "content": self.system})

        # 최근 N턴만 선택
        n = self.window_pairs * 2 if self.window_pairs else None
        total = self.r.llen(self.msg_key)
        start = max(0, total - n) if n else 0
        selected = []
        for x in self.r.lrange(self.msg_key, start, -1):
            if isinstance(x, (bytes, bytearray)):
                x = x.decode()
            try:
                selected.append(_json.loads(x))
            except Exception:
                pass

        # 문자 수 제한
        if self.max_chars:
            acc, rev = 0, []
            for m in reversed(selected):
                L = len(m["content"])
                if acc + L > self.max_chars and rev:
                    break
                rev.append(m); acc += L
            selected = list(reversed(rev))

        msgs.extend(selected)
        return msgs