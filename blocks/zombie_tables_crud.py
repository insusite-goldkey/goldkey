# ══════════════════════════════════════════════════════════════════════════════
# [MODULE] blocks/zombie_tables_crud.py
# 좀비 테이블 4개 CRUD UI - Phase 4
# gk_customer_docs, gk_agent_profiles, gk_home_notes, gk_home_ins
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional
import datetime


# ══════════════════════════════════════════════════════════════════════════════
# §1. gk_customer_docs CRUD
# ══════════════════════════════════════════════════════════════════════════════

def render_customer_docs_manager(person_id: str, agent_id: str, key_prefix: str = "cdocs") -> None:
    """고객 문서 관리 UI."""
    
    if not person_id or not agent_id:
        st.info("💡 고객을 선택하세요.")
        return
    
    st.markdown("""
    <div style='background:#fef3c7;border:1px dashed #f59e0b;border-radius:10px;padding:12px;margin-bottom:10px;'>
      <div style='color:#92400e;font-size:0.85rem;font-weight:900;'>📁 고객 문서 관리</div>
    </div>""", unsafe_allow_html=True)
    
    try:
        from shared_components import get_supabase_client
        sb = get_supabase_client()
        
        # 문서 조회
        docs = sb.table("gk_customer_docs").select("*").eq("person_id", person_id).eq("agent_id", agent_id).eq("is_deleted", False).order("created_at", desc=True).execute().data
        
        # 신규 문서 추가
        with st.expander("➕ 새 문서 추가", expanded=False):
            _doc_type = st.selectbox("문서 유형", ["contract", "claim", "medical", "id_card", "other"], key=f"{key_prefix}_type")
            _doc_name = st.text_input("문서명", key=f"{key_prefix}_name")
            _file_path = st.text_input("파일 경로 (GCS)", key=f"{key_prefix}_path")
            _notes = st.text_area("메모", key=f"{key_prefix}_notes", height=80)
            
            if st.button("💾 문서 저장", key=f"{key_prefix}_save"):
                if _doc_name and _file_path:
                    sb.table("gk_customer_docs").insert({
                        "person_id": person_id,
                        "agent_id": agent_id,
                        "doc_type": _doc_type,
                        "doc_name": _doc_name,
                        "file_path": _file_path,
                        "notes": _notes,
                    }).execute()
                    st.success("✅ 문서가 저장되었습니다!")
                    st.rerun()
                else:
                    st.warning("문서명과 파일 경로를 입력하세요.")
        
        # 문서 목록
        if docs:
            st.markdown(f"**📄 등록된 문서 ({len(docs)}건)**")
            for doc in docs:
                with st.expander(f"{doc['doc_type']} - {doc['doc_name']}", expanded=False):
                    st.markdown(f"**파일 경로**: `{doc['file_path']}`")
                    st.markdown(f"**등록일**: {doc['created_at'][:10]}")
                    if doc.get('notes'):
                        st.markdown(f"**메모**: {doc['notes']}")
                    
                    if st.button("🗑️ 삭제", key=f"{key_prefix}_del_{doc['doc_id']}"):
                        sb.table("gk_customer_docs").update({"is_deleted": True}).eq("doc_id", doc['doc_id']).execute()
                        st.success("삭제되었습니다.")
                        st.rerun()
        else:
            st.info("등록된 문서가 없습니다.")
    
    except Exception as e:
        st.error(f"❌ 오류: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# §2. gk_agent_profiles CRUD
# ══════════════════════════════════════════════════════════════════════════════

def render_agent_profile_editor(agent_id: str, key_prefix: str = "aprof") -> None:
    """설계사 프로필 편집 UI."""
    
    if not agent_id:
        st.info("💡 로그인이 필요합니다.")
        return
    
    st.markdown("""
    <div style='background:#dbeafe;border:1px dashed #3b82f6;border-radius:10px;padding:12px;margin-bottom:10px;'>
      <div style='color:#1e3a8a;font-size:0.85rem;font-weight:900;'>👤 내 프로필 관리</div>
    </div>""", unsafe_allow_html=True)
    
    try:
        from shared_components import get_supabase_client
        sb = get_supabase_client()
        
        # 프로필 조회
        profile = sb.table("gk_agent_profiles").select("*").eq("agent_id", agent_id).execute().data
        
        if profile:
            profile = profile[0]
            _display_name = st.text_input("표시 이름", value=profile.get("display_name", ""), key=f"{key_prefix}_name")
            _company = st.text_input("소속 회사", value=profile.get("company", ""), key=f"{key_prefix}_company")
            _department = st.text_input("부서", value=profile.get("department", ""), key=f"{key_prefix}_dept")
            _position = st.text_input("직급", value=profile.get("position", ""), key=f"{key_prefix}_pos")
            _license_number = st.text_input("자격증 번호", value=profile.get("license_number", ""), key=f"{key_prefix}_lic")
            _office_phone = st.text_input("사무실 전화", value=profile.get("office_phone", ""), key=f"{key_prefix}_phone")
            _bio = st.text_area("소개", value=profile.get("bio", ""), key=f"{key_prefix}_bio", height=100)
            
            if st.button("💾 프로필 업데이트", key=f"{key_prefix}_update"):
                sb.table("gk_agent_profiles").update({
                    "display_name": _display_name,
                    "company": _company,
                    "department": _department,
                    "position": _position,
                    "license_number": _license_number,
                    "office_phone": _office_phone,
                    "bio": _bio,
                }).eq("agent_id", agent_id).execute()
                st.success("✅ 프로필이 업데이트되었습니다!")
        else:
            st.info("프로필이 없습니다. 신규 생성하세요.")
            _display_name = st.text_input("표시 이름", key=f"{key_prefix}_name")
            _company = st.text_input("소속 회사", key=f"{key_prefix}_company")
            _bio = st.text_area("소개", key=f"{key_prefix}_bio", height=100)
            
            if st.button("➕ 프로필 생성", key=f"{key_prefix}_create"):
                if _display_name:
                    sb.table("gk_agent_profiles").insert({
                        "agent_id": agent_id,
                        "display_name": _display_name,
                        "company": _company,
                        "bio": _bio,
                    }).execute()
                    st.success("✅ 프로필이 생성되었습니다!")
                    st.rerun()
                else:
                    st.warning("표시 이름을 입력하세요.")
    
    except Exception as e:
        st.error(f"❌ 오류: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# §3. gk_home_notes CRUD
# ══════════════════════════════════════════════════════════════════════════════

def render_home_notes_manager(agent_id: str, key_prefix: str = "hnotes") -> None:
    """홈 화면 메모 관리 UI."""
    
    if not agent_id:
        st.info("💡 로그인이 필요합니다.")
        return
    
    st.markdown("""
    <div style='background:#fef3c7;border:1px dashed #f59e0b;border-radius:10px;padding:12px;margin-bottom:10px;'>
      <div style='color:#92400e;font-size:0.85rem;font-weight:900;'>📝 내 메모</div>
    </div>""", unsafe_allow_html=True)
    
    try:
        from shared_components import get_supabase_client
        sb = get_supabase_client()
        
        # 메모 조회
        notes = sb.table("gk_home_notes").select("*").eq("agent_id", agent_id).eq("is_archived", False).order("is_pinned", desc=True).order("created_at", desc=True).execute().data
        
        # 신규 메모 추가
        with st.expander("➕ 새 메모 작성", expanded=False):
            _title = st.text_input("제목", key=f"{key_prefix}_title")
            _content = st.text_area("내용", key=f"{key_prefix}_content", height=120)
            _priority = st.selectbox("우선순위", ["low", "normal", "high", "urgent"], index=1, key=f"{key_prefix}_priority")
            _is_pinned = st.checkbox("📌 상단 고정", key=f"{key_prefix}_pin")
            
            if st.button("💾 메모 저장", key=f"{key_prefix}_save"):
                if _title and _content:
                    sb.table("gk_home_notes").insert({
                        "agent_id": agent_id,
                        "title": _title,
                        "content": _content,
                        "priority": _priority,
                        "is_pinned": _is_pinned,
                    }).execute()
                    st.success("✅ 메모가 저장되었습니다!")
                    st.rerun()
                else:
                    st.warning("제목과 내용을 입력하세요.")
        
        # 메모 목록
        if notes:
            st.markdown(f"**📝 내 메모 ({len(notes)}개)**")
            for note in notes:
                _pin_icon = "📌 " if note.get("is_pinned") else ""
                _priority_colors = {"low": "#94a3b8", "normal": "#3b82f6", "high": "#f59e0b", "urgent": "#ef4444"}
                _priority_color = _priority_colors.get(note.get("priority", "normal"), "#3b82f6")
                
                with st.expander(f"{_pin_icon}{note['title']}", expanded=False):
                    st.markdown(f"<div style='background:{_priority_color}20;border-left:3px solid {_priority_color};padding:8px;border-radius:4px;'>{note['content']}</div>", unsafe_allow_html=True)
                    st.markdown(f"**우선순위**: {note.get('priority', 'normal')} · **작성일**: {note['created_at'][:10]}")
                    
                    _col1, _col2 = st.columns(2)
                    with _col1:
                        if st.button("📌 고정 토글", key=f"{key_prefix}_toggle_{note['note_id']}"):
                            sb.table("gk_home_notes").update({"is_pinned": not note.get("is_pinned", False)}).eq("note_id", note['note_id']).execute()
                            st.rerun()
                    with _col2:
                        if st.button("🗑️ 삭제", key=f"{key_prefix}_del_{note['note_id']}"):
                            sb.table("gk_home_notes").update({"is_archived": True}).eq("note_id", note['note_id']).execute()
                            st.success("삭제되었습니다.")
                            st.rerun()
        else:
            st.info("작성된 메모가 없습니다.")
    
    except Exception as e:
        st.error(f"❌ 오류: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# §4. gk_home_ins CRUD
# ══════════════════════════════════════════════════════════════════════════════

def render_home_insights_viewer(agent_id: str, key_prefix: str = "hins") -> None:
    """홈 화면 인사이트 조회 UI."""
    
    if not agent_id:
        st.info("💡 로그인이 필요합니다.")
        return
    
    st.markdown("""
    <div style='background:#e0f2fe;border:1px dashed #0284c7;border-radius:10px;padding:12px;margin-bottom:10px;'>
      <div style='color:#0c4a6e;font-size:0.85rem;font-weight:900;'>📊 인사이트 & 통계</div>
    </div>""", unsafe_allow_html=True)
    
    try:
        from shared_components import get_supabase_client
        sb = get_supabase_client()
        
        # 인사이트 조회
        insights = sb.table("gk_home_ins").select("*").eq("agent_id", agent_id).order("created_at", desc=True).limit(10).execute().data
        
        if insights:
            for ins in insights:
                _trend_icons = {"up": "📈", "down": "📉", "stable": "➡️"}
                _trend_icon = _trend_icons.get(ins.get("trend", "stable"), "➡️")
                
                with st.expander(f"{_trend_icon} {ins['title']}", expanded=False):
                    st.markdown(f"**요약**: {ins.get('summary', '')}")
                    if ins.get('metric_value'):
                        st.metric(ins.get('title', ''), f"{ins['metric_value']} {ins.get('metric_unit', '')}")
                    if ins.get('data_snapshot'):
                        st.json(ins['data_snapshot'])
                    st.markdown(f"**생성일**: {ins['created_at'][:10]}")
                    
                    if not ins.get('is_read'):
                        if st.button("✅ 읽음 표시", key=f"{key_prefix}_read_{ins['insight_id']}"):
                            sb.table("gk_home_ins").update({"is_read": True}).eq("insight_id", ins['insight_id']).execute()
                            st.rerun()
        else:
            st.info("인사이트가 없습니다.")
    
    except Exception as e:
        st.error(f"❌ 오류: {e}")
