import streamlit as st
import os ,httpx, json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    button[data-testid="stSidebarCollapseButton"] {display: none !important;}
    div[data-testid="stSidebarCollapseButton"] {display: none !important;}
    [data-testid="stSidebarNav"] {display: none;}

    
    /* 우측 상단 언어 선택 박스 위치 조정 */
    .lang-select {
        position: absolute;
        top: 15px;
        right: 20px;
        z-index: 100;
        background-color: #262730;
        padding: 6px 10px;
        border-radius: 8px;
        color: white;
    }
    </style>


"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown("""
    <style>
    /* 채팅 메시지가 추가될 때 희미→선명 효과 없애기 */
    div[data-testid="stChatMessage"] {
        opacity: 1 !important;
        transition: none !important;
        animation: none !important;
    }
    div[data-testid="stChatMessageContent"] {
        opacity: 1 !important;
        transition: none !important;
        animation: none !important;
    }
    </style>
""", unsafe_allow_html=True)

BASE_PATH = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[0]))
DATA_PATH = BASE_PATH / "src" / "data"

# OpenAI 클라이언트 생성
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 1단계 결과 표시 ---
if "step1_result" in st.session_state:
    full_answer = st.session_state.step1_result["answer"]
    print(st.session_state.step1_result)
    st.sidebar.header("📌 1단계 결과")
    st.sidebar.markdown(st.session_state.step1_result['summary'])

    for img_path in st.session_state.step1_result["images"]:
        path = (BASE_PATH / Path(img_path.replace("\\", "/"))).resolve()
        if path.exists():
            with open(path, "rb") as f:
                st.sidebar.image(f.read(), width=232)

    # --- 상세 일정표 ---
    st.sidebar.markdown("---")
    st.sidebar.markdown("**상세 일정표**")

    blocks = full_answer.split("## ")
    for block in blocks:
        if not block.strip():
            continue
        lines = block.strip().splitlines()

        # 🔹 제목 줄
        raw_title = lines[0].strip() if lines else "알 수 없음"
        clean_title = raw_title.lstrip("0123456789. #")
        st.sidebar.markdown(f"**{clean_title}**")

        # 체류시간
        stay = next((l for l in lines if "체류" in l), None)
        if stay:
            st.sidebar.markdown(f"- 체류시간: {stay.replace('체류:', '').strip()}")

        # 기념품 리스트
        if any("기념품" in l for l in lines):
            st.sidebar.markdown("- 기념품:")
            for l in lines:
                if l.strip().startswith("- "):
                    st.sidebar.markdown(f"  • {l[2:].strip()}")

    # --- 사이드바 chat 요약 수정 끝 ---

# --- 채팅 표시 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": full_answer}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메세지를 입력하세요.."):

    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 어시스턴트 응답 표시 (스트리밍)
    with st.chat_message("assistant"):
        with st.spinner("생각 중... 🤔"):
            message_placeholder = st.empty()
            full_response = ""
    
            with httpx.stream(
                "POST",
                "http://localhost:8000/chat",
                params={"user_text": prompt},
                timeout=None,
            ) as r:
                for chunk in r.iter_text():
                    if not chunk:
                        continue

                    # JSON 파싱 시도(goods images)
                    try:
                        data = json.loads(chunk)  

                        # if data["type"] == "images":
                        #     # ✅ 이미지 여러 개 출력
                        #     cols = st.columns(len(data["content"]))
                        #     for col, img_path in zip(cols, data["content"]):
                        #         with open(str(DATA_PATH / img_path), "rb") as f:
                        #             col.image(f.read(), width=200)
                        if data["type"] == "images":
                            # ✅ CSS 스타일 먼저 선언
                            st.markdown("""
                            <style>
                            .image-grid {
                                display: flex;
                                flex-wrap: wrap;
                                gap: 12px;              /* 간격 고정 */
                            }
                            .image-grid img {
                                width: 180px;           /* 카드 크기 고정 */
                                height: auto;
                                border-radius: 8px;
                            }
                            </style>
                            """, unsafe_allow_html=True)
                        
                            # ✅ HTML로 이미지 직접 출력
                            html = '<div class="image-grid">'
                            for img_path in data["content"]:
                                with open(str(DATA_PATH / img_path), "rb") as f:
                                    import base64
                                    img_base64 = base64.b64encode(f.read()).decode("utf-8")
                                    html += f'<img src="data:image/png;base64,{img_base64}" />'
                            html += '</div>'
                        
                            st.markdown(html, unsafe_allow_html=True)

                        
                    except:
                        # 일반 텍스트 응답
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                        continue
                    
            message_placeholder.markdown(full_response)
            
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )