from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import src.chat.chat_client as chat_client
from src.chat.SessionStore import SessionStore
import src.common.GlobalSetting as gl
from ollama import Client
import src.head_mi_dm as head
from src.common.SelectImage import SelectImage
from typing import List
from pydantic import BaseModel


app = FastAPI()

# Redis + Ollama 설정
llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME

# ✅ session_store는 FastAPI에서만 관리
system_prompt = "You are a helpful assistant. Explain step-by-step for beginners."
session_store = SessionStore(
    system_prompt=system_prompt, window_pairs=6, max_chars=8000
)

def get_user_ip(request: Request):
    client_ip = request.headers.get("x-forwarded-for")
    if client_ip:
        user_ip = client_ip.split(",")[0]
    else:
        user_ip = request.client.host
    return user_ip

@app.get("/title")
def get_title():
    return {"title": "서울 여행 루트 추천"}

class PlaceRequest(BaseModel):
    lang: str
    selects: List[SelectImage]

@app.post("/send_place")
def send_place_and_lang(req: PlaceRequest, request: Request):
    
    lang = req.lang
    selects = req.selects

    answer = head.send_prompt(selects)
    if lang == "en":
        answer = head.translate_answer(answer)

    summary = head.make_summary_one_line(answer)
    if lang == "en":
        summary = head.translate_answer(summary)
    
    # user_ip = get_user_ip(request)
    # mem = session_store.get(user_ip)
    # mem.set_system(answer)

    # 문자열로 강제 변환
    payload = {
        "summary": str(summary) if summary is not None else "",
        "answer": str(answer) if answer is not None else "",
    }
    return JSONResponse(payload)   # orjson/uvicorn 조합 이슈 회피

@app.post("/chat")
async def chat_endpoint(user_text: str, request: Request):
    user_ip = get_user_ip(request)
    mem = session_store.get(user_ip)
    mem.add_user(user_text)
    messages = mem.build_messages()

    return StreamingResponse(
        chat_client.stream_chat(mem, messages), media_type="text/plain"
    )
