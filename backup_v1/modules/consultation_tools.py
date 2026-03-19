# -*- coding: utf-8 -*-
"""
modules/consultation_tools.py
────────────────────────────────────────────────────────────────────────────
🎮 N-SECTION 상담 전용 도구 모듈
  - 실시간 플랜 시뮬레이터 (슬라이더 → 차트 실시간 업데이트)
  - 통합 리포트 내보내기 (PDF / 카카오 알림톡)
  - '오늘의 상담 치트키' 카드 (N-SECTION 자동 로드)
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Any

# KB 브랜드 컬러
_KB_NAVY   = "#002D56"
_KB_YELLOW = "#FFCC00"
_KB_LIGHT  = "#F4F4F4"
_KB_ALERT  = "#dc2626"
_KB_OK     = "#16a34a"
_KB_WARN   = "#ca8a04"


# ─────────────────────────────────────────────────────────────────────────────
# §1  실시간 플랜 시뮬레이터 데이터
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SimPlanResult:
    """슬라이더 조정 후 산출된 시뮬레이션 결과."""
    add_cancer:     float   # 추가 암 진단비 (만원)
    add_brain:      float   # 추가 뇌혈관 (만원)
    add_heart:      float   # 추가 심장 (만원)
    add_injury:     float   # 추가 장해 (만원)
    add_surgery:    float   # 추가 수술비 (만원)
    new_kb_total:   float   # 조정 후 KB 총 스코어 (만원)
    new_income_gap: float   # 조정 후 소득 공백 (만원)
    new_coverage_ratio: float  # 조정 후 커버율 (%)
    risk_level:     str
    monthly_premium_increase: float  # 예상 추가 보험료/월 (원, 단순 추정)


def calc_sim_plan(
    golden_time_fund:   float,
    current_kb_cancer:  float,
    add_cancer:         float = 0.0,
    add_brain:          float = 0.0,
    add_heart:          float = 0.0,
    add_injury:         float = 0.0,
    add_surgery:        float = 0.0,
) -> SimPlanResult:
    """슬라이더 값으로 시뮬레이션 결과 산출."""
    total_add    = add_cancer + add_brain + add_heart + add_injury + add_surgery
    new_kb_total = current_kb_cancer + total_add
    new_gap      = golden_time_fund - new_kb_total
    cov_ratio    = (new_kb_total / golden_time_fund * 100) if golden_time_fund > 0 else 0.0
    cov_ratio    = min(cov_ratio, 200.0)
    risk_level   = "양호" if cov_ratio >= 80 else ("주의" if cov_ratio >= 50 else "위험")

    # 보험료 단순 추정: 추가 진단비 100만원당 약 1,500원/월
    monthly_inc = total_add * 10_000 / 1_000_000 * 1_500   # 원

    return SimPlanResult(
        add_cancer              = add_cancer,
        add_brain               = add_brain,
        add_heart               = add_heart,
        add_injury              = add_injury,
        add_surgery             = add_surgery,
        new_kb_total            = round(new_kb_total, 1),
        new_income_gap          = round(new_gap, 1),
        new_coverage_ratio      = round(cov_ratio, 1),
        risk_level              = risk_level,
        monthly_premium_increase = round(monthly_inc, 0),
    )


# ─────────────────────────────────────────────────────────────────────────────
# §2  N-SECTION 브릿지 치트키 카드 (Streamlit HTML)
# ─────────────────────────────────────────────────────────────────────────────

def render_cheat_key_card(bridge: dict) -> str:
    """
    'n_section_bridge' 딕셔너리를 받아 '오늘의 상담 치트키' HTML 카드 반환.
    st.markdown(..., unsafe_allow_html=True)로 렌더링.
    """
    name       = bridge.get("client_name", "고객")
    gap        = bridge.get("total_gap", 0.0)
    ratio      = bridge.get("coverage_ratio", 0.0)
    risk       = bridge.get("risk_level", "N/A")
    alert      = bridge.get("alert_mode", False)
    mo_income  = bridge.get("monthly_income", 0.0)
    ann_income = bridge.get("annual_income", 0.0)
    gtf        = bridge.get("golden_time_fund", 0.0)
    closing    = bridge.get("closing_solution", "")
    kb_grade   = bridge.get("kb_grade", "N/A")

    risk_c = {"위험": _KB_ALERT, "주의": _KB_WARN, "양호": _KB_OK}.get(risk, "#6b7280")
    alert_badge = (
        f'<span style="background:{_KB_YELLOW};color:{_KB_NAVY};font-size:0.62rem;'
        f'font-weight:900;padding:2px 8px;border-radius:4px;margin-left:8px;'
        f'animation:blink 1s step-end infinite;">🚨 긴급: 24개월 소득 공백 위험군</span>'
        if alert else ""
    )

    def _w(v: float) -> str:
        if v >= 10_000:
            ok = int(v) // 10_000
            rem = int(v) % 10_000
            return f"{ok}억 {rem:,}만" if rem else f"{ok}억"
        return f"{v:,.0f}만"

    return f"""
<style>
@keyframes blink {{
  0%,100% {{ opacity:1; }} 50% {{ opacity:0.3; }}
}}
@keyframes glow {{
  0%,100% {{ box-shadow:0 0 8px 3px {_KB_YELLOW}66; }}
  50%      {{ box-shadow:0 0 18px 6px {_KB_YELLOW}cc; }}
}}
.tri-alert {{ animation: glow 1.8s ease-in-out infinite; }}
</style>
<div class="{'tri-alert' if alert else ''}" style="background:{_KB_NAVY};border-radius:12px;
     padding:14px 18px;border-left:6px solid {_KB_YELLOW};margin-bottom:12px;">
  <div style="display:flex;align-items:center;margin-bottom:8px;">
    <span style="color:{_KB_YELLOW};font-size:0.82rem;font-weight:900;letter-spacing:0.08em;">
      🎯 오늘의 상담 치트키 — {name}님
    </span>
    {alert_badge}
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:20px;margin-bottom:10px;">
    <div style="text-align:center;">
      <div style="color:#8ca9be;font-size:0.62rem;">월 경제가치</div>
      <div style="color:{_KB_YELLOW};font-size:1.1rem;font-weight:900;">{_w(mo_income)}만</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#8ca9be;font-size:0.62rem;">골든타임 필요자금</div>
      <div style="color:#fff;font-size:1.1rem;font-weight:900;">{_w(gtf)}만</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#8ca9be;font-size:0.62rem;">생계 파괴 공백</div>
      <div style="color:{_KB_ALERT};font-size:1.2rem;font-weight:900;">{_w(abs(gap))}만</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#8ca9be;font-size:0.62rem;">소득 대체율</div>
      <div style="background:{risk_c};color:#fff;font-size:0.85rem;font-weight:900;
                  padding:3px 10px;border-radius:5px;">{ratio:.0f}% ({risk})</div>
    </div>
    <div style="text-align:center;">
      <div style="color:#8ca9be;font-size:0.62rem;">KB 보장 등급</div>
      <div style="color:{_KB_YELLOW};font-size:1.1rem;font-weight:900;">{kb_grade}등급</div>
    </div>
  </div>
  {f'<div style="background:#0d1f35;border-radius:6px;padding:8px 10px;font-size:0.72rem;color:#e2e8f0;line-height:1.7;border-left:3px solid {_KB_YELLOW};"><b style="color:{_KB_YELLOW};">💬 핵심 멘트:</b> {closing}</div>' if closing else ''}
</div>
"""


# ─────────────────────────────────────────────────────────────────────────────
# §3  리포트 텍스트 내보내기 (PDF 생성은 앱 레이어에서 처리)
# ─────────────────────────────────────────────────────────────────────────────

def build_report_text(bridge: dict) -> str:
    """통합 리포트 텍스트 생성 (PDF/카카오 알림톡 공통 베이스)."""
    name  = bridge.get("client_name", "고객")
    gap   = bridge.get("total_gap", 0.0)
    gtf   = bridge.get("golden_time_fund", 0.0)
    ratio = bridge.get("coverage_ratio", 0.0)
    risk  = bridge.get("risk_level", "N/A")
    ann   = bridge.get("annual_income", 0.0)

    def _w(v):
        if v >= 10_000:
            ok = int(v) // 10_000
            rem = int(v) % 10_000
            return f"{ok}억 {rem:,}만" if rem else f"{ok}억"
        return f"{v:,.0f}만"

    cats = bridge.get("kb_categories", [])
    cat_lines = "\n".join(
        f"  [{c['category']}] {c['status']} — 스코어 {c['weighted_score']:,.0f}만 / 권장 {c['benchmark']:,.0f}만"
        for c in cats
    )

    return (
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ 통합 증권 갭 분석 리포트\n"
        f"대상: {name}님  |  추정 연봉: {_w(ann)}만\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[트리니티 골든타임 필요자금] {_w(gtf)}만\n"
        f"[KB 보장 커버율] {ratio:.1f}% ({risk})\n"
        f"[생계 파괴 공백] {_w(abs(gap))}만\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[KB 7대 보장 분류 현황]\n{cat_lines}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"[핵심 클로징]\n{bridge.get('closing_solution','')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Powered by Goldkey AI Masters 2026\n"
    )
