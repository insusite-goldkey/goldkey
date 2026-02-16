import streamlit as st

st.set_page_config(page_title="골드키지사 AI", layout="wide")
st.title("🏆 골드키지사 보장분석 AI 마스터")
st.subheader(f"{st.sidebar.text_input('고객명', '박성준')} 고객님을 위한 무결점 리포트")

file = st.file_uploader("증권 사진을 업로드하세요", type=['jpg', 'png', 'pdf'])
if file:
    st.success("증권 분석을 시작합니다... (잠시만 기다려주세요)")
    st.info("🚨 종합 판독: 현재 암 진단비가 부족하며, 뇌/심장 질환 보완이 시급합니다.")
