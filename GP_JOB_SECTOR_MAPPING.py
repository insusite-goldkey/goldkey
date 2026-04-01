# ══════════════════════════════════════════════════════════════════════════════
# [GP-JOB-SECTOR] 직업-섹터 자동 매핑 로직
# 고객의 직업 정보를 기반으로 최적의 전문 상담 섹터를 자동 추천
# ══════════════════════════════════════════════════════════════════════════════
# 작성일: 2026-04-01
# 목적: 직업 분류 DB(_JOB_TREE_DB)와 CORE_PROTOCOL 섹터를 연결하여 상담 효율성 극대화
# ══════════════════════════════════════════════════════════════════════════════

from typing import Literal


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 1] 직업-섹터 매핑 테이블
# ──────────────────────────────────────────────────────────────────────────────

_JOB_SECTOR_MAPPING: dict[str, list[str]] = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [경영·임원] CEO·임원·대표
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "CEO·임원": ["ceo_plan", "succession", "inheritance_tax", "stock_valuation", "life", "cancer"],
    "대표이사": ["ceo_plan", "succession", "inheritance_tax", "stock_valuation", "corp_factory", "pl"],
    "법인 대표": ["ceo_plan", "corp_factory", "pl", "group", "succession", "inheritance_tax"],
    "개인사업자 대표": ["personal_factory", "commercial_fire", "pl", "ceo_plan", "workers_comp"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [제조업] 공장·생산직
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "제조업 대표": ["corp_factory", "personal_factory", "pl", "ceo_plan", "workers_comp", "group"],
    "공장장": ["corp_factory", "workers_comp", "group", "accident", "life"],
    "생산직 근로자": ["workers_comp", "accident", "medical", "surgery", "cancer"],
    "화학공장 근로자": ["workers_comp", "corp_factory", "accident", "cancer", "medical"],
    "위험물 취급자": ["workers_comp", "accident", "life", "medical", "cancer"],
    "기계 조작원": ["workers_comp", "accident", "medical", "surgery"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [상가·자영업] 점포 운영자
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "상가 운영자": ["commercial_fire", "pl", "professional", "medical", "cancer"],
    "음식점 운영자": ["commercial_fire", "pl", "workers_comp", "medical", "accident"],
    "카페 운영자": ["commercial_fire", "pl", "medical", "cancer", "pension"],
    "편의점 운영자": ["commercial_fire", "pl", "medical", "cancer", "pension"],
    "소매업 운영자": ["commercial_fire", "pl", "medical", "cancer", "pension"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [전문직] 의사·변호사·회계사·건축사
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "의사": ["professional", "medical", "cancer", "brain", "heart", "pension", "life"],
    "치과의사": ["professional", "dental", "medical", "cancer", "pension", "life"],
    "한의사": ["professional", "medical", "cancer", "pension", "life"],
    "변호사": ["professional", "cancer", "brain", "heart", "pension", "life"],
    "회계사": ["professional", "cancer", "brain", "heart", "pension", "life"],
    "세무사": ["professional", "cancer", "brain", "heart", "pension", "life"],
    "건축사": ["professional", "pl", "cancer", "brain", "heart", "pension"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [운전·운송] 운전기사·배달원
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "택시 기사": ["driver", "auto", "accident", "medical", "cancer", "life"],
    "버스 기사": ["driver", "auto", "accident", "medical", "cancer", "life"],
    "화물차 기사": ["driver", "auto", "accident", "medical", "cancer", "life"],
    "배달 기사": ["driver", "auto", "accident", "medical", "cancer"],
    "대리운전 기사": ["driver", "auto", "accident", "medical", "life"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [건설·건축] 건설 현장 근로자
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "건설 현장 근로자": ["workers_comp", "accident", "medical", "surgery", "life"],
    "철근공": ["workers_comp", "accident", "medical", "surgery", "life"],
    "용접공": ["workers_comp", "accident", "medical", "surgery", "cancer"],
    "도장공": ["workers_comp", "accident", "medical", "cancer"],
    "비계공": ["workers_comp", "accident", "medical", "surgery", "life"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [사무직] 일반 사무직·공무원
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "일반 사무직": ["cancer", "brain", "heart", "medical", "pension", "life"],
    "공무원": ["cancer", "brain", "heart", "medical", "pension", "life"],
    "교사": ["cancer", "brain", "heart", "medical", "pension", "life"],
    "은행원": ["cancer", "brain", "heart", "medical", "pension", "life"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [주부·무직] 가정주부·은퇴자
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "가정주부": ["cancer", "brain", "heart", "medical", "dementia", "dental", "pension"],
    "은퇴자": ["cancer", "brain", "heart", "medical", "dementia", "dental", "pension"],
    "무직": ["cancer", "medical", "accident", "life"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [부동산] 부동산 관련 직업
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "부동산 중개업자": ["professional", "home_fire", "cancer", "brain", "pension"],
    "건물주": ["home_fire", "commercial_fire", "inheritance_tax", "succession", "pension"],
    "임대업자": ["home_fire", "commercial_fire", "inheritance_tax", "pension"],
}


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 2] 상해급수별 섹터 추천
# ──────────────────────────────────────────────────────────────────────────────

_GRADE_SECTOR_MAPPING: dict[int, list[str]] = {
    1: ["cancer", "brain", "heart", "medical", "pension", "life"],  # 1급 (사무직)
    2: ["cancer", "brain", "heart", "medical", "accident", "life"],  # 2급 (일반 현장직)
    3: ["workers_comp", "accident", "medical", "surgery", "cancer", "life"],  # 3급 (고위험 현장직)
    4: ["workers_comp", "accident", "medical", "surgery", "life"],  # 4급 (초고위험 현장직)
}


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 3] 키워드 기반 섹터 추천
# ──────────────────────────────────────────────────────────────────────────────

_KEYWORD_SECTOR_MAPPING: dict[str, list[str]] = {
    # 업종 키워드
    "제조": ["corp_factory", "personal_factory", "pl", "workers_comp"],
    "공장": ["corp_factory", "personal_factory", "pl", "workers_comp"],
    "화학": ["corp_factory", "workers_comp", "cancer", "medical"],
    "식품": ["pl", "commercial_fire", "workers_comp"],
    "음식": ["commercial_fire", "pl", "workers_comp"],
    "카페": ["commercial_fire", "pl"],
    "편의점": ["commercial_fire", "pl"],
    "상가": ["commercial_fire", "pl"],
    "점포": ["commercial_fire", "pl"],
    "건설": ["workers_comp", "accident", "medical"],
    "건축": ["professional", "pl", "workers_comp"],
    
    # 직급 키워드
    "대표": ["ceo_plan", "succession", "inheritance_tax"],
    "CEO": ["ceo_plan", "succession", "inheritance_tax", "stock_valuation"],
    "임원": ["ceo_plan", "succession", "life"],
    "사장": ["ceo_plan", "succession", "inheritance_tax"],
    
    # 전문직 키워드
    "의사": ["professional", "medical", "cancer"],
    "변호사": ["professional", "cancer", "brain"],
    "회계사": ["professional", "cancer", "brain"],
    "세무사": ["professional", "cancer", "brain"],
    
    # 운전 키워드
    "운전": ["driver", "auto", "accident"],
    "택시": ["driver", "auto", "accident"],
    "버스": ["driver", "auto", "accident"],
    "화물": ["driver", "auto", "accident"],
    "배달": ["driver", "auto", "accident"],
}


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 4] 섹터 추천 엔진
# ──────────────────────────────────────────────────────────────────────────────

def recommend_sectors_by_job(
    job_name: str,
    job_grade: int | None = None,
    job_flags: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    직업 정보를 기반으로 최적의 섹터 추천
    
    Args:
        job_name: 직업명 (예: "CEO·임원", "제조업 대표")
        job_grade: 상해급수 (1~4)
        job_flags: 고지의무 플래그 리스트
        top_k: 추천할 섹터 수 (기본값: 5)
    
    Returns:
        추천 섹터 리스트 (우선순위 순)
        [
            {"sector_key": "ceo_plan", "score": 100, "reason": "직업 직접 매칭"},
            {"sector_key": "succession", "score": 90, "reason": "직업 직접 매칭"},
            ...
        ]
    """
    sector_scores: dict[str, dict] = {}
    
    # 1. 직업명 직접 매칭 (최우선)
    if job_name in _JOB_SECTOR_MAPPING:
        for idx, sector_key in enumerate(_JOB_SECTOR_MAPPING[job_name]):
            score = 100 - (idx * 5)  # 순서대로 점수 감소
            sector_scores[sector_key] = {
                "score": score,
                "reason": "직업 직접 매칭",
            }
    
    # 2. 키워드 기반 매칭
    for keyword, sectors in _KEYWORD_SECTOR_MAPPING.items():
        if keyword in job_name:
            for idx, sector_key in enumerate(sectors):
                base_score = 80 - (idx * 5)
                if sector_key in sector_scores:
                    sector_scores[sector_key]["score"] += base_score * 0.3
                    sector_scores[sector_key]["reason"] += f", 키워드 매칭({keyword})"
                else:
                    sector_scores[sector_key] = {
                        "score": base_score,
                        "reason": f"키워드 매칭({keyword})",
                    }
    
    # 3. 상해급수 기반 매칭
    if job_grade and job_grade in _GRADE_SECTOR_MAPPING:
        for idx, sector_key in enumerate(_GRADE_SECTOR_MAPPING[job_grade]):
            base_score = 60 - (idx * 3)
            if sector_key in sector_scores:
                sector_scores[sector_key]["score"] += base_score * 0.2
                sector_scores[sector_key]["reason"] += f", 상해급수({job_grade}급)"
            else:
                sector_scores[sector_key] = {
                    "score": base_score,
                    "reason": f"상해급수({job_grade}급)",
                }
    
    # 4. 고지의무 플래그 기반 추가 가중치
    if job_flags:
        for flag in job_flags:
            if "화학" in flag or "위험물" in flag:
                for sector_key in ["workers_comp", "cancer", "medical"]:
                    if sector_key in sector_scores:
                        sector_scores[sector_key]["score"] += 10
                        sector_scores[sector_key]["reason"] += f", 고위험 직업"
    
    # 5. 기본 섹터 추가 (매칭 결과가 없을 경우)
    if not sector_scores:
        default_sectors = ["cancer", "medical", "accident", "life", "pension"]
        for idx, sector_key in enumerate(default_sectors):
            sector_scores[sector_key] = {
                "score": 50 - (idx * 5),
                "reason": "기본 추천",
            }
    
    # 6. 점수 순으로 정렬 및 상위 K개 반환
    sorted_sectors = sorted(
        [
            {"sector_key": k, "score": v["score"], "reason": v["reason"]}
            for k, v in sector_scores.items()
        ],
        key=lambda x: x["score"],
        reverse=True,
    )
    
    return sorted_sectors[:top_k]


def get_sector_priority_by_customer(
    job: str,
    age: int | None = None,
    is_ceo: bool = False,
    has_factory: bool = False,
    has_commercial: bool = False,
) -> list[str]:
    """
    고객 프로필 기반 섹터 우선순위 반환
    
    Args:
        job: 직업명
        age: 나이
        is_ceo: CEO/대표 여부
        has_factory: 공장 소유 여부
        has_commercial: 상가 소유 여부
    
    Returns:
        섹터 키 리스트 (우선순위 순)
    """
    sectors = []
    
    # 1. CEO/대표 우선 섹터
    if is_ceo:
        sectors.extend(["ceo_plan", "succession", "inheritance_tax", "stock_valuation"])
    
    # 2. 자산 보유 기반 섹터
    if has_factory:
        sectors.extend(["corp_factory", "personal_factory", "pl", "workers_comp"])
    
    if has_commercial:
        sectors.extend(["commercial_fire", "pl"])
    
    # 3. 직업 기반 섹터
    job_recommendations = recommend_sectors_by_job(job, top_k=5)
    sectors.extend([r["sector_key"] for r in job_recommendations])
    
    # 4. 연령 기반 섹터
    if age:
        if age >= 60:
            sectors.extend(["dementia", "pension", "cancer", "brain", "heart"])
        elif age >= 40:
            sectors.extend(["cancer", "brain", "heart", "pension"])
        else:
            sectors.extend(["accident", "medical", "cancer"])
    
    # 5. 중복 제거 및 순서 유지
    seen = set()
    unique_sectors = []
    for sector in sectors:
        if sector not in seen:
            seen.add(sector)
            unique_sectors.append(sector)
    
    return unique_sectors


# ──────────────────────────────────────────────────────────────────────────────
# [SECTION 5] 테스트 및 검증
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("[GP-JOB-SECTOR] 직업-섹터 자동 매핑 테스트")
    print("=" * 80)
    
    # 테스트 케이스
    test_cases = [
        {"job": "제조업 대표", "grade": 1, "flags": []},
        {"job": "CEO·임원", "grade": 1, "flags": []},
        {"job": "화학공장 근로자", "grade": 3, "flags": ["유해화학물질 ⚠️ 고지의무"]},
        {"job": "상가 운영자", "grade": 1, "flags": []},
        {"job": "택시 기사", "grade": 2, "flags": []},
        {"job": "일반 사무직", "grade": 1, "flags": []},
    ]
    
    for idx, case in enumerate(test_cases, 1):
        print(f"\n[테스트 {idx}] 직업: {case['job']}, 상해급수: {case['grade']}급")
        recommendations = recommend_sectors_by_job(
            job_name=case["job"],
            job_grade=case["grade"],
            job_flags=case["flags"],
            top_k=5,
        )
        print("추천 섹터:")
        for rec in recommendations:
            print(f"  - {rec['sector_key']} (점수: {rec['score']:.1f}, 이유: {rec['reason']})")
    
    print("\n" + "=" * 80)
    print("고객 프로필 기반 섹터 우선순위 테스트")
    print("=" * 80)
    
    priority = get_sector_priority_by_customer(
        job="제조업 대표",
        age=55,
        is_ceo=True,
        has_factory=True,
        has_commercial=False,
    )
    print(f"\n고객: 제조업 대표 (55세, CEO, 공장 소유)")
    print(f"우선순위 섹터 (상위 10개): {priority[:10]}")
    
    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)
