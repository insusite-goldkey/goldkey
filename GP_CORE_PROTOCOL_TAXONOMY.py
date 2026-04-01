# ══════════════════════════════════════════════════════════════════════════════
# [GP-CORE-PROTOCOL] 25개 핵심 분류 체계 (Taxonomy)
# 4대 상위 프로토콜 기반 전문 상담 섹터 정의
# ══════════════════════════════════════════════════════════════════════════════
# 작성일: 2026-04-01
# 목적: 전문 상담 분야를 4대 프로토콜로 그룹화하여 관리 효율성과 상담 전문성 극대화
# ══════════════════════════════════════════════════════════════════════════════

from typing import TypedDict, Literal


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 1] 4대 상위 프로토콜 정의
# ──────────────────────────────────────────────────────────────────────────────

class ProtocolDefinition(TypedDict):
    """프로토콜 정의 타입"""
    protocol_id: str
    protocol_name: str
    protocol_name_en: str
    description: str
    icon: str
    color: str
    bg_color: str


CORE_PROTOCOLS: list[ProtocolDefinition] = [
    {
        "protocol_id": "PSP",
        "protocol_name": "인적 보안 프로토콜",
        "protocol_name_en": "Personal Security Protocol",
        "description": "개인의 생애 주기 리스크를 방어하는 가장 기초적이고 필수적인 규약",
        "icon": "🛡️",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
    },
    {
        "protocol_id": "APP",
        "protocol_name": "자산 보호 프로토콜",
        "protocol_name_en": "Asset Protection Protocol",
        "description": "물리적 자산의 손실을 방지하고 원상복구(Indemnity)를 보장하는 정밀 기술 프로토콜",
        "icon": "🏛️",
        "color": "#0369a1",
        "bg_color": "#f0f9ff",
    },
    {
        "protocol_id": "BRP",
        "protocol_name": "비즈니스 리스크 프로토콜",
        "protocol_name_en": "Business Risk Protocol",
        "description": "기업 경영 및 전문 활동 중 발생하는 법적/경제적 책임을 통제하는 고도의 법률적 규약",
        "icon": "⚖️",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
    },
    {
        "protocol_id": "WOP",
        "protocol_name": "부(富)의 이전 및 최적화 프로토콜",
        "protocol_name_en": "Wealth Optimization Protocol",
        "description": "자산의 효율적 운용과 세대 간 이전을 위한 세무/법률 융합 프로토콜",
        "icon": "💎",
        "color": "#d97706",
        "bg_color": "#fffbeb",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 2] 25개 전문 상담 섹터 정의
# ──────────────────────────────────────────────────────────────────────────────

class SectorDefinition(TypedDict):
    """섹터 정의 타입"""
    sector_id: str
    sector_name: str
    sector_name_en: str
    protocol_id: Literal["PSP", "APP", "BRP", "WOP"]
    icon: str
    color: str
    bg_color: str
    keywords: list[str]
    war_room_key: str  # 기존 _WAR_ROOM_CATEGORIES와의 매핑


CORE_SECTORS: list[SectorDefinition] = [
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [PSP] 인적 보안 프로토콜 (Personal Security Protocol) — 10개 섹터
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "sector_id": "PSP-01",
        "sector_name": "암",
        "sector_name_en": "Cancer",
        "protocol_id": "PSP",
        "icon": "🎗️",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["암", "암보험", "암진단", "항암", "표적항암", "면역항암", "NGS", "CAR-T"],
        "war_room_key": "cancer",
    },
    {
        "sector_id": "PSP-02",
        "sector_name": "뇌혈관",
        "sector_name_en": "Cerebrovascular",
        "protocol_id": "PSP",
        "icon": "🧠",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["뇌", "뇌졸중", "뇌경색", "뇌출혈", "중풍", "뇌혈관", "뇌질환"],
        "war_room_key": "brain",
    },
    {
        "sector_id": "PSP-03",
        "sector_name": "심장질환",
        "sector_name_en": "Cardiovascular",
        "protocol_id": "PSP",
        "icon": "❤️",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["심장", "심근경색", "협심증", "심장질환", "급성심근경색", "관상동맥"],
        "war_room_key": "heart",
    },
    {
        "sector_id": "PSP-04",
        "sector_name": "실손의료비",
        "sector_name_en": "Actual Loss Medical",
        "protocol_id": "PSP",
        "icon": "💊",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["실손", "실손의료비", "실비", "의료비", "입원비", "통원비", "4세대실손"],
        "war_room_key": "medical",
    },
    {
        "sector_id": "PSP-05",
        "sector_name": "수술/입원",
        "sector_name_en": "Surgery & Hospitalization",
        "protocol_id": "PSP",
        "icon": "🏥",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["수술", "입원", "수술비", "입원비", "입원일당", "수술급여금"],
        "war_room_key": "surgery",
    },
    {
        "sector_id": "PSP-06",
        "sector_name": "치매/간병",
        "sector_name_en": "Dementia & Nursing Care",
        "protocol_id": "PSP",
        "icon": "🧓",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["치매", "간병", "장기요양", "요양병원", "간병비", "치매진단"],
        "war_room_key": "dementia",
    },
    {
        "sector_id": "PSP-07",
        "sector_name": "치아",
        "sector_name_en": "Dental",
        "protocol_id": "PSP",
        "icon": "🦷",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["치아", "치과", "임플란트", "보철", "치아보험", "치과치료"],
        "war_room_key": "dental",
    },
    {
        "sector_id": "PSP-08",
        "sector_name": "종신/정기(사망)",
        "sector_name_en": "Life Insurance",
        "protocol_id": "PSP",
        "icon": "⚰️",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["종신", "정기", "사망", "종신보험", "정기보험", "사망보험금"],
        "war_room_key": "life",
    },
    {
        "sector_id": "PSP-09",
        "sector_name": "연금",
        "sector_name_en": "Pension",
        "protocol_id": "PSP",
        "icon": "💰",
        "color": "#d97706",
        "bg_color": "#fffbeb",
        "keywords": ["연금", "노후", "연금보험", "개인연금", "국민연금", "퇴직연금"],
        "war_room_key": "pension",
    },
    {
        "sector_id": "PSP-10",
        "sector_name": "상해/레저",
        "sector_name_en": "Accident & Leisure",
        "protocol_id": "PSP",
        "icon": "🏃",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["상해", "레저", "골프", "스키", "등산", "상해보험", "레저보험"],
        "war_room_key": "accident",
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [APP] 자산 보호 프로토콜 (Asset Protection Protocol) — 6개 섹터
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "sector_id": "APP-01",
        "sector_name": "자동차",
        "sector_name_en": "Auto Insurance",
        "protocol_id": "APP",
        "icon": "🚙",
        "color": "#065f46",
        "bg_color": "#f0fdf4",
        "keywords": ["자동차", "자차", "대물", "대인", "자동차보험", "차량보험"],
        "war_room_key": "auto",
    },
    {
        "sector_id": "APP-02",
        "sector_name": "운전자",
        "sector_name_en": "Driver Insurance",
        "protocol_id": "APP",
        "icon": "🚗",
        "color": "#0369a1",
        "bg_color": "#f0f9ff",
        "keywords": ["운전자", "운전자보험", "형사합의금", "민식이법", "교통사고"],
        "war_room_key": "driver",
    },
    {
        "sector_id": "APP-03",
        "sector_name": "주택화재",
        "sector_name_en": "Home Fire Insurance",
        "protocol_id": "APP",
        "icon": "🏠",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["주택", "주택화재", "아파트화재", "화재보험", "가재도난"],
        "war_room_key": "home_fire",
    },
    {
        "sector_id": "APP-04",
        "sector_name": "개인공장 화재",
        "sector_name_en": "Personal Factory Fire",
        "protocol_id": "APP",
        "icon": "🏭",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["개인공장", "공장화재", "개인사업자", "제조업", "화재"],
        "war_room_key": "personal_factory",
    },
    {
        "sector_id": "APP-05",
        "sector_name": "법인공장 화재",
        "sector_name_en": "Corporate Factory Fire",
        "protocol_id": "APP",
        "icon": "🏢",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["법인공장", "법인화재", "공장", "법인", "화재보험"],
        "war_room_key": "corp_factory",
    },
    {
        "sector_id": "APP-06",
        "sector_name": "상가화재",
        "sector_name_en": "Commercial Fire",
        "protocol_id": "APP",
        "icon": "🏪",
        "color": "#dc2626",
        "bg_color": "#fff1f2",
        "keywords": ["상가", "상가화재", "점포", "영업손실", "화재"],
        "war_room_key": "commercial_fire",
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [BRP] 비즈니스 리스크 프로토콜 (Business Risk Protocol) — 5개 섹터
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "sector_id": "BRP-01",
        "sector_name": "PL(제조물책임)",
        "sector_name_en": "Product Liability",
        "protocol_id": "BRP",
        "icon": "⚠️",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "keywords": ["PL", "제조물책임", "배상책임", "제품결함", "리콜"],
        "war_room_key": "pl",
    },
    {
        "sector_id": "BRP-02",
        "sector_name": "전문직 배상책임",
        "sector_name_en": "Professional Liability",
        "protocol_id": "BRP",
        "icon": "👔",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "keywords": ["전문직", "배상책임", "의사", "변호사", "회계사", "건축사"],
        "war_room_key": "professional",
    },
    {
        "sector_id": "BRP-03",
        "sector_name": "단체보험",
        "sector_name_en": "Group Insurance",
        "protocol_id": "BRP",
        "icon": "👥",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "keywords": ["단체", "단체보험", "복리후생", "임직원", "직원보험"],
        "war_room_key": "group",
    },
    {
        "sector_id": "BRP-04",
        "sector_name": "근로자재해(산재보완)",
        "sector_name_en": "Workers' Compensation",
        "protocol_id": "BRP",
        "icon": "🛠️",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "keywords": ["산재", "근로자재해", "산재보험", "업무상재해", "사업주배상"],
        "war_room_key": "workers_comp",
    },
    {
        "sector_id": "BRP-05",
        "sector_name": "법인 전환 리스크",
        "sector_name_en": "Corporate Conversion Risk",
        "protocol_id": "BRP",
        "icon": "🔄",
        "color": "#7c3aed",
        "bg_color": "#f5f3ff",
        "keywords": ["법인전환", "개인사업자", "법인화", "전환", "리스크"],
        "war_room_key": "corp_conversion",
    },
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [WOP] 부(富)의 이전 및 최적화 프로토콜 (Wealth Optimization Protocol) — 4개 섹터
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "sector_id": "WOP-01",
        "sector_name": "CEO 플랜",
        "sector_name_en": "CEO Plan",
        "protocol_id": "WOP",
        "icon": "👑",
        "color": "#d97706",
        "bg_color": "#fffbeb",
        "keywords": ["CEO", "CEO플랜", "대표", "경영인", "임원", "경영인정기"],
        "war_room_key": "ceo_plan",
    },
    {
        "sector_id": "WOP-02",
        "sector_name": "상속세/증여세",
        "sector_name_en": "Inheritance & Gift Tax",
        "protocol_id": "WOP",
        "icon": "📜",
        "color": "#d97706",
        "bg_color": "#fffbeb",
        "keywords": ["상속세", "증여세", "상속", "증여", "세금", "절세"],
        "war_room_key": "inheritance_tax",
    },
    {
        "sector_id": "WOP-03",
        "sector_name": "가업승계",
        "sector_name_en": "Business Succession",
        "protocol_id": "WOP",
        "icon": "🏛️",
        "color": "#d97706",
        "bg_color": "#fffbeb",
        "keywords": ["가업승계", "승계", "경영권", "주식", "비상장주식"],
        "war_room_key": "succession",
    },
    {
        "sector_id": "WOP-04",
        "sector_name": "비상장주식평가",
        "sector_name_en": "Unlisted Stock Valuation",
        "protocol_id": "WOP",
        "icon": "📊",
        "color": "#d97706",
        "bg_color": "#fffbeb",
        "keywords": ["비상장주식", "주식평가", "상증법", "순자산", "경영권할증"],
        "war_room_key": "stock_valuation",
    },
]


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 3] 헬퍼 함수
# ──────────────────────────────────────────────────────────────────────────────

def get_protocol_by_id(protocol_id: str) -> ProtocolDefinition | None:
    """프로토콜 ID로 프로토콜 정의 조회"""
    for protocol in CORE_PROTOCOLS:
        if protocol["protocol_id"] == protocol_id:
            return protocol
    return None


def get_sector_by_id(sector_id: str) -> SectorDefinition | None:
    """섹터 ID로 섹터 정의 조회"""
    for sector in CORE_SECTORS:
        if sector["sector_id"] == sector_id:
            return sector
    return None


def get_sectors_by_protocol(protocol_id: str) -> list[SectorDefinition]:
    """프로토콜 ID로 해당 프로토콜의 모든 섹터 조회"""
    return [s for s in CORE_SECTORS if s["protocol_id"] == protocol_id]


def get_sector_by_war_room_key(war_room_key: str) -> SectorDefinition | None:
    """War Room 키로 섹터 정의 조회 (기존 시스템과의 호환성)"""
    for sector in CORE_SECTORS:
        if sector["war_room_key"] == war_room_key:
            return sector
    return None


def search_sectors_by_keyword(keyword: str) -> list[SectorDefinition]:
    """키워드로 섹터 검색"""
    keyword_lower = keyword.lower()
    results = []
    for sector in CORE_SECTORS:
        if any(keyword_lower in kw.lower() for kw in sector["keywords"]):
            results.append(sector)
    return results


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 4] War Room 호환 레이어 (기존 시스템과의 브릿지)
# ──────────────────────────────────────────────────────────────────────────────

def generate_war_room_categories() -> list[dict]:
    """
    CORE_SECTORS를 기존 _WAR_ROOM_CATEGORIES 형식으로 변환
    기존 시스템과의 호환성 유지
    """
    return [
        {
            "key": sector["war_room_key"],
            "label": f"{sector['icon']} {sector['sector_name']}",
            "color": sector["color"],
            "bg": sector["bg_color"],
            "sector_id": sector["sector_id"],
            "protocol_id": sector["protocol_id"],
        }
        for sector in CORE_SECTORS
    ]


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 5] GCS 경로 생성 함수 (4대 프로토콜 기반)
# ──────────────────────────────────────────────────────────────────────────────

def generate_gcs_path(
    protocol_id: str,
    sector_id: str,
    agent_id: str,
    person_id: str,
    file_type: Literal["report", "policy", "analysis", "consultation"],
    filename: str,
) -> str:
    """
    4대 프로토콜 체계 기반 GCS 저장 경로 생성
    
    경로 구조:
    {protocol_id}/{sector_id}/{agent_id}/{person_id}/{file_type}/{filename}
    
    예시:
    PSP/PSP-01/agent_123/person_456/report/cancer_analysis_20260401.pdf
    APP/APP-05/agent_123/person_789/policy/factory_fire_policy.pdf
    """
    return f"{protocol_id}/{sector_id}/{agent_id}/{person_id}/{file_type}/{filename}"


def generate_gcs_bucket_structure() -> dict:
    """
    GCS 버킷 구조 정의 (4대 프로토콜 기반)
    
    반환값:
    {
        "PSP": ["PSP-01", "PSP-02", ...],
        "APP": ["APP-01", "APP-02", ...],
        "BRP": ["BRP-01", "BRP-02", ...],
        "WOP": ["WOP-01", "WOP-02", ...]
    }
    """
    structure = {}
    for protocol in CORE_PROTOCOLS:
        protocol_id = protocol["protocol_id"]
        sectors = get_sectors_by_protocol(protocol_id)
        structure[protocol_id] = [s["sector_id"] for s in sectors]
    return structure


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 6] 통계 및 검증 함수
# ──────────────────────────────────────────────────────────────────────────────

def get_taxonomy_stats() -> dict:
    """분류 체계 통계 반환"""
    return {
        "total_protocols": len(CORE_PROTOCOLS),
        "total_sectors": len(CORE_SECTORS),
        "sectors_by_protocol": {
            p["protocol_id"]: len(get_sectors_by_protocol(p["protocol_id"]))
            for p in CORE_PROTOCOLS
        },
        "protocol_names": {p["protocol_id"]: p["protocol_name"] for p in CORE_PROTOCOLS},
    }


def validate_taxonomy() -> dict:
    """분류 체계 무결성 검증"""
    errors = []
    warnings = []
    
    # 1. 섹터 ID 중복 검사
    sector_ids = [s["sector_id"] for s in CORE_SECTORS]
    if len(sector_ids) != len(set(sector_ids)):
        errors.append("섹터 ID 중복 발견")
    
    # 2. War Room 키 중복 검사
    war_room_keys = [s["war_room_key"] for s in CORE_SECTORS]
    if len(war_room_keys) != len(set(war_room_keys)):
        errors.append("War Room 키 중복 발견")
    
    # 3. 프로토콜 ID 유효성 검사
    valid_protocol_ids = {p["protocol_id"] for p in CORE_PROTOCOLS}
    for sector in CORE_SECTORS:
        if sector["protocol_id"] not in valid_protocol_ids:
            errors.append(f"유효하지 않은 프로토콜 ID: {sector['protocol_id']} (섹터: {sector['sector_id']})")
    
    # 4. 25개 섹터 달성 여부
    if len(CORE_SECTORS) != 25:
        warnings.append(f"섹터 수 불일치: {len(CORE_SECTORS)}/25")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "stats": get_taxonomy_stats(),
    }


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 7] 초기화 및 검증
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 분류 체계 검증
    validation = validate_taxonomy()
    print("=" * 80)
    print("[GP-CORE-PROTOCOL] 25개 핵심 분류 체계 검증 결과")
    print("=" * 80)
    print(f"\n✅ 유효성: {validation['valid']}")
    print(f"\n📊 통계:")
    for key, value in validation["stats"].items():
        print(f"  - {key}: {value}")
    
    if validation["errors"]:
        print(f"\n❌ 오류:")
        for error in validation["errors"]:
            print(f"  - {error}")
    
    if validation["warnings"]:
        print(f"\n⚠️ 경고:")
        for warning in validation["warnings"]:
            print(f"  - {warning}")
    
    print("\n" + "=" * 80)
    print("War Room 호환 레이어 생성 테스트")
    print("=" * 80)
    war_room_cats = generate_war_room_categories()
    print(f"\n생성된 카테고리 수: {len(war_room_cats)}")
    print("\n샘플 (처음 5개):")
    for cat in war_room_cats[:5]:
        print(f"  - {cat['label']} (key: {cat['key']}, protocol: {cat['protocol_id']})")
    
    print("\n" + "=" * 80)
    print("GCS 경로 생성 테스트")
    print("=" * 80)
    sample_path = generate_gcs_path(
        protocol_id="PSP",
        sector_id="PSP-01",
        agent_id="agent_123",
        person_id="person_456",
        file_type="report",
        filename="cancer_analysis_20260401.pdf"
    )
    print(f"\n샘플 경로: {sample_path}")
    
    print("\n" + "=" * 80)
    print("검증 완료")
    print("=" * 80)
