# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] crm_coverage_analysis_block.py
# STEP 6-9: 보장 분석 결과 화면 - 3단 일람표 + 다이내믹 필터링
# 2026-03-29 신규 생성 - GP 감성 프롬프트 + 영업 친화적 UI
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import pandas as pd
from typing import Optional


def render_coverage_comparison_table(
    coverage_data: list[dict],
    customer_name: str = "고객",
) -> None:
    """
    [STEP 8] 3단 보장 일람표 렌더링.
    
    Args:
        coverage_data: 보장 분석 결과 리스트
            [
                {
                    "category": "암 진단비",
                    "current_amount": 3000,  # 만원
                    "shortage_amount": 2000,  # 만원
                    "recommended_amount": 5000,  # 만원
                    "insurance_type": "장기",  # 장기/자동차/화재/운전자/연금/암
                },
                ...
            ]
        customer_name: 고객 이름
    """
    if not coverage_data:
        st.info("분석할 보장 데이터가 없습니다.")
        return
    
    # ── 헤더 ──────────────────────────────────────────────────────────
    st.markdown(
        f"<div style='background:linear-gradient(135deg, #667eea 0%, #764ba2 100%);"
        "border-radius:12px;padding:16px;margin-bottom:16px;'>"
        f"<div style='font-size:1.1rem;font-weight:700;color:#fff;margin-bottom:6px;'>"
        f"📊 {customer_name}님 보장 분석 결과 — 3단 일람표</div>"
        "<div style='font-size:0.78rem;color:#e0e7ff;line-height:1.6;'>"
        "💡 현재 가입금액과 부족한 금액, AI 제안금액을 한눈에 비교하세요.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    # ── DataFrame 생성 ─────────────────────────────────────────────────
    df_rows = []
    for item in coverage_data:
        df_rows.append({
            "보장 항목": item.get("category", ""),
            "현재 가입금액 (만원)": f"{item.get('current_amount', 0):,}",
            "부족한 금액 (만원)": f"{item.get('shortage_amount', 0):,}",
            "AI 제안금액 (만원)": f"{item.get('recommended_amount', 0):,}",
            "종목": item.get("insurance_type", ""),
        })
    
    df = pd.DataFrame(df_rows)
    
    # ── 스타일링된 테이블 렌더링 ──────────────────────────────────────
    st.markdown("""
<style>
/* 3단 일람표 테이블 스타일링 */
.coverage-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 0.85rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-radius: 8px;
    overflow: hidden;
}
.coverage-table thead tr {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    text-align: left;
    font-weight: 700;
}
.coverage-table th,
.coverage-table td {
    padding: 12px 14px;
    border-bottom: 1px solid #e5e7eb;
}
.coverage-table tbody tr:hover {
    background-color: #f3f4f6;
}
.coverage-table tbody tr:last-child td {
    border-bottom: none;
}
/* 금액 컬럼 우측 정렬 */
.coverage-table td:nth-child(2),
.coverage-table td:nth-child(3),
.coverage-table td:nth-child(4) {
    text-align: right;
    font-weight: 600;
}
/* 현재 가입금액 - 빨강 */
.coverage-table td:nth-child(2) {
    color: #dc2626;
}
/* 부족한 금액 - 주황 */
.coverage-table td:nth-child(3) {
    color: #f59e0b;
}
/* AI 제안금액 - 초록 */
.coverage-table td:nth-child(4) {
    color: #059669;
}
</style>
""", unsafe_allow_html=True)
    
    # Streamlit DataFrame 대신 HTML 테이블로 렌더링 (스타일 적용)
    table_html = df.to_html(index=False, classes="coverage-table", escape=False)
    st.markdown(table_html, unsafe_allow_html=True)
    
    # ── 감성 메시지 ───────────────────────────────────────────────────
    total_shortage = sum(item.get("shortage_amount", 0) for item in coverage_data)
    if total_shortage > 0:
        st.markdown(
            f"<div style='background:#fef3c7;border-left:4px solid #f59e0b;"
            "border-radius:8px;padding:14px 16px;margin-top:16px;'>"
            "<div style='font-size:0.88rem;font-weight:700;color:#92400e;margin-bottom:6px;'>"
            f"💬 {customer_name}님께 드리는 진심 어린 조언</div>"
            "<div style='font-size:0.82rem;color:#78350f;line-height:1.7;'>"
            f"고객님, 현재 <b style='color:#dc2626;'>총 {total_shortage:,}만원</b>의 보장이 부족한 상황입니다. "
            "이 부분의 위험이 진심으로 걱정됩니다. 만약의 상황에서 경제적 어려움이 가중될 수 있어 "
            "마음이 무겁습니다. 아래 AI 제안금액을 참고하시어 보장을 보강해 주시길 간곡히 부탁드립니다."
            "</div></div>",
            unsafe_allow_html=True,
        )


def render_insurance_type_filter(
    coverage_data: list[dict],
    filter_key: str = "coverage_filter",
) -> list[str]:
    """
    [STEP 7] 보험 종목별 다이내믹 필터링 UI.
    
    Args:
        coverage_data: 보장 분석 결과 리스트
        filter_key: 세션 상태 키
    
    Returns:
        선택된 보험 종목 리스트 (예: ["장기", "암"])
    """
    if not coverage_data:
        return []
    
    # ── 사용 가능한 보험 종목 추출 ─────────────────────────────────────
    available_types = sorted(set(
        item.get("insurance_type", "기타")
        for item in coverage_data
        if item.get("insurance_type")
    ))
    
    if not available_types:
        return []
    
    # ── 필터 UI 렌더링 ────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#f0f9ff;border-radius:10px;padding:12px 16px;"
        "margin-bottom:16px;border:1px solid #bae6fd;'>"
        "<div style='font-size:0.88rem;font-weight:700;color:#0c4a6e;margin-bottom:8px;'>"
        "🔍 보험 종목별 필터링</div>"
        "<div style='font-size:0.75rem;color:#475569;margin-bottom:10px;'>"
        "아래 버튼을 선택하여 특정 종목만 보거나 전체를 볼 수 있습니다.</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    
    # ── st.pills 또는 st.multiselect 사용 ────────────────────────────
    # Streamlit 1.35+ 에서 st.pills 사용 가능
    try:
        selected_types = st.pills(
            "보험 종목 선택",
            options=["전체"] + available_types,
            selection_mode="multi",
            key=filter_key,
            label_visibility="collapsed",
        )
    except AttributeError:
        # st.pills 미지원 시 st.multiselect 폴백
        selected_types = st.multiselect(
            "보험 종목 선택",
            options=["전체"] + available_types,
            default=["전체"],
            key=filter_key,
            label_visibility="collapsed",
        )
    
    # ── "전체" 선택 시 모든 종목 반환 ──────────────────────────────────
    if not selected_types or "전체" in selected_types:
        return available_types
    
    return selected_types


def render_filtered_coverage_analysis(
    coverage_data: list[dict],
    customer_name: str = "고객",
    filter_key: str = "coverage_filter",
) -> None:
    """
    [STEP 7 + STEP 8] 통합 렌더링: 필터링 UI + 3단 일람표.
    
    Args:
        coverage_data: 보장 분석 결과 리스트
        customer_name: 고객 이름
        filter_key: 세션 상태 키
    """
    if not coverage_data:
        st.info("분석할 보장 데이터가 없습니다.")
        return
    
    # ── STEP 7: 필터링 UI ─────────────────────────────────────────────
    selected_types = render_insurance_type_filter(coverage_data, filter_key)
    
    # ── 필터링된 데이터 ───────────────────────────────────────────────
    filtered_data = [
        item for item in coverage_data
        if item.get("insurance_type") in selected_types
    ]
    
    if not filtered_data:
        st.warning("선택한 종목에 해당하는 보장 데이터가 없습니다.")
        return
    
    # ── STEP 8: 3단 일람표 ────────────────────────────────────────────
    render_coverage_comparison_table(filtered_data, customer_name)


# ══════════════════════════════════════════════════════════════════════════════
# 샘플 데이터 생성 함수 (테스트용)
# ══════════════════════════════════════════════════════════════════════════════
def generate_sample_coverage_data() -> list[dict]:
    """테스트용 샘플 보장 데이터 생성."""
    return [
        {
            "category": "암 진단비",
            "current_amount": 3000,
            "shortage_amount": 2000,
            "recommended_amount": 5000,
            "insurance_type": "장기",
        },
        {
            "category": "뇌혈관 진단비",
            "current_amount": 2000,
            "shortage_amount": 3000,
            "recommended_amount": 5000,
            "insurance_type": "장기",
        },
        {
            "category": "심장 진단비",
            "current_amount": 1000,
            "shortage_amount": 4000,
            "recommended_amount": 5000,
            "insurance_type": "장기",
        },
        {
            "category": "자동차 대인배상 II",
            "current_amount": 10000,
            "shortage_amount": 0,
            "recommended_amount": 10000,
            "insurance_type": "자동차",
        },
        {
            "category": "자동차 대물배상",
            "current_amount": 5000,
            "shortage_amount": 5000,
            "recommended_amount": 10000,
            "insurance_type": "자동차",
        },
        {
            "category": "화재보험 건물",
            "current_amount": 20000,
            "shortage_amount": 10000,
            "recommended_amount": 30000,
            "insurance_type": "화재",
        },
        {
            "category": "운전자 벌금",
            "current_amount": 2000,
            "shortage_amount": 1000,
            "recommended_amount": 3000,
            "insurance_type": "운전자",
        },
        {
            "category": "개인연금",
            "current_amount": 50000,
            "shortage_amount": 50000,
            "recommended_amount": 100000,
            "insurance_type": "연금",
        },
    ]
