content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# 현재 상태: for 루프 끝 다음에 바로 HIRA-KCD 블록이 옴
# selectbox / 버튼 / selected_row 처리 / hr / _ga1,_ga2 컬럼 전부 사라진 상태
# 성명/직업/생년월일 CSS + selectbox + 버튼 + selected_row + hr + text_input 전체 삽입 필요

OLD = '''            _cust_options_map = {"✏️ 고객 입력 & 검색": None}
            for _cr in _cust_rows:
                _cust_options_map[_cust_label(_cr)] = _cr

            # ── [HIRA-KCD] 질병 코드 자동완성 입력 블록 ──────────────────'''

NEW = '''            _cust_options_map = {"✏️ 고객 입력 & 검색": None}
            for _cr in _cust_rows:
                _cust_options_map[_cust_label(_cr)] = _cr
            _search_label = st.session_state.get("_home_selected_cust_label", "✏️ 고객 입력 & 검색")
            if _search_label not in _cust_options_map:
                _search_label = "✏️ 고객 입력 & 검색"

            _srch_col1, _srch_col2, _srch_col3 = st.columns([3, 1, 1])
            with _srch_col1:
                _selected_label = st.selectbox(
                    "고객 선택 (이름 검색)",
                    options=list(_cust_options_map.keys()),
                    index=list(_cust_options_map.keys()).index(_search_label),
                    key="home_cust_selectbox",
                    help="등록된 고객 이름으로 검색·선택하면 아래 정보가 자동 채워집니다"
                )
            with _srch_col2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("검색 적용", key="btn_cust_apply", use_container_width=True,
                             help="선택한 고객 정보를 아래 입력란에 적용합니다"):
                    st.rerun()
            with _srch_col3:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("목록 갱신", key="btn_cust_search", use_container_width=True,
                             help="고객 목록을 DB에서 다시 불러옵니다"):
                    st.session_state.pop("_home_selected_cust_label", None)
                    _uid_inv = st.session_state.get("user_id", "")
                    st.session_state.pop(f"_cust_rows_{_uid_inv}", None)
                    st.session_state.pop(f"_cust_rows_ts_{_uid_inv}", None)
                    st.rerun()

            _selected_row = _cust_options_map.get(_selected_label)
            if _selected_row and _selected_label != "✏️ 고객 입력 & 검색":
                st.session_state["_home_selected_cust_label"] = _selected_label
                st.session_state["selected_customer_id"] = _selected_row.get("id")
                _prof = _selected_row.get("profile") or {}
                _auto_map = {
                    "scan_client_name":  _selected_row.get("name", ""),
                    "scan_client_dob":   _prof.get("dob", ""),
                    "scan_client_job":   _prof.get("job", ""),
                    "scan_client_sick":  _prof.get("sick", "해당없음"),
                    "scan_client_items": _prof.get("items", []),
                }
                for _k, _v in _auto_map.items():
                    if st.session_state.get(_k) != _v:
                        st.session_state[_k] = _v
                st.success(f"✅ [{_selected_row.get('name','')}] 자동 로드 완료")
            else:
                st.session_state["selected_customer_id"] = None
                st.session_state["_home_selected_cust_label"] = "✏️ 고객 입력 & 검색"

            st.markdown("<hr style='margin:10px 0;border-color:#ffcccc;'>", unsafe_allow_html=True)

            _SICK_OPTIONS = [
                "해당없음",
                "심사필요(3개월이내 치료 있음)",
                "유병자(입원·수술이력 있음)",
                "유병자(당뇨·고혈압·심장 등 약 투약중)",
                "유병자(암·중풍 발병 있음)",
            ]
            _SICK_GUIDE = {
                "해당없음":                             "✅ 일반·건강체 보험가입 설계 가능",
                "심사필요(3개월이내 치료 있음)":          "⚠️ 최종 통원일 경과 후 신규보험 상담 진행. 유병자 운전자보험은 1개월 경과 후 심사 요청 가능",
                "유병자(입원·수술이력 있음)":            "📋 유병자보험 3.0.5~3.5.5 — 병력에 따라 구분 가입 상담",
                "유병자(당뇨·고혈압·심장 등 약 투약중)": "📋 유병자보험 3.0.5~3.5.5 — 병력에 따라 구분 가입 상담",
                "유병자(암·중풍 발병 있음)":             "⚠️ 최종 통원일 이후 5년 경과 후 암 상담. 향후 유병자 신규 상품 가입 가능 여부 확인",
            }
            _cur_sick = st.session_state.get("scan_client_sick", "해당없음")
            if _cur_sick not in _SICK_OPTIONS:
                _cur_sick = "해당없음"

            st.markdown("""<style>
div[data-testid="stTextInput"][data-key="home_si_name"] input,
div[data-testid="stTextInput"][data-key="home_si_dob"] input,
div[data-testid="stTextInput"][data-key="home_si_job"] input {
    border: 1.5px dashed #000000 !important;
    border-radius: 6px !important;
}
</style>""", unsafe_allow_html=True)
            _ga1, _ga2 = st.columns([1, 1])
            with _ga1:
                _si_name = st.text_input("성명", value=st.session_state.get("scan_client_name", ""),
                                         placeholder="예) 홍길동", key="home_si_name")
                _si_dob  = st.text_input("생년월일 (YYYYMMDD)", value=st.session_state.get("scan_client_dob", ""),
                                         placeholder="예) 19800101", max_chars=8, key="home_si_dob")
            with _ga2:
                _si_job  = st.text_input("직업", value=st.session_state.get("scan_client_job", ""),
                                         placeholder="예) 회사원", key="home_si_job")
                _si_sick = st.selectbox("유병자 여부", _SICK_OPTIONS,
                                        index=_SICK_OPTIONS.index(_cur_sick), key="home_si_sick")
            _sick_guide_text = _SICK_GUIDE.get(_si_sick, "")
            if _sick_guide_text:
                _sick_color = "#9a3412" if "⚠️" in _sick_guide_text else "#14532d"
                _sick_bg    = "#fff7ed" if "⚠️" in _sick_guide_text else "#f0fdf4"
                _sick_bdr   = "#f97316" if "⚠️" in _sick_guide_text else "#22c55e"
                st.markdown(
                    f\'<div style="background:{_sick_bg};border:1.5px solid {_sick_bdr};border-radius:8px;\'
                    f\'padding:8px 12px;font-size:0.82rem;font-weight:700;color:{_sick_color};\'
                    f\'white-space:pre-line;margin-bottom:8px;">{_sick_guide_text}</div>\',
                    unsafe_allow_html=True)

            # ── [HIRA-KCD] 질병 코드 자동완성 입력 블록 ──────────────────'''

if OLD in content:
    content = content.replace(OLD, NEW)
    open('D:/CascadeProjects/app.py', 'w', encoding='utf-8-sig').write(content)
    print('FIXED OK')
else:
    print('OLD string NOT FOUND')
    idx = content.find('for _cr in _cust_rows:\n                _cust_options_map[_cust_label(_cr)] = _cr')
    if idx != -1:
        line = content[:idx].count('\n') + 1
        print(f'Found partial at L{line}:')
        print(repr(content[idx:idx+300]))
