"""
[GP-제88조] 월간 구독 자동 갱신 로직 (Lazy Evaluation)
Goldkey AI Masters 2026 - 로그인 시 자동 검증 및 만료 처리
"""
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from db_utils import _get_sb


# ──────────────────────────────────────────────────────────────────────────
# [§1] 월간 갱신일 검증 (Lazy Check)
# ──────────────────────────────────────────────────────────────────────────

def check_and_renew_subscription(user_id: str) -> Dict[str, Any]:
    """
    사용자 로그인 시 월간 갱신일(monthly_renewal_date)을 검증하고,
    만료된 경우 subscription_status를 'expired'로 변경.
    [GP-DOWNGRADE] next_plan_type이 있으면 갱신 시 자동 전환.
    
    Args:
        user_id: 회원 ID
        
    Returns:
        {
            "is_active": bool,
            "status": str,
            "renewal_date": str,
            "days_remaining": int,
            "message": str,
            "next_plan_type": str (optional)
        }
    """
    sb = _get_sb()
    if not sb:
        return {
            "is_active": False,
            "status": "error",
            "renewal_date": None,
            "days_remaining": 0,
            "message": "데이터베이스 연결 실패"
        }
    
    try:
        # 1. 회원 정보 조회 (next_plan_type 추가)
        result = sb.table('gk_members').select(
            'subscription_status, monthly_renewal_date, current_credits, plan_type, next_plan_type'
        ).eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return {
                "is_active": False,
                "status": "not_found",
                "renewal_date": None,
                "days_remaining": 0,
                "message": "회원 정보를 찾을 수 없습니다"
            }
        
        member = result.data[0]
        current_status = member.get('subscription_status', 'inactive')
        renewal_date_str = member.get('monthly_renewal_date')
        current_credits = member.get('current_credits', 0)
        plan_type = member.get('plan_type', 'BASIC')
        next_plan_type = member.get('next_plan_type')  # 다운그레이드 예약
        
        # 2. 갱신일이 없는 경우 (신규 회원 또는 무료 회원)
        if not renewal_date_str:
            # BETA 회원은 갱신일 자동 설정 (30일 후)
            if current_status == 'BETA':
                new_renewal_date = datetime.now() + timedelta(days=30)
                sb.table('gk_members').update({
                    'monthly_renewal_date': new_renewal_date.strftime('%Y-%m-%d')
                }).eq('user_id', user_id).execute()
                
                return {
                    "is_active": True,
                    "status": "BETA",
                    "renewal_date": new_renewal_date.strftime('%Y-%m-%d'),
                    "days_remaining": 30,
                    "message": "BETA 회원 — 30일 무료 체험 중"
                }
            
            return {
                "is_active": current_credits > 0,
                "status": current_status,
                "renewal_date": None,
                "days_remaining": 0,
                "message": "무료 회원 (코인 잔액으로만 이용 가능)"
            }
        
        # 3. 갱신일 파싱
        renewal_date = datetime.strptime(renewal_date_str, '%Y-%m-%d')
        today = datetime.now()
        days_remaining = (renewal_date - today).days
        
        # 4. 갱신일이 지났는지 확인
        if today > renewal_date:
            # 4-1. [GP-DOWNGRADE] next_plan_type이 있으면 플랜 전환 처리
            if next_plan_type:
                new_plan = next_plan_type
                coin_cost = 50 if new_plan == 'BASIC' else 150  # BASIC=50, PRO=150
                
                if current_credits >= coin_cost:
                    # 코인 차감 후 플랜 전환
                    new_credits = current_credits - coin_cost
                    new_renewal = today + timedelta(days=30)
                    
                    sb.table('gk_members').update({
                        'plan_type': new_plan,
                        'next_plan_type': None,  # 예약 해제
                        'subscription_status': 'active',
                        'monthly_renewal_date': new_renewal.strftime('%Y-%m-%d'),
                        'current_credits': new_credits,
                        'updated_at': 'NOW()'
                    }).eq('user_id', user_id).execute()
                    
                    # 플랜 전환 내역 기록
                    sb.table('gk_credit_history').insert({
                        'user_id': user_id,
                        'action_type': 'PLAN_CHANGED',
                        'amount': -coin_cost,
                        'balance_after': new_credits,
                        'description': f'{plan_type} → {new_plan} 플랜 전환 (예약 다운그레이드)'
                    }).execute()
                    
                    return {
                        "is_active": True,
                        "status": "active",
                        "renewal_date": new_renewal.strftime('%Y-%m-%d'),
                        "days_remaining": 30,
                        "message": f"플랜 전환 완료: {plan_type} → {new_plan} ({coin_cost}코인 차감)"
                    }
                else:
                    # 코인 부족 시 만료 처리
                    sb.table('gk_members').update({
                        'subscription_status': 'expired',
                        'next_plan_type': None,
                        'updated_at': 'NOW()'
                    }).eq('user_id', user_id).execute()
                    
                    return {
                        "is_active": False,
                        "status": "expired",
                        "renewal_date": renewal_date_str,
                        "days_remaining": days_remaining,
                        "message": f"플랜 전환 실패: 코인 부족 (필요: {coin_cost}, 보유: {current_credits})"
                    }
            
            # 4-2. 일반 구독 만료 처리
            if current_status == 'active':
                sb.table('gk_members').update({
                    'subscription_status': 'expired',
                    'updated_at': 'NOW()'
                }).eq('user_id', user_id).execute()
                
                # 만료 내역 기록
                sb.table('gk_credit_history').insert({
                    'user_id': user_id,
                    'action_type': 'SUBSCRIPTION_EXPIRED',
                    'amount': 0,
                    'balance_after': current_credits,
                    'description': f'월간 구독 만료 (갱신일: {renewal_date_str})'
                }).execute()
                
                return {
                    "is_active": False,
                    "status": "expired",
                    "renewal_date": renewal_date_str,
                    "days_remaining": days_remaining,
                    "message": f"구독이 만료되었습니다 ({abs(days_remaining)}일 경과)"
                }
            
            # 4-3. 이미 만료 상태인 경우
            return {
                "is_active": current_credits > 0,
                "status": "expired",
                "renewal_date": renewal_date_str,
                "days_remaining": days_remaining,
                "message": f"구독 만료 ({abs(days_remaining)}일 경과) — 코인 잔액: {current_credits}",
                "next_plan_type": next_plan_type
            }
        
        # 5. 갱신일이 아직 남은 경우
        result = {
            "is_active": True,
            "status": current_status,
            "renewal_date": renewal_date_str,
            "days_remaining": days_remaining,
            "message": f"구독 활성 (갱신일까지 {days_remaining}일 남음)"
        }
        
        # [GP-DOWNGRADE] 다운그레이드 예약 정보 추가
        if next_plan_type:
            result["next_plan_type"] = next_plan_type
            result["message"] += f" | 예약: {plan_type} → {next_plan_type}"
        
        return result
        
    except Exception as e:
        print(f"[SUBSCRIPTION] 갱신일 검증 오류: {e}")
        return {
            "is_active": False,
            "status": "error",
            "renewal_date": None,
            "days_remaining": 0,
            "message": f"검증 오류: {str(e)}"
        }


# ──────────────────────────────────────────────────────────────────────────
# [§1-B] 다운그레이드 예약 (Scheduled Downgrade)
# ──────────────────────────────────────────────────────────────────────────

def schedule_downgrade(user_id: str, target_plan: str = "BASIC") -> Dict[str, Any]:
    """
    [GP-DOWNGRADE] 플랜 다운그레이드 예약.
    즉시 권한을 뺏지 않고, 다음 갱신일부터 적용.
    
    Args:
        user_id: 회원 ID
        target_plan: 목표 플랜 (BASIC/PRO)
        
    Returns:
        {"success": bool, "renewal_date": str, "message": str}
    """
    sb = _get_sb()
    if not sb:
        return {"success": False, "renewal_date": None, "message": "DB 연결 실패"}
    
    try:
        # 1. 현재 회원 정보 조회
        result = sb.table('gk_members').select(
            'plan_type, monthly_renewal_date, subscription_status'
        ).eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return {"success": False, "renewal_date": None, "message": "회원 정보 없음"}
        
        member = result.data[0]
        current_plan = member.get('plan_type', 'BASIC')
        renewal_date = member.get('monthly_renewal_date')
        status = member.get('subscription_status', 'inactive')
        
        # 2. 유효성 검증
        if current_plan == target_plan:
            return {
                "success": False,
                "renewal_date": renewal_date,
                "message": f"이미 {target_plan} 플랜입니다"
            }
        
        if status != 'active':
            return {
                "success": False,
                "renewal_date": renewal_date,
                "message": "활성 구독만 다운그레이드 예약 가능합니다"
            }
        
        # 3. next_plan_type 업데이트
        sb.table('gk_members').update({
            'next_plan_type': target_plan,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 4. 예약 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'PLAN_DOWNGRADE_SCHEDULED',
            'amount': 0,
            'balance_after': 0,
            'description': f'{current_plan} → {target_plan} 다운그레이드 예약 (적용일: {renewal_date})'
        }).execute()
        
        return {
            "success": True,
            "renewal_date": renewal_date,
            "current_plan": current_plan,
            "target_plan": target_plan,
            "message": f"예약 완료: {renewal_date}까지 {current_plan} 유지 → 다음 결제일부터 {target_plan} 전환"
        }
        
    except Exception as e:
        print(f"[SUBSCRIPTION] 다운그레이드 예약 오류: {e}")
        return {"success": False, "renewal_date": None, "message": f"예약 실패: {str(e)}"}


def cancel_downgrade(user_id: str) -> Dict[str, Any]:
    """
    [GP-DOWNGRADE] 다운그레이드 예약 취소.
    
    Args:
        user_id: 회원 ID
        
    Returns:
        {"success": bool, "message": str}
    """
    sb = _get_sb()
    if not sb:
        return {"success": False, "message": "DB 연결 실패"}
    
    try:
        # next_plan_type을 NULL로 설정
        sb.table('gk_members').update({
            'next_plan_type': None,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 취소 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'PLAN_DOWNGRADE_CANCELLED',
            'amount': 0,
            'balance_after': 0,
            'description': '다운그레이드 예약 취소'
        }).execute()
        
        return {
            "success": True,
            "message": "다운그레이드 예약이 취소되었습니다"
        }
        
    except Exception as e:
        print(f"[SUBSCRIPTION] 예약 취소 오류: {e}")
        return {"success": False, "message": f"취소 실패: {str(e)}"}


# ──────────────────────────────────────────────────────────────────────────
# [§2] 구독 갱신 처리 (결제 완료 시)
# ──────────────────────────────────────────────────────────────────────────

def renew_subscription(
    user_id: str,
    plan_type: str = "PRO",
    duration_days: int = 30,
    bonus_credits: int = 0
) -> Dict[str, Any]:
    """
    구독 갱신 처리 (결제 완료 시 호출).
    
    Args:
        user_id: 회원 ID
        plan_type: 플랜 유형 (BASIC/PRO)
        duration_days: 연장 기간 (일)
        bonus_credits: 보너스 코인 (선택)
        
    Returns:
        {"success": bool, "new_renewal_date": str, "message": str}
    """
    sb = _get_sb()
    if not sb:
        return {"success": False, "new_renewal_date": None, "message": "DB 연결 실패"}
    
    try:
        # 1. 현재 갱신일 조회
        result = sb.table('gk_members').select(
            'monthly_renewal_date, current_credits'
        ).eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            return {"success": False, "new_renewal_date": None, "message": "회원 정보 없음"}
        
        member = result.data[0]
        current_renewal_str = member.get('monthly_renewal_date')
        current_credits = member.get('current_credits', 0)
        
        # 2. 새 갱신일 계산
        if current_renewal_str:
            current_renewal = datetime.strptime(current_renewal_str, '%Y-%m-%d')
            # 현재 갱신일이 미래인 경우 → 그 날짜부터 연장
            if current_renewal > datetime.now():
                new_renewal_date = current_renewal + timedelta(days=duration_days)
            else:
                # 이미 만료된 경우 → 오늘부터 연장
                new_renewal_date = datetime.now() + timedelta(days=duration_days)
        else:
            # 갱신일이 없는 경우 → 오늘부터 연장
            new_renewal_date = datetime.now() + timedelta(days=duration_days)
        
        new_renewal_str = new_renewal_date.strftime('%Y-%m-%d')
        
        # 3. DB 업데이트
        new_credits = current_credits + bonus_credits
        sb.table('gk_members').update({
            'subscription_status': 'active',
            'monthly_renewal_date': new_renewal_str,
            'plan_type': plan_type,
            'current_credits': new_credits,
            'updated_at': 'NOW()'
        }).eq('user_id', user_id).execute()
        
        # 4. 갱신 내역 기록
        sb.table('gk_credit_history').insert({
            'user_id': user_id,
            'action_type': 'SUBSCRIPTION_RENEWED',
            'amount': bonus_credits,
            'balance_after': new_credits,
            'description': f'{plan_type} 플랜 {duration_days}일 갱신 (보너스: {bonus_credits}코인)'
        }).execute()
        
        return {
            "success": True,
            "new_renewal_date": new_renewal_str,
            "message": f"구독 갱신 완료 (다음 갱신일: {new_renewal_str})"
        }
        
    except Exception as e:
        print(f"[SUBSCRIPTION] 갱신 처리 오류: {e}")
        return {"success": False, "new_renewal_date": None, "message": f"갱신 실패: {str(e)}"}


# ──────────────────────────────────────────────────────────────────────────
# [§3] 구독 상태 UI 렌더링
# ──────────────────────────────────────────────────────────────────────────

def render_subscription_status_banner(user_id: str) -> None:
    """
    구독 상태를 상단 배너로 표시.
    
    Args:
        user_id: 회원 ID
    """
    status = check_and_renew_subscription(user_id)
    
    if not status["is_active"]:
        # 만료 또는 비활성 상태
        if status["status"] == "expired":
            st.warning(
                f"⚠️ **구독이 만료되었습니다** ({abs(status['days_remaining'])}일 경과)\n\n"
                f"• 다음 갱신일: {status['renewal_date']}\n"
                f"• 현재 상태: 만료\n\n"
                f"플랜을 업그레이드하거나 코인을 충전해 주세요."
            )
        elif status["status"] == "error":
            st.error(f"❌ {status['message']}")
    else:
        # 활성 상태
        if status["days_remaining"] <= 7:
            # 갱신일 7일 이내 경고
            st.info(
                f"ℹ️ **구독 갱신일이 다가옵니다**\n\n"
                f"• 다음 갱신일: {status['renewal_date']}\n"
                f"• 남은 기간: {status['days_remaining']}일\n\n"
                f"자동 갱신이 설정되어 있지 않다면 미리 결제해 주세요."
            )


# ──────────────────────────────────────────────────────────────────────────
# [§4] 세션 상태 동기화
# ──────────────────────────────────────────────────────────────────────────

def sync_subscription_to_session(user_id: str) -> None:
    """
    구독 상태를 세션 상태에 동기화.
    
    Args:
        user_id: 회원 ID
    """
    status = check_and_renew_subscription(user_id)
    
    st.session_state['subscription_status'] = status['status']
    st.session_state['subscription_is_active'] = status['is_active']
    st.session_state['subscription_renewal_date'] = status['renewal_date']
    st.session_state['subscription_days_remaining'] = status['days_remaining']
