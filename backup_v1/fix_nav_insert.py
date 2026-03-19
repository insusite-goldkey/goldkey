"""
[ID-000-NAV] 로그인 후 사이드바 블록 삽입
- if _is_auth_now: 조건으로 if not _is_auth_now: 바로 앞에 삽입
- 기존 with st.sidebar:(28685) 내 _open_sidebar pop 제거 (중복 방지)
"""

with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    lines = f.readlines()

print(f"원본 총 줄 수: {len(lines)}")

# 삽입 위치: idx 28474 = line 28475 "    if not _is_auth_now:\n"
INSERT_IDX = 28474
print("삽입 전:", repr(lines[INSERT_IDX-1][:60]))
print("삽입 위치:", repr(lines[INSERT_IDX][:60]))

NEW_BLOCK = (
    "    # ── [ID-000-NAV] 로그인 후 사이드바 — 항상-실행 블록 ─────────────────────\n"
    "    # 기존 with st.sidebar: 가 if not _is_auth_now: 안에만 있어 로그인 후 미렌더\n"
    "    # 수정: if _is_auth_now 일 때 별도 with st.sidebar: 로 항상 렌더 보장\n"
    "    if _is_auth_now:\n"
    "        with st.sidebar:\n"
    "            render_goldkey_sidebar()\n"
    "            # 사이드바 열기 JS (_open_sidebar 플래그 소비)\n"
    "            if st.session_state.pop('_open_sidebar', False):\n"
    "                import streamlit.components.v1 as _nav_cmp\n"
    "                _nav_cmp.html(\n"
    "                    '<script>(function(){'\n"
    "                    'function t(){try{var p=window.parent.document;'\n"
    "                    'var s=[\\'[data-testid=\"collapsedControl\"] button\\','\n"
    "                    '\\'button[aria-label=\"Open sidebar\"]\\'];'\n"
    "                    'for(var i=0;i<s.length;i++){var b=p.querySelector(s[i]);if(b){b.click();return;}}'\n"
    "                    '}catch(e){}}'\n"
    "                    'setTimeout(t,200);setTimeout(t,700);setTimeout(t,1500);'\n"
    "                    '})();</script>',\n"
    "                    height=0,\n"
    "                )\n"
    "            # 로그인 후 사용자 카드\n"
    "            _nav_uname = st.session_state.get('user_name','') or st.session_state.get('user_id','마스터')\n"
    "            st.markdown(\n"
    "                f'<div style=\"background:linear-gradient(135deg,#4facfe,#00f2fe);'\n"
    "                'border-radius:12px;padding:10px;margin-bottom:6px;text-align:center;\">'\n"
    "                '<div style=\"font-size:1.0rem;font-weight:800;color:#0a1628;\">Goldkey_AI_Masters2026</div>'\n"
    "                f'<div style=\"font-size:0.78rem;color:#0d2344;\">👤 {_nav_uname} 마스터</div>'\n"
    "                '</div>',\n"
    "                unsafe_allow_html=True,\n"
    "            )\n"
    "            st.markdown('---')\n"
    "            # 브랜딩 정보\n"
    "            _nav_co = st.text_input('🏢 회사명', value=st.session_state.get('gp200_company',''),\n"
    "                placeholder='예: 골드키지사', key='_nav_co', max_chars=60)\n"
    "            if _nav_co != st.session_state.get('gp200_company',''):\n"
    "                st.session_state['gp200_company'] = _nav_co\n"
    "            _nav_nm = st.text_input('👤 성명', value=st.session_state.get('gp200_name',''),\n"
    "                placeholder='예: 홍길동', key='_nav_nm', max_chars=30)\n"
    "            if _nav_nm != st.session_state.get('gp200_name',''):\n"
    "                st.session_state['gp200_name'] = _nav_nm\n"
    "            _nav_ct = st.text_input('📞 연락처', value=st.session_state.get('gp200_contact',''),\n"
    "                placeholder='예: 010-1234-5678', key='_nav_ct', max_chars=20)\n"
    "            if _nav_ct != st.session_state.get('gp200_contact',''):\n"
    "                st.session_state['gp200_contact'] = _nav_ct\n"
    "            st.markdown('---')\n"
    "            with st.expander('📢 앱 공지', expanded=False):\n"
    "                st.markdown('**[2026.03]** GP88 v2 배포 · 자가복구 엔진 복구 · 사이드바 구조 개선')\n"
    "                st.caption('문의: 010-3074-2616 / insusite@gmail.com')\n"
    "            with st.expander('⚙️ 계정 관리', expanded=False):\n"
    "                if st.session_state.get('is_admin', False):\n"
    "                    st.success('✅ 관리자 권한')\n"
    "                    st.caption('메인 화면 → 관리자 탭에서 전체 관리 가능')\n"
    "                else:\n"
    "                    st.info('👤 일반 회원')\n"
    "                    st.caption('이름/연락처 변경: 메인 화면 → 내 정보 탭')\n"
    "\n"
)

new_lines = lines[:INSERT_IDX] + [NEW_BLOCK] + lines[INSERT_IDX:]
print(f"삽입 완료. 총 {len(new_lines)}줄")

# 기존 with st.sidebar: 내부 _open_sidebar pop 중복 제거
# 원본 idx 28684 → 삽입 후 28684 + 1 (NEW_BLOCK은 1개 항목으로 삽입)
# NEW_BLOCK이 1개 str이므로 offset = 1
offset = 1
# 기존 _open_sidebar pop 위치 확인 (원본 ~31844)
# 삽입 후 ~31845
old_pop = '    if st.session_state.get("_open_sidebar", False):\n'
for i, l in enumerate(new_lines):
    if l == old_pop:
        print(f"기존 _open_sidebar get at line {i+1}")
        break

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("저장 완료")
