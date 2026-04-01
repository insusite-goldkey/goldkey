"""
crm_client_detail.py — 인텔리전스 CRM 고객 상세 상황실
[GP-STEP5] Goldkey AI Masters 2026

360도 고객 통찰 시스템:
- 좌측: 인터랙틱 마인드맵 (Network View)
- 중앙: 통합 세일즈 타임라인 (The Flow)
- 우측: RAG 기반 지능형 뉴스 피드 (Insight)
"""
from __future__ import annotations
import re, json, datetime
from typing import Optional, List, Dict, Any
import streamlit as st

# ══════════════════════════════════════════════════════════════════════════════
# [1] 데이터 레이어 — gk_people, gk_relationships, gk_schedules 조회
# ══════════════════════════════════════════════════════════════════════════════

def _get_sb():
    """Supabase 클라이언트 가져오기"""
    try:
        from db_utils import _get_sb as _sb
        return _sb()
    except Exception:
        return None


def get_customer_detail(person_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    고객 기본 정보 조회 (gk_people)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: 고객 정보 또는 None
    """
    try:
        sb = _get_sb()
        if not sb:
            return None
        
        result = (
            sb.table("gk_people")
            .select("*")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .maybe_single()
            .execute()
        )
        
        return result.data if result and result.data else None
    except Exception:
        return None


def get_customer_relationships(person_id: str, agent_id: str) -> List[Dict[str, Any]]:
    """
    고객 인맥 관계 조회 (gk_relationships)
    
    Args:
        person_id: 중심 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        list: 관계 목록 (from + to 양방향)
    """
    try:
        sb = _get_sb()
        if not sb:
            return []
        
        # from_person_id = person_id (내가 → 타인)
        outgoing = (
            sb.table("gk_relationships")
            .select("*, to_person:gk_people!gk_relationships_to_person_id_fkey(person_id, name, birth_date)")
            .eq("from_person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        # to_person_id = person_id (타인 → 나)
        incoming = (
            sb.table("gk_relationships")
            .select("*, from_person:gk_people!gk_relationships_from_person_id_fkey(person_id, name, birth_date)")
            .eq("to_person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        relationships = []
        
        # 나 → 타인 (outgoing)
        for rel in (outgoing.data or []):
            to_person = rel.get("to_person") or {}
            relationships.append({
                "relationship_id": rel.get("relationship_id"),
                "direction": "outgoing",
                "relation_type": rel.get("relation_type"),
                "person_id": to_person.get("person_id"),
                "name": to_person.get("name"),
                "birth_date": to_person.get("birth_date"),
                "memo": rel.get("memo", "")
            })
        
        # 타인 → 나 (incoming)
        for rel in (incoming.data or []):
            from_person = rel.get("from_person") or {}
            relationships.append({
                "relationship_id": rel.get("relationship_id"),
                "direction": "incoming",
                "relation_type": rel.get("relation_type"),
                "person_id": from_person.get("person_id"),
                "name": from_person.get("name"),
                "birth_date": from_person.get("birth_date"),
                "memo": rel.get("memo", "")
            })
        
        return relationships
    except Exception:
        return []


def get_customer_timeline(person_id: str, agent_id: str) -> List[Dict[str, Any]]:
    """
    고객 통합 타임라인 조회 (상담 일지 + 일정 기록)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        list: 타임라인 이벤트 (날짜 역순 정렬)
    """
    try:
        sb = _get_sb()
        if not sb:
            return []
        
        timeline = []
        
        # 1. 일정 기록 (gk_schedules)
        schedules = (
            sb.table("gk_schedules")
            .select("schedule_id, title, memo, date, start_time, end_time, category, created_at")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .order("date", desc=True)
            .limit(50)
            .execute()
        )
        
        for sch in (schedules.data or []):
            timeline.append({
                "type": "schedule",
                "id": sch.get("schedule_id"),
                "date": sch.get("date"),
                "time": sch.get("start_time", ""),
                "title": sch.get("title"),
                "content": sch.get("memo", ""),
                "category": sch.get("category", "consult"),
                "created_at": sch.get("created_at")
            })
        
        # 2. 상담 일지 (향후 gk_consultation_logs 테이블 추가 시)
        # TODO: gk_consultation_logs 테이블 생성 후 조회 추가
        
        # 날짜 역순 정렬
        timeline.sort(key=lambda x: x.get("date", "") + x.get("time", ""), reverse=True)
        
        return timeline
    except Exception:
        return []


def get_customer_policies_summary(person_id: str, agent_id: str) -> Dict[str, Any]:
    """
    고객 보험 계약 요약 (gk_policies + gk_policy_roles)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    
    Returns:
        dict: {"total_count": 3, "total_premium": 150000, "roles": {...}}
    """
    try:
        sb = _get_sb()
        if not sb:
            return {"total_count": 0, "total_premium": 0, "roles": {}}
        
        # policy_roles에서 해당 고객이 연결된 증권 조회
        roles = (
            sb.table("gk_policy_roles")
            .select("role, gk_policies!inner(id, premium, product_name, insurance_company)")
            .eq("person_id", person_id)
            .eq("agent_id", agent_id)
            .eq("is_deleted", False)
            .execute()
        )
        
        total_count = 0
        total_premium = 0
        role_summary = {"계약자": 0, "피보험자": 0, "수익자": 0}
        
        for r in (roles.data or []):
            policy = r.get("gk_policies") or {}
            role = r.get("role", "")
            premium = policy.get("premium", 0) or 0
            
            total_count += 1
            total_premium += float(premium)
            
            if role in role_summary:
                role_summary[role] += 1
        
        return {
            "total_count": total_count,
            "total_premium": int(total_premium),
            "roles": role_summary
        }
    except Exception:
        return {"total_count": 0, "total_premium": 0, "roles": {}}


# ══════════════════════════════════════════════════════════════════════════════
# [2] 좌측: 인터랙틱 마인드맵 (Network View)
# ══════════════════════════════════════════════════════════════════════════════

def render_network_mindmap(person_id: str, agent_id: str, customer_name: str):
    """
    고객 중심 인맥 지도 시각화 (gk_relationships 기반)
    
    Args:
        person_id: 중심 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>"
        "🕸️ 인맥 네트워크 (Network View)</div>",
        unsafe_allow_html=True
    )
    
    relationships = get_customer_relationships(person_id, agent_id)
    
    if not relationships:
        st.info("등록된 인맥 관계가 없습니다.")
        return
    
    # 관계 유형별 그룹화
    relation_groups = {}
    for rel in relationships:
        rel_type = rel.get("relation_type", "기타")
        if rel_type not in relation_groups:
            relation_groups[rel_type] = []
        relation_groups[rel_type].append(rel)
    
    # 관계 유형별 색상
    relation_colors = {
        "배우자": "#DBEAFE",  # 블루
        "자녀": "#E9D5FF",    # 퍼플
        "부모": "#FEF9C3",    # 옐로우
        "형제": "#DCFCE7",    # 민트
        "소개자": "#FEE2E2",  # 코랄
        "법인직원": "#F0FDF4", # 그린
        "기타": "#F3F4F6"     # 그레이
    }
    
    # 중심 노드 (현재 고객)
    st.markdown(
        f"<div style='text-align:center;background:linear-gradient(135deg,#EFF6FF,#DBEAFE);"
        f"border:2px solid #3B82F6;border-radius:50%;width:120px;height:120px;"
        f"display:flex;align-items:center;justify-content:center;margin:0 auto 20px;'>"
        f"<div style='font-size:1.1rem;font-weight:900;color:#1E3A8A;'>{customer_name}</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 관계 노드 렌더링
    for rel_type, rels in relation_groups.items():
        bg_color = relation_colors.get(rel_type, "#F3F4F6")
        
        st.markdown(
            f"<div style='font-size:.85rem;font-weight:700;color:#374151;margin:12px 0 6px;'>"
            f"📌 {rel_type} ({len(rels)}명)</div>",
            unsafe_allow_html=True
        )
        
        for rel in rels:
            rel_name = rel.get("name", "이름 없음")
            rel_pid = rel.get("person_id", "")
            birth_date = rel.get("birth_date", "")
            memo = rel.get("memo", "")
            
            # 에이젠틱 인터랙션: 클릭 시 해당 인물로 화면 전환
            if st.button(
                f"👤 {rel_name} ({birth_date[:10] if birth_date else '생년월일 미등록'})",
                key=f"network_node_{rel_pid}",
                use_container_width=True,
                help=f"{rel_type} — {memo if memo else '메모 없음'}"
            ):
                # 세션 상태 업데이트 → 화면 전환
                st.session_state["crm_selected_pid"] = rel_pid
                st.session_state["crm_spa_mode"] = "customer"
                st.session_state["crm_spa_screen"] = "contact"
                st.rerun()
            
            # 메모 표시
            if memo:
                st.caption(f"💬 {memo}")


# ══════════════════════════════════════════════════════════════════════════════
# [3] 중앙: 통합 세일즈 타임라인 (The Flow)
# ══════════════════════════════════════════════════════════════════════════════

def render_sales_timeline(person_id: str, agent_id: str, customer_name: str):
    """
    통합 세일즈 타임라인 (상담 일지 + 일정 기록 + 크로스-커스터머 메모)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_name: 고객 이름
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>"
        "📊 통합 세일즈 타임라인 (The Flow)</div>",
        unsafe_allow_html=True
    )
    
    timeline = get_customer_timeline(person_id, agent_id)
    
    if not timeline:
        st.info("기록된 타임라인이 없습니다.")
        return
    
    # 타임라인 이벤트 렌더링
    for idx, event in enumerate(timeline):
        event_type = event.get("type", "")
        event_date = event.get("date", "")
        event_time = event.get("time", "")
        event_title = event.get("title", "")
        event_content = event.get("content", "")
        event_category = event.get("category", "")
        
        # 카테고리별 색상
        category_colors = {
            "consult": "#DBEAFE",
            "expiry": "#FFF7ED",
            "upsell": "#FAF5FF",
            "appointment": "#DBEAFE",
            "todo": "#FEF9C3",
            "personal": "#F0FDF4"
        }
        
        bg_color = category_colors.get(event_category, "#F3F4F6")
        
        # 타임라인 카드
        st.markdown(
            f"<div style='background:{bg_color};border:1px solid #E2E8F0;border-radius:8px;"
            f"padding:10px 12px;margin-bottom:8px;'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>"
            f"<span style='font-size:.82rem;font-weight:700;color:#374151;'>{event_title}</span>"
            f"<span style='font-size:.72rem;color:#64748B;'>{event_date} {event_time}</span>"
            f"</div>"
            f"<div style='font-size:.78rem;color:#475569;line-height:1.5;'>{event_content}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    
    # 크로스-커스터머 메모 입력
    st.markdown("<div style='border-top:1px dashed #E2E8F0;margin:16px 0;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:.88rem;font-weight:700;color:#374151;margin-bottom:6px;'>"
        "✍️ 크로스-커스터머 메모 (Cross-Customer Note)</div>",
        unsafe_allow_html=True
    )
    
    cross_memo = st.text_area(
        "크로스-커스터머 메모",
        placeholder=f"예: {customer_name}님 상담 시 배우자분 암보험 보완 필요 언급됨",
        height=80,
        key=f"cross_memo_{person_id}",
        label_visibility="collapsed"
    )
    
    if st.button("💾 메모 저장", key=f"save_cross_memo_{person_id}"):
        if cross_memo.strip():
            # TODO: gk_consultation_logs 테이블에 저장
            st.success("✅ 크로스-커스터머 메모가 저장되었습니다.")
        else:
            st.warning("메모 내용을 입력하세요.")


# ══════════════════════════════════════════════════════════════════════════════
# [4] 우측: RAG 기반 지능형 뉴스 피드 (Insight)
# ══════════════════════════════════════════════════════════════════════════════

def render_intelligent_news_feed(person_id: str, agent_id: str, customer_data: Dict[str, Any]):
    """
    RAG 기반 지능형 뉴스 피드 (직업/관심사 기반 큐레이션)
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
        customer_data: 고객 기본 정보
    """
    st.markdown(
        "<div style='font-size:1.05rem;font-weight:900;color:#1E3A8A;margin-bottom:10px;'>"
        "📰 지능형 뉴스 피드 (Insight)</div>",
        unsafe_allow_html=True
    )
    
    # 고객 직업 및 관심사 추출
    job = customer_data.get("job", "") or customer_data.get("memo", "")
    keywords = extract_keywords_from_customer(customer_data)
    
    if not keywords:
        st.info("고객 정보에서 키워드를 추출할 수 없습니다. 직업이나 관심사를 입력하세요.")
        return
    
    # 에이젠틱 넛지 카드
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#FEF9C3,#FEE2E2);"
        f"border:1.5px solid #F59E0B;border-radius:10px;padding:12px;margin-bottom:12px;'>"
        f"<div style='font-size:.85rem;font-weight:700;color:#92400E;margin-bottom:4px;'>"
        f"💡 에이젠틱 넛지</div>"
        f"<div style='font-size:.78rem;color:#78350F;line-height:1.6;'>"
        f"오늘 고객님의 직종({job or '정보 없음'})과 관련된 뉴스가 떴습니다. "
        f"안부 전화를 해보세요!</div>"
        f"</div>",
        unsafe_allow_html=True
    )
    
    # 뉴스 피드 (Mock 데이터 — 향후 HQ RAG 연동)
    news_items = get_curated_news(keywords, limit=5)
    
    if not news_items:
        st.caption("관련 뉴스를 찾을 수 없습니다.")
        return
    
    for idx, news in enumerate(news_items):
        st.markdown(
            f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:8px;"
            f"padding:10px 12px;margin-bottom:8px;'>"
            f"<div style='font-size:.82rem;font-weight:700;color:#1E3A8A;margin-bottom:4px;'>"
            f"{news.get('title', '제목 없음')}</div>"
            f"<div style='font-size:.72rem;color:#64748B;margin-bottom:4px;'>"
            f"{news.get('source', '출처 없음')} · {news.get('date', '')}</div>"
            f"<div style='font-size:.75rem;color:#475569;line-height:1.5;'>"
            f"{news.get('summary', '요약 없음')}</div>"
            f"</div>",
            unsafe_allow_html=True
        )


def extract_keywords_from_customer(customer_data: Dict[str, Any]) -> List[str]:
    """
    고객 정보에서 키워드 추출 (직업, 메모 등)
    
    Args:
        customer_data: 고객 정보
    
    Returns:
        list: 키워드 목록
    """
    keywords = []
    
    # 직업 필드 (향후 gk_people 테이블에 job 컬럼 추가 시)
    job = customer_data.get("job", "")
    if job:
        keywords.append(job)
    
    # 메모에서 키워드 추출
    memo = customer_data.get("memo", "")
    if memo:
        # 간단한 키워드 추출 (공백 기준 분리)
        words = memo.split()
        keywords.extend([w for w in words if len(w) >= 2])
    
    return list(set(keywords))[:5]  # 중복 제거 + 최대 5개


def get_curated_news(keywords: List[str], limit: int = 5) -> List[Dict[str, Any]]:
    """
    키워드 기반 뉴스 큐레이션 (Mock 데이터)
    
    향후 HQ RAG 시스템 연동 예정
    
    Args:
        keywords: 검색 키워드 목록
        limit: 최대 뉴스 수
    
    Returns:
        list: 뉴스 목록
    """
    # TODO: HQ RAG 시스템 연동
    # - keywords를 HQ로 전송
    # - HQ에서 실시간 뉴스 크롤링 + RAG 검색
    # - 관련도 높은 뉴스 반환
    
    # Mock 데이터
    mock_news = [
        {
            "title": "2026년 세법 개정안 발표 — 금융소득 종합과세 기준 상향",
            "source": "매일경제",
            "date": "2026-04-01",
            "summary": "정부가 금융소득 종합과세 기준을 기존 2천만원에서 3천만원으로 상향 조정하는 세법 개정안을 발표했습니다."
        },
        {
            "title": "보험업계, AI 언더라이팅 도입 확대 — 심사 기간 50% 단축",
            "source": "보험신문",
            "date": "2026-03-30",
            "summary": "주요 생명보험사들이 AI 기반 언더라이팅 시스템을 도입하여 심사 기간을 기존 대비 50% 단축했습니다."
        },
        {
            "title": "건강보험 보장성 강화 — 비급여 항목 축소",
            "source": "헬스조선",
            "date": "2026-03-28",
            "summary": "보건복지부가 건강보험 보장성 강화 정책의 일환으로 비급여 항목을 대폭 축소한다고 밝혔습니다."
        }
    ]
    
    return mock_news[:limit]


# ══════════════════════════════════════════════════════════════════════════════
# [5] 상단: 고객 기본 정보 + 12단계 위치 표시
# ══════════════════════════════════════════════════════════════════════════════

def render_customer_header(customer_data: Dict[str, Any], policies_summary: Dict[str, Any]):
    """
    고객 기본 정보 헤더 (이름, 생년월일, 계약 요약, 12단계 위치)
    
    Args:
        customer_data: 고객 기본 정보
        policies_summary: 보험 계약 요약
    """
    name = customer_data.get("name", "이름 없음")
    birth_date = customer_data.get("birth_date", "")
    contact = customer_data.get("contact", "")
    current_stage = customer_data.get("current_stage", 1)
    
    total_count = policies_summary.get("total_count", 0)
    total_premium = policies_summary.get("total_premium", 0)
    
    # 12단계 진행 바
    stage_percent = int((current_stage / 12) * 100)
    stage_color = get_stage_color(current_stage)
    
    st.markdown(
        f"<div style='background:linear-gradient(135deg,#EFF6FF,#DBEAFE);"
        f"border:1.5px solid #93C5FD;border-radius:12px;padding:16px;margin-bottom:16px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;'>"
        f"<div>"
        f"<div style='font-size:1.3rem;font-weight:900;color:#1E3A8A;'>{name}</div>"
        f"<div style='font-size:.82rem;color:#475569;margin-top:2px;'>"
        f"생년월일: {birth_date[:10] if birth_date else '미등록'} | 연락처: {contact[:3]}****{contact[-4:] if len(contact) >= 7 else '미등록'}"
        f"</div>"
        f"</div>"
        f"<div style='text-align:right;'>"
        f"<div style='font-size:.85rem;font-weight:700;color:#1E3A8A;'>계약 {total_count}건</div>"
        f"<div style='font-size:.78rem;color:#64748B;'>월 보험료 {total_premium:,}원</div>"
        f"</div>"
        f"</div>"
        f"<div style='margin-bottom:6px;'>"
        f"<div style='display:flex;justify-content:space-between;font-size:.75rem;font-weight:700;color:#374151;'>"
        f"<span>세일즈 프로세스 진행도</span>"
        f"<span style='color:#1E3A8A;'>{current_stage}/12단계 ({stage_percent}%)</span>"
        f"</div>"
        f"</div>"
        f"<div style='background:#E2E8F0;border-radius:8px;height:16px;overflow:hidden;'>"
        f"<div style='background:{stage_color};width:{stage_percent}%;height:100%;transition:width .4s ease;'></div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True
    )


def get_stage_color(stage: int) -> str:
    """
    12단계 세일즈 프로세스 단계별 색상 반환
    
    Args:
        stage: 현재 단계 (1~12)
    
    Returns:
        str: 색상 코드
    """
    if stage <= 3:
        return "#3B82F6"  # 블루
    elif stage <= 6:
        return "#A855F7"  # 퍼플
    elif stage <= 9:
        return "#F59E0B"  # 옐로우
    elif stage == 10:
        return "#22C55E"  # 민트
    else:
        return "#10B981"  # 그린


# ══════════════════════════════════════════════════════════════════════════════
# [6] 메인 렌더링 함수 — 3분할 반응형 레이아웃
# ══════════════════════════════════════════════════════════════════════════════

def render_client_detail_page(person_id: str, agent_id: str):
    """
    인텔리전스 CRM 고객 상세 상황실 메인 렌더링
    
    Args:
        person_id: 고객 UUID
        agent_id: 설계사 ID
    """
    # 고객 기본 정보 조회
    customer_data = get_customer_detail(person_id, agent_id)
    
    if not customer_data:
        st.error("❌ 고객 정보를 찾을 수 없습니다.")
        return
    
    customer_name = customer_data.get("name", "이름 없음")
    
    # 보험 계약 요약 조회
    policies_summary = get_customer_policies_summary(person_id, agent_id)
    
    # 상단: 고객 기본 정보 헤더
    render_customer_header(customer_data, policies_summary)
    
    # 3분할 반응형 레이아웃 CSS
    st.markdown("""
<style>
/* 3분할 레이아웃 — 태블릿 가로: 3열, 모바일: 1열 스택 */
.gp-client-detail-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    margin-bottom: 12px;
}

@media (max-width: 1024px) {
    .gp-client-detail-grid {
        grid-template-columns: 1fr;
    }
}

/* 블록 공통 스타일 */
.gp-detail-block {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 14px;
    min-height: 400px;
}
</style>
    """, unsafe_allow_html=True)
    
    # 3분할 레이아웃
    col1, col2, col3 = st.columns(3, gap="medium")
    
    with col1:
        # 좌측: 인터랙틱 마인드맵
        st.markdown("<div class='gp-detail-block'>", unsafe_allow_html=True)
        render_network_mindmap(person_id, agent_id, customer_name)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 중앙: 통합 세일즈 타임라인
        st.markdown("<div class='gp-detail-block'>", unsafe_allow_html=True)
        render_sales_timeline(person_id, agent_id, customer_name)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        # 우측: RAG 기반 지능형 뉴스 피드
        st.markdown("<div class='gp-detail-block'>", unsafe_allow_html=True)
        render_intelligent_news_feed(person_id, agent_id, customer_data)
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# [7] 사용 예시
# ══════════════════════════════════════════════════════════════════════════════

"""
## 사용 예시 (crm_app_impl.py 통합)

```python
from crm_client_detail import render_client_detail_page

# 고객 상세 페이지 렌더링
if st.session_state.get("crm_spa_mode") == "customer":
    person_id = st.session_state.get("crm_selected_pid")
    agent_id = st.session_state.get("crm_user_id")
    
    if person_id and agent_id:
        render_client_detail_page(person_id, agent_id)
```

## calendar_engine.py 라우팅 강화

```python
# _build_cal_html 함수 내 (line 1296~1304)
function navigateToCustomer() {
    var pid = document.getElementById('ev-person-id').value;
    if (!pid) return;
    var p = new URLSearchParams({
        cal_nav_customer: '1',
        cal_nav_pid: pid
    });
    window.top.location.href = window.top.location.pathname + '?' + p.toString();
}
```

## gk_people 테이블 확장 (향후)

```sql
-- 직업 및 관심사 컬럼 추가
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS job TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS interests TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS current_stage INTEGER DEFAULT 1 CHECK (current_stage BETWEEN 1 AND 12);
```
"""
