from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import src.chat.chat_client as chat_client
from src.chat.SessionStore import SessionStore
import src.common.GlobalSetting as gl
from ollama import Client

app = FastAPI()

# Redis + Ollama 설정
llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME

# ✅ session_store는 FastAPI에서만 관리
system_prompt = "You are a helpful assistant. Explain step-by-step for beginners."
session_store = SessionStore(system_prompt=system_prompt, window_pairs=6, max_chars=8000)

@app.get("/title")
def read_root():
    return {"title": "K 테크 에이전트 화이팅!!"}

def get_user_ip(request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        user_ip = client_ip.split(",")[0]
    else:
        user_ip = request.client.host
    return user_ip

@app.post("/chat")
async def chat_endpoint(user_text: str, request: Request):
    user_ip = get_user_ip(request)
    mem = session_store.get(user_ip)
    mem.add_user(user_text)
    messages = mem.build_messages()

    return StreamingResponse(chat_client.stream_chat(mem, messages), media_type="text/plain")

@app.post("/init_session")
async def init_session(system_message: str, request: Request):
    user_ip = get_user_ip(request)
    mem = session_store.get(user_ip)
    mem.set_system(system_message)
    return {"system_message": system_message}