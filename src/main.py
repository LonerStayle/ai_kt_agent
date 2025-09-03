
import common.GlobalSetting as gl
import common.prompts as prompts
from common.SelectImage import SelectImage
from ollama import Client
from pipe_lines.rag import hybrid_search, rerank

kt_base_name = "K-intelligence/Midm-2.0-Base-Instruct"
client = Client(host="http://127.0.0.1:11434")



def send_prompt(selected_places: list[SelectImage]):
    
    query_by_rag = prompts.build_find_rag_prompts(selected_places)
    candidates = hybrid_search(query_by_rag, top_k=5) 

    messages = prompts.build_question_prompts(selected_places,candidates)
    print(messages)
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


