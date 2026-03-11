# -*- coding: utf-8 -*-
"""HIRA-KCD + LAW-API 엔진을 app.py의 _JOB_TREE_DB 앞에 삽입"""
import sys

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
anchor = '_JOB_TREE_DB: dict = {'
assert src.count(anchor) == 1, f"anchor found {src.count(anchor)} times"

INSERT = r'''# =====================================================================
# [HIRA-KCD §1] 심평원 질병마스터 API 엔진 + KCD 자동완성 UI
# [LAW-API §1]  국가법령정보센터 API 엔진 (OC=goldkey)
# =====================================================================

def _hira_get_key() -> str:
    import os as _os
    try:
        import streamlit as _st
        return _os.environ.get("HIRA_API_KEY", "") or _st.secrets.get("HIRA_API_KEY", "")
    except Exception:
        return _os.environ.get("HIRA_API_KEY", "")


_KCD_FALLBACK_DATA: list = [
    {"kcd": "C50", "name": "유방악성종양",       "category": "신생물",       "detail": "Malignant neoplasm of breast"},
    {"kcd": "C16", "name": "위악성종양",         "category": "신생물",       "detail": "Malignant neoplasm of stomach"},
    {"kcd": "C34", "name": "기관지및폐악성종양", "category": "신생물",       "detail": "Malignant neoplasm of bronchus and lung"},
    {"kcd": "C22", "name": "간악성종양",         "category": "신생물",       "detail": "Malignant neoplasm of liver"},
    {"kcd": "C73", "name": "갑상선악성종양",     "category": "신생물",       "detail": "Malignant neoplasm of thyroid gland"},
    {"kcd": "C61", "name": "전립선악성종양",     "category": "신생물",       "detail": "Malignant neoplasm of prostate"},
    {"kcd": "C25", "name": "췌장악성종양",       "category": "신생물",       "detail": "Malignant neoplasm of pancreas"},
    {"kcd": "C80", "name": "부위불명악성종양",   "category": "신생물",       "detail": "Malignant neoplasm without specification of site"},
    {"kcd": "I63", "name": "뇌경색증",           "category": "뇌혈관질환",   "detail": "Cerebral infarction"},
    {"kcd": "I60", "name": "지주막하출혈",       "category": "뇌혈관질환",   "detail": "Subarachnoid haemorrhage"},
    {"kcd": "I61", "name": "뇌내출혈",           "category": "뇌혈관질환",   "detail": "Intracerebral haemorrhage"},
    {"kcd": "I64", "name": "뇌졸중",             "category": "뇌혈관질환",   "detail": "Stroke, not specified as haemorrhage or infarction"},
    {"kcd": "I21", "name": "급성심근경색증",     "category": "허혈심장질환", "detail": "Acute myocardial infarction"},
    {"kcd": "I20", "name": "협심증",             "category": "허혈심장질환", "detail": "Angina pectoris"},
    {"kcd": "I25", "name": "만성허혈심장질환",   "category": "허혈심장질환", "detail": "Chronic ischaemic heart disease"},
    {"kcd": "I50", "name": "심부전",             "category": "심장질환",     "detail": "Heart failure"},
    {"kcd": "I10", "name": "본태성고혈압",       "category": "순환기질환",   "detail": "Essential hypertension"},
    {"kcd": "E11", "name": "인슐린비의존당뇨병", "category": "내분비질환",   "detail": "Type 2 diabetes mellitus"},
    {"kcd": "E10", "name": "인슐린의존당뇨병",   "category": "내분비질환",   "detail": "Type 1 diabetes mellitus"},
    {"kcd": "N18", "name": "만성신장병",         "category": "비뇨기질환",   "detail": "Chronic kidney disease"},
    {"kcd": "K74", "name": "간섬유증및간경변증", "category": "소화기질환",   "detail": "Fibrosis and cirrhosis of liver"},
    {"kcd": "J45", "name": "천식",               "category": "호흡기질환",   "detail": "Asthma"},
    {"kcd": "F00", "name": "알츠하이머치매",     "category": "정신질환",     "detail": "Dementia in Alzheimer disease"},
    {"kcd": "F01", "name": "혈관치매",           "category": "정신질환",     "detail": "Vascular dementia"},
    {"kcd": "G20", "name": "파킨슨병",           "category": "신경질환",     "detail": "Parkinson disease"},
    {"kcd": "M05", "name": "류마티스관절염",     "category": "근골격질환",   "detail": "Rheumatoid arthritis"},
    {"kcd": "S06", "name": "두개내손상",         "category": "손상",         "detail": "Intracranial injury"},
    {"kcd": "S72", "name": "대퇴골골절",         "category": "손상",         "detail": "Fracture of femur"},
]


def _hira_disease_search(query: str, limit: int = 10) -> list:
    """[HIRA-KCD §2] HIRA API 호출 → 로컬 폴백."""
    import urllib.request as _req, urllib.parse as _up, json as _json
    _key = _hira_get_key()
    _results = []
    if _key and query.strip():
        try:
            _params = _up.urlencode({
                "serviceKey": _key, "numOfRows": limit, "pageNo": 1,
                "sickType": 1, "medTp": 1, "diseaseType": "SICK_NM",
                "searchText": query.strip(),
            })
            _url = "https://apis.data.go.kr/B551182/diseaseInfoService1/getDiseaseInfo1?" + _params
            _resp = _req.urlopen(_url, timeout=4)
            _raw = _json.loads(_resp.read().decode("utf-8"))
            _items = _raw.get("response", {}).get("body", {}).get("items", {}).get("item", [])
            if isinstance(_items, dict):
                _items = [_items]
            for _it in _items:
                _results.append({
                    "kcd": _it.get("sickCd", ""), "name": _it.get("sickNm", ""),
                    "category": _it.get("sickCatNm", ""), "detail": _it.get("sickEngNm", ""),
                    "_source": "hira",
                })
        except Exception:
            pass
    if not _results:
        _q = query.strip().lower()
        for _r in _KCD_FALLBACK_DATA:
            if (_q in _r["name"].lower() or _q in _r["kcd"].lower()
                    or _q in _r["detail"].lower() or _q in _r["category"].lower()):
                _results.append({**_r, "_source": "local"})
            if len(_results) >= limit:
                break
    return _results[:limit]


_KCD_COVERAGE_MAP: dict = {
    "C":   {"label": "암",          "color": "#dc2626", "bg": "#fef2f2",
            "coverages": [{"type": "암진단비",   "std_min": 2000, "std_rec": 5000, "unit": "만원"},
                          {"type": "항암치료비", "std_min": 1000, "std_rec": 3000, "unit": "만원"},
                          {"type": "암입원일당", "std_min": 10,   "std_rec": 30,   "unit": "만원/일"}],
            "kcd_notes": "C00-C97 악성신생물. 갑상선암(C73)은 소액암 적용 상품 多."},
    "I6":  {"label": "뇌혈관질환",  "color": "#7c3aed", "bg": "#f5f3ff",
            "coverages": [{"type": "뇌졸중진단비",     "std_min": 1000, "std_rec": 3000, "unit": "만원"},
                          {"type": "뇌혈관질환진단비", "std_min": 500,  "std_rec": 1500, "unit": "만원"},
                          {"type": "장기간병비",       "std_min": 100,  "std_rec": 200,  "unit": "만원/월"}],
            "kcd_notes": "I60-I69 뇌혈관질환. I63 뇌경색=허혈성, I61 뇌출혈=출혈성."},
    "I2":  {"label": "허혈심장질환","color": "#b45309", "bg": "#fffbeb",
            "coverages": [{"type": "급성심근경색진단비", "std_min": 1000, "std_rec": 3000, "unit": "만원"},
                          {"type": "심장질환진단비",    "std_min": 500,  "std_rec": 1500, "unit": "만원"},
                          {"type": "심장수술비",        "std_min": 1000, "std_rec": 2000, "unit": "만원"}],
            "kcd_notes": "I21 급성심근경색 = 3대질병. I20 협심증은 별도 심장질환 담보."},
    "F0":  {"label": "치매",        "color": "#0369a1", "bg": "#f0f9ff",
            "coverages": [{"type": "치매진단비", "std_min": 1000, "std_rec": 3000, "unit": "만원"},
                          {"type": "치매간병비", "std_min": 100,  "std_rec": 200,  "unit": "만원/월"}],
            "kcd_notes": "F00-F03. CDR 1 이상 경도치매부터 지급 조건 확인 필수."},
    "E1":  {"label": "당뇨병",      "color": "#15803d", "bg": "#f0fdf4",
            "coverages": [{"type": "당뇨합병증진단비", "std_min": 500, "std_rec": 1000, "unit": "만원"},
                          {"type": "입원일당",         "std_min": 5,   "std_rec": 10,   "unit": "만원/일"}],
            "kcd_notes": "E11 2형당뇨 = 유병자보험 심사 대상."},
    "I10": {"label": "고혈압",      "color": "#64748b", "bg": "#f8fafc",
            "coverages": [{"type": "혈관질환진단비", "std_min": 300, "std_rec": 500, "unit": "만원"},
                          {"type": "입원일당",       "std_min": 5,   "std_rec": 10,  "unit": "만원/일"}],
            "kcd_notes": "단순 고혈압은 유병자보험(3.0.5~3.5.5) 가입 가능."},
    "G2":  {"label": "파킨슨병",    "color": "#0369a1", "bg": "#f0f9ff",
            "coverages": [{"type": "파킨슨진단비", "std_min": 1000, "std_rec": 2000, "unit": "만원"},
                          {"type": "장기간병비",   "std_min": 100,  "std_rec": 200,  "unit": "만원/월"}],
            "kcd_notes": "G20 파킨슨병. 호엔야르 단계 3 이상 시 간병 수요 급증."},
}


def _kcd_get_coverage(kcd_code: str) -> dict:
    if not kcd_code:
        return {}
    for _p in [kcd_code[:3], kcd_code[:2], kcd_code[:1]]:
        if _p in _KCD_COVERAGE_MAP:
            return _KCD_COVERAGE_MAP[_p]
    return {}


def render_kcd_autocomplete(
    label: str = "질병 검색 (KCD)",
    session_key: str = "kcd_selected",
    placeholder: str = "예) 유방암, 뇌경색, C50, I63…",
    autofill_kcd_key: str = "kcd_code",
    show_coverage: bool = True,
) -> str:
    """[HIRA-KCD §5] KCD 질병 타입어헤드 자동완성 UI. 반환: 선택된 질병명"""
    import streamlit as _st
    _cur   = _st.session_state.get(session_key, "")
    _typed = _st.text_input(label, value=_cur, placeholder=placeholder, key=f"{session_key}_input")
    _is_typing = _typed.strip() != "" and _typed != _cur
    if _is_typing:
        _hits = _hira_disease_search(_typed, limit=10)
        if _hits:
            _st.markdown(
                "<div style='border:1px dashed #000;border-radius:10px;background:#fff;"
                "padding:6px 0;margin-top:-4px;box-shadow:0 4px 16px rgba(0,0,0,0.10);'>"
                "<div style='font-size:0.68rem;color:#64748b;padding:4px 14px 2px;font-weight:700;'>"
                "🔬 질병 선택 (클릭 → KCD 자동 입력)</div>",
                unsafe_allow_html=True,
            )
            for _h in _hits:
                _cov = _kcd_get_coverage(_h.get("kcd", ""))
                _lbl = _cov.get("label", "") if _cov else ""
                _src = "" if _h.get("_source") == "hira" else " 📋"
                _btn = (f"**[{_h['kcd']}]** {_h['name']}{_src}"
                        + (f"  ·  {_lbl}" if _lbl else "")
                        + f"  ·  {_h.get('category', '')}")
                if _st.button(_btn, key=f"kcd_ac_{session_key}_{_h['kcd']}", use_container_width=True):
                    _st.session_state[session_key]              = _h["name"]
                    _st.session_state[autofill_kcd_key]         = _h["kcd"]
                    _st.session_state[f"{session_key}_detail"]  = _h
                    _st.rerun()
            _st.markdown("</div>", unsafe_allow_html=True)
        else:
            _st.markdown(
                "<div style='font-size:0.72rem;color:#94a3b8;padding:2px 6px;'>"
                "질환명/코드 확인 후 다시 검색하세요.</div>",
                unsafe_allow_html=True,
            )
    else:
        if _typed.strip():
            _st.session_state[session_key] = _typed
    _sel     = _st.session_state.get(session_key, "")
    _sel_kcd = _st.session_state.get(autofill_kcd_key, "")
    _sel_det = _st.session_state.get(f"{session_key}_detail", {})
    if show_coverage and _sel and not _is_typing:
        _cov = _kcd_get_coverage(_sel_kcd)
        _bg  = _cov.get("bg",    "#f8fafc") if _cov else "#f8fafc"
        _cl  = _cov.get("color", "#374151") if _cov else "#374151"
        _lbl = _cov.get("label", "")        if _cov else ""
        _hdr = (
            f"<div style='background:{_bg};border:1px dashed #000;border-radius:10px;"
            f"padding:12px 16px;margin-top:6px;'>"
            f"<div style='display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:6px;'>"
            f"<span style='font-size:0.92rem;font-weight:900;color:#000;'>🔬 {_sel}</span>"
        )
        if _lbl:
            _hdr += (
                f"<span style='background:{_cl};color:#fff;border-radius:10px;"
                f"padding:2px 10px;font-size:0.70rem;font-weight:900;'>{_lbl}</span>"
            )
        if _sel_kcd:
            _hdr += f"<span style='font-size:0.78rem;color:#374151;'>KCD: <b>{_sel_kcd}</b></span>"
        _hdr += "</div>"
        _st.markdown(_hdr, unsafe_allow_html=True)
        if _sel_det:
            _en  = _sel_det.get("detail",   "")
            _cat = _sel_det.get("category", "")
            if _en or _cat:
                _parts = ("📋 " + _cat if _cat else "") + (f"&nbsp;·&nbsp;<i>{_en}</i>" if _en else "")
                _st.markdown(
                    f"<div style='font-size:0.75rem;color:#64748b;margin-bottom:6px;'>{_parts}</div>",
                    unsafe_allow_html=True,
                )
        if _cov and _cov.get("coverages"):
            _st.markdown(
                "<div style='font-size:0.76rem;font-weight:700;color:#1565C0;margin-bottom:4px;'>"
                "📊 관련 보장 항목 &amp; 표준 설계 금액</div>",
                unsafe_allow_html=True,
            )
            _rows = [c for c in _cov["coverages"] if "type" in c]
            if _rows:
                _nc   = min(len(_rows), 3)
                _cols = _st.columns(_nc)
                for _ci, _cv in enumerate(_rows[:3]):
                    with _cols[_ci % _nc]:
                        _st.metric(
                            label=_cv["type"],
                            value=f"{_cv['std_rec']:,}{_cv['unit']}",
                            delta=f"최소 {_cv['std_min']:,}{_cv['unit']}",
                            delta_color="off",
                        )
            _note = _cov.get("kcd_notes", "")
            if _note:
                _st.markdown(
                    f"<div style='font-size:0.73rem;color:#374151;background:#f1f5f9;"
                    f"border-radius:6px;padding:6px 10px;margin-top:6px;"
                    f"border-left:3px solid {_cl};'>💡 {_note}</div>",
                    unsafe_allow_html=True,
                )
        _st.markdown("</div>", unsafe_allow_html=True)
        if _st.button("✕ 질병 초기화", key=f"kcd_reset_{session_key}", use_container_width=False):
            for _k in (session_key, autofill_kcd_key, f"{session_key}_detail"):
                _st.session_state.pop(_k, None)
            _st.rerun()
    return _sel


# =====================================================================
# [LAW-API §1] 국가법령정보센터 API 엔진 (OC=goldkey, user=insusite@gmail.com)
# =====================================================================

def _law_get_oc() -> str:
    import os as _os
    try:
        import streamlit as _st
        return _os.environ.get("LAW_API_OC", "") or _st.secrets.get("LAW_API_OC", "goldkey")
    except Exception:
        return _os.environ.get("LAW_API_OC", "goldkey")


_LAW_FALLBACK: list = [
    {"law_id": "001", "title": "보험업법",       "article": "제4조",    "category": "보험규제",   "priority": 1,
     "content": "보험업을 경영하고자 하는 자는 금융위원회의 허가를 받아야 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=226428"},
    {"law_id": "002", "title": "상법(보험편)",   "article": "제638조",  "category": "보험계약",   "priority": 1,
     "content": "보험계약은 당사자 일방이 약정한 보험료를 지급하고 재산 또는 생명이나 신체에 불확정한 사고가 생길 경우에 상대방이 일정한 보험금이나 그 밖의 급여를 지급할 것을 약정함으로써 효력이 생긴다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
    {"law_id": "003", "title": "상법(보험편)",   "article": "제651조",  "category": "고지의무",   "priority": 1,
     "content": "보험계약당시에 보험계약자 또는 피보험자가 고의 또는 중대한 과실로 인하여 중요한 사항을 고지하지 아니하거나 부실의 고지를 한 때에는 보험자는 계약을 해지할 수 있다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
    {"law_id": "004", "title": "상법(보험편)",   "article": "제657조",  "category": "보험사고통지","priority": 1,
     "content": "보험사고가 발생한 때에는 보험계약자 또는 피보험자나 보험수익자는 지체없이 보험자에게 그 통지를 발송하여야 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
    {"law_id": "005", "title": "상법(보험편)",   "article": "제662조",  "category": "소멸시효",   "priority": 1,
     "content": "보험금액의 청구권과 보험료의 반환청구권은 3년간, 보험료청구권은 2년간 행사하지 아니하면 시효의 완성으로 소멸한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
    {"law_id": "006", "title": "보험업법",       "article": "제95조의2","category": "설명의무",   "priority": 1,
     "content": "보험설계사는 보험계약의 체결을 권유하는 때에는 보험계약자에게 보험약관에 기재된 중요한 사항을 설명하여야 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=226428"},
    {"law_id": "007", "title": "개인정보보호법", "article": "제15조",   "category": "개인정보수집","priority": 2,
     "content": "개인정보처리자는 정보주체의 동의를 받은 경우에는 개인정보를 수집할 수 있으며 그 수집 목적의 범위에서 이용할 수 있다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=248408"},
    {"law_id": "008", "title": "금융소비자보호법","article": "제19조",  "category": "금융소비자보호","priority": 1,
     "content": "금융상품판매업자등은 일반금융소비자에게 계약체결을 권유하는 경우 금융상품에 관한 중요한 사항을 이해할 수 있도록 설명하여야 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=232504"},
    {"law_id": "009", "title": "보험업법",       "article": "제102조",  "category": "보험금지급", "priority": 1,
     "content": "보험회사는 보험금의 지급사유가 발생한 때에는 지체없이 지급할 보험금액을 결정하고 그 결정된 날부터 7일 이내에 지급하여야 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=226428"},
    {"law_id": "010", "title": "상법(보험편)",   "article": "제659조",  "category": "면책사유",   "priority": 1,
     "content": "보험사고가 보험계약자 또는 피보험자나 보험수익자의 고의 또는 중대한 과실로 인하여 생긴 때에는 보험자는 보험금액을 지급할 책임이 없다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
    {"law_id": "011", "title": "신용정보법",     "article": "제32조",   "category": "마이데이터동의","priority": 2,
     "content": "신용정보주체는 신용정보회사등에게 본인에 관한 신용정보를 제공하는 행위에 동의하거나 동의를 철회할 수 있다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=244605"},
    {"law_id": "012", "title": "상법(보험편)",   "article": "제732조",  "category": "무효계약",   "priority": 2,
     "content": "15세 미만자, 심신상실자 또는 심신박약자의 사망을 보험사고로 한 보험계약은 무효로 한다.",
     "url": "https://www.law.go.kr/lsInfoP.do?lsiSeq=234364"},
]

_LAW_KCD_LINK: dict = {
    "C":   ["001", "002", "003", "009"],
    "I6":  ["001", "002", "003", "009"],
    "I2":  ["001", "002", "003", "009"],
    "F0":  ["001", "002", "003", "009"],
    "E1":  ["003", "006", "008"],
    "I10": ["003", "006"],
}


def _law_search(query: str, limit: int = 8) -> list:
    """[LAW-API §2] 국가법령정보센터 API → 로컬 폴백."""
    import urllib.request as _req, urllib.parse as _up, json as _json
    _oc = _law_get_oc()
    _results = []
    if _oc and query.strip():
        try:
            _params = _up.urlencode({
                "OC": _oc, "target": "law", "type": "JSON",
                "query": query.strip(), "display": limit,
            })
            _url = "https://www.law.go.kr/DRF/lawSearch.do?" + _params
            _resp = _req.urlopen(_url, timeout=5)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _items = _raw.get("LawSearch", {}).get("law", [])
            if isinstance(_items, dict):
                _items = [_items]
            for _it in _items:
                _lid = str(_it.get("\ubc95\ub839ID", ""))
                _results.append({
                    "law_id":   _lid,
                    "title":    _it.get("\ubc95\ub839\uba85", ""),
                    "article":  "",
                    "content":  _it.get("\ubc95\ub839\uc57d\uce6d\uba85", "") or _it.get("\ubc95\ub839\uba85", ""),
                    "category": _it.get("\ubc95\ub839\uad6c\ubd84\uba85", ""),
                    "url":      f"https://www.law.go.kr/lsInfoP.do?lsiSeq={_lid}",
                    "_source":  "api",
                })
        except Exception:
            pass
    if not _results:
        _q = query.strip().lower()
        _matches = []
        for _r in _LAW_FALLBACK:
            _score = 0
            if _q in _r["title"].lower():    _score += 100
            if _q in _r["article"].lower():  _score += 80
            if _q in _r["content"].lower():  _score += 50
            if _q in _r["category"].lower(): _score += 40
            if _score > 0:
                _matches.append((_score, _r))
        if not _matches:
            _matches = [(0, _r) for _r in _LAW_FALLBACK]
        _matches.sort(key=lambda x: -x[0])
        _results = [{**r, "_source": "local"} for _, r in _matches[:limit]]
    return _results[:limit]


def _law_get_linked(kcd_code: str) -> list:
    """[LAW-API §3] KCD 코드에 연관된 법령 목록 반환."""
    if not kcd_code:
        return []
    _ids: set = set()
    for _p in [kcd_code[:3], kcd_code[:2], kcd_code[:1]]:
        _ids.update(_LAW_KCD_LINK.get(_p, []))
    return [r for r in _LAW_FALLBACK if r["law_id"] in _ids]


def render_law_search(
    session_key: str = "law_search",
    kcd_code: str = "",
    show_linked: bool = True,
) -> None:
    """[LAW-API §4] 법령/판례 실시간 검색 UI 컴포넌트."""
    import streamlit as _st
    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:10px;"
        "background:#fffbeb;padding:10px 14px 8px;margin-bottom:10px;'>"
        "<div style='color:#78350f;font-weight:900;font-size:0.86rem;margin-bottom:6px;'>"
        "⚖️ 법령·판례 실시간 검색 — 국가법령정보센터 연동</div>",
        unsafe_allow_html=True,
    )
    _q = _st.text_input(
        "법령/조문 검색",
        value=_st.session_state.get(f"{session_key}_query", ""),
        placeholder="예) 보험금 청구, 고지의무, 상법 651조, 면책사유…",
        key=f"{session_key}_input",
    )
    if _q.strip():
        _st.session_state[f"{session_key}_query"] = _q

    if show_linked and kcd_code and not _q.strip():
        _linked = _law_get_linked(kcd_code)
        if _linked:
            _st.markdown(
                f"<div style='font-size:0.72rem;color:#0369a1;font-weight:700;margin-bottom:4px;'>"
                f"🔗 KCD [{kcd_code}] 관련 핵심 법령 자동 연결</div>",
                unsafe_allow_html=True,
            )
            for _r in _linked:
                _st.markdown(
                    f"<div style='background:#fff;border:1px solid #fde68a;border-radius:8px;"
                    f"padding:8px 12px;margin-bottom:5px;word-break:keep-all;'>"
                    f"<div style='font-size:0.80rem;font-weight:900;color:#92400e;'>"
                    f"📌 {_r['title']} {_r['article']}</div>"
                    f"<div style='font-size:0.76rem;color:#374151;line-height:1.7;margin-top:3px;'>"
                    f"{_r['content'][:120]}{'...' if len(_r['content'])>120 else ''}</div>"
                    f"<a href='{_r['url']}' target='_blank' style='font-size:0.68rem;"
                    f"color:#2563eb;text-decoration:underline;'>전문 보기 →</a>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    if _q.strip():
        _hits = _law_search(_q, limit=8)
        _src_tag = ("🌐 법령정보센터" if any(h.get("_source") == "api" for h in _hits) else "📋 내장 DB")
        _st.markdown(
            f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:4px;'>"
            f"{_src_tag} 검색 결과 {len(_hits)}건</div>",
            unsafe_allow_html=True,
        )
        _cat_colors = {
            "보험규제": "#dc2626", "보험계약": "#7c3aed", "고지의무": "#b45309",
            "보험금지급": "#15803d", "면책사유": "#ef4444",
        }
        for _r in _hits:
            _cc = _cat_colors.get(_r.get("category", ""), "#374151")
            _article_html = (
                f"<span style='font-size:0.72rem;font-weight:700;color:{_cc};'>"
                f"{_r['article']}</span>" if _r.get("article") else ""
            )
            _cat_html = (
                f"<span style='background:#f1f5f9;color:#64748b;border-radius:8px;"
                f"padding:1px 7px;font-size:0.65rem;font-weight:700;'>{_r['category']}</span>"
                if _r.get("category") else ""
            )
            _st.markdown(
                f"<div style='background:#fff;border:1px dashed #000;border-radius:8px;"
                f"padding:10px 14px;margin-bottom:6px;word-break:keep-all;'>"
                f"<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;'>"
                f"<span style='font-size:0.82rem;font-weight:900;color:#000;'>📌 {_r['title']}</span>"
                f"{_article_html}{_cat_html}</div>"
                f"<div style='font-size:0.78rem;color:#374151;line-height:1.75;'>"
                f"{_r['content'][:200]}{'...' if len(_r['content'])>200 else ''}</div>"
                f"<a href='{_r['url']}' target='_blank' style='font-size:0.68rem;"
                f"color:#2563eb;text-decoration:underline;margin-top:3px;display:inline-block;'>"
                f"전문 보기 →</a></div>",
                unsafe_allow_html=True,
            )
    _st.markdown("</div>", unsafe_allow_html=True)


'''

new_src = src.replace(anchor, INSERT + anchor, 1)
assert new_src != src, "replace had no effect"
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(new_src)
lines = new_src.split('\n')
print(f"OK total lines: {len(lines)}")
print(f"anchor now at line: {[i+1 for i, l in enumerate(lines) if anchor in l]}")
