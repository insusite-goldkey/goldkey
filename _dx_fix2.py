# -*- coding: utf-8 -*-
"""
진단 결과 기반 엔진 수정 v2:
1. _KCD_FALLBACK_DATA 확장 (당뇨/협심증 등 키워드 추가)
2. _hira_disease_search 엔드포인트 교체 (500 오류 수정)
3. _fss_search_products 로컬 전용으로 단순화 (404 오류 제거)
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0 = len(src.split('\n'))
print(f"원본: {n0}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. _KCD_FALLBACK_DATA 확장 — 키워드 필드 추가 + 항목 보강
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_DB = '''_KCD_FALLBACK_DATA: list = [
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
]'''

assert src.count(OLD_DB) == 1, f"OLD_DB count={src.count(OLD_DB)}"

NEW_DB = '''_KCD_FALLBACK_DATA: list = [
    # ── 암 계열 ──
    {"kcd": "C50", "name": "유방암 (유방악성종양)",       "category": "신생물",       "detail": "Malignant neoplasm of breast",         "keywords": ["유방암","암"]},
    {"kcd": "C16", "name": "위암 (위악성종양)",           "category": "신생물",       "detail": "Malignant neoplasm of stomach",        "keywords": ["위암","암"]},
    {"kcd": "C34", "name": "폐암 (기관지및폐악성종양)",   "category": "신생물",       "detail": "Malignant neoplasm of bronchus/lung",  "keywords": ["폐암","암"]},
    {"kcd": "C22", "name": "간암 (간악성종양)",           "category": "신생물",       "detail": "Malignant neoplasm of liver",          "keywords": ["간암","암"]},
    {"kcd": "C73", "name": "갑상선암 (갑상선악성종양)",   "category": "신생물",       "detail": "Malignant neoplasm of thyroid gland",  "keywords": ["갑상선암","갑상샘암","암"]},
    {"kcd": "C61", "name": "전립선암 (전립선악성종양)",   "category": "신생물",       "detail": "Malignant neoplasm of prostate",       "keywords": ["전립선암","암"]},
    {"kcd": "C25", "name": "췌장암 (췌장악성종양)",       "category": "신생물",       "detail": "Malignant neoplasm of pancreas",       "keywords": ["췌장암","암"]},
    {"kcd": "C18", "name": "대장암 (결장악성종양)",       "category": "신생물",       "detail": "Malignant neoplasm of colon",          "keywords": ["대장암","결장암","암"]},
    {"kcd": "C20", "name": "직장암 (직장악성종양)",       "category": "신생물",       "detail": "Malignant neoplasm of rectum",         "keywords": ["직장암","암"]},
    {"kcd": "C53", "name": "자궁경부암",                  "category": "신생물",       "detail": "Malignant neoplasm of cervix uteri",   "keywords": ["자궁경부암","암"]},
    {"kcd": "C80", "name": "부위불명악성종양",            "category": "신생물",       "detail": "Malignant neoplasm NOS",               "keywords": ["암","악성종양"]},
    # ── 뇌혈관 계열 ──
    {"kcd": "I63", "name": "뇌경색증",                    "category": "뇌혈관질환",   "detail": "Cerebral infarction",                  "keywords": ["뇌경색","허혈뇌졸중","뇌졸중","중풍"]},
    {"kcd": "I60", "name": "지주막하출혈",                "category": "뇌혈관질환",   "detail": "Subarachnoid haemorrhage",             "keywords": ["지주막하출혈","뇌출혈","뇌졸중"]},
    {"kcd": "I61", "name": "뇌내출혈",                    "category": "뇌혈관질환",   "detail": "Intracerebral haemorrhage",             "keywords": ["뇌출혈","뇌졸중","출혈성뇌졸중"]},
    {"kcd": "I64", "name": "뇌졸중 (출혈또는경색 미분류)","category": "뇌혈관질환",   "detail": "Stroke NOS",                          "keywords": ["뇌졸중","중풍"]},
    # ── 협심증/심장 계열 ──
    {"kcd": "I20",  "name": "협심증",                     "category": "허혈심장질환", "detail": "Angina pectoris",                      "keywords": ["협심증","가슴통증","흉통"]},
    {"kcd": "I20.0","name": "불안정협심증",               "category": "허혈심장질환", "detail": "Unstable angina",                      "keywords": ["불안정협심증","협심증"]},
    {"kcd": "I20.1","name": "변이형협심증 (경련협심증)",  "category": "허혈심장질환", "detail": "Angina pectoris with documented spasm","keywords": ["변이형협심증","협심증"]},
    {"kcd": "I21",  "name": "급성 심근경색증",            "category": "허혈심장질환", "detail": "Acute myocardial infarction",          "keywords": ["심근경색","급성심근경색","심장마비"]},
    {"kcd": "I25",  "name": "만성 허혈심장질환",          "category": "허혈심장질환", "detail": "Chronic ischaemic heart disease",      "keywords": ["허혈심장","만성협심증","협심증"]},
    {"kcd": "I50",  "name": "심부전",                     "category": "심장질환",     "detail": "Heart failure",                        "keywords": ["심부전","심장기능저하"]},
    # ── 당뇨 계열 ──
    {"kcd": "E11",  "name": "제2형 당뇨병 (인슐린비의존)",  "category": "내분비질환",   "detail": "Type 2 diabetes mellitus",           "keywords": ["당뇨","당뇨병","2형당뇨","성인당뇨"]},
    {"kcd": "E10",  "name": "제1형 당뇨병 (인슐린의존)",    "category": "내분비질환",   "detail": "Type 1 diabetes mellitus",           "keywords": ["당뇨","1형당뇨","소아당뇨","인슐린의존"]},
    {"kcd": "E11.5","name": "제2형 당뇨병성 말초순환합병증","category": "내분비질환",   "detail": "Type 2 DM with peripheral circulation complications","keywords": ["당뇨합병증","당뇨발","당뇨"]},
    {"kcd": "E14",  "name": "상세불명의 당뇨병",           "category": "내분비질환",   "detail": "Unspecified diabetes mellitus",        "keywords": ["당뇨"]},
    # ── 고혈압 ──
    {"kcd": "I10",  "name": "본태성(원발성) 고혈압",       "category": "순환기질환",   "detail": "Essential hypertension",              "keywords": ["고혈압","혈압높음"]},
    {"kcd": "I11",  "name": "고혈압성 심장병",             "category": "순환기질환",   "detail": "Hypertensive heart disease",          "keywords": ["고혈압성심장병","고혈압"]},
    # ── 치매 ──
    {"kcd": "F00",  "name": "알츠하이머병의 치매",         "category": "정신질환",     "detail": "Dementia in Alzheimer disease",        "keywords": ["알츠하이머","치매","알쯔하이머"]},
    {"kcd": "F01",  "name": "혈관성 치매",                 "category": "정신질환",     "detail": "Vascular dementia",                   "keywords": ["혈관치매","치매"]},
    {"kcd": "F03",  "name": "상세불명의 치매",             "category": "정신질환",     "detail": "Unspecified dementia",                "keywords": ["치매"]},
    {"kcd": "G30",  "name": "알츠하이머병",                "category": "신경질환",     "detail": "Alzheimer disease",                   "keywords": ["알츠하이머","치매"]},
    # ── 신장/간/호흡기 ──
    {"kcd": "N18",  "name": "만성신장병",                  "category": "비뇨기질환",   "detail": "Chronic kidney disease",              "keywords": ["만성신부전","신장병","콩팥병","투석"]},
    {"kcd": "K74",  "name": "간섬유증 및 간경변증",        "category": "소화기질환",   "detail": "Fibrosis and cirrhosis of liver",      "keywords": ["간경변","간경화","간섬유증"]},
    {"kcd": "J45",  "name": "천식",                        "category": "호흡기질환",   "detail": "Asthma",                              "keywords": ["천식","기관지천식"]},
    {"kcd": "J44",  "name": "만성 폐쇄성 폐질환(COPD)",   "category": "호흡기질환",   "detail": "Other COPD",                          "keywords": ["copd","만성폐쇄성","폐기종"]},
    # ── 신경/근골격 ──
    {"kcd": "G20",  "name": "파킨슨병",                    "category": "신경질환",     "detail": "Parkinson disease",                   "keywords": ["파킨슨","파킨슨병"]},
    {"kcd": "M05",  "name": "류마티스 관절염",             "category": "근골격질환",   "detail": "Rheumatoid arthritis",                "keywords": ["류마티스관절염","류마티스"]},
    {"kcd": "M54",  "name": "등통증 (요추간판장애)",        "category": "근골격질환",   "detail": "Dorsalgia",                           "keywords": ["허리통증","요통","허리디스크"]},
    # ── 손상 ──
    {"kcd": "S06",  "name": "두개내손상 (뇌진탕)",         "category": "손상",         "detail": "Intracranial injury",                 "keywords": ["두개내손상","뇌진탕","머리외상"]},
    {"kcd": "S72",  "name": "대퇴골 골절 (고관절골절)",   "category": "손상",         "detail": "Fracture of femur",                   "keywords": ["대퇴골골절","고관절골절","넙다리뼈"]},
]'''

assert src.count(OLD_DB) == 1
src = src.replace(OLD_DB, NEW_DB, 1)
print("✓ _KCD_FALLBACK_DATA 확장 (키워드 필드 + 항목 보강)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. _hira_disease_search 교체 — 다중 엔드포인트 + keywords 검색 지원
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_SEARCH_FN = '''def _hira_disease_search(query: str, limit: int = 10) -> list:
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
    return _results[:limit]'''

assert src.count(OLD_SEARCH_FN) == 1, f"count={src.count(OLD_SEARCH_FN)}"

NEW_SEARCH_FN = '''def _hira_disease_search(query: str, limit: int = 10) -> list:
    """[엔진 A] HIRA 질병마스터 검색 — 다중 엔드포인트 + 키워드 강화 로컬 폴백"""
    import urllib.request as _req, urllib.parse as _up, json as _json
    _key = _hira_get_key()
    _q   = query.strip()
    if not _q:
        return []

    # API 시도 (다중 엔드포인트)
    _api_endpoints = [
        ("https://apis.data.go.kr/B551182/msInfrm/getDissInfo",
         {"serviceKey": _key, "numOfRows": str(limit), "pageNo": "1",
          "sickType": "1", "medTp": "1", "searchText": _q, "_type": "json"}),
        ("https://apis.data.go.kr/B551182/diseaseInfoService1/getDiseaseInfo1",
         {"serviceKey": _key, "numOfRows": str(limit), "pageNo": "1",
          "sickType": "1", "medTp": "1", "diseaseType": "SICK_NM", "searchText": _q}),
    ]
    for _base, _params in _api_endpoints:
        try:
            _url  = _base + "?" + _up.urlencode(_params)
            _resp = _req.urlopen(_url, timeout=5)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _items = (_raw.get("response", {}).get("body", {})
                          .get("items", {}) or {})
            if isinstance(_items, dict):
                _items = _items.get("item", [])
            if isinstance(_items, dict):
                _items = [_items]
            if _items:
                return [{"kcd": _it.get("sickCd",""), "name": _it.get("sickNm",""),
                         "category": _it.get("sickCatNm",""),
                         "detail": _it.get("sickEngNm",""), "_source": "hira"}
                        for _it in _items[:limit]]
        except Exception:
            continue

    # 로컬 폴백 — 이름 + keywords + KCD코드 + 카테고리 다중 매칭
    _ql = _q.lower()
    _results = []
    for _r in _KCD_FALLBACK_DATA:
        _kws = _r.get("keywords", [])
        if (
            _ql in _r["name"].lower()
            or _ql in _r["kcd"].lower()
            or _ql in _r.get("detail","").lower()
            or _ql in _r["category"].lower()
            or any(_ql in kw.lower() for kw in _kws)
        ):
            _results.append({**_r, "_source": "local"})
        if len(_results) >= limit:
            break
    return _results[:limit]'''

src = src.replace(OLD_SEARCH_FN, NEW_SEARCH_FN, 1)
print("✓ _hira_disease_search 교체 (키워드 매칭 + 다중 엔드포인트)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. _fss_search_products — API 시도 제거, 로컬 전용으로 단순화
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_FSS_FN_MARKER = 'def _fss_search_products(kcd_code: str = "", gap_coverages: list = None, limit: int = 4) -> list:'
lines = src.split('\n')
fss_start = next(i for i, l in enumerate(lines) if OLD_FSS_FN_MARKER in l)
fss_end   = next(i for i in range(fss_start + 1, len(lines)) if lines[i].startswith('def '))
old_fss = '\n'.join(lines[fss_start:fss_end])
print(f"FSS fn: {fss_start+1}~{fss_end}")

NEW_FSS_FN = '''def _fss_search_products(kcd_code: str = "", gap_coverages: list = None, limit: int = 4) -> list:
    """[엔진 E] 금감원 비교 상품 — 로컬 DB 스코어링 (FSS API 404 우회)"""
    if gap_coverages is None:
        gap_coverages = []
    _gap_name_map = {
        "cancer": "암", "stroke": "뇌", "heart": "심장",
        "dementia": "치매", "lci": "간병", "hospitalize": "입원",
        "surgery": "수술", "disability": "장해", "accident": "상해",
        "death": "사망", "annuity": "연금",
    }
    _scored = []
    for _p in _FSS_PRODUCT_FALLBACK:
        _s = _p["score"]
        if kcd_code:
            for _tk in _p["target_kcd"]:
                if kcd_code.upper().startswith(_tk.upper()):
                    _s += 30
                    break
        for _gap in gap_coverages:
            _gn = _gap_name_map.get(_gap, _gap)
            if any(_gn in cv for cv in _p["coverages"]):
                _s += 15
        _scored.append((_s, _p))
    _scored.sort(key=lambda x: -x[0])
    return [{**p, "score": s, "_source": "local"} for s, p in _scored[:limit]]'''

src = src.replace(old_fss, NEW_FSS_FN, 1)
print("✓ _fss_search_products 로컬 전용으로 단순화")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
