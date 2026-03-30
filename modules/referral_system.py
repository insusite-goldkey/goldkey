"""
[GP-VIRAL] 추천인 마케팅 시스템 모듈
- 추천인 보상 지급 (7일 후 +100코인)
- 코인으로 구독 연장
- 추천인 리워드 현황 조회
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    from modules.db_utils import get_supabase_client
except ImportError:
    from db_utils import get_supabase_client


# ═══════════════════════════════════════════════════════════════════════════
# [1] 추천인 보상 지급 함수
# ═══════════════════════════════════════════════════════════════════════════

def grant_referral_reward(
    referrer_id: str,
    new_member_id: str,
    new_member_name: str
) -> Dict[str, Any]:
    """
    추천인에게 보상 지급 (+100코인)
    
    Args:
        referrer_id: 추천인 ID
        new_member_id: 신규 가입자 ID
        new_member_name: 신규 가입자 이름
    
    Returns:
        결과 딕셔너리 (success, reward_coins, new_balance 등)
    """
    try:
        supabase = get_supabase_client()
        
        # RPC 함수 호출
        result = supabase.rpc(
            'grant_referral_reward',
            {
                'p_referrer_id': referrer_id,
                'p_new_member_id': new_member_id,
                'p_new_member_name': new_member_name
            }
        ).execute()
        
        if result.data:
            return result.data
        else:
            return {
                'success': False,
                'error': 'No data returned from RPC'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def check_and_grant_pending_rewards() -> List[Dict[str, Any]]:
    """
    7일이 지난 신규 가입자의 추천인에게 보상 지급
    
    Returns:
        지급 결과 리스트
    """
    try:
        supabase = get_supabase_client()
        
        # 7일 전 날짜 계산
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        # 7일 이상 지난 신규 가입자 중 추천인이 있는 회원 조회
        result = supabase.table("gk_members").select(
            "id, name, referrer_id, created_at"
        ).not_.is_("referrer_id", "null").lte("created_at", seven_days_ago).execute()
        
        if not result.data:
            return []
        
        rewards_granted = []
        
        for member in result.data:
            # 이미 보상을 받았는지 확인
            history_check = supabase.table("gk_credit_history").select("id").eq(
                "user_id", member['referrer_id']
            ).eq("transaction_type", "REFERRAL_REWARD").like(
                "reason", f"%{member['id']}%"
            ).execute()
            
            if history_check.data:
                continue  # 이미 지급됨
            
            # 보상 지급
            reward_result = grant_referral_reward(
                member['referrer_id'],
                member['id'],
                member['name']
            )
            
            if reward_result.get('success'):
                rewards_granted.append(reward_result)
        
        return rewards_granted
        
    except Exception as e:
        st.error(f"⚠️ 추천인 보상 지급 오류: {str(e)}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
# [2] 코인으로 구독 연장 함수
# ═══════════════════════════════════════════════════════════════════════════

def extend_subscription_with_coins(
    user_id: str,
    plan_type: str = 'basic'
) -> Dict[str, Any]:
    """
    코인으로 구독 기간 연장
    
    Args:
        user_id: 사용자 ID
        plan_type: 플랜 타입 ('basic' 또는 'pro')
    
    Returns:
        결과 딕셔너리 (success, coins_deducted, new_renewal_date 등)
    """
    try:
        supabase = get_supabase_client()
        
        # RPC 함수 호출
        result = supabase.rpc(
            'extend_subscription_with_coins',
            {
                'p_user_id': user_id,
                'p_plan_type': plan_type
            }
        ).execute()
        
        if result.data:
            return result.data
        else:
            return {
                'success': False,
                'error': 'No data returned from RPC'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ═══════════════════════════════════════════════════════════════════════════
# [3] 추천인 리워드 현황 조회
# ═══════════════════════════════════════════════════════════════════════════

def get_referral_rewards_history(user_id: str) -> List[Dict[str, Any]]:
    """
    추천인 리워드 현황 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        리워드 내역 리스트
    """
    try:
        supabase = get_supabase_client()
        
        # v_referral_rewards 뷰에서 조회
        result = supabase.table("gk_credit_history").select(
            "*"
        ).eq("user_id", user_id).eq("transaction_type", "REFERRAL_REWARD").order(
            "created_at", desc=True
        ).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"⚠️ 리워드 내역 조회 오류: {str(e)}")
        return []


def get_referral_stats(user_id: str) -> Dict[str, Any]:
    """
    추천인 통계 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        통계 딕셔너리 (total_referrals, total_rewards 등)
    """
    try:
        supabase = get_supabase_client()
        
        # RPC 함수 호출
        result = supabase.rpc(
            'get_referral_stats',
            {'p_user_id': user_id}
        ).execute()
        
        if result.data:
            return result.data
        else:
            return {
                'total_referrals': 0,
                'total_rewards': 0,
                'average_reward': 0
            }
            
    except Exception as e:
        return {
            'total_referrals': 0,
            'total_rewards': 0,
            'average_reward': 0
        }


# ═══════════════════════════════════════════════════════════════════════════
# [4] UI 렌더링 함수
# ═══════════════════════════════════════════════════════════════════════════

def render_referral_rewards_section(user_id: str) -> None:
    """
    추천인 리워드 현황 섹션 렌더링
    
    Args:
        user_id: 사용자 ID
    """
    st.markdown("### 🎁 나의 추천인 리워드 현황")
    
    # 통계 조회
    stats = get_referral_stats(user_id)
    
    # 통계 요약
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 추천 인원", f"{stats.get('total_referrals', 0)}명")
    with col2:
        st.metric("총 받은 보상", f"{stats.get('total_rewards', 0)} 🪙")
    with col3:
        st.metric("1인당 평균", f"{stats.get('average_reward', 0)} 🪙")
    
    # 리워드 내역 조회
    rewards = get_referral_rewards_history(user_id)
    
    if not rewards:
        st.info("📭 아직 추천인 보상 내역이 없습니다.")
        st.markdown(
            "<div style='background:#fffbeb;border:1px solid #fbbf24;border-radius:8px;"
            "padding:14px 18px;margin-top:12px;'>"
            "<div style='font-size:0.9rem;color:#92400e;line-height:1.6;'>"
            "💡 <b>친구를 초대하고 보상을 받으세요!</b><br>"
            "친구가 가입하고 7일이 지나면 <b>+100코인</b>을 드립니다."
            "</div></div>",
            unsafe_allow_html=True
        )
        return
    
    # 데이터프레임 변환
    df_data = []
    for record in rewards:
        # 가입한 친구 이름 추출 (reason에서 파싱)
        reason = record.get("reason", "")
        friend_name = "알 수 없음"
        
        if "추천인 보상:" in reason:
            try:
                friend_name = reason.split("추천인 보상:")[1].split("님")[0].strip()
                # 이름 마스킹 (첫 글자만 표시)
                if len(friend_name) > 1:
                    friend_name = friend_name[0] + "*" * (len(friend_name) - 1)
            except:
                pass
        
        df_data.append({
            "지급 일자": datetime.fromisoformat(
                record["created_at"].replace("Z", "+00:00")
            ).strftime("%Y-%m-%d"),
            "가입한 친구": friend_name,
            "지급 코인": f"+{record.get('amount', 0)} 🪙",
            "당시 잔액": f"{record.get('balance_after', 0)} 🪙"
        })
    
    df = pd.DataFrame(df_data)
    
    # 테이블 표시
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "지급 일자": st.column_config.TextColumn("지급 일자", width="medium"),
            "가입한 친구": st.column_config.TextColumn("가입한 친구", width="medium"),
            "지급 코인": st.column_config.TextColumn("지급 코인", width="small"),
            "당시 잔액": st.column_config.TextColumn("당시 잔액", width="small")
        }
    )


def render_subscription_extension_section(user_id: str) -> None:
    """
    코인으로 구독 연장 섹션 렌더링
    
    Args:
        user_id: 사용자 ID
    """
    st.markdown("### 🪙 코인으로 구독 기간 연장")
    
    # 현재 사용자 정보 조회
    try:
        supabase = get_supabase_client()
        result = supabase.table("gk_members").select(
            "current_credits, subscription_plan, monthly_renewal_date"
        ).eq("id", user_id).execute()
        
        if not result.data:
            st.error("⚠️ 사용자 정보를 찾을 수 없습니다.")
            return
        
        member = result.data[0]
        current_credits = member.get("current_credits", 0)
        plan = member.get("subscription_plan", "basic").lower()
        renewal_date = member.get("monthly_renewal_date")
        
        # 플랜별 필요 코인
        required_coins = 120 if plan == "basic" else 360
        
        # 안내 박스
        st.markdown(
            f"<div style='background:#f0f9ff;border:2px solid #0ea5e9;border-radius:8px;"
            f"padding:14px 18px;margin-bottom:16px;'>"
            f"<div style='font-size:0.9rem;color:#0c4a6e;line-height:1.6;'>"
            f"💡 <b>현재 보유 코인:</b> {current_credits} 🪙<br>"
            f"💡 <b>필요 코인:</b> {required_coins} 🪙 ({plan.upper()} 플랜 1개월 연장)<br>"
            f"💡 <b>다음 갱신일:</b> {renewal_date[:10] if renewal_date else '미설정'}"
            f"</div></div>",
            unsafe_allow_html=True
        )
        
        # 코인 부족 시 경고
        if current_credits < required_coins:
            st.warning(
                f"⚠️ 코인이 부족합니다. {required_coins - current_credits} 🪙 더 필요합니다."
            )
            st.info("💳 코인을 충전하거나 친구를 초대하여 보상을 받으세요!")
            return
        
        # 연장 버튼
        if st.button(
            f"🪙 {required_coins}코인으로 1개월 연장하기",
            type="primary",
            use_container_width=True,
            key="extend_subscription_btn"
        ):
            # 확인 팝업
            with st.spinner("구독 기간 연장 중..."):
                result = extend_subscription_with_coins(user_id, plan)
                
                if result.get('success'):
                    # 세션 상태 업데이트
                    st.session_state['current_credits'] = result.get('new_balance', 0)
                    
                    # 축하 메시지
                    st.balloons()
                    st.success(
                        f"✅ 코인 결제로 구독 기간이 1개월 연장되었습니다!\n\n"
                        f"• 차감된 코인: {result.get('coins_deducted', 0)} 🪙\n"
                        f"• 남은 코인: {result.get('new_balance', 0)} 🪙\n"
                        f"• 새로운 갱신일: {result.get('new_renewal_date', '')[:10]}"
                    )
                    
                    # 페이지 새로고침
                    st.rerun()
                else:
                    st.error(f"❌ 구독 연장 실패: {result.get('error', '알 수 없는 오류')}")
        
    except Exception as e:
        st.error(f"⚠️ 오류 발생: {str(e)}")


def render_referral_input(
    current_referrer_id: Optional[str] = None,
    user_id: Optional[str] = None,
    is_signup: bool = True
) -> Optional[str]:
    """
    추천인 입력란 렌더링
    
    Args:
        current_referrer_id: 현재 설정된 추천인 ID
        user_id: 사용자 ID (마이페이지에서 수정 시)
        is_signup: 가입 화면 여부
    
    Returns:
        입력된 추천인 ID
    """
    st.markdown(
        "<div style='background:#f0fdf4;border:1px solid #10b981;border-radius:8px;"
        "padding:12px 16px;margin:12px 0;'>"
        "<div style='font-size:0.85rem;color:#065f46;font-weight:600;margin-bottom:6px;'>"
        "🤝 나를 소개한 사람 (추천인)</div>"
        "<div style='font-size:0.75rem;color:#047857;line-height:1.5;'>"
        "추천인의 연락처 또는 추천 코드를 입력하시면, 가입 후 7일이 지나면 추천인에게 <b>+100코인</b>이 지급됩니다."
        "</div></div>",
        unsafe_allow_html=True
    )
    
    referrer_id = st.text_input(
        "추천인 연락처 또는 코드",
        value=current_referrer_id or "",
        placeholder="예: 010-1234-5678 또는 추천코드",
        key=f"referrer_input_{'signup' if is_signup else 'mypage'}",
        help="선택 사항입니다. 추천인이 없으면 비워두세요."
    )
    
    # 마이페이지에서 수정 시 저장 버튼
    if not is_signup and user_id:
        if st.button("💾 추천인 정보 저장", key="save_referrer_btn"):
            try:
                supabase = get_supabase_client()
                supabase.table("gk_members").update({
                    "referrer_id": referrer_id if referrer_id else None
                }).eq("id", user_id).execute()
                
                st.success("✅ 추천인 정보가 저장되었습니다!")
            except Exception as e:
                st.error(f"❌ 저장 실패: {str(e)}")
    
    return referrer_id if referrer_id else None
