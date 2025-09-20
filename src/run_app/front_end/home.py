import streamlit as st
import time
from pathlib import Path
import base64

# ====== 설정 ======
DUR   = 1.8
DELAY = 0.9
HOLD  = 0.8

# ====== 배경 이미지 base64로 변환 ======
BG_PATH = Path("src/data/thumb/home.png")  # 실제 이미지 경로
def get_base64_of_image(img_path: Path) -> str:
    with open(img_path, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()

bg_img_base64 = get_base64_of_image(BG_PATH)
import streamlit as st

st.markdown("""
    <style>
    /* 상단 상태바(Deploy, Running 등) 숨기기 */
    header[data-testid="stHeader"] {display: none !important;}
    div[data-testid="stStatusWidget"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# ====== 스타일 적용 ======
st.markdown(f"""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarNav"] {{ display:none !important; }}

.intro-wrap {{
  position:fixed; inset:0;
  background: url("data:image/png;base64,{bg_img_base64}") no-repeat center center;
  background-size: cover;
  display:flex; align-items:center; justify-content:center;
  z-index:9999; text-align:center; padding:0 24px;
}}

.intro-overlay {{
  position:absolute; inset:0; background:rgba(0,0,0,0.55);
}}

.line {{
  position:relative;
  color:#fff; font-size:52px; font-weight:800; line-height:1.35;
  opacity:0; transform:translateY(60px);
  animation-name:slideUp; animation-timing-function:cubic-bezier(.2,.7,.2,1);
  animation-fill-mode:forwards;
}}

@keyframes slideUp {{
  to {{ transform:translateY(0); opacity:1; }}
}}
</style>
""", unsafe_allow_html=True)

# ====== 문구 ======
phrases = [
    "K-컬처에서 K-라이프까지, 한 번에",
    "여행은 지금,",
    "필요할 때 커리어·정착 가이드까지 자연스럽게."
]

html = "<div class='intro-wrap'><div class='intro-overlay'></div><div>"
for i, p in enumerate(phrases):
    html += f"<div class='line' style='animation-duration:{DUR}s; animation-delay:{i*DELAY}s'>{p}</div>"
html += "</div></div>"
st.markdown(html, unsafe_allow_html=True)

# ====== 페이지 전환 ======
total = (len(phrases)-1)*DELAY + DUR + HOLD
time.sleep(total)
st.switch_page(str(Path(__file__).parent / "pages" /"0_5_theme_intro.py"))

