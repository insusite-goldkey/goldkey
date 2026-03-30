# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] downgrade_ui.py
# GP 다운그레이드 예약 UI 모듈 - 마이페이지/구독 관리용
# 2026-03-30 신규 생성 - 유연한 다운그레이드 시스템
# ══════════════════════════════════════════════════════════════════════════════

import streamlit as st
from typing import Dict, Any
from modules.subscription_manager import schedule_downgrade, cancel_downgrade, check_and_renew_subscription
from db_utils import _get_sb


def render_downgrade_ui(user_id: str) -> None:
    """
    [GP-DOWNGRADE] 다운그레이드 예약 UI 렌더링.
    
    Args:
        user_id: 회원 ID
    """
    # 1. 현재 구독 상태 조회
    status = check_and_renew_subscription(user_id)
    
    if not status["is_active"]:
        st.warning("⚠️ 활성 구독이 없습니다. 다운그레이드는 활성 구독에서만 가능합니다.")
        return
    
    # 2. 회원 정보 조회
    sb = _get_sb()
    if not sb:
        st.error("❌ 데이터베이스 연결 실패")
        return
    
    try:
        result = sb.table('gk_members').select(
            'plan_type, next_plan_type, monthly_renewal_date, current_credits'
        ).eq('user_id', user_id).execute()
        
        if not result.data or len(result.data) == 0:
            st.error("❌ 회원 정보를 찾을 수 없습니다")
            return
        
        member = result.data[0]
        current_plan = member.get('plan_type', 'BASIC')
        next_plan = member.get('next_plan_type')
        renewal_date = member.get('monthly_renewal_date', '알 수 없음')
        current_credits = member.get('current_credits', 0)
        
    except Exception as e:
        st.error(f"❌ 회원 정보 조회 오류: {e}")
        return
    
    # 3. 현재 플랜 정보 표시
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#f0f9ff,#e0f2fe);"
        f"border:2px solid #0ea5e9;border-radius:12px;padding:16px;margin:12px 0;'>"
        f"<div style='font-size:1.05rem;font-weight:900;color:#0c4a6e;margin-bottom:8px;'>"
        f"📊 현재 구독 정보</div>"
        f"<div style='font-size:0.9rem;color:#075985;line-height:1.7;'>"
        f"• 현재 플랜: <b style='color:#0369a1;font-size:1.1rem;'>{current_plan}</b><br>"
        f"• 다음 갱신일: <b>{renewal_date}</b><br>"
        f"• 보유 코인: <b>{current_credits}🪙</b><br>"
        f"• 남은 기간: <b>{status.get('days_remaining', 0)}일</b></div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 4. 다운그레이드 예약 상태 확인
    if next_plan:
        # 이미 예약된 경우
        st.markdown(
            f"<div style='background:linear-gradient(135deg,#fef3c7,#fde68a);"
            f"border:2px solid #f59e0b;border-radius:12px;padding:16px;margin:12px 0;'>"
            f"<div style='font-size:1rem;font-weight:900;color:#92400e;margin-bottom:8px;'>"
            f"✅ 다운그레이드 예약 완료</div>"
            f"<div style='font-size:0.88rem;color:#78350f;line-height:1.7;'>"
            f"<b>{renewal_date}</b>까지는 <b style='color:#b45309;'>{current_plan} 플랜 혜택</b>이 유지되며,<br>"
            f"다음 결제일부터 <b style='color:#dc2626;'>{next_plan} 플랜</b>으로 자동 전환됩니다.<br><br>"
            f"<span style='font-size:0.82rem;color:#a16207;'>"
            f"💡 {next_plan} 플랜 월 구독료: <b>50🪙</b> (현재 보유: {current_credits}🪙)</span></div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # 예약 취소 버튼
        if st.button("🔄 다운그레이드 예약 취소", use_container_width=True, type="secondary"):
            result = cancel_downgrade(user_id)
            if result["success"]:
                st.success(f"✅ {result['message']}")
                st.rerun()
            else:
                st.error(f"❌ {result['message']}")
    
    else:
        # 예약되지 않은 경우
        if current_plan == "PRO":
            # PRO → BASIC 다운그레이드 가능
            st.markdown(
                "<div style='background:#fff;border:2px solid #e5e7eb;border-radius:12px;"
                "padding:16px;margin:12px 0;'>"
                "<div style='font-size:1rem;font-weight:900;color:#374151;margin-bottom:8px;'>"
                "💡 베이직 플랜으로 변경하시겠습니까?</div>"
                "<div style='font-size:0.88rem;color:#6b7280;line-height:1.7;'>"
                "베이직 플랜은 기본 상담 및 분석 기능을 제공하며, 월 구독료가 <b>50🪙</b>으로 저렴합니다.<br>"
                "다운그레이드를 예약하시면 <b>현재 갱신일까지 PRO 혜택이 유지</b>되며, "
                "다음 결제일부터 자동으로 베이직 플랜으로 전환됩니다.</div>"
                "</div>",
                unsafe_allow_html=True
            )
            
            # 다운그레이드 예약 버튼
            if st.button("⬇️ 베이직 플랜으로 변경 예약", use_container_width=True, type="primary"):
                result = schedule_downgrade(user_id, target_plan="BASIC")
                if result["success"]:
                    st.success(
                        f"✅ **{result['message']}**\n\n"
                        f"• 현재 플랜: {result['current_plan']}\n"
                        f"• 전환 예정: {result['target_plan']}\n"
                        f"• 적용일: {result['renewal_date']}\n\n"
                        f"💡 {result['renewal_date']}까지는 PRO 플랜 혜택이 계속 유지됩니다."
                    )
                    st.rerun()
                else:
                    st.error(f"❌ {result['message']}")
        
        elif current_plan == "BASIC":
            st.info("ℹ️ 현재 베이직 플랜을 사용 중입니다. PRO 플랜으로 업그레이드하시겠습니까?")


def render_legacy_report_badge() -> None:
    """
    [GP-DOWNGRADE] 과거 PRO 시절 생성한 리포트 배지 렌더링.
    """
    st.markdown(
        "<span style='background:linear-gradient(135deg,#dbeafe,#bfdbfe);"
        "color:#1e40af;padding:3px 10px;border-radius:6px;font-size:0.75rem;"
        "font-weight:700;margin-left:6px;border:1px solid #93c5fd;'>"
        "🔓 과거 PRO 리포트 (0🪙 무료 조회)</span>",
        unsafe_allow_html=True
    )


def check_and_show_legacy_access(user_id: str, report_id: str) -> bool:
    """
    [GP-DOWNGRADE] 과거 리포트 접근 권한 확인 및 안내 표시.
    
    Args:
        user_id: 회원 ID
        report_id: 리포트 ID
        
    Returns:
        True: 접근 가능
        False: 접근 불가
    """
    from modules.access_control import check_access
    
    # STEP 7~9는 PRO 전용 (리포트 조회)
    access = check_access(user_id, step_number=7, report_id=report_id)
    
    if access["allowed"]:
        if access.get("legacy_access"):
            # 과거 PRO 시절 리포트 무료 조회
            st.info(
                "ℹ️ **과거 PRO 시절 생성한 리포트입니다**\n\n"
                "베이직 플랜으로 전환하셨지만, PRO 시절 생성한 리포트는 "
                "**0코인 무료 조회**가 가능합니다. 자산이 보존됩니다! 🎉"
            )
        return True
    else:
        if access.get("upgrade_required"):
            st.warning(
                "⚠️ **PRO 플랜 전용 리포트입니다**\n\n"
                "이 리포트를 조회하려면 PRO 플랜으로 업그레이드해 주세요."
            )
        return False
