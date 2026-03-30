"""
[GP-제89조] STEP 1~12 통합 네비게이션 시스템
Goldkey AI Masters 2026 - 12단계 마스터플랜 UI 구현
"""
import streamlit as st
from typing import Dict, List, Tuple, Optional


# ──────────────────────────────────────────────────────────────────────────
# [§1] STEP 1~12 정의 (마스터플랜)
# ──────────────────────────────────────────────────────────────────────────

STEP_DEFINITIONS: List[Dict] = [
    {
        "step": 1,
        "title": "고객 정보 동기화",
        "icon": "👤",
        "tier": "Basic",
        "coins": 0,
        "app": "HQ",
        "description": "메인 파트에서 입력된 고객 정보 자동 불러오기"
    },
    {
        "step": 2,
        "title": "내보험다보여 동의 SMS",
        "icon": "📱",
        "tier": "Basic",
        "coins": 0,
        "app": "HQ",
        "description": "금융감독원 개인정보 제공 동의 요청 발송"
    },
    {
        "step": 3,
        "title": "보험 가입 현황 수집",
        "icon": "📋",
        "tier": "Basic",
        "coins": 0,
        "app": "HQ",
        "description": "내보험다보여 API 연동 또는 수동 입력"
    },
    {
        "step": 4,
        "title": "KB 스탠다드 분석",
        "icon": "🔬",
        "tier": "Pro",
        "coins": 3,
        "app": "HQ",
        "description": "KB 7대 보장 × KOSIS 데이터 요새 교차분석"
    },
    {
        "step": 5,
        "title": "카카오톡 리포트 발송",
        "icon": "💬",
        "tier": "Pro",
        "coins": 1,
        "app": "HQ",
        "description": "분석 결과 알림톡 자동 발송"
    },
    {
        "step": 6,
        "title": "OCR 스캔 분석",
        "icon": "📸",
        "tier": "Pro",
        "coins": 3,
        "app": "CRM",
        "description": "증권/의무기록 Gemini Vision API 분석"
    },
    {
        "step": 7,
        "title": "트리니티 가치 분석",
        "icon": "💎",
        "tier": "Pro",
        "coins": 3,
        "app": "CRM",
        "description": "소득 × 보장 × 위험 점수 종합 분석"
    },
    {
        "step": 8,
        "title": "인맥 관계망 시각화",
        "icon": "🗺️",
        "tier": "Basic",
        "coins": 0,
        "app": "CRM",
        "description": "고객-가족-소개자 네트워크 그래프"
    },
    {
        "step": 9,
        "title": "보험 계약 관리",
        "icon": "📝",
        "tier": "Basic",
        "coins": 0,
        "app": "CRM",
        "description": "A/B/C 파트 계약 CRUD"
    },
    {
        "step": 10,
        "title": "만기 알림 자동화",
        "icon": "⏰",
        "tier": "Basic",
        "coins": 0,
        "app": "CRM",
        "description": "보험 만기 30일 전 자동 알림"
    },
    {
        "step": 11,
        "title": "증권 해지 처리",
        "icon": "🗑️",
        "tier": "Basic",
        "coins": 0,
        "app": "CRM",
        "description": "보험 증권 해지 신청 및 Soft Delete"
    },
    {
        "step": 12,
        "title": "데이터 요새 관리",
        "icon": "🏰",
        "tier": "Basic",
        "coins": 0,
        "app": "CRM",
        "description": "4대 테이블 CRUD 통합 관리"
    }
]


# ──────────────────────────────────────────────────────────────────────────
# [§2] STEP 네비게이션 UI 렌더링
# ──────────────────────────────────────────────────────────────────────────

def render_step_navigation(
    current_step: Optional[int] = None,
    app_type: str = "HQ",
    show_all: bool = False
) -> None:
    """
    STEP 1~12 네비게이션 UI 렌더링.
    
    Args:
        current_step: 현재 활성화된 STEP 번호 (1~12)
        app_type: 앱 유형 ("HQ" 또는 "CRM")
        show_all: True일 경우 모든 STEP 표시, False일 경우 해당 앱만 표시
    """
    # 앱별 필터링
    if show_all:
        steps = STEP_DEFINITIONS
    else:
        steps = [s for s in STEP_DEFINITIONS if s["app"] == app_type]
    
    # 헤더
    st.markdown(
        f"<div style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        f"padding:16px;border-radius:12px;text-align:center;margin-bottom:20px;'>"
        f"<h2 style='color:white;margin:0;font-size:1.3rem;'>🎯 {app_type} 12단계 워크플로우</h2>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # STEP 카드 그리드 (3열)
    cols_per_row = 3
    for i in range(0, len(steps), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(steps):
                step_data = steps[i + j]
                with col:
                    _render_step_card(step_data, is_active=(step_data["step"] == current_step))


def _render_step_card(step_data: Dict, is_active: bool = False) -> None:
    """
    개별 STEP 카드 렌더링.
    
    Args:
        step_data: STEP 정보 딕셔너리
        is_active: 현재 활성화 여부
    """
    step_num = step_data["step"]
    title = step_data["title"]
    icon = step_data["icon"]
    tier = step_data["tier"]
    coins = step_data["coins"]
    description = step_data["description"]
    
    # 활성화 상태에 따른 스타일
    if is_active:
        bg_color = "#dbeafe"
        border_color = "#3b82f6"
        border_width = "3px"
    else:
        bg_color = "#ffffff"
        border_color = "#000000"
        border_width = "1px"
    
    # Pro 전용 배지
    tier_badge = ""
    if tier == "Pro":
        tier_badge = "<span style='background:#dc2626;color:white;padding:2px 8px;border-radius:6px;font-size:0.7rem;font-weight:700;margin-left:6px;'>PRO</span>"
    
    # 코인 표시
    coin_display = ""
    if coins > 0:
        coin_display = f"<div style='font-size:0.75rem;color:#f59e0b;font-weight:700;margin-top:4px;'>🪙 {coins} 코인</div>"
    
    st.markdown(
        f"<div style='background:{bg_color};border:{border_width} dashed {border_color};"
        f"border-radius:12px;padding:16px;text-align:center;min-height:180px;"
        f"transition:all 0.3s ease;'>"
        f"<div style='font-size:2rem;margin-bottom:8px;'>{icon}</div>"
        f"<div style='font-size:0.7rem;color:#6b7280;font-weight:700;margin-bottom:4px;'>STEP {step_num}</div>"
        f"<div style='font-size:0.9rem;font-weight:900;color:#1e293b;margin-bottom:6px;'>"
        f"{title}{tier_badge}</div>"
        f"<div style='font-size:0.75rem;color:#475569;line-height:1.4;'>{description}</div>"
        f"{coin_display}"
        f"</div>",
        unsafe_allow_html=True
    )


# ──────────────────────────────────────────────────────────────────────────
# [§3] STEP 진행 상태 표시
# ──────────────────────────────────────────────────────────────────────────

def render_step_progress(completed_steps: List[int]) -> None:
    """
    STEP 진행 상태 프로그레스 바 렌더링.
    
    Args:
        completed_steps: 완료된 STEP 번호 리스트 (예: [1, 2, 3])
    """
    total_steps = len(STEP_DEFINITIONS)
    completed_count = len(completed_steps)
    progress_percent = (completed_count / total_steps) * 100
    
    st.markdown(
        f"<div style='background:#f9fafb;border:1px dashed #000;border-radius:8px;padding:16px;margin-bottom:20px;'>"
        f"<div style='font-size:0.85rem;font-weight:700;color:#1e293b;margin-bottom:8px;'>"
        f"📊 전체 진행률: {completed_count}/{total_steps} ({progress_percent:.0f}%)</div>"
        f"<div style='background:#e5e7eb;border-radius:8px;height:12px;overflow:hidden;'>"
        f"<div style='background:linear-gradient(90deg, #10b981 0%, #059669 100%);"
        f"height:100%;width:{progress_percent}%;transition:width 0.5s ease;'></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 완료된 STEP 목록
    if completed_steps:
        completed_titles = [
            f"{s['icon']} STEP {s['step']}: {s['title']}"
            for s in STEP_DEFINITIONS if s['step'] in completed_steps
        ]
        st.success(f"✅ 완료: {', '.join(completed_titles)}")


# ──────────────────────────────────────────────────────────────────────────
# [§4] STEP 권한 체크
# ──────────────────────────────────────────────────────────────────────────

def check_step_access(step_num: int, user_id: str) -> Tuple[bool, str]:
    """
    STEP 접근 권한 체크.
    
    Args:
        step_num: STEP 번호 (1~12)
        user_id: 회원 ID
        
    Returns:
        (접근 가능 여부, 메시지)
    """
    step_data = next((s for s in STEP_DEFINITIONS if s["step"] == step_num), None)
    
    if not step_data:
        return False, f"STEP {step_num}을 찾을 수 없습니다"
    
    # Basic 등급은 항상 접근 가능
    if step_data["tier"] == "Basic":
        return True, "접근 가능"
    
    # Pro 등급 체크
    try:
        from modules.calendar_ai_helper import check_pro_tier
        
        if not check_pro_tier(user_id):
            return False, f"Pro 등급 전용 기능입니다 (필요 코인: {step_data['coins']})"
        
        return True, "접근 가능"
        
    except Exception as e:
        print(f"[STEP] 권한 체크 오류: {e}")
        return False, "권한 확인 실패"


# ──────────────────────────────────────────────────────────────────────────
# [§5] STEP 코인 차감
# ──────────────────────────────────────────────────────────────────────────

def deduct_step_coins(step_num: int, user_id: str) -> bool:
    """
    STEP 실행 시 코인 차감.
    
    Args:
        step_num: STEP 번호 (1~12)
        user_id: 회원 ID
        
    Returns:
        True: 차감 성공
        False: 차감 실패 (코인 부족)
    """
    step_data = next((s for s in STEP_DEFINITIONS if s["step"] == step_num), None)
    
    if not step_data:
        return False
    
    # 0코인 기능은 차감 없이 통과
    if step_data["coins"] == 0:
        return True
    
    # 코인 차감
    try:
        from modules.credit_manager import check_and_deduct_credit
        
        return check_and_deduct_credit(
            user_id,
            step_data["coins"],
            f"STEP {step_num}: {step_data['title']}"
        )
        
    except Exception as e:
        print(f"[STEP] 코인 차감 오류: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────
# [§6] STEP 정보 조회
# ──────────────────────────────────────────────────────────────────────────

def get_step_info(step_num: int) -> Optional[Dict]:
    """
    STEP 정보 조회.
    
    Args:
        step_num: STEP 번호 (1~12)
        
    Returns:
        STEP 정보 딕셔너리 또는 None
    """
    return next((s for s in STEP_DEFINITIONS if s["step"] == step_num), None)


def get_steps_by_app(app_type: str) -> List[Dict]:
    """
    앱별 STEP 목록 조회.
    
    Args:
        app_type: 앱 유형 ("HQ" 또는 "CRM")
        
    Returns:
        STEP 정보 리스트
    """
    return [s for s in STEP_DEFINITIONS if s["app"] == app_type]


def get_steps_by_tier(tier: str) -> List[Dict]:
    """
    등급별 STEP 목록 조회.
    
    Args:
        tier: 등급 ("Basic" 또는 "Pro")
        
    Returns:
        STEP 정보 리스트
    """
    return [s for s in STEP_DEFINITIONS if s["tier"] == tier]
