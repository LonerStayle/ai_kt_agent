
import src.common.GlobalSetting as gl
import src.common.prompts as prompts
from src.common.SelectImage import SelectImage
from ollama import Client
from src.tools.rag import hybrid_search, rerank
import json
import redis
import uuid

kt_base_name = "K-intelligence/Midm-2.0-Base-Instruct"
client = Client(host="http://127.0.0.1:11434")
cache = redis.Redis(host='127.0.0.1', port=6379, decode_responses=True)

# 어싱크로 감싼 이유는 추후 비동기를 사용하기 위함 입니다.
# 툴 사용할때 LLM 호출 2번 할탠데 툴 불러오는 과정의 연산을 최적화 하기 위함 
async def async_hybrid_search(query):
    return hybrid_search(query, top_k=5)

def send_prompt(selected_places: list[SelectImage]):
    
    tool_llm = client.chat(
        model = gl.MODEL_NAME,
        messages=[
            {"role": "system", "content": prompts.tool_selection_prompt},
            {"role": "user", "content": f"선택된 장소: {selected_places}"}
        ],
        stream=True,
        options={
            "num_predict":128
        }
    )

    # action = json.load(tool_llm["meesage"]["content"])
    # tool_name, tool_input =  action["action"], action["input"]

    # tools = {
    #     "search": search_places,
    # }

    query_by_rag = prompts.build_find_rag_prompts(selected_places)
    candidates = hybrid_search(query_by_rag, top_k=5) 

    messages = prompts.build_question_prompts(selected_places,candidates)
    print(messages)
    
    # uuid라는 유니크한 문자열 생성
    user_key = f"user:{uuid.uuid4().hex}"
    print(f"user key: {user_key}")
    
    # redis(임시 저장소)에 생성한 값을 저장/불러오기
    cache.set(user_key, json.dumps(messages), ex=300)  # 300초간 유지
    print(cache.get(user_key))
    
    for chunk in client.chat(
        model= gl.MODEL_NAME,  
        messages=messages,
        stream=True,
        options={
        "num_predict": 128  
        }
    ):         
        if isinstance(chunk, tuple): chunk = chunk[0]
        if "message" in chunk and "content" in chunk["message"]:
            print(chunk["message"]["content"], end="", flush=True)
def main():
    send_prompt([SelectImage.A, SelectImage.B ])


if __name__ == "__main__":
    main()



