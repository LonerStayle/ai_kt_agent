
import src.common.GlobalSetting as gl
import src.common.prompts as prompts
from src.common.SelectImage import SelectImage
from ollama import Client
from src.tools.rag import hybrid_search, rerank
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

kt_base_name = "K-intelligence/Midm-2.0-Base-Instruct"
client = Client(host="http://127.0.0.1:11434")

api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=api_key)

# 어싱크로 감싼 이유는 추후 비동기를 사용하기 위함 입니다.
# 툴 사용할때 LLM 호출 2번 할탠데 툴 불러오는 과정의 연산을 최적화 하기 위함 
async def async_hybrid_search(query):
    return hybrid_search(query, top_k=5)

def send_prompt(selected_places: list[SelectImage]):

    query_by_rag = prompts.build_find_rag_prompts(selected_places)
    candidates = hybrid_search(query_by_rag, top_k=5) 

    messages = prompts.build_question_prompts(selected_places,candidates)
    print(messages)

    full_answer = []

    for chunk in client.chat(
        model= gl.MODEL_NAME,  
        messages=messages,
        stream=True,
        options={
        "num_predict": 1000
        }
    ):         
        if isinstance(chunk, tuple): chunk = chunk[0]

        if "message" in chunk and "content" in chunk["message"]:
            full_answer.append(chunk["message"]["content"])
            print(chunk["message"]["content"], end="", flush=True)

    return ''.join(full_answer)    
    
def translate_answer(answer: str): 
    
    message = prompts.build_translate_prompts(answer)
    
    response = llm.chat.completions.create(
        model="gpt-5",
        messages=message
    )
    
    return response.choices[0].message.content
    
def make_summary_one_line(trans_link_answer: str):
    
    message = prompts.build_summary_prompts(trans_link_answer)

    return "".join(
        chunk["message"]["content"] for chunk in client.chat(
            model=gl.MODEL_NAME, 
            messages=message, 
            stream=True, 
            options={"num_predict": 1000})
    )        
    
def main():
    answer = send_prompt([SelectImage.GYEONGBOKGUNG, SelectImage.COEX])
    
    print('korean')
    print(answer)
    
    # TODO 화면단에서 받아오는 언어값으로 치환
    language = 'en'
    
    if language == 'en':
        answer = translate_answer(answer)
        
    summary = make_summary_one_line(answer)

    # TODO 이 부분은 믿음2.0으로 바꾸는 것 고려 / 영어로 했을 때 20자 넘어가는 것 수정
    if language == 'en':
        summary = translate_answer(summary)
    
    print('summary')
    print(summary)
    
    print('answer')
    print(answer)

if __name__ == "__main__":
    main()



