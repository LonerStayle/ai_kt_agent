# run_app/pages/1_select_image.py
import streamlit as st
from pathlib import Path
import requests
from enum import Enum
from typing import List, Dict, Optional, Tuple

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
    """파일명(stem) -> SelectImage 매핑 테이블"""
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
    """단일 파일 경로 -> SelectImage (없으면 None)"""
    mapping = _file_to_enum_map()
    stem = Path(path).stem
    return mapping.get(stem)


def paths_to_enums(paths: List[str]) -> Tuple[List[SelectImage], List[str]]:
    """경로 리스트 -> (Enum 리스트, 실패 경로 리스트)"""
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

# -----------------------------
# CSS
# -----------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stAppViewContainer"] { background: #fff; color: #000; }

/* ✅ 사이드바 제거 */
[data-testid="stSidebar"] {display: none;}
[data-testid="stSidebarNav"] {display: none;}
section[data-testid="stSidebar"] {display: none !important;}

            
.top-bar {display:flex; justify-content:space-between; align-items:center; padding:8px 10px;}
.top-title {flex:1; text-align:center; font-family: Inter, sans-serif; font-size:24px; font-weight:700;}
.lang-label {font-family: Inter, sans-serif; font-size:16px; border:0.5px solid #000; border-radius:20px; padding:4px 12px;}

div.stButton > button:first-child {
    background-color: white !important;
    color: black !important;
    border: 1px solid #000 !important;
}
div.stButton > button:first-child:hover {
    background-color: #f0f0f0 !important;
    color: black !important;
}
</style>
<div class="top-bar">
    <div style="width:64px;"></div>
    <div class="top-title">궁금한 여행지를 선택하세요</div>
    <div class="lang-label">KOR</div>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<style>
/* ✅ 이미지 캡션 색상 강제 변경 */
[data-testid="stCaptionContainer"] p {
    color: black !important;
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 메인 그리드 (3열)
# -----------------------------
cols_per_row = 2
rows = (len(IMAGES) + cols_per_row - 1) // cols_per_row

for r in range(rows):
    cols = st.columns(cols_per_row, gap="large")
    for c in range(cols_per_row):
        i = r * cols_per_row + c
        if i >= len(IMAGES):
            continue
        path = IMAGES[i]
        is_sel = i in st.session_state.selected
        with cols[c]:
            # ✅ 이미지 꽉 차게
            st.image(str(path), use_column_width=True, caption=path.stem)

            # ✅ 버튼은 컬럼 폭 전체 차지
            btn_col = st.columns(1)[0]
            with btn_col:
                if st.button(("해제" if is_sel else "선택"), key=f"btn_{i}"):
                    with st.spinner("서버가 이미지를 처리 중입니다..."):  # ✅ 스피너 추가
                        if is_sel:
                            st.session_state.selected.remove(i)
                        else:
                            st.session_state.selected.add(i)

# -----------------------------
# 아래: 선택된 이미지
# -----------------------------
st.markdown("---")
st.markdown("<h3 style='color:black;'>선택한 여행지</h3>", unsafe_allow_html=True)

if st.session_state.selected:
    thumbs_per_row = 6
    selected_indices = sorted(st.session_state.selected)
    rows = (len(selected_indices) + thumbs_per_row - 1) // thumbs_per_row

    for r in range(rows):
        row_cols = st.columns(thumbs_per_row, gap="small")
        for c in range(thumbs_per_row):
            k = r * thumbs_per_row + c
            if k >= len(selected_indices):
                continue
            idx = selected_indices[k]
            p = IMAGES[idx]
            with row_cols[c]:
                st.image(str(p), width=120, caption=p.stem)
else:
    st.caption("아직 선택된 장소가 없습니다. 위의 이미지를 선택해보세요.")

# -----------------------------
# 선택 완료 버튼
# -----------------------------
btn_col = st.columns(1)[0]
with btn_col:
    if st.button("선택 완료", type="primary"):
        choose_images = [str(IMAGES[i]) for i in sorted(st.session_state.selected)]
        if choose_images:

            enums, failed = paths_to_enums(choose_images)
            if failed:
                st.warning("다음 항목은 Enum 매핑을 찾지 못했습니다:")
                st.write(failed)

            payload = {
                "lang": "ko",
                "selects": [e.value for e in enums]
            }

            try:
                url = "http://localhost:8000/send_place"
                with st.spinner("서버가 결과를 생성 중입니다..."):
                    res = requests.post(url, json=payload, timeout=(5, 600))
                    res.raise_for_status()
                    data = res.json()

                # 세션 저장
                st.session_state["step1_result"] = {
                    "images": choose_images,
                    "summary": data.get("summary"),
                    "answer": data.get("answer"),
                }

                st.switch_page("pages/2_chat.py")

            except Exception as e:
                st.error(f"API 호출 실패: {e}")
        else:
            st.warning("선택된 이미지가 없습니다.")
