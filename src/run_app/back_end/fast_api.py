from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import StreamingResponse, JSONResponse
import src.agent.chat_agent as chat_agent
from src.memory.SessionStore import SessionStore
import src.common.GlobalSetting as gl
from ollama import Client
import src.agent.mi_dm_agent as head
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
    
    user_ip = get_user_ip(request)
    mem = session_store.get(user_ip)
    chat_instroduct = f"""
    너는 외국인의 관광을 안내하는 1:1 관광 가이드야
    교통, 역사, 지리, 즐길거리에 아주 현명한 에이전트로써
    외국인에게 입체적인 관광 안내를 제공합니다.

    아래는 이전 여행사로부터 받은 현재 외국인에게 추천한 
    여행 코스입니다. 
    아래 상황을 보고 맞는 가이드를 진행하세요
    ------------------------------------------

    {answer}

    ------------------------------------------
    """
    mem.set_system(chat_instroduct)

    # 문자열로 강제 변환
    payload = {
        "summary": str(summary) if summary is not None else "",
        "answer": str(answer) if answer is not None else "",
    }
    return JSONResponse(payload)   # orjson/uvicorn 조합 이슈 회피

@app.post("/chat")
async def chat_endpoint(
    request: Request,
    user_text: str = Form(...),               # 텍스트는 Form 필드
    image: UploadFile | None = File(None),    # 이미지는 File 필드 (옵션)
):
    user_ip = get_user_ip(request)
    mem = session_store.get(user_ip)
    mem.add_user(user_text)
    messages = mem.build_messages()

    print(user_text)
    print(image)
    # 이미지가 있으면 바이트로 읽거나 파일로 저장
    if image is not None:
        raw_bytes = await image.read()
        # 예: 저장
        # with open(f"uploads/{image.filename}", "wb") as f:
        #     f.write(raw_bytes)
        # 예: 바로 LLM에 넘기기
        # llm_response = call_llm(user_text, raw_bytes)

    return StreamingResponse(chat_agent.chat(mem, messages), media_type="text/plain")