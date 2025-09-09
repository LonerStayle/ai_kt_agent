

import streamlit as st
from pathlib import Path
st.set_page_config(layout="wide")

page_bg = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
[data-testid="stAppViewContainer"] {
    background-color: white;
    color: black;
}
[data-testid="stHeader"] {
    background-color: white;
}
[data-testid="stSidebar"], [data-testid="stSidebarNav"] {
    display: none; /* 사이드바 숨기고 싶으면 */
}

.top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 16px;
}
.top-title {
    flex: 1;
    text-align: center;
    font-family: 'Inter', sans-serif;
    font-size: 24px;
    font-weight: 700;  /* Bold */
}
.lang-label {
    font-family: 'Inter', sans-serif;
    font-size: 18px;
    font-weight: 400;  /* Regular */
    border: 0.5px solid #000000;
    border-radius: 20px;
    padding: 4px 12px;
}

/* 모달 기본 숨김 */
.modal {
    display: none; 
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    overflow: auto;
    background-color: rgba(0,0,0,0.4); /* 반투명 배경 */
}

/* 모달 콘텐츠 */
.modal-content {
    background-color: #fff;
    margin: 15% auto;
    padding: 20px;
    border-radius: 12px;
    width: 300px;
    font-family: 'Inter', sans-serif;
    text-align: center;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
}

</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)
st.markdown(
    """
    <div class="top-bar">
        <div class="top-title">궁금한 여행지를 선택하세요</div>
        <div class="lang-label">KOR</div>
    </div>
    """,
    unsafe_allow_html=True,
)



# --- 이미지 리스트 ---
# images = [
#     r"C:\PythonProject\ai_kt_agent\src\data\낙산공원 성곽길.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\남산타워.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\경복궁.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\서울올림픽 경기장.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\청담대교.jpg",
#     r"C:\PythonProject\ai_kt_agent\src\data\코엑스.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\한옥마을_밤.png",
#     r"C:\PythonProject\ai_kt_agent\src\data\명동.png",
# ]

