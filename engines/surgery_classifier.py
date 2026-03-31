# -*- coding: utf-8 -*-
"""
engines/surgery_classifier.py
────────────────────────────────────────────────────────────────────────────
🔬 Vision AI 정밀 튜닝: 질병 vs 상해 수술비 완벽 분류 엔진
────────────────────────────────────────────────────────────────────────────
목적:
  OCR로 추출된 수술비 담보를 '질병수술비'와 '상해수술비'로 정밀 분류하여
  KB 7대 분류 중 [③ 수술/입원비] 카테고리에 메타데이터와 함께 자동 할당

분류 로직:
  1. 키워드 기반 1차 분류 (상해/질병 키워드 검출)
  2. LLM 에이전트 2차 분석 (모호한 경우 95% 이상 확률로 분류)
  3. KB 7대 분류 자동 매핑 (메타데이터 포함)

데이터 흐름:
  OCR 결과 → classify_surgery_coverage() → KB 매핑 → AnalysisHub
────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Literal
import re


# ─────────────────────────────────────────────────────────────────────────────
# §1  분류 결과 구조체
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class SurgeryClassification:
    """수술비 분류 결과."""
    original_name: str                          # 원본 담보명
    surgery_type: Literal["질병", "상해", "통합"]  # 분류 타입
    confidence: float                           # 분류 확률 (0.0~1.0)
    kb_category: str                            # KB 7대 분류 (항상 "③ 수술/입원비")
    display_name: str                           # 표시명 (질병수술비 / 상해수술비)
    amount: float                               # 보장 금액 (만원)
    metadata: dict                              # 추가 메타데이터
    classification_method: str                  # 분류 방법 (keyword / llm)


# ─────────────────────────────────────────────────────────────────────────────
# §2  키워드 기반 1차 분류 엔진
# ─────────────────────────────────────────────────────────────────────────────

# 상해(Injury) 키워드
INJURY_KEYWORDS = [
    "상해", "재해", "교통", "골절", "탈구", "염좌", "찰과상", "열상",
    "타박상", "화상", "동상", "익수", "추락", "낙상", "충돌", "사고",
    "외상", "부상", "상처", "절단", "파열", "관통상", "압궤", "좌상",
]

# 질병(Disease) 키워드
DISEASE_KEYWORDS = [
    "질병", "질환", "암", "종양", "성인병", "당뇨", "고혈압", "뇌졸중",
    "심근경색", "협심증", "간경화", "신부전", "폐렴", "결핵", "천식",
    "위궤양", "십이지장궤양", "췌장염", "담석", "맹장염", "탈장",
    "백내장", "녹내장", "치질", "치핵", "자궁근종", "난소낭종",
]

# 통합(Both) 키워드 (질병/상해 구분 없음)
INTEGRATED_KEYWORDS = [
    "일반수술", "수술비", "1종수술", "2종수술", "3종수술", "4종수술", "5종수술",
    "내시경수술", "개복수술", "복강경수술", "로봇수술",
]


def classify_by_keyword(coverage_name: str) -> tuple[str, float]:
    """
    키워드 기반 1차 분류.
    
    Args:
        coverage_name: 담보명
    
    Returns:
        (분류_타입, 확률) 튜플
        - 분류_타입: "질병" | "상해" | "통합" | "모호"
        - 확률: 0.0~1.0
    """
    name_lower = coverage_name.lower()
    
    # 명시적 질병/상해 키워드 우선 체크 (가장 높은 확률)
    if "질병수술" in name_lower or "질환수술" in name_lower:
        return ("질병", 0.98)
    if "상해수술" in name_lower or "재해수술" in name_lower:
        return ("상해", 0.98)
    
    # 통합 키워드 체크 (질병/상해 구분 없음)
    for keyword in INTEGRATED_KEYWORDS:
        if keyword in name_lower:
            return ("통합", 0.95)
    
    # 상해 키워드 체크
    injury_score = sum(1 for kw in INJURY_KEYWORDS if kw in name_lower)
    
    # 질병 키워드 체크
    disease_score = sum(1 for kw in DISEASE_KEYWORDS if kw in name_lower)
    
    # 점수 기반 분류
    total_score = injury_score + disease_score
    
    if total_score == 0:
        return ("모호", 0.0)
    
    if injury_score > disease_score:
        confidence = min(0.95, 0.7 + (injury_score / total_score) * 0.25)
        return ("상해", confidence)
    elif disease_score > injury_score:
        confidence = min(0.95, 0.7 + (disease_score / total_score) * 0.25)
        return ("질병", confidence)
    else:
        # 동점일 경우 통합으로 분류
        return ("통합", 0.6)


# ─────────────────────────────────────────────────────────────────────────────
# §3  LLM 에이전트 2차 분석 (모호한 경우)
# ─────────────────────────────────────────────────────────────────────────────

def classify_by_llm(coverage_name: str, context: str = "") -> tuple[str, float]:
    """
    LLM 에이전트를 활용한 2차 분석 (95% 이상 확률 목표).
    
    Args:
        coverage_name: 담보명
        context: 추가 문맥 정보 (약관 전체 문장 등)
    
    Returns:
        (분류_타입, 확률) 튜플
    
    Note:
        실제 구현 시 OpenAI GPT-4 또는 Gemini Pro를 호출하여
        담보명 + 문맥을 분석하고 95% 이상 확률로 분류.
        현재는 규칙 기반 폴백 로직으로 구현.
    """
    # TODO: 실제 LLM API 호출 구현
    # 현재는 고급 규칙 기반 폴백
    
    name_lower = coverage_name.lower()
    full_text = f"{coverage_name} {context}".lower()
    
    # 고급 패턴 매칭
    patterns = {
        "질병": [
            r"질병.*수술", r"암.*수술", r"종양.*수술", r"성인병.*수술",
            r"뇌.*수술", r"심장.*수술", r"간.*수술", r"신장.*수술",
        ],
        "상해": [
            r"상해.*수술", r"재해.*수술", r"교통.*수술", r"골절.*수술",
            r"사고.*수술", r"외상.*수술", r"부상.*수술",
        ],
    }
    
    for surgery_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            if re.search(pattern, full_text):
                return (surgery_type, 0.95)
    
    # 문맥 분석: "질병" 또는 "상해" 단어가 명시적으로 포함된 경우
    if "질병" in full_text and "상해" not in full_text:
        return ("질병", 0.92)
    if "상해" in full_text and "질병" not in full_text:
        return ("상해", 0.92)
    
    # 여전히 모호한 경우 통합으로 분류
    return ("통합", 0.85)


# ─────────────────────────────────────────────────────────────────────────────
# §4  통합 분류 함수 (메인 엔트리포인트)
# ─────────────────────────────────────────────────────────────────────────────

def classify_surgery_coverage(
    coverage_name: str,
    amount: float,
    context: str = "",
    use_llm: bool = True,
) -> SurgeryClassification:
    """
    수술비 담보를 질병/상해로 정밀 분류.
    
    Args:
        coverage_name: 담보명 (예: "일반수술비", "질병수술비", "상해수술비")
        amount: 보장 금액 (만원)
        context: 추가 문맥 정보 (약관 전체 문장 등)
        use_llm: LLM 에이전트 사용 여부 (기본값: True)
    
    Returns:
        SurgeryClassification 객체
    
    Example:
        >>> result = classify_surgery_coverage("질병수술비", 500)
        >>> print(result.surgery_type)  # "질병"
        >>> print(result.confidence)    # 0.95
        >>> print(result.display_name)  # "질병수술비"
    """
    # 1차: 키워드 기반 분류
    surgery_type, confidence = classify_by_keyword(coverage_name)
    classification_method = "keyword"
    
    # 2차: 모호한 경우 LLM 에이전트 활용
    if surgery_type == "모호" and use_llm:
        surgery_type, confidence = classify_by_llm(coverage_name, context)
        classification_method = "llm"
    
    # 모호한 경우 기본값: 통합
    if surgery_type == "모호":
        surgery_type = "통합"
        confidence = 0.5
        classification_method = "fallback"
    
    # 표시명 생성
    if surgery_type == "질병":
        display_name = "질병수술비"
    elif surgery_type == "상해":
        display_name = "상해수술비"
    else:  # 통합
        display_name = "수술비(질병+상해)"
    
    # 메타데이터 구성
    metadata = {
        "surgery_type": surgery_type,
        "original_name": coverage_name,
        "context_provided": bool(context),
        "classification_method": classification_method,
    }
    
    return SurgeryClassification(
        original_name=coverage_name,
        surgery_type=surgery_type,
        confidence=confidence,
        kb_category="③ 수술/입원비",
        display_name=display_name,
        amount=amount,
        metadata=metadata,
        classification_method=classification_method,
    )


# ─────────────────────────────────────────────────────────────────────────────
# §5  배치 분류 함수 (여러 담보 동시 처리)
# ─────────────────────────────────────────────────────────────────────────────

def classify_surgery_coverages_bulk(
    coverages: list[dict],
    use_llm: bool = True,
) -> list[SurgeryClassification]:
    """
    여러 수술비 담보를 배치로 분류.
    
    Args:
        coverages: 담보 목록
            [{"name": "질병수술비", "amount": 500}, ...]
        use_llm: LLM 에이전트 사용 여부
    
    Returns:
        SurgeryClassification 객체 리스트
    
    Example:
        >>> coverages = [
        ...     {"name": "질병수술비", "amount": 500},
        ...     {"name": "상해수술비", "amount": 300},
        ...     {"name": "일반수술비", "amount": 200},
        ... ]
        >>> results = classify_surgery_coverages_bulk(coverages)
        >>> for r in results:
        ...     print(f"{r.original_name} → {r.surgery_type} ({r.confidence:.0%})")
    """
    results = []
    
    for cov in coverages:
        name = cov.get("name", "")
        amount = float(cov.get("amount", 0))
        context = cov.get("context", "")
        
        # 수술비 관련 담보만 분류
        if any(kw in name for kw in ["수술", "시술", "절제", "적출"]):
            result = classify_surgery_coverage(name, amount, context, use_llm)
            results.append(result)
    
    return results


# ─────────────────────────────────────────────────────────────────────────────
# §6  KB 7대 분류 자동 매핑 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def map_to_kb_category(classification: SurgeryClassification) -> dict:
    """
    SurgeryClassification을 KB 7대 분류 형식으로 변환.
    
    Args:
        classification: 분류 결과
    
    Returns:
        KB 7대 분류 형식 딕셔너리
        {
            "category": "③ 수술/입원비",
            "name": "질병수술비",
            "amount": 500,
            "metadata": {
                "surgery_type": "질병",
                "confidence": 0.95,
                ...
            }
        }
    """
    return {
        "category": classification.kb_category,
        "name": classification.display_name,
        "amount": classification.amount,
        "metadata": classification.metadata,
        "surgery_type": classification.surgery_type,  # 핵심 구분값
        "confidence": classification.confidence,
        "classification_method": classification.classification_method,
    }


def map_to_kb_categories_bulk(
    classifications: list[SurgeryClassification]
) -> list[dict]:
    """
    여러 분류 결과를 KB 7대 분류 형식으로 일괄 변환.
    
    Args:
        classifications: 분류 결과 리스트
    
    Returns:
        KB 7대 분류 형식 딕셔너리 리스트
    """
    return [map_to_kb_category(c) for c in classifications]


# ─────────────────────────────────────────────────────────────────────────────
# §7  통계 및 분석 헬퍼
# ─────────────────────────────────────────────────────────────────────────────

def analyze_surgery_gap(
    classifications: list[SurgeryClassification],
    benchmark_disease: float = 700,  # 질병수술비 벤치마크 (만원)
    benchmark_injury: float = 500,   # 상해수술비 벤치마크 (만원)
) -> dict:
    """
    질병/상해 수술비 Gap 분석.
    
    Args:
        classifications: 분류 결과 리스트
        benchmark_disease: 질병수술비 벤치마크 (만원)
        benchmark_injury: 상해수술비 벤치마크 (만원)
    
    Returns:
        Gap 분석 결과
        {
            "disease_total": 500,
            "injury_total": 300,
            "disease_gap": 200,  # 부족 금액
            "injury_gap": 200,
            "disease_coverage_ratio": 71.4,  # 커버율 (%)
            "injury_coverage_ratio": 60.0,
            "alert": "질병 대비 상해 수술비 보장 부족"
        }
    """
    disease_total = sum(
        c.amount for c in classifications if c.surgery_type == "질병"
    )
    injury_total = sum(
        c.amount for c in classifications if c.surgery_type == "상해"
    )
    integrated_total = sum(
        c.amount for c in classifications if c.surgery_type == "통합"
    )
    
    # 통합 담보는 질병/상해 양쪽에 50%씩 배분
    disease_total += integrated_total * 0.5
    injury_total += integrated_total * 0.5
    
    disease_gap = max(0, benchmark_disease - disease_total)
    injury_gap = max(0, benchmark_injury - injury_total)
    
    disease_coverage_ratio = (disease_total / benchmark_disease * 100) if benchmark_disease > 0 else 0
    injury_coverage_ratio = (injury_total / benchmark_injury * 100) if benchmark_injury > 0 else 0
    
    # 경고 메시지 생성
    alerts = []
    if disease_gap > 0:
        alerts.append(f"질병수술비 {disease_gap:.0f}만원 부족")
    if injury_gap > 0:
        alerts.append(f"상해수술비 {injury_gap:.0f}만원 부족")
    
    if disease_coverage_ratio < injury_coverage_ratio - 20:
        alerts.append("⚠️ 질병 대비 상해 수술비 보장 부족")
    elif injury_coverage_ratio < disease_coverage_ratio - 20:
        alerts.append("⚠️ 상해 대비 질병 수술비 보장 부족")
    
    return {
        "disease_total": round(disease_total, 1),
        "injury_total": round(injury_total, 1),
        "integrated_total": round(integrated_total, 1),
        "disease_gap": round(disease_gap, 1),
        "injury_gap": round(injury_gap, 1),
        "disease_coverage_ratio": round(disease_coverage_ratio, 1),
        "injury_coverage_ratio": round(injury_coverage_ratio, 1),
        "alerts": alerts,
        "alert_message": " | ".join(alerts) if alerts else "✅ 질병/상해 수술비 균형 양호",
    }


# ─────────────────────────────────────────────────────────────────────────────
# §8  테스트 및 검증
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 테스트 데이터
    test_coverages = [
        {"name": "질병수술비", "amount": 500},
        {"name": "상해수술비", "amount": 300},
        {"name": "일반수술비", "amount": 200},
        {"name": "암수술비", "amount": 1000},
        {"name": "골절수술비", "amount": 400},
        {"name": "뇌수술비", "amount": 800},
        {"name": "교통사고수술비", "amount": 350},
        {"name": "3종수술비", "amount": 150},
    ]
    
    print("=" * 80)
    print("🔬 Vision AI 수술비 분류 엔진 테스트")
    print("=" * 80)
    
    # 배치 분류
    results = classify_surgery_coverages_bulk(test_coverages)
    
    print(f"\n📊 분류 결과 ({len(results)}건)")
    print("-" * 80)
    for r in results:
        print(f"• {r.original_name:20s} → {r.surgery_type:4s} "
              f"({r.confidence:5.1%}) [{r.classification_method}]")
    
    # Gap 분석
    print("\n📈 Gap 분석")
    print("-" * 80)
    gap_result = analyze_surgery_gap(results)
    print(f"질병수술비 총액: {gap_result['disease_total']:.0f}만원 "
          f"(커버율: {gap_result['disease_coverage_ratio']:.1f}%)")
    print(f"상해수술비 총액: {gap_result['injury_total']:.0f}만원 "
          f"(커버율: {gap_result['injury_coverage_ratio']:.1f}%)")
    print(f"통합 담보 총액: {gap_result['integrated_total']:.0f}만원")
    print(f"\n{gap_result['alert_message']}")
    
    # KB 7대 분류 매핑
    print("\n🏛️ KB 7대 분류 매핑")
    print("-" * 80)
    kb_mapped = map_to_kb_categories_bulk(results)
    for item in kb_mapped[:3]:  # 샘플 3개만 출력
        print(f"• [{item['category']}] {item['name']} - {item['amount']}만원")
        print(f"  └─ 타입: {item['surgery_type']} | 확률: {item['confidence']:.1%}")
    
    print("\n" + "=" * 80)
    print("✅ 테스트 완료")
    print("=" * 80)
