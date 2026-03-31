# -*- coding: utf-8 -*-
"""
마케팅 포인트 추출 서비스
LLM을 사용하여 보험 리플릿에서 핵심 판매포인트 자동 추출

작성일: 2026-03-31
목적: 이달의 핵심 판매포인트를 LLM으로 추출하여 Supabase에 저장
"""

import os
from typing import List, Dict, Optional
from datetime import datetime

try:
    import openai
except ImportError:
    print("❌ openai 라이브러리가 설치되어 있지 않습니다.")
    raise

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    raise


class MarketingPointExtractor:
    """
    마케팅 포인트 추출 서비스
    
    핵심 기능:
    1. PDF 텍스트에서 LLM으로 핵심 판매포인트 추출
    2. 보험사 구분 (손해보험/생명보험) 자동 판별
    3. Supabase insurance_marketing_points 테이블에 저장
    """
    
    # 손해보험사 목록
    NON_LIFE_INSURANCE = [
        "삼성화재", "현대해상", "DB손해보험", "메리츠화재", "KB손해보험",
        "한화손해보험", "흥국화재", "롯데손해보험", "MG손해보험"
    ]
    
    # 생명보험사 목록
    LIFE_INSURANCE = [
        "삼성생명", "한화생명", "교보생명", "KB생명", "신한라이프",
        "미래에셋생명", "DGB생명", "ABL생명", "푸본현대생명"
    ]
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Args:
            openai_api_key: OpenAI API Key
            supabase_url: Supabase URL
            supabase_key: Supabase Service Key
        """
        # OpenAI 초기화
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        openai.api_key = self.openai_api_key
        
        # Supabase 초기화
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    def classify_company_type(self, company: str) -> str:
        """
        보험사 구분 (손해보험/생명보험)
        
        Args:
            company: 보험사명
        
        Returns:
            str: "손해보험" 또는 "생명보험"
        """
        if any(comp in company for comp in self.NON_LIFE_INSURANCE):
            return "손해보험"
        elif any(comp in company for comp in self.LIFE_INSURANCE):
            return "생명보험"
        else:
            # 기본값: 이름에 "손보", "화재" 포함 시 손해보험
            if "손보" in company or "화재" in company:
                return "손해보험"
            else:
                return "생명보험"
    
    def extract_marketing_points(
        self,
        text: str,
        company: str,
        max_points: int = 3
    ) -> List[str]:
        """
        LLM으로 핵심 판매포인트 추출
        
        Args:
            text: 리플릿 텍스트
            company: 보험사명
            max_points: 최대 추출 개수
        
        Returns:
            List[str]: 핵심 판매포인트 리스트
        """
        prompt = f"""당신은 보험 마케팅 전문가입니다.
다음 {company}의 보험 리플릿에서 고객에게 어필할 수 있는 핵심 판매포인트를 추출하세요.

[리플릿 내용]
{text[:3000]}

[추출 기준]
1. 고객 입장에서 가장 매력적인 혜택
2. 경쟁사 대비 차별화 포인트
3. 이달의 특별 프로모션 또는 신상품

[출력 형식]
- 각 포인트는 한 줄로 간결하게 (최대 50자)
- 최대 {max_points}개만 추출
- 번호나 기호 없이 텍스트만 출력
- 각 포인트는 줄바꿈으로 구분

예시:
암 진단 시 최대 5천만원 보장
월 보험료 30% 할인 이벤트 (3월 한정)
가입 즉시 건강검진 무료 쿠폰 제공
"""
        
        try:
            response = openai.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "당신은 보험 마케팅 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            content = response.choices[0].message.content.strip()
            
            # 줄바꿈으로 분리
            points = [line.strip() for line in content.split('\n') if line.strip()]
            
            # 최대 개수 제한
            return points[:max_points]
        
        except Exception as e:
            print(f"❌ LLM 추출 실패: {e}")
            return []
    
    def save_marketing_points(
        self,
        company: str,
        marketing_points: List[str],
        year: int,
        month: int,
        priority: int = 0
    ) -> bool:
        """
        마케팅 포인트를 Supabase에 저장
        
        Args:
            company: 보험사명
            marketing_points: 판매포인트 리스트
            year: 적용 연도
            month: 적용 월
            priority: 우선순위
        
        Returns:
            bool: 저장 성공 여부
        """
        company_type = self.classify_company_type(company)
        
        try:
            for idx, point in enumerate(marketing_points):
                data = {
                    "company": company,
                    "company_type": company_type,
                    "marketing_point": point,
                    "reference_year": year,
                    "reference_month": month,
                    "priority": priority - idx,  # 첫 번째가 가장 높은 우선순위
                    "extracted_at": datetime.now().isoformat()
                }
                
                self.supabase.table("insurance_marketing_points").insert(data).execute()
            
            return True
        
        except Exception as e:
            print(f"❌ 저장 실패: {e}")
            return False
    
    def process_leaflet(
        self,
        text: str,
        company: str,
        year: Optional[int] = None,
        month: Optional[int] = None,
        max_points: int = 3
    ) -> Dict[str, any]:
        """
        리플릿 처리 (추출 + 저장)
        
        Args:
            text: 리플릿 텍스트
            company: 보험사명
            year: 적용 연도 (기본값: 현재)
            month: 적용 월 (기본값: 현재)
            max_points: 최대 추출 개수
        
        Returns:
            Dict: 처리 결과
        """
        if year is None or month is None:
            now = datetime.now()
            year = year or now.year
            month = month or now.month
        
        print(f"\n{'='*70}")
        print(f"📊 마케팅 포인트 추출: {company} ({year}년 {month}월)")
        print(f"{'='*70}")
        
        # 1. LLM으로 추출
        print(f"\n🤖 [1/2] LLM 추출 중...")
        marketing_points = self.extract_marketing_points(text, company, max_points)
        
        if not marketing_points:
            return {
                "success": False,
                "message": "마케팅 포인트 추출 실패",
                "points": []
            }
        
        print(f"✅ {len(marketing_points)}개 포인트 추출 완료")
        for idx, point in enumerate(marketing_points, 1):
            print(f"   {idx}. {point}")
        
        # 2. Supabase에 저장
        print(f"\n💾 [2/2] Supabase 저장 중...")
        success = self.save_marketing_points(company, marketing_points, year, month)
        
        if success:
            print(f"✅ 저장 완료")
            return {
                "success": True,
                "message": f"{len(marketing_points)}개 포인트 저장 완료",
                "points": marketing_points,
                "company": company,
                "company_type": self.classify_company_type(company),
                "year": year,
                "month": month
            }
        else:
            return {
                "success": False,
                "message": "Supabase 저장 실패",
                "points": marketing_points
            }


def main():
    """테스트 실행"""
    print("=" * 70)
    print("📊 마케팅 포인트 추출 서비스")
    print("=" * 70)
    
    print("\n💡 사용 예시:")
    print("""
from hq_backend.services.marketing_point_extractor import MarketingPointExtractor

extractor = MarketingPointExtractor()

# 리플릿 처리
result = extractor.process_leaflet(
    text=leaflet_text,
    company="삼성생명",
    year=2026,
    month=3,
    max_points=3
)

if result["success"]:
    print(f"추출 완료: {result['points']}")
    """)


if __name__ == "__main__":
    main()
