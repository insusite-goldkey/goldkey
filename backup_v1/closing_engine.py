# closing_engine.py — Goldkey AI Masters 2026
"""
[AI 필살 클로징 생성 엔진]
트리니티 분석 결과 → FCS(Fact-Crisis-Solution) 3단계 설득 스크립트 자동 생성.

exports:
  generate_killer_closing() — 맞춤형 클로징 스크립트 반환 (str)
"""
from __future__ import annotations

# ── 담보별 치료 기간 메타 ────────────────────────────────────────────────────
_ITEM_PERIOD_MAP: dict[str, tuple[int, str]] = {
    "암진단비":       (24, "최소 2년"),
    "뇌졸중진단비":   (24, "1년 6개월 ~ 2년"),
    "심근경색진단비": (18, "1년 ~ 1년 6개월"),
    "상해후유장해":   (0,  "영구 장해 보정"),
    "실손의료비":     (0,  "실비 청구 필수"),
    "수술비":         (3,  "1회 수술 기준"),
    "입원일당":       (0,  "일당 기준"),
    "사망보험금":     (0,  "가족 생활 보전"),
    "치매진단비":     (0,  "장기 요양 기준"),
}

# ── 항목별 특수 전술 멘트 ────────────────────────────────────────────────────
_SPECIAL_TACTICS: dict[str, str] = {
    "상해후유장해": (
        "1억 들었다고 좋아하실 게 아닙니다. "
        "10% 장해 입으면 고작 1,000만 원 나옵니다. "
        "휠체어 리프트 하나 다는 비용도 안 됩니다. "
        "그래서 제가 5억을 제안하는 겁니다."
    ),
    "치매진단비": (
        "치매는 본인이 아닌 '가족이 쓰러지는 병'입니다. "
        "요양병원 월 100만 원, 10년이면 1억 2천만 원. "
        "지금 준비 안 하면 자녀가 그 부담을 고스란히 집니다."
    ),
    "실손의료비": (
        "실손만 있으면 된다고 생각하시는 분들이 많습니다. "
        "하지만 실손은 '치료비'만 채워줄 뿐, "
        "투병 중 빠져나가는 월급은 한 푼도 보상하지 않습니다."
    ),
}


def generate_killer_closing(
    analysis_result: dict,
    estimated_income: float,
    client_name: str = "고객",
) -> str:
    """
    트리니티 분석 결과를 기반으로 FCS 3단계 맞춤형 설득 스크립트 생성.

    Args:
        analysis_result:  run_trinity_analysis() 반환 dict
        estimated_income: 추정 월소득(원) — 건보료 역산값
        client_name:      고객명

    Returns:
        str — 마크다운 형식의 클로징 스크립트
    """
    # 1. Gap이 가장 큰 항목 탐색 (메타 키 제외)
    max_gap_item     = "암진단비"
    max_gap_val      = 0.0
    max_gap_adequate = 0.0
    max_gap_current  = 0.0

    for k, v in analysis_result.items():
        if str(k).startswith("_"):
            continue
        gap = float(v.get("부족분", 0) or 0)
        if gap > max_gap_val:
            max_gap_val      = gap
            max_gap_item     = k
            max_gap_adequate = float(v.get("적정_역산", 0) or 0)
            max_gap_current  = float(v.get("현재가입",  0) or 0)

    # 2. 해당 항목 치료 기간
    _period_mo, _period_str = _ITEM_PERIOD_MAP.get(max_gap_item, (24, "최소 2년"))

    income_str = f"{estimated_income:,.0f}"
    gap_str    = f"{max_gap_val:,.0f}"
    ade_str    = f"{max_gap_adequate:,.0f}"
    cur_str    = f"{max_gap_current:,.0f}"

    # 3. 특수 전술 (항목별 추가 멘트)
    _special_block = ""
    if max_gap_item in _SPECIAL_TACTICS:
        _special_block = (
            f"\n> ⚠️ *\"{_SPECIAL_TACTICS[max_gap_item]}\"*\n"
        )

    # 4. FCS 스크립트 조립
    script = f"""**[🎯 AI 마스터의 필살 클로징 스크립트]**

---

**1. 도입: 안심과 확인 (The Fact)**
> *"{client_name}님, 지금 가입하신 보험을 보니 업계 평균 정도는 준비를 잘 하셨습니다. {max_gap_item} 현재 {cur_str}원 — 남들 하는 만큼은 하신 거죠. 하지만..."*

---

**2. 위기: 실질 소득 공백 타격 (The Crisis)**
> *"{max_gap_item}은 단순한 치료비 문제가 아닙니다. 통계적으로 완치까지 **'{_period_str}'**이 걸리는데, {client_name}님의 월 소득 **{income_str}원**을 기준으로 보면 그 기간 동안 약 **{gap_str}원**의 소득이 증발하게 됩니다.*
>
> *지금 가진 보험금으로는 치료비 내고 나면 가족들 생활비는 6개월도 버티기 힘듭니다."*
{_special_block}
---

**3. 해결: 생존의 가치 제안 (The Solution)**
> *"보험은 '남들만큼' 드는 게 아니라 **'내 삶의 규모'**만큼 들어야 합니다.*
>
> *{max_gap_item} 적정액 **{ade_str}원** — 부족한 **{gap_str}원**만 채워두시면, 투병 기간 중에도 가족들의 삶은 무너지지 않습니다. 저라면 오늘 이 '생존 자금'부터 확정 짓겠습니다."*

---

🔑 **[건보료 역산의 권위]**
> *"제가 계산한 게 아니라, 국가에 내시는 건보료가 증명하는 {client_name}님의 '삶의 가치'입니다. 월 소득 {income_str}원이 곧 {client_name}님 가족의 생활 기반입니다."*

📅 **[치료 기간의 구체성]**
> *"암 2년, 뇌졸중 2년 — 이 숫자는 의학 통계입니다. 그 기간 동안 {client_name}님의 통장에 매달 {income_str}원이 들어와야 가족이 버팁니다."*"""

    return script.strip()
