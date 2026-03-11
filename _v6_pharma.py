# -*- coding: utf-8 -*-
"""
[V6-PHARMA] 약제 정보 기반 질병 역추적 엔진
1. [엔진 G] 심평원 약가 API + 로컬 폴백 DB (50종)
2. 약제 → KCD 역추적 매핑
3. render_pharma_panel() UI (알약 카드 + 급여/비급여 + 약관 시너지)
4. GK-RISK 6탭 → 7탭 확장
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0 = len(src.split('\n'))
print(f"원본: {n0}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. 엔진 G 전체 코드 — _loss_ins_search 앞에 삽입
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINE_G_ANCHOR = 'def _loss_ins_search(query: str = "", generation: int = 0) -> list:'
assert src.count(ENGINE_G_ANCHOR) == 1

ENGINE_G = '''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [엔진 G] 심평원 약가 정보 + 질병 역추적 엔진
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── 50종 대표 약제 로컬 DB ───────────────────────────────────────────────────
_PHARMA_LOCAL_DB: list = [
    # 당뇨
    {"code": "645202ATB", "name": "메트포르민염산염", "brand": "글루코파지",
     "ingredient": "Metformin HCl", "category": "혈당강하제", "edi": "급여",
     "signal": "당뇨", "kcd": ["E11", "E10", "E14"],
     "alert": None, "keywords": ["메트포르민", "글루코파지", "당뇨약", "혈당"]},
    {"code": "645801ATB", "name": "글리메피리드", "brand": "아마릴",
     "ingredient": "Glimepiride", "category": "혈당강하제(설포닐우레아)", "edi": "급여",
     "signal": "당뇨", "kcd": ["E11", "E14"],
     "alert": None, "keywords": ["글리메피리드", "아마릴", "당뇨약"]},
    {"code": "A11DA00", "name": "시타글립틴", "brand": "자누비아",
     "ingredient": "Sitagliptin", "category": "혈당강하제(DPP-4억제제)", "edi": "급여",
     "signal": "당뇨", "kcd": ["E11", "E14"],
     "alert": None, "keywords": ["시타글립틴", "자누비아", "당뇨"]},
    {"code": "A10BK01", "name": "엠파글리플로진", "brand": "자디앙",
     "ingredient": "Empagliflozin", "category": "혈당강하제(SGLT-2억제제)", "edi": "급여",
     "signal": "당뇨/심부전", "kcd": ["E11", "I50"],
     "alert": None, "keywords": ["엠파글리플로진", "자디앙", "당뇨", "sglt2"]},
    {"code": "A10BJ01", "name": "리라글루티드", "brand": "빅토자",
     "ingredient": "Liraglutide", "category": "혈당강하제(GLP-1)", "edi": "급여",
     "signal": "당뇨/비만", "kcd": ["E11", "E66"],
     "alert": None, "keywords": ["리라글루티드", "빅토자", "ozempic", "glp1"]},
    # 고혈압
    {"code": "C09AA01", "name": "카프토프릴", "brand": "카포텐",
     "ingredient": "Captopril", "category": "ACE억제제(고혈압)", "edi": "급여",
     "signal": "고혈압", "kcd": ["I10", "I11"],
     "alert": None, "keywords": ["카프토프릴", "ace억제제", "고혈압약"]},
    {"code": "C09CA01", "name": "로사르탄칼륨", "brand": "코자",
     "ingredient": "Losartan K", "category": "ARB(고혈압)", "edi": "급여",
     "signal": "고혈압", "kcd": ["I10", "I12"],
     "alert": None, "keywords": ["로사르탄", "코자", "고혈압", "arb"]},
    {"code": "C08CA01", "name": "암로디핀베실산염", "brand": "노바스크",
     "ingredient": "Amlodipine besylate", "category": "칼슘채널차단제", "edi": "급여",
     "signal": "고혈압/협심증", "kcd": ["I10", "I20"],
     "alert": None, "keywords": ["암로디핀", "노바스크", "고혈압", "협심증"]},
    # 협심증/심장
    {"code": "C01DA02", "name": "니트로글리세린", "brand": "니트로민",
     "ingredient": "Nitroglycerin", "category": "혈관확장제(협심증)", "edi": "급여",
     "signal": "협심증", "kcd": ["I20", "I20.0"],
     "alert": None, "keywords": ["니트로글리세린", "협심증", "흉통"]},
    {"code": "B01AC06", "name": "아스피린(저용량)", "brand": "아스피린프로텍트",
     "ingredient": "Acetylsalicylic acid", "category": "항혈소판제", "edi": "급여",
     "signal": "심근경색/협심증/뇌졸중", "kcd": ["I21", "I20", "I63"],
     "alert": None, "keywords": ["아스피린", "항혈소판", "심장", "뇌졸중"]},
    {"code": "C10AA01", "name": "심바스타틴", "brand": "조코",
     "ingredient": "Simvastatin", "category": "스타틴(고지혈증)", "edi": "급여",
     "signal": "고지혈증/심장", "kcd": ["E78", "I25"],
     "alert": None, "keywords": ["심바스타틴", "스타틴", "고지혈증", "콜레스테롤"]},
    {"code": "C10AA05", "name": "아토르바스타틴", "brand": "리피토",
     "ingredient": "Atorvastatin", "category": "스타틴(고지혈증)", "edi": "급여",
     "signal": "고지혈증/심장", "kcd": ["E78", "I25"],
     "alert": None, "keywords": ["아토르바스타틴", "리피토", "고지혈증"]},
    # 항암제 — alert 발동
    {"code": "L01BC02", "name": "플루오로우라실(5-FU)", "brand": "플루오로우라실주",
     "ingredient": "Fluorouracil", "category": "항암제(대사길항제)", "edi": "급여",
     "signal": "암(대장/위/췌장)", "kcd": ["C18", "C16", "C25"],
     "alert": "chemo", "keywords": ["5-fu", "플루오로우라실", "항암", "항암제"]},
    {"code": "L01XE01", "name": "이마티닙", "brand": "글리벡",
     "ingredient": "Imatinib", "category": "항암제(표적치료제)", "edi": "급여",
     "signal": "만성골수성백혈병/위장관기질종양", "kcd": ["C91", "C49"],
     "alert": "chemo", "keywords": ["이마티닙", "글리벡", "표적항암", "백혈병"]},
    {"code": "L01XC03", "name": "트라스투주맙", "brand": "허셉틴",
     "ingredient": "Trastuzumab", "category": "항암제(HER2표적)", "edi": "급여",
     "signal": "유방암(HER2양성)/위암", "kcd": ["C50", "C16"],
     "alert": "chemo", "keywords": ["트라스투주맙", "허셉틴", "유방암", "her2"]},
    {"code": "L01XX05", "name": "히드록시우레아", "brand": "하이드레아",
     "ingredient": "Hydroxycarbamide", "category": "항암제", "edi": "급여",
     "signal": "백혈병/골수증식", "kcd": ["C91", "C92"],
     "alert": "chemo", "keywords": ["히드록시우레아", "하이드레아", "항암"]},
    {"code": "L01BA01", "name": "메토트렉세이트", "brand": "메토트렉세이트",
     "ingredient": "Methotrexate", "category": "항암제/면역억제제", "edi": "급여",
     "signal": "암/류마티스관절염", "kcd": ["C91", "M05"],
     "alert": "chemo", "keywords": ["메토트렉세이트", "mtx", "항암", "류마티스"]},
    # 희귀난치성
    {"code": "N07XX02", "name": "릴루졸", "brand": "릴루텍",
     "ingredient": "Riluzole", "category": "희귀난치성(ALS)", "edi": "급여",
     "signal": "근위축성측삭경화증(루게릭)", "kcd": ["G12.2"],
     "alert": "rare", "keywords": ["릴루졸", "als", "루게릭", "희귀"]},
    {"code": "A16AX01", "name": "이미글루세라제", "brand": "세레자임",
     "ingredient": "Imiglucerase", "category": "희귀난치성(고셔병)", "edi": "급여",
     "signal": "고셔병(희귀)", "kcd": ["E75.2"],
     "alert": "rare", "keywords": ["이미글루세라제", "세레자임", "고셔", "희귀"]},
    {"code": "L04AB04", "name": "아달리무맙", "brand": "휴미라",
     "ingredient": "Adalimumab", "category": "TNF억제제(희귀/자가면역)", "edi": "급여",
     "signal": "류마티스관절염/크론병/강직성척추염", "kcd": ["M05", "K50", "M45"],
     "alert": "rare", "keywords": ["아달리무맙", "휴미라", "tnf", "류마티스", "크론"]},
    # 치매/신경
    {"code": "N06DA02", "name": "도네페질", "brand": "아리셉트",
     "ingredient": "Donepezil", "category": "치매치료제(AChE억제제)", "edi": "급여",
     "signal": "치매(알츠하이머)", "kcd": ["F00", "G30"],
     "alert": None, "keywords": ["도네페질", "아리셉트", "치매", "알츠하이머"]},
    {"code": "N06DA04", "name": "갈란타민", "brand": "레미닐",
     "ingredient": "Galantamine", "category": "치매치료제", "edi": "급여",
     "signal": "치매", "kcd": ["F00", "F01"],
     "alert": None, "keywords": ["갈란타민", "레미닐", "치매"]},
    {"code": "N04BB01", "name": "아만타딘", "brand": "피케이멜츠",
     "ingredient": "Amantadine", "category": "파킨슨치료제", "edi": "급여",
     "signal": "파킨슨병", "kcd": ["G20"],
     "alert": None, "keywords": ["아만타딘", "파킨슨", "피케이멜츠"]},
    {"code": "N04BA02", "name": "레보도파/카르비도파", "brand": "시네메트",
     "ingredient": "Levodopa+Carbidopa", "category": "파킨슨치료제", "edi": "급여",
     "signal": "파킨슨병", "kcd": ["G20"],
     "alert": None, "keywords": ["레보도파", "시네메트", "파킨슨"]},
    # 호흡기
    {"code": "R03AC02", "name": "살부타몰", "brand": "벤토린",
     "ingredient": "Salbutamol", "category": "기관지확장제(천식/COPD)", "edi": "급여",
     "signal": "천식/COPD", "kcd": ["J45", "J44"],
     "alert": None, "keywords": ["살부타몰", "벤토린", "천식", "흡입기"]},
    {"code": "R03BA02", "name": "부데소니드", "brand": "풀미코트",
     "ingredient": "Budesonide", "category": "흡입스테로이드(천식)", "edi": "급여",
     "signal": "천식", "kcd": ["J45"],
     "alert": None, "keywords": ["부데소니드", "풀미코트", "천식"]},
    # 신장/간
    {"code": "B03BA01", "name": "에포에틴알파", "brand": "에포카인",
     "ingredient": "Epoetin alfa", "category": "조혈제(빈혈/만성신부전)", "edi": "급여",
     "signal": "만성신부전", "kcd": ["N18"],
     "alert": None, "keywords": ["에포에틴", "에포카인", "빈혈", "신부전"]},
    {"code": "A05BA03", "name": "실리마린", "brand": "레가론",
     "ingredient": "Silymarin", "category": "간보호제", "edi": "비급여",
     "signal": "간질환", "kcd": ["K74", "K70"],
     "alert": None, "keywords": ["실리마린", "레가론", "간", "간보호"]},
    # 통증/근골격
    {"code": "M01AB05", "name": "디클로페낙나트륨", "brand": "볼타렌",
     "ingredient": "Diclofenac Na", "category": "비스테로이드소염제(NSAIDs)", "edi": "급여",
     "signal": "관절염/통증", "kcd": ["M05", "M47", "M54"],
     "alert": None, "keywords": ["디클로페낙", "볼타렌", "소염제", "관절"]},
    {"code": "M01AH01", "name": "셀레콕시브", "brand": "쎄레브렉스",
     "ingredient": "Celecoxib", "category": "COX-2억제제(관절염)", "edi": "급여",
     "signal": "관절염", "kcd": ["M05", "M47"],
     "alert": None, "keywords": ["셀레콕시브", "쎄레브렉스", "관절염"]},
    # 정신건강
    {"code": "N06AB06", "name": "세르트랄린", "brand": "졸로푸트",
     "ingredient": "Sertraline", "category": "SSRI(우울증/불안)", "edi": "급여",
     "signal": "우울증/불안장애", "kcd": ["F32", "F41"],
     "alert": None, "keywords": ["세르트랄린", "졸로푸트", "우울증", "ssri"]},
    {"code": "N05AH02", "name": "클로자핀", "brand": "클로자릴",
     "ingredient": "Clozapine", "category": "비정형항정신병약", "edi": "급여",
     "signal": "조현병", "kcd": ["F20"],
     "alert": None, "keywords": ["클로자핀", "클로자릴", "조현병"]},
    # 갑상선
    {"code": "H03AA01", "name": "레보티록신나트륨", "brand": "씬지록신",
     "ingredient": "Levothyroxine Na", "category": "갑상선호르몬", "edi": "급여",
     "signal": "갑상선기능저하증/갑상선암수술후", "kcd": ["E03", "C73"],
     "alert": None, "keywords": ["레보티록신", "씬지록신", "갑상선"]},
    # 항응고/혈전
    {"code": "B01AF02", "name": "리바록사반", "brand": "자렐토",
     "ingredient": "Rivaroxaban", "category": "항응고제(NOAC)", "edi": "급여",
     "signal": "심방세동/혈전", "kcd": ["I48", "I26"],
     "alert": None, "keywords": ["리바록사반", "자렐토", "항응고", "혈전"]},
    {"code": "B01AE07", "name": "다비가트란", "brand": "프라닥사",
     "ingredient": "Dabigatran", "category": "항응고제(NOAC)", "edi": "급여",
     "signal": "심방세동/혈전", "kcd": ["I48"],
     "alert": None, "keywords": ["다비가트란", "프라닥사", "항응고"]},
    # 비급여 대표
    {"code": "N/A-01", "name": "비타민D3(고용량)", "brand": "디-비오",
     "ingredient": "Cholecalciferol", "category": "영양제/비타민", "edi": "비급여",
     "signal": "골다공증/골연화증", "kcd": ["M81", "M83"],
     "alert": None, "keywords": ["비타민d", "비타민d3", "골다공증", "뼈"]},
    {"code": "N/A-02", "name": "오메가3(고순도)", "brand": "오마코",
     "ingredient": "Omega-3 FA ethyl esters", "category": "고지혈증치료제", "edi": "급여",
     "signal": "고중성지방혈증", "kcd": ["E78"],
     "alert": None, "keywords": ["오메가3", "오마코", "중성지방", "고지혈증"]},
]

# ── 알림 등급별 약관 시너지 메시지 ──────────────────────────────────────────
_PHARMA_ALERT_INFO: dict = {
    "chemo": {
        "title": "🎗️ 항암제 감지 — 암보험 특약 자동 조회",
        "color": "#dc2626", "bg": "#fef2f2",
        "law": "보험업법 제95조의2 / 상법(보험편) 제638조",
        "desc": (
            "항암제 복용이 확인되었습니다. 다음 특약의 보장 공백을 즉시 점검하세요:\n"
            "• 암 진단비 (특정암/소액암 구분 확인)\n"
            "• 항암 방사선·약물치료비 특약\n"
            "• 암 수술비 / 암 입원일당\n"
            "• 비급여 항암치료비 보장 특약 (신약·표적치료)"
        ),
        "policy_hint": "PDF 약관 분석기 → '항암치료비' 키워드 검색 권고",
    },
    "rare": {
        "title": "🔬 희귀난치성 약제 감지 — 특약 긴급 점검",
        "color": "#7c3aed", "bg": "#fdf4ff",
        "law": "보험업법 제102조 / 희귀질환관리법 제12조",
        "desc": (
            "희귀난치성 질환 치료제가 감지되었습니다. 다음을 즉시 확인하세요:\n"
            "• 희귀질환 입원·수술 특약 보장 여부\n"
            "• 중증질환(산정특례) 진단비 특약\n"
            "• 간병인 지원 및 장기간병(LCI) 특약\n"
            "• 실손보험 급여/비급여 본인부담금 한도"
        ),
        "policy_hint": "PDF 약관 분석기 → '희귀질환' / '산정특례' 키워드 검색 권고",
    },
}

# ── 약제 → KCD 역추적 매핑 ──────────────────────────────────────────────────
def _pharma_to_kcd(drug: dict) -> list:
    """약제 dict에서 KCD 목록 반환 + 보장 매핑"""
    return drug.get("kcd", [])


def _pharma_local_search(query: str, limit: int = 8) -> list:
    """로컬 약제 DB 검색"""
    _ql = query.strip().lower()
    if not _ql:
        return []
    _results = []
    for _d in _PHARMA_LOCAL_DB:
        if (
            _ql in _d["name"].lower()
            or _ql in _d.get("brand", "").lower()
            or _ql in _d.get("ingredient", "").lower()
            or any(_ql in kw.lower() for kw in _d.get("keywords", []))
        ):
            _results.append({**_d, "_source": "local"})
        if len(_results) >= limit:
            break
    return _results


def _pharma_search(query: str, limit: int = 8) -> list:
    """[엔진 G §1] 심평원 약가 API → 로컬 폴백"""
    import urllib.request as _req, urllib.parse as _up, json as _json
    _key = _hira_get_key()
    _q   = query.strip()
    if not _q:
        return []

    # 심평원 약가 API 시도
    _api_endpoints = [
        ("https://apis.data.go.kr/B551182/msInfrm/getDrugsInfo",
         {"serviceKey": _key, "numOfRows": str(limit), "pageNo": "1",
          "searchText": _q, "_type": "json"}),
        ("https://apis.data.go.kr/1471000/DrbEasyDrugInfoService/getDrbEasyDrugList",
         {"serviceKey": _key, "numOfRows": str(limit), "pageNo": "1",
          "itemName": _q, "type": "json"}),
    ]
    for _base, _params in _api_endpoints:
        try:
            _url  = _base + "?" + _up.urlencode(_params)
            _resp = _req.urlopen(_url, timeout=5)
            _raw  = _json.loads(_resp.read().decode("utf-8"))
            _body = (_raw.get("response", {}).get("body", {})
                     or _raw.get("body", {}))
            _items = _body.get("items", {})
            if isinstance(_items, dict):
                _items = _items.get("item", [])
            if isinstance(_items, dict):
                _items = [_items]
            if _items:
                _out = []
                for _it in _items[:limit]:
                    _nm = (_it.get("DRUG_NM") or _it.get("itemName")
                           or _it.get("drugNm") or "")
                    _ing = (_it.get("INGR_KOR_NM") or _it.get("efcyQesitm")
                            or _it.get("mainIngr") or "")
                    _cat = (_it.get("CLSF_NM") or _it.get("bizrno") or "")
                    _edi = "급여" if "급여" in str(_it) else "확인필요"
                    if _nm:
                        _out.append({
                            "code": _it.get("DRUG_CD", ""),
                            "name": _nm, "brand": "",
                            "ingredient": _ing, "category": _cat,
                            "edi": _edi, "signal": "", "kcd": [],
                            "alert": None, "_source": "hira_api",
                            "keywords": [],
                        })
                if _out:
                    return _out
        except Exception:
            continue

    return _pharma_local_search(_q, limit)


def render_pharma_panel(session_key: str = "pharma") -> None:
    """[엔진 G §2] 약제 정보 + 질병 역추적 UI"""
    import streamlit as _st

    _st.markdown(
        "<div style='border:1px dashed #000;border-radius:12px;"
        "background:#f0fdf4;padding:14px 18px;margin-bottom:10px;'>"
        "<div style='font-size:0.90rem;font-weight:900;color:#065f46;margin-bottom:8px;'>"
        "💊 약제 역진단 엔진 — [엔진 G] 심평원 약가 연동</div>"
        "<div style='font-size:0.74rem;color:#374151;margin-bottom:10px;"
        "word-break:keep-all;'>"
        "약 이름 또는 성분명을 입력하면 KCD 질병코드를 역추적하고, "
        "항암제·희귀난치성 약제 감지 시 관련 보험 특약을 자동으로 안내합니다.</div>",
        unsafe_allow_html=True,
    )

    _col_in, _col_btn = _st.columns([4, 1], gap="small")
    with _col_in:
        _drug_q = _st.text_input(
            "약 이름 / 성분명 / 제품명",
            value=_st.session_state.get(f"{session_key}_q", ""),
            placeholder="예) 메트포르민, 글루코파지, 허셉틴, 아스피린…",
            key=f"{session_key}_input",
        )
    with _col_btn:
        _st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        _do_search = _st.button("🔍 검색", key=f"{session_key}_btn",
                                use_container_width=True)

    if _do_search and _drug_q.strip():
        _st.session_state[f"{session_key}_q"] = _drug_q.strip()
        with _st.spinner("약제 정보 조회 중…"):
            _results = _pharma_search(_drug_q.strip(), 6)
        _st.session_state[f"{session_key}_results"] = _results

    _results = _st.session_state.get(f"{session_key}_results", [])

    if not _results:
        _st.markdown("</div>", unsafe_allow_html=True)
        return

    _src_tag = ("🌐 심평원 API" if any(r.get("_source") == "hira_api" for r in _results)
                else "📋 내장 DB")
    _st.markdown(
        f"<div style='font-size:0.68rem;color:#64748b;margin-bottom:8px;'>"
        f"{_src_tag} — {len(_results)}건 검색됨</div>",
        unsafe_allow_html=True,
    )

    for _d in _results:
        _edi      = _d.get("edi", "")
        _edi_color = "#1d4ed8" if _edi == "급여" else ("#dc2626" if _edi == "비급여" else "#6b7280")
        _edi_bg    = "#dbeafe" if _edi == "급여" else ("#fee2e2" if _edi == "비급여" else "#f1f5f9")
        _edi_label = ("🔵 급여" if _edi == "급여" else ("🔴 비급여" if _edi == "비급여" else f"⚪ {_edi}"))

        _kcd_list  = _d.get("kcd", [])
        _kcd_tags  = "".join(
            f"<span style='background:#f1f5f9;color:#1e293b;border:1px solid #e2e8f0;"
            f"border-radius:5px;padding:1px 7px;font-size:0.70rem;font-weight:700;'>"
            f"{kc}</span> "
            for kc in _kcd_list[:4]
        )
        _alert = _d.get("alert")

        _st.markdown(
            f"<div style='background:#fff;border:1px dashed #000;border-radius:10px;"
            f"padding:12px 16px;margin-bottom:8px;word-break:keep-all;'>"
            # 헤더줄: 알약아이콘 + 약품명 + 급여배지
            f"<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;"
            f"margin-bottom:6px;'>"
            f"<span style='font-size:1.3rem;'>💊</span>"
            f"<span style='font-size:0.90rem;font-weight:900;color:#065f46;'>"
            f"{_d['name']}</span>"
            + (f"<span style='font-size:0.74rem;color:#64748b;'>({_d.get('brand','')})</span>"
               if _d.get('brand') else "")
            + f"<span style='background:{_edi_bg};color:{_edi_color};"
            f"border:1px solid {_edi_color};border-radius:6px;"
            f"padding:1px 8px;font-size:0.72rem;font-weight:900;'>{_edi_label}</span>"
            f"</div>"
            # 성분 / 분류
            f"<div style='display:grid;grid-template-columns:70px 1fr;"
            f"gap:3px 10px;font-size:0.75rem;margin-bottom:6px;'>"
            f"<span style='color:#6b7280;font-weight:700;'>주성분</span>"
            f"<span style='color:#1e293b;'>{_d.get('ingredient','—')}</span>"
            f"<span style='color:#6b7280;font-weight:700;'>효능군</span>"
            f"<span style='color:#1e293b;'>{_d.get('category','—')}</span>"
            + (f"<span style='color:#6b7280;font-weight:700;'>관련질환</span>"
               f"<span style='color:#374151;'>{_d.get('signal','—')}</span>"
               if _d.get('signal') else "")
            + f"</div>"
            # KCD 역추적 태그
            + (f"<div style='margin-bottom:5px;'>"
               f"<span style='font-size:0.70rem;font-weight:700;color:#374151;'>"
               f"🔬 KCD 역추적: </span>{_kcd_tags}</div>"
               if _kcd_tags else "")
            + f"</div>",
            unsafe_allow_html=True,
        )

        # 항암제/희귀난치성 알림 박스
        if _alert and _alert in _PHARMA_ALERT_INFO:
            _ai = _PHARMA_ALERT_INFO[_alert]
            _desc_html = _ai["desc"].replace("\n", "<br>")
            _st.markdown(
                f"<div style='background:{_ai['bg']};border:2px dashed {_ai['color']};"
                f"border-radius:10px;padding:12px 16px;margin-bottom:10px;"
                f"word-break:keep-all;'>"
                f"<div style='font-size:0.84rem;font-weight:900;color:{_ai['color']};"
                f"margin-bottom:6px;'>{_ai['title']}</div>"
                f"<div style='font-size:0.76rem;color:#374151;line-height:1.85;'>"
                f"{_desc_html}</div>"
                f"<div class='risk-law-ref' style='margin-top:8px;'>"
                f"⚖️ <b>{_ai['law']}</b></div>"
                f"<div style='margin-top:8px;background:#fff;border:1px dashed #000;"
                f"border-radius:6px;padding:6px 10px;font-size:0.72rem;font-weight:700;"
                f"color:#1d4ed8;'>"
                f"📄 {_ai['policy_hint']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # KCD 세션 자동 저장 (첫 번째 KCD를 GK-RISK에 연동)
        if _kcd_list and not _st.session_state.get(f"{session_key}_kcd_set"):
            _st.session_state["risk_kcd_code"] = _kcd_list[0]
            _st.session_state[f"{session_key}_kcd_set"] = True
            _st.markdown(
                f"<div style='font-size:0.70rem;color:#16a34a;font-weight:700;"
                f"margin-bottom:4px;'>"
                f"✅ KCD [{_kcd_list[0]}] → 위험 분석 섹터에 자동 연동됨</div>",
                unsafe_allow_html=True,
            )

    _st.markdown("</div>", unsafe_allow_html=True)


'''

src = src.replace(ENGINE_G_ANCHOR, ENGINE_G + ENGINE_G_ANCHOR, 1)
print("✓ [엔진 G] 약제 역진단 엔진 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. GK-RISK 탭 6개 → 7개
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
lines = src.split('\n')
tab_line_idx = next(i for i, l in enumerate(lines)
                    if '_stab1, _stab2, _stab3, _stab4, _stab5, _stab6 = st.tabs([' in l)

# 탭 선언 블록 끝 찾기 ('])')
end_idx = next(i for i in range(tab_line_idx, tab_line_idx + 6)
               if lines[i].strip() == '])')

old_tab_block = '\n'.join(lines[tab_line_idx:end_idx + 1])
print(f"기존 탭 블록: {repr(old_tab_block[:100])}")

new_tab_block = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5, _stab6, _stab7 = st.tabs([\n'
    '        "🏥 실손보험 분석", "💀 생명보험 갭", "🏆 최적 상품 추천",\n'
    '        "⚖️ 법령 검색", "🔬 KCD 상세", "🏢 사업자 조회", "💊 약제 역진단",\n'
    '    ])'
)

src = src.replace(old_tab_block, new_tab_block, 1)
print("✓ 탭 7개로 확장")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. _stab6 뒤에 _stab7 블록 추가
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_STAB6_END = (
    '    with _stab6:\n'
    '        render_biz_status_panel(session_key="risk_biz")\n'
    '\n'
    '\n'
    '\n'
    'def _render_gk_job():'
)
assert src.count(OLD_STAB6_END) == 1, f"stab6 end: {src.count(OLD_STAB6_END)}"

NEW_STAB7 = (
    '    with _stab6:\n'
    '        render_biz_status_panel(session_key="risk_biz")\n'
    '\n'
    '    with _stab7:\n'
    '        render_pharma_panel(session_key="risk_pharma")\n'
    '\n'
    '\n'
    '\n'
    'def _render_gk_job():'
)
src = src.replace(OLD_STAB6_END, NEW_STAB7, 1)
print("✓ _stab7 (약제 역진단) 블록 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
