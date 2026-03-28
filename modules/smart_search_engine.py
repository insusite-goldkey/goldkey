"""
[GP-SMART-SEARCH] 지능형 고객 검색 엔진 (HQ 전용)
- 성함(개인/CEO), 법인상호, 사업자등록번호로 즉시 조회
- 법인상호 검색 시 법인격 표기((주), 주식회사, (유), 유한회사) 무시하고 실제 상호 본 이름 기준 매칭
"""
from __future__ import annotations
import re
from typing import Optional


def normalize_company_name(name: str) -> str:
    """
    법인상호를 정규화하여 실제 상호 본 이름만 추출.
    
    예시:
        '(주)삼성' → '삼성'
        '삼성 주식회사' → '삼성'
        '유한회사 삼성' → '삼성'
        '삼성전자(주)' → '삼성전자'
    """
    if not name:
        return ""
    
    # 법인격 표기 패턴 정의
    patterns = [
        r'\(주\)',           # (주)
        r'\(유\)',           # (유)
        r'주식회사\s*',      # 주식회사
        r'유한회사\s*',      # 유한회사
        r'\s*주식회사',      # 주식회사 (뒤)
        r'\s*유한회사',      # 유한회사 (뒤)
        r'\(주식회사\)',     # (주식회사)
        r'\(유한회사\)',     # (유한회사)
        r'㈜',               # ㈜
        r'㈲',               # ㈲
    ]
    
    normalized = name.strip()
    for pattern in patterns:
        normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
    
    # 연속된 공백 제거 및 양쪽 공백 제거
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    return normalized


def normalize_business_number(number: str) -> str:
    """
    사업자등록번호를 정규화 (숫자만 추출).
    
    예시:
        '123-45-67890' → '1234567890'
        '123 45 67890' → '1234567890'
    """
    if not number:
        return ""
    
    # 숫자만 추출
    return re.sub(r'\D', '', number)


def smart_search_customers(
    query: str,
    customers: list[dict],
    search_fields: Optional[list[str]] = None
) -> list[dict]:
    """
    지능형 고객 검색 엔진.
    
    Args:
        query: 검색어 (성함, 법인상호, 사업자등록번호)
        customers: 고객 리스트 (각 dict는 name, company, business_number 등 포함)
        search_fields: 검색할 필드 목록 (기본값: ['name', 'company', 'business_number'])
    
    Returns:
        매칭된 고객 리스트
    """
    if not query or not customers:
        return []
    
    if search_fields is None:
        search_fields = ['name', 'company', 'business_number', 'job']
    
    query = query.strip()
    if not query:
        return []
    
    # 검색어 정규화
    normalized_query = normalize_company_name(query)
    normalized_query_lower = normalized_query.lower()
    
    # 사업자등록번호 검색용
    normalized_query_number = normalize_business_number(query)
    
    results = []
    
    for customer in customers:
        matched = False
        
        # 1. 성함 검색 (정확 매칭 + 부분 매칭)
        if 'name' in search_fields:
            name = str(customer.get('name', '') or '').strip()
            if name:
                if query in name or name in query:
                    matched = True
                elif normalized_query_lower in name.lower():
                    matched = True
        
        # 2. 법인상호 검색 (법인격 무시)
        if not matched and 'company' in search_fields:
            company = str(customer.get('company', '') or customer.get('job', '') or '').strip()
            if company:
                normalized_company = normalize_company_name(company)
                normalized_company_lower = normalized_company.lower()
                
                # 정규화된 상호 기준 매칭
                if normalized_query_lower in normalized_company_lower:
                    matched = True
                elif normalized_company_lower in normalized_query_lower:
                    matched = True
        
        # 3. 사업자등록번호 검색
        if not matched and 'business_number' in search_fields:
            business_number = str(customer.get('business_number', '') or '').strip()
            if business_number:
                normalized_bn = normalize_business_number(business_number)
                if normalized_query_number and normalized_query_number in normalized_bn:
                    matched = True
        
        # 4. 직업 필드 추가 검색 (법인상호가 job에 저장된 경우)
        if not matched and 'job' in search_fields:
            job = str(customer.get('job', '') or '').strip()
            if job:
                normalized_job = normalize_company_name(job)
                normalized_job_lower = normalized_job.lower()
                
                if normalized_query_lower in normalized_job_lower:
                    matched = True
                elif normalized_job_lower in normalized_query_lower:
                    matched = True
        
        if matched:
            results.append(customer)
    
    return results


def render_smart_search_widget(user_id: str, on_select_callback=None):
    """
    HQ 메인 대시보드용 스마트 검색 위젯 (조회 전용).
    
    Args:
        user_id: 현재 로그인한 사용자 ID
        on_select_callback: 고객 선택 시 호출할 콜백 함수
    """
    import streamlit as st
    
    st.markdown(
        "<div style='background:linear-gradient(135deg,#e0f2fe 0%,#bae6fd 100%);"
        "border:1px dashed #0369a1;border-radius:12px;padding:14px 18px;margin-bottom:12px;'>"
        "<div style='font-size:clamp(13px,2vw,16px);font-weight:900;color:#0c4a6e;margin-bottom:8px;'>"
        "🔍 지능형 고객 검색 (성함·법인상호·사업자번호)</div>"
        "<div style='font-size:clamp(11px,1.6vw,13px);color:#075985;'>"
        "💡 법인상호 검색 시 (주), 주식회사 등 법인격 표기 자동 무시</div>"
        "</div>",
        unsafe_allow_html=True
    )
    
    search_query = st.text_input(
        "🔍 검색어 입력",
        placeholder="예: 삼성, 123-45-67890, 홍길동",
        key="hq_smart_search_input",
        label_visibility="collapsed"
    )
    
    if search_query and search_query.strip():
        try:
            # 고객 데이터 로드 (CRM Fortress)
            try:
                from crm_fortress import search_people
                from shared_components import get_env_secret
                from supabase import create_client as _create_sb_client
                
                _sb_url = get_env_secret("SUPABASE_URL")
                _sb_key = get_env_secret("SUPABASE_KEY")
                _sb = _create_sb_client(_sb_url, _sb_key) if _sb_url and _sb_key else None
                
                all_customers = search_people(_sb, user_id) if _sb else []
            except Exception:
                # Fallback: 세션 캐시에서 로드
                all_customers = st.session_state.get("customers", [])
            
            # 스마트 검색 실행
            results = smart_search_customers(search_query, all_customers)
            
            if results:
                st.success(f"✅ {len(results)}명의 고객이 검색되었습니다.")
                
                # 결과 표시
                for idx, customer in enumerate(results[:10]):  # 최대 10개까지 표시
                    name = customer.get('name', '이름 없음')
                    company = customer.get('company') or customer.get('job', '')
                    person_id = customer.get('person_id', '')
                    
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        display_text = f"**{name}**"
                        if company:
                            normalized_company = normalize_company_name(company)
                            display_text += f" · {normalized_company}"
                        st.markdown(display_text)
                    
                    with col2:
                        if st.button("선택", key=f"select_customer_{idx}_{person_id}", use_container_width=True):
                            if on_select_callback:
                                on_select_callback(customer)
                            else:
                                st.session_state["selected_customer_id"] = person_id
                                st.session_state["selected_customer"] = customer
                                st.success(f"✅ {name} 고객이 선택되었습니다.")
                
                if len(results) > 10:
                    st.caption(f"💡 {len(results) - 10}명의 추가 결과가 있습니다. 검색어를 더 구체적으로 입력하세요.")
            else:
                st.warning("⚠️ 검색 결과가 없습니다.")
        
        except Exception as e:
            st.error(f"🔴 검색 오류: {e}")
