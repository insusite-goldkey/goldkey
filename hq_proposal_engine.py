"""
hq_proposal_engine.py — AI 감성 세일즈 전략 및 제안서 엔진
[GP-STEP8] Goldkey AI Masters 2026

AI 전략 엔진:
- 보장 공백 분석 (Gap Analysis)
- 감성 페르소나 매칭 (Emotional Persona Matching)
- 3가지 톤 스크립트 생성 (전문적/감성적/직설적)
- 3가지 플랜 추천 (실속/표준/VIP)
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, Dict, Any, List, Tuple
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 레이어 — Step 5 + Step 7 데이터 융합
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def get_customer_persona(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    고객 페르소나 조회 (Step 5 데이터)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 고객 페르소나 정보
    """
    try:
        sb = _get_sb()
        if not sb:
            return {}
        
        result = (
            sb.table("gk_people")
            .select("*")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .maybe_single()
            .execute()
        )
        
        if not result or not result.data:
            return {}
        
        customer = result.data
        
        return {
            "name": customer.get("name", ""),
            "birth_date": customer.get("birth_date", ""),
            "gender": customer.get("gender", ""),
            "job": customer.get("job", ""),
            "interests": customer.get("interests", ""),
            "current_stage": customer.get("current_stage", 1),
            "last_contact": customer.get("last_contact", "")
        }
    except Exception:
        return {}


def get_insurance_buckets(person_id: str, agent_id: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    보험 3버킷 데이터 조회 (Step 7 데이터)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 버킷별 보험 계약 목록
    """
    try:
        sb = _get_sb()
        if not sb:
            return {"A": [], "B": [], "C": []}
        
        # gk_policy_roles를 통해 person_id와 연결된 증권 조회
        result = (
            sb.table("gk_policy_roles")
            .select("*, gk_policies!inner(*)")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        buckets = {"A": [], "B": [], "C": []}
        
        for role_data in (result.data or []):
            policy = role_data.get("gk_policies") or {}
            part = policy.get("part", "A")
            
            policy_info = {
                "policy_id": policy.get("id"),
                "policy_number": policy.get("policy_number", ""),
                "insurance_company": policy.get("insurance_company", ""),
                "product_name": policy.get("product_name", ""),
                "product_type": policy.get("product_type", ""),
                "premium": policy.get("premium", 0),
                "contract_date": policy.get("contract_date", ""),
                "expiry_date": policy.get("expiry_date", ""),
                "role": role_data.get("role", "")
            }
            
            if part in buckets:
                buckets[part].append(policy_info)
        
        return buckets
    except Exception:
        return {"A": [], "B": [], "C": []}


# ══════════════════════════════════════════════════════════════════════════════
# [2] 보장 공백 분석 (Gap Analysis)
# ══════════════════════════════════════════════════════════════════════════════

def analyze_coverage_gap(
    buckets: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    보장 공백 분석 (3버킷 기반) + 3세대 항암 치료비 전이 시뮬레이션
    
    Args:
        buckets: 3버킷 데이터 (A/B/C)
    
    Returns:
        dict: 보장 공백 분석 결과
    """
    current_coverage = {}
    total_premium = 0
    
    # A버킷 (우리사 계약) 분석
    for policy in buckets.get("A", []):
        premium = float(policy.get("premium", 0) or 0)
        total_premium += premium
        
        # 담보 분석 (간단 예시)
        product_name = policy.get("product_name", "").lower()
        if "암" in product_name:
            current_coverage["cancer"] = current_coverage.get("cancer", 0) + 50000000
        if "실손" in product_name:
            current_coverage["medical"] = current_coverage.get("medical", 0) + 100000000
    
    # [GP-PSP-01] 암보험 3세대 치료비 전이 시뮬레이션
    # NGS 검사비: 본인부담 70~150만원, 비급여 시 최대 400만원
    ngs_cost_min = 700000
    ngs_cost_max = 4000000
    
    # 1세대 독성항암: 수백만원
    gen1_cost = 5000000
    
    # 2세대 표적항암: 연간 3~8천만원
    gen2_cost_min = 30000000
    gen2_cost_max = 80000000
    
    # 3세대 면역항암: 연간 1억원 이상
    gen3_cost = 100000000
    
    # 비급여 부담금: 암 환자 1인당 연간 평균 2,800만원 ~ 5,500만원
    avg_non_covered_min = 28000000
    avg_non_covered_max = 55000000
    
    # [GP-PSP-01-3] 지역 거점 병원 vs 수도권 Big 5 전략
    # 수도권 원정 진료비 (교통비 + 숙박비 + 간병비)
    metro_travel_cost_monthly = 5000000  # 월 500만원
    metro_travel_cost_yearly = metro_travel_cost_monthly * 12  # 연간 6,000만원
    
    # 임상시험 참여 시 약제비 절감 효과
    clinical_trial_drug_cost_yearly = 120000000  # 키트루다 연간 1억 2천만원 무상
    clinical_trial_drug_cost_yearly_opdivo = 80000000  # 옵디보 연간 8천만원 무상
    
    # 비급여 약제비 (임상시험 미참여 시)
    non_covered_drug_cost_monthly = 10000000  # 월 1,000만원
    non_covered_drug_cost_yearly = non_covered_drug_cost_monthly * 12  # 연간 1억 2천만원
    
    # 경제적 역설 분석: 수도권 원정 진료비 vs 지방 비급여 약제비
    economic_paradox = {
        "metro_travel_yearly": metro_travel_cost_yearly,
        "clinical_trial_savings": clinical_trial_drug_cost_yearly,
        "non_covered_drug_yearly": non_covered_drug_cost_yearly,
        "net_savings": clinical_trial_drug_cost_yearly - metro_travel_cost_yearly  # 6천만원 절감
    }
    
    # 보장 공백 판단 (최신 치료비 기준)
    gaps = []
    cancer_coverage = current_coverage.get("cancer", 0)
    
    # 암보험 공백 분석 (표적항암 최소 기준 7천만원 + 수도권 원정 진료비 6천만원)
    # [GP-STEP13] Financial Toxicity (경제적 파산) 엔진
    if cancer_coverage < 70000000:
        # AI 브리핑: 단순 진단비 3~5천만원은 현대 암 치료의 6개월치 비용에 불과
        financial_toxicity_warning = (
            f"⚠️ 경제적 파산(Financial Toxicity) 리스크: "
            f"단순 진단비 3~5천만원은 현대 암 치료의 6개월치 비용에 불과합니다. "
            f"NGS 검사비(평균 150만원) + 비급여 표적항암제(연간 5천만원~1억원) 리스크를 반드시 고려해야 합니다."
        )
        
        gaps.append({
            "type": "암보험",
            "severity": "critical",
            "message": f"암 진단비 부족 (현재: {cancer_coverage//10000}만원, 권장: 7천만원 이상)",
            "detail": (
                f"NGS 검사비 {ngs_cost_max//10000}만원 + "
                f"2세대 표적항암 연간 {gen2_cost_max//10000}만원 + "
                f"3세대 면역항암 연간 {gen3_cost//10000}만원 대비 필요"
            ),
            "financial_toxicity_warning": financial_toxicity_warning,
            "cost_simulation": {
                "ngs": {"min": ngs_cost_min, "max": ngs_cost_max},
                "ngs_average": 1500000,  # NGS 검사비 평균 150만원
                "gen1": gen1_cost,
                "gen2": {"min": gen2_cost_min, "max": gen2_cost_max},
                "gen3": gen3_cost,
                "non_covered_avg": {"min": avg_non_covered_min, "max": avg_non_covered_max},
                "non_covered_targeted_yearly": {"min": 50000000, "max": 100000000}  # 비급여 표적항암제 연간 5천만원~1억원
            },
            "regional_strategy": {
                "stage_1_3": {
                    "recommendation": "지방 거점 병원 (화순전남대병원 등)",
                    "reason": "수도권 대기(2~4주) 대비 신속 수술로 예후 15% 이상 유리",
                    "cost_advantage": "원정 진료비 절감"
                },
                "stage_4_recurrence": {
                    "recommendation": "수도권 Big 5 (임상시험 접근성)",
                    "reason": "신약 임상시험 참여 시 수억 원대 약제비 무상 투여",
                    "cost_advantage": f"연간 {clinical_trial_drug_cost_yearly//10000}만원 절감 가능"
                }
            },
            "economic_paradox": economic_paradox
        })
    
    if current_coverage.get("medical", 0) < 100000000:
        gaps.append({
            "type": "실손의료보험",
            "severity": "high",
            "message": "실손의료보험 가입 필요"
        })
    
    if "pension" not in current_coverage:
        gaps.append({
            "type": "연금",
            "severity": "medium",
            "message": "노후 준비 필요 (연금 보장 부재)"
        })
    
    # [GP-STEP13] APP 프로토콜 - 공장/상가 화재보험 비례보상 리스크 분석
    factory_coverage = current_coverage.get("factory_fire", 0)
    if factory_coverage > 0:
        # 재조달가액 산정 미비 리스크 분석
        # 예시: 재조달가액 10억 원, 보험가입 5억 원 → 비례보상 50%
        estimated_replacement_cost = factory_coverage * 2  # 가정: 보험가액이 재조달가액의 50%
        proportional_compensation_risk = (
            f"⚠️ 비례보상 리스크: 보험가액 {factory_coverage//100000000}억원이 "
            f"재조달가액 {estimated_replacement_cost//100000000}억원보다 낮을 경우, "
            f"화재 시 1억원 피해 발생해도 50%인 5천만원만 보상받습니다. "
            f"재조달가액 정밀 산정 후 보험가액 상향 조정이 필요합니다."
        )
        
        gaps.append({
            "type": "공장화재보험",
            "severity": "critical",
            "message": f"공장 화재보험 비례보상 리스크 (현재 보험가액: {factory_coverage//100000000}억원)",
            "detail": "재조달가액 산정 미비로 인한 비례보상 원칙 적용 주의",
            "proportional_compensation_warning": proportional_compensation_risk,
            "factory_risk_analysis": {
                "current_coverage": factory_coverage,
                "estimated_replacement_cost": estimated_replacement_cost,
                "compensation_ratio": 0.5,  # 50% 보상 비율
                "average_fire_damage": {
                    "제조업": 350000000,  # 3억 5천만원
                    "창고업": 280000000,  # 2억 8천만원
                    "식품공장": 420000000  # 4억 2천만원
                },
                "bi_coverage_recommendation": "영업중단 손실(BI) 특약 가입 권장 - 화재 복구 기간 동안 고정비 및 영업이익 손실 보상"
            }
        })
    
    # 타사 계약 중 승환 추천
    conversion_targets = []
    for policy in buckets.get("B", []):
        premium = float(policy.get("premium", 0) or 0)
        if premium > 100000:  # 월 10만원 이상
            conversion_targets.append({
                "policy_id": policy.get("policy_id"),
                "product_name": policy.get("product_name", ""),
                "insurance_company": policy.get("insurance_company", ""),
                "premium": premium,
                "reason": "고액 보험료 절감 가능"
            })
    
    return {
        "current_coverage": current_coverage,
        "total_premium": total_premium,
        "gaps": gaps,
        "conversion_targets": conversion_targets,
        "economic_paradox_analysis": economic_paradox,
        "factory_fire_risk_detected": factory_coverage > 0
    }


# ══════════════════════════════════════════════════════════════════════════════
# [3] 감성 페르소나 매칭 (Emotional Persona Matching)
# ══════════════════════════════════════════════════════════════════════════════

def generate_emotional_scripts(
    persona: Dict[str, Any],
    gap_analysis: Dict[str, Any]
) -> Dict[str, Dict[str, str]]:
    """
    감성 페르소나 매칭 — 3가지 톤 스크립트 생성
    
    Args:
        persona: 고객 페르소나
        gap_analysis: 보장 공백 분석 결과
    
    Returns:
        dict: 3가지 톤별 스크립트
    """
    name = persona.get("name", "고객님")
    job = persona.get("job", "")
    interests = persona.get("interests", "")
    
    # 보장 공백 요약
    gaps = gap_analysis.get("gaps", [])
    gap_summary = ", ".join([g["message"] for g in gaps[:2]]) if gaps else "현재 보장 상태 양호"
    
    # 1. 전문적 톤 (Professional)
    professional = {
        "opening": f"{name}님, 안녕하세요. 골드키 AI 마스터즈입니다. "
                   f"오늘은 {name}님의 보험 포트폴리오를 분석한 결과를 말씀드리고자 합니다.",
        "body": f"현재 {name}님의 보장 현황을 분석한 결과, {gap_summary}입니다. "
                f"전문가 관점에서 볼 때, 이 부분을 보완하시면 더욱 안정적인 보장 설계가 가능합니다.",
        "objection_handling": "걱정하지 마세요. 무리한 권유는 절대 하지 않습니다. "
                              "다만, 전문가로서 객관적인 분석 결과를 공유드리는 것이니 참고만 해주시면 됩니다."
    }
    
    # 2. 감성적 톤 (Emotional) + 비급여 리스크 + 지역 전략 강조
    emotional = {
        "opening": f"{name}님, 요즘 어떻게 지내세요? "
                   f"바쁘신 와중에도 시간 내주셔서 정말 감사합니다.",
        "body": f"{name}님의 소중한 가족과 미래를 위해, 현재 보장 상태를 꼼꼼히 살펴봤습니다. "
                f"{gap_summary}. "
                f"2021년 국가암등록통계에 따르면 남성 39.1%(2.5명 중 1명), 여성 36.0%(3명 중 1명)이 평생 한 번 암을 진단받습니다. "
                f"의학의 발전으로 암은 죽는 병이 아니라 돈으로 고치는 병이 되었지만, "
                f"건강보험이 따라가지 못하는 비급여 표적항암제와 면역항암 요법의 비용은 가족의 경제적 파산을 초래할 수 있습니다. "
                f"혹시 모를 위험에 대비해, 지금부터라도 준비하시면 좋을 것 같아요.",
        "objection_handling": "저도 {name}님의 입장이라면 같은 생각을 했을 거예요. "
                              "하지만 최신 면역항암제 연간 치료비가 1억 원인 시대에 진단비 5천만 원은 6개월치 치료비에 불과합니다. "
                              "가족을 생각하면, 지금 이 순간이 가장 중요한 시기일 수 있습니다.",
        "regional_strategy": "서울 큰 병원으로 가야 하지 않을까 걱정되시죠? "
                            "병기에 따라 전략이 달라야 합니다. 초기라면 가족 곁에서 신속히 수술하는 것이 최고이며, "
                            "만약 신약이 필요한 단계라면 제가 서울의 임상시험 센터와 연결된 네트워크를 찾아봐 드리겠습니다. "
                            "임상시험에 참여하시면 수억 원대 신약을 무상으로 투여받으실 수 있어요."
    }
    
    # 3. 직설적 톤 (Direct) + 치료비 폭증 구조 명시
    direct = {
        "opening": f"{name}님, 바로 본론으로 들어가겠습니다. "
                   f"시간 낭비 없이 핵심만 말씀드리겠습니다.",
        "body": f"현재 {name}님의 보장 상태는 솔직히 말씀드려 부족합니다. {gap_summary}. "
                f"암 치료는 1세대 독성항암(수백만 원) → 2세대 표적항암(연간 3~8천만 원) → 3세대 면역항암(연간 1억 원 이상)으로 비용이 폭증합니다. "
                f"지금 당장 조치하지 않으면, 나중에 후회할 수 있습니다.",
        "objection_handling": "거절하시는 건 자유입니다. 하지만 나중에 '그때 들어둘 걸' 하고 후회하지 마세요. "
                              "NGS 검사비만 400만 원, 표적항암제는 연간 8천만 원입니다. 기회는 지금입니다."
    }
    
    # 직업별 커스터마이징
    if job:
        if "의사" in job or "간호" in job:
            professional["opening"] += f" {job}님이시니 보험의 중요성을 누구보다 잘 아실 거라 생각합니다."
        elif "교사" in job or "교수" in job:
            emotional["opening"] += f" {job}님이시니 미래 설계의 중요성을 잘 아실 것 같아요."
        elif "사업" in job or "대표" in job:
            direct["opening"] += f" {job}님이시니 숫자와 리스크 관리에 익숙하실 겁니다."
    
    return {
        "professional": professional,
        "emotional": emotional,
        "direct": direct
    }


# ══════════════════════════════════════════════════════════════════════════════
# [4] 3가지 플랜 추천 (실속/표준/VIP)
# ══════════════════════════════════════════════════════════════════════════════

def generate_three_plans(
    persona: Dict[str, Any],
    gap_analysis: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    3가지 플랜 추천 (실속/표준/VIP)
    
    Args:
        persona: 고객 페르소나
        gap_analysis: 보장 공백 분석 결과
    
    Returns:
        list: 3가지 플랜 목록
    """
    current_premium = gap_analysis.get("total_premium", 0)
    gaps = gap_analysis.get("gaps", [])
    
    # 실속형 플랜 (현재 보험료 +20%)
    budget_plan = {
        "plan_type": "실속",
        "monthly_premium": int(current_premium * 1.2),
        "coverage_items": [
            {"name": "생명보험", "amount": "1억원", "premium": 50000},
            {"name": "실손의료보험", "amount": "5천만원", "premium": 30000},
        ],
        "total_coverage": "1.5억원",
        "features": [
            "필수 보장만 집중",
            "합리적인 보험료",
            "기본 보장 완성"
        ],
        "recommendation": "예산을 고려하면서도 필수 보장을 갖추고 싶으신 분께 추천합니다."
    }
    
    # 표준형 플랜 (현재 보험료 +50%)
    standard_plan = {
        "plan_type": "표준",
        "monthly_premium": int(current_premium * 1.5),
        "coverage_items": [
            {"name": "생명보험", "amount": "3억원", "premium": 100000},
            {"name": "실손의료보험", "amount": "1억원", "premium": 50000},
            {"name": "암보험", "amount": "5천만원", "premium": 40000},
        ],
        "total_coverage": "4.5억원",
        "features": [
            "균형잡힌 보장 설계",
            "주요 질병 보장 포함",
            "가족 보장 고려"
        ],
        "recommendation": "안정적인 보장과 합리적인 보험료의 균형을 원하시는 분께 추천합니다."
    }
    
    # VIP형 플랜 (현재 보험료 +100%)
    vip_plan = {
        "plan_type": "VIP",
        "monthly_premium": int(current_premium * 2.0),
        "coverage_items": [
            {"name": "생명보험", "amount": "5억원", "premium": 150000},
            {"name": "실손의료보험", "amount": "2억원", "premium": 80000},
            {"name": "암보험", "amount": "1억원", "premium": 70000},
            {"name": "연금보험", "amount": "월 200만원", "premium": 200000},
        ],
        "total_coverage": "8억원 + 연금",
        "features": [
            "최고 수준 보장",
            "노후 준비 포함",
            "프리미엄 서비스"
        ],
        "recommendation": "최상의 보장과 노후 준비를 동시에 원하시는 분께 추천합니다."
    }
    
    return [budget_plan, standard_plan, vip_plan]


# ══════════════════════════════════════════════════════════════════════════════
# [5] 통합 제안서 생성 (Main Engine)
# ══════════════════════════════════════════════════════════════════════════════

def generate_proposal(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    통합 제안서 생성 (AI 전략 엔진 메인 함수)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 제안서 데이터
    """
    # 1. 고객 페르소나 조회 (Step 5)
    persona = get_customer_persona(person_id, agent_id)
    
    if not persona or not persona.get("name"):
        return {
            "success": False,
            "error": "고객 정보를 찾을 수 없습니다."
        }
    
    # 2. 보험 3버킷 조회 (Step 7)
    buckets = get_insurance_buckets(person_id, agent_id)
    
    # 3. 보장 공백 분석
    gap_analysis = analyze_coverage_gap(buckets)
    
    # 4. 감성 페르소나 매칭 (3가지 톤 스크립트)
    emotional_scripts = generate_emotional_scripts(persona, gap_analysis)
    
    # 5. 3가지 플랜 추천
    three_plans = generate_three_plans(persona, gap_analysis)
    
    # 6. 제안서 메타데이터
    proposal_metadata = {
        "proposal_id": f"PROP_{person_id[:8]}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "created_at": datetime.datetime.now().isoformat(),
        "customer_name": persona.get("name", ""),
        "agent_id": agent_id
    }
    
    return {
        "success": True,
        "metadata": proposal_metadata,
        "persona": persona,
        "buckets": buckets,
        "gap_analysis": gap_analysis,
        "emotional_scripts": emotional_scripts,
        "three_plans": three_plans
    }


# ══════════════════════════════════════════════════════════════════════════════
# [6] 제안서 저장 (Supabase)
# ══════════════════════════════════════════════════════════════════════════════

def save_proposal_to_db(proposal_data: Dict[str, Any], person_id: str, agent_id: str) -> bool:
    """
    제안서 데이터를 Supabase에 저장
    
    Args:
        proposal_data: 제안서 데이터
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # gk_proposals 테이블에 저장 (테이블 생성 필요)
        proposal_record = {
            "proposal_id": proposal_data["metadata"]["proposal_id"],
            "person_id": person_id,
            "agent_id": agent_id,
            "proposal_data": json.dumps(proposal_data, ensure_ascii=False),
            "created_at": proposal_data["metadata"]["created_at"]
        }
        
        result = sb.table("gk_proposals").insert(proposal_record).execute()
        
        return bool(result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [7] 에이전틱 단계 업데이트 (4단계 → 5/6단계)
# ══════════════════════════════════════════════════════════════════════════════

def update_customer_stage_to_proposal(person_id: str, agent_id: str, target_stage: int = 5) -> bool:
    """
    고객 세일즈 단계 업데이트 (제안서 생성 완료)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        target_stage: 목표 단계 (5: 제안, 6: 설득)
    
    Returns:
        bool: 성공 여부
    """
    try:
        sb = _get_sb()
        if not sb:
            return False
        
        # gk_people 테이블 업데이트
        result = (
            sb.table("gk_people")
            .update({"current_stage": target_stage})
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .execute()
        )
        
        return bool(result.data)
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [8] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_proposal_ui.py 통합)

```python
from hq_proposal_engine import generate_proposal, save_proposal_to_db, update_customer_stage_to_proposal

# 제안서 생성
proposal_data = generate_proposal(person_id, agent_id)

if proposal_data.get("success"):
    # 제안서 저장
    save_proposal_to_db(proposal_data, person_id, agent_id)
    
    # 에이전틱 단계 업데이트 (4단계 → 5단계)
    update_customer_stage_to_proposal(person_id, agent_id, target_stage=5)
    
    # UI 렌더링
    render_proposal_ui(proposal_data)
```

## gk_proposals 테이블 생성 SQL

```sql
CREATE TABLE IF NOT EXISTS gk_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id TEXT NOT NULL UNIQUE,
    person_id TEXT NOT NULL REFERENCES gk_people(person_id) ON DELETE RESTRICT,
    agent_id TEXT NOT NULL,
    proposal_data JSONB NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_proposals_person_id ON gk_proposals(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_agent_id ON gk_proposals(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_proposal_id ON gk_proposals(proposal_id);

COMMENT ON TABLE gk_proposals IS 'AI 제안서 저장 테이블 (Step 8)';
```
"""
