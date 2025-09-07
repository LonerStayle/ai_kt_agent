# ===============================
# chat_main.py  (IP별 세션 + 파일/Redis 하이브리드)
# ===============================

# 0) 프로젝트 내 기존 의존성 (그대로 유지)
import src.common.GlobalSetting as gl

# 1) 표준 라이브러리 & 설정
import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List
from src.chat.SessionStore import SessionStore

# ---- 하이브리드 옵션(필요에 따라 바꾸세요) ----
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
USE_REDIS = True         # True: Redis 사용 / False: 로컬(SimpleMemory)만 사용
SAVE_SNAPSHOT = True     # latest.json 저장 여부
SAVE_DAILY_LOG = True    # log-YYYYMMDD.jsonl 저장 여부
print(f"[BOOT] USE_REDIS={USE_REDIS}, REDIS_URL={REDIS_URL}")
# ----------------------------------------------

# 2) Ollama 클라이언트
from ollama import Client
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
    mem = session_store.get(_sanitize_id(user_ip))   # 1) 세션 메모리 확보
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
