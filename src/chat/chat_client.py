import src.common.GlobalSetting as gl
from ollama import Client

llm_client = Client(host="http://127.0.0.1:11434")
model_name = gl.MODEL_NAME

def stream_chat(mem, messages):
    chunks = []
    for chunk in llm_client.chat(
        model=model_name,
        messages=messages,
        stream=True,
        options={"num_predict": 128}
    ):
        if isinstance(chunk, tuple): chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            piece = chunk["message"]["content"]

            # 올라마는 기본적으로 <|system|> 를 붙이려는 성격이 있음 강제 제거 
            piece = piece.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
            chunks.append(piece)
            yield piece


    # 캐싱: 스트리밍 끝나고만 Redis에 최종 답변 저장
    assistant_text = "".join(chunks).strip()
    assistant_text = assistant_text.replace("<|system|>", "").replace("<|user|>", "").replace("<|assistant|>", "")
    mem.add_assistant(assistant_text)
