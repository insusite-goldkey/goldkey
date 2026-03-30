# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] access_control.py
# GP 권한 제어 엔진 - 12단계 마스터플랜 베이직/프로 등급 체계
# 2026-03-30 신규 생성 - 옵션 B 채택
# ══════════════════════════════════════════════════════════════════════════════

"""
[GP-MASTERPLAN] 권한 제어 시스템

핵심 논리:
"서버 비용(Cloud Run 토큰)이 적게 드는 실무 관리는 베이직, 고부하 AI 연산은 프로"

베이직(Basic) 플랜:
- STEP 1~6: 기본 상담 및 분석 (0~1🪙)
- STEP 10: 계약 등록 및 DB 저장 (0~1🪙)
- STEP 11 (부분): 스마트 스케줄러 - 달력 뷰 (0🪙)

프로(Pro) 플랜:
- STEP 7~9: AI 전략 수립 및 제안서 생성 (3🪙)
- STEP 11 (부분): AI 전략 브리핑 및 맞춤 작문 (3🪙)
- STEP 12: 리워드 기반 소개 확보 (3🪙)
"""

from typing import Literal, Optional, Dict, Any
import streamlit as st
from db_utils import _get_sb

# ══════════════════════════════════════════════════════════════════════════════
# [§1] STEP 권한 매핑 테이블
# ══════════════════════════════════════════════════════════════════════════════

STEP_ACCESS_MAP: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "고객상담 (상담신청)",
        "tier": "basic",
        "coins": 0,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "기본 정보 입력",
    },
    2: {
        "name": "개인정보 동의 및 인증",
        "tier": "basic",
        "coins": 0,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "셀프 힐링 포함",
    },
    3: {
        "name": "증권 및 의무기록 스캔",
        "tier": "basic",
        "coins": 1,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "OCR 데이터 추출",
    },
    4: {
        "name": "AI 트리니티 계산법",
        "tier": "basic",
        "coins": 1,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "건보료 역산 분석",
    },
    5: {
        "name": "KB 평균 가입금액 비교",
        "tier": "basic",
        "coins": 1,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "통계 기반 보장 분석",
    },
    6: {
        "name": "통합 보장 공백 진단",
        "tier": "basic",
        "coins": 1,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "분석 결과 리포트",
    },
    7: {
        "name": "에이젠틱 AI 전략 수립",
        "tier": "pro",
        "coins": 3,
        "badge": "[⭐PRO플랜]",
        "badge_color": "#f59e0b",
        "description": "고부하 AI 전략 연산",
    },
    8: {
        "name": "AI 감성 제안 및 작문",
        "tier": "pro",
        "coins": 3,
        "badge": "[⭐PRO플랜]",
        "badge_color": "#f59e0b",
        "description": "AI 페르소나 작문",
    },
    9: {
        "name": "1:1 맞춤 제안서 생성",
        "tier": "pro",
        "coins": 3,
        "badge": "[⭐PRO플랜]",
        "badge_color": "#f59e0b",
        "description": "리포트 정밀 렌더링",
    },
    10: {
        "name": "청약 진행 및 계약 등록",
        "tier": "basic",
        "coins": 1,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "데이터 요새(DB) 저장",
    },
    11: {
        "name": "지능형 계약 관리 (하이브리드)",
        "tier": "hybrid",
        "coins": 0,  # 베이직: 0🪙 (달력), 프로: 3🪙 (AI)
        "badge": "[하이브리드]",
        "badge_color": "#8b5cf6",
        "description": "베이직: 스마트 스케줄러 / 프로: AI 전략 브리핑",
    },
    12: {
        "name": "리워드 기반 소개 확보",
        "tier": "pro",
        "coins": 3,
        "badge": "[⭐PRO플랜]",
        "badge_color": "#f59e0b",
        "description": "리워드 시스템 운영",
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# [§2] 사용자 등급 확인
# ══════════════════════════════════════════════════════════════════════════════

def get_user_tier(user_id: str) -> Literal["basic", "pro"]:
    """
    사용자 등급 확인.
    
    Args:
        user_id: 회원 ID
        
    Returns:
        "basic" 또는 "pro"
    """
    sb = _get_sb()
    if not sb or not user_id:
        return "basic"
    
    try:
        resp = sb.table("gk_members").select("subscription_status, current_credits").eq("user_id", user_id).execute()
        if not resp.data:
            return "basic"
        
        member = resp.data[0]
        status = member.get("subscription_status", "")
        credits = member.get("current_credits", 0)
        
        # 프로 조건: 구독 활성 또는 150코인 이상 보유
        if status == "active" or credits >= 150:
            return "pro"
        
        return "basic"
    except Exception:
        return "basic"


# ══════════════════════════════════════════════════════════════════════════════
# [§3] 권한 검증
# ══════════════════════════════════════════════════════════════════════════════

def check_access(user_id: str, step_number: int, report_id: Optional[str] = None) -> Dict[str, Any]:
    """
    STEP 권한 검증.
    [GP-DOWNGRADE] 과거 PRO 시절 생성한 리포트는 베이직 전환 후에도 0코인 조회 가능.
    
    Args:
        user_id: 회원 ID
        step_number: STEP 번호 (1~12)
        report_id: 리포트 ID (과거 데이터 조회 시)
        
    Returns:
        {
            "allowed": bool,
            "tier": str,
            "step_info": dict,
            "user_tier": str,
            "upgrade_required": bool,
            "legacy_access": bool (과거 데이터 접근 여부)
        }
    """
    if step_number not in STEP_ACCESS_MAP:
        return {
            "allowed": False,
            "tier": "unknown",
            "step_info": {},
            "user_tier": "basic",
            "upgrade_required": False,
            "legacy_access": False,
            "error": "Invalid STEP number"
        }
    
    step_info = STEP_ACCESS_MAP[step_number]
    user_tier = get_user_tier(user_id)
    required_tier = step_info["tier"]
    
    # 하이브리드는 항상 허용 (내부에서 기능별 제어)
    if required_tier == "hybrid":
        return {
            "allowed": True,
            "tier": "hybrid",
            "step_info": step_info,
            "user_tier": user_tier,
            "upgrade_required": False,
            "legacy_access": False
        }
    
    # 베이직 기능은 모두 허용
    if required_tier == "basic":
        return {
            "allowed": True,
            "tier": "basic",
            "step_info": step_info,
            "user_tier": user_tier,
            "upgrade_required": False,
            "legacy_access": False
        }
    
    # 프로 기능 검증
    if required_tier == "pro":
        # 현재 프로 등급이면 허용
        if user_tier == "pro":
            return {
                "allowed": True,
                "tier": "pro",
                "step_info": step_info,
                "user_tier": user_tier,
                "upgrade_required": False,
                "legacy_access": False
            }
        
        # [GP-DOWNGRADE] 베이직이지만 과거 PRO 시절 생성한 리포트 조회는 허용
        if report_id and _check_legacy_report_access(user_id, report_id):
            return {
                "allowed": True,
                "tier": "pro",
                "step_info": step_info,
                "user_tier": user_tier,
                "upgrade_required": False,
                "legacy_access": True,  # 과거 데이터 접근
                "message": "과거 PRO 시절 생성한 리포트 (0코인 무료 조회)"
            }
        
        # 일반 베이직 사용자는 차단
        return {
            "allowed": False,
            "tier": "pro",
            "step_info": step_info,
            "user_tier": user_tier,
            "upgrade_required": True,
            "legacy_access": False
        }
    
    return {
        "allowed": False,
        "tier": required_tier,
        "step_info": step_info,
        "user_tier": user_tier,
        "upgrade_required": True,
        "legacy_access": False
    }


def _check_legacy_report_access(user_id: str, report_id: str) -> bool:
    """
    [GP-DOWNGRADE] 과거 PRO 시절 생성한 리포트인지 확인.
    
    Args:
        user_id: 회원 ID
        report_id: 리포트 ID
        
    Returns:
        True: 과거 PRO 시절 생성한 리포트 (무료 조회 가능)
        False: 신규 리포트 또는 권한 없음
    """
    from db_utils import _get_sb
    
    sb = _get_sb()
    if not sb:
        return False
    
    try:
        # gk_unified_reports 테이블에서 리포트 조회
        result = sb.table('gk_unified_reports').select(
            'agent_id, created_at, report_type'
        ).eq('id', report_id).execute()
        
        if not result.data or len(result.data) == 0:
            return False
        
        report = result.data[0]
        
        # 1. 본인이 생성한 리포트인지 확인
        if report.get('agent_id') != user_id:
            return False
        
        # 2. PRO 전용 리포트 타입인지 확인
        pro_report_types = ['ai_strategy', 'ai_proposal', 'custom_report']
        if report.get('report_type') not in pro_report_types:
            return False
        
        # 3. 과거 데이터인지 확인 (생성일이 존재하면 과거 데이터로 간주)
        if report.get('created_at'):
            return True
        
        return False
        
    except Exception as e:
        print(f"[ACCESS_CONTROL] 과거 리포트 확인 오류: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
# [§4] UI 배지 렌더링
# ══════════════════════════════════════════════════════════════════════════════

def render_step_badge(step_number: int, inline: bool = True) -> str:
    """
    STEP 배지 HTML 생성.
    
    Args:
        step_number: STEP 번호
        inline: True면 인라인 span, False면 블록 div
        
    Returns:
        HTML 문자열
    """
    if step_number not in STEP_ACCESS_MAP:
        return ""
    
    info = STEP_ACCESS_MAP[step_number]
    badge = info["badge"]
    color = info["badge_color"]
    
    tag = "span" if inline else "div"
    style = (
        f"background:{color};color:#fff;padding:3px 10px;border-radius:6px;"
        f"font-size:0.75rem;font-weight:700;margin-left:6px;"
        f"white-space:nowrap;display:inline-block;"
    )
    
    return f"<{tag} style='{style}'>{badge}</{tag}>"


def render_step_title(step_number: int, show_badge: bool = True) -> str:
    """
    STEP 제목 + 배지 HTML 생성.
    
    Args:
        step_number: STEP 번호
        show_badge: 배지 표시 여부
        
    Returns:
        HTML 문자열
    """
    if step_number not in STEP_ACCESS_MAP:
        return f"STEP {step_number}"
    
    info = STEP_ACCESS_MAP[step_number]
    title = f"STEP {step_number}. {info['name']}"
    
    if show_badge:
        badge = render_step_badge(step_number, inline=True)
        return f"{title} {badge}"
    
    return title


# ══════════════════════════════════════════════════════════════════════════════
# [§5] 업그레이드 팝업 (3회 클릭 넛지)
# ══════════════════════════════════════════════════════════════════════════════

def track_pro_click(user_id: str, step_number: int) -> int:
    """
    프로 기능 클릭 추적.
    
    Args:
        user_id: 회원 ID
        step_number: STEP 번호
        
    Returns:
        누적 클릭 횟수
    """
    key = f"_pro_click_count_{user_id}"
    if key not in st.session_state:
        st.session_state[key] = 0
    
    st.session_state[key] += 1
    return st.session_state[key]


def render_upgrade_popup(click_count: int = 0, feature_name: str = "프로 전용 기능") -> None:
    """
    업그레이드 팝업 렌더링 (3회 클릭 시 특가 팝업).
    
    Args:
        click_count: 누적 클릭 횟수
        feature_name: 기능 이름
    """
    # 3회 클릭 시 특가 팝업
    if click_count >= 3:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#fef3c7,#fde68a);"
            "border:3px solid #f59e0b;border-radius:16px;padding:20px 24px;"
            "margin:16px 0;box-shadow:0 8px 24px rgba(245,158,11,0.3);'>"
            "<div style='font-size:1.2rem;font-weight:900;color:#92400e;margin-bottom:12px;'>"
            "🎁 오늘만 긴급 혜택: PRO플랜 특가 이벤트</div>"
            "<div style='font-size:0.95rem;color:#78350f;line-height:1.7;margin-bottom:16px;'>"
            "지금 PRO플랜 전환 시 <b style='color:#dc2626;font-size:1.1rem;'>50코인 즉시 추가 증정</b>.<br>"
            "전문가용 AI 점검 기능 바로 활성화됩니다.<br>"
            "<span style='font-size:0.85rem;color:#a16207;'>✨ 이 혜택은 오늘 하루만 제공됩니다!</span></div>"
            "<div style='text-align:center;'>"
            "<a href='#' style='display:inline-block;background:linear-gradient(135deg,#dc2626,#b91c1c);"
            "color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;"
            "font-weight:900;font-size:1rem;box-shadow:0 4px 12px rgba(220,38,38,0.4);'>"
            "💎 지금 바로 PRO플랜 전환하기</a></div>"
            "</div>",
            unsafe_allow_html=True
        )
    else:
        # 일반 업그레이드 안내
        st.warning(
            f"🔒 **{feature_name}**은 PRO플랜 전용 기능입니다.\n\n"
            f"PRO플랜으로 업그레이드하시면 고부하 AI 전략 수립, 맞춤 제안서 생성 등 "
            f"전문가용 기능을 모두 사용하실 수 있습니다.\n\n"
            f"💡 **남은 클릭: {3 - click_count}회** (3회 클릭 시 특가 혜택 공개)"
        )


# ══════════════════════════════════════════════════════════════════════════════
# [§6] STEP 11 하이브리드 마케팅 넛지
# ══════════════════════════════════════════════════════════════════════════════

def render_step11_marketing_nudge(customer_name: str = "고객") -> None:
    """
    STEP 11 하이브리드 마케팅 넛지 - 전문가용 상담 검증 테마.
    
    Args:
        customer_name: 고객 이름
    """
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#e0f2fe,#bae6fd);"
        f"border:2px solid #0ea5e9;border-radius:12px;padding:16px 20px;"
        f"margin:12px 0;box-shadow:0 4px 12px rgba(14,165,233,0.2);'>"
        f"<div style='font-size:1rem;font-weight:900;color:#0c4a6e;margin-bottom:8px;'>"
        f"🚀 PRO 전용: AI 상담 점검 시스템</div>"
        f"<div style='font-size:0.88rem;color:#075985;line-height:1.7;margin-bottom:12px;'>"
        f"AI가 <b style='color:#0369a1;'>{customer_name}님의 상담 이력을 정밀 점검</b>하여, "
        f"현재 놓치고 있는 <b style='color:#dc2626;'>보장 공백</b>과 "
        f"최적의 상담 포인트를 제안합니다.<br><br>"
        f"<span style='font-size:0.85rem;color:#0c4a6e;font-weight:600;'>"
        f"💡 전문가다운 완벽한 상담을 준비하세요!</span></div>"
        f"<div style='text-align:center;'>"
        f"<a href='#' style='display:inline-block;background:linear-gradient(135deg,#0ea5e9,#0284c7);"
        f"color:#fff;padding:10px 24px;border-radius:8px;text-decoration:none;"
        f"font-weight:700;font-size:0.9rem;box-shadow:0 2px 8px rgba(14,165,233,0.3);'>"
        f"💎 프로로 전환하기</a></div>"
        f"</div>",
        unsafe_allow_html=True
    )


# ══════════════════════════════════════════════════════════════════════════════
# [§7] 전체 STEP 매핑 현황 조회
# ══════════════════════════════════════════════════════════════════════════════

def get_all_steps_info() -> Dict[int, Dict[str, Any]]:
    """
    전체 STEP 정보 반환.
    
    Returns:
        STEP_ACCESS_MAP
    """
    return STEP_ACCESS_MAP


def get_step_info(step_number: int) -> Optional[Dict[str, Any]]:
    """
    특정 STEP 정보 반환.
    
    Args:
        step_number: STEP 번호
        
    Returns:
        STEP 정보 또는 None
    """
    return STEP_ACCESS_MAP.get(step_number)


# ══════════════════════════════════════════════════════════════════════════════
# [§8] 세션 상태 초기화
# ══════════════════════════════════════════════════════════════════════════════

def init_access_control_session() -> None:
    """
    권한 제어 세션 상태 초기화.
    """
    if "_access_control_initialized" not in st.session_state:
        st.session_state["_access_control_initialized"] = True
        st.session_state["_pro_click_count"] = {}
