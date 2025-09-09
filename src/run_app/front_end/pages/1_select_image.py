# run_app/pages/1_select_image.py
import streamlit as st
from pathlib import Path
import requests
from enum import Enum
from typing import List, Dict, Optional, Tuple

st.set_page_config(page_title="여행지 선택", layout="wide")

# TODO 경로로 불러오면 에러나서 일단 중복 => 추후 기존 ENUM 불러오는 것으로 변경
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
    stem = Path(path).stem  # "src/data/thumb/경복궁.webp" -> "경복궁"
    return mapping.get(stem)


def paths_to_enums(paths: List[str]) -> Tuple[List[SelectImage], List[str]]:
    """
    경로 리스트 -> (Enum 리스트, 매핑 실패 경로 리스트)
    실패 항목을 함께 반환하여 UI 경고용으로 활용
    """
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
# 썸네일 디렉터리 (make_thumbs.py로 미리 생성)
# =============================
THUMB_DIR = Path("src/data/thumb")
IMAGES = sorted(list(THUMB_DIR.glob("*.webp")))  # 파일명순 정렬

if "selected" not in st.session_state:
    st.session_state.selected = set()

# -----------------------------
# CSS (버튼: 흰색)
# -----------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
[data-testid="stAppViewContainer"] { background: #fff; color: #000; }

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

# -----------------------------
# 메인 그리드(3열): 큰 썸네일 + 선택/해제 버튼
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
        is_sel = i in st.session_state.selected
        with cols[c]:
            st.image(str(path), width="stretch", caption=path.stem)
            if st.button(("해제" if is_sel else "선택"), key=f"btn_{i}", width="stretch"):
                if is_sel:
                    st.session_state.selected.remove(i)
                else:
                    st.session_state.selected.add(i)

# -----------------------------
# 아래: 선택된 이미지 (작게 표시) + 선택 완료 버튼
# -----------------------------
st.markdown("---")
st.write("### 선택한 여행지")

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
                # 선택된 썸네일은 작게만 보여줌
                st.image(str(p), width=120, caption=p.stem)
else:
    st.caption("아직 선택된 장소가 없습니다. 위의 이미지를 선택해보세요.")

# -----------------------------
# 선택 완료 버튼
# -----------------------------
if st.button("선택 완료", type="primary", width="stretch"):
    choose_images = [str(IMAGES[i]) for i in sorted(st.session_state.selected)]
    if choose_images:
        st.success(f"{len(choose_images)}개 선택됨")
        st.json({"images": choose_images})
        
        # 경로 -> Enum 매핑
        enums, failed = paths_to_enums(choose_images)
        if failed:
            st.warning("다음 항목은 Enum 매핑을 찾지 못했습니다. 파일명(stem)을 확인하세요:")
            st.write(failed)

        # API 호출 payload 구성
        # FastAPI가 PlaceRequest(selects: List[SelectImage])를 받으므로
        # Enum의 value(한글 값) 리스트로 전송
        payload = {
            "lang": "ko",  # or "en"
            "selects": [e.value for e in enums]
        }

        try:
            url = "http://localhost:8000/send_place"  # FastAPI 서버 주소
            with st.spinner("서버가 결과를 생성 중입니다..."):
                res = requests.post(url, json=payload, timeout=(5, 600)) # 응답대기 넉넉하게 10분
                res.raise_for_status()
                data = res.json()
            
            print(res)
            res.raise_for_status()
            data = res.json()
            
            # 세션에 저장 (다음 페이지에서 활용)
            st.session_state["step1_result"] = {
                "images": choose_images,                 # 원본 경로
                "summary": data.get("summary"),
                "answer": data.get("answer"),
            }

            # 다음 페이지로 이동
            st.switch_page("pages/2_chat.py")

        except Exception as e:
            st.error(f"API 호출 실패: {e}")

    else:
        st.warning("선택된 이미지가 없습니다.")