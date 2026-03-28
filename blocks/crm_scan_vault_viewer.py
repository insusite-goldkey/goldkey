# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_scan_vault_viewer.py
# CRM 스캔 문서 보관함 이력 뷰어 - Phase 3
# gk_scan_files 테이블에서 고객별 스캔 파일 이력 조회 및 표시
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
from typing import Optional


def render_scan_vault_viewer(person_id: str, agent_id: str) -> None:
    """
    [GP-PHASE3] 고객별 스캔 문서 보관함 이력 뷰어.
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
    """
    
    if not person_id or not agent_id:
        st.info("💡 고객을 선택하면 스캔 문서 이력을 조회할 수 있습니다.")
        return
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 50%,#fcd34d 100%);
      border-radius:12px;padding:14px 18px;margin-bottom:12px;border-left:4px solid #f59e0b;'>
      <div style='color:#92400e;font-size:0.95rem;font-weight:900;letter-spacing:0.04em;'>
    📦 스캔 문서 보관함 (Phase 3)
      </div>
      <div style='color:#b45309;font-size:0.75rem;margin-top:4px;'>
    GCS에 저장된 모든 스캔 파일의 메타데이터를 조회합니다.
      </div>
    </div>""", unsafe_allow_html=True)
    
    try:
        import db_utils as du
        
        # 스캔 파일 조회
        scan_files = du.get_scan_files(person_id=person_id, agent_id=agent_id, limit=50)
        
        if not scan_files:
            st.info("📭 아직 스캔된 문서가 없습니다. 증권 스캔 센터에서 문서를 촬영하세요.")
            return
        
        # 파일 타입별 카운트
        type_counts = {}
        for sf in scan_files:
            ft = sf.get("file_type", "other")
            type_counts[ft] = type_counts.get(ft, 0) + 1
        
        # 요약 카드
        _col1, _col2, _col3, _col4 = st.columns(4)
        with _col1:
            st.metric("📄 전체", len(scan_files))
        with _col2:
            st.metric("🏥 증권", type_counts.get("policy", 0))
        with _col3:
            st.metric("🩺 의무기록", type_counts.get("medical", 0))
        with _col4:
            st.metric("🧾 영수증", type_counts.get("receipt", 0))
        
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        
        # 파일 목록 테이블
        for idx, sf in enumerate(scan_files):
            _file_type = sf.get("file_type", "other")
            _file_name = sf.get("file_name", "파일명 없음")
            _uploaded_at = sf.get("uploaded_at", "")
            _ocr_status = sf.get("ocr_status", "pending")
            _extracted_fields = sf.get("extracted_fields") or {}
            _tags = sf.get("tags") or []
            
            # 파일 타입 아이콘 및 색상
            _type_icons = {
                "policy": ("🏥", "#3b82f6"),
                "medical": ("🩺", "#10b981"),
                "receipt": ("🧾", "#f59e0b"),
                "claim": ("📋", "#8b5cf6"),
                "other": ("📄", "#6b7280"),
            }
            _icon, _color = _type_icons.get(_file_type, ("📄", "#6b7280"))
            
            # OCR 상태 배지
            _status_badges = {
                "pending": ("⏳ 대기", "#94a3b8"),
                "processing": ("⚙️ 처리중", "#3b82f6"),
                "completed": ("✅ 완료", "#22c55e"),
                "failed": ("❌ 실패", "#ef4444"),
            }
            _status_text, _status_color = _status_badges.get(_ocr_status, ("❓ 미확인", "#6b7280"))
            
            with st.expander(f"{_icon} {_file_name} · {_uploaded_at[:10] if _uploaded_at else ''}", expanded=False):
                st.markdown(f"""
                <div style='background:#f8fafc;border-radius:8px;padding:12px;'>
                  <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                    <div style='color:#475569;font-size:0.75rem;font-weight:700;'>파일 타입</div>
                    <div style='background:{_color};color:#fff;font-size:0.7rem;font-weight:800;
                      padding:2px 8px;border-radius:12px;'>{_file_type.upper()}</div>
                  </div>
                  <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                    <div style='color:#475569;font-size:0.75rem;font-weight:700;'>OCR 상태</div>
                    <div style='background:{_status_color};color:#fff;font-size:0.7rem;font-weight:800;
                      padding:2px 8px;border-radius:12px;'>{_status_text}</div>
                  </div>
                  <div style='color:#475569;font-size:0.75rem;font-weight:700;margin-bottom:4px;'>업로드 시각</div>
                  <div style='color:#1e293b;font-size:0.8rem;margin-bottom:8px;'>{_uploaded_at}</div>
                  <div style='color:#475569;font-size:0.75rem;font-weight:700;margin-bottom:4px;'>GCS 경로</div>
                  <div style='color:#64748b;font-size:0.7rem;font-family:monospace;margin-bottom:8px;
                    word-break:break-all;'>{sf.get("gcs_path", "")}</div>
                </div>""", unsafe_allow_html=True)
                
                # 추출된 필드 표시
                if _extracted_fields:
                    st.markdown("**📊 추출된 정보**")
                    for key, val in _extracted_fields.items():
                        if val:
                            st.markdown(f"- **{key}**: {val}")
                
                # 태그 표시
                if _tags:
                    st.markdown("**🏷️ 태그**")
                    _tag_html = " ".join([
                        f"<span style='background:#e0e7ff;color:#3730a3;font-size:0.7rem;font-weight:700;"
                        f"padding:2px 8px;border-radius:10px;margin-right:4px;'>{tag}</span>"
                        for tag in _tags
                    ])
                    st.markdown(_tag_html, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ 스캔 문서 조회 오류: {e}")


def render_scan_vault_summary(person_id: str, agent_id: str) -> None:
    """
    [GP-PHASE3] 스캔 문서 보관함 요약 카드 (간단 버전).
    
    Args:
        person_id: 고객 ID
        agent_id: 설계사 ID
    """
    
    if not person_id or not agent_id:
        return
    
    try:
        import db_utils as du
        
        scan_files = du.get_scan_files(person_id=person_id, agent_id=agent_id, limit=10)
        
        if not scan_files:
            return
        
        # 최근 스캔 파일
        latest = scan_files[0]
        _file_type = latest.get("file_type", "other")
        _uploaded_at = latest.get("uploaded_at", "")
        
        st.markdown(f"""
        <div style='background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:10px 12px;
          margin-bottom:8px;'>
          <div style='color:#92400e;font-size:0.75rem;font-weight:800;margin-bottom:4px;'>
        📦 최근 스캔 문서
          </div>
          <div style='color:#b45309;font-size:0.7rem;'>
        {_file_type.upper()} · {_uploaded_at[:10] if _uploaded_at else ''} · 총 {len(scan_files)}건
          </div>
        </div>""", unsafe_allow_html=True)
        
    except Exception:
        pass
