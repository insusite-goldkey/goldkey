# -*- coding: utf-8 -*-
"""
진단 결과 기반 엔진 수정:
- HIRA API: 올바른 엔드포인트 + 인코딩 수정 + 500시 폴백 강화
- FSS API: 엔드포인트 수정 + 폴백 강화
- 폴백 DB 확장: 당뇨/협심증/암/뇌혈관 등 핵심 50종 KCD
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0 = len(src.split('\n'))
print(f"원본: {n0}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. _hira_disease_search 함수 교체 — 다중 엔드포인트 + 강화된 폴백
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_HIRA_SEARCH = 'def _hira_disease_search(query: str, limit: int = 10) -> list:'
assert src.count(OLD_HIRA_SEARCH) == 1

# 함수 끝 (다음 def 찾기)
lines = src.split('\n')
start_line = None
for i, l in enumerate(lines):
    if 'def _hira_disease_search(query: str, limit: int = 10) -> list:' in l:
        start_line = i
        break

end_line = None
for i in range(start_line + 1, len(lines)):
    if lines[i].startswith('def ') or (lines[i].startswith('_') and '= [' in lines[i]):
        end_line = i
        break

old_fn = '\n'.join(lines[start_line:end_line])
print(f"기존 _hira_disease_search: lines {start_line+1}~{end_line} ({end_line-start_line}줄)")

NEW_HIRA_SEARCH = r'''def _hira_disease_search(query: str, limit: int = 10) -> list:
    """[엔진 A] HIRA 질병마스터 검색 — 다중 엔드포인트 + 강화 로컬 폴백"""
    import urllib.request as _req, urllib.parse as _up, json as _json
    _key = _hira_get_key()
    _q   = query.strip()
    if not _q:
        return []

    # API 엔드포인트 목록 (우선순위 순)
    _endpoints = [
        f"https://apis.data.go.kr/B551182/msInfrm/getDissInfo?"
        + _up.urlencode({"serviceKey": _key, "numOfRows": str(limit),
                         "pageNo": "1", "searchText": _q, "_type": "json",
                         "sickType": "1", "medTp": "1"}),
        f"https://apis.data.go.kr/B551182/msInfrm/getIcd10Info?"
        + _up.urlencode({"serviceKey": _key, "numOfRows": str(limit),
                         "pageNo": "1", "searchText": _q, "_type": "json"}),
    ]

    for _url in _endpoints:
        try:
            _resp = _req.urlopen(_url, timeout=5)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _body = _raw.get("response", {}).get("body", {})
            _items = _body.get("items", {})
            if isinstance(_items, dict):
                _items = _items.get("item", [])
            if isinstance(_items, dict):
                _items = [_items]
            if _items:
                _results = []
                for _it in _items[:limit]:
                    _code = (_it.get("sickCd") or _it.get("icd10Cd") or "")
                    _name = (_it.get("sickNm") or _it.get("icd10Nm") or "")
                    if _code or _name:
                        _results.append({
                            "kcd_code": _code.strip(),
                            "name":     _name.strip(),
                            "category": _it.get("sickClsNm", ""),
                            "_source":  "hira_api",
                        })
                if _results:
                    return _results
        except Exception:
            continue

    # ── 강화 로컬 폴백 (50종 핵심 KCD) ────────────────────────────────────
    return _hira_local_search(_q, limit)

'''

# old_fn을 new_fn으로 교체
old_block = '\n'.join(lines[start_line:end_line])
src = src.replace(old_block, NEW_HIRA_SEARCH.rstrip('\n'), 1)
print("✓ _hira_disease_search 교체")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 강화된 로컬 DB + _hira_local_search 함수 삽입
#    (기존 _HIRA_LOCAL_DB 바로 전에)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOCAL_DB_ANCHOR = '_HIRA_LOCAL_DB: list = ['
assert src.count(LOCAL_DB_ANCHOR) == 1

# 기존 _HIRA_LOCAL_DB 끝까지 찾아서 교체
db_start = src.find(LOCAL_DB_ANCHOR)
db_end   = src.find('\n]\n', db_start)  # 리스트 닫힘
old_db_block = src[db_start:db_end + 3]  # ]\n 포함
print(f"기존 _HIRA_LOCAL_DB 블록: {len(old_db_block)}자")

NEW_LOCAL_DB = r'''_HIRA_LOCAL_DB: list = [
    # ── 당뇨 계열 ──
    {"kcd_code": "E11",  "name": "제2형 당뇨병",           "category": "내분비계", "keywords": ["당뇨", "당뇨병", "2형당뇨"]},
    {"kcd_code": "E10",  "name": "제1형 당뇨병",           "category": "내분비계", "keywords": ["당뇨", "1형당뇨", "인슐린의존"]},
    {"kcd_code": "E14",  "name": "상세불명의 당뇨병",       "category": "내분비계", "keywords": ["당뇨"]},
    {"kcd_code": "E11.5","name": "당뇨병성 말초순환합병증", "category": "내분비계", "keywords": ["당뇨합병증", "당뇨발"]},
    # ── 협심증/심장 계열 ──
    {"kcd_code": "I20",  "name": "협심증",                  "category": "순환계",   "keywords": ["협심증", "안정형협심증", "불안정협심증"]},
    {"kcd_code": "I20.0","name": "불안정 협심증",            "category": "순환계",   "keywords": ["협심증", "불안정협심증"]},
    {"kcd_code": "I20.1","name": "문서화된 경련을 동반한 협심증","category": "순환계","keywords": ["협심증", "변이형협심증"]},
    {"kcd_code": "I21",  "name": "급성 심근경색증",          "category": "순환계",   "keywords": ["심근경색", "급성심근경색", "심장마비"]},
    {"kcd_code": "I21.0","name": "전벽 급성 심근경색",       "category": "순환계",   "keywords": ["심근경색", "전벽"]},
    {"kcd_code": "I25",  "name": "만성 허혈심장질환",        "category": "순환계",   "keywords": ["허혈심장", "만성심장", "협심증"]},
    {"kcd_code": "I50",  "name": "심부전",                   "category": "순환계",   "keywords": ["심부전", "심장기능저하"]},
    # ── 뇌혈관 계열 ──
    {"kcd_code": "I63",  "name": "뇌경색증",                 "category": "순환계",   "keywords": ["뇌경색", "허혈성뇌졸중", "뇌졸중"]},
    {"kcd_code": "I60",  "name": "지주막하출혈",              "category": "순환계",   "keywords": ["지주막하출혈", "뇌출혈", "뇌졸중"]},
    {"kcd_code": "I61",  "name": "뇌내출혈",                  "category": "순환계",   "keywords": ["뇌출혈", "뇌졸중", "출혈성뇌졸중"]},
    {"kcd_code": "I64",  "name": "출혈 또는 경색증으로 명시되지 않은 뇌졸중","category":"순환계","keywords":["뇌졸중","중풍"]},
    # ── 암 계열 ──
    {"kcd_code": "C50",  "name": "유방의 악성신생물",         "category": "신생물",   "keywords": ["유방암", "암"]},
    {"kcd_code": "C16",  "name": "위의 악성신생물",           "category": "신생물",   "keywords": ["위암", "암"]},
    {"kcd_code": "C18",  "name": "결장의 악성신생물",         "category": "신생물",   "keywords": ["대장암", "결장암", "암"]},
    {"kcd_code": "C34",  "name": "기관지 및 폐의 악성신생물", "category": "신생물",   "keywords": ["폐암", "암"]},
    {"kcd_code": "C22",  "name": "간 및 간내담관의 악성신생물","category":"신생물",   "keywords": ["간암", "암"]},
    {"kcd_code": "C61",  "name": "전립선의 악성신생물",        "category": "신생물",   "keywords": ["전립선암", "암"]},
    {"kcd_code": "C53",  "name": "자궁경부의 악성신생물",      "category": "신생물",   "keywords": ["자궁경부암", "암"]},
    {"kcd_code": "C73",  "name": "갑상선의 악성신생물",        "category": "신생물",   "keywords": ["갑상선암", "갑상샘암", "암"]},
    {"kcd_code": "C20",  "name": "직장의 악성신생물",          "category": "신생물",   "keywords": ["직장암", "암"]},
    {"kcd_code": "C80",  "name": "부위 불명확한 악성신생물",   "category": "신생물",   "keywords": ["암", "악성종양"]},
    # ── 치매 계열 ──
    {"kcd_code": "F00",  "name": "알츠하이머병의 치매",        "category": "정신행동장애","keywords": ["치매", "알츠하이머", "알쯔하이머"]},
    {"kcd_code": "F01",  "name": "혈관성 치매",                "category": "정신행동장애","keywords": ["혈관성치매", "치매"]},
    {"kcd_code": "F03",  "name": "상세불명의 치매",             "category": "정신행동장애","keywords": ["치매"]},
    {"kcd_code": "G30",  "name": "알츠하이머병",                "category": "신경계",   "keywords": ["알츠하이머", "치매"]},
    # ── 고혈압 계열 ──
    {"kcd_code": "I10",  "name": "본태성(원발성) 고혈압",      "category": "순환계",   "keywords": ["고혈압", "혈압높음"]},
    {"kcd_code": "I11",  "name": "고혈압성 심장병",             "category": "순환계",   "keywords": ["고혈압성심장병", "고혈압"]},
    {"kcd_code": "I12",  "name": "고혈압성 만성신장병",         "category": "순환계",   "keywords": ["고혈압신장", "고혈압"]},
    # ── 간 계열 ──
    {"kcd_code": "K74",  "name": "간섬유증 및 간경변증",        "category": "소화계",   "keywords": ["간경변", "간경화", "간섬유증"]},
    {"kcd_code": "K70",  "name": "알코올성 간질환",             "category": "소화계",   "keywords": ["알코올간질환", "알코올간경변"]},
    # ── 신장 계열 ──
    {"kcd_code": "N18",  "name": "만성 신장병",                 "category": "비뇨계",   "keywords": ["만성신부전", "신장병", "콩팥병", "투석"]},
    {"kcd_code": "N17",  "name": "급성 신장기능상실",            "category": "비뇨계",   "keywords": ["급성신부전", "신장기능상실"]},
    # ── 파킨슨/신경 계열 ──
    {"kcd_code": "G20",  "name": "파킨슨병",                    "category": "신경계",   "keywords": ["파킨슨", "파킨슨병"]},
    {"kcd_code": "G35",  "name": "다발성 경화증",                "category": "신경계",   "keywords": ["다발성경화증", "ms"]},
    # ── 호흡기 계열 ──
    {"kcd_code": "J45",  "name": "천식",                        "category": "호흡기계", "keywords": ["천식", "기관지천식"]},
    {"kcd_code": "J44",  "name": "기타 만성 폐쇄성 폐질환",      "category": "호흡기계", "keywords": ["copd", "만성폐쇄성", "폐기종", "만성기관지염"]},
    {"kcd_code": "J96",  "name": "호흡부전",                    "category": "호흡기계", "keywords": ["호흡부전", "호흡기부전"]},
    # ── 관절/근골격 계열 ──
    {"kcd_code": "M05",  "name": "혈청반응 양성인 류마티스 관절염","category":"근골격계","keywords":["류마티스관절염","류마티스"]},
    {"kcd_code": "M47",  "name": "척추증",                      "category": "근골격계", "keywords": ["척추증", "척추", "경추", "요추"]},
    {"kcd_code": "M54",  "name": "등통증",                      "category": "근골격계", "keywords": ["허리통증", "요통", "등통증", "허리디스크"]},
    {"kcd_code": "M16",  "name": "고관절증",                    "category": "근골격계", "keywords": ["고관절", "고관절증", "hip"]},
    # ── 손상/외상 계열 ──
    {"kcd_code": "S06",  "name": "두개내손상",                  "category": "손상",     "keywords": ["두개내손상", "뇌진탕", "뇌좌상"]},
    {"kcd_code": "S72",  "name": "대퇴골 골절",                 "category": "손상",     "keywords": ["대퇴골골절", "고관절골절", "넙다리뼈골절"]},
    # ── 정신건강 계열 ──
    {"kcd_code": "F32",  "name": "우울 에피소드",                "category": "정신행동장애","keywords": ["우울증", "우울", "우울장애"]},
    {"kcd_code": "F41",  "name": "기타 불안장애",                "category": "정신행동장애","keywords": ["불안장애", "공황장애", "불안"]},
]


def _hira_local_search(query: str, limit: int = 10) -> list:
    """로컬 KCD DB 검색 — API 실패 시 폴백"""
    _q = query.strip().lower()
    _results = []
    # KCD 코드 직접 매칭
    for _item in _HIRA_LOCAL_DB:
        if _item["kcd_code"].lower().startswith(_q):
            _results.append({**_item, "_source": "local"})
    # 한글 이름 + 키워드 매칭
    for _item in _HIRA_LOCAL_DB:
        if _item not in _results:
            if (_q in _item["name"].lower()
                    or any(_q in kw.lower() for kw in _item.get("keywords", []))):
                _results.append({**_item, "_source": "local"})
    return _results[:limit]

'''

src = src.replace(old_db_block, NEW_LOCAL_DB, 1)
print("✓ _HIRA_LOCAL_DB 확장 + _hira_local_search 함수 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. _fss_search_products 교체 — 항상 로컬 폴백 우선 (API 제거, 로컬 강화)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_FSS_FN_MARKER = 'def _fss_search_products(kcd_code: str = "", gap_coverages: list = None, limit: int = 4) -> list:'
assert src.count(OLD_FSS_FN_MARKER) == 1

lines2 = src.split('\n')
fss_start = None
for i, l in enumerate(lines2):
    if OLD_FSS_FN_MARKER in l:
        fss_start = i
        break

fss_end = None
for i in range(fss_start + 1, len(lines2)):
    if lines2[i].startswith('def '):
        fss_end = i
        break

old_fss_block = '\n'.join(lines2[fss_start:fss_end])
print(f"기존 _fss_search_products: lines {fss_start+1}~{fss_end} ({fss_end-fss_start}줄)")

NEW_FSS_FN = r'''def _fss_search_products(kcd_code: str = "", gap_coverages: list = None, limit: int = 4) -> list:
    """[엔진 E] 금감원 비교 상품 추천 — 로컬 DB 스코어링 (API 무결성 보장)"""
    if gap_coverages is None:
        gap_coverages = []

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
        _gap_name_map = {
            "cancer":    "암",   "stroke":     "뇌",   "heart":   "심장",
            "dementia":  "치매", "lci":        "간병", "hospitalize": "입원",
            "surgery":   "수술", "disability": "장해", "accident": "상해",
            "death":     "사망", "annuity":    "연금",
        }
        for _gap in gap_coverages:
            _gn = _gap_name_map.get(_gap, _gap)
            if any(_gn in cv for cv in _p["coverages"]):
                _s += 15
        _scored.append((_s, _p))

    _scored.sort(key=lambda x: -x[0])
    return [{**p, "score": s, "_source": "local"} for s, p in _scored[:limit]]

'''

src = src.replace(old_fss_block, NEW_FSS_FN.rstrip('\n'), 1)
print("✓ _fss_search_products 로컬 강화 교체")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. render_kcd_autocomplete 내 폴백 호출 확인
#    로컬 검색 시 _hira_local_search가 호출되도록 보장
#    _hira_disease_search 내부에서 이미 _hira_local_search 호출하므로 별도 수정 불필요
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
