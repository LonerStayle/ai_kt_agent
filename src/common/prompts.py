from common.LLMType import LLMType

travel_system_prompt = """
너는 K-컬처 여행 & 기념품 추천 전문 AI 에이전트야.
사용자가 입력한 이미지, 질문, 키워드, 그리고 선택한 장소 후보를 기반으로,
- 한국 여행 장소 (POI)
- 최적 여행 루트
- K-팝 및 전통 기념품/굿즈
를 연결해서 추천해야 해.

규칙:
1. 반드시 사용자가 선택한 장소 후보와 검색된 문서(context)를 함께 참고해서 답변할 것.
2. 선택된 장소들을 중심으로, 장소 이름·위치·간단 설명·관련 굿즈를 제공할 것.
3. 링크나 지도 정보가 있으면 알려주기.
4. 한국어/영어 모두 가능한 답변을 제공하되, 사용자가 요청하면 해당 언어로만 답변.

답변 스타일:
- 여행 가이드처럼 친절하고 명확하게
- 불필요한 추측은 하지 않고, 자료에 근거
"""


def selected_places_to_text(
        selected_places: list[str]
): 
    if not selected_places: raise ValueError("선택된 장소가 없습니다.")
    return ", ".join(place.name for place in selected_places)


def build_find_rag_prompts(
    selected_places: list[str]
    
):   
    if not selected_places: return
    return f"""
    케이팝 데몬 헌터스에서 다음 장소들과 관련된 내용을 찾아줘
    {selected_places_to_text(selected_places)}
    """



def build_question_prompts(
    selected_places: list[str],
    context_docs: list[dict],
):
    # 장소 후보 정하지 않으면 리턴
    if not selected_places: raise ValueError("선택된 장소가 없습니다.")
    places_text = selected_places_to_text(selected_places)

    # Rag에서 받는 context 문서 받기  
    if context_docs:
        context_text = "\n\n".join(
            [f"[출처: {d.get('source','?')} p{d.get('page','?')}]\n{d['text']}" for d in context_docs]
        )
    else:
        context_text = "관련 문서가 없습니다."

    # 최종 질문 프롬프트 입니당
    user_prompt = f"""
사용자가 선택한 장소 후보: {places_text}

검색된 문서(context):
{context_text}

위 장소들과 문서를 기반으로 여행 루트와 기념품 추천을 해줘.
""".strip()

    return [
        {"role": "system", "content": travel_system_prompt.strip()},
        {"role": "user", "content": user_prompt},
    ]