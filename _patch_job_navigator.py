# [PATCH] 계층형 보험 직업 탐색기 삽입
# 1) L675 직후: _JOB_TREE_DB + render_job_navigator() 삽입
# 2) t0 탭 연락처 입력 이후: render_job_navigator() 호출 삽입
# 3) crm_set_profile 호출: job 관련 파라미터 추가

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ═══════════════════════════════════════════════════════════════════════
# PATCH 1: 직업 트리 DB + render_job_navigator() 함수 삽입
# 위치: gp200_search_companies 함수 끝(L675) 이후
# ═══════════════════════════════════════════════════════════════════════

JOB_BLOCK = '''
# ══════════════════════════════════════════════════════════════════════════════
# [GP-JOB] 계층형 보험 직업분류 DB (보험개발원 표준, 대-중-소분류 + 상해급수)
# 상해급수: 1급(녹색,저위험) / 2급(황색,중위험) / 3급(적색,고위험)
# ══════════════════════════════════════════════════════════════════════════════
_JOB_TREE_DB: dict = {
    "사무/관리직": {
        "경영·행정·사무": {
            "CEO·임원": {"code": "0101", "grade": 1, "flags": []},
            "일반 사무직": {"code": "0102", "grade": 1, "flags": []},
            "경리·회계": {"code": "0103", "grade": 1, "flags": []},
            "인사·총무": {"code": "0104", "grade": 1, "flags": []},
            "기획·전략": {"code": "0105", "grade": 1, "flags": []},
        },
        "금융·보험": {
            "은행원": {"code": "0201", "grade": 1, "flags": []},
            "보험설계사": {"code": "0202", "grade": 1, "flags": []},
            "증권사 직원": {"code": "0203", "grade": 1, "flags": []},
            "카드사 직원": {"code": "0204", "grade": 1, "flags": []},
        },
        "법률·행정": {
            "변호사": {"code": "0301", "grade": 1, "flags": []},
            "검사·판사": {"code": "0302", "grade": 1, "flags": []},
            "법무사": {"code": "0303", "grade": 1, "flags": []},
            "공무원(내근)": {"code": "0304", "grade": 1, "flags": []},
            "공무원(외근)": {"code": "0305", "grade": 2, "flags": ["외근직 여부 확인"]},
        },
    },
    "전문/기술직": {
        "의료·보건": {
            "의사(내과계)": {"code": "1101", "grade": 1, "flags": []},
            "외과 의사": {"code": "1102", "grade": 2, "flags": ["수술 집도 여부"]},
            "치과의사": {"code": "1103", "grade": 1, "flags": []},
            "한의사": {"code": "1104", "grade": 1, "flags": []},
            "간호사": {"code": "1105", "grade": 1, "flags": ["야간근무 여부"]},
            "의료기사": {"code": "1106", "grade": 1, "flags": []},
            "약사": {"code": "1107", "grade": 1, "flags": []},
        },
        "IT·소프트웨어": {
            "소프트웨어 개발자": {"code": "1201", "grade": 1, "flags": []},
            "시스템 엔지니어": {"code": "1202", "grade": 1, "flags": []},
            "네트워크 관리자": {"code": "1203", "grade": 1, "flags": []},
            "데이터 분석가": {"code": "1204", "grade": 1, "flags": []},
        },
        "교육·연구": {
            "교사(초중고)": {"code": "1301", "grade": 1, "flags": []},
            "대학교수": {"code": "1302", "grade": 1, "flags": []},
            "연구원": {"code": "1303", "grade": 1, "flags": []},
            "학원강사": {"code": "1304", "grade": 1, "flags": []},
        },
        "건축·토목 설계": {
            "건축사(설계)": {"code": "1401", "grade": 1, "flags": []},
            "토목 설계사": {"code": "1402", "grade": 1, "flags": []},
            "인테리어 디자이너": {"code": "1403", "grade": 2, "flags": ["현장 작업 여부"]},
        },
    },
    "서비스직": {
        "판매·유통": {
            "백화점·마트 직원": {"code": "2101", "grade": 1, "flags": []},
            "영업사원(내근)": {"code": "2102", "grade": 1, "flags": []},
            "영업사원(외근)": {"code": "2103", "grade": 2, "flags": ["차량 운전 빈도"]},
            "택배 기사": {"code": "2104", "grade": 2, "flags": ["오토바이 운전 여부", "차량 사고 이력"]},
        },
        "음식·숙박": {
            "식당 종업원": {"code": "2201", "grade": 1, "flags": []},
            "요리사·주방장": {"code": "2202", "grade": 2, "flags": ["칼·화기 취급 여부"]},
            "호텔 직원(프런트)": {"code": "2203", "grade": 1, "flags": []},
            "카페 바리스타": {"code": "2204", "grade": 1, "flags": []},
        },
        "운수·운전": {
            "버스 기사": {"code": "2301", "grade": 2, "flags": ["차량 사고 이력", "야간운행 여부"]},
            "택시 기사": {"code": "2302", "grade": 2, "flags": ["차량 사고 이력", "야간운행 여부"]},
            "화물 트럭 기사": {"code": "2303", "grade": 3, "flags": ["오토바이 운전 여부", "장거리 운행 여부", "위험물 취급"]},
            "오토바이 배달": {"code": "2304", "grade": 3, "flags": ["오토바이 운전 여부 ⚠️ 고지의무", "사고 이력"]},
            "지게차 운전원": {"code": "2305", "grade": 3, "flags": ["중장비 자격증 여부", "야적장 작업"]},
        },
        "경비·보안": {
            "건물 경비원": {"code": "2401", "grade": 2, "flags": ["야간근무 여부"]},
            "보안요원": {"code": "2402", "grade": 2, "flags": ["무기 소지 여부"]},
            "청원경찰": {"code": "2403", "grade": 2, "flags": ["총기 소지 여부 ⚠️ 고지의무"]},
        },
    },
    "생산/기술직": {
        "기계·금속": {
            "기계 조작원(실내)": {"code": "3101", "grade": 2, "flags": ["프레스 취급 여부"]},
            "용접공": {"code": "3102", "grade": 3, "flags": ["고온 작업 여부", "고소 작업 여부"]},
            "금속 가공원": {"code": "3103", "grade": 3, "flags": ["절삭기 취급", "금속 분진 노출"]},
        },
        "건설·토목": {
            "현장 감독": {"code": "3201", "grade": 2, "flags": ["고소 작업 여부", "현장 상주 여부"]},
            "형틀·철근공": {"code": "3202", "grade": 3, "flags": ["고소 작업 ⚠️ 고지의무", "중량물 취급"]},
            "지붕·외장공": {"code": "3203", "grade": 3, "flags": ["고소 작업 ⚠️ 고지의무"]},
            "굴착·발파공": {"code": "3204", "grade": 3, "flags": ["화약 취급 ⚠️ 고지의무", "갱내 작업"]},
            "조적·미장공": {"code": "3205", "grade": 2, "flags": ["고소 작업 여부"]},
            "전기·설비 공사": {"code": "3206", "grade": 3, "flags": ["고압 전기 취급 ⚠️ 고지의무", "고소 작업"]},
        },
        "화학·위험물": {
            "화학공장 근로자": {"code": "3301", "grade": 3, "flags": ["유해화학물질 ⚠️ 고지의무", "방호복 착용"]},
            "위험물 취급자": {"code": "3302", "grade": 3, "flags": ["위험물 자격증 여부 ⚠️ 고지의무"]},
            "LPG·LNG 배관공": {"code": "3303", "grade": 3, "flags": ["가스 취급 ⚠️ 고지의무"]},
        },
        "조선·중공업": {
            "조선소 근로자": {"code": "3401", "grade": 3, "flags": ["도장·샌딩 작업 여부", "밀폐공간 여부"]},
            "선박 기관사": {"code": "3402", "grade": 3, "flags": ["해상 근무 여부", "야간 항해"]},
        },
    },
    "농림/어업": {
        "농업": {
            "일반 농업인": {"code": "4101", "grade": 2, "flags": ["농기계 사용 여부"]},
            "농기계 운전원": {"code": "4102", "grade": 3, "flags": ["트랙터·콤바인 ⚠️ 고지의무"]},
            "비닐하우스 재배": {"code": "4103", "grade": 1, "flags": []},
        },
        "어업": {
            "연안 어업인": {"code": "4201", "grade": 3, "flags": ["해상 작업 ⚠️ 고지의무", "선박 승선"]},
            "원양 어업인": {"code": "4202", "grade": 3, "flags": ["원양 항해 ⚠️ 고지의무", "해외 체류"]},
            "양식업": {"code": "4203", "grade": 2, "flags": ["잠수 작업 여부"]},
        },
        "임업": {
            "벌목·산림 작업": {"code": "4301", "grade": 3, "flags": ["전동톱 취급 ⚠️ 고지의무", "산악 작업"]},
        },
    },
    "무직/기타": {
        "무직·주부": {
            "주부(전업)": {"code": "9001", "grade": 1, "flags": []},
            "무직": {"code": "9002", "grade": 1, "flags": ["소득 증빙 여부"]},
            "학생(초중고)": {"code": "9003", "grade": 1, "flags": []},
            "대학생": {"code": "9004", "grade": 1, "flags": []},
        },
        "예술·스포츠": {
            "운동선수(프로)": {"code": "9101", "grade": 3, "flags": ["종목 고지의무 ⚠️", "격렬 신체활동"]},
            "아마추어 선수": {"code": "9102", "grade": 2, "flags": ["운동 종목 확인"]},
            "연예인·방송인": {"code": "9103", "grade": 1, "flags": []},
            "작가·예술가": {"code": "9104", "grade": 1, "flags": []},
        },
        "자영업": {
            "일반 소매업": {"code": "9201", "grade": 1, "flags": []},
            "요식업(주방 포함)": {"code": "9202", "grade": 2, "flags": ["칼·화기 취급"]},
            "유흥업소 종사자": {"code": "9203", "grade": 3, "flags": ["야간 영업 ⚠️ 고지의무"]},
        },
    },
}

# 직업 전체 플랫 리스트 (검색용)
_JOB_FLAT_LIST: list = []
for _jmaj, _jmids in _JOB_TREE_DB.items():
    for _jmid, _jsubs in _jmids.items():
        for _jsub, _jinfo in _jsubs.items():
            _JOB_FLAT_LIST.append({
                "major": _jmaj,
                "mid": _jmid,
                "sub": _jsub,
                "code": _jinfo["code"],
                "grade": _jinfo["grade"],
                "flags": _jinfo["flags"],
                "label": f"{_jmaj} > {_jmid} > {_jsub}",
            })

_JOB_GRADE_COLORS = {1: "#22c55e", 2: "#f59e0b", 3: "#ef4444"}
_JOB_GRADE_LABELS = {1: "1급 (저위험)", 2: "2급 (중위험)", 3: "3급 (고위험)"}
_JOB_GRADE_ICONS  = {1: "🟢", 2: "🟡", 3: "🔴"}


def _job_search(query: str, limit: int = 8) -> list:
    """직업명 키워드 검색 → 매칭된 플랫 직업 리스트 반환"""
    q = query.strip().lower()
    if not q:
        return []
    hits = []
    for item in _JOB_FLAT_LIST:
        if q in item["sub"].lower() or q in item["mid"].lower() or q in item["major"].lower():
            hits.append(item)
        if len(hits) >= limit:
            break
    return hits


def render_job_navigator(session_prefix: str = "job_nav", compact: bool = False) -> dict:
    """
    [GP-JOB] 계층형 보험 직업 탐색기 UI 컴포넌트.
    반환: {"sub": 직업명, "code": 코드, "grade": 급수, "flags": 체크리스트, "path": "대>중>소"}
    session_prefix로 여러 곳에서 독립 사용 가능.
    """
    import streamlit as st

    _result = {}
    _saved = {
        "major": st.session_state.get(f"{session_prefix}_major", ""),
        "mid":   st.session_state.get(f"{session_prefix}_mid",   ""),
        "sub":   st.session_state.get(f"{session_prefix}_sub",   ""),
        "code":  st.session_state.get(f"{session_prefix}_code",  ""),
        "grade": st.session_state.get(f"{session_prefix}_grade", 0),
        "flags": st.session_state.get(f"{session_prefix}_flags", []),
    }

    # ── 컨테이너 스타일 ─────────────────────────────────────────────────
    st.markdown(
        "<div style='border:1px dashed #000;border-radius:10px;"
        "padding:10px 14px 12px 14px;margin:6px 0 10px 0;"
        "background:#fafafa;box-sizing:border-box;'>",
        unsafe_allow_html=True
    )

    # ── 브레드크럼 ────────────────────────────────────────────────────
    if _saved["sub"]:
        _bc_color = _JOB_GRADE_COLORS.get(_saved["grade"], "#666")
        _bc_icon  = _JOB_GRADE_ICONS.get(_saved["grade"], "⚪")
        _bc_label = _JOB_GRADE_LABELS.get(_saved["grade"], "")
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap;'>"
            f"<span style='font-size:0.78rem;color:#374151;font-weight:700;'>"
            f"📍 {_saved['major']} &gt; {_saved['mid']} &gt; <b>{_saved['sub']}</b></span>"
            f"<span style='background:{_bc_color};color:#fff;font-size:0.75rem;font-weight:800;"
            f"padding:2px 10px;border-radius:20px;white-space:nowrap;'>"
            f"{_bc_icon} {_bc_label}</span>"
            f"<span style='font-size:0.72rem;color:#6b7280;'>코드: {_saved['code']}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

    # ── 탭: 검색 vs 루트 탐색 ─────────────────────────────────────────
    _tab_search, _tab_tree = st.tabs(["🔍 직업 검색", "🗂️ 분류별 탐색"])

    # ─────────── 검색 탭 ───────────────────────────────────────────────
    with _tab_search:
        _q = st.text_input(
            "직업명 입력",
            placeholder="예: 용접, 배달, 간호, 교사...",
            key=f"{session_prefix}_search_q",
            label_visibility="collapsed",
        )
        _hits = _job_search(_q) if _q else []
        if _hits:
            _options = ["─ 선택하세요 ─"] + [f"{h['major']} > {h['mid']} > {h['sub']}  [{_JOB_GRADE_ICONS[h['grade']]}]" for h in _hits]
            _pick_idx = st.selectbox(
                "검색 결과",
                range(len(_options)),
                format_func=lambda i: _options[i],
                key=f"{session_prefix}_search_pick",
                label_visibility="collapsed",
            )
            if _pick_idx and _pick_idx > 0:
                _hit = _hits[_pick_idx - 1]
                st.session_state[f"{session_prefix}_major"] = _hit["major"]
                st.session_state[f"{session_prefix}_mid"]   = _hit["mid"]
                st.session_state[f"{session_prefix}_sub"]   = _hit["sub"]
                st.session_state[f"{session_prefix}_code"]  = _hit["code"]
                st.session_state[f"{session_prefix}_grade"] = _hit["grade"]
                st.session_state[f"{session_prefix}_flags"] = _hit["flags"]
                st.rerun()
        elif _q:
            st.caption("⚠️ 검색 결과 없음 — 분류별 탐색 탭을 이용하세요.")

    # ─────────── 루트 탐색 탭 ─────────────────────────────────────────
    with _tab_tree:
        _major_list = ["─ 대분류 선택 ─"] + list(_JOB_TREE_DB.keys())
        _major_idx  = (_major_list.index(_saved["major"])
                       if _saved["major"] in _major_list else 0)
        _sel_major = st.selectbox(
            "① 대분류",
            _major_list,
            index=_major_idx,
            key=f"{session_prefix}_major_sel",
        )
        if _sel_major and _sel_major != "─ 대분류 선택 ─":
            _mid_map = _JOB_TREE_DB[_sel_major]
            _mid_list = ["─ 중분류 선택 ─"] + list(_mid_map.keys())
            _mid_idx  = (_mid_list.index(_saved["mid"])
                         if (_saved["major"] == _sel_major and _saved["mid"] in _mid_list) else 0)
            _sel_mid = st.selectbox(
                "② 중분류",
                _mid_list,
                index=_mid_idx,
                key=f"{session_prefix}_mid_sel",
            )
            if _sel_mid and _sel_mid != "─ 중분류 선택 ─":
                _sub_map = _mid_map[_sel_mid]
                _sub_list = ["─ 소분류 선택 ─"] + list(_sub_map.keys())
                _sub_idx  = (_sub_list.index(_saved["sub"])
                             if (_saved["major"] == _sel_major and _saved["mid"] == _sel_mid
                                 and _saved["sub"] in _sub_list) else 0)
                _sel_sub = st.selectbox(
                    "③ 소분류",
                    _sub_list,
                    index=_sub_idx,
                    key=f"{session_prefix}_sub_sel",
                )
                if _sel_sub and _sel_sub != "─ 소분류 선택 ─":
                    _info = _sub_map[_sel_sub]
                    if (st.session_state.get(f"{session_prefix}_sub") != _sel_sub
                            or st.session_state.get(f"{session_prefix}_major") != _sel_major):
                        st.session_state[f"{session_prefix}_major"] = _sel_major
                        st.session_state[f"{session_prefix}_mid"]   = _sel_mid
                        st.session_state[f"{session_prefix}_sub"]   = _sel_sub
                        st.session_state[f"{session_prefix}_code"]  = _info["code"]
                        st.session_state[f"{session_prefix}_grade"] = _info["grade"]
                        st.session_state[f"{session_prefix}_flags"] = _info["flags"]
                        st.rerun()

    # ── 위험등급 배지 + 고지의무 체크리스트 ────────────────────────────
    _cur_grade = st.session_state.get(f"{session_prefix}_grade", 0)
    _cur_flags = st.session_state.get(f"{session_prefix}_flags", [])
    _cur_sub   = st.session_state.get(f"{session_prefix}_sub", "")
    if _cur_grade and _cur_sub:
        _gc = _JOB_GRADE_COLORS[_cur_grade]
        _gl = _JOB_GRADE_LABELS[_cur_grade]
        _gi = _JOB_GRADE_ICONS[_cur_grade]
        _grade_cols = st.columns([3, 2])
        with _grade_cols[0]:
            st.markdown(
                f"<div style='background:{_gc}22;border:1.5px solid {_gc};"
                f"border-radius:10px;padding:8px 12px;margin-top:6px;'>"
                f"<span style='font-size:0.85rem;font-weight:700;color:{_gc};'>"
                f"{_gi} 상해급수: {_gl}</span><br>"
                f"<span style='font-size:0.72rem;color:#374151;'>"
                f"직업코드: {st.session_state.get(f'{session_prefix}_code','')}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
        with _grade_cols[1]:
            if _cur_flags:
                st.markdown(
                    "<div style='background:#fff7ed;border:1px dashed #f59e0b;"
                    "border-radius:8px;padding:6px 10px;margin-top:6px;'>"
                    "<div style='font-size:0.72rem;font-weight:800;color:#92400e;margin-bottom:3px;'>"
                    "⚠️ 고지/통지의무 체크리스트</div>"
                    + "".join(f"<div style='font-size:0.71rem;color:#7c3aed;'>▸ {f}</div>" for f in _cur_flags)
                    + "</div>",
                    unsafe_allow_html=True
                )
        # 초기화 버튼
        if st.button("🗑️ 직업 초기화", key=f"{session_prefix}_reset", use_container_width=False):
            for _k in ["major", "mid", "sub", "code", "grade", "flags"]:
                st.session_state.pop(f"{session_prefix}_{_k}", None)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # 결과 반환
    if st.session_state.get(f"{session_prefix}_sub"):
        return {
            "sub":   st.session_state[f"{session_prefix}_sub"],
            "code":  st.session_state[f"{session_prefix}_code"],
            "grade": st.session_state[f"{session_prefix}_grade"],
            "flags": st.session_state[f"{session_prefix}_flags"],
            "path":  f"{st.session_state.get(f'{session_prefix}_major','')} > "
                     f"{st.session_state.get(f'{session_prefix}_mid','')} > "
                     f"{st.session_state[f'{session_prefix}_sub']}",
        }
    return {}

'''

ANCHOR1 = "# ── 제35조 §3 — CDR 단계별 권장 담보 매핑 ──────────────────────────────"
if ANCHOR1 in content:
    content = content.replace(ANCHOR1, JOB_BLOCK + ANCHOR1, 1)
    print("PATCH 1: 직업 DB + render_job_navigator() 삽입 OK")
else:
    print("WARNING PATCH 1: 앵커 미발견")

# ═══════════════════════════════════════════════════════════════════════
# PATCH 2: t0 탭 — 연락처 입력 이후 직업 탐색기 삽입
# 위치: 소개자/연고 토글 섹션 바로 위 (L34231 앞)
# ═══════════════════════════════════════════════════════════════════════

OLD_CONTACT_SECTION = '''                # ── 소개자/연고 토글 ──────────────────────────────────────
                _known_names = [n for n in _reg.keys() if n not in ("", "익명 고객", _effective_name)]'''

NEW_CONTACT_SECTION = '''                # ── 직업 탐색기 (GP-JOB) ─────────────────────────────────────
                _job_toggle = st.toggle(
                    "💼 직업 정보 입력 (상해급수 자동 판정)",
                    value=bool(_crm_p.get("job_code") or _crm_p.get("job_sub")),
                    key="t0_job_toggle"
                )
                if _job_toggle:
                    # 저장된 직업 정보를 세션에 복원
                    if _crm_p.get("job_sub") and not st.session_state.get("t0_job_sub"):
                        st.session_state["t0_job_major"] = _crm_p.get("job_major", "")
                        st.session_state["t0_job_mid"]   = _crm_p.get("job_mid", "")
                        st.session_state["t0_job_sub"]   = _crm_p.get("job_sub", "")
                        st.session_state["t0_job_code"]  = _crm_p.get("job_code", "")
                        st.session_state["t0_job_grade"] = _crm_p.get("job_grade", 0)
                        st.session_state["t0_job_flags"] = _crm_p.get("job_flags", [])
                    _pf_job_result = render_job_navigator(session_prefix="t0_job")
                else:
                    _pf_job_result = {}

                # ── 소개자/연고 토글 ──────────────────────────────────────
                _known_names = [n for n in _reg.keys() if n not in ("", "익명 고객", _effective_name)]'''

if OLD_CONTACT_SECTION in content:
    content = content.replace(OLD_CONTACT_SECTION, NEW_CONTACT_SECTION, 1)
    print("PATCH 2: t0 탭 직업 탐색기 삽입 OK")
else:
    print("WARNING PATCH 2: 소개자/연고 토글 앵커 미발견")

# ═══════════════════════════════════════════════════════════════════════
# PATCH 3: crm_set_profile 호출에 job 파라미터 추가
# ═══════════════════════════════════════════════════════════════════════

OLD_SAVE_CALL = '''                        crm_set_profile(
                            _reg, _effective_name,
                            entity_type="법인대표" if _is_corp_mode else "개인",
                            dob=(_pf_dob.strip() if isinstance(_pf_dob, str) else ""),
                            company=_pf_company.strip() if _is_corp_mode else "",
                            title=_pf_title.strip() if isinstance(_pf_title, str) else "",
                            is_ceo=bool(_pf_is_ceo) if _is_corp_mode else False,
                            biz_no=_pf_biz_no.strip() if _is_corp_mode else "",
                            biz_addr=_pf_biz_addr.strip() if _is_corp_mode else "",
                            family=_fam_list, family_rel=_fam_rel,
                            phone=_pf_phone.strip(), carrier=_pf_carrier,
                            referrer=_pf_referrer.strip() if (_rel_toggle and isinstance(_pf_referrer, str)) else _crm_p.get("referrer",""),
                            affinity=_pf_affinity.strip() if (_rel_toggle and isinstance(_pf_affinity, str)) else _crm_p.get("affinity",""),
                            memo=_pf_memo.strip() if (_memo_toggle and isinstance(_pf_memo, str)) else _crm_p.get("memo",""),
                        )'''

NEW_SAVE_CALL = '''                        crm_set_profile(
                            _reg, _effective_name,
                            entity_type="법인대표" if _is_corp_mode else "개인",
                            dob=(_pf_dob.strip() if isinstance(_pf_dob, str) else ""),
                            company=_pf_company.strip() if _is_corp_mode else "",
                            title=_pf_title.strip() if isinstance(_pf_title, str) else "",
                            is_ceo=bool(_pf_is_ceo) if _is_corp_mode else False,
                            biz_no=_pf_biz_no.strip() if _is_corp_mode else "",
                            biz_addr=_pf_biz_addr.strip() if _is_corp_mode else "",
                            family=_fam_list, family_rel=_fam_rel,
                            phone=_pf_phone.strip(), carrier=_pf_carrier,
                            referrer=_pf_referrer.strip() if (_rel_toggle and isinstance(_pf_referrer, str)) else _crm_p.get("referrer",""),
                            affinity=_pf_affinity.strip() if (_rel_toggle and isinstance(_pf_affinity, str)) else _crm_p.get("affinity",""),
                            memo=_pf_memo.strip() if (_memo_toggle and isinstance(_pf_memo, str)) else _crm_p.get("memo",""),
                            job_major=st.session_state.get("t0_job_major", _crm_p.get("job_major", "")),
                            job_mid=st.session_state.get("t0_job_mid", _crm_p.get("job_mid", "")),
                            job_sub=st.session_state.get("t0_job_sub", _crm_p.get("job_sub", "")),
                            job_code=st.session_state.get("t0_job_code", _crm_p.get("job_code", "")),
                            job_grade=st.session_state.get("t0_job_grade", _crm_p.get("job_grade", 0)),
                            job_flags=st.session_state.get("t0_job_flags", _crm_p.get("job_flags", [])),
                        )'''

if OLD_SAVE_CALL in content:
    content = content.replace(OLD_SAVE_CALL, NEW_SAVE_CALL, 1)
    print("PATCH 3: crm_set_profile job 파라미터 추가 OK")
else:
    print("WARNING PATCH 3: crm_set_profile 앵커 미발견")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDONE: job navigator patch applied")
