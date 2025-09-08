# app.py
import streamlit as st
from streamlit_extras.st_clickable_images import clickable_images
from pathlib import Path

# -----------------------------
# 기본 설정 & 상태
# -----------------------------
st.set_page_config(page_title="Travel Picker", layout="wide")

def ss_init():
    ss = st.session_state
    ss.setdefault("lang", "ENG")                # ENG or KOR
    ss.setdefault("show_lang_modal", False)
    ss.setdefault("picked_idx", None)           # 현재 선택 인덱스
    ss.setdefault("picked_history", [])         # 선택 히스토리(썸네일용)

ss_init()

# 데모용 이미지 (로컬/URL 아무거나 넣어도 됨)
# 실제 앱에서는 프로젝트 내 static 경로나 CDN URL 사용 권장
IMG_DIR = Path(__file__).parent / "images"
IMG_DIR.mkdir(exist_ok=True)
# 샘플 URL(임시). 실제 이미지로 교체 가능
images = [
    "https://picsum.photos/id/1011/640/360",
    "https://picsum.photos/id/1015/640/360",
    "https://picsum.photos/id/1036/640/360",
    "https://picsum.photos/id/1041/640/360",
    "https://picsum.photos/id/1050/640/360",
    "https://picsum.photos/id/1057/640/360",
    "https://picsum.photos/id/1069/640/360",
    "https://picsum.photos/id/1074/640/360",
    "https://picsum.photos/id/1084/640/360",
]

# -----------------------------
# 언어 문자열
# -----------------------------
STR = {
    "ENG": {
        "title": "Pick a destination you’re curious about",
        "select_placeholder": "Select a photo",
        "confirm": "Confirm",
        "lang_badge": "ENG",
        "modal_title": "Choose language",
        "kor": "한국어",
        "eng": "English",
    },
    "KOR": {
        "title": "궁금했던 여행지를 선택해주세요",
        "select_placeholder": "사진을 선택하세요",
        "confirm": "확인",
        "lang_badge": "KOR",
        "modal_title": "언어 선택",
        "kor": "한국어",
        "eng": "English",
    },
}

# -----------------------------
# 스타일 (스크린샷과 유사한 느낌)
# -----------------------------
st.markdown(
    """
    <style>
    /* 전체 배경 어둡게 */
    [data-testid="stAppViewContainer"] {
        background-color: #1f1f1f;
    }
    /* 카드 */
    .picker-card {
        background: #ffffff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        padding: 12px 12px 8px 12px;
        border: 1px solid #eaeaea;
    }
    .topbar {
        display:flex; align-items:center; justify-content:center;
        padding: 4px 4px 8px 4px;
        position: relative;
    }
    .title {
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, 'Noto Sans', sans-serif;
        font-weight: 700;
        font-size: 16px;
        color: #222;
        text-align: center;
        line-height: 1.2;
    }
    .lang-badge {
        position:absolute; right:4px; top:0;
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #cfd3d9;
        background:#fff;
        color:#333; font-size:12px; font-weight:600;
        cursor: pointer;
    }
    /* 이미지 그리드(3 x 3) */
    .grid {
        display:grid; grid-template-columns: repeat(3, 1fr);
        gap: 8px; margin-top: 6px;
    }
    /* clickable_images 내부 img 사이 간격 보정 */
    .grid img { border-radius: 6px; }
    /* 하단 바 */
    .bottombar {
        margin-top: 10px;
        background: #eef2f7;
        border-radius: 8px;
        padding: 10px;
        display:flex; align-items:center; justify-content:space-between;
        gap: 8px;
    }
    .placeholder {
        color:#6b7280; font-size: 13px;
    }
    .thumbs {
        display:flex; gap:6px; align-items:center; overflow-x:auto;
        max-width: 65%;
    }
    .thumbs img { width:62px; height:38px; object-fit:cover; border-radius:6px; border:1px solid #dfe3ea; }
    .confirm-btn[disabled] {
        opacity: 0.55;
        cursor: not-allowed;
    }
    .section-title {
        color:#d1d5db; font-weight:700; font-size:22px; margin: 8px 0 10px 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------
# 상단 섹션 제목 (예시로 ENG. 여행지 선택)
# -----------------------------
st.markdown(f"<div class='section-title'>{st.session_state['lang']}. 여행지 선택</div>", unsafe_allow_html=True)

# -----------------------------
# 카드 렌더
# -----------------------------
with st.container():
    st.markdown("<div class='picker-card'>", unsafe_allow_html=True)

    # Topbar: Title + Lang Badge (우측)
    with st.container():
        st.markdown(
            f"""
            <div class='topbar'>
              <div class='title'>{STR[st.session_state['lang']]['title']}</div>
              <button class='lang-badge' onclick="window.parent.postMessage({{'type':'lang_modal'}}, '*')">
                {STR[st.session_state['lang']]['lang_badge']}
              </button>
            </div>""",
            unsafe_allow_html=True,
        )
        # 버튼 클릭을 Python으로 전달: Streamlit의 CustomEvent 사용
        # NOTE: streamlit 1.38+ 에서 지원되는 postMessage 훅. 아래 js_listener가 세션상태를 바꿔줌.
        st.components.v1.html(
            """
            <script>
            window.addEventListener("message", (event) => {
                if (event.data && event.data.type === "lang_modal") {
                    const streamlitSendMessage = window.parent.postMessage || window.top.postMessage;
                    streamlitSendMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: "open"}, "*");
                }
            });
            </script>
            """,
            height=0,
        )
        # 위에서 postMessage 받은 값을 파이썬으로 변환
        open_val = st.experimental_get_query_params().get("_lang_open", None)  # 안전장치
        # 간단한 토글 버튼으로 대체
        # streamlit JS-hook 없이도 아래 버튼으로 모달 오픈 가능:
        open_modal = st.button(STR[st.session_state["lang"]]["lang_badge"], key="open_lang_modal_btn", help="Change language", use_container_width=False)
        if open_modal:
            st.session_state.show_lang_modal = True

    # Image Grid
    st.markdown("<div class='grid'>", unsafe_allow_html=True)
    clicked = clickable_images(
        images,
        titles=[f"#{i}" for i in range(len(images))],
        div_style={"display": "grid", "gridTemplateColumns": "repeat(3, 1fr)", "gap": "8px"},
        img_style={"border-radius": "6px", "height": "120px", "object-fit": "cover"},
        key="img_grid",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # 클릭 처리
    if clicked > -1:
        st.session_state.picked_idx = clicked
        # 히스토리 관리(중복 제거, 최근 6장 유지)
        if clicked not in st.session_state.picked_history:
            st.session_state.picked_history.insert(0, clicked)
            st.session_state.picked_history = st.session_state.picked_history[:6]

    # Bottom bar
    st.markdown("<div class='bottombar'>", unsafe_allow_html=True)
    left = st.container()
    right = st.container()

    # 왼쪽: 플레이스홀더/썸네일
    with left:
        if st.session_state.picked_idx is None:
            st.markdown(f"<div class='placeholder'>{STR[st.session_state['lang']]['select_placeholder']}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='thumbs'>", unsafe_allow_html=True)
            for idx in st.session_state.picked_history:
                st.image(images[idx], use_column_width=False)
            st.markdown("</div>", unsafe_allow_html=True)

    # 오른쪽: Confirm 버튼
    with right:
        is_disabled = st.session_state.picked_idx is None
        confirm = st.button(
            STR[st.session_state["lang"]]["confirm"],
            key="confirm_btn",
            disabled=is_disabled,
        )
        if confirm:
            st.success(f"Selected index: {st.session_state.picked_idx}")

    st.markdown("</div>", unsafe_allow_html=True)  # end .bottombar
    st.markdown("</div>", unsafe_allow_html=True)  # end .picker-card

# -----------------------------
# 언어 선택 모달
# -----------------------------
if st.session_state.show_lang_modal:
    with st.modal(STR[st.session_state["lang"]]["modal_title"], key="lang_modal", max_width=420):
        st.write("")  # spacing
        col1, col2 = st.columns(2)
        with col1:
            if st.button(STR["KOR"]["kor"], use_container_width=True):
                st.session_state.lang = "KOR"
                st.session_state.show_lang_modal = False
                st.rerun()
        with col2:
            if st.button(STR["ENG"]["eng"], use_container_width=True):
                st.session_state.lang = "ENG"
                st.session_state.show_lang_modal = False
                st.rerun()
        st.write("")
        st.button("Close" if st.session_state.lang == "ENG" else "닫기", on_click=lambda: st.session_state.update({"show_lang_modal": False}), use_container_width=True)

# import streamlit as st
# from pathlib import Path
# st.set_page_config(layout="wide")

# page_bg = """
# <style>
# #MainMenu {visibility: hidden;}
# footer {visibility: hidden;}
# header {visibility: hidden;}
# [data-testid="stAppViewContainer"] {
#     background-color: white;
#     color: black;
# }
# [data-testid="stHeader"] {
#     background-color: white;
# }
# [data-testid="stSidebar"], [data-testid="stSidebarNav"] {
#     display: none; /* 사이드바 숨기고 싶으면 */
# }

# .top-bar {
#     display: flex;
#     justify-content: space-between;
#     align-items: center;
#     padding: 8px 16px;
# }
# .top-title {
#     flex: 1;
#     text-align: center;
#     font-family: 'Inter', sans-serif;
#     font-size: 24px;
#     font-weight: 700;  /* Bold */
# }
# .lang-label {
#     font-family: 'Inter', sans-serif;
#     font-size: 18px;
#     font-weight: 400;  /* Regular */
#     border: 0.5px solid #000000;
#     border-radius: 20px;
#     padding: 4px 12px;
# }

# /* 모달 기본 숨김 */
# .modal {
#     display: none; 
#     position: fixed;
#     z-index: 1000;
#     left: 0;
#     top: 0;
#     width: 100%;
#     height: 100%;
#     overflow: auto;
#     background-color: rgba(0,0,0,0.4); /* 반투명 배경 */
# }

# /* 모달 콘텐츠 */
# .modal-content {
#     background-color: #fff;
#     margin: 15% auto;
#     padding: 20px;
#     border-radius: 12px;
#     width: 300px;
#     font-family: 'Inter', sans-serif;
#     text-align: center;
#     box-shadow: 0 5px 15px rgba(0,0,0,0.3);
# }

# </style>
# """
# st.markdown(page_bg, unsafe_allow_html=True)
# st.markdown(
#     """
#     <div class="top-bar">
#         <div class="top-title">궁금한 여행지를 선택하세요</div>
#         <div class="lang-label">KOR</div>
#     </div>
#     """,
#     unsafe_allow_html=True,
# )



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

