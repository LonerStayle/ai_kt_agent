import streamlit as st
import requests, os ,httpx
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    button[data-testid="stSidebarCollapseButton"] {display: none !important;}
    div[data-testid="stSidebarCollapseButton"] {display: none !important;}
    [data-testid="stSidebarNav"] {display: none;}

    
    /* 우측 상단 언어 선택 박스 위치 조정 */
    .lang-select {
        position: absolute;
        top: 15px;
        right: 20px;
        z-index: 100;
        background-color: #262730;
        padding: 6px 10px;
        border-radius: 8px;
        color: white;
    }
    </style>


"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# if "step1_result" not in st.session_state:
#     st.session_state.step1_result = {
#         "images": [
#             r"src\data\낙산공원 성곽길.png",
#             r"src\data\남산타워.png",
#             r"src\data\명동.png",
#         ],
#         "summary": "1일차: 남산타워 → 명동 → 낙산공원...(피그마 표시에서만 생략)...",
#         "answer": """
# # 케이팝 데몬헌터스 애니메이션 팬들을 위한 서울 여행 코스 ✨

# ## 최종 선택 지역: 경복궁(GYEONGGOKGUNG) & 코엑스(COEX)

# 애니메이션 '케이팝 데몬 헌터스'에서 주인공들의 전통문화 체험 장면이 등장한 바로 그 장소들로 구성된 최적의 한국 문화 탐험 루트입니다! 🏯🎵

# ### 추천 일정: 반나절(4시간 30분) 코스

# **[경복궁 → 인사동(도보 10분) → 북촌 한옥마을(도보 15분) → 삼청동(도보 5분) → 코엑스]**

# ---

# ## 1. 경복궁(GYEONGGOGUNG Palace) - 한국의 대표 궁 (체류 60분)

# * **간단 설명**: 조선왕조 최대 규모의 궁궐로, 애니메이션에서 저승사자가 전통 복장을 입고 등장하는 장면이 촬영된 곳! 화려한 근정전과 경회루는 K-컬처의 정수를 보여줍니다.

# [지도 열기: https://www.kh.or.kr/visit/location/location01.do] · ✅ 이동팁: 북촌 한옥마을과 도보 10분 거리

# ### 기념품 추천:

# 1. **한복 체험 대여** (경복궁 앞 한복거리) - 전통 의상 입고 애니메이션 속 주인공처럼 사진 촬영! [위치: 경복궁역 5번 출구에서 직진 50m, 매장지도링크]
# 2. **전통 부채 DIY 키트** (경복궁 내 기념품점) - 애니메이션에 나온 화려한 색감의 한국 전통 부채 만들기 체험 [온라인 공식몰: https://www.khmall.com/]

# ## 2. 인사동 - K-컬처의 중심지 (체류 30분)

# * **간단 설명**: 애니메이션에서 주인공들이 전통 문화를 체험하는 장면이 등장한 곳! 찻집과 공예품점, 골동품 상점이 가득한 한국 전통문화의 거리

# [지도 열기: https://www.visitinsadong.com/ko/] · 🚶‍♂️ 이동팁: 경복궁에서 도보 5분

# ### 기념품 추천:

# 1. **한글 캘리그라피 엽서** - 애니메이션 속 K-팝 가사를 한글로 적어보는 체험 [인사동 공예거리 내 한글캘리숍]
# 2. **전통 찻잔 세트** (인사동 다례원) - 한국 전통 차와 함께 즐기는 특별한 경험

# ## 3. 북촌 한옥마을 (체류 60분)

# * **간단 설명**: 애니메이션에서 전통 가옥과 정원이 촬영된 바로 그 장소! 조선시대 양반가의 생활공간을 현대적으로 재해석한 공간

# [지도 열기: https://www.visitbukchon.com/] · 🚶‍♂️ 이동팁: 인사동에서 도보 10분

# ### 기념품 추천:

# 1. **한지 공예품 세트** - 애니메이션에 나온 전통 문양이 들어간 한지 등, 문패 만들기 [북촌 한옥마을 내 한지공방]
# 2. **전통 다식 만들기 키트** (온라인 구매) [링크: https://www.koreanfestival.co.kr/]

# ## 4. 삼청동 문화거리 (체류 30분)

# * **간단 설명**: 애니메이션에서 K-팝 뮤직비디오 촬영지 같은 분위기의 현대적이면서도 전통이 살아있는 거리! 갤러리, 카페, 공예품점이 어우러진 공간

# [지도 열기: https://namu.wiki/w/%EB%B6%81%EC%B4%89%20%ED%95%98%EB%85%B8%EB%A7%88%EC%9D%84] · 🚶‍♂️ 이동팁: 북촌 한옥마을에서 도보 5 5분

# ### 기념품 추천:

# 1. **K-팝 데몬헌터스 공식 굿즈** (삼청동 카페/편집샵) - 애니메이션 캐릭터가 그려진 머그컵, 스티커 등 [위치: 삼청동 한옥마을 초입]
# 2. **전통주 세트** (삼청동 전통주 갤러리) - 한국의 술 문화 체험하기

# ## 5. 코엑스 COEX - K-컬처 쇼핑 성지 (체류 60분)

# * **간단 설명**: 애니메이션에서 현대적인 K-팝 콘서트 장면들이 촬영된 곳! 대형 쇼핑몰과 전시관이 모여있는 현대 한국문화의 중심지

# [지도 열기: https://www.coex.co.kr/] · 🚇 이동팁: 지하철 3호선 안국역 하차 후 도보 5분

# ### 기념품 추천:

# 1. **케이팝 데몬헌터스 공식 굿즈샵** (스타필드 코엑스몰) - 애니메이션 캐릭터가 그려진 머플러, 후드티 등 [위치: 스타필드 코엑스몰 지하 2층]
# 2. **K-POP 랜덤박스** (코엑스 지하 1층 K-POP 랜덤박스 매장) - 다양한 아이돌 상품이 랜덤으로 들어있는 선물상자

# ## 전체 경로 지도: https://goo.gl/maps/4xZjE3yN7R9V8tD98?ll=37.5540,126.9908

# ---

# ⚠️ **여행 팁/주의사항**:
# - 경복궁과 인사동은케이팝 데몬헌터스 팬들을 위한 서울 전통문화 탐방 코스!
# """,
#     }

# --- 우측 상단 언어 선택 ---
# st.markdown(f"<div class='lang-select'>KOR</div>", unsafe_allow_html=True)
st.markdown("""
    <style>
    /* 채팅 메시지가 추가될 때 희미→선명 효과 없애기 */
    div[data-testid="stChatMessage"] {
        opacity: 1 !important;
        transition: none !important;
        animation: none !important;
    }
    div[data-testid="stChatMessageContent"] {
        opacity: 1 !important;
        transition: none !important;
        animation: none !important;
    }
    </style>
""", unsafe_allow_html=True)



BASE_PATH = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parents[0]))
# --- 1단계 결과 표시 ---
if "step1_result" in st.session_state:
    print(st.session_state.step1_result)
    st.sidebar.header("📌 1단계 결과")
    st.sidebar.markdown(
        f"**[추천 루트 요약]**\n\n{st.session_state.step1_result['summary']}"
    )


    for img_path in st.session_state.step1_result["images"]:
        # Windows 경로(\) → 슬래시(/)로 변환 후 Path 객체로 만들기
        path = (BASE_PATH / Path(img_path.replace("\\", "/"))).resolve()

        if path.exists():
            # 1단계 결과에서 사이드바에서 이미지 폭 맞춤으로 수정
            with open(path, "rb") as f:
                st.sidebar.image(f.read(), use_column_width=True)


# --- 채팅 표시 ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": st.session_state.step1_result["answer"]}
    ]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("메세지를 입력하세요.."):

    # 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 어시스턴트 응답 표시 (스트리밍)
    with st.chat_message("assistant"):
        with st.spinner("생각 중... 🤔"):
            message_placeholder = st.empty()
            full_response = ""
    
            with httpx.stream(
                "POST",
                "http://localhost:8000/chat",
                params={"user_text": prompt},
                timeout=None,
            ) as r:
                for chunk in r.iter_text():
                    if chunk:
                        full_response += chunk
                        message_placeholder.markdown(full_response + "▌")
    
            message_placeholder.markdown(full_response)
            st.session_state.messages.append(
                {"role": "assistant", "content": full_response}
            )