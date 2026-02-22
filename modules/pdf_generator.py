# ==========================================================
# PDF 생성 및 문서 관리 모듈
# ==========================================================

import streamlit as st
import tempfile
import os
from datetime import datetime as dt

def render_upload_interface():
    """파일 업로드 인터페이스"""
    st.subheader("📸 의무기록 및 증권 일괄 분석")
    
    files = st.file_uploader(
        "자료 업로드", 
        accept_multiple_files=True, 
        type=['pdf', 'jpg', 'jpeg', 'png']
    )
    
    if files:
        st.info(f"📁 {len(files)}개 파일이 업로드되었습니다.")
        
        # 파일 정보 표시
        for i, file in enumerate(files):
            st.write(f"{i+1}. {file.name} ({file.size//1024}KB)")
        
        if st.button("📄 일괄 PDF 생성 및 다운로드", type="primary"):
            with st.spinner("PDF를 생성하고 있습니다..."):
                try:
                    # 간단한 PDF 생성 로직 (실제로는 PyMuPDF 필요)
                    pdf_file = create_simple_pdf(files)
                    if pdf_file:
                        st.success(f"✅ PDF 생성 완료: {pdf_file}")
                        
                        # 다운로드 버튼
                        with open(pdf_file, "rb") as f:
                            st.download_button(
                                label="📥 일괄 PDF 다운로드",
                                data=f.read(),
                                file_name=f"merged_documents_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                                mime="application/pdf"
                            )
                except Exception as e:
                    st.error(f"PDF 생성 실패: {e}")

def render_document_manager():
    """문서 관리자 인터페이스"""
    st.subheader("📄 내 문서 관리")
    
    # 문서 목록 (시뮬레이션)
    if 'documents' not in st.session_state:
        st.session_state.documents = [
            {"name": "보험증권_202401.pdf", "date": "2024-01-15", "size": "2.3MB"},
            {"name": "진단서_202402.jpg", "date": "2024-02-20", "size": "1.5MB"},
            {"name": "상담기록_202403.pdf", "date": "2024-03-10", "size": "3.1MB"}
        ]
    
    # 문서 목록 표시
    for doc in st.session_state.documents:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 {doc['name']}")
        with col2:
            st.write(f"📅 {doc['date']}")
        with col3:
            if st.button("🗑️", key=f"del_{doc['name']}"):
                st.session_state.documents.remove(doc)
                st.rerun()
    
    # 문서 통계
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 문서", len(st.session_state.documents))
    with col2:
        total_size = sum([float(doc['size'].replace('MB', '')) for doc in st.session_state.documents])
        st.metric("총 용량", f"{total_size:.1f}MB")
    with col3:
        st.metric("평균 용량", f"{total_size/len(st.session_state.documents):.1f}MB")

def create_simple_pdf(files):
    """간단한 PDF 생성 (시뮬레이션)"""
    # 실제 구현에서는 PyMuPDF 등 라이브러리 필요
    # 여기서는 더미 파일 생성
    temp_dir = tempfile.mkdtemp()
    pdf_file = os.path.join(temp_dir, f"merged_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    # 더미 PDF 내용 생성
    pdf_content = f"""
    보고서: 일괄 문서 병합
    생성일: {dt.now().strftime('%Y년 %m월 %d일')}
    포함된 파일 수: {len(files)}
    파일 목록:
    {chr(10).join([f"- {file.name}" for file in files])}
    """
    
    with open(pdf_file, "w", encoding='utf-8') as f:
        f.write(pdf_content)
    
    return pdf_file
