# ==========================================================
# PDF 생성 및 문서 관리 모듈 (reportlab 기반 실제 PDF 생성)
# ==========================================================

import streamlit as st
import tempfile
import os
import io
from datetime import datetime as dt


# ==========================================================================
# [CORE] reportlab 기반 실제 PDF 생성
# ==========================================================================
def _build_planner_footer(planner_info: dict | None) -> str:
    """[GP200조] planner_info dict에서 브랜딩 푸터 텍스트 생성."""
    if not planner_info:
        return ""
    _co = (planner_info.get("company") or "").strip()
    _br = (planner_info.get("branch") or "").strip()
    _nm = (planner_info.get("name") or "").strip()
    _ct = (planner_info.get("contact") or "").strip()
    if not (_co or _nm or _ct):
        return ""
    _affil = " ".join(filter(None, [_co, _br]))
    _parts = []
    if _affil:
        _parts.append(_affil)
    if _nm:
        _parts.append(f"{_nm} 마스터")
    if _ct:
        _parts.append(_ct)
    return "담당: " + " | ".join(_parts)


def create_report_pdf(
    title: str,
    content: str,
    *,
    client_name: str = "",
    created_by: str = "골드키 AI 마스터",
    footer: str = "본 리포트는 AI 분석 결과이며, 최종 판단은 전문가와 상담하십시오.",
    planner_info: dict | None = None,
) -> bytes:
    """
    리포트 텍스트를 실제 PDF로 변환 (reportlab 사용).
    반환: bytes (PDF 바이너리) — 실패 시 빈 bytes
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.colors import HexColor
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            HRFlowable, Table, TableStyle,
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # 한글 폰트 등록 시도 (NanumGothic 또는 시스템 폰트)
        _font_name = "Helvetica"
        _font_bold = "Helvetica-Bold"
        for _fp in [
            "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
            "/usr/share/fonts/nanum/NanumGothic.ttf",
            "C:/Windows/Fonts/malgun.ttf",
            "C:/Windows/Fonts/NanumGothic.ttf",
        ]:
            if os.path.exists(_fp):
                try:
                    pdfmetrics.registerFont(TTFont("NanumGothic", _fp))
                    _font_name = "NanumGothic"
                    _font_bold = "NanumGothic"
                    break
                except Exception:
                    pass

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=25 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()
        style_title = ParagraphStyle(
            "GKTitle",
            fontName=_font_bold,
            fontSize=16,
            leading=22,
            textColor=HexColor("#1a3a5c"),
            spaceAfter=6,
        )
        style_sub = ParagraphStyle(
            "GKSub",
            fontName=_font_name,
            fontSize=9,
            textColor=HexColor("#64748b"),
            spaceAfter=4,
        )
        style_body = ParagraphStyle(
            "GKBody",
            fontName=_font_name,
            fontSize=10,
            leading=16,
            textColor=HexColor("#1e293b"),
            spaceAfter=4,
        )
        style_footer = ParagraphStyle(
            "GKFooter",
            fontName=_font_name,
            fontSize=8,
            textColor=HexColor("#94a3b8"),
        )

        story = []

        # ── 헤더 ────────────────────────────────────────────────────
        story.append(Paragraph(title, style_title))
        story.append(Paragraph(
            f"생성일시: {dt.now().strftime('%Y년 %m월 %d일 %H:%M')}  |  "
            f"{'고객명: ' + client_name + '  |  ' if client_name else ''}"
            f"작성: {created_by}",
            style_sub,
        ))
        story.append(HRFlowable(width="100%", thickness=1.5,
                                 color=HexColor("#1a3a5c"), spaceAfter=8))

        # ── 본문 (줄바꿈 유지) ───────────────────────────────────────
        for line in content.split("\n"):
            _safe = (
                line.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .strip()
            )
            if _safe:
                story.append(Paragraph(_safe, style_body))
            else:
                story.append(Spacer(1, 4))

        # ── 푸터 ────────────────────────────────────────────────────
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                 color=HexColor("#cbd5e1"), spaceBefore=4))
        story.append(Paragraph(footer, style_footer))
        # [GP200조] 플래너 브랜딩 푸터
        _planner_line = _build_planner_footer(planner_info)
        if _planner_line:
            story.append(Spacer(1, 3))
            style_brand = ParagraphStyle(
                "GKBrand",
                fontName=_font_bold,
                fontSize=8,
                textColor=HexColor("#1a3a5c"),
                backColor=HexColor("#f0f6ff"),
                borderPad=4,
            )
            story.append(Paragraph(_planner_line, style_brand))

        doc.build(story)
        return buf.getvalue()

    except Exception as e:
        # reportlab 없거나 오류 → 텍스트 기반 최소 PDF 반환
        return _create_fallback_pdf(title, content, error=str(e))


def _create_fallback_pdf(title: str, content: str, error: str = "") -> bytes:
    """reportlab 없을 때 최소한의 유효한 PDF 바이너리 생성 (ASCII only)"""
    lines = [title, "", f"생성: {dt.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for line in content.split("\n"):
        safe = line.encode("ascii", errors="replace").decode("ascii")
        lines.append(safe[:200])
    if error:
        lines += ["", f"[PDF 생성 라이브러리 오류: {error[:100]}]",
                  "[reportlab을 설치하면 한글 PDF가 정상 생성됩니다]"]

    body = "\n".join(lines)
    pdf_str = (
        "%PDF-1.4\n"
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842]\n"
        "   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
        "4 0 obj\n<< /Length " + str(len(body) + 50) + " >>\nstream\n"
        "BT /F1 11 Tf 40 800 Td 12 TL\n"
        + "\n".join(f"({ln[:100]}) Tj T*" for ln in lines[:60])
        + "\nET\nendstream\nendobj\n"
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        "xref\n0 6\n0000000000 65535 f \n"
        "trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    )
    return pdf_str.encode("latin-1", errors="replace")


# ==========================================================================
# [UI] 보고서 PDF 다운로드 버튼 헬퍼
# ==========================================================================
def render_pdf_download(
    report_text: str,
    title: str = "골드키 AI 분석 리포트",
    *,
    client_name: str = "",
    button_label: str = " PDF 다운로드",
    file_prefix: str = "goldkey_report",
    key: str = "pdf_dl",
    planner_info: dict | None = None,
) -> None:
    """
    분석 리포트를 PDF로 변환하여 다운로드 버튼을 렌더링합니다.
    planner_info: {"company", "branch", "name", "contact"} — GP200조 브랜딩 푸터
    """
    if not report_text or not report_text.strip():
        st.caption(" 다운로드할 보고서가 없습니다. 먼저 AI 분석을 실행하세요.")
        return

    with st.spinner(" PDF 생성 중..."):
        pdf_bytes = create_report_pdf(title, report_text, client_name=client_name,
                                      planner_info=planner_info)

    if pdf_bytes:
        fname = f"{file_prefix}_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            label=button_label,
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            key=key,
            use_container_width=True,
        )
    else:
        st.error("PDF 생성에 실패했습니다.")


# ==========================================================================
# [UI] Streamlit 파일 업로드 인터페이스 (기존 API 호환 유지)
# ==========================================================================
def render_upload_interface():
    """파일 업로드 및 PDF 병합 인터페이스"""
    st.subheader("📸 의무기록 및 증권 일괄 분석")

    files = st.file_uploader(
        "자료 업로드",
        accept_multiple_files=True,
        type=["pdf", "jpg", "jpeg", "png"],
    )

    if files:
        st.info(f"📁 {len(files)}개 파일이 업로드되었습니다.")
        for i, file in enumerate(files):
            st.write(f"{i+1}. {file.name} ({file.size // 1024}KB)")

        if st.button("📄 일괄 PDF 생성 및 다운로드", type="primary"):
            with st.spinner("PDF를 생성하고 있습니다..."):
                try:
                    content_lines = [
                        f"일괄 문서 병합 리포트",
                        f"생성일: {dt.now().strftime('%Y년 %m월 %d일')}",
                        f"포함된 파일 수: {len(files)}",
                        "",
                        "파일 목록:",
                    ] + [f"  - {f.name} ({f.size // 1024}KB)" for f in files]
                    content = "\n".join(content_lines)
                    pdf_bytes = create_report_pdf("일괄 문서 병합", content)
                    if pdf_bytes:
                        st.success("✅ PDF 생성 완료")
                        st.download_button(
                            label="📥 일괄 PDF 다운로드",
                            data=pdf_bytes,
                            file_name=f"merged_documents_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                        )
                except Exception as e:
                    st.error(f"PDF 생성 실패: {e}")


def render_document_manager():
    """문서 관리자 인터페이스"""
    st.subheader("📄 내 문서 관리")

    if "documents" not in st.session_state:
        st.session_state.documents = []

    if not st.session_state.documents:
        st.info("저장된 문서가 없습니다.")
        return

    for doc in st.session_state.documents:
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.write(f"📄 {doc['name']}")
        with col2:
            st.write(f"📅 {doc.get('date', '')}")
        with col3:
            if st.button("🗑️", key=f"del_{doc['name']}"):
                st.session_state.documents.remove(doc)
                st.rerun()

    st.markdown("---")
    st.metric("총 문서", len(st.session_state.documents))


# 기존 호환용 별칭
def create_simple_pdf(files) -> bytes:
    content = "\n".join([f"- {f.name}" for f in files])
    return create_report_pdf("문서 병합", content)
