import streamlit as st
import os, httpx, json, base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- 공통 UI 정리 ---
st.markdown("""
<style>
#MainMenu, footer, header {visibility:hidden;}
button[data-testid="stSidebarCollapseButton"],
div[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNav"]{display:none!important;}
/* 채팅 페이드 제거 */
div[data-testid="stChatMessage"],
div[data-testid="stChatMessageContent"]{
  opacity:1!important;transition:none!important;animation:none!important;
}
/* === 업로더를 아이콘 버튼처럼 === */
div[data-testid="stFileUploader"]{
  width:40px!important; height:40px!important;
  position:relative; overflow:hidden!important;
  border-radius:8px; background:#444;
  display:flex; align-items:center; justify-content:center;
}
div[data-testid="stFileUploader"]:hover{ background:#666; }
div[data-testid="stFileUploader"] section{ position:absolute; inset:0; opacity:0; }
div[data-testid="stFileUploader"]::before{
  content:"📷"; position:absolute; inset:0;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; color:#fff; pointer-events:none;
}
div[data-testid="stFileUploader"] input[type=file]{
  position:absolute; inset:0; opacity:0; cursor:pointer;
}
div[data-testid="stFileUploader"] span,
div[data-testid="stFileUploader"] small,
div[data-testid="stFileUploader"] [data-testid="stFileUploaderFileName"],
div[data-testid="stFileUploader"] .uploadedFile { display:none !important; }
.preview-title{ color:#bbb; font-size:13px; margin:0 0 6px 2px; }
</style>
""", unsafe_allow_html=True)

BASE_PATH = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[0]))
DATA_PATH = BASE_PATH / "src" / "data"

# --- 1단계 결과 표시 ---
if "step1_result" in st.session_state:
    st.sidebar.header("📌 1단계 결과")
    st.sidebar.markdown(
        f"**[추천 루트 요약]**\n\n{st.session_state.step1_result['summary']}"
    )
    for img_path in st.session_state.step1_result["images"]:
        path = (BASE_PATH / Path(img_path.replace("\\", "/"))).resolve()
        if path.exists():
            with open(path, "rb") as f:
                st.sidebar.image(f.read(), width=232)
    st.session_state.messages = [
        {"role": "assistant", "content": st.session_state.step1_result["answer"]}
    ]

# --- 메시지 초기화 ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 기존 대화 출력 ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 스크롤 anchor ---
scroll_anchor = st.empty()

# --- 업로드 미리보기 ---
preview_slot = st.empty()
if "uploaded_image" in st.session_state:
    with preview_slot.container():
        st.markdown("**첨부된 이미지 미리보기**")
        st.image(st.session_state["uploaded_image"])
        if st.button("✖️ 제거", key="remove_preview"):
            del st.session_state["uploaded_image"]
            preview_slot.empty()

# ===== 입력창 (맨 하단) =====
prompt = st.chat_input("메세지를 입력하세요..")  # ✅ 항상 하단에 위치

# ===== 업로드 버튼 (입력창 바로 아래로 이동) =====
uploaded_file = st.file_uploader(
    "이미지 업로드", type=["png","jpg","jpeg"],
    label_visibility="collapsed", key="chat_uploader_bottom"
)
if uploaded_file:
    st.session_state["uploaded_image"] = uploaded_file

# --- 입력 처리 ---
if prompt:
    user_msg = {"role": "user", "content": prompt}
    if "uploaded_image" in st.session_state:
        user_msg["image"] = st.session_state["uploaded_image"]

    st.session_state.messages.append(user_msg)

    # 유저 메시지 출력
    with st.chat_message("user"):
        st.markdown(prompt)
        if user_msg.get("image"):
            st.image(user_msg["image"])

    # 어시스턴트 응답
    with st.chat_message("assistant"):
        with st.spinner("생각 중... 🤔"):
            message_placeholder = st.empty()
            full_response = ""

            files = None
            uf = st.session_state.get("uploaded_image", None)
            if uf:
                try: uf.seek(0)
                except: pass
                files = {"image": (uf.name, uf, uf.type or "application/octet-stream")}

            with httpx.stream(
                "POST",
                "http://localhost:8000/chat",
                data={"user_text": prompt},
                files=files,
                timeout=None,
            ) as r:
                for chunk in r.iter_text():
                    if not chunk: continue
                    try:
                        data = json.loads(chunk)
                        if data.get("type") == "images":
                            st.markdown("""
                            <style>
                            .image-grid{display:flex;flex-wrap:wrap;gap:12px;}
                            .image-grid img{width:180px;height:auto;border-radius:8px;}
                            </style>
                            """, unsafe_allow_html=True)
                            html = '<div class="image-grid">'
                            for p in data["content"]:
                                with open(str((DATA_PATH / p)), "rb") as f:
                                    b64 = base64.b64encode(f.read()).decode("utf-8")
                                    html += f'<img src="data:image/png;base64,{b64}" />'
                            html += '</div>'
                            st.markdown(html, unsafe_allow_html=True)
                        else:
                            full_response += json.dumps(data, ensure_ascii=False)
                            message_placeholder.markdown(full_response + "▌")
                    except Exception:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
                        continue

            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role":"assistant","content":full_response})

    # ✅ 요청 끝난 뒤 초기화
    if "uploaded_image" in st.session_state:
        del st.session_state["uploaded_image"]
        preview_slot.empty()
    
    # ✅ 스크롤 최하단 이동
    scroll_anchor.markdown("<div id='scroll-to'></div>", unsafe_allow_html=True)
    st.markdown(
        "<script>window.scrollTo(0, document.body.scrollHeight);</script>",
        unsafe_allow_html=True,
    )
