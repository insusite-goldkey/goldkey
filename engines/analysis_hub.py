# -*- coding: utf-8 -*-
"""
engines/analysis_hub.py
────────────────────────────────────────────────────────────────────────────
🏛️ 통합 증권 갭 분석 시스템 (Unified Insurance Gap Analysis System)
   중앙 사령부 오케스트레이터 — KB 엔진 + 트리니티 엔진 결합

데이터 흐름:
  raw_data (내보험다보여 JSON / 직접 입력)
      ↓
  analysis_hub.run_unified_analysis()
      ├─→ kb_scoring_system.run_kb_analysis()     → KBReport
      └─→ trinity_value_engine.run_trinity_analysis() → TrinityReport
             ↓
  UnifiedReport  (Gap = TrinityGoldenFund - KBCancerScore)
      ↓
  st.session_state.integrated_report
  st.session_state.n_section_bridge      ← N-SECTION 자동 전송
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

from engines.kb_scoring_system import run_kb_analysis, KBReport
from engines.trinity_value_engine import run_trinity_analysis, TrinityReport, _w
from engines.surgery_classifier import (
    classify_surgery_coverages_bulk,
    map_to_kb_categories_bulk,
    analyze_surgery_gap,
)


# ─────────────────────────────────────────────────────────────────────────────
# §1  통합 결과 구조체
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class UnifiedGapResult:
    """실질 생계 파괴 공백."""
    golden_time_fund:   float   # 트리니티: 필요 자금 (만원)
    kb_cancer_score:    float   # KB: 암 가중 스코어 (만원)
    kb_total_score:     float   # KB: 전체 가중 스코어 (만원)
    income_gap:         float   # 생계 파괴 공백 = golden - kb_cancer (만원)
    total_gap:          float   # 전체 공백 = golden - kb_total (만원)
    coverage_ratio:     float   # 커버율 (%)
    risk_level:         str     # "위험" | "주의" | "양호"
    alert_mode:         bool    # 강력 경고 모드 (gap > 50% 이상 또는 공백 1억+)


@dataclass
class UnifiedReport:
    """통합 증권 갭 분석 최종 보고서."""
    kb:        Optional[KBReport]      = None
    trinity:   Optional[TrinityReport] = None
    gap:       Optional[UnifiedGapResult] = None
    surgery_gap: Optional[dict]        = None  # 수술비 Gap 분석 (질병 vs 상해)
    client_name: str = "고객"
    ok:        bool  = False
    errors:    list  = field(default_factory=list)

    # N-SECTION 브릿지 패킷 생성
    def to_bridge_packet(self) -> dict:
        """N-SECTION 자동 전송용 딕셔너리."""
        if not self.ok:
            return {}
        cs = self.trinity.closing if self.trinity else None
        gap = self.gap
        return {
            "client_name":     self.client_name,
            "total_gap":       gap.income_gap   if gap else 0.0,
            "coverage_ratio":  gap.coverage_ratio if gap else 0.0,
            "risk_level":      gap.risk_level   if gap else "N/A",
            "alert_mode":      gap.alert_mode   if gap else False,
            "golden_time_fund": gap.golden_time_fund if gap else 0.0,
            "kb_cancer_score":  gap.kb_cancer_score  if gap else 0.0,
            "kb_total_score":   gap.kb_total_score   if gap else 0.0,
            "kb_grade":        self.kb.grade     if self.kb else "N/A",
            "kb_total_score_val": self.kb.total_score if self.kb else 0.0,
            "monthly_income":  self.trinity.income.monthly_income if self.trinity else 0.0,
            "annual_income":   self.trinity.income.annual_income  if self.trinity else 0.0,
            "closing_fact":    cs.fact     if cs else "",
            "closing_crisis":  cs.crisis   if cs else "",
            "closing_gap":     cs.gap      if cs else "",
            "closing_solution": cs.solution if cs else "",
            "kb_categories":   [
                {
                    "category": c.category,
                    "status":   c.status,
                    "weighted_score": c.weighted_score,
                    "benchmark":      c.benchmark,
                    "gap":            c.gap,
                }
                for c in (self.kb.categories if self.kb else [])
            ],
        }


# ─────────────────────────────────────────────────────────────────────────────
# §2  중앙 사령부 (AnalysisHub)
# ─────────────────────────────────────────────────────────────────────────────
class AnalysisHub:
    """
    KB 엔진 + 트리니티 엔진을 동시 구동하고 통합 Gap을 산출하는 오케스트레이터.

    Parameters
    ----------
    coverages : list[dict]
        [{"name": "암진단비", "amount": 3000}, ...] 형태의 담보 목록.
    nhis_premium : float
        건강보험료 본인 부담액 (원).
    age : int
        고객 나이.
    gender : "남" | "여"
    employment_type : "직장" | "지역"
    ltc_included : bool
        건보료에 장기요양 포함 여부.
    customer_name : str
    """

    def __init__(
        self,
        coverages:        list,
        nhis_premium:     float,
        age:              int   = 40,
        gender:           str   = "남",
        employment_type:  str   = "직장",
        ltc_included:     bool  = False,
        customer_name:    str   = "고객",
    ):
        self.coverages       = coverages or []
        self.nhis_premium    = float(nhis_premium or 0)
        self.age             = int(age or 40)
        self.gender          = gender
        self.employment_type = employment_type
        self.ltc_included    = ltc_included
        self.customer_name   = customer_name

    def run(self) -> UnifiedReport:
        """전체 분석 실행 → UnifiedReport 반환."""
        report = UnifiedReport(client_name=self.customer_name)
        errors = []

        # ── [신규] 수술비 전처리: 질병 vs 상해 분류 ──────────────────────
        surgery_classifications = []
        try:
            # 수술비 담보 자동 분류 및 메타데이터 추가
            surgery_classifications = classify_surgery_coverages_bulk(
                self.coverages, use_llm=True
            )
            
            # 분류 결과를 coverages에 메타데이터로 추가
            if surgery_classifications:
                surgery_map = {
                    c.original_name: c for c in surgery_classifications
                }
                for cov in self.coverages:
                    if cov.get("name") in surgery_map:
                        classification = surgery_map[cov["name"]]
                        cov["surgery_type"] = classification.surgery_type
                        cov["surgery_confidence"] = classification.confidence
                        cov["surgery_display_name"] = classification.display_name
                        cov["kb_category"] = "③ 수술/입원비"
                
                # Gap 분석 실행 (우측 분석창용)
                report.surgery_gap = analyze_surgery_gap(
                    surgery_classifications,
                    benchmark_disease=700,  # 연령별 벤치마크는 추후 동적 설정
                    benchmark_injury=500,
                )
        except Exception as e:
            errors.append(f"수술비분류: {e}")

        # ── KB 엔진 실행 ────────────────────────────────────────────────
        try:
            kb_rpt = run_kb_analysis(
                coverages = self.coverages,
                age       = self.age,
                gender    = self.gender,
            )
            report.kb = kb_rpt
        except Exception as e:
            errors.append(f"KB엔진: {e}")

        # ── 트리니티 엔진 실행 ──────────────────────────────────────────
        tri_rpt = None
        try:
            # KB 암 스코어 연동
            kb_cancer = 0.0
            kb_total  = 0.0
            if report.kb:
                kb_cancer = sum(
                    c.weighted_score for c in report.kb.categories if "암" in c.category
                )
                kb_total = report.kb.total_score

            tri_rpt = run_trinity_analysis(
                nhis_premium    = self.nhis_premium,
                employment_type = self.employment_type,
                ltc_included    = self.ltc_included,
                kb_cancer_score = kb_cancer,
                kb_total_score  = kb_total,
                customer_name   = self.customer_name,
            )
            report.trinity = tri_rpt
        except Exception as e:
            errors.append(f"트리니티: {e}")

        # ── 통합 Gap 계산 ────────────────────────────────────────────────
        try:
            report.gap = self._calc_unified_gap(report.kb, tri_rpt)
        except Exception as e:
            errors.append(f"Gap계산: {e}")

        report.errors = errors
        report.ok = len(errors) == 0 or (report.kb is not None or tri_rpt is not None)
        return report

    def _calc_unified_gap(
        self,
        kb:  Optional[KBReport],
        tri: Optional[TrinityReport],
    ) -> UnifiedGapResult:
        gtf     = tri.gap.golden_time_fund if tri else 0.0
        k_cancer = tri.gap.kb_cancer_score  if tri else 0.0
        k_total  = tri.gap.kb_total_score   if tri else 0.0

        # KB에서 직접 뽑기 (더 정밀)
        if kb:
            k_cancer = sum(c.weighted_score for c in kb.categories if "암" in c.category)
            k_total  = kb.total_score

        income_gap     = gtf - k_cancer
        total_gap      = gtf - k_total
        coverage_ratio = (k_cancer / gtf * 100) if gtf > 0 else 0.0
        coverage_ratio = min(coverage_ratio, 200.0)

        risk_level = "양호" if coverage_ratio >= 80 else ("주의" if coverage_ratio >= 50 else "위험")

        # 강력 경고 모드: Gap > 50% 이상 or 공백 1억원 이상
        alert_mode = (coverage_ratio < 50) or (income_gap >= 10_000)

        return UnifiedGapResult(
            golden_time_fund = round(gtf, 1),
            kb_cancer_score  = round(k_cancer, 1),
            kb_total_score   = round(k_total, 1),
            income_gap       = round(income_gap, 1),
            total_gap        = round(total_gap, 1),
            coverage_ratio   = round(coverage_ratio, 1),
            risk_level       = risk_level,
            alert_mode       = alert_mode,
        )


# ─────────────────────────────────────────────────────────────────────────────
# §3  세션 관리 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def clear_analysis_session(ss: Any) -> None:
    """분석 시작 전 이전 결과 완전 소거."""
    for key in ("integrated_report", "n_section_bridge", "_tri_report", "_kb_report",
                "_tri_ai_closing", "_kb_ai_summary", "temp_plan"):
        ss.pop(key, None)


def run_unified_analysis(
    coverages:       list,
    nhis_premium:    float,
    age:             int  = 40,
    gender:          str  = "남",
    employment_type: str  = "직장",
    ltc_included:    bool = False,
    customer_name:   str  = "고객",
    session_state:   Any  = None,
) -> UnifiedReport:
    """
    원스톱 통합 분석 + 세션 자동 저장.
    session_state 전달 시 integrated_report / n_section_bridge 자동 저장.
    """
    hub = AnalysisHub(
        coverages       = coverages,
        nhis_premium    = nhis_premium,
        age             = age,
        gender          = gender,
        employment_type = employment_type,
        ltc_included    = ltc_included,
        customer_name   = customer_name,
    )
    report = hub.run()

    if session_state is not None and report.ok:
        session_state["integrated_report"] = report
        session_state["n_section_bridge"]  = report.to_bridge_packet()
        # KB / Trinity 개별 세션에도 저장 (각 독립 파트 호환)
        if report.kb:
            session_state["_kb_report"] = report.kb
        if report.trinity:
            session_state["_tri_report"] = report.trinity

    return report
