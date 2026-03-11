# -*- coding: utf-8 -*-
"""
[FINAL ULTIMATUM V4] 업그레이드 스크립트
1. [엔진 D] 생명보험 가입정보 API + 로컬 폴백 + 보장 갭 진단
2. [엔진 E] 금감원 비교 상품 엔진 (FSS API) + 최적 상품 매칭 UI
3. GK-RISK 5대 탭 확장 (기존 3탭 → 5탭: +생명보험 갭, +비교상품)
4. t0 탭 위험분석 섹션 → GK-RISK 섹터 딥링크 CTA 배너 추가
5. 라우터에서 gk_risk를 home/war_room 바로 다음으로 최우선 배치
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
original_lines = len(src.split('\n'))
print(f"원본: {original_lines}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. [엔진 D + E] 실손보험 엔진 앞에 삽입 (_loss_ins_search def 앞)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINE_DE_ANCHOR = "def _loss_ins_search(query: str = \"\", generation: int = 0) -> list:"
assert src.count(ENGINE_DE_ANCHOR) == 1

ENGINE_DE = r'''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [엔진 D] 생명보험 가입정보 데이터 엔진 (HIRA 인증키 공용)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_LIFE_INS_COVERAGE_ITEMS: list = [
    {"id": "death",       "name": "사망보장",       "icon": "💀", "category": "기본"},
    {"id": "cancer",      "name": "암진단비",        "icon": "🎗️", "category": "3대질병"},
    {"id": "stroke",      "name": "뇌혈관질환진단비","icon": "🧠", "category": "3대질병"},
    {"id": "heart",       "name": "허혈심장질환진단비","icon": "❤️", "category": "3대질병"},
    {"id": "dementia",    "name": "치매간병비",       "icon": "🧩", "category": "간병"},
    {"id": "lci",         "name": "장기간병(LCI)",    "icon": "🛏️", "category": "간병"},
    {"id": "disability",  "name": "장해보험금",       "icon": "♿", "category": "장해"},
    {"id": "accident",    "name": "상해사망/후유",    "icon": "🚑", "category": "상해"},
    {"id": "hospitalize", "name": "입원일당",         "icon": "🏥", "category": "입원"},
    {"id": "surgery",     "name": "수술비",           "icon": "🔪", "category": "수술"},
    {"id": "annuity",     "name": "연금/노후보장",    "icon": "💰", "category": "노후"},
]

# KCD → 필수 보장 매핑
_KCD_REQUIRED_COVERAGES: dict = {
    "C":   ["cancer", "hospitalize", "surgery"],
    "I6":  ["stroke", "lci", "hospitalize"],
    "I2":  ["heart", "hospitalize", "surgery"],
    "F0":  ["dementia", "lci"],
    "F01": ["dementia", "lci"],
    "G2":  ["lci", "disability"],
    "E1":  ["hospitalize", "surgery"],
    "I10": ["hospitalize"],
    "S":   ["accident", "disability", "hospitalize"],
    "N18": ["hospitalize", "surgery", "lci"],
}

_LIFE_GAP_LAW_REFS: dict = {
    "cancer":      ("상법(보험편) 제638조 + 보험업법 제95조의2",
                    "암진단비 미가입 — 설계사 설명의무 이행 후 3대질병 보장 설계 권고"),
    "stroke":      ("상법(보험편) 제638조",
                    "뇌혈관질환 진단비 미가입 — 뇌졸중·뇌경색 고위험군 필수 보장"),
    "heart":       ("금융소비자보호법 제19조",
                    "허혈심장질환 진단비 미가입 — 급성심근경색 적합성 상품 안내 의무"),
    "dementia":    ("보험업법 제102조",
                    "치매간병비 미가입 — 고령 고객 장기간병 리스크 노출"),
    "lci":         ("보험업법 제95조의2",
                    "장기간병 미가입 — LCI·치매·파킨슨 대비 설계 필수"),
    "death":       ("상법(보험편) 제638조",
                    "사망보장 미가입 — 기본 생명보험 가입 검토 필요"),
    "disability":  ("상법(보험편) 제659조",
                    "장해보장 미가입 — 직업 위험등급 고려한 상해 담보 추가 권고"),
}


def _life_gap_assess(kcd_code: str, held_coverages: list) -> dict:
    """[엔진 D §1] KCD 기반 생명보험 보장 공백 진단"""
    _required = set()
    for _p in [kcd_code[:4], kcd_code[:3], kcd_code[:2], kcd_code[:1]]:
        _required.update(_KCD_REQUIRED_COVERAGES.get(_p, []))
    if not _required:
        _required = {"death", "hospitalize"}  # 기본 필수

    _held_set = set(held_coverages)
    _gaps     = [c for c in _required if c not in _held_set]
    _covered  = [c for c in _required if c in _held_set]

    _gap_items = [next((i for i in _LIFE_INS_COVERAGE_ITEMS if i["id"] == g), None) for g in _gaps]
    _gap_items = [i for i in _gap_items if i]
    _cov_items = [next((i for i in _LIFE_INS_COVERAGE_ITEMS if i["id"] == c), None) for c in _covered]
    _cov_items = [i for i in _cov_items if i]

    _score = round(len(_covered) / max(len(_required), 1) * 100)
    _grade = "RED" if _score < 40 else ("YELLOW" if _score < 75 else "GREEN")

    return {
        "required": list(_required),
        "gaps": _gaps,
        "covered": list(_covered),
        "gap_items": _gap_items,
        "cov_items": _cov_items,
        "score": _score,
        "grade": _grade,
    }


def render_life_gap_panel(
    session_key: str = "life_gap",
    kcd_code: str = "",
) -> None:
    """[엔진 D §2] 생명보험 보장 갭 진단 UI"""
    import streamlit as _st

    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#fdf4ff;padding:14px 18px;margin-bottom:10px;'>"
        "<div style='font-size:0.90rem;font-weight:900;color:#7c3aed;margin-bottom:8px;'>"
        "💀 생명보험 보장 갭 진단 — [엔진 D]</div>",
        unsafe_allow_html=True,
    )

    # 보유 보장 입력
    _all_ids   = [i["id"] for i in _LIFE_INS_COVERAGE_ITEMS]
    _all_names = [f"{i['icon']} {i['name']}" for i in _LIFE_INS_COVERAGE_ITEMS]
    _held_raw  = _st.multiselect(
        "현재 보유 생명보험 보장 항목",
        options=_all_ids,
        default=_st.session_state.get(f"{session_key}_held", []),
        format_func=lambda x: next(
            (f"{i['icon']} {i['name']}" for i in _LIFE_INS_COVERAGE_ITEMS if i["id"] == x), x
        ),
        key=f"{session_key}_held_sel",
    )
    if _held_raw:
        _st.session_state[f"{session_key}_held"] = _held_raw

    _result = _life_gap_assess(kcd_code or "", _held_raw)

    # 점수 게이지
    _sc = _result["score"]
    _gc = {"RED": "#dc2626", "YELLOW": "#f59e0b", "GREEN": "#16a34a"}.get(_result["grade"], "#374151")
    _st.markdown(
        f"<div style='background:#f1f5f9;border:1px dashed #000;border-radius:10px;"
        f"padding:10px 16px;margin-bottom:8px;'>"
        f"<div style='display:flex;align-items:center;gap:12px;flex-wrap:wrap;'>"
        f"<span style='font-size:0.80rem;font-weight:700;color:#374151;'>보장 충족도</span>"
        f"<div style='flex:1;min-width:120px;background:#e5e7eb;border-radius:8px;height:14px;overflow:hidden;'>"
        f"<div style='width:{_sc}%;height:100%;background:{_gc};border-radius:8px;transition:width 0.4s;'></div>"
        f"</div>"
        f"<span style='font-size:1.1rem;font-weight:900;color:{_gc};'>{_sc}%</span>"
        f"<div class='risk-mega-badge-{_result['grade']}' style='font-size:0.85rem !important;"
        f"padding:4px 14px !important;'>"
        f"{'🚨 보장 공백' if _result['grade']=='RED' else '⚠️ 일부 공백' if _result['grade']=='YELLOW' else '✅ 양호'}"
        f"</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

    # 공백 항목
    if _result["gap_items"]:
        _st.markdown(
            "<div style='font-size:0.78rem;font-weight:800;color:#dc2626;margin-bottom:4px;'>"
            "🚨 보장 공백 — 즉시 설계 필요</div>",
            unsafe_allow_html=True,
        )
        for _gi in _result["gap_items"]:
            _law = _LIFE_GAP_LAW_REFS.get(_gi["id"], ("", ""))
            _st.markdown(
                f"<div style='display:flex;align-items:flex-start;gap:10px;flex-wrap:wrap;"
                f"padding:8px 12px;background:#fff;border:1px dashed #dc2626;"
                f"border-radius:8px;margin-bottom:5px;word-break:keep-all;'>"
                f"<span style='font-size:1.1rem;'>{_gi['icon']}</span>"
                f"<div style='flex:1;'>"
                f"<div style='font-size:0.82rem;font-weight:900;color:#991b1b;'>{_gi['name']} 미가입</div>"
                + (f"<div class='risk-law-ref' style='margin-top:3px;'>"
                   f"⚖️ <b>{_law[0]}</b><br>{_law[1]}</div>" if _law[0] else "")
                + "</div></div>",
                unsafe_allow_html=True,
            )

    # 보유 항목
    if _result["cov_items"]:
        _tags = "".join(
            f"<span class='syn-tag' style='background:#dcfce7;color:#166534;'>"
            f"{i['icon']} {i['name']}</span>"
            for i in _result["cov_items"]
        )
        _st.markdown(
            f"<div style='margin-top:6px;'>"
            f"<span style='font-size:0.72rem;font-weight:700;color:#374151;'>✅ 보유: </span>"
            f"{_tags}</div>",
            unsafe_allow_html=True,
        )

    _st.markdown("</div>", unsafe_allow_html=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [엔진 E] 금감원 비교 상품 엔진 (FSS API + 로컬 폴백)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _fss_get_key() -> str:
    import os as _os
    try:
        import streamlit as _st
        return _os.environ.get("FSS_API_KEY", "") or _st.secrets.get("FSS_API_KEY", "ae6f53ce")
    except Exception:
        return _os.environ.get("FSS_API_KEY", "ae6f53ce")


_FSS_PRODUCT_FALLBACK: list = [
    {
        "product_id": "P001", "insurer": "삼성생명", "name": "삼성생명 무배당 통합건강보험",
        "type": "건강보험", "premium_min": 32000, "premium_max": 89000, "unit": "월",
        "coverages": ["암진단비", "뇌혈관질환", "허혈심장질환", "입원일당", "수술비"],
        "special": "3대질병 집중 보장, 갱신형/비갱신형 선택",
        "target_kcd": ["C", "I6", "I2"],
        "score": 95,
        "url": "https://www.samsunglife.com",
    },
    {
        "product_id": "P002", "insurer": "한화생명", "name": "한화생명 암보험(무배당)",
        "type": "암보험", "premium_min": 18000, "premium_max": 55000, "unit": "월",
        "coverages": ["암진단비", "항암치료비", "암입원일당", "암수술비"],
        "special": "갑상선암·유방암 소액암 포함, 비급여 항암 특약",
        "target_kcd": ["C"],
        "score": 92,
        "url": "https://www.hanwhalife.com",
    },
    {
        "product_id": "P003", "insurer": "교보생명", "name": "교보 뇌심장보험",
        "type": "뇌심장보험", "premium_min": 25000, "premium_max": 72000, "unit": "월",
        "coverages": ["뇌졸중진단비", "급성심근경색진단비", "뇌혈관질환진단비", "심장질환진단비"],
        "special": "2대질병 집중, 뇌·심 동시 진단 시 추가 지급",
        "target_kcd": ["I6", "I2", "I21"],
        "score": 90,
        "url": "https://www.kyobo.co.kr",
    },
    {
        "product_id": "P004", "insurer": "DB손해보험", "name": "DB 간편가입 유병자보험",
        "type": "유병자보험", "premium_min": 45000, "premium_max": 130000, "unit": "월",
        "coverages": ["암진단비(소액)", "뇌혈관질환", "허혈심장질환", "입원일당"],
        "special": "유병자 3가지 간편 고지, 당뇨·고혈압 가입 가능",
        "target_kcd": ["E11", "E10", "I10", "C73"],
        "score": 88,
        "url": "https://www.idbins.com",
    },
    {
        "product_id": "P005", "insurer": "현대해상", "name": "현대해상 치매안심보험",
        "type": "치매보험", "premium_min": 28000, "premium_max": 85000, "unit": "월",
        "coverages": ["치매진단비", "치매간병비", "경도인지장애보험금", "중증치매연금"],
        "special": "경도인지장애(MCI)부터 지급, CDR 단계별 차등 지급",
        "target_kcd": ["F00", "F01", "F02", "F03"],
        "score": 93,
        "url": "https://www.hi.co.kr",
    },
    {
        "product_id": "P006", "insurer": "KB손해보험", "name": "KB 실손의료보험(4세대)",
        "type": "실손보험", "premium_min": 12000, "premium_max": 38000, "unit": "월",
        "coverages": ["입원실손", "통원실손", "처방조제실손"],
        "special": "4세대 표준, 비급여 30% 본인부담, 보험료 최저 수준",
        "target_kcd": [],
        "score": 85,
        "url": "https://www.kbinsure.co.kr",
    },
    {
        "product_id": "P007", "insurer": "메리츠화재", "name": "메리츠 운전자보험",
        "type": "운전자보험", "premium_min": 8000, "premium_max": 22000, "unit": "월",
        "coverages": ["교통사고처리지원금", "변호사선임비용", "면허정지·취소위로금"],
        "special": "형사합의금 최대 3억, 자동차사고 법률비용 포함",
        "target_kcd": ["S", "T"],
        "score": 86,
        "url": "https://www.meritzfire.com",
    },
    {
        "product_id": "P008", "insurer": "삼성화재", "name": "삼성 장기간병보험",
        "type": "간병보험", "premium_min": 35000, "premium_max": 95000, "unit": "월",
        "coverages": ["장기요양보험금", "간병인지원서비스", "뇌·심장·치매 통합"],
        "special": "장기요양 1~5등급 지급, 홈케어 서비스 연계",
        "target_kcd": ["G20", "F00", "F01", "N18", "I6"],
        "score": 91,
        "url": "https://www.samsungfire.com",
    },
]


def _fss_search_products(kcd_code: str = "", gap_coverages: list = None, limit: int = 4) -> list:
    """[엔진 E §1] FSS API → 로컬 폴백, KCD+보장갭 기반 상품 추천"""
    import urllib.request as _req, urllib.parse as _up, json as _json
    if gap_coverages is None:
        gap_coverages = []

    _key = _fss_get_key()
    _results = []

    # FSS 금융상품 통합비교공시 API 시도
    if _key and _key != "ae6f53ce":
        try:
            _params = _up.urlencode({
                "auth": _key, "menuCode": "M001", "col": "l",
                "responseType": "json",
            })
            _url = f"https://finlife.fss.or.kr/finlifeapi/lifeInsuranceList.json?{_params}"
            _resp = _req.urlopen(_url, timeout=4)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _items = (_raw.get("result", {}).get("baseList", [])
                      or _raw.get("result", {}).get("optionList", []))
            for _it in _items[:limit]:
                _results.append({
                    "product_id": _it.get("fin_prdt_cd", ""),
                    "insurer":    _it.get("kor_co_nm", ""),
                    "name":       _it.get("fin_prdt_nm", ""),
                    "type":       _it.get("join_way", ""),
                    "premium_min": 0, "premium_max": 0, "unit": "월",
                    "coverages":  [],
                    "special":    _it.get("etc_note", ""),
                    "target_kcd": [],
                    "score":      70,
                    "url":        "https://finlife.fss.or.kr",
                    "_source":    "fss_api",
                })
        except Exception:
            pass

    # 로컬 폴백 + KCD 매칭 스코어링
    if not _results:
        _scored = []
        for _p in _FSS_PRODUCT_FALLBACK:
            _s = _p["score"]
            # KCD 접두사 매칭 보너스
            if kcd_code:
                for _tk in _p["target_kcd"]:
                    if kcd_code.upper().startswith(_tk.upper()):
                        _s += 30
                        break
            # 보장 갭 매칭 보너스
            for _gap in gap_coverages:
                _gap_name_map = {
                    "cancer": "암", "stroke": "뇌", "heart": "심장",
                    "dementia": "치매", "lci": "간병", "hospitalize": "입원",
                    "surgery": "수술", "disability": "장해", "accident": "상해",
                }
                _gn = _gap_name_map.get(_gap, _gap)
                if any(_gn in cv for cv in _p["coverages"]):
                    _s += 15
            _scored.append((_s, _p))
        _scored.sort(key=lambda x: -x[0])
        _results = [{**p, "score": s, "_source": "local"} for s, p in _scored[:limit]]

    return _results[:limit]


def render_fss_product_panel(
    session_key: str = "fss_prod",
    kcd_code: str = "",
    gap_coverages: list = None,
) -> None:
    """[엔진 E §2] 금감원 비교 상품 추천 UI"""
    import streamlit as _st
    if gap_coverages is None:
        gap_coverages = []

    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#eff6ff;padding:14px 18px;margin-bottom:10px;'>"
        "<div style='font-size:0.90rem;font-weight:900;color:#1d4ed8;margin-bottom:8px;'>"
        "🏆 보장 공백 최적 보완 상품 — [엔진 E] 금감원 비교공시 연동</div>",
        unsafe_allow_html=True,
    )

    if kcd_code or gap_coverages:
        _kcd_disp = f"KCD [{kcd_code}]" if kcd_code else ""
        _gap_disp = ", ".join(gap_coverages[:3]) if gap_coverages else ""
        _st.markdown(
            f"<div style='font-size:0.72rem;color:#1d4ed8;background:#dbeafe;"
            f"border-radius:6px;padding:3px 10px;margin-bottom:8px;word-break:keep-all;'>"
            f"🎯 매칭 기준: {_kcd_disp}{' · ' if _kcd_disp and _gap_disp else ''}"
            f"{_gap_disp}</div>",
            unsafe_allow_html=True,
        )

    _prods = _fss_search_products(kcd_code=kcd_code, gap_coverages=gap_coverages, limit=4)
    _src_tag = ("🌐 금감원 공시" if any(p.get("_source") == "fss_api" for p in _prods) else "📋 내장 DB")
    _st.markdown(
        f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:6px;'>"
        f"{_src_tag} 추천 {len(_prods)}건</div>",
        unsafe_allow_html=True,
    )

    for _idx, _p in enumerate(_prods):
        _rank_emoji = ["🥇", "🥈", "🥉", "🏅"][_idx] if _idx < 4 else "📌"
        _score_color = "#16a34a" if _p["score"] >= 110 else ("#0369a1" if _p["score"] >= 90 else "#374151")
        _prem_disp = (f"{_p['premium_min']:,}~{_p['premium_max']:,}원/{_p['unit']}"
                      if _p["premium_min"] else "견적 문의")

        _cov_tags = "".join(
            f"<span class='syn-tag' style='background:#dbeafe;color:#1d4ed8;'>{cv}</span>"
            for cv in _p["coverages"][:4]
        )
        _st.markdown(
            f"<div style='background:#fff;border:1px dashed #000;border-radius:10px;"
            f"padding:12px 16px;margin-bottom:8px;word-break:keep-all;'>"
            f"<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:6px;'>"
            f"<span style='font-size:1.1rem;'>{_rank_emoji}</span>"
            f"<span style='font-size:0.88rem;font-weight:900;color:#000;'>{_p['name']}</span>"
            f"<span style='font-size:0.72rem;color:#64748b;background:#f1f5f9;"
            f"border-radius:6px;padding:1px 7px;'>{_p['insurer']}</span>"
            f"<span style='font-size:0.72rem;color:#fff;background:{_score_color};"
            f"border-radius:6px;padding:1px 7px;font-weight:900;'>★ {_p['score']}</span>"
            f"</div>"
            f"<div style='margin-bottom:4px;'>{_cov_tags}</div>"
            f"<div style='font-size:0.76rem;color:#374151;margin-bottom:4px;"
            f"word-break:keep-all;'>{_p['special']}</div>"
            f"<div style='display:flex;align-items:center;justify-content:space-between;"
            f"flex-wrap:wrap;gap:6px;'>"
            f"<span style='font-size:0.80rem;font-weight:900;color:#1d4ed8;'>{_prem_disp}</span>"
            f"<a href='{_p['url']}' target='_blank' style='font-size:0.70rem;color:#2563eb;"
            f"text-decoration:underline;'>상품 상세 →</a>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    _st.markdown("</div>", unsafe_allow_html=True)


'''

src = src.replace(ENGINE_DE_ANCHOR, ENGINE_DE + ENGINE_DE_ANCHOR, 1)
print("✓ [엔진 D+E] 생명보험 갭 + 금감원 비교상품 엔진 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. GK-RISK 탭 3개 → 5개로 확장
#    기존: ["🏥 실손보험 분석", "⚖️ 법령 검색", "🔬 KCD 상세"]
#    신규: + "💀 생명보험 갭" + "🏆 최적 상품 추천"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_TABS = '    _stab1, _stab2, _stab3 = st.tabs(["🏥 실손보험 분석", "⚖️ 법령 검색", "🔬 KCD 상세"])'
assert src.count(OLD_TABS) == 1, f"OLD_TABS count: {src.count(OLD_TABS)}"

NEW_TABS_BLOCK = r'''    _stab1, _stab2, _stab3, _stab4, _stab5 = st.tabs([
        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천", "⚖️ 법령 검색", "🔬 KCD 상세",
    ])'''

src = src.replace(OLD_TABS, NEW_TABS_BLOCK, 1)
print("✓ 탭 구조 5개로 확장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 기존 _stab2/_stab3 → _stab4/_stab5로 번호 조정,
#    새 _stab2(생명보험 갭) + _stab3(비교상품) 블록 삽입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_STAB2 = '''    with _stab2:
        render_law_search(
            session_key="risk_law2",
            kcd_code=_syn_kcd,
            show_linked=True,
        )
        if _syn_kcd:
            _kst2 = _loss_kcd_status(_syn_kcd)
            if _kst2.get("status") == "면책":
                st.markdown(
                    "<div class='risk-law-ref' style='border:1px dashed #dc2626;background:#fef2f2;'>"
                    "🚨 <b>면책 사유 필수 설명</b> — 보험업법 제95조의2 설명의무 이행 후 계약 체결하십시오.</div>",
                    unsafe_allow_html=True,
                )

    with _stab3:'''

assert src.count(OLD_STAB2) == 1, f"OLD_STAB2 count: {src.count(OLD_STAB2)}"

NEW_STAB2_TO_5 = r'''    with _stab2:
        _life_gap_kcd = (_syn_kcd or st.session_state.get("risk_kcd_code", ""))
        _life_held    = st.session_state.get("life_gap_held", [])
        render_life_gap_panel(
            session_key="life_gap",
            kcd_code=_life_gap_kcd,
        )

    with _stab3:
        _gap_held_raw = st.session_state.get("life_gap_held_sel",
                        st.session_state.get("life_gap_held", []))
        _life_result  = _life_gap_assess(_syn_kcd or "", _gap_held_raw)
        render_fss_product_panel(
            session_key="fss_prod",
            kcd_code=_syn_kcd or "",
            gap_coverages=_life_result.get("gaps", []),
        )

    with _stab4:
        render_law_search(
            session_key="risk_law2",
            kcd_code=_syn_kcd,
            show_linked=True,
        )
        if _syn_kcd:
            _kst2 = _loss_kcd_status(_syn_kcd)
            if _kst2.get("status") == "면책":
                st.markdown(
                    "<div class='risk-law-ref' style='border:1px dashed #dc2626;background:#fef2f2;'>"
                    "🚨 <b>면책 사유 필수 설명</b> — 보험업법 제95조의2 설명의무 이행 후 계약 체결하십시오.</div>",
                    unsafe_allow_html=True,
                )

    with _stab5:'''

src = src.replace(OLD_STAB2, NEW_STAB2_TO_5, 1)
print("✓ 탭 내용 재배치 (생명갭 _stab2, 비교상품 _stab3, 법령 _stab4, KCD _stab5)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. t0 탭 내 보험 분석 섹션 바로 위에 GK-RISK 딥링크 CTA 배너 추가
#    t0 섹션 if cur == "t0": 직후에 삽입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# t0 라우터 직후 첫 st.markdown 또는 렌더 함수 찾기
lines = src.split('\n')
t0_router_line = None
for i, l in enumerate(lines, 1):
    if l.strip() == 'if cur == "t0":':
        t0_router_line = i
        break

# t0 라우터 다음 함수 호출 찾기
t0_render_call = None
for i in range(t0_router_line, t0_router_line + 5):
    if '_render_' in lines[i-1] or 'render_' in lines[i-1]:
        t0_render_call = lines[i-1]
        break

print(f"t0 라우터: line {t0_router_line}")
print(f"t0 렌더 콜: {repr(t0_render_call[:60] if t0_render_call else 'None')}")

# t0 섹션에서 실제 렌더링 함수 이름 찾기
T0_SECTION_ANCHOR = None
for i in range(t0_router_line, min(t0_router_line + 8, len(lines))):
    ln = lines[i-1]
    if '_render_' in ln and ln.strip().startswith('_render_'):
        T0_SECTION_ANCHOR = ln.rstrip()
        break
    if 'render_' in ln and '(' in ln:
        T0_SECTION_ANCHOR = ln.rstrip()
        break

print(f"T0_SECTION_ANCHOR: {repr(T0_SECTION_ANCHOR)}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. 라우터 순서에서 gk_risk를 최상위로 이동 (home/home_portal 바로 다음)
#    현재: intro > home_portal > claim_scanner > war_room > gk_risk
#    목표: intro > home_portal > gk_risk > claim_scanner > war_room > ...
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 현재 war_room 라우터와 gk_risk 라우터 블록을 찾아서 순서 교환
ROUTER_WAR_ROOM = (
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    # [WAR-ROOM] 실전 상담 전략실 라우터\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    if cur == \"war_room\":\n"
    "        _render_war_room()\n"
    "        st.stop()\n"
    "\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    # [GK-RISK] 전략적 위험 분석 사령부 라우터\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    if cur == \"gk_risk\":\n"
    "        _render_gk_risk()\n"
    "        st.stop()\n"
)

ROUTER_RISK_FIRST = (
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    # [GK-RISK] 전략적 위험 분석 사령부 라우터 — 최우선 배치\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    if cur == \"gk_risk\":\n"
    "        _render_gk_risk()\n"
    "        st.stop()\n"
    "\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    # [WAR-ROOM] 실전 상담 전략실 라우터\n"
    "    # ══════════════════════════════════════════════════════════════════════\n"
    "    if cur == \"war_room\":\n"
    "        _render_war_room()\n"
    "        st.stop()\n"
)

if src.count(ROUTER_WAR_ROOM) == 1:
    src = src.replace(ROUTER_WAR_ROOM, ROUTER_RISK_FIRST, 1)
    print("✓ gk_risk 라우터 최우선 배치 완료")
else:
    print(f"⚠ war_room+gk_risk 블록 count={src.count(ROUTER_WAR_ROOM)}, 라우터 순서 변경 생략")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
new_lines = len(src.split('\n'))
print(f"OK total lines: {new_lines} (+{new_lines-original_lines})")
