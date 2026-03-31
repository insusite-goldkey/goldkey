# =============================================================================
# [GP-PENSION-ANALYTICS] 연금 분석 모니터링 및 A/B 테스트 모듈
# 목적: 사용자 행동 추적, 전환율 분석, 통계 수집
# =============================================================================

import streamlit as st
from datetime import datetime
from typing import Dict, Optional
import json


def log_pension_analysis(
    agent_id: str,
    analysis_params: Dict,
    analysis_result: Dict,
    customer_name: Optional[str] = None,
    customer_id: Optional[str] = None,
) -> bool:
    """
    연금 분석 실행 로그 기록
    
    Args:
        agent_id: 설계사 ID
        analysis_params: 분석 입력 파라미터
        analysis_result: 분석 결과
        customer_name: 고객명 (선택)
        customer_id: 고객 ID (선택)
    
    Returns:
        성공 여부
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # 로그 데이터 구성
        log_data = {
            "agent_id": agent_id,
            "customer_name": customer_name,
            "customer_id": customer_id,
            
            # 입력 파라미터
            "age": analysis_params.get("age"),
            "retirement_age": analysis_params.get("retirement_age"),
            "life_expectancy": analysis_params.get("life_expectancy"),
            "region_type": analysis_params.get("region_type"),
            "household_type": analysis_params.get("household_type"),
            "monthly_contribution": analysis_params.get("monthly_contribution"),
            "annual_return_rate": analysis_params.get("annual_return_rate"),
            "monthly_salary": analysis_params.get("monthly_salary"),
            
            # 4층 보장
            "national_pension_amt": analysis_params.get("national_pension_amt", 0),
            "retirement_pension_amt": analysis_params.get("retirement_pension_amt", 0),
            "housing_pension_amt": analysis_params.get("housing_pension_amt", 0),
            "annual_income": analysis_params.get("annual_income"),
            
            # 분석 옵션
            "inflation_scenario": analysis_params.get("inflation_scenario"),
            "use_trinity_mode": analysis_params.get("use_trinity_mode", False),
            
            # 분석 결과
            "accumulated_amount": analysis_result.get("accumulated_amount"),
            "monthly_pension_standard": analysis_result.get("monthly_pension_standard"),
            "monthly_pension_trinity": analysis_result.get("monthly_pension_trinity"),
            "gap_amount": analysis_result.get("gap_amount"),
            "gap_percentage": analysis_result.get("gap_percentage"),
            "total_replacement_rate": analysis_result.get("total_replacement_rate"),
            "annual_tax_benefit": analysis_result.get("annual_tax_benefit"),
            "total_tax_benefit": analysis_result.get("total_tax_benefit"),
            
            # 메타데이터
            "session_id": st.session_state.get("session_id"),
            "device_type": _detect_device_type(),
        }
        
        # Supabase 삽입
        result = supabase.table("pension_analysis_logs").insert(log_data).execute()
        
        # 로그 ID 세션에 저장 (전환 추적용)
        if result.data:
            st.session_state["last_pension_log_id"] = result.data[0].get("id")
        
        return True
        
    except Exception as e:
        st.warning(f"⚠️ 분석 로그 기록 실패: {e}")
        return False


def track_conversion(
    stage: str,
    agent_id: str,
    customer_id: Optional[str] = None,
    is_converted: bool = False,
    contract_amount: Optional[int] = None,
    contract_product: Optional[str] = None,
    test_group: Optional[str] = None,
    notes: Optional[str] = None,
) -> bool:
    """
    전환율 추적 기록
    
    Args:
        stage: 단계 (view/interest/consult/contract)
        agent_id: 설계사 ID
        customer_id: 고객 ID (선택)
        is_converted: 계약 전환 여부
        contract_amount: 계약 금액 (원/월)
        contract_product: 계약 상품명
        test_group: A/B 테스트 그룹
        notes: 상담 메모
    
    Returns:
        성공 여부
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        # 마지막 분석 로그 ID 가져오기
        analysis_log_id = st.session_state.get("last_pension_log_id")
        
        # 마지막 분석에서 보여준 Gap 정보 가져오기
        last_result = st.session_state.get("pension_analysis_result")
        last_inputs = st.session_state.get("pension_inputs")
        
        tracking_data = {
            "analysis_log_id": analysis_log_id,
            "agent_id": agent_id,
            "customer_id": customer_id,
            "stage": stage,
            "is_converted": is_converted,
            "contract_amount": contract_amount,
            "contract_product": contract_product,
            "test_group": test_group or "A",  # 기본값 A
            "inflation_scenario_shown": last_inputs.get("inflation_scenario") if last_inputs else None,
            "gap_amount_shown": last_result.gap_amount if last_result else None,
            "notes": notes,
        }
        
        # Supabase 삽입
        supabase.table("pension_conversion_tracking").insert(tracking_data).execute()
        
        return True
        
    except Exception as e:
        st.warning(f"⚠️ 전환 추적 기록 실패: {e}")
        return False


def log_dashboard_usage(
    agent_id: str,
    page_view: bool = True,
    analysis_run: bool = False,
    input_change: bool = False,
    scenario_change: bool = False,
) -> bool:
    """
    대시보드 사용 통계 기록
    
    Args:
        agent_id: 설계사 ID
        page_view: 페이지 조회 여부
        analysis_run: 분석 실행 여부
        input_change: 입력 필드 변경 여부
        scenario_change: 시나리오 변경 여부
    
    Returns:
        성공 여부
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            return False
        
        session_id = st.session_state.get("session_id", "unknown")
        today = datetime.now().date().isoformat()
        
        # 기존 레코드 조회
        existing = supabase.table("pension_dashboard_usage").select("*").eq(
            "agent_id", agent_id
        ).eq("session_id", session_id).eq("usage_date", today).execute()
        
        if existing.data:
            # 업데이트
            record = existing.data[0]
            update_data = {
                "page_view_count": record["page_view_count"] + (1 if page_view else 0),
                "analysis_run_count": record["analysis_run_count"] + (1 if analysis_run else 0),
                "input_changes_count": record["input_changes_count"] + (1 if input_change else 0),
                "scenario_changes_count": record["scenario_changes_count"] + (1 if scenario_change else 0),
            }
            supabase.table("pension_dashboard_usage").update(update_data).eq(
                "id", record["id"]
            ).execute()
        else:
            # 신규 삽입
            insert_data = {
                "agent_id": agent_id,
                "session_id": session_id,
                "page_view_count": 1 if page_view else 0,
                "analysis_run_count": 1 if analysis_run else 0,
                "input_changes_count": 1 if input_change else 0,
                "scenario_changes_count": 1 if scenario_change else 0,
                "device_type": _detect_device_type(),
                "usage_date": today,
            }
            supabase.table("pension_dashboard_usage").insert(insert_data).execute()
        
        return True
        
    except Exception as e:
        # 조용히 실패 (사용자 경험에 영향 없음)
        return False


def get_ab_test_group(agent_id: str) -> str:
    """
    A/B 테스트 그룹 할당
    
    Args:
        agent_id: 설계사 ID
    
    Returns:
        테스트 그룹 (A/B/C)
    """
    # 설계사 ID 해시값 기반으로 그룹 할당 (일관성 유지)
    import hashlib
    hash_value = int(hashlib.md5(agent_id.encode()).hexdigest(), 16)
    group_index = hash_value % 3
    
    groups = ["A", "B", "C"]
    return groups[group_index]


def get_recommended_inflation_scenario(test_group: str) -> str:
    """
    A/B 테스트 그룹별 권장 물가상승률 시나리오
    
    Args:
        test_group: A/B 테스트 그룹
    
    Returns:
        권장 시나리오 (보수적/중립/공격적)
    """
    scenario_map = {
        "A": "보수적",  # 3% - 낙관적
        "B": "중립",    # 4% - 현실적
        "C": "공격적",  # 5% - 비관적 (공포 타격)
    }
    return scenario_map.get(test_group, "중립")


def _detect_device_type() -> str:
    """
    디바이스 타입 감지
    
    Returns:
        디바이스 타입 (desktop/tablet/mobile)
    """
    try:
        # Streamlit의 user agent 정보 활용 (가능한 경우)
        # 현재는 간단히 세션 정보 기반으로 추정
        if "device_type" in st.session_state:
            return st.session_state["device_type"]
        
        # 기본값
        return "desktop"
    except:
        return "unknown"


def render_analytics_dashboard(agent_id: str):
    """
    설계사용 분석 통계 대시보드 렌더링
    
    Args:
        agent_id: 설계사 ID
    """
    try:
        from db_utils import get_supabase_client
        
        supabase = get_supabase_client()
        if not supabase:
            st.warning("⚠️ 통계 데이터를 불러올 수 없습니다.")
            return
        
        st.markdown("### 📊 나의 연금 분석 통계")
        
        # 기간 선택
        col1, col2 = st.columns(2)
        with col1:
            days = st.selectbox("조회 기간", [7, 30, 90], index=1)
        
        # 통계 조회
        from datetime import timedelta
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        logs = supabase.table("pension_analysis_logs").select("*").eq(
            "agent_id", agent_id
        ).gte("created_at", start_date).execute()
        
        if not logs.data:
            st.info(f"📭 최근 {days}일간 분석 기록이 없습니다.")
            return
        
        # 통계 계산
        total_analyses = len(logs.data)
        unique_customers = len(set(log.get("customer_id") for log in logs.data if log.get("customer_id")))
        avg_gap = sum(log.get("gap_percentage", 0) for log in logs.data) / total_analyses
        
        scenario_counts = {
            "보수적": sum(1 for log in logs.data if log.get("inflation_scenario") == "보수적"),
            "중립": sum(1 for log in logs.data if log.get("inflation_scenario") == "중립"),
            "공격적": sum(1 for log in logs.data if log.get("inflation_scenario") == "공격적"),
        }
        
        # 메트릭 표시
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("총 분석 횟수", f"{total_analyses}회")
        with col2:
            st.metric("고유 고객 수", f"{unique_customers}명")
        with col3:
            st.metric("평균 Gap", f"{avg_gap:.1f}%")
        with col4:
            most_used = max(scenario_counts, key=scenario_counts.get)
            st.metric("주로 사용한 시나리오", most_used)
        
        # 시나리오별 분포
        st.markdown("#### 물가 시나리오 사용 분포")
        st.bar_chart(scenario_counts)
        
    except Exception as e:
        st.error(f"❌ 통계 조회 오류: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# [EXPORT] 주요 함수 목록
# ══════════════════════════════════════════════════════════════════════════════

__all__ = [
    "log_pension_analysis",
    "track_conversion",
    "log_dashboard_usage",
    "get_ab_test_group",
    "get_recommended_inflation_scenario",
    "render_analytics_dashboard",
]
