with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

ANCHOR = '\ndef _rag_sector_query('
if ANCHOR not in content:
    print("ERROR: _rag_sector_query anchor not found"); exit(1)

SEC08_FUNC = '''

# ══════════════════════════════════════════════════════════════════════════════
# [GK-SEC-08] 화재·특종보험 전술 상담 센터 렌더러
# ══════════════════════════════════════════════════════════════════════════════
def _render_gk_sec08() -> None:
    """GK-SEC-08 화재·특종보험 전술 상담 센터 — PART1 건물평가 / PART2 2x2그리드 / PART3 세무"""
    import datetime as _dt

    # ── CSS ──────────────────────────────────────────────────────────────────
    st.markdown("""
<style>
.gks08-wrap {
    border: 1px dashed #000 !important;
    background: #FFF3E0 !important;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.gks08-header {
    background: linear-gradient(135deg, #BF360C 0%, #E64A19 60%, #FF7043 100%);
    border-radius: 12px;
    padding: 16px 22px;
    margin-bottom: 18px;
    border: 1px dashed #000;
}
.gks08-header h2 { color:#fff !important; font-size:1.25rem; font-weight:900; margin:0 0 4px 0; }
.gks08-header p  { color:#FFCCBC !important; font-size:0.82rem; margin:0; }
.gks08-card {
    border: 1px dashed #000;
    background: #FFF3E0;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 10px;
}
.gks08-card-title { font-size:0.92rem; font-weight:900; color:#BF360C; margin-bottom:4px; }
.gks08-card-desc  { font-size:0.78rem; color:#333; font-weight:700; }
.gks08-alarm {
    border: 2px dashed #c0392b !important;
    background: #FFEBEE !important;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 12px 0;
}
.gks08-alarm-title { font-size:1rem; font-weight:900; color:#c0392b; }
.gks08-rag-box {
    border: 1px dashed #000;
    background: #FFF8E1;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 6px 0;
    font-size:0.82rem;
    color:#333;
    font-weight:700;
}
.gks08-rag-src { font-size:0.72rem; color:#777; margin-top:4px; }
input, textarea, .stTextInput input, .stTextArea textarea {
    font-weight:700 !important; color:#000 !important;
}
</style>""", unsafe_allow_html=True)

    # ── 헤더 ────────────────────────────────────────────────────────────────
    st.markdown("""
<div class="gks08-header">
  <h2>🔥 GK-SEC-08 화재·특종보험 전술 상담 센터</h2>
  <p>자산의 가치를 증명하고 법률로 방어하라. 재물 보호의 정석을 마스터의 사령부에 이식하라.</p>
</div>""", unsafe_allow_html=True)

    # ── 상단 네비게이션 ──────────────────────────────────────────────────────
    if st.button("⬅️ 네비게이션 게이트웨이로 돌아가기", key="sec08_back_top"):
        st.session_state["current_tab"] = "home"
        st.session_state["_scroll_top"] = True
        st.rerun()

    _c_name = (
        st.session_state.get("gs_c_name") or
        st.session_state.get("current_c_name") or
        st.session_state.get("_gp89_customer_name") or ""
    )

    # ── PART 탭 구성 ─────────────────────────────────────────────────────────
    _p1, _p2, _p3 = st.tabs([
        "🏗️ PART 1 건물 평가 엔진",
        "🛡️ PART 2 재물·배상·특종",
        "💼 PART 3 세무 전략",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # PART 1 — 건물 진단 & 가액 평가 엔진
    # ══════════════════════════════════════════════════════════════════════════
    with _p1:
        st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
        st.markdown("#### 🏗️ 건물 진단 시스템 (건축물대장 기반)")

        _pc1, _pc2, _pc3 = st.columns(3)
        with _pc1:
            _bld_use = st.selectbox("건물 용도", [
                "주택(단독/다가구)", "공동주택(아파트/빌라)", "근린생활시설",
                "판매·영업시설", "업무시설(오피스)", "공장/창고", "복합건물",
            ], key="sec08_bld_use")
        with _pc2:
            _bld_struc = st.selectbox("주요 구조", [
                "철근콘크리트(RC)", "철골·콘크리트(SRC)", "철골조", "조적조(벽돌)", "목조", "경량철골",
            ], key="sec08_bld_struc")
        with _pc3:
            _bld_area = st.number_input("연면적 (㎡)", min_value=0.0, value=200.0, step=10.0, key="sec08_area")

        _pc4, _pc5 = st.columns(2)
        with _pc4:
            _bld_year = st.number_input("준공연도", min_value=1950, max_value=2030,
                                        value=2000, step=1, key="sec08_year")
        with _pc5:
            _bld_floor = st.number_input("지상 층수", min_value=1, max_value=100,
                                         value=5, step=1, key="sec08_floor")

        # ── 건물 급수 판정 ───────────────────────────────────────────────────
        _GRADE_MAP = {
            "철근콘크리트(RC)": 1,
            "철골·콘크리트(SRC)": 1,
            "철골조": 2,
            "조적조(벽돌)": 3,
            "목조": 4,
            "경량철골": 3,
        }
        _grade = _GRADE_MAP.get(_bld_struc, 3)
        if _bld_use == "복합건물":
            _grade = min(_grade + 1, 4)
            _grade_note = "복합건물 혼재 요율 +1급 적용"
        elif _bld_use == "공장/창고":
            _grade = min(_grade + 1, 4)
            _grade_note = "공장/창고 위험물 가산 +1급"
        else:
            _grade_note = "단일 용도 기준"

        _grade_color = ["", "#2E7D32", "#1565C0", "#E65100", "#c0392b"][_grade]
        st.markdown(
            f'<div style="border:1px dashed #000;background:#FFF3E0;border-radius:8px;'
            f'padding:10px 16px;margin:10px 0;">'
            f'<b style="font-size:0.9rem;">🏷️ 건물 급수 판정: </b>'
            f'<span style="font-size:1.2rem;font-weight:900;color:{_grade_color};">{_grade}급</span>'
            f'&nbsp;&nbsp;<span style="font-size:0.78rem;color:#555;font-weight:700;">{_grade_note}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown("#### 💰 보험가액 평가 시뮬레이터")
        _vc1, _vc2 = st.columns(2)
        with _vc1:
            _unit_price = st.number_input(
                "㎡당 신축 단가 (원)", min_value=0, value=1_500_000, step=100_000,
                key="sec08_unit_price", format="%d",
            )
            _rebuild_val = int(_bld_area * _unit_price)
            st.metric("재조달가액 (신축비용 기준)", f"{_rebuild_val:,}원")
        with _vc2:
            _age = _dt.date.today().year - _bld_year
            _RESIDUAL_MIN = 0.20  # 최종 잔가율 20%
            _USEFUL_LIFE = 50
            _depreciation = min(_age / _USEFUL_LIFE, 1.0 - _RESIDUAL_MIN)
            _market_val = int(_rebuild_val * (1.0 - _depreciation))
            st.metric("시가 (계속사용재 감가)", f"{_market_val:,}원",
                      delta=f"감가율 {_depreciation*100:.1f}% / 잔가율 {(1-_depreciation)*100:.1f}%")

        # ── 80% 비례보상 위험 알람 ──────────────────────────────────────────
        _ins_val = st.number_input(
            "계약 보험가액 (원, 실제 가입액 기준)",
            min_value=0, value=_market_val, step=1_000_000, key="sec08_ins_val", format="%d",
        )
        _ratio = _ins_val / _market_val if _market_val > 0 else 1.0

        if _ratio < 0.80:
            st.markdown(
                f'<div class="gks08-alarm">'
                f'<div class="gks08-alarm-title">⚠️ 비례보상 위험 알람!</div>'
                f'<div style="font-size:0.85rem;font-weight:700;color:#c0392b;margin-top:6px;">'
                f'보험가액({_ins_val:,}원)이 시가의 {_ratio*100:.1f}%로 <b>80% 미만</b>입니다.<br>'
                f'손해액이 {_ins_val:,}원 이내라도 비례 삭감 적용 → 실제 보상 = 손해액 × {_ratio:.3f}<br>'
                f'<b>즉시 보험가액을 {int(_market_val*0.80):,}원 이상으로 증액하세요.</b>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.success(f"✅ 보험가액 적정 ({_ratio*100:.1f}%) — 80% 전부보험 인정 조건 충족")

        # ── RAG: 법률 라이브러리 ────────────────────────────────────────────
        _law_refs = _rag_sector_query("민법 758조 공작물 책임 실화책임법", sector="terms", top_k=2)
        if _law_refs:
            st.markdown("**📚 법률 RAG 참조 — 민법 제758조·실화책임법**")
            for _r in _law_refs:
                st.markdown(
                    f'<div class="gks08-rag-box">📖 <b>{_r["title"]}</b><br>{_r["content"]}'
                    f'<div class="gks08-rag-src">출처: {_r["source"]}'
                    f'{(" · " + str(_r["page"]) + "p") if _r.get("page") else ""}</div></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div class="gks08-rag-box">📖 <b>민법 제758조 — 공작물 등의 점유자·소유자 책임</b><br>'
                '공작물의 설치 또는 보존의 하자로 타인에게 손해를 가한 때에는 점유자가 배상책임을 진다. '
                '단, 점유자가 손해 방지에 필요한 주의를 해태하지 않은 때에는 소유자가 책임을 진다.'
                '<div class="gks08-rag-src">출처: 민법 제758조 (내장 데이터)</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="gks08-rag-box">📖 <b>실화책임에 관한 법률 — 경과실 책임 제한</b><br>'
                '실화(失火)가 중대한 과실에 의하지 아니한 경우, 법원은 제반 사정을 고려하여 '
                '손해배상액을 경감할 수 있다. (경과실 실화자 보호 → 화재배상책임보험 역할 핵심)'
                '<div class="gks08-rag-src">출처: 실화책임에 관한 법률 (내장 데이터)</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 2 — 재물·배상책임·특종·보상실무 2x2 그리드
    # ══════════════════════════════════════════════════════════════════════════
    with _p2:
        _g_row1_c1, _g_row1_c2 = st.columns(2)
        _g_row2_c1, _g_row2_c2 = st.columns(2)

        # [1] 재물보험 파트
        with _g_row1_c1:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("##### 🏠 재물보험 전술")
            st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.79rem;font-family:sans-serif;">
<thead><tr style="background:#E64A19;color:#fff;">
  <th style="padding:6px 8px;">물건 분류</th>
  <th style="padding:6px 8px;">요율 특성</th>
  <th style="padding:6px 8px;">80% 전부보험</th>
</tr></thead>
<tbody>
<tr style="background:#FFF3E0;">
  <td style="padding:6px;font-weight:700;">주택</td>
  <td style="padding:6px;">1~2급 구조 기준, 장기 적립식 권장</td>
  <td style="padding:6px;color:#2E7D32;font-weight:700;">자동 적용</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:6px;font-weight:700;">일반(상가)</td>
  <td style="padding:6px;">용도·구조 복합 요율, 영업배상 병합</td>
  <td style="padding:6px;color:#1565C0;font-weight:700;">약관 명시 필요</td>
</tr>
<tr style="background:#FFF3E0;">
  <td style="padding:6px;font-weight:700;">공장</td>
  <td style="padding:6px;">위험물·작업공정별 할증, 기계위험 병합</td>
  <td style="padding:6px;color:#c0392b;font-weight:700;">별도 협의</td>
</tr>
</tbody></table></div>""", height=145)
            st.markdown('<div class="gks08-card"><div class="gks08-card-title">📄 1년 소멸식 vs 장기 적립식</div>'
                        '<div class="gks08-card-desc">소멸식: 연납·저보험료, 갱신 리스크<br>'
                        '장기적립식: 만기환급·보험료 고정, 감가상각 대응 유리</div></div>',
                        unsafe_allow_html=True)
            st.markdown('<div class="gks08-card"><div class="gks08-card-title">📋 국문 vs 영문 약관 비교</div>'
                        '<div class="gks08-card-desc">국문: 열거주의(보상 사유 명시), 영문(All-Risks): 포괄주의·면책 사유 외 전부 보상<br>'
                        '공장·정밀기계·수출입 화물은 영문 약관 강력 권장</div></div>',
                        unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # [2] 배상책임 파트
        with _g_row1_c2:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("##### ⚖️ 배상책임 전술")
            st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.79rem;font-family:sans-serif;">
<thead><tr style="background:#E64A19;color:#fff;">
  <th style="padding:6px 8px;">담보</th>
  <th style="padding:6px 8px;">대상</th>
  <th style="padding:6px 8px;">의무 여부</th>
  <th style="padding:6px 8px;">법적 근거</th>
</tr></thead>
<tbody>
<tr style="background:#FFF3E0;">
  <td style="padding:6px;font-weight:700;">화재배상(대인)</td>
  <td style="padding:6px;">인접 거주자 사망·부상</td>
  <td style="padding:6px;color:#c0392b;font-weight:700;">임의</td>
  <td style="padding:6px;">실화법·민758조</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:6px;font-weight:700;">화재배상(대물)</td>
  <td style="padding:6px;">인접 재물 손해</td>
  <td style="padding:6px;color:#c0392b;font-weight:700;">임의</td>
  <td style="padding:6px;">민750·758조</td>
</tr>
<tr style="background:#FFF3E0;">
  <td style="padding:6px;font-weight:700;color:#1565C0;">특수건물 신체배상</td>
  <td style="padding:6px;">연면적 2,000㎡↑ 특수건물</td>
  <td style="padding:6px;color:#2E7D32;font-weight:700;">의무(법정)</td>
  <td style="padding:6px;">화재특수건물법</td>
</tr>
</tbody></table></div>""", height=145)
            st.markdown('<div class="gks08-card"><div class="gks08-card-title">🔄 임차인 원상복구 & 구상권 방어</div>'
                        '<div class="gks08-card-desc">'
                        '<b>민법 제615조:</b> 임차인은 임대차 종료 시 원상복구 의무<br>'
                        '<b>상법 제682조:</b> 보험자 대위(구상권) — 임차인이 배상책임보험 가입 시 차단<br>'
                        '→ <b>임차인에게 화재배상+원상복구 특약 가입 필수 설득</b></div></div>',
                        unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # [3] 특종보험 체크리스트
        with _g_row2_c1:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("##### 🔬 특종보험 의무·업종별 체크리스트")
            _mandatory = [
                ("승강기 배상책임", "승강기 설치 건물 전체", "승강기시설법"),
                ("가스사고 배상책임", "도시가스 사업자·LP가스 판매점", "가스안전법"),
                ("다중이용업소 배상", "노래방·PC방·식당·학원 등", "다중이용업법"),
                ("재난배상책임", "100명 이상 수용 다중이용시설", "재난안전법"),
                ("체육시설 배상", "체육시설 사업자 전체", "체육시설법"),
                ("학원 배상책임", "학원 등록 사업자", "학원법"),
            ]
            for _ins, _target, _law in _mandatory:
                _chk = st.checkbox(f"**{_ins}**", key=f"sec08_mandatory_{_ins}")
                if _chk:
                    st.caption(f"   대상: {_target} | 근거: {_law}")

            st.divider()
            st.markdown("**🏭 업종별 특화 담보**")
            _specialty = {
                "건설업": "건설공사보험 + 조립보험 + 건설배상",
                "제조업": "패키지(재산종합)보험 + 생산물배상",
                "의료/전문직": "전문직 배상책임(E&O)",
                "자동차 정비": "정비업자 배상 + 수탁물배상",
                "미용/피부": "미용배상책임 + 수탁물배상",
                "음식업": "음식물배상 + 영업배상",
            }
            _biz_type = st.selectbox("업종 선택", list(_specialty.keys()), key="sec08_biz_type")
            st.markdown(
                f'<div class="gks08-card"><div class="gks08-card-title">✅ {_biz_type} 추천 담보</div>'
                f'<div class="gks08-card-desc">{_specialty[_biz_type]}</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

        # [4] 보상 실무 RAG
        with _g_row2_c2:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("##### 🔍 보상 실무 RAG 검색")
            _comp_query = st.selectbox("조회 주제", [
                "실화법 적용 판례 (경과실 책임 제한)",
                "중복보험 안분 계산 — 독립책임액 비례",
                "기왕증 상계 사례 요약",
                "대위변제 및 구상권 청구 절차",
                "전부보험 vs 일부보험 보상 차이",
            ], key="sec08_comp_query")

            if st.button("🔍 보상실무 RAG 검색", key="sec08_comp_search", type="primary"):
                _comp_res = _rag_sector_query(_comp_query, sector="terms", top_k=3)
                st.session_state["_sec08_comp_res"] = _comp_res
                st.session_state["_sec08_comp_q"] = _comp_query

            _c_res = st.session_state.get("_sec08_comp_res", [])
            _c_q   = st.session_state.get("_sec08_comp_q", "")
            if _c_res:
                for _r in _c_res:
                    st.markdown(
                        f'<div class="gks08-rag-box"><b>{_r["title"]}</b><br>{_r["content"]}'
                        f'<div class="gks08-rag-src">출처: {_r["source"]}'
                        f'{(" · " + str(_r["page"]) + "p") if _r.get("page") else ""}</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                # 내장 데이터
                _BUILTIN_COMP = [
                    ("중복보험 독립책임액 비례 분담 공식",
                     "각 보험사별 단독 보상 한도액(독립책임액) 비율로 실손액 분담. "
                     "A사 독립책임액 8천만 / B사 6천만 → 총 1.4억 기준 A: 57%, B: 43% 분담.",
                     "상법 제672조"),
                    ("실화책임법 — 경과실 책임 경감 판례",
                     "대법원: 경과실 실화 시 손해배상액 경감 가능. 중과실(술취한 채 담뱃불 방치 등)은 전액 책임. "
                     "화재배상책임보험이 이 공백을 커버.",
                     "실화책임법 제3조"),
                    ("기왕증 상계 — 기존 질환 기여도 공제",
                     "화재 부상자에게 기존 질환(기왕증)이 있는 경우, 법원은 손해배상액에서 기왕증 기여도만큼 공제. "
                     "통상 10~40% 상계 적용.",
                     "민법 제763조 준용"),
                ]
                for _t, _c, _s in _BUILTIN_COMP:
                    st.markdown(
                        f'<div class="gks08-rag-box"><b>{_t}</b><br>{_c}'
                        f'<div class="gks08-rag-src">출처: {_s} (내장 데이터)</div></div>',
                        unsafe_allow_html=True,
                    )
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════════
    # PART 3 — 기업·개인사업자 세무 전략
    # ══════════════════════════════════════════════════════════════════════════
    with _p3:
        _tax_corp, _tax_indiv = st.tabs(["🏭 법인(공장) 컨설팅", "🧑‍💼 개인사업자 전략"])

        with _tax_corp:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("#### 🏭 법인 보험료 세무 처리 전략")
            st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.8rem;font-family:sans-serif;">
<thead><tr style="background:#E64A19;color:#fff;">
  <th style="padding:7px 10px;">보험 종류</th>
  <th style="padding:7px 10px;">세무 처리</th>
  <th style="padding:7px 10px;">비고</th>
</tr></thead>
<tbody>
<tr style="background:#FFF3E0;">
  <td style="padding:7px;font-weight:700;">화재보험료</td>
  <td style="padding:7px;color:#2E7D32;font-weight:700;">전액 손비 처리</td>
  <td style="padding:7px;">법인세법 제19조 — 업무 관련 보험료 필요경비 인정</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">임원 생명보험 (만기환급형)</td>
  <td style="padding:7px;color:#1565C0;font-weight:700;">자산 처리 (환급액) + 보장 부분 손비</td>
  <td style="padding:7px;">국세청 예규: 만기환급금은 자산, 순수보장 부분은 비용</td>
</tr>
<tr style="background:#FFF3E0;">
  <td style="padding:7px;font-weight:700;">직원 단체 상해보험</td>
  <td style="padding:7px;color:#2E7D32;font-weight:700;">전액 손비 처리</td>
  <td style="padding:7px;">수익자 = 법인 또는 직원(임금보전 성격)</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">CEO 유족보상금 플랜</td>
  <td style="padding:7px;color:#E65100;font-weight:700;">퇴직금 재원 + 비용 처리 가능</td>
  <td style="padding:7px;">상법 제462조 중간배당 + 사망 시 퇴직금 비용 처리</td>
</tr>
</tbody></table></div>""", height=195)

            st.markdown("**📊 이익잉여금·비상장주식평가 영향**")
            _profit_reserve = st.number_input("이익잉여금 (원)", min_value=0,
                                               value=1_000_000_000, step=10_000_000,
                                               key="sec08_profit_reserve", format="%d")
            _annual_premium = st.number_input("연간 보험료 (원, 손비 처리 시)",
                                               min_value=0, value=50_000_000, step=1_000_000,
                                               key="sec08_annual_premium", format="%d")
            _corp_tax_rate = 0.22
            _tax_saving = int(_annual_premium * _corp_tax_rate)
            _reserve_after = _profit_reserve - _annual_premium
            st.markdown(
                f'<div class="gks08-card">'
                f'<div class="gks08-card-title">💡 손비 처리 효과 시뮬레이션</div>'
                f'<div class="gks08-card-desc">'
                f'연간 법인세 절감액: <b style="color:#c0392b;">{_tax_saving:,}원</b> (세율 22% 기준)<br>'
                f'이익잉여금 감소 → 비상장주식 평가액 하락 효과<br>'
                f'처리 후 잔여 이익잉여금: {_reserve_after:,}원'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

        with _tax_indiv:
            st.markdown('<div class="gks08-wrap">', unsafe_allow_html=True)
            st.markdown("#### 🧑‍💼 개인사업자 보험료 세무 전략")
            st.components.v1.html("""
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;font-size:0.8rem;font-family:sans-serif;">
<thead><tr style="background:#E64A19;color:#fff;">
  <th style="padding:7px 10px;">구분</th>
  <th style="padding:7px 10px;">복식부기 의무자</th>
  <th style="padding:7px 10px;">추계신고 대상</th>
</tr></thead>
<tbody>
<tr style="background:#FFF3E0;">
  <td style="padding:7px;font-weight:700;">화재보험료</td>
  <td style="padding:7px;color:#2E7D32;font-weight:700;">전액 필요경비 인정</td>
  <td style="padding:7px;color:#c0392b;font-weight:700;">기준경비율 내 포함 — 별도 인정 안됨</td>
</tr>
<tr style="background:#fff;">
  <td style="padding:7px;font-weight:700;">직원 단체 상해보험</td>
  <td style="padding:7px;color:#2E7D32;font-weight:700;">전액 필요경비</td>
  <td style="padding:7px;color:#c0392b;font-weight:700;">추계신고 시 별도 공제 불가</td>
</tr>
<tr style="background:#FFF3E0;">
  <td style="padding:7px;font-weight:700;">사업주 본인 상해보험</td>
  <td style="padding:7px;color:#E65100;font-weight:700;">불인정 (개인 비용)</td>
  <td style="padding:7px;color:#E65100;font-weight:700;">불인정</td>
</tr>
</tbody></table></div>""", height=165)

            _income = st.number_input("종합소득 과세표준 (원)",
                                       min_value=0, value=80_000_000, step=5_000_000,
                                       key="sec08_income", format="%d")
            _TAX_BRACKETS = [
                (14_000_000, 0.06, 0),
                (50_000_000, 0.15, 1_260_000),
                (88_000_000, 0.24, 5_760_000),
                (150_000_000, 0.35, 15_440_000),
                (300_000_000, 0.38, 19_940_000),
                (500_000_000, 0.40, 25_940_000),
                (1_000_000_000, 0.42, 35_940_000),
                (float('inf'), 0.45, 65_940_000),
            ]
            _tax = 0
            for _limit, _rate, _deduction in _TAX_BRACKETS:
                if _income <= _limit:
                    _tax = int(_income * _rate - _deduction)
                    _effective = _rate
                    break
            st.markdown(
                f'<div class="gks08-card">'
                f'<div class="gks08-card-title">📊 종합소득세 추정</div>'
                f'<div class="gks08-card-desc">'
                f'적용 세율: <b>{_effective*100:.0f}%</b>&nbsp;&nbsp;'
                f'추정 세액: <b style="color:#c0392b;">{_tax:,}원</b><br>'
                f'화재보험료 필요경비 인정 시 절세 효과: '
                f'<b>{int(_annual_premium * _effective if "_annual_premium" in dir() else 0):,}원</b>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
            st.markdown('</div>', unsafe_allow_html=True)

    # ── 중단 네비게이션 ──────────────────────────────────────────────────────
    st.divider()
    _mid_c1, _mid_c2 = st.columns(2)
    with _mid_c1:
        if st.button("🏠 홈", key="sec08_mid_home", use_container_width=True):
            st.session_state["current_tab"] = "home"
            st.session_state["_scroll_top"] = True
            st.rerun()
    with _mid_c2:
        if st.button("📂 고객 상담 보고서 생성 →", key="sec08_report_btn",
                     use_container_width=True, type="primary"):
            st.session_state["current_tab"] = "home"
            st.session_state["_scroll_top"] = True
            st.rerun()

'''

content = content.replace(ANCHOR, SEC08_FUNC + ANCHOR, 1)

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: _render_gk_sec08 inserted")
