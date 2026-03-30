"""
[GP-제90조] 모바일 최적화 유틸리티
Goldkey AI Masters 2026 - 반응형 테이블 및 카드 레이아웃
"""
import streamlit as st
import pandas as pd
from typing import List, Dict, Any, Optional


# ──────────────────────────────────────────────────────────────────────────
# [§1] 반응형 테이블 렌더링
# ──────────────────────────────────────────────────────────────────────────

def render_responsive_table(
    data: List[Dict[str, Any]],
    columns: List[str],
    column_labels: Optional[Dict[str, str]] = None,
    mobile_card_template: Optional[str] = None
) -> None:
    """
    데스크톱에서는 테이블, 모바일에서는 카드 형태로 렌더링.
    
    Args:
        data: 데이터 리스트 (딕셔너리 배열)
        columns: 표시할 컬럼 리스트
        column_labels: 컬럼 라벨 매핑 (예: {"name": "이름", "age": "나이"})
        mobile_card_template: 모바일 카드 HTML 템플릿 (선택)
    """
    if not data:
        st.info("표시할 데이터가 없습니다.")
        return
    
    # 컬럼 라벨 기본값 설정
    if column_labels is None:
        column_labels = {col: col for col in columns}
    
    # 데스크톱 테이블 (st.table 사용 - 가로 스크롤 없음)
    df = pd.DataFrame(data)[columns]
    df.columns = [column_labels.get(col, col) for col in columns]
    
    st.markdown(
        "<div class='desktop-only' style='display:block;'>",
        unsafe_allow_html=True
    )
    st.table(df)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 모바일 카드 (CSS로 숨김/표시 전환)
    st.markdown(
        "<div class='mobile-only' style='display:none;'>",
        unsafe_allow_html=True
    )
    
    for idx, row in enumerate(data):
        if mobile_card_template:
            # 커스텀 템플릿 사용
            card_html = mobile_card_template.format(**row)
        else:
            # 기본 카드 템플릿
            card_html = _generate_default_card(row, columns, column_labels)
        
        st.markdown(card_html, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


def _generate_default_card(
    row: Dict[str, Any],
    columns: List[str],
    column_labels: Dict[str, str]
) -> str:
    """
    기본 모바일 카드 HTML 생성.
    
    Args:
        row: 데이터 행
        columns: 컬럼 리스트
        column_labels: 컬럼 라벨 매핑
        
    Returns:
        카드 HTML 문자열
    """
    card_items = ""
    for col in columns:
        label = column_labels.get(col, col)
        value = row.get(col, "")
        card_items += (
            f"<div style='margin-bottom:8px;'>"
            f"<span style='font-size:0.75rem;color:#6b7280;font-weight:700;'>{label}:</span> "
            f"<span style='font-size:0.85rem;color:#1e293b;'>{value}</span>"
            f"</div>"
        )
    
    return (
        f"<div style='background:#ffffff;border:1px dashed #000;border-radius:8px;"
        f"padding:12px;margin-bottom:12px;'>"
        f"{card_items}"
        f"</div>"
    )


# ──────────────────────────────────────────────────────────────────────────
# [§2] 반응형 CSS 주입
# ──────────────────────────────────────────────────────────────────────────

def inject_mobile_responsive_css() -> None:
    """
    모바일 반응형 CSS를 앱에 주입.
    """
    st.markdown(
        """
        <style>
        /* 모바일 최적화 CSS */
        @media (max-width: 768px) {
            .desktop-only {
                display: none !important;
            }
            .mobile-only {
                display: block !important;
            }
            
            /* 테이블 가로 스크롤 방지 */
            .stDataFrame {
                overflow-x: hidden !important;
            }
            
            /* 컬럼 너비 자동 조절 */
            .stColumn {
                width: 100% !important;
                min-width: 0 !important;
            }
            
            /* 버튼 풀 너비 */
            .stButton > button {
                width: 100% !important;
            }
            
            /* 폰트 크기 조절 */
            body {
                font-size: 14px !important;
            }
            
            h1 {
                font-size: 1.5rem !important;
            }
            
            h2 {
                font-size: 1.2rem !important;
            }
            
            h3 {
                font-size: 1rem !important;
            }
        }
        
        @media (min-width: 769px) {
            .desktop-only {
                display: block !important;
            }
            .mobile-only {
                display: none !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# ──────────────────────────────────────────────────────────────────────────
# [§3] 반응형 그리드 레이아웃
# ──────────────────────────────────────────────────────────────────────────

def render_responsive_grid(
    items: List[Dict[str, Any]],
    desktop_cols: int = 3,
    mobile_cols: int = 1,
    card_renderer: Optional[callable] = None
) -> None:
    """
    반응형 그리드 레이아웃 렌더링.
    
    Args:
        items: 아이템 리스트
        desktop_cols: 데스크톱 컬럼 수
        mobile_cols: 모바일 컬럼 수
        card_renderer: 카드 렌더링 함수 (선택)
    """
    if not items:
        st.info("표시할 항목이 없습니다.")
        return
    
    # 데스크톱 그리드
    st.markdown(
        "<div class='desktop-only'>",
        unsafe_allow_html=True
    )
    
    for i in range(0, len(items), desktop_cols):
        cols = st.columns(desktop_cols)
        for j, col in enumerate(cols):
            if i + j < len(items):
                with col:
                    if card_renderer:
                        card_renderer(items[i + j])
                    else:
                        st.write(items[i + j])
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 모바일 그리드
    st.markdown(
        "<div class='mobile-only'>",
        unsafe_allow_html=True
    )
    
    for i in range(0, len(items), mobile_cols):
        cols = st.columns(mobile_cols)
        for j, col in enumerate(cols):
            if i + j < len(items):
                with col:
                    if card_renderer:
                        card_renderer(items[i + j])
                    else:
                        st.write(items[i + j])
    
    st.markdown("</div>", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────
# [§4] 모바일 친화적 입력 폼
# ──────────────────────────────────────────────────────────────────────────

def render_mobile_friendly_form(
    fields: List[Dict[str, Any]],
    submit_label: str = "제출",
    form_key: str = "mobile_form"
) -> Optional[Dict[str, Any]]:
    """
    모바일 친화적 입력 폼 렌더링.
    
    Args:
        fields: 필드 정의 리스트
            [
                {"name": "name", "label": "이름", "type": "text", "required": True},
                {"name": "age", "label": "나이", "type": "number", "min": 0, "max": 120},
                {"name": "gender", "label": "성별", "type": "select", "options": ["남", "여"]}
            ]
        submit_label: 제출 버튼 라벨
        form_key: 폼 고유 키
        
    Returns:
        제출된 데이터 딕셔너리 또는 None
    """
    with st.form(form_key):
        form_data = {}
        
        for field in fields:
            field_name = field["name"]
            field_label = field.get("label", field_name)
            field_type = field.get("type", "text")
            required = field.get("required", False)
            
            # 필수 표시
            if required:
                field_label = f"{field_label} *"
            
            # 필드 타입별 렌더링
            if field_type == "text":
                form_data[field_name] = st.text_input(
                    field_label,
                    key=f"{form_key}_{field_name}"
                )
            elif field_type == "number":
                min_val = field.get("min", None)
                max_val = field.get("max", None)
                form_data[field_name] = st.number_input(
                    field_label,
                    min_value=min_val,
                    max_value=max_val,
                    key=f"{form_key}_{field_name}"
                )
            elif field_type == "select":
                options = field.get("options", [])
                form_data[field_name] = st.selectbox(
                    field_label,
                    options,
                    key=f"{form_key}_{field_name}"
                )
            elif field_type == "date":
                form_data[field_name] = st.date_input(
                    field_label,
                    key=f"{form_key}_{field_name}"
                )
            elif field_type == "textarea":
                form_data[field_name] = st.text_area(
                    field_label,
                    key=f"{form_key}_{field_name}"
                )
        
        # 제출 버튼
        submitted = st.form_submit_button(submit_label, use_container_width=True, type="primary")
        
        if submitted:
            # 필수 필드 검증
            for field in fields:
                if field.get("required", False):
                    field_name = field["name"]
                    if not form_data.get(field_name):
                        st.error(f"{field.get('label', field_name)}은(는) 필수 항목입니다.")
                        return None
            
            return form_data
    
    return None


# ──────────────────────────────────────────────────────────────────────────
# [§5] 모바일 최적화 체크
# ──────────────────────────────────────────────────────────────────────────

def is_mobile_device() -> bool:
    """
    모바일 디바이스 여부 감지 (JavaScript 기반).
    
    Returns:
        True: 모바일 디바이스
        False: 데스크톱
    """
    # Streamlit에서는 직접 감지 불가, CSS 미디어 쿼리로 처리
    # 이 함수는 서버 사이드에서 사용 불가, 클라이언트 사이드 CSS로 대체
    return False


def get_optimal_column_count() -> int:
    """
    화면 크기에 따른 최적 컬럼 수 반환.
    
    Returns:
        컬럼 수 (1~4)
    """
    # 기본값: 데스크톱 3열
    # 실제 화면 크기는 CSS 미디어 쿼리로 처리
    return 3
