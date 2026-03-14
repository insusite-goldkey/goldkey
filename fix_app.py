import re

# 1. 파일 읽기 (BOM 및 인코딩 처리)
try:
    with open('app.py', 'rb') as f:
        raw = f.read()
    text = raw.lstrip(b'\xef\xbb\xbf').decode('utf-8')
except Exception as e:
    print(f"파일 읽기 오류: {e}")
    exit()

lines = text.splitlines(keepends=True)

# 2. 새로운 헤더 정의 (5초 스플래시 포함)
NEW_HEADER = """import streamlit as st
import os as _os_top
import time as _time_top

if "initialized" not in st.session_state:
    st.session_state["initialized"] = False

_sb_state = "collapsed" if st.session_state.get("initialized") else "expanded"

st.set_page_config(
    page_title="goldkey_Ai_masters2026 마스터 AI",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state=_sb_state,
)

st.markdown(\"\"\"
    <style>
        [data-testid="stSidebar"] { display: block !important; visibility: visible !important; }
        .stApp [data-testid="stStatusWidget"] { visibility: hidden !important; }
    </style>
\"\"\", unsafe_allow_html=True)

if not st.session_state["initialized"]:
    _splash = st.empty()
    with _splash.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        _sc1, _sc2, _sc3 = st.columns([1, 2, 1])
        with _sc2:
            try:
                st.image("splash_mobile.jpg", use_container_width=True)
            except Exception:
                st.markdown("<div style='text-align:center;font-size:3rem;'>🏆</div>", unsafe_allow_html=True)
            st.info("🚀 **Goldkey_AI_Masters가 구동중! 최적의 환경을 준비하고 있습니다...**")

    _time_top.sleep(5)
    _splash.empty()
    st.session_state["initialized"] = True
    st.rerun()

"""

# 3. 수술 시작
# 기존 1~51번 줄 (0~50 인덱스) 제거
body = lines[51:]

# 중복된 4561~4599번 줄 (51번이 빠졌으므로 인덱스 시프트됨)
# 원본 4561번 줄 인덱스는 4560. 여기서 51을 빼면 4509
dup_start = 4560 - 51
dup_end = 4598 - 51

print(f"검증: 중복 시작줄 내용 -> {body[dup_start][:50]}")

# 중복 구간 삭제
final_body = body[:dup_start] + body[dup_end + 1:]

# 4. 합치기 및 저장
final_content = NEW_HEADER + "".join(final_body)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(final_content)

print("✅ 수술 성공! app.py가 깨끗하게 업데이트되었습니다.")