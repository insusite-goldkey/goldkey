"""
[GP-TRUST] 마이페이지 및 사용자 신뢰 구축 UI 모듈
- 플랜 뱃지
- 구독 관리
- 크레딧 사용 내역
- 결제 완료 항목 표기
- 추천인 리워드 현황
- 코인으로 구독 연장
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    from modules.db_utils import get_supabase_client
except ImportError:
    from db_utils import get_supabase_client

try:
    from modules.referral_system import (
        render_referral_rewards_section,
        render_subscription_extension_section,
        render_referral_input
    )
    _REFERRAL_OK = True
except ImportError:
    _REFERRAL_OK = False


# ═══════════════════════════════════════════════════════════════════════════
# [1] 플랜 및 잔여 코인 상시 노출 뱃지
# ═══════════════════════════════════════════════════════════════════════════

def render_plan_badge(user_id: str) -> None:
    """
    사이드바 상단에 플랜 및 잔여 코인 뱃지 렌더링
    
    Args:
        user_id: 사용자 ID
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("gk_members").select("current_credits, subscription_plan").eq("id", user_id).execute()
        
        if not result.data:
            return
        
        member = result.data[0]
        credits = member.get("current_credits", 0)
        plan = member.get("subscription_plan", "basic").lower()
        
        # 플랜별 뱃지 스타일
        if plan == "pro":
            badge_icon = "👑"
            badge_text = "PRO 플랜"
            badge_color = "#fbbf24"
            text_color = "#92400e"
        else:
            badge_icon = "🟢"
            badge_text = "BASIC 플랜"
            badge_color = "#60a5fa"
            text_color = "#1e40af"
        
        st.sidebar.markdown(
            f"<div style='background:linear-gradient(135deg,{badge_color}22,{badge_color}11);"
            f"border:2px solid {badge_color};border-radius:12px;padding:12px 16px;"
            f"margin:8px 0 16px 0;text-align:center;'>"
            f"<div style='font-size:0.95rem;font-weight:700;color:{text_color};margin-bottom:6px;'>"
            f"{badge_icon} {badge_text}</div>"
            f"<div style='font-size:1.1rem;font-weight:900;color:#0a1628;'>"
            f"잔여: 🪙 {credits}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.sidebar.error(f"⚠️ 플랜 정보 로드 실패: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# [2] 마이페이지 - 구독 관리
# ═══════════════════════════════════════════════════════════════════════════

def render_subscription_management(user_id: str = None) -> None:
    """
    구독 관리 섹션 렌더링 (구독 해지 버튼 + 코인으로 연장 포함)
    
    Args:
        user_id: 사용자 ID (코인 연장 기능용)
    """
    st.markdown("### ⚙️ 구독 관리")
    
    # [GP-VIRAL] 코인으로 구독 연장 섹션
    if _REFERRAL_OK and user_id:
        render_subscription_extension_section(user_id)
        st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)
    
    st.markdown(
        "<div style='background:#fff3cd;border:1px solid #f0a500;border-radius:8px;"
        "padding:14px 18px;margin-bottom:16px;'>"
        "<div style='font-size:0.9rem;color:#7a4f00;line-height:1.6;'>"
        "📌 <b>구독 해지 안내</b><br>"
        "구독 해지는 구글 플레이 스토어에서 안전하게 진행됩니다.<br>"
        "해지 후에도 현재 결제 주기 종료일까지는 정상 이용 가능합니다."
        "</div></div>",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🚫 정기 구독 해지하기", type="secondary", use_container_width=True):
            # 구글 플레이 스토어 구독 관리 페이지 URL
            play_store_url = "https://play.google.com/store/account/subscriptions"
            st.markdown(
                f"<script>window.open('{play_store_url}', '_blank');</script>",
                unsafe_allow_html=True
            )
            st.info("🔗 구글 플레이 스토어 구독 관리 페이지가 새 창에서 열립니다.")
    
    with col2:
        if st.button("💳 플랜 업그레이드", type="primary", use_container_width=True):
            st.info("💡 플랜 업그레이드는 구글 플레이 스토어에서 진행해주세요.")


# ═══════════════════════════════════════════════════════════════════════════
# [3] 크레딧 사용 내역 조회
# ═══════════════════════════════════════════════════════════════════════════

def get_credit_history(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    크레딧 사용 내역 조회
    
    Args:
        user_id: 사용자 ID
        start_date: 시작 날짜
        end_date: 종료 날짜
        transaction_type: 거래 유형 (DEDUCT, GRANT, REFUND)
    
    Returns:
        크레딧 내역 리스트
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("gk_credit_history").select("*").eq("user_id", user_id).order("created_at", desc=True)
        
        if start_date:
            query = query.gte("created_at", start_date.isoformat())
        if end_date:
            query = query.lte("created_at", end_date.isoformat())
        if transaction_type and transaction_type != "전체":
            query = query.eq("transaction_type", transaction_type)
        
        result = query.execute()
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"⚠️ 크레딧 내역 조회 실패: {str(e)}")
        return []


def render_credit_history_table(user_id: str) -> None:
    """
    크레딧 사용 내역 테이블 렌더링
    
    Args:
        user_id: 사용자 ID
    """
    st.markdown("### 💰 크레딧 사용 내역")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        start_date = st.date_input(
            "시작 날짜",
            value=datetime.now() - timedelta(days=30),
            key="credit_history_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "종료 날짜",
            value=datetime.now(),
            key="credit_history_end_date"
        )
    
    with col3:
        transaction_type = st.selectbox(
            "유형",
            ["전체", "DEDUCT", "GRANT", "REFUND"],
            key="credit_history_type"
        )
    
    # 데이터 조회
    history = get_credit_history(
        user_id,
        datetime.combine(start_date, datetime.min.time()),
        datetime.combine(end_date, datetime.max.time()),
        transaction_type
    )
    
    if not history:
        st.info("📭 조회된 내역이 없습니다.")
        return
    
    # 데이터프레임 변환
    df_data = []
    for record in history:
        transaction_type_kr = {
            "DEDUCT": "🔻 차감",
            "GRANT": "🔺 충전",
            "REFUND": "↩️ 환불"
        }.get(record.get("transaction_type", ""), record.get("transaction_type", ""))
        
        df_data.append({
            "일시": datetime.fromisoformat(record["created_at"].replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M"),
            "유형": transaction_type_kr,
            "코인": record.get("amount", 0),
            "잔여": record.get("balance_after", 0),
            "상세 내용": record.get("reason", "-")
        })
    
    df = pd.DataFrame(df_data)
    
    # 스타일링된 테이블 표시
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "일시": st.column_config.TextColumn("일시", width="medium"),
            "유형": st.column_config.TextColumn("유형", width="small"),
            "코인": st.column_config.NumberColumn("코인", format="%d 🪙"),
            "잔여": st.column_config.NumberColumn("잔여", format="%d 🪙"),
            "상세 내용": st.column_config.TextColumn("상세 내용", width="large")
        }
    )
    
    # 통계 요약
    total_deduct = sum(r.get("amount", 0) for r in history if r.get("transaction_type") == "DEDUCT")
    total_grant = sum(r.get("amount", 0) for r in history if r.get("transaction_type") == "GRANT")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 차감", f"{total_deduct} 🪙")
    with col2:
        st.metric("총 충전", f"{total_grant} 🪙")
    with col3:
        st.metric("순 변동", f"{total_grant - total_deduct:+d} 🪙")


# ═══════════════════════════════════════════════════════════════════════════
# [4] 결제 완료 항목 시각적 표기
# ═══════════════════════════════════════════════════════════════════════════

def get_paid_analysis_list(person_id: str, agent_id: str) -> List[Dict[str, Any]]:
    """
    특정 고객의 결제 완료된 분석 항목 조회
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
    
    Returns:
        결제 완료 분석 항목 리스트
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("analysis_reports").select("*").eq("person_id", person_id).eq("agent_id", agent_id).order("created_at", desc=True).execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        st.error(f"⚠️ 분석 내역 조회 실패: {str(e)}")
        return []


def render_paid_analysis_badge(analysis_type: str, created_at: str, coins_used: int) -> str:
    """
    결제 완료 항목 뱃지 HTML 생성
    
    Args:
        analysis_type: 분석 유형
        created_at: 생성 일시
        coins_used: 사용된 코인
    
    Returns:
        HTML 문자열
    """
    analysis_type_kr = {
        "SCAN": "증권 스캔",
        "TRINITY": "AI 트리니티 분석",
        "AI_STRATEGY": "에이젠틱 AI 전략",
        "KAKAO_MESSAGE": "카카오톡 멘트",
        "EMOTIONAL_PROPOSAL": "감성 제안서",
        "TABLE_3STEP": "3단 일람표",
        "AI_TARGETING": "AI 타겟팅",
        "COMPARISON_STRATEGY": "비교 전략",
        "NIBO_ANALYSIS": "내보험다보여 분석",
        "MEDICAL_RECORD": "진료기록 분석",
        "ACCIDENT_REPORT": "사고 보고서"
    }.get(analysis_type, analysis_type)
    
    date_str = datetime.fromisoformat(created_at.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")
    
    return (
        f"<div style='display:inline-block;margin:4px 0;'>"
        f"<span style='text-decoration:underline;text-decoration-thickness:2px;"
        f"text-decoration-color:#10b981;font-weight:600;color:#0a1628;'>"
        f"{analysis_type_kr}</span> "
        f"<span style='background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:4px;"
        f"font-size:0.75rem;font-weight:700;margin-left:6px;'>"
        f"✅ 결제완료: 무료열람 ({coins_used}🪙)</span> "
        f"<span style='color:#6b7280;font-size:0.8rem;margin-left:6px;'>{date_str}</span>"
        f"</div>"
    )


def render_paid_analysis_list(person_id: str, agent_id: str) -> None:
    """
    고객 상세 페이지에 결제 완료 항목 리스트 렌더링
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
    """
    paid_items = get_paid_analysis_list(person_id, agent_id)
    
    if not paid_items:
        st.info("📭 아직 결제된 분석 항목이 없습니다.")
        return
    
    st.markdown("### 📋 결제 완료 항목 (무료 열람 가능)")
    
    for item in paid_items:
        badge_html = render_paid_analysis_badge(
            item.get("analysis_type", ""),
            item.get("created_at", ""),
            item.get("coins_used", 0)
        )
        
        st.markdown(badge_html, unsafe_allow_html=True)
        
        # 클릭 시 모달 표시
        if st.button(f"📄 열람하기", key=f"view_{item['id']}", type="secondary"):
            st.session_state[f"show_modal_{item['id']}"] = True
        
        # 모달 렌더링
        if st.session_state.get(f"show_modal_{item['id']}", False):
            render_analysis_modal(item)


# ═══════════════════════════════════════════════════════════════════════════
# [5] 무료 열람 모달
# ═══════════════════════════════════════════════════════════════════════════

def render_analysis_modal(analysis_data: Dict[str, Any]) -> None:
    """
    분석 결과 모달 렌더링
    
    Args:
        analysis_data: 분석 데이터
    """
    analysis_type_kr = {
        "SCAN": "증권 스캔",
        "TRINITY": "AI 트리니티 분석",
        "AI_STRATEGY": "에이젠틱 AI 전략",
        "KAKAO_MESSAGE": "카카오톡 멘트",
        "EMOTIONAL_PROPOSAL": "감성 제안서",
        "TABLE_3STEP": "3단 일람표"
    }.get(analysis_data.get("analysis_type", ""), analysis_data.get("analysis_type", ""))
    
    with st.expander(f"📄 {analysis_type_kr} 결과 (무료 열람)", expanded=True):
        st.markdown(
            "<div style='background:#f0fdf4;border:2px solid #10b981;border-radius:8px;"
            "padding:16px;margin-bottom:12px;'>"
            "<div style='font-size:0.85rem;color:#065f46;font-weight:600;margin-bottom:8px;'>"
            "✅ 이 분석은 이미 코인이 차감되어 저장된 결과입니다. 무료로 열람하실 수 있습니다."
            "</div></div>",
            unsafe_allow_html=True
        )
        
        result_data = analysis_data.get("result_data", {})
        
        # JSON 데이터를 보기 좋게 표시
        if isinstance(result_data, dict):
            for key, value in result_data.items():
                st.markdown(f"**{key}:**")
                if isinstance(value, (dict, list)):
                    st.json(value)
                else:
                    st.write(value)
        else:
            st.json(result_data)
        
        if st.button("닫기", key=f"close_modal_{analysis_data['id']}"):
            st.session_state[f"show_modal_{analysis_data['id']}"] = False
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════
# [통합] 마이페이지 메인 렌더링
# ═══════════════════════════════════════════════════════════════════════════

def render_mypage(user_id: str) -> None:
    """
    마이페이지 메인 화면 렌더링
    
    Args:
        user_id: 사용자 ID
    """
    st.title("⚙️ 마이페이지 / 구독 관리")
    
    # 탭 구성
    if _REFERRAL_OK:
        tab1, tab2, tab3 = st.tabs(["💰 크레딧 사용 내역", "🎁 추천인 리워드", "⚙️ 구독 관리"])
    else:
        tab1, tab2 = st.tabs(["💰 크레딧 사용 내역", "⚙️ 구독 관리"])
    
    with tab1:
        render_credit_history_table(user_id)
    
    if _REFERRAL_OK:
        with tab2:
            render_referral_rewards_section(user_id)
            
            # 추천인 정보 수정
            st.markdown("<hr style='border-top:1px solid #e5e7eb;margin:20px 0;'>", unsafe_allow_html=True)
            st.markdown("### 🤝 추천인 정보 수정")
            
            try:
                supabase = get_supabase_client()
                result = supabase.table("gk_members").select("referrer_id").eq("id", user_id).execute()
                current_referrer = result.data[0].get("referrer_id") if result.data else None
            except:
                current_referrer = None
            
            render_referral_input(current_referrer, user_id, is_signup=False)
        
        with tab3:
            render_subscription_management(user_id)
    else:
        with tab2:
            render_subscription_management(user_id)
