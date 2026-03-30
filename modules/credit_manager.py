"""
[GP-제14조] 크레딧 과금 통제 시스템
Goldkey AI Masters 2026 - 1코인/3코인 차등 차감 및 하드 락 구현
"""
import streamlit as st
from typing import Optional, Dict, Any
from db_utils import _get_sb


# ──────────────────────────────────────────────────────────────────────────
# [§1] 크레딧 확인 및 차감
# ──────────────────────────────────────────────────────────────────────────

def check_and_deduct_credit(
    user_id: str,
    required_coins: int,
    reason: str,
    auto_deduct: bool = True
) -> bool:
    """
    사용자의 크레딧을 확인하고 차감하는 함수.
    
    Args:
        user_id: 회원 ID
        required_coins: 필요한 코인 수량
        reason: 차감 사유
        auto_deduct: True일 경우 자동 차감, False일 경우 확인만
    
    Returns:
        True: 크레딧 충분 (차감 성공)
        False: 크레딧 부족 (하드 락)
    """
    # 1. 세션에서 현재 크레딧 조회
    current_credits = st.session_state.get('current_credits', 0)
    
    # 2. 하드 락: 크레딧 부족 시 차단
    if current_credits < required_coins:
        st.error(
            f"🚨 **잔여 코인이 부족합니다.**\n\n"
            f"• 필요 코인: **{required_coins} 🪙**\n"
            f"• 현재 잔액: **{current_credits} 🪙**\n\n"
            f"플랜을 업그레이드하거나 코인을 충전해 주세요."
        )
        return False
    
    # 3. 확인만 하는 경우 (auto_deduct=False)
    if not auto_deduct:
        return True
    
    # 4. Supabase에서 실제 차감 처리
    sb = _get_sb()
    if not sb:
        st.error("❌ 데이터베이스 연결 실패")
        return False
    
    try:
        # 현재 잔액 재확인 (동시성 제어)
        result = sb.table('gk_members').select('current_credits').eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            st.error("❌ 사용자 정보를 찾을 수 없습니다.")
            return False
        
        db_credits = result.data[0].get('current_credits', 0)
        
        if db_credits < required_coins:
            st.error(f"🚨 잔여 코인 부족 (DB 잔액: {db_credits} 🪙)")
            st.session_state['current_credits'] = db_credits
            return False
        
        # 코인 차감
        new_credits = db_credits - required_coins
        sb.table('gk_members').update({
            'current_credits': new_credits,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'USAGE',
            'amount': -required_coins,
            'balance_after': new_credits,
            'description': reason
        }).execute()
        
        # 세션 업데이트
        st.session_state['current_credits'] = new_credits
        
        return True
    
    except Exception as e:
        print(f"[CREDIT] 코인 차감 실패: {e}")
        st.error(f"❌ 코인 차감 처리 실패: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────
# [§2] 0코인 방어 로직 - 기존 분석 결과 조회
# ──────────────────────────────────────────────────────────────────────────

def get_existing_analysis(
    person_id: str,
    analysis_type: str,
    agent_id: str = ""
) -> Optional[Dict[str, Any]]:
    """
    DB에서 기존 분석 결과 조회 (0코인 무료 조회).
    
    Args:
        person_id: 고객 ID
        analysis_type: 분석 유형 ('SCAN', 'TRINITY', 'AI_STRATEGY', 'KAKAO_MESSAGE')
        agent_id: 설계사 ID (선택)
    
    Returns:
        기존 분석 결과 딕셔너리 또는 None
    """
    sb = _get_sb()
    if not sb:
        return None
    
    try:
        # analysis_reports 테이블에서 조회
        query = sb.table('analysis_reports').select('*').eq('person_id', person_id).eq('analysis_type', analysis_type)
        
        if agent_id:
            query = query.eq('agent_id', agent_id)
        
        result = query.order('created_at', desc=True).limit(1).execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    
    except Exception as e:
        print(f"[CREDIT] 기존 분석 조회 실패: {e}")
        return None


def save_analysis_result(
    person_id: str,
    agent_id: str,
    analysis_type: str,
    result_data: Dict[str, Any],
    coins_used: int = 0
) -> bool:
    """
    분석 결과를 DB에 저장 (다음 조회 시 0코인 무료).
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
        analysis_type: 분석 유형
        result_data: 분석 결과 데이터
        coins_used: 사용된 코인 수량
    
    Returns:
        True: 저장 성공
        False: 저장 실패
    """
    sb = _get_sb()
    if not sb:
        return False
    
    try:
        sb.table('analysis_reports').insert({
            'person_id': person_id,
            'agent_id': agent_id,
            'analysis_type': analysis_type,
            'result_data': result_data,
            'coins_used': coins_used,
            'created_at': 'NOW()'
        }).execute()
        
        return True
    
    except Exception as e:
        print(f"[CREDIT] 분석 결과 저장 실패: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────
# [§3] 통합 분석 실행 함수 (0코인 방어 + 차감 + 저장)
# ──────────────────────────────────────────────────────────────────────────

def run_analysis_with_credit_control(
    user_id: str,
    person_id: str,
    analysis_type: str,
    analysis_function,
    required_coins: int,
    reason: str,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """
    크레딧 통제가 적용된 분석 실행 함수.
    
    처리 순서:
    1. 기존 분석 결과 확인 (0코인 무료 조회)
    2. 없으면 크레딧 차감 시도
    3. 분석 함수 실행
    4. 결과 DB 저장
    
    Args:
        user_id: 회원 ID
        person_id: 고객 ID
        analysis_type: 분석 유형
        analysis_function: 실제 분석을 수행하는 함수
        required_coins: 필요한 코인 수량
        reason: 차감 사유
        **kwargs: analysis_function에 전달할 추가 파라미터
    
    Returns:
        분석 결과 딕셔너리 또는 None
    """
    # 1. 기존 분석 결과 확인 (0코인 로직)
    existing_data = get_existing_analysis(person_id, analysis_type, user_id)
    
    if existing_data:
        st.success(
            f"✅ **저장된 분석 데이터를 무료로 불러왔습니다.**\n\n"
            f"🪙 코인 차감: **0** (평생 무료 조회)"
        )
        return existing_data.get('result_data', existing_data)
    
    # 2. 결과가 없으면 크레딧 차감 시도
    if not check_and_deduct_credit(user_id, required_coins, reason):
        # 하드 락 - 크레딧 부족
        return None
    
    # 3. 코인 차감 성공 알림
    st.toast(f"🪙 코인이 차감되었습니다. (-{required_coins})", icon="💰")
    
    # 4. 분석 함수 실행
    try:
        result = analysis_function(**kwargs)
        
        if result:
            # 5. DB에 저장 (다음엔 무료로 조회)
            save_analysis_result(
                person_id=person_id,
                agent_id=user_id,
                analysis_type=analysis_type,
                result_data=result,
                coins_used=required_coins
            )
        
        return result
    
    except Exception as e:
        print(f"[CREDIT] 분석 실행 실패: {e}")
        st.error(f"❌ 분석 실행 중 오류 발생: {e}")
        
        # 실패 시 코인 환불 처리
        refund_credits(user_id, required_coins, f"분석 실패 환불: {reason}")
        
        return None


# ──────────────────────────────────────────────────────────────────────────
# [§4] 코인 환불 처리
# ──────────────────────────────────────────────────────────────────────────

def refund_credits(user_id: str, amount: int, reason: str) -> bool:
    """
    코인 환불 처리.
    
    Args:
        user_id: 회원 ID
        amount: 환불할 코인 수량
        reason: 환불 사유
    
    Returns:
        True: 환불 성공
        False: 환불 실패
    """
    sb = _get_sb()
    if not sb:
        return False
    
    try:
        # 현재 잔액 조회
        result = sb.table('gk_members').select('current_credits').eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return False
        
        current_credits = result.data[0].get('current_credits', 0)
        new_credits = current_credits + amount
        
        # 코인 환불
        sb.table('gk_members').update({
            'current_credits': new_credits,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'REFUND',
            'amount': amount,
            'balance_after': new_credits,
            'description': reason
        }).execute()
        
        # 세션 업데이트
        st.session_state['current_credits'] = new_credits
        
        st.info(f"💰 코인이 환불되었습니다. (+{amount} 🪙)")
        
        return True
    
    except Exception as e:
        print(f"[CREDIT] 코인 환불 실패: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────
# [§5] 크레딧 잔액 조회
# ──────────────────────────────────────────────────────────────────────────

def get_current_credits(user_id: str, force_refresh: bool = False) -> int:
    """
    현재 코인 잔액 조회.
    
    Args:
        user_id: 회원 ID
        force_refresh: True일 경우 DB에서 강제 조회
    
    Returns:
        코인 잔액
    """
    # 세션에서 조회 (캐시)
    if not force_refresh and 'current_credits' in st.session_state:
        return st.session_state.get('current_credits', 0)
    
    # DB에서 조회
    sb = _get_sb()
    if not sb:
        return 0
    
    try:
        result = sb.table('gk_members').select('current_credits').eq('user_id', user_id).execute()
        
        if result.data and len(result.data) > 0:
            credits = result.data[0].get('current_credits', 0)
            st.session_state['current_credits'] = credits
            return credits
        
        return 0
    
    except Exception as e:
        print(f"[CREDIT] 코인 잔액 조회 실패: {e}")
        return 0


# ──────────────────────────────────────────────────────────────────────────
# [§6] UI 헬퍼 함수
# ──────────────────────────────────────────────────────────────────────────

def render_coin_button(
    label: str,
    required_coins: int,
    key: str,
    button_type: str = "secondary",
    use_container_width: bool = True
) -> bool:
    """
    코인 표시가 포함된 버튼 렌더링 (하드 락 자동 적용).
    
    Args:
        label: 버튼 라벨
        required_coins: 필요한 코인 수량
        key: 버튼 고유 키
        button_type: 버튼 타입 ("primary", "secondary")
        use_container_width: 전체 너비 사용 여부
    
    Returns:
        True: 버튼 클릭됨
        False: 버튼 클릭 안됨 또는 비활성화됨
    """
    current_credits = st.session_state.get('current_credits', 0)
    is_locked = current_credits < required_coins
    
    # 버튼 라벨에 코인 표시 추가
    button_label = f"{label} (🪙 -{required_coins})"
    
    # 잔액 부족 시 경고 표시
    if is_locked:
        button_label = f"🔒 {label} (부족: {required_coins - current_credits} 🪙)"
    
    return st.button(
        button_label,
        key=key,
        disabled=is_locked,
        type=button_type,
        use_container_width=use_container_width
    )


def render_credit_warning(required_coins: int) -> None:
    """
    코인 부족 경고 메시지 렌더링.
    
    Args:
        required_coins: 필요한 코인 수량
    """
    current_credits = st.session_state.get('current_credits', 0)
    
    if current_credits < required_coins:
        shortage = required_coins - current_credits
        st.warning(
            f"⚠️ **코인이 부족합니다.**\n\n"
            f"• 필요: {required_coins} 🪙\n"
            f"• 현재: {current_credits} 🪙\n"
            f"• 부족: {shortage} 🪙\n\n"
            f"플랜을 업그레이드하거나 코인을 충전해 주세요."
        )
