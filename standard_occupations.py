"""
standard_occupations.py — 손해보험사 표준 직업분류 DB
KB손해보험·메리츠 등 국내 손보사 상해급수 기준 (1급/2급/3급)

직업코드 체계:
  GK-J-1xxx : 상해 1급 (저위험 — 사무/가정)
  GK-J-2xxx : 상해 2급 (중위험 — 영업/현장 일반)
  GK-J-3xxx : 상해 3급 (고위험 — 이륜차/건설/운송)

상해급수 인수 기준 요약:
  1급: 일반 조건, 최대 한도 가입 가능
  2급: 상해담보 할증 가능, 일부 특약 제한
  3급: 상해담보 고위험 할증, 입원일당 한도 축소, 일부 거절 가능
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# 표준 직업분류 DB — 75개 대표 직종
# ──────────────────────────────────────────────────────────────────────────────
STANDARD_OCCUPATIONS: list[dict] = [
    # ── 1급: 저위험 ──────────────────────────────────────────────────────────
    {"job_code": "GK-J-1001", "job_name": "사무직 (일반 사무원)",          "injury_level": 1, "category": "사무·관리"},
    {"job_code": "GK-J-1002", "job_name": "공무원 (일반직)",               "injury_level": 1, "category": "공공·행정"},
    {"job_code": "GK-J-1003", "job_name": "교원 (초·중·고 교사)",          "injury_level": 1, "category": "교육"},
    {"job_code": "GK-J-1004", "job_name": "교수 (대학교)",                 "injury_level": 1, "category": "교육"},
    {"job_code": "GK-J-1005", "job_name": "가정주부",                       "injury_level": 1, "category": "가정"},
    {"job_code": "GK-J-1006", "job_name": "대학생·학생",                   "injury_level": 1, "category": "학생"},
    {"job_code": "GK-J-1007", "job_name": "의사 (내과·소아과 등 내근)",    "injury_level": 1, "category": "의료"},
    {"job_code": "GK-J-1008", "job_name": "한의사",                         "injury_level": 1, "category": "의료"},
    {"job_code": "GK-J-1009", "job_name": "약사",                           "injury_level": 1, "category": "의료"},
    {"job_code": "GK-J-1010", "job_name": "간호사 (병원 내근)",             "injury_level": 1, "category": "의료"},
    {"job_code": "GK-J-1011", "job_name": "변호사",                         "injury_level": 1, "category": "법률·회계"},
    {"job_code": "GK-J-1012", "job_name": "공인회계사 (CPA)",              "injury_level": 1, "category": "법률·회계"},
    {"job_code": "GK-J-1013", "job_name": "세무사",                         "injury_level": 1, "category": "법률·회계"},
    {"job_code": "GK-J-1014", "job_name": "법무사",                         "injury_level": 1, "category": "법률·회계"},
    {"job_code": "GK-J-1015", "job_name": "IT 개발자·프로그래머",          "injury_level": 1, "category": "IT·기술"},
    {"job_code": "GK-J-1016", "job_name": "디자이너 (실내 근무)",           "injury_level": 1, "category": "IT·기술"},
    {"job_code": "GK-J-1017", "job_name": "금융업 종사자 (은행원·증권사)", "injury_level": 1, "category": "금융"},
    {"job_code": "GK-J-1018", "job_name": "보험설계사",                     "injury_level": 1, "category": "금융"},
    {"job_code": "GK-J-1019", "job_name": "언론인·기자 (사무)",            "injury_level": 1, "category": "미디어"},
    {"job_code": "GK-J-1020", "job_name": "PD·방송작가 (실내)",            "injury_level": 1, "category": "미디어"},
    {"job_code": "GK-J-1021", "job_name": "연구원 (연구소 내근)",           "injury_level": 1, "category": "연구"},
    {"job_code": "GK-J-1022", "job_name": "군인 (장교·사무)",              "injury_level": 1, "category": "국방·경찰"},
    {"job_code": "GK-J-1023", "job_name": "경찰관 (일반 행정·내근)",       "injury_level": 1, "category": "국방·경찰"},
    {"job_code": "GK-J-1024", "job_name": "성직자 (목사·승려·신부)",       "injury_level": 1, "category": "종교"},
    {"job_code": "GK-J-1025", "job_name": "은퇴자·무직",                   "injury_level": 1, "category": "기타"},

    # ── 2급: 중위험 ──────────────────────────────────────────────────────────
    {"job_code": "GK-J-2001", "job_name": "영업직 (일반 외근 영업)",       "injury_level": 2, "category": "영업·판매"},
    {"job_code": "GK-J-2002", "job_name": "영업관리자",                     "injury_level": 2, "category": "영업·판매"},
    {"job_code": "GK-J-2003", "job_name": "부동산 중개인",                  "injury_level": 2, "category": "영업·판매"},
    {"job_code": "GK-J-2004", "job_name": "자동차 딜러",                    "injury_level": 2, "category": "영업·판매"},
    {"job_code": "GK-J-2005", "job_name": "미용사·헤어디자이너",            "injury_level": 2, "category": "서비스"},
    {"job_code": "GK-J-2006", "job_name": "요리사·조리사 (주방)",          "injury_level": 2, "category": "서비스"},
    {"job_code": "GK-J-2007", "job_name": "제과·제빵사",                    "injury_level": 2, "category": "서비스"},
    {"job_code": "GK-J-2008", "job_name": "호텔·숙박업 종사자",             "injury_level": 2, "category": "서비스"},
    {"job_code": "GK-J-2009", "job_name": "항공 승무원",                    "injury_level": 2, "category": "운송"},
    {"job_code": "GK-J-2010", "job_name": "운전기사 (버스·택시, 비유상)",  "injury_level": 2, "category": "운송"},
    {"job_code": "GK-J-2011", "job_name": "자동차 정비사",                  "injury_level": 2, "category": "기계·정비"},
    {"job_code": "GK-J-2012", "job_name": "전기기사 (일반 실내)",           "injury_level": 2, "category": "기계·정비"},
    {"job_code": "GK-J-2013", "job_name": "배관공 (일반 주거용)",           "injury_level": 2, "category": "기계·정비"},
    {"job_code": "GK-J-2014", "job_name": "농업인 (농경지 재배)",           "injury_level": 2, "category": "농·수산"},
    {"job_code": "GK-J-2015", "job_name": "어업인 (연안 어업)",             "injury_level": 2, "category": "농·수산"},
    {"job_code": "GK-J-2016", "job_name": "건설업 현장 관리자",             "injury_level": 2, "category": "건설"},
    {"job_code": "GK-J-2017", "job_name": "인테리어 디자이너 (현장 감리)", "injury_level": 2, "category": "건설"},
    {"job_code": "GK-J-2018", "job_name": "체육 교사·스포츠 강사 (실내)", "injury_level": 2, "category": "스포츠"},
    {"job_code": "GK-J-2019", "job_name": "물류센터 관리자",                "injury_level": 2, "category": "유통·물류"},
    {"job_code": "GK-J-2020", "job_name": "생산직 (경공업·조립)",          "injury_level": 2, "category": "제조·생산"},
    {"job_code": "GK-J-2021", "job_name": "의료기기 영업",                  "injury_level": 2, "category": "의료"},
    {"job_code": "GK-J-2022", "job_name": "사회복지사",                     "injury_level": 2, "category": "복지"},
    {"job_code": "GK-J-2023", "job_name": "경비원 (일반 건물)",             "injury_level": 2, "category": "보안"},
    {"job_code": "GK-J-2024", "job_name": "택배 배송기사 (승용차·화물차)", "injury_level": 2, "category": "운송"},
    {"job_code": "GK-J-2025", "job_name": "판매직 (일반 매장)",             "injury_level": 2, "category": "영업·판매"},

    # ── 3급: 고위험 ──────────────────────────────────────────────────────────
    {"job_code": "GK-J-3001", "job_name": "건설 현장 근로자 (철골·비계)", "injury_level": 3, "category": "건설"},
    {"job_code": "GK-J-3002", "job_name": "건설 현장 크레인 기사",          "injury_level": 3, "category": "건설"},
    {"job_code": "GK-J-3003", "job_name": "용접사 (현장)",                  "injury_level": 3, "category": "건설"},
    {"job_code": "GK-J-3004", "job_name": "이륜차 배달기사 (유상)",         "injury_level": 3, "category": "운송·이륜차"},
    {"job_code": "GK-J-3005", "job_name": "오토바이 퀵서비스",              "injury_level": 3, "category": "운송·이륜차"},
    {"job_code": "GK-J-3006", "job_name": "택시기사 (유상운송)",            "injury_level": 3, "category": "운송"},
    {"job_code": "GK-J-3007", "job_name": "화물트럭 기사 (대형)",           "injury_level": 3, "category": "운송"},
    {"job_code": "GK-J-3008", "job_name": "버스기사 (대중교통 유상)",       "injury_level": 3, "category": "운송"},
    {"job_code": "GK-J-3009", "job_name": "소방관 (현장 진압)",             "injury_level": 3, "category": "국방·경찰"},
    {"job_code": "GK-J-3010", "job_name": "경찰관 (형사·순찰·기동대)",     "injury_level": 3, "category": "국방·경찰"},
    {"job_code": "GK-J-3011", "job_name": "군인 (특수부대·전투병)",         "injury_level": 3, "category": "국방·경찰"},
    {"job_code": "GK-J-3012", "job_name": "광부·광산 근로자",               "injury_level": 3, "category": "광업"},
    {"job_code": "GK-J-3013", "job_name": "선박·해상 근무자",               "injury_level": 3, "category": "해상"},
    {"job_code": "GK-J-3014", "job_name": "잠수사",                          "injury_level": 3, "category": "해상"},
    {"job_code": "GK-J-3015", "job_name": "항공기 조종사",                   "injury_level": 3, "category": "항공"},
    {"job_code": "GK-J-3016", "job_name": "전기공 (고압·송전선)",           "injury_level": 3, "category": "기계·정비"},
    {"job_code": "GK-J-3017", "job_name": "가스·화학 플랜트 근로자",        "injury_level": 3, "category": "화학·에너지"},
    {"job_code": "GK-J-3018", "job_name": "위험물 취급자 (폭발물·유류)",   "injury_level": 3, "category": "화학·에너지"},
    {"job_code": "GK-J-3019", "job_name": "프로 스포츠 선수",               "injury_level": 3, "category": "스포츠"},
    {"job_code": "GK-J-3020", "job_name": "격투기·무도 선수",               "injury_level": 3, "category": "스포츠"},
    {"job_code": "GK-J-3021", "job_name": "모터스포츠 선수",                 "injury_level": 3, "category": "스포츠"},
    {"job_code": "GK-J-3022", "job_name": "등산 가이드·암벽등반 강사",     "injury_level": 3, "category": "스포츠"},
    {"job_code": "GK-J-3023", "job_name": "철거 해체 근로자",               "injury_level": 3, "category": "건설"},
    {"job_code": "GK-J-3024", "job_name": "임업 종사자 (벌목)",             "injury_level": 3, "category": "농·수산"},
    {"job_code": "GK-J-3025", "job_name": "스턴트 배우·특수 연기자",        "injury_level": 3, "category": "기타"},
]


# ──────────────────────────────────────────────────────────────────────────────
# 검색 & 조회 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def search_occupations(keyword: str, max_results: int = 10) -> list[dict]:
    """키워드 포함 직업 검색 (job_name + category 동시 탐색)."""
    if not keyword or not keyword.strip():
        return []
    kw = keyword.strip().lower()
    results = [
        j for j in STANDARD_OCCUPATIONS
        if kw in j["job_name"].lower() or kw in j["category"].lower()
    ]
    return results[:max_results]


def get_occupation_by_name(job_name: str) -> dict | None:
    """직업명 정확 일치 조회."""
    for j in STANDARD_OCCUPATIONS:
        if j["job_name"] == job_name:
            return j
    return None


def get_injury_level(job_name: str) -> int:
    """직업명 → 상해급수 반환 (미발견 시 1 기본값)."""
    occ = get_occupation_by_name(job_name)
    return occ["injury_level"] if occ else 1


# ──────────────────────────────────────────────────────────────────────────────
# 상해급수 인수심사 가이드라인
# ──────────────────────────────────────────────────────────────────────────────
INJURY_LEVEL_GUIDE: dict[int, dict] = {
    1: {
        "label":   "1급 (저위험)",
        "color":   "#1d4ed8",
        "bg":      "#dbeafe",
        "border":  "#3b82f6",
        "badge_emoji": "🔵",
        "underwriting": (
            "일반 조건 인수 가능. 상해·입원일당 최대 한도까지 가입 가능. "
            "모든 특약 거절 사유 없음."
        ),
    },
    2: {
        "label":   "2급 (중위험)",
        "color":   "#92400e",
        "bg":      "#fef3c7",
        "border":  "#f59e0b",
        "badge_emoji": "🟡",
        "underwriting": (
            "상해담보 10~20% 할증 가능. 이륜차 특약 불가. "
            "입원일당 한도 통상 조건 내 가입. 고위험 특약 심사 필요."
        ),
    },
    3: {
        "label":   "3급 (고위험)",
        "color":   "#991b1b",
        "bg":      "#fee2e2",
        "border":  "#ef4444",
        "badge_emoji": "🔴",
        "underwriting": (
            "상해담보 20~50% 할증 또는 거절 가능. 입원일당 한도 절반 축소 심사. "
            "생명보험 사망담보 가입 한도 제한. 이륜차·레저 특약 전면 거절. "
            "언더라이터 특별심사 필요."
        ),
    },
}
