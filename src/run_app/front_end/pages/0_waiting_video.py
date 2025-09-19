# run_app/pages/waiting_video.py
import streamlit as st
import requests
import time
import base64
import random
import os
from pathlib import Path
from dotenv import load_dotenv

st.set_page_config(page_title="영상 재생 중...", layout="wide")

load_dotenv()

video_dir = Path("C:/ai_kt_agent/src/data")

st.markdown("<h3>AI 서버가 응답을 생성 중입니다... 잠시만 기다려 주세요!</h3>", unsafe_allow_html=True)

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
/* ✅ 사이드바 제거 */
[data-testid="stSidebar"] {display: none;}
[data-testid="stSidebarNav"] {display: none;}
section[data-testid="stSidebar"] {display: none !important;}

/* ✅ 텍스트 중앙 정렬 */
h3 {
    text-align: center;
    font-family: Inter, sans-serif;
    font-size: 24px;
    margin-top: 20px;
}

/* ✅ video 중앙 정렬 & 크기 조정 */
video {
    display: block;
    margin-left: auto;
    margin-right: auto;
    border-radius: 12px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    width: 95% !important;   /* 화면 거의 다 차게 */
    height: auto !important;
}
</style>
""", unsafe_allow_html=True)

video_files = list(video_dir.glob("*.mp4"))
if video_files:
    chosen_video = random.choice(video_files)   # 무작위 선택
    video_bytes = chosen_video.read_bytes()
    video_base64 = base64.b64encode(video_bytes).decode("utf-8")

    st.markdown(
        f"""
        <video autoplay playsinline loop>
            <source src="data:video/mp4;base64,{video_base64}" type="video/mp4">
        </video>

        <script>
            const video = document.getElementById('bgVideo');
            video.volume = 0.1;  // 🔊 음량을 10%로 설정
        </script>
        """,
        unsafe_allow_html=True
    )
else:
    st.error(f"❌ 영상 파일을 찾을 수 없습니다: {video_dir}")

# ✅ 서버 응답 대기
if "step1_payload" in st.session_state:
    payload = st.session_state["step1_payload"]
    choose_images = st.session_state.get("step1_images", [])

    try:
        url = "http://localhost:8000/send_place"
        with st.spinner(""):
            res = requests.post(url, json=payload)
            res.raise_for_status()
            data = res.json()

        # ✅ 세션 저장
        st.session_state["step1_result"] = {
            "images": choose_images,
            "summary": data.get("summary"),
            "answer": data.get("answer"),
        }

        # ✅ 자동으로 다음 페이지 이동
        time.sleep(1)  # 영상 잠깐 보여주고 넘어가기 (선택)
        st.switch_page("pages/2_chat_goods.py")

    except Exception as e:
        st.error(f"API 호출 실패: {e}")
else:
    st.warning("API 요청 데이터가 없습니다.")