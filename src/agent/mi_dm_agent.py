import src.common.GlobalSetting as gl
import src.common.prompts as prompts
from src.common.SelectImage import SelectImage
from ollama import Client
from src.tools.rag import hybrid_search, rerank
import os
from dotenv import load_dotenv
from openai import OpenAI
import src.tools.tavily_client as tavily_client


load_dotenv()

kt_base_name = "K-intelligence/Midm-2.0-Base-Instruct"
client = Client(host="http://127.0.0.1:11434")

api_key = os.getenv("OPENAI_API_KEY")
llm = OpenAI(api_key=api_key)


# 어싱크로 감싼 이유는 추후 비동기를 사용하기 위함 입니다.
# 툴 사용할때 LLM 호출 2번 할탠데 툴 불러오는 과정의 연산을 최적화 하기 위함
async def async_hybrid_search(query):
    return hybrid_search(query, top_k=5)


def get_move_times(selected_places: list[SelectImage]):
    result_dict = {}

    for i in range(len(selected_places) - 1):
        start = selected_places[i].value
        end = selected_places[i + 1].value

        temp = """
        [역할]
        너는 서울 교통 안내 도우미야.
        {start}에서 {end}까지 대중 교통 시간을 알려줘

        [필수 규칙]
        반드시 OUTPUT 규칙에 따른 응답을 할 것
        
        [OUTPUT 규칙]
        택시는 40분,
        버스는 1시간 30분,
        지하철 1시간,
        """
        query = temp.format(start = start, end = end)
        response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": query},
            {"role": "user", "content": f"{start}에서 {end}까지 각 대중교통 시간을 알려줘"}
        ])
        result_text = response.choices[0].message.content
        result_dict[f"{start} -> {end} 이동경로"] = result_text
    return result_dict

def get_remaind_times(selected_places: list[SelectImage]):
    result_dict = {}

    for i in range(len(selected_places)):
        place = selected_places[i].value

        temp = """
        [역할]
        너는 여행 체류시간 전문 가이드야
        너무 적어도 안돼, 여유를 즐긴다는 가정이야
        {place}에서 얼마나 놀면 좋을지 현실적으로 이야기 해줘
        
        [필수 규칙]
        반드시 OUTPUT 규칙에 따른 응답을 할 것
        
        [OUTPUT 규칙]
        {place}의 체류시간은 1시간 20분
        """
        query = temp.format(place = place)
        response = llm.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": query},
            {"role": "user", "content": "{place}의 여행에서 놀만한 체류 시간을 알려줘"}
        ])
        result_text = response.choices[0].message.content
        result_dict[place+"의 체류 시간"] = result_text

    return result_dict

def send_prompt(selected_places: list[SelectImage]):
    selected_places

    query_by_rag = prompts.build_find_rag_prompts(selected_places)
    candidates = hybrid_search(query_by_rag, top_k=5)
    move_times = get_move_times(selected_places)
    remaind_times = get_remaind_times(selected_places)
    
    messages = prompts.build_question_prompts(selected_places, candidates, move_times, remaind_times)
    print(messages)

    full_answer = []

    for chunk in client.chat(
        model=gl.MODEL_NAME,
        messages=messages,
        stream=True,
        options={"num_predict": 1000},
    ):
        if isinstance(chunk, tuple):
            chunk = chunk[0]

        if "message" in chunk and "content" in chunk["message"]:
            full_answer.append(chunk["message"]["content"])
            print(chunk["message"]["content"], end="", flush=True)

    return "".join(full_answer)


def translate_answer(answer: str):

    message = prompts.build_translate_prompts(answer)

    response = llm.chat.completions.create(model="gpt-5", messages=message)

    return response.choices[0].message.content


def make_summary_one_line(trans_link_answer: str):

    message = prompts.build_summary_prompts(trans_link_answer)

    return "".join(
        chunk["message"]["content"]
        for chunk in client.chat(
            model=gl.MODEL_NAME,
            messages=message,
            stream=True,
            options={
                "num_predict": 1000
            },
        )
    )
