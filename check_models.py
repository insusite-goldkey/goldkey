import streamlit as st
import google.generativeai as genai

st.title("🔍 내 API Key로 쓸 수 있는 모델 찾기")

api_key = st.text_input("API Key 입력", type="password")

if st.button("확인하기"):
    try:
        genai.configure(api_key=api_key)
        st.write("### ✅ 사용 가능한 모델 목록:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                st.success(f"- {m.name}")
    except Exception as e:
        st.error(f"오류 발생: {e}")
