import streamlit as st
import time

# ====== 속도만 여기서 조절 ======
DUR   = 1.8   # 한 줄 올라오는 시간(초)
DELAY = 0.9   # 줄 사이 시작 지연(초)
HOLD  = 0.8   # 마지막 줄 표시 후 머무는 시간(초)

# ====== 사이드바 숨김 + 튜토리얼 스타일 ======
st.markdown("""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarNav"] { display:none !important; }

.intro-wrap{
  position:fixed; inset:0; background:#000;
  display:flex; align-items:center; justify-content:center;
  z-index:9999; text-align:center; padding:0 24px;
}
.line{
  color:#fff; font-size:48px; font-weight:800; line-height:1.35;
  opacity:0; transform:translateY(60px);
  animation-name:slideUp; animation-timing-function:cubic-bezier(.2,.7,.2,1);
  animation-fill-mode:forwards;
}
@keyframes slideUp { to { transform:translateY(0); opacity:1; } }
</style>
""", unsafe_allow_html=True)

phrases = [
    "K-컬처에서 K-라이프까지, 한 번에",
    "여행은 지금,",
    "필요할 때 커리어·정착 가이드까지 자연스럽게."
]

# ====== 오버레이에 3줄 넣고, 끝나면 자동 이동 ======
html = "<div class='intro-wrap'><div>"
for i, p in enumerate(phrases):
    html += f"<div class='line' style='animation-duration:{DUR}s; animation-delay:{i*DELAY}s'>{p}</div>"
html += "</div></div>"
st.markdown(html, unsafe_allow_html=True)

# 전체 재생시간만큼 기다렸다가 다음 페이지로
total = (len(phrases)-1)*DELAY + DUR + HOLD
time.sleep(total)
st.switch_page("pages/1_select_image.py")


# --- 평소 버튼 (백업용) ---
if st.button("Go to Select Image Page"):
    st.switch_page("pages/1_select_image.py")

if st.button("Go to Chat Page"):
    st.switch_page("pages/2_chat.py")