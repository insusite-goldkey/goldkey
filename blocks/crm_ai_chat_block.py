"""
[Phase 5] CRM AI 상담 채팅 블록 — RAG 엔진 기반 전문 지식 검색
법인/배상책임/화재보험 332개 지식 조각(Chunks) 활용
"""
from __future__ import annotations

import streamlit as st
import os
from pathlib import Path
from typing import Optional


def render_crm_ai_chat(user_id: str, sel_pid: str = "") -> None:
    """
    RAG 엔진 기반 AI 상담 채팅 인터페이스
    
    Args:
        user_id: 설계사 ID
        sel_pid: 선택된 고객 person_id
    """
    st.markdown(
        "<div style='font-size:clamp(13px,2vw,16px);font-weight:900;color:#0f172a;margin-bottom:8px;'>"
        "🤖 AI 상담 채팅 (RAG 전문 지식 검색)</div>",
        unsafe_allow_html=True,
    )
    
    # RAG 엔진 초기화
    if "rag_engine" not in st.session_state:
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent.parent / ".env"
            load_dotenv(env_path)
            
            SUPABASE_URL = os.getenv("SUPABASE_URL")
            SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", os.getenv("SUPABASE_KEY"))
            OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
            
            if not all([SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY]):
                st.error("❌ 환경변수 미설정: SUPABASE_URL, SUPABASE_KEY, OPENAI_API_KEY, GEMINI_API_KEY")
                return
            
            from hq_backend.engines.rag_engine import RAGEngine
            
            st.session_state["rag_engine"] = RAGEngine(
                supabase_url=SUPABASE_URL,
                supabase_key=SUPABASE_KEY,
                openai_api_key=OPENAI_API_KEY,
                gemini_api_key=GEMINI_API_KEY
            )
            st.session_state["rag_engine_ready"] = True
        except Exception as e:
            st.error(f"❌ RAG 엔진 초기화 실패: {str(e)}")
            st.session_state["rag_engine_ready"] = False
            return
    
    if not st.session_state.get("rag_engine_ready"):
        st.warning("⚠️ RAG 엔진이 준비되지 않았습니다.")
        return
    
    # 채팅 히스토리 초기화
    if "crm_chat_history" not in st.session_state:
        st.session_state["crm_chat_history"] = []
    
    # 카테고리 선택
    st.markdown(
        "<div style='font-size:clamp(11px,1.6vw,13px);font-weight:700;color:#475569;margin:8px 0 4px;'>"
        "📚 전문 지식 카테고리</div>",
        unsafe_allow_html=True,
    )
    
    category_options = {
        "전체": "",
        "법인컨설팅": "법인컨설팅",
        "배상책임": "배상책임",
        "화재보험": "화재보험"
    }
    
    selected_category = st.selectbox(
        "카테고리 선택",
        options=list(category_options.keys()),
        key="crm_chat_category",
        label_visibility="collapsed"
    )
    
    # 채팅 히스토리 표시
    st.markdown(
        "<div style='font-size:clamp(11px,1.6vw,13px);font-weight:700;color:#475569;margin:12px 0 4px;'>"
        "💬 상담 내역</div>",
        unsafe_allow_html=True,
    )
    
    chat_container = st.container()
    with chat_container:
        if not st.session_state["crm_chat_history"]:
            st.markdown(
                "<div style='background:#f8fafc;padding:16px;border-radius:8px;border:1px dashed #cbd5e1;"
                "text-align:center;color:#64748b;font-size:clamp(11px,1.5vw,13px);'>"
                "💡 아래 질문 입력창에 법인/배상책임/화재보험 관련 질문을 입력하세요.<br>"
                "332개의 전문 지식 조각에서 정확한 답변을 찾아드립니다.</div>",
                unsafe_allow_html=True,
            )
        else:
            for msg in st.session_state["crm_chat_history"]:
                if msg["role"] == "user":
                    st.markdown(
                        f"<div style='background:#dbeafe;padding:10px 12px;border-radius:8px;margin:4px 0;"
                        f"border-left:3px solid #3b82f6;'>"
                        f"<div style='font-size:clamp(10px,1.4vw,12px);font-weight:700;color:#1e40af;margin-bottom:4px;'>"
                        f"👤 질문</div>"
                        f"<div style='font-size:clamp(11px,1.5vw,13px);color:#1e3a8a;'>{msg['content']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"<div style='background:#f0fdf4;padding:10px 12px;border-radius:8px;margin:4px 0;"
                        f"border-left:3px solid #10b981;'>"
                        f"<div style='font-size:clamp(10px,1.4vw,12px);font-weight:700;color:#065f46;margin-bottom:4px;'>"
                        f"🤖 AI 답변 (신뢰도: {msg.get('confidence', 0):.1%})</div>"
                        f"<div style='font-size:clamp(11px,1.5vw,13px);color:#064e3b;white-space:pre-wrap;'>{msg['content']}</div>",
                        unsafe_allow_html=True,
                    )
                    if msg.get("sources"):
                        sources_html = "<div style='font-size:clamp(10px,1.3vw,11px);color:#6b7280;margin-top:6px;'>"
                        sources_html += "<b>📄 출처:</b><br>"
                        for src in msg["sources"][:3]:
                            doc_name = src.get("document_name", "알 수 없음")
                            page = src.get("source_page", "?")
                            sources_html += f"• {doc_name} (페이지 {page})<br>"
                        sources_html += "</div></div>"
                        st.markdown(sources_html, unsafe_allow_html=True)
    
    # 질문 입력
    st.markdown(
        "<div style='font-size:clamp(11px,1.6vw,13px);font-weight:700;color:#475569;margin:12px 0 4px;'>"
        "✍️ 질문 입력</div>",
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_query = st.text_input(
            "질문을 입력하세요",
            key="crm_chat_input",
            placeholder="예: 법인 임원 퇴직금 세무 처리 방법은?",
            label_visibility="collapsed"
        )
    
    with col2:
        send_button = st.button("📤 전송", key="crm_chat_send", use_container_width=True)
    
    # 질문 처리
    if send_button and user_query.strip():
        with st.spinner("🔍 전문 지식 검색 중..."):
            try:
                rag_engine = st.session_state["rag_engine"]
                
                # RAG 엔진 쿼리
                result = rag_engine.query(
                    user_query=user_query,
                    category=category_options[selected_category],
                    match_threshold=0.7,
                    match_count=5
                )
                
                # 채팅 히스토리에 추가
                st.session_state["crm_chat_history"].append({
                    "role": "user",
                    "content": user_query
                })
                
                st.session_state["crm_chat_history"].append({
                    "role": "assistant",
                    "content": result["answer"],
                    "confidence": result["confidence"],
                    "sources": result["sources"]
                })
                
                # 입력창 초기화를 위한 rerun
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ 답변 생성 실패: {str(e)}")
    
    # 히스토리 초기화 버튼
    if st.session_state["crm_chat_history"]:
        if st.button("🗑️ 대화 내역 초기화", key="crm_chat_clear"):
            st.session_state["crm_chat_history"] = []
            st.rerun()
    
    # 안내 메시지
    st.markdown(
        "<div style='background:#fef3c7;padding:10px;border-radius:6px;border:1px solid #fbbf24;"
        "margin-top:12px;'>"
        "<div style='font-size:clamp(10px,1.4vw,12px);font-weight:700;color:#92400e;margin-bottom:4px;'>"
        "💡 RAG 전문 지식 검색 안내</div>"
        "<div style='font-size:clamp(10px,1.3vw,11px);color:#78350f;line-height:1.6;'>"
        "• <b>332개 지식 조각</b>: 법인 상담 자료(167개), 배상책임(72개), 화재보험(93개)<br>"
        "• <b>환각 방지</b>: Gemini 1.5 Pro temperature=0.0 + 엄격한 프롬프트<br>"
        "• <b>신뢰도 표시</b>: 벡터 유사도 기반 답변 신뢰도 자동 계산<br>"
        "• <b>출처 명시</b>: 모든 답변에 원본 문서명 및 페이지 번호 표시"
        "</div></div>",
        unsafe_allow_html=True,
    )
