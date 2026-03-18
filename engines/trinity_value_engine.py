# -*- coding: utf-8 -*-
"""
engines/trinity_value_engine.py
────────────────────────────────────────────────────────────────────────────
🔱 트리니티(Trinity) 경제가치 분석 엔진 — 독립 모듈
KB 엔진(상품 중심)과 완전 분리된 '인생 가치 산출기'

Tri-Logic 3축:
  ① 소득 역산 축  (Income Back-calculation)  — 건보료 → 월소득 → 연봉
  ② 소득 대체 공백 축 (Income Gap Analysis)  — 24개월 골든타임 필요 자금
  ③ 심리적 클로징 축  (Psychological Closing) — Fact-Crisis-Gap-Solution 스크립트

건강보험료율 기준 (2026):
  직장가입자 총 요율: 7.19%  →  본인 부담: 7.19 / 2 = 3.595% (노사 각 50%)
  역산 공식: 본인납부액 × 2 ÷ 7.19% = 추정 월소득
  장기요양보험: 건보료의 12.95% (별도, 역산 시 제외)
  상한: 월 보수 110,332,300원
  하한: 월 보수 279,256원
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# §1  건보료 상수 (2026 기준)
# ─────────────────────────────────────────────────────────────────────────────
TOTAL_HEALTH_RATE_2026       = 0.0719   # 2026년 총 건강보험료율 (7.19%)
EMPLOYEE_RATE                = TOTAL_HEALTH_RATE_2026 / 2   # 근로자 본인 부담분 (50%, ≈3.595%)
AVERAGE_TOTAL_DEDUCTION_RATE = 0.155   # 평균 총 공제율 (4대보험 9.5% + 소득세 6% = 15.5%)
LTC_RATE_ON_NHIS       = 0.1295          # 장기요양보험료 = 건보료 × 12.95%

# 월 보수 상한/하한
MONTHLY_INCOME_MAX   = 110_332_300   # 원
MONTHLY_INCOME_MIN   =     279_256   # 원

# 본인부담 건보료 상한/하한
NHIS_PREMIUM_MAX     = int(MONTHLY_INCOME_MAX * EMPLOYEE_RATE)   # ≈ 3,966,446원
NHIS_PREMIUM_MIN     = int(MONTHLY_INCOME_MIN * EMPLOYEE_RATE)   # ≈ 10,041원

# 골든타임: 중대 질병 소득 대체 기간
GOLDEN_TIME_MONTHS   = 24

# 지역가입자 소득 등급별 근사 건보료 → 추정 월 소득 (만원 단위, 2024 기준)
# (건보료_원, 추정_월소득_만원) — 최소 ~ 최대 11등급 점프
_LOCAL_APPROX_TABLE: list[tuple[int, int]] = [
    (10_000,   50),
    (30_000,  100),
    (60_000,  150),
    (100_000, 200),
    (150_000, 280),
    (200_000, 380),
    (280_000, 500),
    (380_000, 680),
    (500_000, 900),
    (700_000, 1_200),
    (1_000_000, 1_700),
    (1_500_000, 2_500),
    (2_000_000, 3_300),
    (3_000_000, 5_000),
    (3_911_279, 11_033),  # 상한
]


# ─────────────────────────────────────────────────────────────────────────────
# §1-B  소득 역산 편의 함수
# ─────────────────────────────────────────────────────────────────────────────
def calculate_estimated_income(employee_premium: float) -> dict:
    """
    고객의 본인 부담 건강보험료를 바탕으로 세전/세후 소득을 역산합니다.
    - employee_premium: 고객이 납부하는 월 건보료 (노사 50% 본인 부담분)

    역산 공식 (2026 기준):
      1단계) 본인 납부액 × 2 → 총 건강보험료(100%) 환원
      2단계) 총 건강보험료 ÷ 7.19% → 세전 소득
      3단계) 세전 소득 × (1 - 15.5%) → 세후 가처분 소득

    검증: 250,000원 입력
      → 세전 500,000 / 0.0719 ≈ 6,954,102원
      → 세후 6,954,102 × 0.845 ≈ 5,876,216원
    """
    if employee_premium <= 0:
        return {"gross_income": 0, "net_income": 0}

    # 1단계: 본인 납부액 × 2 → 총 건강보험료 (노사 합산 100%)
    total_premium = employee_premium * 2

    # 2단계: 총 건강보험료 ÷ 총 요율(7.19%) → 세전 소득
    gross_income = total_premium / TOTAL_HEALTH_RATE_2026

    # 3단계: 세전 소득 × (1 - 15.5%) → 세후 가처분 소득
    net_income = gross_income * (1 - AVERAGE_TOTAL_DEDUCTION_RATE)

    return {"gross_income": round(gross_income), "net_income": round(net_income)}


# ─────────────────────────────────────────────────────────────────────────────
# §2  결과 구조체
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class TrinityIncomeData:
    """소득 역산 결과."""
    employment_type:      str            # "직장" | "지역" | "추정"
    nhis_premium_input:   float          # 입력된 건보료 (원, 본인부담)
    monthly_income:       float          # 추정 월 소득 (만원)
    annual_income:        float          # 추정 연봉 (만원)
    disposable_monthly:   float          # 세후 가처분 소득 = 월소득 × (1 - 15.5%) (4대보험+소득세 공제)
    golden_time_fund:     float          # 골든타임 필요 자금 = 월소득 × 24 (만원)
    is_capped:            bool           # 상한/하한 보정 여부
    note:                 str            # 참고 메시지


@dataclass
class TrinityGapResult:
    """소득 공백 분석 결과."""
    golden_time_fund:     float          # 골든타임 필요 자금 (만원)
    kb_cancer_score:      float          # KB 엔진 암 가중 스코어 (만원, 선택)
    kb_total_score:       float          # KB 엔진 전체 스코어 (만원, 선택)
    income_gap:           float          # 생계 파괴 공백 = golden_time - kb_cancer_score
    total_gap:            float          # 전체 공백 = golden_time - kb_total_score
    coverage_ratio:       float          # KB 커버율 (%)
    risk_level:           str            # "위험" | "주의" | "양호"


@dataclass
class TrinityClosingScript:
    """클로징 멘트 4단계."""
    fact:     str
    crisis:   str
    gap:      str
    solution: str


@dataclass
class TrinityReport:
    """트리니티 전체 분석 결과."""
    income:   TrinityIncomeData
    gap:      TrinityGapResult
    closing:  TrinityClosingScript


# ─────────────────────────────────────────────────────────────────────────────
# §3  TrinityValueEngine 클래스
# ─────────────────────────────────────────────────────────────────────────────
class TrinityValueEngine:
    """
    트리니티 경제가치 분석 엔진.

    Parameters
    ----------
    nhis_premium : float
        건강보험료 본인 부담액 (원). 직장: 월급명세서의 건강보험료 항목.
    employment_type : "직장" | "지역"
        가입 유형.
    ltc_included : bool
        입력 금액에 장기요양보험료 포함 여부 (포함 시 자동 분리).
    kb_cancer_score : float
        KB 엔진에서 산출된 암 가중 스코어 (만원). 0이면 비교 생략.
    kb_total_score : float
        KB 엔진 전체 가중 스코어 (만원).
    customer_name : str
        클로징 멘트에 사용할 고객명 (선택).
    """

    def __init__(
        self,
        nhis_premium:     float,
        employment_type:  str   = "직장",
        ltc_included:     bool  = False,
        kb_cancer_score:  float = 0.0,
        kb_total_score:   float = 0.0,
        customer_name:    str   = "고객",
    ):
        self.raw_premium      = float(nhis_premium or 0)
        self.employment_type  = employment_type
        self.ltc_included     = ltc_included
        self.kb_cancer_score  = float(kb_cancer_score or 0)
        self.kb_total_score   = float(kb_total_score  or 0)
        self.customer_name    = customer_name or "고객"

    # ── 공개 메서드 ──────────────────────────────────────────────────────────

    def run_full_analysis(self) -> TrinityReport:
        """3축 전체 분석 실행 → TrinityReport 반환."""
        income  = self._reverse_calculate_income()
        gap     = self._calculate_gap(income)
        closing = self._generate_closing_script(income, gap)
        return TrinityReport(income=income, gap=gap, closing=closing)

    # ── 축 ① 소득 역산 ─────────────────────────────────────────────────────

    def _reverse_calculate_income(self) -> TrinityIncomeData:
        premium = self.raw_premium

        # 장기요양 분리: 입력이 건보료+장기요양 합산이라면 건보료만 추출
        if self.ltc_included and premium > 0:
            # 합산 = 건보료 × (1 + 0.1295)  →  건보료 = 합산 / 1.1295
            premium = premium / (1 + LTC_RATE_ON_NHIS)

        is_capped = False
        note = ""

        if self.employment_type == "직장":
            _inc = calculate_estimated_income(premium)
            monthly_income_raw = float(_inc["gross_income"])   # 세전 소득 (원)
            # 상한 보정
            if monthly_income_raw > MONTHLY_INCOME_MAX:
                monthly_income_raw = MONTHLY_INCOME_MAX
                is_capped = True
                note = f"상한 보정 적용 (월 보수 {MONTHLY_INCOME_MAX/10000:,.0f}만원 상한)"
            # 하한 보정
            elif monthly_income_raw < MONTHLY_INCOME_MIN:
                monthly_income_raw = MONTHLY_INCOME_MIN
                is_capped = True
                note = f"하한 보정 적용 (월 보수 {MONTHLY_INCOME_MIN/10000:,.1f}만원 하한)"

            monthly_income_man = monthly_income_raw / 10_000   # 만원 단위
            emp_type_display = "직장가입자"

        else:
            # 지역가입자: 선형 보간 근사치
            monthly_income_man = _local_approx_income(premium)
            emp_type_display = "지역가입자(추정)"
            note = "지역가입자 점수제 특성상 근사 추정값입니다. 실제 소득과 차이가 있을 수 있습니다."

        annual_income_man    = monthly_income_man * 12
        disposable_monthly   = monthly_income_man * (1 - AVERAGE_TOTAL_DEDUCTION_RATE)   # 세후 가처분 (15.5% 공제)
        golden_time_fund     = disposable_monthly * GOLDEN_TIME_MONTHS

        return TrinityIncomeData(
            employment_type    = emp_type_display,
            nhis_premium_input = premium,
            monthly_income     = round(monthly_income_man, 1),
            annual_income      = round(annual_income_man, 1),
            disposable_monthly = round(disposable_monthly, 1),
            golden_time_fund   = round(golden_time_fund, 1),
            is_capped          = is_capped,
            note               = note,
        )

    # ── 축 ② 소득 대체 공백 ─────────────────────────────────────────────────

    def _calculate_gap(self, income: TrinityIncomeData) -> TrinityGapResult:
        gtf = income.golden_time_fund
        k_cancer = self.kb_cancer_score
        k_total  = self.kb_total_score

        income_gap = gtf - k_cancer   # 암 진단비 기준 공백
        total_gap  = gtf - k_total    # 전체 담보 기준 공백

        # 커버율 (암 기준)
        coverage_ratio = (k_cancer / gtf * 100) if gtf > 0 else 0.0
        coverage_ratio = min(coverage_ratio, 200.0)

        if coverage_ratio >= 80:
            risk_level = "양호"
        elif coverage_ratio >= 50:
            risk_level = "주의"
        else:
            risk_level = "위험"

        return TrinityGapResult(
            golden_time_fund = gtf,
            kb_cancer_score  = k_cancer,
            kb_total_score   = k_total,
            income_gap       = round(income_gap, 1),
            total_gap        = round(total_gap, 1),
            coverage_ratio   = round(coverage_ratio, 1),
            risk_level       = risk_level,
        )

    # ── 축 ③ 심리적 클로징 ──────────────────────────────────────────────────

    def _generate_closing_script(
        self,
        income: TrinityIncomeData,
        gap:    TrinityGapResult,
    ) -> TrinityClosingScript:
        name = self.customer_name
        mo   = income.monthly_income
        ann  = income.annual_income
        disp = income.disposable_monthly
        gtf  = gap.golden_time_fund
        kc   = gap.kb_cancer_score
        ig   = gap.income_gap

        # ── FACT: 차가운 논리
        fact = (
            f"{name}님의 건강보험료 {_w(income.nhis_premium_input/10000)}만원은 "
            f"{name}님이 매월 {_w(mo)}만원(연봉 {_w(ann)}만원)의 경제적 가치를 창출하는 "
            f"핵심 자산임을 증명합니다. "
            f"세후 가처분 소득 기준으로는 월 {_w(disp)}만원입니다."
        )

        # ── CRISIS: 따뜻한 위기
        crisis = (
            f"중대 질병 진단 시 치료·회복에 필요한 24개월 동안, "
            f"{name}님이라는 {_w(gtf)}만원 규모의 경제적 자산은 "
            f"가동을 멈추게 됩니다. "
            f"이것은 단순한 의료비 문제가 아닌 가족 전체의 생존 기반이 흔들리는 위기입니다."
        )

        # ── GAP: 정밀한 타격
        if kc > 0:
            gap_txt = (
                f"현재 보험의 암 진단 가중 보장은 {_w(kc)}만원입니다. "
                f"하지만 소득 대체에 필요한 골든타임 자금 {_w(gtf)}만원과 비교하면 "
                f"{_w(abs(ig))}만원의 생계 파괴 공백이 존재합니다 "
                f"(소득 대체율 {gap.coverage_ratio:.0f}%). "
                f"부족한 것은 보험금이 아니라, 가족의 생활비입니다."
            )
        else:
            gap_txt = (
                f"골든타임 동안 필요한 소득 대체 자금은 {_w(gtf)}만원입니다. "
                f"현재 암 진단 보장 데이터가 없어 정확한 공백 산출을 위해 "
                f"KB 전문 증권분석 엔진과의 연동이 필요합니다."
            )

        # ── SOLUTION: 확신에 찬 대안
        if ig > 0:
            solution = (
                f"가족의 생활을 지키기 위해 {_w(ig)}만원의 추가 준비가 반드시 필요합니다. "
                f"이는 단순 보험 가입이 아니라, "
                f"{name}님의 경제적 존재 가치를 보존하는 전략적 결단입니다. "
                f"KB손해보험 정밀 설계로 이 {GOLDEN_TIME_MONTHS}개월의 소득 공백을 완벽히 메우십시오."
            )
        else:
            solution = (
                f"현재 보장이 골든타임 필요 자금을 충족하고 있습니다. "
                f"다만 물가 상승률과 생활 수준 유지를 위한 재검토를 권장드립니다. "
                f"KB손해보험 전문가와의 정기 점검으로 보장의 완전성을 유지하십시오."
            )

        return TrinityClosingScript(
            fact     = fact,
            crisis   = crisis,
            gap      = gap_txt,
            solution = solution,
        )


# ─────────────────────────────────────────────────────────────────────────────
# §4  헬퍼 함수
# ─────────────────────────────────────────────────────────────────────────────

def _w(val: float) -> str:
    """만원 단위 금액 → 억/만 가독성 포맷."""
    if val >= 10_000:
        ok = int(val) // 10_000
        rem = int(val) % 10_000
        if rem == 0:
            return f"{ok}억"
        return f"{ok}억 {rem:,}만"
    return f"{val:,.0f}만"


def _local_approx_income(premium_won: float) -> float:
    """지역가입자 건보료 → 추정 월소득(만원) 선형 보간."""
    table = _LOCAL_APPROX_TABLE
    if premium_won <= table[0][0]:
        return float(table[0][1])
    if premium_won >= table[-1][0]:
        return float(table[-1][1])
    for i in range(len(table) - 1):
        p0, i0 = table[i]
        p1, i1 = table[i + 1]
        if p0 <= premium_won <= p1:
            ratio = (premium_won - p0) / (p1 - p0)
            return round(i0 + ratio * (i1 - i0), 1)
    return float(table[-1][1])


# ─────────────────────────────────────────────────────────────────────────────
# §5  편의 함수 (one-shot)
# ─────────────────────────────────────────────────────────────────────────────

def run_trinity_analysis(
    nhis_premium:    float,
    employment_type: str   = "직장",
    ltc_included:    bool  = False,
    kb_cancer_score: float = 0.0,
    kb_total_score:  float = 0.0,
    customer_name:   str   = "고객",
) -> TrinityReport:
    """원스톱 트리니티 분석. run_full_analysis()의 래퍼."""
    engine = TrinityValueEngine(
        nhis_premium     = nhis_premium,
        employment_type  = employment_type,
        ltc_included     = ltc_included,
        kb_cancer_score  = kb_cancer_score,
        kb_total_score   = kb_total_score,
        customer_name    = customer_name,
    )
    return engine.run_full_analysis()


def calculate_income_gap(
    nhis_premium:    float,
    kb_cancer_score: float = 0.0,
    kb_total_score:  float = 0.0,
    employment_type: str   = "직장",
) -> TrinityGapResult:
    """KB 엔진 결과와의 소득 공백만 빠르게 산출."""
    engine = TrinityValueEngine(
        nhis_premium    = nhis_premium,
        employment_type = employment_type,
        kb_cancer_score = kb_cancer_score,
        kb_total_score  = kb_total_score,
    )
    income = engine._reverse_calculate_income()
    return engine._calculate_gap(income)


def generate_closing_script(
    nhis_premium:    float,
    kb_cancer_score: float = 0.0,
    kb_total_score:  float = 0.0,
    employment_type: str   = "직장",
    customer_name:   str   = "고객",
) -> TrinityClosingScript:
    """클로징 멘트만 빠르게 생성."""
    rpt = run_trinity_analysis(
        nhis_premium    = nhis_premium,
        employment_type = employment_type,
        kb_cancer_score = kb_cancer_score,
        kb_total_score  = kb_total_score,
        customer_name   = customer_name,
    )
    return rpt.closing
