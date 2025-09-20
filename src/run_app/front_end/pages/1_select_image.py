# run_app/pages/1_select_image.py
import streamlit as st
from pathlib import Path
import base64
from enum import Enum
from typing import List, Dict, Optional, Tuple
import requests

st.set_page_config(page_title="여행지 선택", layout="wide")

# =============================
# Enum 정의
# =============================
class SelectImage(str, Enum):
    GYEONGBOKGUNG = '경복궁'
    NAKSAN_WALL = '낙산공원 성곽길'
    NAMSAN_TOWER = '남산타워'
    OLYMPIC_STADIUM = '서울올림픽 경기장'
    COEX = '코엑스'
    BUKCHON_HANOK = '북촌 한옥마을'
    CHEONGDAM_BRIDGE = '청담대교'
    MYEONG_DONG = '명동'  


# =============================
# 경로 -> Enum 매핑 유틸 함수
# =============================
def _file_to_enum_map() -> Dict[str, SelectImage]:
    return {
        "경복궁": SelectImage.GYEONGBOKGUNG,
        "낙산공원 성곽길": SelectImage.NAKSAN_WALL,
        "남산타워": SelectImage.NAMSAN_TOWER,
        "서울올림픽 경기장": SelectImage.OLYMPIC_STADIUM,
        "코엑스": SelectImage.COEX,
        "북촌 한옥마을": SelectImage.BUKCHON_HANOK,
        "청담대교": SelectImage.CHEONGDAM_BRIDGE,
        "명동": SelectImage.MYEONG_DONG,
    }


def path_to_enum(path: str) -> Optional[SelectImage]:
    mapping = _file_to_enum_map()
    stem = Path(path).stem
    return mapping.get(stem)


def paths_to_enums(paths: List[str]) -> Tuple[List[SelectImage], List[str]]:
    enums: List[SelectImage] = []
    failed: List[str] = []
    for p in paths:
        e = path_to_enum(p)
        if e is None:
            failed.append(p)
        else:
            enums.append(e)
    return enums, failed

# =============================
# 썸네일 디렉터리
# =============================
THUMB_DIR = Path("src/data/thumb")
IMAGES = sorted(list(THUMB_DIR.glob("*.webp")))

if "selected" not in st.session_state:
    st.session_state.selected = set()


def image_to_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stAppViewContainer"] { background: #fff; color: #000; }

/* ✅ 전체 화면 배경색 */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #DBDFEA !important;
}

/* ✅ 사이드바 제거 */
[data-testid="stSidebar"] {display: none;}
[data-testid="stSidebarNav"] {display: none;}
section[data-testid="stSidebar"] {display: none !important;}

.block-container {
    padding-top: 2rem;   
    padding-bottom: 2rem;
}

/* 상단 타이틀바 */
.top-bar {display:flex; justify-content:space-between; align-items:center; padding:12px 10px;}
.top-title {flex:1; text-align:center; font-family: Inter, sans-serif; font-size:26px; font-weight:700; margin-bottom:30px;}
.lang-label {font-family: Inter, sans-serif; font-size:16px; border:0.5px solid #000; border-radius:20px; padding:4px 12px; margin-bottom:30px;}

/* 버튼 스타일 */
div.stButton {
    display: flex;
    justify-content: center;
    margin-top: 6px;
}
div.stButton > button {
    background-color: #007bff !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px 20px !important;
    font-size: 14px !important;
    font-weight: 600 !important;
    cursor: pointer;
}
div.stButton > button:hover {
    background-color: #0056b3 !important;
    color: white !important;
}
</style>
<div class="top-bar">
    <div style="width:64px;"></div>
    <div class="top-title">궁금한 여행지를 선택하세요</div>
    <div class="lang-label">KOR</div>
</div>
""", unsafe_allow_html=True)


# -----------------------------
# 메인 그리드 (3열)
# -----------------------------
cols_per_row = 3
rows = (len(IMAGES) + cols_per_row - 1) // cols_per_row

for r in range(rows):
    cols = st.columns(cols_per_row, gap="large")
    for c in range(cols_per_row):
        i = r * cols_per_row + c
        if i >= len(IMAGES):
            continue
        path = IMAGES[i]
        img_b64 = image_to_base64(path)
        is_selected = str(path) in st.session_state.selected

        with cols[c]:
            st.markdown(
                f"""
                <div style="text-align:center;">
                    <img src="data:image/webp;base64,{img_b64}" 
                        style="width:100%; height:260px; object-fit:cover; border-radius:8px;">
                    <p style="margin-top:6px; font-size:15px; color:black;">{path.stem}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            btn_label = "해제하기" if is_selected else "선택하기"
            btn_key = f"btn_{i}"

            if st.button(btn_label, key=btn_key):
                if is_selected:
                    st.session_state.selected.remove(str(path))
                    st.session_state.toast_msg = f"'{path.stem}' 선택이 해제되었습니다."
                else:
                    st.session_state.selected.add(str(path))
                    st.session_state.toast_msg = f"'{path.stem}' 여행지를 선택했습니다."

                st.experimental_rerun()
            # rerun 후에도 토스트 표시
        if "toast_msg" in st.session_state:
            st.toast(st.session_state.toast_msg)
            del st.session_state.toast_msg

    # ✅ 버튼 색상 커스터마이징 (id 기반으로만 지정)
            if is_selected:
    # 해제하기 상태 → 회색
                st.markdown(
                     f"""
                     <style>
                    div.stButton > button[kind="secondary"][aria-label="{btn_label}"] {{
                        background-color: #6c757d !important;  /* 회색 */
                        color: white !important;
                        border: none !important;
                    }}
                    div.stButton > button[kind="secondary"][aria-label="{btn_label}"]:hover {{
                        background-color: #5a6268 !important;  /* hover 시 진한 회색 */
                    }}
                    </style>
                    """,
                    unsafe_allow_html=True
                )
            else:
    # 선택하기 상태 → 파란색
             st.markdown(
              f"""
              <style>
                div.stButton > button[kind="secondary"][aria-label="{btn_label}"] {{
                    background-color: #007bff !important;  /* 파랑 */
                    color: white !important;
                    border: none !important;
                }}
                div.stButton > button[kind="secondary"][aria-label="{btn_label}"]:hover {{
                    background-color: #0056b3 !important;  /* hover 시 진한 파랑 */
                }}
                </style>
                """,
                unsafe_allow_html=True
            )



# -----------------------------
# 선택된 이미지 + 광고 배너
# -----------------------------
st.markdown("---")
col_left, col_right = st.columns([2, 3], gap="large")

with col_left:
    st.markdown("<h3 style='color:black; margin-bottom:20px;'>선택한 여행지</h3>", unsafe_allow_html=True)

    if st.session_state.selected:
        selected_paths = sorted(st.session_state.selected)

        # ✅ 모든 이미지를 한 번에 HTML로 합치기
        html_blocks = []
        for p in selected_paths:
            path_obj = Path(p)
            img_b64 = image_to_base64(path_obj)
            html_blocks.append(
                f"""
<div style="flex:0 0 auto; text-align:center;">
    <img src="data:image/webp;base64,{img_b64}" 
         style="width:160px; height:120px; object-fit:cover; border-radius:8px;">
    <p style="margin-top:4px; font-size:14px; color:black;">{path_obj.stem}</p>
</div>
"""
            )

        # ✅ 컨테이너에 한 번에 삽입 (가로 배치)
        st.markdown(
            f"""
<div style="display:flex; flex-wrap:wrap; gap:16px; padding:10px 0;">
    {"".join(html_blocks)}
</div>
""",
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            "<p style='color:#333333; font-size:15px;'>아직 선택된 장소가 없습니다. 위의 이미지를 클릭해보세요.</p>",
            unsafe_allow_html=True
        )


with col_right:
    ad_img_path = "src/data/banner/seoul_goods.png"
    ad_link = "https://english.visitseoul.net/partners-en/seoul-goods"
    if Path(ad_img_path).exists():
        ad_b64 = image_to_base64(Path(ad_img_path))
        st.markdown(
            f"""
            <a href="{ad_link}" target="_blank">
                <img src="data:image/png;base64,{ad_b64}" 
                    style="width:100%; height:auto; border-radius:12px; 
                           box-shadow:0 4px 12px rgba(0,0,0,0.3); cursor:pointer;">
            </a>
            """,
            unsafe_allow_html=True
        )


# -----------------------------
# 선택 완료 버튼
# -----------------------------
btn_col = st.columns(1)[0]

with btn_col:
    if st.button("선택 완료", type="primary"):
        choose_images = sorted(st.session_state.selected)
        if choose_images:

            enums, failed = paths_to_enums(choose_images)
            if failed:
                st.warning("다음 항목은 Enum 매핑을 찾지 못했습니다:")
                st.write(failed)

            payload = {"lang": "ko", "selects": [e.value for e in enums]}

            try:
                st.session_state["step1_payload"] = payload
                st.session_state["step1_images"] = choose_images
                from pathlib import Path
                st.switch_page(str(Path(__file__).parent / "0_waiting_video.py"))        

            except Exception as e:
                st.error(f"API 호출 실패: {e}")
        else:
            st.warning("선택된 이미지가 없습니다.")