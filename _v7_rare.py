# -*- coding: utf-8 -*-
"""
[V7-RARE DISEASE DEFENSE] 4단계 패치
1. _PHARMA_ALERT_INFO 'rare' 강화 + 'rare_critical' 신규 등급 추가
2. _PHARMA_LOCAL_DB 희귀약 플래그 'rare_critical' 업그레이드 + 30종 전용 DB 추가
3. render_pharma_panel() — 금색 테두리 엠블럼 + FLASHING RED 배지 + 보장 공백 분석
4. _render_gk_risk CSS — @keyframes flash-red 애니메이션 추가
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
n0  = len(src.split('\n'))
print(f"원본: {n0}줄")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1. _PHARMA_ALERT_INFO 'rare_critical' 신규 등급 추가
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_ALERT_END = '''    "rare": {
        "title": "🔬 희귀난치성 약제 감지 — 특약 긴급 점검",
        "color": "#7c3aed", "bg": "#fdf4ff",
        "law": "보험업법 제102조 / 희귀질환관리법 제12조",
        "desc": (
            "희귀난치성 질환 치료제가 감지되었습니다. 다음을 즉시 확인하세요:\\n"
            "• 희귀질환 입원·수술 특약 보장 여부\\n"
            "• 중증질환(산정특례) 진단비 특약\\n"
            "• 간병인 지원 및 장기간병(LCI) 특약\\n"
            "• 실손보험 급여/비급여 본인부담금 한도"
        ),
        "policy_hint": "PDF 약관 분석기 → '희귀질환' / '산정특례' 키워드 검색 권고",
    },
}'''

assert src.count(OLD_ALERT_END) == 1, f"ALERT_END count={src.count(OLD_ALERT_END)}"

NEW_ALERT_END = '''    "rare": {
        "title": "🔬 희귀난치성 약제 감지 — 특약 긴급 점검",
        "color": "#7c3aed", "bg": "#fdf4ff",
        "law": "보험업법 제102조 / 희귀질환관리법 제12조",
        "desc": (
            "희귀난치성 질환 치료제가 감지되었습니다. 다음을 즉시 확인하세요:\\n"
            "• 희귀질환 입원·수술 특약 보장 여부\\n"
            "• 중증질환(산정특례) 진단비 특약\\n"
            "• 간병인 지원 및 장기간병(LCI) 특약\\n"
            "• 실손보험 급여/비급여 본인부담금 한도"
        ),
        "policy_hint": "PDF 약관 분석기 → '희귀질환' / '산정특례' 키워드 검색 권고",
    },
    "rare_critical": {
        "title": "🚨 국가지정 희귀의약품 감지 — 최고위험 경보 발동",
        "color": "#b91c1c", "bg": "#fff1f2",
        "law": "희귀질환관리법 제17조 / 보험업법 제95조의2 / 상법(보험편) 제638조",
        "desc": (
            "국가 지정 희귀의약품 복용이 확인되었습니다. 즉각 보장 자산 점검을 실시하세요:\\n"
            "• ⛔ 희귀난치성 질환 특약 — 미가입 시 '보장 자산 부족' 상태\\n"
            "• 산정특례 등록 여부 및 실손 비급여 한도 재확인\\n"
            "• 중증 희귀질환 진단비 (치료비 연간 수천만 원 가능)\\n"
            "• 장기 간병인 비용 특약 (입원 180일 초과 시 무보장 위험)\\n"
            "• 생명보험 사망보장 — 희귀질환으로 인한 조기 사망 대비"
        ),
        "policy_hint": "PDF 약관 분석기 → '희귀질환' / '산정특례' / '중증질환' 전체 조항 즉시 검토",
        "gap_warning": "국가 지정 희귀약물 사용 시 보장 자산 부족",
        "badge_override": "FLASH_RED",
    },
}'''

src = src.replace(OLD_ALERT_END, NEW_ALERT_END, 1)
print("✓ STEP1: _PHARMA_ALERT_INFO rare_critical 추가")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2. _PHARMA_LOCAL_DB 희귀약 플래그 'rare' → 'rare_critical' + 30종 전용 DB
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 기존 DB의 alert:"rare" → alert:"rare_critical" 전환
src = src.replace('"alert": "rare"', '"alert": "rare_critical"', )
print(f"✓ STEP2a: alert:rare → rare_critical 전환 ({src.count('rare_critical')}회)")

# 30종 희귀의약품 전용 DB 삽입 — _PHARMA_LOCAL_DB 끝 ']' 바로 앞 앵커 사용
RARE_DB_ANCHOR = '''# ── 약제 → KCD 역추적 매핑 ──────────────────────────────────────────────────
def _pharma_to_kcd(drug: dict) -> list:'''

assert src.count(RARE_DB_ANCHOR) == 1, f"RARE_DB_ANCHOR={src.count(RARE_DB_ANCHOR)}"

RARE_DB_INSERT = '''# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [V7] 국가지정 희귀의약품 전용 DB (30종)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_RARE_DRUG_DB: list = [
    {"code": "A16AB14", "name": "이데루살파제베타", "brand": "헌터라제",
     "ingredient": "Idursulfase beta", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "헌터증후군(MPS II)", "kcd": ["E76.1"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "헌터증후군 (뮤코다당증 II형)",
     "annual_cost_krw": 300000000,
     "keywords": ["이데루살파제", "헌터라제", "헌터증후군", "mps", "희귀"]},
    {"code": "A16AB02", "name": "이미글루세라제", "brand": "세레자임",
     "ingredient": "Imiglucerase", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "고셔병 1·3형", "kcd": ["E75.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "고셔병",
     "annual_cost_krw": 200000000,
     "keywords": ["이미글루세라제", "세레자임", "고셔", "고셔병", "희귀"]},
    {"code": "A16AB07", "name": "알글루코시다제알파", "brand": "마이오자임",
     "ingredient": "Alglucosidase alfa", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "폼페병(당원축적증 II형)", "kcd": ["E74.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "폼페병",
     "annual_cost_krw": 250000000,
     "keywords": ["알글루코시다제", "마이오자임", "폼페병", "희귀"]},
    {"code": "A16AB05", "name": "라로니다제", "brand": "알두라자임",
     "ingredient": "Laronidase", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "뮤코다당증 I형(헐러증후군)", "kcd": ["E76.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "헐러증후군 (MPS I)",
     "annual_cost_krw": 180000000,
     "keywords": ["라로니다제", "알두라자임", "헐러증후군", "mps1", "희귀"]},
    {"code": "N07XX02", "name": "릴루졸", "brand": "릴루텍",
     "ingredient": "Riluzole", "category": "희귀의약품/ALS치료제",
     "edi": "급여", "signal": "근위축성측삭경화증(루게릭병)", "kcd": ["G12.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "근위축성측삭경화증(ALS/루게릭병)",
     "annual_cost_krw": 8000000,
     "keywords": ["릴루졸", "릴루텍", "als", "루게릭", "근위축", "희귀"]},
    {"code": "L04AB04", "name": "아달리무맙", "brand": "휴미라",
     "ingredient": "Adalimumab", "category": "희귀의약품/TNF억제제",
     "edi": "급여", "signal": "크론병·강직성척추염·희귀자가면역", "kcd": ["K50", "M45"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "크론병/강직성척추염",
     "annual_cost_krw": 25000000,
     "keywords": ["아달리무맙", "휴미라", "tnf", "크론병", "희귀"]},
    {"code": "B06AC01", "name": "이카티반트", "brand": "피라자이어",
     "ingredient": "Icatibant", "category": "희귀의약품/브라디키닌길항제",
     "edi": "급여", "signal": "유전성 혈관부종(HAE)", "kcd": ["D84.1"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "유전성 혈관부종 (HAE)",
     "annual_cost_krw": 40000000,
     "keywords": ["이카티반트", "피라자이어", "혈관부종", "hae", "희귀"]},
    {"code": "C05CX01", "name": "보센탄", "brand": "트라클리어",
     "ingredient": "Bosentan", "category": "희귀의약품/폐동맥고혈압",
     "edi": "급여", "signal": "폐동맥고혈압(PAH)", "kcd": ["I27.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "폐동맥 고혈압(PAH)",
     "annual_cost_krw": 50000000,
     "keywords": ["보센탄", "트라클리어", "폐동맥고혈압", "pah", "희귀"]},
    {"code": "C05CX02", "name": "실데나필(폐동맥고혈압)", "brand": "레바티오",
     "ingredient": "Sildenafil (PAH)", "category": "희귀의약품/폐동맥고혈압",
     "edi": "급여", "signal": "폐동맥고혈압(PAH)", "kcd": ["I27.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "폐동맥 고혈압(PAH)",
     "annual_cost_krw": 30000000,
     "keywords": ["실데나필", "레바티오", "폐동맥고혈압", "pah", "희귀"]},
    {"code": "L04AC07", "name": "토실리주맙", "brand": "악템라",
     "ingredient": "Tocilizumab", "category": "희귀의약품/IL-6억제제",
     "edi": "급여", "signal": "전신형소아특발성관절염/성인형스틸병", "kcd": ["M08.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "전신형 소아특발성관절염",
     "annual_cost_krw": 35000000,
     "keywords": ["토실리주맙", "악템라", "소아관절염", "희귀"]},
    {"code": "L01XC31", "name": "아테졸리주맙", "brand": "티쎈트릭",
     "ingredient": "Atezolizumab", "category": "항암제/면역관문억제제",
     "edi": "급여", "signal": "방광암·폐암(PD-L1양성)", "kcd": ["C67", "C34"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "방광암/비소세포폐암",
     "annual_cost_krw": 80000000,
     "keywords": ["아테졸리주맙", "티쎈트릭", "면역항암", "방광암", "희귀"]},
    {"code": "L01XC32", "name": "니볼루맙", "brand": "옵디보",
     "ingredient": "Nivolumab", "category": "항암제/면역관문억제제",
     "edi": "급여", "signal": "흑색종·폐암·신세포암(희귀적응증)", "kcd": ["C43", "C34"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "흑색종/비소세포폐암",
     "annual_cost_krw": 90000000,
     "keywords": ["니볼루맙", "옵디보", "면역항암", "흑색종", "희귀"]},
    {"code": "L01XC17", "name": "페르투주맙", "brand": "퍼제타",
     "ingredient": "Pertuzumab", "category": "항암제/HER2표적",
     "edi": "급여", "signal": "HER2양성 전이성유방암", "kcd": ["C50"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "HER2양성 전이성 유방암",
     "annual_cost_krw": 70000000,
     "keywords": ["페르투주맙", "퍼제타", "her2", "유방암", "희귀"]},
    {"code": "L01XC24", "name": "라무시루맙", "brand": "사이람자",
     "ingredient": "Ramucirumab", "category": "항암제/VEGFR2표적",
     "edi": "급여", "signal": "위암·간세포암·폐암 희귀적응증", "kcd": ["C16", "C22"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "전이성 위암/간세포암",
     "annual_cost_krw": 60000000,
     "keywords": ["라무시루맙", "사이람자", "위암", "희귀항암"]},
    {"code": "A16AX04", "name": "니티시논", "brand": "오르파딘",
     "ingredient": "Nitisinone", "category": "희귀의약품/선천대사이상",
     "edi": "급여", "signal": "유전성 티로신혈증 I형", "kcd": ["E70.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "유전성 티로신혈증 I형",
     "annual_cost_krw": 120000000,
     "keywords": ["니티시논", "오르파딘", "티로신혈증", "희귀"]},
    {"code": "A16AX06", "name": "사프로프테린", "brand": "쿠반",
     "ingredient": "Sapropterin", "category": "희귀의약품/페닐케톤뇨증",
     "edi": "급여", "signal": "페닐케톤뇨증(PKU)", "kcd": ["E70.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "페닐케톤뇨증(PKU)",
     "annual_cost_krw": 15000000,
     "keywords": ["사프로프테린", "쿠반", "페닐케톤뇨증", "pku", "희귀"]},
    {"code": "L04AA27", "name": "핀골리모드", "brand": "질레니아",
     "ingredient": "Fingolimod", "category": "희귀의약품/다발성경화증",
     "edi": "급여", "signal": "재발완화형 다발성경화증(MS)", "kcd": ["G35"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "다발성 경화증(MS)",
     "annual_cost_krw": 28000000,
     "keywords": ["핀골리모드", "질레니아", "다발성경화증", "ms", "희귀"]},
    {"code": "L04AA36", "name": "나탈리주맙", "brand": "타이사브리",
     "ingredient": "Natalizumab", "category": "희귀의약품/다발성경화증",
     "edi": "급여", "signal": "재발완화형 다발성경화증(MS)", "kcd": ["G35"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "다발성 경화증(MS)",
     "annual_cost_krw": 32000000,
     "keywords": ["나탈리주맙", "타이사브리", "다발성경화증", "ms", "희귀"]},
    {"code": "N07AA01", "name": "네오스티그민 (근무력증)", "brand": "프로스티그민",
     "ingredient": "Neostigmine (MG)", "category": "희귀의약품/중증근무력증",
     "edi": "급여", "signal": "중증근무력증(MG)", "kcd": ["G70.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "중증근무력증(MG)",
     "annual_cost_krw": 5000000,
     "keywords": ["네오스티그민", "프로스티그민", "중증근무력증", "mg", "희귀"]},
    {"code": "L04AC11", "name": "에쿨리주맙", "brand": "솔리리스",
     "ingredient": "Eculizumab", "category": "희귀의약품/보체억제제",
     "edi": "급여", "signal": "발작야간혈색소뇨증/비정형HUS", "kcd": ["D59.5"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "발작성 야간 혈색소뇨증(PNH)",
     "annual_cost_krw": 700000000,
     "keywords": ["에쿨리주맙", "솔리리스", "pnh", "혈색소뇨증", "희귀"]},
    {"code": "A16AB13", "name": "벨라글루세라제알파", "brand": "비프리브",
     "ingredient": "Velaglucerase alfa", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "고셔병 1형", "kcd": ["E75.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "고셔병 1형",
     "annual_cost_krw": 180000000,
     "keywords": ["벨라글루세라제", "비프리브", "고셔", "희귀"]},
    {"code": "B02BD02", "name": "옥토코그알파", "brand": "애드베이트",
     "ingredient": "Octocog alfa (Factor VIII)", "category": "희귀의약품/혈우병A",
     "edi": "급여", "signal": "혈우병 A형", "kcd": ["D66"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "혈우병 A형",
     "annual_cost_krw": 100000000,
     "keywords": ["옥토코그", "애드베이트", "혈우병", "희귀"]},
    {"code": "B02BD04", "name": "모로토코그알파", "brand": "리팍토 어드밴스",
     "ingredient": "Moroctocog alfa", "category": "희귀의약품/혈우병A",
     "edi": "급여", "signal": "혈우병 A형", "kcd": ["D66"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "혈우병 A형",
     "annual_cost_krw": 120000000,
     "keywords": ["모로토코그", "리팍토", "혈우병", "희귀"]},
    {"code": "L01XC07", "name": "베바시주맙", "brand": "아바스틴",
     "ingredient": "Bevacizumab", "category": "항암제/VEGF표적",
     "edi": "급여", "signal": "전이성대장암·난소암·자궁경부암 희귀적응증", "kcd": ["C18", "C56"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "전이성 대장암/난소암",
     "annual_cost_krw": 45000000,
     "keywords": ["베바시주맙", "아바스틴", "대장암", "난소암", "희귀항암"]},
    {"code": "J06BA02", "name": "인간면역글로불린(정맥)", "brand": "아이비글로불린",
     "ingredient": "Human immunoglobulin IV", "category": "희귀의약품/면역결핍증",
     "edi": "급여", "signal": "원발성면역결핍증(PID)", "kcd": ["D83"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "원발성 면역결핍증(PID)",
     "annual_cost_krw": 20000000,
     "keywords": ["면역글로불린", "아이비글로불린", "pid", "면역결핍", "희귀"]},
    {"code": "L04AX04", "name": "타리도마이드", "brand": "탈리도마이드",
     "ingredient": "Thalidomide", "category": "희귀의약품/다발성골수종",
     "edi": "급여", "signal": "다발성골수종·나병성결절홍반", "kcd": ["C90.0"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "다발성 골수종",
     "annual_cost_krw": 10000000,
     "keywords": ["타리도마이드", "탈리도마이드", "골수종", "희귀"]},
    {"code": "L01XE15", "name": "에베로리무스(희귀종양)", "brand": "아피니토",
     "ingredient": "Everolimus (rare tumor)", "category": "희귀의약품/mTOR억제제",
     "edi": "급여", "signal": "결절성경화증복합체·신경내분비종양", "kcd": ["Q85.1"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "결절성 경화증 복합체(TSC)",
     "annual_cost_krw": 55000000,
     "keywords": ["에베로리무스", "아피니토", "결절성경화증", "tsc", "희귀"]},
    {"code": "A16AX10", "name": "세벨리파제알파", "brand": "카눠마",
     "ingredient": "Sebelipase alfa", "category": "희귀의약품/LAL결핍증",
     "edi": "급여", "signal": "리소좀산성지방분해효소결핍증(LAL-D)", "kcd": ["E75.5"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "리소좀산성지방분해효소결핍증",
     "annual_cost_krw": 400000000,
     "keywords": ["세벨리파제", "카눠마", "lal", "희귀"]},
    {"code": "A16AB18", "name": "아가보시다제베타", "brand": "파브라자임",
     "ingredient": "Agalsidase beta", "category": "희귀의약품/파브리병",
     "edi": "급여", "signal": "파브리병(Fabry disease)", "kcd": ["E75.2"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "파브리병 (Fabry disease)",
     "annual_cost_krw": 220000000,
     "keywords": ["아가보시다제", "파브라자임", "파브리", "fabry", "희귀"]},
    {"code": "A16AB12", "name": "이두르술파제", "brand": "엘라프라제",
     "ingredient": "Idursulfase", "category": "희귀의약품/효소대체요법",
     "edi": "급여", "signal": "헌터증후군(MPS II)", "kcd": ["E76.1"],
     "alert": "rare_critical", "rare_official": True,
     "rare_disease": "헌터증후군 (MPS II)",
     "annual_cost_krw": 320000000,
     "keywords": ["이두르술파제", "엘라프라제", "헌터증후군", "mps2", "희귀"]},
]

def _is_rare_critical(drug: dict) -> bool:
    """희귀의약품 최고위험 여부 판별"""
    return drug.get("alert") == "rare_critical" or drug.get("rare_official") is True

def _rare_gap_analysis(drug: dict) -> dict:
    """희귀약 보장 공백 분석"""
    _annual = drug.get("annual_cost_krw", 0)
    _disease = drug.get("rare_disease", drug.get("signal", ""))
    _gaps = []
    if drug.get("rare_official"):
        _gaps.append("희귀난치성 질환 특약 — 미가입 시 연간 치료비 전액 자부담")
        if _annual >= 100000000:
            _gaps.append(f"연간 예상 치료비 약 {_annual//100000000}억원 이상 — 중증질환 진단비 특약 긴급 필요")
        elif _annual >= 10000000:
            _gaps.append(f"연간 예상 치료비 약 {_annual//10000000}천만원 이상 — 산정특례 적용 후 본인부담 확인")
        _gaps.append("장기 간병인 비용 특약 (입원 장기화 대비)")
        _gaps.append("실손 비급여 한도 초과 분 대비 특약 확인")
    return {
        "disease": _disease,
        "annual_cost": _annual,
        "gaps": _gaps,
        "warning": drug.get("alert") == "rare_critical",
    }

# ── 약제 → KCD 역추적 매핑 ──────────────────────────────────────────────────
def _pharma_to_kcd(drug: dict) -> list:'''

src = src.replace(RARE_DB_ANCHOR, RARE_DB_INSERT, 1)
print("✓ STEP2b: _RARE_DRUG_DB 30종 + _is_rare_critical + _rare_gap_analysis 삽입")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3. _pharma_local_search — _RARE_DRUG_DB 도 검색 통합
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OLD_LOCAL_SEARCH = '''def _pharma_local_search(query: str, limit: int = 8) -> list:
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
    return _results'''

assert src.count(OLD_LOCAL_SEARCH) == 1, f"local search count={src.count(OLD_LOCAL_SEARCH)}"

NEW_LOCAL_SEARCH = '''def _pharma_local_search(query: str, limit: int = 8) -> list:
    """로컬 약제 DB 검색 — 일반 + 희귀의약품 통합"""
    _ql = query.strip().lower()
    if not _ql:
        return []
    _results = []
    # 희귀의약품 DB 우선 검색 (상위 노출)
    for _d in _RARE_DRUG_DB:
        if (
            _ql in _d["name"].lower()
            or _ql in _d.get("brand", "").lower()
            or _ql in _d.get("ingredient", "").lower()
            or any(_ql in kw.lower() for kw in _d.get("keywords", []))
        ):
            _results.append({**_d, "_source": "local_rare"})
        if len(_results) >= limit:
            break
    # 일반 약제 DB 보충
    for _d in _PHARMA_LOCAL_DB:
        if len(_results) >= limit:
            break
        if (
            _ql in _d["name"].lower()
            or _ql in _d.get("brand", "").lower()
            or _ql in _d.get("ingredient", "").lower()
            or any(_ql in kw.lower() for kw in _d.get("keywords", []))
        ):
            _results.append({**_d, "_source": "local"})
    return _results[:limit]'''

src = src.replace(OLD_LOCAL_SEARCH, NEW_LOCAL_SEARCH, 1)
print("✓ STEP3: _pharma_local_search 희귀약 DB 통합")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4. render_pharma_panel() — 금색 테두리 + FLASHING RED + 보장 공백 분석
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4a: 카드 렌더링 부분 교체 — 일반 vs 희귀 분기
OLD_CARD = '''        _st.markdown(
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
        )'''

assert src.count(OLD_CARD) == 1, f"card count={src.count(OLD_CARD)}"

NEW_CARD = '''        _is_rare = _is_rare_critical(_d)
        _rare_border = (
            "border:2px solid #d97706;background:linear-gradient(135deg,#fffbeb,#fff7ed);"
            if _is_rare else "border:1px dashed #000;background:#fff;"
        )
        _rare_emblem = (
            "<span style='background:linear-gradient(135deg,#f59e0b,#d97706);"
            "color:#fff;border-radius:6px;padding:2px 8px;font-size:0.70rem;"
            "font-weight:900;margin-left:4px;letter-spacing:0.04em;'>"
            "⚜️ 국가지정 희귀의약품</span>"
            if _is_rare else ""
        )
        _annual = _d.get("annual_cost_krw", 0)
        _annual_tag = (
            f"<span style='background:#fef2f2;color:#b91c1c;border:1px solid #fca5a5;"
            f"border-radius:5px;padding:1px 7px;font-size:0.68rem;font-weight:900;'>"
            f"연간 치료비 약 {_annual//10000:,}만원</span>"
            if _annual else ""
        )
        _st.markdown(
            f"<div style='{_rare_border}border-radius:10px;"
            f"padding:12px 16px;margin-bottom:8px;word-break:keep-all;'>"
            # 희귀약 경고 배너
            + (f"<div style='background:#d97706;color:#fff;border-radius:6px 6px 0 0;"
               f"padding:5px 12px;font-size:0.74rem;font-weight:900;"
               f"margin:-12px -16px 10px -16px;letter-spacing:0.04em;'>"
               f"🚨 국가 지정 희귀의약품 — 최고위험 경보 발동</div>"
               if _is_rare else "")
            # 헤더줄
            + f"<div style='display:flex;align-items:center;gap:8px;flex-wrap:wrap;"
            f"margin-bottom:6px;'>"
            f"<span style='font-size:1.3rem;'>💊</span>"
            f"<span style='font-size:0.90rem;font-weight:900;"
            f"color:{'#92400e' if _is_rare else '#065f46'};'>"
            f"{_d['name']}</span>"
            + (f"<span style='font-size:0.74rem;color:#64748b;'>({_d.get('brand','')})</span>"
               if _d.get('brand') else "")
            + f"<span style='background:{_edi_bg};color:{_edi_color};"
            f"border:1px solid {_edi_color};border-radius:6px;"
            f"padding:1px 8px;font-size:0.72rem;font-weight:900;'>{_edi_label}</span>"
            + _rare_emblem
            + f"</div>"
            # 성분 / 분류 (성분명은 break-all)
            f"<div style='display:grid;grid-template-columns:70px 1fr;"
            f"gap:3px 10px;font-size:0.75rem;margin-bottom:6px;'>"
            f"<span style='color:#6b7280;font-weight:700;'>주성분</span>"
            f"<span style='color:#1e293b;word-break:break-all;'>{_d.get('ingredient','—')}</span>"
            f"<span style='color:#6b7280;font-weight:700;'>효능군</span>"
            f"<span style='color:#1e293b;'>{_d.get('category','—')}</span>"
            + (f"<span style='color:#6b7280;font-weight:700;'>적응질환</span>"
               f"<span style='color:#374151;word-break:keep-all;'>"
               f"{_d.get('rare_disease') or _d.get('signal','—')}</span>"
               if _d.get('rare_disease') or _d.get('signal') else "")
            + f"</div>"
            # 연간 치료비 태그
            + (f"<div style='margin-bottom:6px;'>{_annual_tag}</div>" if _annual_tag else "")
            # KCD 역추적 태그
            + (f"<div style='margin-bottom:5px;'>"
               f"<span style='font-size:0.70rem;font-weight:700;color:#374151;'>"
               f"🔬 KCD 역추적: </span>{_kcd_tags}</div>"
               if _kcd_tags else "")
            + f"</div>",
            unsafe_allow_html=True,
        )

        # 희귀약 보장 공백 분석
        if _is_rare:
            _gap_info = _rare_gap_analysis(_d)
            if _gap_info["gaps"]:
                _gap_html = "".join(
                    f"<div style='display:flex;align-items:flex-start;gap:6px;"
                    f"margin-bottom:4px;font-size:0.74rem;'>"
                    f"<span style='color:#b91c1c;font-weight:900;flex-shrink:0;'>⛔</span>"
                    f"<span style='color:#1e293b;word-break:keep-all;'>{g}</span></div>"
                    for g in _gap_info["gaps"]
                )
                _warning_msg = _PHARMA_ALERT_INFO.get("rare_critical", {}).get(
                    "gap_warning", "국가 지정 희귀약물 사용 시 보장 자산 부족")
                _st.markdown(
                    f"<div style='background:#fff1f2;border:2px dashed #b91c1c;"
                    f"border-radius:10px;padding:12px 16px;margin-bottom:10px;"
                    f"word-break:keep-all;'>"
                    f"<div style='font-size:0.84rem;font-weight:900;color:#b91c1c;"
                    f"margin-bottom:8px;letter-spacing:0.03em;'>"
                    f"🚨 보장 자산 긴급 점검 — {_warning_msg}</div>"
                    f"{_gap_html}"
                    f"<div class='risk-law-ref' style='margin-top:8px;'>"
                    f"⚖️ <b>희귀질환관리법 제17조</b> — 국가 희귀의약품 지원 범위 확인<br>"
                    f"⚖️ <b>보험업법 제95조의2</b> — 특약 미가입 공백은 설명의무 대상</div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            # FLASHING RED 배지 — session_state에 badge_override 설정
            _st.session_state["risk_badge_override"] = "FLASH_RED"
            _st.session_state["risk_badge_reason"]   = _d.get("rare_disease", _d["name"])'''

src = src.replace(OLD_CARD, NEW_CARD, 1)
print("✓ STEP4a: 카드 렌더링 희귀약 금색 테두리 + 보장 공백 분석")

# STEP 5 는 _v7_rare2.py 에서 처리
print("STEP5: CSS+badge_override 는 _v7_rare2.py 에서 처리")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 저장
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
n1 = len(src.split('\n'))
print(f"OK total lines: {n1} (+{n1-n0})")
