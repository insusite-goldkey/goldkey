"""
[GP-IAP] 코인 충전 UI 및 하드 락(Hard Lock) 화면
Goldkey AI Masters 2026 - 인앱 결제 UI 컴포넌트
"""
import streamlit as st
from typing import Optional


def render_hard_lock_screen(
    user_id: str,
    current_credits: int = 0,
    required_credits: int = 1,
    feature_name: str = "에이젠틱 AI 기능",
    plan_type: str = "BASIC"
) -> None:
    """
    [GP-STANDARD] 코인 부족/PRO 기능 제한 시 하드 락(Hard Lock) 화면 렌더링.
    컴팩트 카드 디자인 + 투트랙 액션 버튼 (직접 결제 / 바이럴 루프)
    
    Args:
        user_id: 회원 ID
        current_credits: 현재 코인 잔액
        required_credits: 필요한 코인 수량
        feature_name: 기능 이름
        plan_type: 현재 플랜 (BASIC/PRO)
    """
    # 중앙 정렬 컨테이너
    col_left, col_center, col_right = st.columns([1, 3, 1])
    
    with col_center:
        # 컴팩트 카드 래퍼 (.sops-wrap 스타일)
        st.markdown(
            "<div style='max-width:500px;margin:40px auto;background:linear-gradient(135deg,#fef3f2,#fef9f5);"
            "border:1px dashed #e5e7eb;border-radius:16px;padding:28px;box-shadow:0 4px 12px rgba(0,0,0,0.08);'>"
            
            # 헤더
            "<div style='text-align:center;margin-bottom:20px;'>"
            "<h2 style='color:#1e293b;font-size:1.35rem;font-weight:900;margin:0 0 8px 0;'>"
            f"🔒 {feature_name} 잠금 (코인 부족)</h2>"
            "<div style='height:2px;width:60px;background:linear-gradient(90deg,#f59e0b,#fbbf24);margin:0 auto;'></div>"
            "</div>"
            
            # 상태창 (코인 잔액 vs 필요량)
            "<div style='background:#f3f4f6;border-radius:10px;padding:14px;margin:16px 0;'>"
            "<div style='display:flex;justify-content:space-around;align-items:center;'>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.75rem;color:#6b7280;font-weight:600;margin-bottom:4px;'>현재 보유 코인</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#dc2626;'>{current_credits}🪙</div>"
            f"</div>"
            f"<div style='font-size:1.2rem;color:#9ca3af;font-weight:700;'>|</div>"
            f"<div style='text-align:center;'>"
            f"<div style='font-size:0.75rem;color:#6b7280;font-weight:600;margin-bottom:4px;'>필요 코인</div>"
            f"<div style='font-size:1.5rem;font-weight:900;color:#0369a1;'>{required_credits}🪙</div>"
            f"</div>"
            "</div>"
            "</div>"
            
            # 가치 어필 문구 (조사 생략형 단문)
            "<div style='background:#fff;border-left:3px solid #0ea5e9;padding:14px;border-radius:8px;margin:16px 0;'>"
            "<div style='font-size:0.88rem;color:#334155;line-height:1.65;font-weight:500;'>"
            "<b style='color:#0c4a6e;'>PRO플랜:</b> AI 정밀 분석·최적 제안 포인트 도출 필수 엔진. "
            "완벽한 상담 준비. <b style='color:#dc2626;'>한도 초과.</b> 충전 및 업그레이드 요망."
            "</div>"
            "</div>"
            
            "</div>",
            unsafe_allow_html=True
        )
        
        # 투트랙 액션 버튼 A: 직접 결제 (딥블루)
        st.markdown(
            "<div style='margin:20px 0 12px 0;'>"
            "<div style='background:#1e3a8a;border-radius:12px;padding:16px;text-align:center;"
            "cursor:pointer;transition:all 0.3s;box-shadow:0 2px 8px rgba(30,58,138,0.3);'>"
            "<div style='color:#fff;font-size:1.05rem;font-weight:900;'>"
            "💎 PRO플랜 즉시 업그레이드 (코인 충전)</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        
        if st.button(
            "💎 PRO플랜 즉시 업그레이드 (코인 충전)",
            key="hard_lock_upgrade_pro",
            use_container_width=True,
            type="primary"
        ):
            _process_recharge(user_id, "pro_addon_300", 300)
        
        # 투트랙 액션 버튼 B: 바이럴 루프 (파스텔 골드/그린)
        st.markdown(
            "<div style='margin:12px 0;'>"
            "<div style='background:linear-gradient(135deg,#FFF8E1,#f0fdf4);border:2px solid #fbbf24;"
            "border-radius:12px;padding:16px;text-align:center;box-shadow:0 2px 8px rgba(251,191,36,0.2);'>"
            "<div style='color:#78350f;font-size:1.05rem;font-weight:900;'>"
            "🎁 동료 1명 소개. 100🪙(2개월분) 즉시 획득</div>"
            "<div style='font-size:0.78rem;color:#92400e;margin-top:6px;'>"
            "✨ 소개받은 분도 50🪙 보너스 지급</div>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        
        if st.button(
            "🎁 동료 1명 소개. 100🪙(2개월분) 즉시 획득",
            key="hard_lock_referral",
            use_container_width=True,
            type="secondary"
        ):
            st.session_state["show_referral_modal"] = True
            st.rerun()
        
        # 뒤로가기 버튼 (탈출구 명확히 제공)
        st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
        
        if st.button(
            "↩️ 이전 화면으로 돌아가기",
            key="hard_lock_back",
            use_container_width=True
        ):
            # 하드 락 플래그 해제
            if "hard_lock_active" in st.session_state:
                del st.session_state["hard_lock_active"]
            st.rerun()
        
        # 하단 안내 문구
        st.markdown(
            "<div style='text-align:center;margin-top:16px;'>"
            "<div style='font-size:0.75rem;color:#9ca3af;line-height:1.5;'>"
            "💡 충전 즉시 코인 반영. 미사용 코인은 익월 이월 불가.<br>"
            "📞 문의: support@goldkey-ai.com"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )


def _process_recharge(user_id: str, product_id: str, coins: int) -> None:
    """
    코인 충전 처리 (내부 함수).
    
    Args:
        user_id: 회원 ID
        product_id: 상품 ID
        coins: 충전할 코인 수량
    """
    from modules.payment_handler import simulate_test_purchase
    
    with st.spinner("🔄 결제 처리 중..."):
        # 테스트 모드: 실제 결제 없이 코인 충전 시뮬레이션
        result = simulate_test_purchase(user_id, product_id)
        
        if result.get('success'):
            # 성공 시 세션 상태 업데이트
            st.session_state['current_credits'] = result.get('balance_after', 0)
            
            # 폭죽 효과
            st.balloons()
            
            # 성공 메시지
            st.success(
                f"✅ 결제가 완료되어 **{coins} 코인**이 즉시 충전되었습니다!\n\n"
                f"💰 현재 잔액: **{result.get('balance_after', 0)} 코인**"
            )
            
            # 화면 새로고침
            st.rerun()
        else:
            # 실패 메시지
            error_msg = result.get('message', '알 수 없는 오류')
            st.error(f"❌ 충전 실패: {error_msg}")


def render_credit_balance_widget(user_id: str) -> None:
    """
    코인 잔액 위젯 (상단 헤더용).
    
    Args:
        user_id: 회원 ID
    """
    from modules.payment_handler import get_current_credits
    
    # 세션에서 코인 조회 (없으면 DB에서 조회)
    if 'current_credits' not in st.session_state:
        st.session_state['current_credits'] = get_current_credits(user_id)
    
    credits = st.session_state.get('current_credits', 0)
    
    # 코인 부족 경고
    if credits < 10:
        color = "#dc2626"
        icon = "⚠️"
    elif credits < 50:
        color = "#f59e0b"
        icon = "💰"
    else:
        color = "#10b981"
        icon = "💎"
    
    st.markdown(
        f"<div style='background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;"
        f"padding:8px 12px;display:inline-block;'>"
        f"<span style='font-size:0.85rem;color:#6b7280;'>보유 코인</span> "
        f"<span style='font-size:1.1rem;font-weight:700;color:{color};'>"
        f"{icon} {credits}</span>"
        f"</div>",
        unsafe_allow_html=True
    )


def check_credits_and_lock(
    user_id: str,
    required_credits: int = 1,
    feature_name: str = "이 기능"
) -> bool:
    """
    코인 잔액 확인 및 부족 시 하드 락 화면 표시.
    
    Args:
        user_id: 회원 ID
        required_credits: 필요한 코인 수량
        feature_name: 기능 이름
    
    Returns:
        True: 코인 충분 (기능 사용 가능)
        False: 코인 부족 (하드 락 화면 표시됨)
    """
    from modules.payment_handler import get_current_credits
    
    # 현재 코인 조회
    if 'current_credits' not in st.session_state:
        st.session_state['current_credits'] = get_current_credits(user_id)
    
    current_credits = st.session_state.get('current_credits', 0)
    
    # 코인 부족 시 하드 락 화면 표시
    if current_credits < required_credits:
        render_hard_lock_screen(
            user_id=user_id,
            current_credits=current_credits,
            required_credits=required_credits,
            feature_name=feature_name
        )
        return False
    
    return True


def deduct_credits(user_id: str, amount: int, description: str = "") -> bool:
    """
    코인 차감 처리.
    
    Args:
        user_id: 회원 ID
        amount: 차감할 코인 수량
        description: 차감 사유
    
    Returns:
        True: 차감 성공
        False: 차감 실패
    """
    from db_utils import _get_sb
    
    sb = _get_sb()
    if not sb:
        return False
    
    try:
        # 현재 코인 조회
        result = sb.table('gk_members').select('current_credits').eq('user_id', user_id).execute()
        if not result.data or len(result.data) == 0:
            return False
        
        current_credits = result.data[0].get('current_credits', 0)
        
        # 잔액 부족 확인
        if current_credits < amount:
            return False
        
        # 코인 차감
        new_credits = current_credits - amount
        sb.table('gk_members').update({
            'current_credits': new_credits,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'USAGE',
            'amount': -amount,
            'balance_after': new_credits,
            'description': description or f'{amount} 코인 사용'
        }).execute()
        
        # 세션 업데이트
        st.session_state['current_credits'] = new_credits
        
        return True
    
    except Exception as e:
        print(f"[IAP] 코인 차감 실패: {e}")
        return False
