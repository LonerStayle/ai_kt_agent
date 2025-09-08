import src.common.GlobalSetting as gl
import re
from typing import List
from src.chat.SessionStore import SessionStore
from ollama import Client

# ---- Redis 전용 ----
REDIS_URL = "redis://localhost:6379/0"
print(f"[BOOT] USE_REDIS=True, REDIS_URL={REDIS_URL}")

# Ollama 클라이언트
llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME

# 세션 스토어 (system_prompt는 Redis에 저장됨)
system_prompt = "You are a helpful assistant. Explain step-by-step for beginners."
session_store = SessionStore(system_prompt=system_prompt, window_pairs=6, max_chars=8000)

def _sanitize_id(raw: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]', '_', raw or 'unknown')

# ------------------------------------------------------------
# 한 턴 대화 함수
# ------------------------------------------------------------
def chat_once(user_text: str, user_ip: str = "127.0.0.1") -> str:
    mem = session_store.get(_sanitize_id(user_ip))
    mem.add_user(user_text)

    messages = mem.build_messages()
    print("\n[모델 입력 메시지들]")
    print(messages)

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
    mem.add_assistant(assistant_text)

    return assistant_text

def chat(question: str, ip: str):
    answer = chat_once(question, user_ip=ip)
    return answer

if __name__ == "__main__":
    answer = chat("내가 좋아하는 음식이 뭐라고?", "127.0.0.2")
