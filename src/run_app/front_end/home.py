

import streamlit as st
# --- 사이드바 숨기기 CSS ---
hide_sidebar = """
    <style>
        [data-testid="stSidebar"] {
            display: none;
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)


if st.button("Go to Select Image Page"):
    st.switch_page("pages/1_select_image.py")

if st.button("Go to Chat Page"):
    st.switch_page("pages/2_chat.py")