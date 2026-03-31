# -*- coding: utf-8 -*-
"""
modules/property_engine.py
────────────────────────────────────────────────────────────────────────────
🏢 건물 급수 산출 엔진 (Property Grade Classification Engine)
화재보험 전문가 로직 - 건물 구조/지붕/외벽 기반 급수 자동 판정
────────────────────────────────────────────────────────────────────────────
목적:
  건물의 구조, 지붕, 외벽 재료를 입력받아 화재보험 급수(1~4급)를 자동 판정하고
  요율 할증률을 계산하여 우측 분석창에 표시

급수 판정 기준 (Fire Insurance Standard):
  1급: 기둥/보/바닥이 내화구조(콘크리트, 철근콘크리트) + 지붕이 불연재료
  2급: 외벽이 벽돌, 석조 등 + 지붕이 불연재료
  3급: 외벽이 목재나 가연성 재료
  4급: 그 외 가설 건축물 등

데이터 흐름:
  사용자 입력 (구조/지붕/외벽) → classify_building_grade() → 급수 판정 + 요율 계산
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


# ─────────────────────────────────────────────────────────────────────────────
# §1  건물 재료 및 구조 상수
# ─────────────────────────────────────────────────────────────────────────────

# 기둥/보/바닥 구조 (Structure)
STRUCTURE_FIREPROOF = "내화구조"  # 콘크리트, 철근콘크리트
STRUCTURE_SEMI_FIREPROOF = "준내화구조"  # 경량철골, ALC
STRUCTURE_WOOD = "목구조"  # 목재
STRUCTURE_STEEL = "철골구조"  # 철골
STRUCTURE_TEMPORARY = "가설구조"  # 컨테이너, 조립식

# 지붕 재료 (Roof)
ROOF_NONCOMBUSTIBLE = "불연재료"  # 기와, 슬레이트, 금속
ROOF_SEMICOMBUSTIBLE = "준불연재료"  # 아스팔트 싱글
ROOF_COMBUSTIBLE = "가연재료"  # 목재, 비닐

# 외벽 재료 (Wall)
WALL_BRICK = "벽돌/석조"  # 벽돌, 석재
WALL_CONCRETE = "콘크리트"  # 콘크리트, 시멘트
WALL_METAL = "금속"  # 철판, 알루미늄
WALL_WOOD = "목재"  # 목재
WALL_COMBUSTIBLE = "가연성재료"  # 비닐, 천막

# 감가상각률 (Depreciation Rate) - 구조별 연간 감가율
DEPRECIATION_RATES = {
    STRUCTURE_FIREPROOF: 0.010,      # 내화구조 1.0%/년
    STRUCTURE_SEMI_FIREPROOF: 0.015, # 준내화구조 1.5%/년
    STRUCTURE_STEEL: 0.012,          # 철골구조 1.2%/년
    STRUCTURE_WOOD: 0.020,           # 목구조 2.0%/년
    STRUCTURE_TEMPORARY: 0.030,      # 가설구조 3.0%/년
}

# 80% 코인슈어런스 기준
COINSURANCE_RATIO = 0.80  # 건물 가액의 80% 이상 가입 필수

# ─────────────────────────────────────────────────────────────────────────────
# §1-2  2026년 재조달가액 감정 엔진 - 용도별 평당 단가 DB
# ─────────────────────────────────────────────────────────────────────────────

# 건물 용도 (Building Use)
USE_APARTMENT = "아파트"
USE_COMMERCIAL = "상가/오피스"
USE_HOUSE = "단독주택"
USE_FACTORY = "공장/창고"

# 2026년 기준 용도별 표준 재조달 단가 (평당, 만원)
# 직접공사비 + 부대비용(5~7%) + 철거/폐기물 처리비 포함
REPLACEMENT_COST_PER_PYEONG_2026 = {
    USE_APARTMENT: 800,      # 아파트 800만원/평 (부대비용 포함)
    USE_COMMERCIAL: 900,     # 상가/오피스 900만원/평 (스마트 설비 가산)
    USE_HOUSE: 850,          # 단독주택 850만원/평 (부대비용 포함)
    USE_FACTORY: 450,        # 공장/창고 450만원/평 (구조별 차등)
}

# 부대비용 비율 (설계/감리/철거/폐기물 처리)
OVERHEAD_COST_RATIO = 0.05  # 직접공사비의 5%

# 친환경/스마트 빌딩 프리미엄 (Green/Smart Building Premium)
GREEN_BUILDING_PREMIUM_MIN = 0.15  # 최소 15% 상향
GREEN_BUILDING_PREMIUM_MAX = 0.20  # 최대 20% 상향


# ─────────────────────────────────────────────────────────────────────────────
# §2  급수 판정 결과 구조체
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class BuildingGradeResult:
    """건물 급수 판정 결과."""
    grade: Literal[1, 2, 3, 4]          # 급수 (1~4급)
    grade_name: str                      # 급수명 (1급지, 2급지, ...)
    structure: str                       # 구조
    roof: str                            # 지붕
    wall: str                            # 외벽
    base_rate: float                     # 기본 요율 (%)
    surcharge_rate: float                # 할증률 (%)
    final_rate: float                    # 최종 요율 (%)
    risk_level: str                      # 위험도 (낮음/보통/높음/매우높음)
    recommendation: str                  # 권장사항
    details: str                         # 상세 설명


@dataclass
class AssetValuation:
    """자산 가치 평가 결과."""
    replacement_cost: float              # 재조달가액 (신가, 만원)
    building_age: int                    # 건축 경과년수
    depreciation_rate: float             # 연간 감가율 (%)
    total_depreciation: float            # 총 감가액 (만원)
    actual_cash_value: float             # 보험가액 (시가, 만원)
    coinsurance_minimum: float           # 80% 코인슈어런스 최소 가입액 (만원)
    depreciation_ratio: float            # 감가 비율 (%)
    building_use: Optional[str] = None   # 건물 용도 (아파트/상가/주택/공장)
    area_pyeong: Optional[float] = None  # 연면적 (평)
    unit_price: Optional[float] = None   # 평당 단가 (만원)
    is_green_building: bool = False      # 친환경/스마트 빌딩 여부
    green_premium_ratio: float = 0.0     # 친환경 프리미엄 비율


@dataclass
class CoinsuranceResult:
    """80% 코인슈어런스 비례보상 결과."""
    actual_cash_value: float             # 보험가액 (시가, 만원)
    insured_amount: float                # 실제 가입금액 (만원)
    coinsurance_minimum: float           # 80% 기준 최소 가입액 (만원)
    loss_amount: float                   # 손해액 (만원)
    is_adequate: bool                    # 충분 가입 여부
    penalty_ratio: float                 # 비례보상 비율 (0.0~1.0)
    actual_payout: float                 # 실제 지급 보험금 (만원)
    penalty_amount: float                # 패널티 금액 (만원)
    warning_message: str                 # 경고 메시지


# ─────────────────────────────────────────────────────────────────────────────
# §3  급수 판정 로직
# ─────────────────────────────────────────────────────────────────────────────

def classify_building_grade(
    structure: str,
    roof: str,
    wall: str,
) -> BuildingGradeResult:
    """
    건물 급수 자동 판정.
    
    Args:
        structure: 기둥/보/바닥 구조 (내화구조, 준내화구조, 목구조, 철골구조, 가설구조)
        roof: 지붕 재료 (불연재료, 준불연재료, 가연재료)
        wall: 외벽 재료 (벽돌/석조, 콘크리트, 금속, 목재, 가연성재료)
    
    Returns:
        BuildingGradeResult 객체
    
    급수 판정 기준:
        1급: 내화구조 + 불연재료 지붕
        2급: (벽돌/석조 또는 콘크리트 외벽) + 불연재료 지붕
        3급: 목재 또는 가연성 외벽
        4급: 가설구조 또는 가연재료 지붕
    """
    # 1급 판정: 내화구조 + 불연재료 지붕
    if structure == STRUCTURE_FIREPROOF and roof == ROOF_NONCOMBUSTIBLE:
        return BuildingGradeResult(
            grade=1,
            grade_name="1급지",
            structure=structure,
            roof=roof,
            wall=wall,
            base_rate=0.05,  # 기본 요율 0.05%
            surcharge_rate=0.0,  # 할증 없음
            final_rate=0.05,
            risk_level="낮음",
            recommendation="최우수 등급입니다. 화재 위험이 매우 낮아 보험료가 가장 저렴합니다.",
            details=(
                "내화구조(콘크리트/철근콘크리트) 건물로 기둥, 보, 바닥이 모두 불에 타지 않는 재료로 구성되어 있으며, "
                "지붕 또한 불연재료(기와/슬레이트/금속)로 되어 있어 화재 확산 위험이 극히 낮습니다."
            )
        )
    
    # 2급 판정: (벽돌/석조 또는 콘크리트 외벽) + 불연재료 지붕
    if (wall in [WALL_BRICK, WALL_CONCRETE] and roof == ROOF_NONCOMBUSTIBLE):
        return BuildingGradeResult(
            grade=2,
            grade_name="2급지",
            structure=structure,
            roof=roof,
            wall=wall,
            base_rate=0.08,  # 기본 요율 0.08%
            surcharge_rate=60.0,  # 1급 대비 60% 할증
            final_rate=0.08,
            risk_level="보통",
            recommendation="양호한 등급입니다. 외벽과 지붕이 불연재료로 화재 위험이 낮습니다.",
            details=(
                f"외벽이 {wall}로 되어 있고 지붕이 불연재료로 구성되어 있어 "
                "화재 발생 시 확산 속도가 느립니다. 1급 대비 요율이 60% 높지만 여전히 안전한 구조입니다."
            )
        )
    
    # 4급 판정: 가설구조 또는 가연재료 지붕 (최우선 체크)
    if structure == STRUCTURE_TEMPORARY or roof == ROOF_COMBUSTIBLE:
        return BuildingGradeResult(
            grade=4,
            grade_name="4급지",
            structure=structure,
            roof=roof,
            wall=wall,
            base_rate=0.30,  # 기본 요율 0.30%
            surcharge_rate=500.0,  # 1급 대비 500% 할증
            final_rate=0.30,
            risk_level="매우높음",
            recommendation="🔥 고위험 등급. 가설 건축물 또는 가연성 지붕으로 화재 위험이 매우 높습니다.",
            details=(
                f"구조: {structure}, 지붕: {roof}로 화재 발생 시 전소 위험이 매우 높습니다. "
                "1급 대비 요율이 500% 높으며, 보험 가입이 거부될 수 있습니다. "
                "건물 구조 개선(외벽 교체, 지붕 불연재료 교체)을 강력히 권장합니다."
            )
        )
    
    # 3급 판정: 목재 또는 가연성 외벽
    if wall in [WALL_WOOD, WALL_COMBUSTIBLE]:
        return BuildingGradeResult(
            grade=3,
            grade_name="3급지",
            structure=structure,
            roof=roof,
            wall=wall,
            base_rate=0.15,  # 기본 요율 0.15%
            surcharge_rate=200.0,  # 1급 대비 200% 할증
            final_rate=0.15,
            risk_level="높음",
            recommendation="⚠️ 주의 필요. 외벽이 가연성 재료로 화재 위험이 높습니다.",
            details=(
                f"외벽이 {wall}로 되어 있어 화재 발생 시 빠르게 확산될 위험이 있습니다. "
                "1급 대비 요율이 200% 높으며, 화재 예방 시설(소화기, 스프링클러) 설치를 강력히 권장합니다."
            )
        )
    
    # 기본값: 2급 (준내화구조 등)
    return BuildingGradeResult(
        grade=2,
        grade_name="2급지",
        structure=structure,
        roof=roof,
        wall=wall,
        base_rate=0.08,
        surcharge_rate=60.0,
        final_rate=0.08,
        risk_level="보통",
        recommendation="표준 등급입니다. 일반적인 건물 구조로 화재 위험이 보통 수준입니다.",
        details=(
            f"구조: {structure}, 지붕: {roof}, 외벽: {wall}로 구성된 건물입니다. "
            "화재 위험이 보통 수준이며, 1급 대비 요율이 60% 높습니다."
        )
    )


# ─────────────────────────────────────────────────────────────────────────────
# §4  자산 가치 평가 엔진 (Asset Valuation Engine)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_replacement_cost_by_area(
    area_pyeong: float,
    building_use: str,
    is_green_building: bool = False,
) -> dict:
    """
    면적 기반 재조달가액 계산 (2026년 기준).
    
    Args:
        area_pyeong: 연면적 (평)
        building_use: 건물 용도 (아파트/상가/주택/공장)
        is_green_building: 친환경/스마트 빌딩 여부
    
    Returns:
        재조달가액 계산 결과 딕셔너리
    """
    # 용도별 평당 단가 조회
    unit_price = REPLACEMENT_COST_PER_PYEONG_2026.get(building_use, 800)
    
    # 친환경/스마트 빌딩 프리미엄 적용
    green_premium_ratio = 0.0
    if is_green_building:
        # 15~20% 프리미엄 (평균 17.5% 적용)
        green_premium_ratio = (GREEN_BUILDING_PREMIUM_MIN + GREEN_BUILDING_PREMIUM_MAX) / 2
        unit_price = unit_price * (1 + green_premium_ratio)
    
    # 기본 재조달가액 (면적 × 평당 단가)
    base_cost = area_pyeong * unit_price
    
    # 부대비용 자동 합산 (설계/감리/철거/폐기물 처리 5%)
    overhead_cost = base_cost * OVERHEAD_COST_RATIO
    
    # 최종 재조달가액 (부대비용 포함)
    total_replacement_cost = base_cost + overhead_cost
    
    return {
        "area_pyeong": area_pyeong,
        "building_use": building_use,
        "unit_price": unit_price,
        "base_cost": base_cost,
        "overhead_cost": overhead_cost,
        "total_replacement_cost": total_replacement_cost,
        "is_green_building": is_green_building,
        "green_premium_ratio": green_premium_ratio,
    }


def calculate_asset_valuation(
    replacement_cost: float,
    building_year: int,
    current_year: int,
    structure: str,
    building_use: Optional[str] = None,
    area_pyeong: Optional[float] = None,
    is_green_building: bool = False,
) -> AssetValuation:
    """
    재조달가액 기반 보험가액 계산 (감가상각 적용).
    
    Args:
        replacement_cost: 재조달가액 (신가, 만원)
        building_year: 건축 연도 (예: 2004)
        current_year: 현재 연도 (예: 2026)
        structure: 건물 구조 (내화구조, 준내화구조, 목구조, 철골구조, 가설구조)
    
    Returns:
        AssetValuation 객체
    
    공식:
        보험가액 = 재조달가액 - 경년감가액
        경년감가액 = 재조달가액 × 경과년수 × 연간 감가율
    """
    # 건축 경과년수 계산
    building_age = current_year - building_year
    if building_age < 0:
        building_age = 0
    
    # 구조별 감가율 조회
    depreciation_rate = DEPRECIATION_RATES.get(structure, 0.015)  # 기본값 1.5%
    
    # 총 감가액 계산 (최대 100%까지만)
    total_depreciation_ratio = min(building_age * depreciation_rate, 1.0)
    total_depreciation = replacement_cost * total_depreciation_ratio
    
    # 보험가액 (시가) 계산
    actual_cash_value = replacement_cost - total_depreciation
    if actual_cash_value < 0:
        actual_cash_value = 0
    
    # 80% 코인슈어런스 최소 가입액
    coinsurance_minimum = actual_cash_value * COINSURANCE_RATIO
    
    # 평당 단가 계산 (면적이 제공된 경우)
    unit_price = None
    if area_pyeong and area_pyeong > 0:
        unit_price = replacement_cost / area_pyeong
    
    # 친환경 프리미엄 비율 계산
    green_premium_ratio = 0.0
    if is_green_building:
        green_premium_ratio = (GREEN_BUILDING_PREMIUM_MIN + GREEN_BUILDING_PREMIUM_MAX) / 2
    
    return AssetValuation(
        replacement_cost=replacement_cost,
        building_age=building_age,
        depreciation_rate=depreciation_rate,
        total_depreciation=total_depreciation,
        actual_cash_value=actual_cash_value,
        coinsurance_minimum=coinsurance_minimum,
        depreciation_ratio=total_depreciation_ratio * 100,
        building_use=building_use,
        area_pyeong=area_pyeong,
        unit_price=unit_price,
        is_green_building=is_green_building,
        green_premium_ratio=green_premium_ratio,
    )


# ─────────────────────────────────────────────────────────────────────────────
# §5  80% 코인슈어런스 비례보상 엔진
# ─────────────────────────────────────────────────────────────────────────────

def calculate_coinsurance_payout(
    actual_cash_value: float,
    insured_amount: float,
    loss_amount: float,
) -> CoinsuranceResult:
    """
    80% 코인슈어런스 비례보상 계산.
    
    Args:
        actual_cash_value: 보험가액 (시가, 만원)
        insured_amount: 실제 가입금액 (만원)
        loss_amount: 손해액 (만원)
    
    Returns:
        CoinsuranceResult 객체
    
    공식:
        보험금 = 손해액 × (실제 가입금액 / (보험가액 × 80%))
        
    핵심:
        - 보험가액의 80% 이상 가입 시: 실손보상 (손해액 전액)
        - 80% 미만 가입 시: 비례보상 (패널티 적용)
    """
    # 80% 기준 최소 가입액
    coinsurance_minimum = actual_cash_value * COINSURANCE_RATIO
    
    # 충분 가입 여부 판단
    is_adequate = insured_amount >= coinsurance_minimum
    
    if is_adequate:
        # 실손보상: 손해액 전액 지급 (단, 가입금액 한도)
        actual_payout = min(loss_amount, insured_amount)
        penalty_ratio = 1.0
        penalty_amount = 0
        warning_message = "✅ 충분한 가입금액입니다. 손해액 전액 보상됩니다."
    else:
        # 비례보상: 패널티 적용
        penalty_ratio = insured_amount / coinsurance_minimum
        actual_payout = loss_amount * penalty_ratio
        
        # 가입금액 한도 체크
        if actual_payout > insured_amount:
            actual_payout = insured_amount
        
        penalty_amount = loss_amount - actual_payout
        
        shortage = coinsurance_minimum - insured_amount
        penalty_percent = (1 - penalty_ratio) * 100
        
        warning_message = (
            f"⚠️ 과소 보험 경고!\n"
            f"보험가액의 80% 미만 가입으로 비례보상이 적용됩니다.\n"
            f"부족 금액: {shortage:,.0f}만원\n"
            f"보상 삭감률: {penalty_percent:.1f}%\n"
            f"실제 지급액: {actual_payout:,.0f}만원 (손해액 {loss_amount:,.0f}만원 중)"
        )
    
    return CoinsuranceResult(
        actual_cash_value=actual_cash_value,
        insured_amount=insured_amount,
        coinsurance_minimum=coinsurance_minimum,
        loss_amount=loss_amount,
        is_adequate=is_adequate,
        penalty_ratio=penalty_ratio,
        actual_payout=actual_payout,
        penalty_amount=penalty_amount,
        warning_message=warning_message,
    )


# ─────────────────────────────────────────────────────────────────────────────
# §6  요율 계산 헬퍼 함수
# ─────────────────────────────────────────────────────────────────────────────

def calculate_premium(
    building_value: float,
    grade_result: BuildingGradeResult,
) -> dict:
    """
    화재보험료 계산.
    
    Args:
        building_value: 건물 가액 (만원)
        grade_result: 급수 판정 결과
    
    Returns:
        {
            "building_value": 건물 가액 (만원),
            "grade": 급수,
            "base_rate": 기본 요율 (%),
            "annual_premium": 연간 보험료 (원),
            "monthly_premium": 월 보험료 (원),
        }
    """
    annual_premium = building_value * 10000 * (grade_result.final_rate / 100)
    monthly_premium = annual_premium / 12
    
    return {
        "building_value": building_value,
        "grade": grade_result.grade,
        "grade_name": grade_result.grade_name,
        "base_rate": grade_result.final_rate,
        "annual_premium": int(annual_premium),
        "monthly_premium": int(monthly_premium),
        "surcharge_rate": grade_result.surcharge_rate,
    }


# ─────────────────────────────────────────────────────────────────────────────
# §7  UI 헬퍼 함수
# ─────────────────────────────────────────────────────────────────────────────

def get_structure_options() -> list[str]:
    """구조 선택 옵션 반환."""
    return [
        STRUCTURE_FIREPROOF,
        STRUCTURE_SEMI_FIREPROOF,
        STRUCTURE_STEEL,
        STRUCTURE_WOOD,
        STRUCTURE_TEMPORARY,
    ]


def get_roof_options() -> list[str]:
    """지붕 선택 옵션 반환."""
    return [
        ROOF_NONCOMBUSTIBLE,
        ROOF_SEMICOMBUSTIBLE,
        ROOF_COMBUSTIBLE,
    ]


def get_wall_options() -> list[str]:
    """외벽 선택 옵션 반환."""
    return [
        WALL_CONCRETE,
        WALL_BRICK,
        WALL_METAL,
        WALL_WOOD,
        WALL_COMBUSTIBLE,
    ]


def get_building_use_options() -> list[str]:
    """건물 용도 선택 옵션 반환."""
    return [
        USE_APARTMENT,
        USE_COMMERCIAL,
        USE_HOUSE,
        USE_FACTORY,
    ]


def format_grade_result(result: BuildingGradeResult) -> str:
    """
    급수 판정 결과를 포맷팅된 문자열로 변환.
    
    Returns:
        마크다운 형식의 결과 문자열
    """
    risk_emoji = {
        "낮음": "✅",
        "보통": "⚠️",
        "높음": "🔥",
        "매우높음": "🚨",
    }
    
    return f"""
## 🏢 건물 급수 판정 결과

### 📊 판정 등급
**{result.grade_name} ({result.grade}급)**  
위험도: {risk_emoji.get(result.risk_level, "⚠️")} **{result.risk_level}**

### 🏗️ 건물 정보
- **구조**: {result.structure}
- **지붕**: {result.roof}
- **외벽**: {result.wall}

### 💰 요율 정보
- **기본 요율**: {result.final_rate:.2f}%
- **할증률**: {result.surcharge_rate:.0f}% (1급 대비)

### 💡 권장사항
{result.recommendation}

### 📝 상세 설명
{result.details}
"""


def get_land_exclusion_warning() -> str:
    """
    토지 가액 배제 경고 메시지 반환.
    
    Returns:
        토지 가액 배제 경고 문구
    """
    return """
⚠️ **중요: 토지 가액 배제 원칙**

재조달가액은 **'건물(구축물)'의 재생산 비용**만을 의미하며, **토지 가격은 절대 포함되지 않습니다**.

- ✅ 포함: 건물 신축 비용 (자재비 + 인건비 + 설계/감리비 + 철거/폐기물 처리비)
- ❌ 제외: 토지 매입 비용, 토지 가격 상승분

**잘못된 예시**: "건물 + 토지 = 10억원" → 토지 가액 제외 필요  
**올바른 예시**: "건물만 = 8억원" → 재조달가액으로 사용 가능

💡 **왜 중요한가?**  
토지 가액을 포함하면 **초과보험(Over-insurance)**이 되어 보험료만 낭비하게 됩니다.  
보험사는 건물 손해만 보상하며, 토지는 화재로 손실되지 않기 때문입니다.
"""


def get_underinsurance_warning_2026() -> str:
    """
    2026년 과소 보험 경고 메시지 반환.
    
    Returns:
        과소 보험 경고 문구
    """
    return """
🚨 **2026년 긴급 경고: 과소 보험(Under-insurance) 위험**

**최근 원자재값 폭등**으로 인해 2년 전 가입한 보험금은 현재 **과소 보험 상태일 확률이 높습니다**.

- 2024년 대비 건설 자재비 상승률: **평균 15~20%**
- 2년 전 가입금액이 현재 재조달가액의 80% 미만일 경우: **비례보상 패널티 적용**

💡 **80% 부보 비율 미달 시 보상액 삭감 예시**:  
- 보험가액: 8억원 (80% 기준 최소 6.4억원)  
- 실제 가입금액: 4억원 (50%)  
- 손해액: 5천만원 → **실제 지급액: 3,125만원** (37.5% 삭감)

**재평가가 시급합니다!** 현재 건물 가치를 재산정하여 적정 가입금액을 확인하세요.
"""


def format_asset_valuation(valuation: AssetValuation) -> str:
    """
    자산 가치 평가 결과를 포맷팅된 문자열로 변환.
    
    Returns:
        마크다운 형식의 결과 문자열
    """
    # 기본 정보
    result = f"""
## 💰 자산 가치 평가 결과

### 📊 재조달가액 vs 보험가액

| 구분 | 금액 |
|------|------|
| **재조달가액 (신가)** | {valuation.replacement_cost:,.0f}만원 |
"""
    
    # 면적 및 용도 정보 (제공된 경우)
    if valuation.area_pyeong and valuation.building_use:
        result += f"| **건물 용도** | {valuation.building_use} |\n"
        result += f"| **연면적** | {valuation.area_pyeong:.1f}평 |\n"
        if valuation.unit_price:
            result += f"| **평당 단가** | {valuation.unit_price:,.0f}만원 |\n"
    
    # 친환경 빌딩 프리미엄 (적용된 경우)
    if valuation.is_green_building:
        premium_pct = valuation.green_premium_ratio * 100
        result += f"| **친환경/스마트 빌딩 프리미엄** | +{premium_pct:.1f}% |\n"
    
    # 감가상각 정보
    result += f"""| **건축 경과년수** | {valuation.building_age}년 |
| **연간 감가율** | {valuation.depreciation_rate:.2f}% |
| **총 감가액** | {valuation.total_depreciation:,.0f}만원 ({valuation.depreciation_ratio:.1f}%) |
| **보험가액 (시가)** | {valuation.actual_cash_value:,.0f}만원 |

### 🎯 80% 코인슈어런스 기준
**최소 가입 권장액**: {valuation.coinsurance_minimum:,.0f}만원

💡 **중요**: 보험가액의 80% 이상 가입 시 실손보상, 미만 시 비례보상 적용  
⚠️ **토지 가액은 포함되지 않습니다** (건물 재생산 비용만 해당)
"""
    
    return result


def format_coinsurance_result(result: CoinsuranceResult) -> str:
    """
    코인슈어런스 비례보상 결과를 포맷팅된 문자열로 변환.
    
    Returns:
        마크다운 형식의 결과 문자열
    """
    status_emoji = "✅" if result.is_adequate else "🚨"
    
    return f"""
## {status_emoji} 80% 코인슈어런스 시뮬레이션

### 📋 가입 현황
- **보험가액 (시가)**: {result.actual_cash_value:,.0f}만원
- **실제 가입금액**: {result.insured_amount:,.0f}만원
- **80% 기준 최소액**: {result.coinsurance_minimum:,.0f}만원
- **가입 비율**: {(result.insured_amount / result.actual_cash_value * 100):.1f}%

### 💥 사고 시나리오
- **손해액**: {result.loss_amount:,.0f}만원
- **비례보상 비율**: {result.penalty_ratio * 100:.1f}%
- **실제 지급 보험금**: {result.actual_payout:,.0f}만원
- **패널티 금액**: {result.penalty_amount:,.0f}만원

### ⚠️ 경고
{result.warning_message}
"""


# ─────────────────────────────────────────────────────────────────────────────
# §8  테스트 및 검증
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("🏢 화재보험 전문가 엔진 V2 테스트")
    print("=" * 80)
    print("📌 테스트 항목:")
    print("  1. 건물 급수 판정 (1~4급)")
    print("  2. 자산 가치 평가 (재조달가액 vs 보험가액)")
    print("  3. 80% 코인슈어런스 비례보상 시뮬레이션")
    print("=" * 80)
    print("\n" + "=" * 80)
    print("🏛️ 건물 급수 판정 테스트")
    print("=" * 80)
    
    # 테스트 케이스
    test_cases = [
        {
            "name": "최우수 건물 (1급)",
            "structure": STRUCTURE_FIREPROOF,
            "roof": ROOF_NONCOMBUSTIBLE,
            "wall": WALL_CONCRETE,
        },
        {
            "name": "양호 건물 (2급)",
            "structure": STRUCTURE_SEMI_FIREPROOF,
            "roof": ROOF_NONCOMBUSTIBLE,
            "wall": WALL_BRICK,
        },
        {
            "name": "주의 건물 (3급)",
            "structure": STRUCTURE_WOOD,
            "roof": ROOF_NONCOMBUSTIBLE,
            "wall": WALL_WOOD,
        },
        {
            "name": "고위험 건물 (4급)",
            "structure": STRUCTURE_TEMPORARY,
            "roof": ROOF_COMBUSTIBLE,
            "wall": WALL_COMBUSTIBLE,
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"테스트 {i}: {case['name']}")
        print(f"{'─' * 80}")
        
        result = classify_building_grade(
            structure=case["structure"],
            roof=case["roof"],
            wall=case["wall"],
        )
        
        print(f"급수: {result.grade_name} ({result.grade}급)")
        print(f"위험도: {result.risk_level}")
        print(f"기본 요율: {result.final_rate:.2f}%")
        print(f"할증률: {result.surcharge_rate:.0f}% (1급 대비)")
        print(f"권장사항: {result.recommendation}")
        
        # 보험료 계산 예시 (건물 가액 5억원)
        premium = calculate_premium(50000, result)
        print(f"\n💰 보험료 예시 (건물 가액 5억원)")
        print(f"  - 연간 보험료: {premium['annual_premium']:,}원")
        print(f"  - 월 보험료: {premium['monthly_premium']:,}원")
    
    # 급수별 보험료 비교
    print("\n" + "=" * 80)
    print("📊 급수별 보험료 비교 (건물 가액 5억원)")
    print("=" * 80)
    print(f"{'\n급수':<10} {'\uc694율':<10} {'\uc5f0간 보험료':<15} {'\uc6d4 보험료':<15} {'1급 대비 차액'}")
    print("-" * 80)
    
    grade_1_premium = 250000
    for i, case in enumerate(test_cases, 1):
        result = classify_building_grade(
            structure=case["structure"],
            roof=case["roof"],
            wall=case["wall"],
        )
        premium = calculate_premium(50000, result)
        diff = premium['annual_premium'] - grade_1_premium
        print(f"{result.grade}급{'':<8} {result.final_rate:.2f}%{'':<6} {premium['annual_premium']:>10,}원{'':<5} {premium['monthly_premium']:>10,}원{'':<5} +{diff:,}원")
    
    print("\n" + "=" * 80)
    print("💰 자산 가치 평가 테스트")
    print("=" * 80)
    
    # 자산 가치 평가 테스트 (20년 된 내화구조 건물)
    print("\n🏛️ 테스트: 20년 된 내화구조 건물 (10억원)")
    print("-" * 80)
    
    valuation = calculate_asset_valuation(
        replacement_cost=100000,  # 10억원 (만원 단위)
        building_year=2004,
        current_year=2024,
        structure=STRUCTURE_FIREPROOF,
    )
    
    print(f"재조달가액 (신가): {valuation.replacement_cost:,.0f}만원")
    print(f"건축 경과년수: {valuation.building_age}년")
    print(f"연간 감가율: {valuation.depreciation_rate:.2f}%")
    print(f"총 감가액: {valuation.total_depreciation:,.0f}만원 ({valuation.depreciation_ratio:.1f}%)")
    print(f"보험가액 (시가): {valuation.actual_cash_value:,.0f}만원")
    print(f"80% 코인슈어런스 최소액: {valuation.coinsurance_minimum:,.0f}만원")
    
    print("\n" + "=" * 80)
    print("🚨 80% 코인슈어런스 시뮬레이션")
    print("=" * 80)
    
    # 케이스 A: 충분 가입 (80% 이상)
    print("\n👍 케이스 A: 충분 가입 (80% 이상)")
    print("-" * 80)
    
    case_a = calculate_coinsurance_payout(
        actual_cash_value=valuation.actual_cash_value,
        insured_amount=70000,  # 7억원 가입 (80% 이상)
        loss_amount=5000,      # 5천만원 손해
    )
    
    print(f"보험가액: {case_a.actual_cash_value:,.0f}만원")
    print(f"가입금액: {case_a.insured_amount:,.0f}만원 (가입비율 {(case_a.insured_amount/case_a.actual_cash_value*100):.1f}%)")
    print(f"손해액: {case_a.loss_amount:,.0f}만원")
    print(f"실제 지급 보험금: {case_a.actual_payout:,.0f}만원")
    print(f"패널티: {case_a.penalty_amount:,.0f}만원")
    print(f"결과: {case_a.warning_message.split(chr(10))[0]}")
    
    # 케이스 B: 과소 보험 (80% 미만)
    print("\n⚠️ 케이스 B: 과소 보험 (80% 미만)")
    print("-" * 80)
    
    case_b = calculate_coinsurance_payout(
        actual_cash_value=valuation.actual_cash_value,
        insured_amount=40000,  # 4억원만 가입 (80% 미만)
        loss_amount=5000,      # 5천만원 손해
    )
    
    print(f"보험가액: {case_b.actual_cash_value:,.0f}만원")
    print(f"가입금액: {case_b.insured_amount:,.0f}만원 (가입비율 {(case_b.insured_amount/case_b.actual_cash_value*100):.1f}%)")
    print(f"80% 기준 최소액: {case_b.coinsurance_minimum:,.0f}만원")
    print(f"부족 금액: {case_b.coinsurance_minimum - case_b.insured_amount:,.0f}만원")
    print(f"손해액: {case_b.loss_amount:,.0f}만원")
    print(f"비례보상 비율: {case_b.penalty_ratio * 100:.1f}%")
    print(f"실제 지급 보험금: {case_b.actual_payout:,.0f}만원 (패널티 {case_b.penalty_amount:,.0f}만원)")
    print(f"보상 삭감률: {(1 - case_b.penalty_ratio) * 100:.1f}%")
    
    print("\n" + "=" * 80)
    print("✅ 모든 테스트 완료")
    print("=" * 80)
    print("\n💡 핵심 결과:")
    print(f"  - 20년 된 건물의 보험가액은 재조달가액 대비 {100 - valuation.depreciation_ratio:.1f}% 수준")
    print(f"  - 80% 미만 가입 시 보상액이 {(1 - case_b.penalty_ratio) * 100:.1f}% 삭감됨")
    print(f"  - 케이스 B에서 {case_b.penalty_amount:,.0f}만원 손해 발생!")
