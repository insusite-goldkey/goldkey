# ══════════════════════════════════════════════════════════════════════════════
# [GP-ZERO-TRUST] 뉴스 크롤링 서비스
# Zero-Trust 4단계 데이터 무결성 파이프라인 적용
# ══════════════════════════════════════════════════════════════════════════════

"""
Zero-Trust 뉴스 크롤링 아키텍처

Step 1: 순수 추출 (BeautifulSoup/Newspaper3k) - LLM 의존 금지
Step 2: AI 가공 (Temperature=0.0, Structured Output)
Step 3: Python 검증 레이어 (자동 교정 + 수치 검증)
Step 4: Human-in-the-Loop (승인 UI)
"""

import streamlit as st
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
import re

from modules.zero_trust_validator import (
    validate_financial_data,
    validate_pydantic_model,
    render_validation_warnings,
    render_validation_errors,
    ValidationResult
)


# ══════════════════════════════════════════════════════════════════════════════
# Step 2: Pydantic 구조화 출력 스키마
# ══════════════════════════════════════════════════════════════════════════════

class NewsAnalysisOutput(BaseModel):
    """뉴스 분석 구조화 스키마 - Gemini 강제 출력 포맷"""
    
    company: str = Field(
        description="보험사명 또는 기업명 (절대 변형 금지, 원본 유지)"
    )
    profit: Optional[str] = Field(
        default=None,
        description="순이익 금액 (예: 12조원, 3000억원)"
    )
    revenue: Optional[str] = Field(
        default=None,
        description="매출액 (예: 50조원)"
    )
    change_rate: Optional[str] = Field(
        default=None,
        description="증감률 (예: 15%, -3.5%)"
    )
    trend: str = Field(
        description="실적 추세 (상승/하락/유지)"
    )
    summary: str = Field(
        description="3줄 요약 (팩트 100% 유지)"
    )
    publish_date: Optional[str] = Field(
        default=None,
        description="발행일 (YYYY-MM-DD)"
    )
    source_url: Optional[str] = Field(
        default=None,
        description="원본 URL"
    )


# ══════════════════════════════════════════════════════════════════════════════
# Step 1: 순수 추출 (Pure Extraction)
# ══════════════════════════════════════════════════════════════════════════════

def extract_raw_news_text(url: str) -> Dict[str, Any]:
    """
    LLM 없이 순수 HTML 파싱으로 텍스트 추출
    
    Args:
        url: 뉴스 기사 URL
    
    Returns:
        {
            "title": "기사 제목",
            "text": "본문 텍스트",
            "publish_date": "발행일",
            "authors": ["저자"]
        }
    """
    try:
        from newspaper import Article
        
        article = Article(url, language='ko')
        article.download()
        article.parse()
        
        return {
            "title": article.title or "",
            "text": article.text or "",
            "publish_date": article.publish_date.strftime("%Y-%m-%d") if article.publish_date else None,
            "authors": article.authors or [],
            "url": url
        }
    except Exception as e:
        # Newspaper3k 실패 시 BeautifulSoup 폴백
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 제목 추출
            title = soup.find('h1') or soup.find('title')
            title_text = title.get_text(strip=True) if title else ""
            
            # 본문 추출 (p 태그 기반)
            paragraphs = soup.find_all('p')
            text = "\n".join([p.get_text(strip=True) for p in paragraphs])
            
            return {
                "title": title_text,
                "text": text,
                "publish_date": None,
                "authors": [],
                "url": url
            }
        except Exception as fallback_error:
            raise Exception(f"뉴스 추출 실패: {str(e)}, 폴백 실패: {str(fallback_error)}")


# ══════════════════════════════════════════════════════════════════════════════
# Step 2: AI 가공 (Temperature=0.0, Structured Output)
# ══════════════════════════════════════════════════════════════════════════════

def analyze_news_with_llm(raw_text: str, url: str) -> NewsAnalysisOutput:
    """
    Temperature=0.0 + Pydantic 강제 출력
    
    Args:
        raw_text: Step 1에서 추출한 순수 텍스트
        url: 원본 URL
    
    Returns:
        NewsAnalysisOutput 객체
    """
    try:
        import google.generativeai as genai
        import os
        
        # Gemini API 키 확인
        api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel(
            'gemini-1.5-pro',
            generation_config={
                "temperature": 0.0,  # 창의성 말살
                "response_mime_type": "application/json",
            }
        )
        
        prompt = f"""
CRITICAL: 기관명, 질병명, 수치(금액/날짜), 금융/의료 전문 용어는 절대 임의로 치환·변형하지 마라.
요약 과정에서도 팩트(명사/숫자)는 100% 원본을 유지하라.

다음 뉴스 기사를 분석하여 JSON 형식으로 응답하라:

{raw_text}

JSON Schema:
{{
    "company": "보험사명 또는 기업명 (원본 그대로)",
    "profit": "순이익 (예: 12조원, 없으면 null)",
    "revenue": "매출액 (예: 50조원, 없으면 null)",
    "change_rate": "증감률 (예: 15%, 없으면 null)",
    "trend": "상승 또는 하락 또는 유지",
    "summary": "3줄 요약 (팩트 100% 유지)",
    "publish_date": "발행일 (YYYY-MM-DD, 없으면 null)",
    "source_url": "{url}"
}}
"""
        
        response = model.generate_content(prompt)
        
        # JSON 파싱
        import json
        response_text = response.text.strip()
        
        # Markdown 코드 블록 제거
        if response_text.startswith("```"):
            response_text = re.sub(r"```json\n?", "", response_text)
            response_text = re.sub(r"```\n?", "", response_text)
        
        data = json.loads(response_text)
        
        return NewsAnalysisOutput(**data)
        
    except Exception as e:
        raise Exception(f"AI 분석 실패: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# Step 3 + Step 4: 통합 파이프라인
# ══════════════════════════════════════════════════════════════════════════════

def zero_trust_news_pipeline(url: str) -> None:
    """
    Zero-Trust 4단계 뉴스 크롤링 파이프라인
    
    Args:
        url: 뉴스 기사 URL
    """
    
    # ── Step 1: 순수 추출 ────────────────────────────────────────────────
    with st.spinner("📰 뉴스 기사 추출 중... (Step 1: Pure Extraction)"):
        try:
            raw_data = extract_raw_news_text(url)
            st.success(f"✅ 텍스트 추출 완료: {len(raw_data['text'])}자")
        except Exception as e:
            st.error(f"❌ 텍스트 추출 실패: {str(e)}")
            return
    
    # ── Step 2: AI 가공 (Temperature=0.0) ────────────────────────────────
    with st.spinner("🤖 AI 분석 중... (Step 2: LLM Analysis, Temperature=0.0)"):
        try:
            ai_result = analyze_news_with_llm(raw_data["text"], url)
            st.success("✅ AI 분석 완료")
        except Exception as e:
            st.error(f"❌ AI 분석 실패: {str(e)}")
            return
    
    # ── Step 3: Python 검증 레이어 ────────────────────────────────────────
    with st.spinner("🛡️ 데이터 검증 중... (Step 3: Validation Layer)"):
        validated_model, validation_result = validate_pydantic_model(
            NewsAnalysisOutput,
            ai_result.dict()
        )
        
        # 자동 교정 경고 표시
        render_validation_warnings(validation_result)
        
        # 검증 실패 시 에러 표시
        if not validation_result.is_valid:
            render_validation_errors(validation_result)
            st.error("❌ 검증 실패: 위 오류를 확인하고 데이터를 수정해주세요.")
        else:
            st.success("✅ 검증 완료")
    
    # ── Step 4: Human-in-the-Loop (승인 UI) ───────────────────────────────
    st.markdown("---")
    st.markdown("### 📋 AI 분석 결과 최종 검토")
    st.info("⚠️ **중요**: 기관명, 수치를 반드시 확인하세요! 승인 후 데이터베이스에 저장됩니다.")
    
    # 편집 가능한 데이터 에디터
    edited_data = st.data_editor(
        validation_result.data,
        num_rows="fixed",
        use_container_width=True,
        key=f"news_review_{hash(url)}",
        column_config={
            "company": st.column_config.TextColumn(
                "보험사/기업명",
                help="AI가 추출한 기관명 (수정 가능)",
                required=True
            ),
            "profit": st.column_config.TextColumn(
                "순이익",
                help="예: 12조원, 3000억원"
            ),
            "revenue": st.column_config.TextColumn(
                "매출액",
                help="예: 50조원"
            ),
            "change_rate": st.column_config.TextColumn(
                "증감률",
                help="예: 15%, -3.5%"
            ),
            "trend": st.column_config.SelectboxColumn(
                "추세",
                options=["상승", "하락", "유지"],
                required=True
            ),
            "summary": st.column_config.TextColumn(
                "요약",
                help="3줄 요약"
            ),
            "publish_date": st.column_config.DateColumn(
                "발행일",
                format="YYYY-MM-DD"
            ),
            "source_url": st.column_config.LinkColumn(
                "원본 URL"
            )
        }
    )
    
    # 승인/취소 버튼
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ 최종 승인 및 저장", type="primary", use_container_width=True):
            try:
                # Supabase 저장
                from shared_components import get_env_secret
                from supabase import create_client
                
                supabase_url = get_env_secret("SUPABASE_URL")
                supabase_key = get_env_secret("SUPABASE_KEY")
                supabase = create_client(supabase_url, supabase_key)
                
                # 저장 데이터 준비
                save_data = {
                    **edited_data,
                    "created_at": datetime.now().isoformat(),
                    "agent_id": st.session_state.get("user_id", "unknown")
                }
                
                # DB 저장
                response = supabase.table("gk_news").insert(save_data).execute()
                
                if response.data:
                    st.success("✅ 뉴스 데이터가 성공적으로 저장되었습니다!")
                    st.balloons()
                else:
                    st.error("❌ 저장 실패: 응답 데이터가 없습니다.")
                    
            except Exception as e:
                st.error(f"❌ 저장 실패: {str(e)}")
    
    with col2:
        if st.button("❌ 취소", use_container_width=True):
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 컴포넌트
# ══════════════════════════════════════════════════════════════════════════════

def render_news_crawler_ui():
    """뉴스 크롤러 UI 렌더링"""
    
    st.markdown("## 📰 Zero-Trust 뉴스 크롤러")
    st.markdown("**AI 환각 방지 4단계 파이프라인 적용**")
    
    # 파이프라인 설명
    with st.expander("🛡️ Zero-Trust 파이프라인이란?", expanded=False):
        st.markdown("""
        ### 4단계 데이터 무결성 방어 시스템
        
        1. **순수 추출 (Pure Extraction)**
           - BeautifulSoup/Newspaper3k로 100% Raw Text 추출
           - LLM에게 스크래핑과 해석을 동시에 맡기지 않음
        
        2. **AI 가공 (Temperature=0.0)**
           - Gemini 1.5 Pro, Temperature=0.0 (창의성 말살)
           - Pydantic 모델로 구조화된 출력 강제
           - "기관명, 수치는 절대 변형 금지" 프롬프트 강제
        
        3. **Python 검증 레이어**
           - 단어 자동 교정 (보병사 → 보험사)
           - 수치/날짜 형식 검증
           - 타입 검증
        
        4. **Human-in-the-Loop**
           - 설계사가 직접 확인 및 수정
           - 승인 후에만 DB 저장
        """)
    
    # URL 입력
    url = st.text_input(
        "뉴스 기사 URL",
        placeholder="https://example.com/news/article",
        help="보험/금융 관련 뉴스 기사 URL을 입력하세요"
    )
    
    # 크롤링 시작 버튼
    if st.button("🚀 크롤링 시작", type="primary", disabled=not url):
        if url:
            zero_trust_news_pipeline(url)
        else:
            st.warning("URL을 입력해주세요.")
    
    # 저장된 뉴스 목록
    st.markdown("---")
    st.markdown("### 📚 저장된 뉴스 목록")
    
    try:
        from shared_components import get_env_secret
        from supabase import create_client
        
        supabase_url = get_env_secret("SUPABASE_URL")
        supabase_key = get_env_secret("SUPABASE_KEY")
        supabase = create_client(supabase_url, supabase_key)
        
        # 최근 뉴스 10개 조회
        response = supabase.table("gk_news")\
            .select("*")\
            .order("created_at", desc=True)\
            .limit(10)\
            .execute()
        
        if response.data:
            st.dataframe(
                response.data,
                use_container_width=True,
                column_config={
                    "source_url": st.column_config.LinkColumn("원본 URL"),
                    "created_at": st.column_config.DatetimeColumn("등록일시")
                }
            )
        else:
            st.info("저장된 뉴스가 없습니다.")
            
    except Exception as e:
        st.warning(f"뉴스 목록 조회 실패: {str(e)}")
