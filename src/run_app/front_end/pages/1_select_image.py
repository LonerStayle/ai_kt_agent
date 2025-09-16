# run_app/pages/1_select_image.py
import streamlit as st
from pathlib import Path
import base64

st.set_page_config(page_title="여행지 선택", layout="wide")

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

/* 버튼 스타일 (중앙, 짧게) */
div.stButton {
    display: flex;
    justify-content: center;   /* ✅ 항상 중앙 정렬 */
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
    margin-left: 330px; /*버튼 center화 하는 다른 css가 적용되지 않아서 값으로 미룸 - 디바이스별 확인 필요*/
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
# 메인 그리드 (고정 3열)
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
            # 이미지 + 캡션
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

            # 버튼 (중앙, 짧게)
            if st.button("해제하기" if is_selected else "선택하기", key=f"btn_{i}"):
                if is_selected:
                    st.session_state.selected.remove(str(path))
                else:
                    st.session_state.selected.add(str(path))


# -----------------------------
# 아래: 선택된 이미지
# -----------------------------
st.markdown("---")
st.markdown("<h3 style='color:black; margin-bottom:20px;'>선택한 여행지</h3>", unsafe_allow_html=True)
st.markdown("---")

if st.session_state.selected:
    thumbs_per_row = 6
    selected_indices = [
        i for i, p in enumerate(IMAGES) if str(p) in st.session_state.selected
    ]
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
                st.image(str(p), width=140, caption=p.stem)
else:
    st.caption("아직 선택된 장소가 없습니다. 위의 이미지를 클릭해보세요.")
