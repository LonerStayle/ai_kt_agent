import streamlit as st
import requests
import httpx


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
if "step1_result" not in st.session_state:
    st.session_state.step1_result = {
        "title": "서울 여행 루트 추천",
        "images": [r"C:\PythonProject\ai_kt_agent\src\data\낙산공원 성곽길.png", 
                   r"C:\PythonProject\ai_kt_agent\src\data\남산타워.png",
                   r"C:\PythonProject\ai_kt_agent\src\data\명동.png",
], 

        "summary": "1일차: 남산타워 → 명동 → 낙산공원...(피그마 표시에서만 생략)..."
    }

# --- 우측 상단 언어 선택 ---
st.markdown(f"<div class='lang-select'>KOR</div>", unsafe_allow_html=True)
            
# --- 제목 표시 ---
if "title" not in st.session_state:
    res = requests.get("http://localhost:8000/title")
    data = res.json()
    st.session_state.title = data["title"]
st.title(st.session_state.title)

# --- 1단계 결과 표시 ---
if "step1_result" in st.session_state:
    st.sidebar.header("📌 1단계 결과")
    st.sidebar.markdown(f"**추천 루트 요약:**\n{st.session_state.step1_result['summary']}")
    for img_path in st.session_state.step1_result["images"]:
        st.sidebar.image(img_path, use_container_width=True)


# --- 채팅 표시 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

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
        message_placeholder = st.empty()
        full_response = ""

        # FastAPI 서버에 스트리밍 요청
        with httpx.stream(
            "POST",
            "http://localhost:8000/chat",
            params={"user_text": prompt},
            timeout=None,
        ) as r:
            for chunk in r.iter_text():
                if chunk:
                    full_response += chunk
                    message_placeholder.markdown(full_response + "▌")  # 커서 표시 효과

        # 최종 응답 확정
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})