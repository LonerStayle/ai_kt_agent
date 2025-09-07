# ===============================
# chat_main.py  (IP별 세션 + 파일/Redis 하이브리드)
# ===============================

# 0) 프로젝트 내 기존 의존성 (그대로 유지)
import src.common.GlobalSetting as gl
import src.common.prompts as prompts
from src.common.SelectImage import SelectImage
from src.tools.rag import hybrid_search, rerank

# 1) 표준 라이브러리 & 설정
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# ---- 하이브리드 옵션(필요에 따라 바꾸세요) ----
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = True         # True: Redis 사용 / False: 로컬(SimpleMemory)만 사용
SAVE_SNAPSHOT = True     # latest.json 저장 여부
SAVE_DAILY_LOG = True    # log-YYYYMMDD.jsonl 저장 여부
print(f"[BOOT] USE_REDIS={USE_REDIS}, REDIS_URL={REDIS_URL}")
# ----------------------------------------------

# 2) Ollama 클라이언트
from ollama import Client


# ------------------------------------------------------------
# A. 간단 메모리 객체 (순수 파이썬) - 최근 N턴만 유지
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# (옵션) Redis 백엔드 메모리 - SimpleMemory와 동일한 인터페이스
# ------------------------------------------------------------
import json as _json
try:
    import redis  # pip install redis
except ImportError:
    redis = None

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


# ------------------------------------------------------------
# B. 세션 파일 경로/저장 유틸 (IP별 폴더에 저장)
# ------------------------------------------------------------
# 프로젝트 루트 고정: src/chat/chat_main.py 기준으로 두 단계 위가 루트
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSIONS_ROOT = PROJECT_ROOT / "sessions"

def _sanitize_id(raw: str) -> str:
    """파일/폴더 이름에 안전하도록 변환 (영문/숫자/._-만 허용)"""
    return re.sub(r'[^A-Za-z0-9_.-]', '_', raw or 'unknown')

def _session_paths(user_id: str):
    """sessions/<user_id>/latest.json + log-YYYYMMDD.jsonl 반환"""
    uid = _sanitize_id(user_id)
    base = SESSIONS_ROOT / uid
    base.mkdir(parents=True, exist_ok=True)
    latest = base / "latest.json"
    log = base / f"log-{datetime.now():%Y%m%d}.jsonl"
    return str(base), str(latest), str(log)

def save_snapshot(memory, user_id: str) -> None:
    """현재 메모리 전체를 latest.json으로 저장 (임시파일→원자교체)"""
    _, latest, _ = _session_paths(user_id)
    tmp = latest + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({"system": getattr(memory, "system", None),
                   "messages": memory.messages}, f, ensure_ascii=False, indent=2)
    os.replace(tmp, latest)

def append_turn_log(user_id: str, user_input: str, assistant_reply: str) -> None:
    """이번 턴만 JSONL로 1줄 append (시간/유저입력/모델응답)"""
    _, _, log = _session_paths(user_id)
    rec = {"ts": datetime.now().isoformat(timespec="seconds"),
           "user": user_input, "assistant": assistant_reply}
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ------------------------------------------------------------
# C. 세션 스토어(하이브리드): Redis or SimpleMemory(+파일)
# ------------------------------------------------------------
class SessionStore:
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
        if USE_REDIS:
            if redis is None:
                raise RuntimeError("redis 패키지가 필요합니다: pip install redis")
            self._redis = redis.from_url(REDIS_URL, decode_responses=False)  # bytes 반환

    def get(self, user_id: str):
        uid = _sanitize_id(user_id)
        if uid in self._pool:
            return self._pool[uid]

        if USE_REDIS:
            mem = RedisMemory(
                r=self._redis,
                key_prefix=f"chat:{uid}",
                system=self.system_prompt,
                window_pairs=self.window_pairs,
                max_chars=self.max_chars,
            )
            # (선택) 로컬 스냅샷이 있고 Redis가 비어있으면 1회 마이그레이션
            try:
                _, latest, _ = _session_paths(uid)
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
            _, latest, _ = _session_paths(uid)
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


# ------------------------------------------------------------
# D. 전역 설정/클라이언트/세션스토어
# ------------------------------------------------------------
model_name = gl.MODEL_NAME
llm_client = Client(host="http://127.0.0.1:11434")

system_prompt = "You are a helpful assistant. Explain step-by-step for beginners."
session_store = SessionStore(system_prompt=system_prompt, window_pairs=6, max_chars=8000)


# ------------------------------------------------------------
# E. 한 턴 대화 함수 (IP별 식별)
# ------------------------------------------------------------
def chat_once(user_text: str, user_ip: str = "127.0.0.1") -> str:
    """
    1) IP로 메모리 가져오기
    2) 유저 입력 저장 → messages 구성 → 모델 스트리밍 호출
    3) 모델 응답 저장
    4) (옵션) 스냅샷/로그 저장
    """
    mem = session_store.get(user_ip)   # 1) 세션 메모리 확보
    mem.add_user(user_text)            # 2) 유저 입력 저장

    messages = mem.build_messages()    # 모델 입력 구성
    print("\n[모델 입력 메시지들]")
    print(messages)

    # 3) 모델 스트리밍 호출
    chunks: List[str] = []
    for chunk in llm_client.chat(
        model=model_name,
        messages=messages,
        stream=True,
        options={"num_predict": 128}
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]
            chunks.append(piece)
            print(piece, end="", flush=True)

    assistant_text = "".join(chunks).strip()

    # 4) 모델 응답 저장 + (옵션) 파일 기록
    mem.add_assistant(assistant_text)
    if SAVE_SNAPSHOT:
        save_snapshot(mem, user_ip)                   # 전체 스냅샷
    if SAVE_DAILY_LOG:
        append_turn_log(user_ip, user_text, assistant_text)  # 턴 로그

    print("\n\n[최종 응답]", assistant_text)
    return assistant_text


# ------------------------------------------------------------
# F. CLI 진입점 (IP 바꾸기 & 경로확인 명령)
# ------------------------------------------------------------
def main():
    print("=== Chat CLI ===")
    print("명령어: /q 종료, /ip <세션ID>, /where 현재 세션 저장 경로 확인")

    current_ip = "127.0.0.1"  # 기본 세션(아이디)

    while True:
        try:
            user_input = input("\nYou> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        if not user_input:
            continue

        # 종료
        if user_input == "/q":
            print("bye")
            break

        # 세션(아이디) 변경: 예) /ip alice  /ip 203.0.113.5
        if user_input.startswith("/ip "):
            current_ip = user_input.split(maxsplit=1)[1].strip()
            print(f"[INFO] Session set to: {current_ip}")
            continue

        # 현재 세션의 저장 경로 확인
        if user_input == "/where":
            base, latest, log = _session_paths(current_ip)
            print("[PATH] base   =", os.path.abspath(base))
            print("[PATH] latest =", os.path.abspath(latest))
            print("[PATH] log    =", os.path.abspath(log))
            continue

        # 일반 대화(현재 세션으로 저장)
        reply = chat_once(user_input, user_ip=current_ip)
        print(f"\nBot> {reply}")


if __name__ == "__main__":
    main()
