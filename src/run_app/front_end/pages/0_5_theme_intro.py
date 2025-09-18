import streamlit as st
from pathlib import Path

st.set_page_config(page_title="테마 선택", layout="wide")

# ✅ 사이드바 감추기
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {display: none;}
        [data-testid="stSidebarNav"] {display: none;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

# ✅ CSS 스타일
st.markdown(
    """
    <style>
    .theme-img {
        border-radius: 12px;
        max-height: 300px;
        object-fit: cover;
    }
    .desc-text p {
        font-size: 16px;
        line-height: 1.6;
        text-align: justify;
        margin-bottom: 12px;
    }
    .center-button {
        display: flex;
        justify-content: center;
        margin-top: 15px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown("<h2 style='text-align:center;'>테마 기반 여행지 선택</h2>", unsafe_allow_html=True)

# ✅ static/images 폴더 기준 경로 잡기
BASE_DIR = Path(__file__).resolve().parent.parent  # -> front_end
STATIC_DIR = BASE_DIR.parent / "static" / "images"  # -> run_app/static/images

themes = {
    "케이팝 데몬헌터스": {
        "img": STATIC_DIR / "kdh.webp",
        "desc": [
            "세계가 열광한 K-팝의 미래적 세계관을 여행으로 다시 만납니다.",
            "경복궁의 고즈넉한 전통미와 명동의 화려한 거리, 코엑스와 올림픽 경기장의 뜨거운 열기까지 —",
            "아이돌 무대의 환상과 한국의 랜드마크가 어우러져, 팬이라면 누구나 꿈꾸던 특별한 여정이 펼쳐집니다."
        ]
    },
    "오징어게임": {
        "img": STATIC_DIR / "squid_game.jpg",
        "desc": [
            "전 세계를 사로잡은 오징어게임의 긴장감과 상징성을 현실 속 여행으로 이어갑니다.",
            "안산 대부도의 해솔길에서 느껴지는 드라마 속 서바이벌의 긴장감,",
            "서울 도심의 거리에서 마주하는 한국적 일상, 그리고 촬영 세트가 재현된 공간까지 —",
            "스크린 속 장면이 당신의 발걸음과 함께 살아납니다."
        ]
    }
}

# ✅ 이미지 + 설명 + 버튼
for theme, info in themes.items():
    col1, col2 = st.columns([2, 1])

    with col1:
        if Path(info["img"]).exists():
            st.image(str(info["img"]), use_container_width=True, output_format="auto")
        else:
            st.error(f"이미지 없음: {info['img']}")

    with col2:
        st.subheader(theme)

        # 여러 문단 출력 (HTML 적용)
        desc_html = "<div class='desc-text'>" + "".join([f"<p>{line}</p>" for line in info["desc"]]) + "</div>"
        st.markdown(desc_html, unsafe_allow_html=True)

        # ✅ 버튼 → 설명 밑에, 가운데 정렬 + 페이지 이동
        if st.button(f"{theme} 선택하기", key=theme):
            st.session_state["selected_theme"] = theme
            st.switch_page("pages/1_select_image.py")

    st.markdown("---")
