# run_app/pages/waiting_video.py
import streamlit as st
import requests
import time

st.set_page_config(page_title="영상 재생 중...", layout="wide")

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

/* ✅ iframe(영상) 중앙 정렬 */
iframe {
    display: block;
    margin-left: auto;
    margin-right: auto;
    border-radius: 10px;  /* 모서리 둥글게 */
    box-shadow: 0 4px 16px rgba(0,0,0,0.25); /* 그림자 */
}
</style>
""", unsafe_allow_html=True)

# ✅ 유튜브 영상 자동재생 (특정 초에서 시작)
    
# u4wuTP7McEY - 과천공연예술축제 / start=0
# kXrUhsshEcM - 영천가을축제 / start=0
# AMR-7YU3nXg - 군산시간여행축제 / start=0
    
# 원래 URL을 embed용으로 변환
video_id = 'u4wuTP7McEY'
start_sec = 0  # 원하는 시작 초 단위
embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1&start={start_sec}"

st.markdown(
    f"""
    <iframe width="900" height="500"
            src="{embed_url}"
            frameborder="0"
            allow="autoplay; encrypted-media"
            allowfullscreen>
    </iframe>
    """,
    unsafe_allow_html=True
)

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
