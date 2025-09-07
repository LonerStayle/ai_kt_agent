# ------------------------------------------------------------
# A. 간단 메모리 객체 (순수 파이썬) - 최근 N턴만 유지
# ------------------------------------------------------------
import os, re, json
from typing import List, Dict, Optional
class SimpleMemory:
    """
    - role 기반(messages 배열)으로 대화 기록 관리
    - window_pairs: '최근 N턴(user+assistant 쌍)'만 남겨 컨텍스트 제한
    - max_chars: 전체 글자 수 제한(2차 안전장치)
    - save_json/load_json: 파일 스냅샷 저장/복구
    """
    def __init__(self, system: Optional[str] = None, window_pairs: int = 6, max_chars: Optional[int] = 8000):
        self.system = system
        self.window_pairs = window_pairs
        self.max_chars = max_chars
        self.messages: List[Dict[str, str]] = []

    def add_user(self, content: str) -> None:
        self.messages.append({"role": "user", "content": content})

    def add_assistant(self, content: str) -> None:
        self.messages.append({"role": "assistant", "content": content})

    def build_messages(self) -> List[Dict[str, str]]:
        final: List[Dict[str, str]] = []
        if self.system:
            final.append({"role": "system", "content": self.system})

        # 최근 N턴 선택
        selected = self.messages[-(self.window_pairs * 2):] if self.window_pairs else self.messages

        # 문자수 제한(최신 → 과거로 거꾸로 담고 다시 뒤집기)
        if self.max_chars:
            acc, rev = 0, []
            for m in reversed(selected):
                L = len(m["content"])
                if acc + L > self.max_chars and rev:
                    break
                rev.append(m); acc += L
            selected = list(reversed(rev))

        final.extend(selected)
        return final

    # ---- 파일 저장/복구 (스냅샷용) ----
    def save_json(self, path: str) -> None:
        data = {"system": self.system, "messages": self.messages}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_json(cls, path: str) -> "SimpleMemory":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mem = cls(system=data.get("system"))
        mem.messages = data.get("messages", [])
        return mem