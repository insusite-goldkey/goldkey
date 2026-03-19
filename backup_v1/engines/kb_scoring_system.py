# -*- coding: utf-8 -*-
"""
engines/kb_scoring_system.py
────────────────────────────────────────────────────────────────────────────
KB손해보험 전문 증권분석 엔진 — 제3장: 전문가용 스코어링 & 벤치마킹
가중치 공식:  Score = Σ (Coverage_Amount × Scope_Weight)
Gap 공식:     Gap = KB_Benchmark - Score
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from engines.kb_policy_mapper import (
    CAT_CANCER_GEN, CAT_CANCER_HIGH, CAT_CANCER_SMALL, CAT_CANCER_TREAT,
    CAT_BRAIN_BROAD, CAT_BRAIN_MID, CAT_BRAIN_NARROW,
    CAT_HEART_BROAD, CAT_HEART_NARROW,
    CAT_INJURY_DIS, CAT_DISEASE_DIS,
    CAT_DRIVER_PROC, CAT_DRIVER_FINE, CAT_DRIVER_AGREE,
    CAT_SURGERY, CAT_HOSP_DAILY, CAT_LIABILITY, CAT_SILSON,
    CAT_DEATH, CAT_DEATH_ACC, CAT_DEMENTIA, CAT_OTHER,
    SCOPE_WEIGHT, map_coverages_bulk,
)

# ─────────────────────────────────────────────────────────────────────────────
# §1  KB 표준 벤치마크 (연령대·성별별 권장 보장액, 단위: 만원)
#     출처: KB손해보험 대리점 표준 설계 가이드라인 + 업계 실무
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class KBBenchmark:
    cancer_gen:   float  # 일반암진단비
    cancer_high:  float  # 고액암진단비
    cancer_small: float  # 소액암진단비
    brain_score:  float  # 뇌혈관 통합 스코어 (가중 적용 후)
    heart_score:  float  # 심장 통합 스코어
    injury_dis:   float  # 상해후유장해
    driver_proc:  float  # 교통사고처리지원금
    death:        float  # 사망
    silson:       float  # 실손의료비 (1=가입필수 기준)
    surgery:      float  # 수술비
    hosp_daily:   float  # 입원일당 (일 기준)


# 연령대·성별 → KBBenchmark
KB_BENCHMARKS: dict[str, KBBenchmark] = {
    # 30대 남성
    "30M": KBBenchmark(
        cancer_gen=5000, cancer_high=10000, cancer_small=500,
        brain_score=3000, heart_score=2000,
        injury_dis=10000, driver_proc=20000,
        death=30000, silson=1, surgery=500, hosp_daily=10,
    ),
    # 30대 여성
    "30F": KBBenchmark(
        cancer_gen=5000, cancer_high=8000, cancer_small=500,
        brain_score=2500, heart_score=1500,
        injury_dis=8000, driver_proc=15000,
        death=20000, silson=1, surgery=500, hosp_daily=10,
    ),
    # 40대 남성
    "40M": KBBenchmark(
        cancer_gen=6000, cancer_high=15000, cancer_small=500,
        brain_score=4000, heart_score=3000,
        injury_dis=10000, driver_proc=20000,
        death=30000, silson=1, surgery=700, hosp_daily=10,
    ),
    # 40대 여성
    "40F": KBBenchmark(
        cancer_gen=6000, cancer_high=10000, cancer_small=500,
        brain_score=3000, heart_score=2000,
        injury_dis=8000, driver_proc=15000,
        death=20000, silson=1, surgery=700, hosp_daily=10,
    ),
    # 50대 남성
    "50M": KBBenchmark(
        cancer_gen=7000, cancer_high=20000, cancer_small=500,
        brain_score=5000, heart_score=4000,
        injury_dis=10000, driver_proc=20000,
        death=30000, silson=1, surgery=1000, hosp_daily=15,
    ),
    # 50대 여성
    "50F": KBBenchmark(
        cancer_gen=7000, cancer_high=15000, cancer_small=500,
        brain_score=4000, heart_score=3000,
        injury_dis=8000, driver_proc=15000,
        death=20000, silson=1, surgery=1000, hosp_daily=15,
    ),
    # 60대 남성
    "60M": KBBenchmark(
        cancer_gen=5000, cancer_high=15000, cancer_small=300,
        brain_score=5000, heart_score=4000,
        injury_dis=8000, driver_proc=15000,
        death=20000, silson=1, surgery=1000, hosp_daily=15,
    ),
    # 60대 여성
    "60F": KBBenchmark(
        cancer_gen=5000, cancer_high=10000, cancer_small=300,
        brain_score=4000, heart_score=3000,
        injury_dis=6000, driver_proc=10000,
        death=15000, silson=1, surgery=1000, hosp_daily=15,
    ),
    # 기본 (연령 미상)
    "DEF": KBBenchmark(
        cancer_gen=5000, cancer_high=10000, cancer_small=500,
        brain_score=3000, heart_score=2000,
        injury_dis=10000, driver_proc=20000,
        death=30000, silson=1, surgery=500, hosp_daily=10,
    ),
}


def get_benchmark(age: Optional[int], gender: str) -> KBBenchmark:
    """연령·성별 → KB 벤치마크 반환. 미상 시 기본값."""
    g = "M" if str(gender).upper() in ("M", "남", "남성", "MALE") else "F"
    if age is None:
        return KB_BENCHMARKS["DEF"]
    decade = (age // 10) * 10
    decade = max(30, min(decade, 60))
    key = f"{decade}{g}"
    return KB_BENCHMARKS.get(key, KB_BENCHMARKS["DEF"])


# ─────────────────────────────────────────────────────────────────────────────
# §2  스코어링 결과 구조체
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class CategoryScore:
    category:     str
    total_amount: float          # 가입 금액 합계 (만원)
    weighted_score: float        # Σ(amount × scope_weight)
    benchmark:    float          # KB 권장 기준
    gap:          float          # benchmark - weighted_score
    status:       str            # "충분" | "부족" | "미가입" | "초과"
    coverages:    list[dict] = field(default_factory=list)


@dataclass
class KBScoreReport:
    categories:       list[CategoryScore]
    total_score:      float
    total_benchmark:  float
    overall_gap:      float
    overall_pct:      float          # 달성률 (%)
    grade:            str            # S/A/B/C/D
    summary:          str
    recommendations:  list[str]
    radar_data:       dict           # 레이더 차트용


# ─────────────────────────────────────────────────────────────────────────────
# §3  스코어링 엔진
# ─────────────────────────────────────────────────────────────────────────────

def _determine_status(weighted: float, benchmark: float) -> str:
    if benchmark == 0:
        return "해당없음"
    ratio = weighted / benchmark
    if ratio >= 1.0:
        return "충분"
    elif ratio >= 0.7:
        return "부족"
    elif ratio > 0:
        return "부족"
    else:
        return "미가입"


def _grade(pct: float) -> str:
    if pct >= 90:   return "S"
    elif pct >= 75: return "A"
    elif pct >= 55: return "B"
    elif pct >= 35: return "C"
    else:           return "D"


def _generate_summary(cats: list[CategoryScore], grade: str, pct: float) -> str:
    issues = [c for c in cats if c.status in ("부족", "미가입")]
    ok     = [c for c in cats if c.status == "충분"]
    lines  = [f"KB 표준 대비 보장 달성률 {pct:.0f}% (등급: {grade})."]
    if ok:
        lines.append("충분 항목: " + ", ".join(c.category for c in ok[:3]) + ".")
    if issues:
        top = sorted(issues, key=lambda x: abs(x.gap), reverse=True)[:3]
        lines.append(
            "공백 주요 항목: "
            + ", ".join(
                f"{c.category} ({'+' if c.gap >= 0 else ''}{c.gap:,.0f}만원 차이)"
                for c in top
            ) + "."
        )
    return " ".join(lines)


def _generate_recommendations(cats: list[CategoryScore]) -> list[str]:
    recs = []
    for c in sorted(cats, key=lambda x: abs(x.gap), reverse=True):
        if c.status == "미가입":
            recs.append(f"[긴급] {c.category} — 미가입 상태. KB 권장 {c.benchmark:,.0f}만원 신규 가입 필요.")
        elif c.status == "부족":
            recs.append(f"[보완] {c.category} — KB 표준 대비 {c.gap:,.0f}만원 부족. 증액 검토 요망.")
        if len(recs) >= 5:
            break
    if not recs:
        recs.append("전 영역 KB 표준 충족. 갱신형→비갱신형 전환 및 실손 세대 점검 권장.")
    return recs


# 분석 대상 카테고리와 벤치마크 필드 매핑
_CAT_BENCHMARK_MAP: list[tuple[str, str, list[str]]] = [
    # (표시 카테고리명, KBBenchmark 필드명, [매핑 카테고리 목록])
    ("암_일반암",         "cancer_gen",   [CAT_CANCER_GEN]),
    ("암_고액암",         "cancer_high",  [CAT_CANCER_HIGH]),
    ("암_소액유사암",     "cancer_small", [CAT_CANCER_SMALL]),
    ("뇌혈관(가중스코어)", "brain_score",  [CAT_BRAIN_BROAD, CAT_BRAIN_MID, CAT_BRAIN_NARROW]),
    ("심장(가중스코어)",   "heart_score",  [CAT_HEART_BROAD, CAT_HEART_NARROW]),
    ("상해후유장해",       "injury_dis",   [CAT_INJURY_DIS, CAT_DISEASE_DIS]),
    ("교통사고처리지원금", "driver_proc",  [CAT_DRIVER_PROC]),
    ("사망",              "death",        [CAT_DEATH, CAT_DEATH_ACC]),
    ("수술비",            "surgery",      [CAT_SURGERY]),
    ("입원일당",          "hosp_daily",   [CAT_HOSP_DAILY]),
]


def calculate_kb_score(
    mapped_coverages: list[dict],
    age: Optional[int] = None,
    gender: str = "M",
) -> KBScoreReport:
    """
    mapped_coverages: map_coverages_bulk() 결과
    반환: KBScoreReport
    """
    bench = get_benchmark(age, gender)
    cat_scores: list[CategoryScore] = []

    for display_cat, bench_field, cat_keys in _CAT_BENCHMARK_MAP:
        relevant = [c for c in mapped_coverages if c["category"] in cat_keys]
        total_amt     = sum(c["amount"] for c in relevant)
        weighted_sum  = sum(c["amount"] * c["scope_weight"] for c in relevant)
        bm_val        = getattr(bench, bench_field, 0) or 0
        gap           = bm_val - weighted_sum
        status        = _determine_status(weighted_sum, bm_val)
        cat_scores.append(CategoryScore(
            category      = display_cat,
            total_amount  = total_amt,
            weighted_score= weighted_sum,
            benchmark     = bm_val,
            gap           = gap,
            status        = status,
            coverages     = relevant,
        ))

    total_ws  = sum(c.weighted_score for c in cat_scores)
    total_bm  = sum(c.benchmark      for c in cat_scores)
    overall_gap = total_bm - total_ws
    pct = (total_ws / total_bm * 100) if total_bm > 0 else 0.0
    grade = _grade(pct)
    summary = _generate_summary(cat_scores, grade, pct)
    recs    = _generate_recommendations(cat_scores)

    # 레이더 차트 데이터
    radar_labels = [c.category for c in cat_scores]
    radar_actual = [round(min(c.weighted_score / c.benchmark * 100, 150), 1)
                    if c.benchmark > 0 else 0
                    for c in cat_scores]
    radar_bench  = [100.0] * len(cat_scores)

    return KBScoreReport(
        categories      = cat_scores,
        total_score     = total_ws,
        total_benchmark = total_bm,
        overall_gap     = overall_gap,
        overall_pct     = round(pct, 1),
        grade           = grade,
        summary         = summary,
        recommendations = recs,
        radar_data      = {
            "labels":  radar_labels,
            "actual":  radar_actual,
            "bench":   radar_bench,
        },
    )


def run_kb_analysis(
    raw_items: list[dict],
    age: Optional[int] = None,
    gender: str = "M",
) -> KBScoreReport:
    """
    one-shot: raw_items → map → score → report
    raw_items: [{"name": str, "amount": float/str}, ...]
    """
    # 금액 정규화
    import re as _re
    def _parse_amount(v) -> float:
        if v is None:
            return 0.0
        s = str(v).replace(",", "").replace(" ", "")
        m = _re.search(r"(\d+(?:\.\d+)?)\s*(억|만|천)?", s)
        if not m:
            return 0.0
        num = float(m.group(1))
        unit = m.group(2) or ""
        if unit == "억":   return num * 10000
        elif unit == "만": return num
        elif unit == "천": return num / 10
        else:
            if num >= 1_000_000: return num / 10000  # 원 단위
            return num
    normalized = [{"name": it.get("name",""), "amount": _parse_amount(it.get("amount",0))} for it in raw_items]
    mapped = map_coverages_bulk(normalized)
    return calculate_kb_score(mapped, age=age, gender=gender)
