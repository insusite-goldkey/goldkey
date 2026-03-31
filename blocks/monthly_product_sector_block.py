# -*- coding: utf-8 -*-
"""
이달의 상품 섹터 블록
보험사별 핵심 판매포인트 표시

작성일: 2026-03-31
목적: 매월 신규 리플릿에서 추출한 마케팅 포인트를 파스텔톤 박스로 표시
디자인: 밝은 파스텔톤 배경 + 2px 검은 테두리 + 연한 구분선
"""

import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional

try:
    from supabase import create_client
except ImportError:
    st.error("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    st.stop()


def render_monthly_product_sector(
    year: Optional[int] = None,
    month: Optional[int] = None
):
    """
    이달의 상품 섹터 박스 렌더링
    
    디자인 가이드:
    - 밝은 파스텔톤 배경색 (#F0F4FF)
    - 2px 두께의 검은색 외곽선 (Solid Black Border)
    - 반응형 유기적 타이포그래피
    - 보험사 간 연한 구분선 (Light Gray Divider)
    
    노출 로직:
    - 손해보험사 7개 우선
    - 생명보험사 3개
    - 초기 10줄만 노출, 이상은 내부 스크롤
    
    Args:
        year: 조회 연도 (기본값: 현재)
        month: 조회 월 (기본값: 현재)
    """
    if year is None or month is None:
        now = datetime.now()
        year = year or now.year
        month = month or now.month
    
    # Supabase에서 데이터 조회
    try:
        supabase_url = st.secrets.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
        supabase_key = st.secrets.get("SUPABASE_SERVICE_KEY") or st.secrets.get("supabase", {}).get("service_key")
        
        if not supabase_url or not supabase_key:
            st.warning("⚠️ Supabase 설정이 없습니다.")
            return
        
        supabase = create_client(supabase_url, supabase_key)
        
        # RPC 함수 호출
        result = supabase.rpc(
            "get_monthly_marketing_points",
            {
                "target_year": year,
                "target_month": month,
                "limit_count": 10
            }
        ).execute()
        
        if not result.data or len(result.data) == 0:
            st.info(f"📭 {year}년 {month}월 마케팅 포인트가 없습니다.")
            return
        
        # 데이터 분류
        non_life_insurance = []  # 손해보험
        life_insurance = []  # 생명보험
        
        for row in result.data:
            if row["company_type"] == "손해보험" and len(non_life_insurance) < 7:
                non_life_insurance.append(row)
            elif row["company_type"] == "생명보험" and len(life_insurance) < 3:
                life_insurance.append(row)
        
        # 전체 데이터 병합 (손해보험 우선)
        all_points = non_life_insurance + life_insurance
        
        if not all_points:
            st.info(f"📭 {year}년 {month}월 마케팅 포인트가 없습니다.")
            return
        
        # CSS 스타일 정의
        # GP 전역 UI/UX 렌더링 헌법 준수: unsafe_allow_html=True 필수
        sector_css = """
        <style>
        .monthly-product-sector {
            background-color: #F0F4FF;
            border: 2px solid #000000;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
        }
        
        .sector-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 16px;
            padding-bottom: 12px;
            border-bottom: 2px solid #000000;
        }
        
        .sector-item {
            padding: 12px 0;
            border-bottom: 1px solid #E5E7EB;
        }
        
        .sector-item:last-child {
            border-bottom: none;
        }
        
        .company-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: #2563eb;
            margin-bottom: 6px;
        }
        
        .company-type-badge {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
            margin-left: 8px;
        }
        
        .badge-non-life {
            background-color: #FEF3C7;
            color: #92400E;
        }
        
        .badge-life {
            background-color: #DBEAFE;
            color: #1E40AF;
        }
        
        .marketing-point {
            font-size: 0.95rem;
            color: #374151;
            line-height: 1.6;
            padding-left: 16px;
            word-wrap: break-word;
            max-width: 100%;
        }
        
        .sector-footer {
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid #D1D5DB;
            font-size: 0.85rem;
            color: #6B7280;
            text-align: center;
        }
        </style>
        """
        
        # HTML 렌더링
        html_content = f"""
        {sector_css}
        <div class="monthly-product-sector">
            <div class="sector-header">
                📊 이달의 상품 ({year}년 {month}월)
            </div>
        """
        
        for idx, point in enumerate(all_points, 1):
            company_type_class = "badge-non-life" if point["company_type"] == "손해보험" else "badge-life"
            
            html_content += f"""
            <div class="sector-item">
                <div class="company-name">
                    {point["company"]}
                    <span class="company-type-badge {company_type_class}">
                        {point["company_type"]}
                    </span>
                </div>
                <div class="marketing-point">
                    {point["marketing_point"]}
                </div>
            </div>
            """
        
        html_content += f"""
            <div class="sector-footer">
                손해보험 {len(non_life_insurance)}개 · 생명보험 {len(life_insurance)}개 · 총 {len(all_points)}개 포인트
            </div>
        </div>
        """
        
        # GP 전역 UI/UX 렌더링 헌법 준수: unsafe_allow_html=True 필수
        st.markdown(html_content, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ 이달의 상품 조회 실패: {e}")


def render_monthly_product_sector_simple():
    """
    이달의 상품 섹터 (간단 버전)
    현재 년월 자동 적용
    """
    now = datetime.now()
    render_monthly_product_sector(year=now.year, month=now.month)


# 테스트 실행
if __name__ == "__main__":
    st.set_page_config(
        page_title="이달의 상품 섹터 테스트",
        layout="wide"
    )
    
    st.title("📊 이달의 상품 섹터 블록 테스트")
    
    # 연월 선택
    col1, col2 = st.columns(2)
    with col1:
        year = st.number_input("연도", min_value=2020, max_value=2030, value=datetime.now().year)
    with col2:
        month = st.number_input("월", min_value=1, max_value=12, value=datetime.now().month)
    
    # 렌더링
    render_monthly_product_sector(year=year, month=month)
