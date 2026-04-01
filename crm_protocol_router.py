# ══════════════════════════════════════════════════════════════════════════════
# [CRM-PROTOCOL-ROUTER] 프로토콜 라우터 UI 컴포넌트
# 고객 직업 입력 시 AI 기반 섹터 자동 추천 UI
# ══════════════════════════════════════════════════════════════════════════════
# 작성일: 2026-04-01
# 목적: 직업 정보 기반 최적 상담 섹터 자동 추천 및 시각적 노출
# ══════════════════════════════════════════════════════════════════════════════

import streamlit as st
from typing import Optional


def render_protocol_router_ui(
    job_name: str,
    job_grade: Optional[int] = None,
    customer_age: Optional[int] = None,
    is_ceo: bool = False,
    has_factory: bool = False,
    has_commercial: bool = False,
) -> None:
    """
    [프로토콜 라우터 UI] 직업 기반 AI 섹터 추천 박스
    
    Args:
        job_name: 고객 직업명
        job_grade: 상해급수 (1~4)
        customer_age: 고객 나이
        is_ceo: CEO/대표 여부
        has_factory: 공장 소유 여부
        has_commercial: 상가 소유 여부
    """
    if not job_name or not job_name.strip():
        return
    
    try:
        from GP_JOB_SECTOR_MAPPING import recommend_sectors_by_job
        from GP_CORE_PROTOCOL_TAXONOMY import get_sector_by_war_room_key, get_protocol_by_id
        
        # 섹터 추천
        recommendations = recommend_sectors_by_job(
            job_name=job_name.strip(),
            job_grade=job_grade,
            job_flags=None,
            top_k=5,
        )
        
        if not recommendations:
            return
        
        # UI 렌더링
        st.markdown(
            "<div style='background:linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);"
            "border:2px solid #818CF8;border-radius:12px;padding:16px;margin:16px 0;'>"
            "<div style='display:flex;align-items:center;gap:8px;margin-bottom:12px;'>"
            "<span style='font-size:1.1rem;'>🎯</span>"
            "<span style='font-size:0.95rem;font-weight:900;color:#312E81;'>"
            "AI 권장 프로토콜</span>"
            "<span style='font-size:0.72rem;color:#4C1D95;background:#DDD6FE;"
            "padding:2px 8px;border-radius:8px;margin-left:auto;'>"
            f"직업: {job_name}</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        
        # 추천 섹터 뱃지
        badge_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
        
        for idx, rec in enumerate(recommendations[:5], 1):
            sector = get_sector_by_war_room_key(rec["sector_key"])
            if not sector:
                continue
            
            protocol = get_protocol_by_id(sector.get("protocol_id", ""))
            protocol_name = protocol["protocol_name"] if protocol else "기타"
            
            # 우선순위에 따른 스타일
            if idx == 1:
                badge_style = (
                    "background:linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);"
                    "border:2px solid #F59E0B;color:#92400E;font-weight:900;"
                )
                priority_icon = "⭐"
            elif idx == 2:
                badge_style = (
                    "background:linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);"
                    "border:2px solid #3B82F6;color:#1E3A8A;font-weight:800;"
                )
                priority_icon = "🔹"
            else:
                badge_style = (
                    "background:linear-gradient(135deg, #F3F4F6 0%, #E5E7EB 100%);"
                    "border:1.5px solid #9CA3AF;color:#374151;font-weight:700;"
                )
                priority_icon = "◦"
            
            badge_html += (
                f"<div style='{badge_style}padding:8px 14px;border-radius:10px;"
                f"cursor:pointer;transition:all 0.2s;' "
                f"title='{rec[\"reason\"]}'>"
                f"<div style='font-size:0.85rem;'>"
                f"{priority_icon} {sector['icon']} {sector['sector_name']}</div>"
                f"<div style='font-size:0.68rem;opacity:0.8;margin-top:2px;'>"
                f"{protocol_name} · 점수 {rec['score']:.0f}</div>"
                f"</div>"
            )
        
        badge_html += "</div>"
        
        st.markdown(badge_html, unsafe_allow_html=True)
        
        # 안내 메시지
        st.markdown(
            "<div style='margin-top:10px;font-size:0.72rem;color:#4C1D95;'>"
            "💡 <b>사용 방법:</b> 위 추천 섹터를 참고하여 War Room에서 해당 섹터를 선택하세요. "
            "AI가 고객의 직업 특성을 분석하여 최적의 상담 분야를 추천했습니다."
            "</div></div>",
            unsafe_allow_html=True,
        )
        
        # 세션 상태에 추천 섹터 저장
        st.session_state["_protocol_router_recommendations"] = [
            rec["sector_key"] for rec in recommendations
        ]
        
    except ImportError:
        # GP_CORE_PROTOCOL 모듈 로드 실패 시 무시
        pass
    except Exception as e:
        # 에러 발생 시 조용히 무시 (UI 깨짐 방지)
        pass


def render_compact_protocol_router(job_name: str) -> None:
    """
    [컴팩트 프로토콜 라우터] 간소화된 섹터 추천 UI
    
    Args:
        job_name: 고객 직업명
    """
    if not job_name or not job_name.strip():
        return
    
    try:
        from GP_JOB_SECTOR_MAPPING import recommend_sectors_by_job
        from GP_CORE_PROTOCOL_TAXONOMY import get_sector_by_war_room_key
        
        recommendations = recommend_sectors_by_job(
            job_name=job_name.strip(),
            job_grade=None,
            job_flags=None,
            top_k=3,
        )
        
        if not recommendations:
            return
        
        # 컴팩트 UI
        sectors_text = " · ".join([
            f"{get_sector_by_war_room_key(rec['sector_key'])['icon']} "
            f"{get_sector_by_war_room_key(rec['sector_key'])['sector_name']}"
            for rec in recommendations[:3]
            if get_sector_by_war_room_key(rec['sector_key'])
        ])
        
        st.markdown(
            f"<div style='background:#EEF2FF;border-left:3px solid #6366F1;"
            f"padding:8px 12px;margin:8px 0;border-radius:6px;'>"
            f"<span style='font-size:0.75rem;color:#4338CA;font-weight:700;'>"
            f"🎯 AI 추천: {sectors_text}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        
    except:
        pass


def get_recommended_sectors_for_session() -> list[str]:
    """
    세션에 저장된 추천 섹터 목록 반환
    
    Returns:
        추천 섹터 키 리스트 (예: ["cancer", "medical", "accident"])
    """
    return st.session_state.get("_protocol_router_recommendations", [])


def apply_sector_theme_css(sector_key: str) -> None:
    """
    [섹터별 테마 자동 적용] 선택된 섹터의 색상 테마를 전역 CSS에 주입
    
    Args:
        sector_key: 섹터 키 (예: "cancer", "ceo_plan")
    """
    try:
        from GP_CORE_PROTOCOL_TAXONOMY import get_sector_by_war_room_key
        
        sector = get_sector_by_war_room_key(sector_key)
        if not sector:
            return
        
        color = sector.get("color", "#6366F1")
        bg_color = sector.get("bg_color", "#EEF2FF")
        
        # 전역 CSS 주입
        st.markdown(
            f"""
            <style>
            /* [GP-CORE-PROTOCOL] 섹터별 테마 자동 적용 */
            :root {{
                --gp-sector-color: {color};
                --gp-sector-bg: {bg_color};
            }}
            
            /* 주요 버튼 스타일 */
            div[data-testid="stButton"] button[kind="primary"] {{
                background: linear-gradient(135deg, {bg_color} 0%, {color}22 100%) !important;
                border: 2px solid {color} !important;
                color: {color} !important;
                font-weight: 900 !important;
            }}
            
            /* 강조 박스 */
            .gp-sector-highlight {{
                background: {bg_color};
                border-left: 4px solid {color};
                padding: 12px;
                border-radius: 8px;
                margin: 12px 0;
            }}
            
            /* 섹터 뱃지 */
            .gp-sector-badge {{
                background: {bg_color};
                color: {color};
                padding: 4px 10px;
                border-radius: 8px;
                font-weight: 900;
                font-size: 0.75rem;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        
    except:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# [테스트 코드]
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 80)
    print("[CRM-PROTOCOL-ROUTER] 프로토콜 라우터 UI 테스트")
    print("=" * 80)
    
    # Streamlit 환경에서만 실행 가능
    print("\n✅ 모듈 로드 성공")
    print("📌 사용 방법:")
    print("   1. render_protocol_router_ui(job_name='제조업 대표')")
    print("   2. render_compact_protocol_router(job_name='택시 기사')")
    print("   3. apply_sector_theme_css(sector_key='cancer')")
    print("\n" + "=" * 80)
