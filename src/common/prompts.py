from src.common.LLMType import LLMType

mini_system_prompt = "너는 이시대 최고의 번역가야 무조건 다 영어로 번역해"
base_system_prompt = "너는 외국인 담당 임금체불 상담 전문가야"

def build_question_prompts(question_prompt, llm_type:LLMType):
    
    if(llm_type == LLMType.KT_MINI):
        system_prompt = mini_system_prompt
    else :
        system_prompt = base_system_prompt

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question_prompt},
    ]

# def build_question_prompts(question_prompt, llm_type:LLMType):
    
#     if(llm_type == LLMType.KT_MINI):
#         system_prompt = mini_system_prompt
#     else :
#         system_prompt = base_system_prompt
    
#     return f"[시스템]\n{system_prompt}\n\n사용자 질문:{question_prompt}"

    
