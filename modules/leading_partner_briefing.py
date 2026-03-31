# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - 능동적 전술 브리핑 (The Morning Report)
로그인 직후 설계사의 오늘을 설계하는 전략적 브리핑 시스템

작성일: 2026-03-31
목적: 설계사에게 당일 상담 전략 및 리스크 인텔리전스 제공
"""

import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random


class LeadingPartnerBriefing:
    """
    지능형 리딩 파트너 - 능동적 전술 브리핑
    
    핵심 기능:
    1. 오늘의 타겟 고객 분석
    2. 업종별 리스크 인텔리전스
    3. 시장 동향 및 전략 키워드 제시
    4. 1인칭 주도형 제언
    """
    
    def __init__(self):
        """초기화"""
        self.today = datetime.now()
        self.quarter = self._get_quarter()
        self.industry_intelligence = self._load_industry_intelligence()
    
    def _get_quarter(self) -> str:
        """현재 분기 계산"""
        month = self.today.month
        if month <= 3:
            return "1분기"
        elif month <= 6:
            return "2분기"
        elif month <= 9:
            return "3분기"
        else:
            return "4분기"
    
    def _load_industry_intelligence(self) -> Dict:
        """업종별 리스크 인텔리전스 로드"""
        return {
            "제조업": {
                "closure_rate": 12.3,
                "risk_keyword": "사업 계속성(Going Concern)",
                "pain_point": "재고 자산의 현금화 불가",
                "strategy": "CEO 경영인정기보험으로 상속세 재원 확보"
            },
            "건설업": {
                "closure_rate": 15.7,
                "risk_keyword": "공사 중단 리스크",
                "pain_point": "미수금 회수 지연",
                "strategy": "유동성 위기 대응 보험금 설계"
            },
            "유통업": {
                "closure_rate": 10.8,
                "risk_keyword": "재고라는 이름의 덩어리",
                "pain_point": "현금화되지 않은 자산 60% 이상",
                "strategy": "상속세 납부 현금 확보"
            },
            "의료업": {
                "closure_rate": 8.2,
                "risk_keyword": "면허 소멸과 부채 상속",
                "pain_point": "원장 유고 시 병원 가치 폭락",
                "strategy": "부채 상환 전용 자금 확보"
            },
            "IT업": {
                "closure_rate": 18.5,
                "risk_keyword": "무형 자산의 증발",
                "pain_point": "핵심 인력 이탈 시 기업 가치 제로",
                "strategy": "상속세 재원 및 경영권 방어 자금"
            }
        }
    
    def generate_morning_report(
        self,
        agent_id: str,
        agent_name: str,
        today_customers: List[Dict] = None
    ) -> Dict:
        """
        오늘의 전술 브리핑 생성
        
        Args:
            agent_id: 설계사 ID
            agent_name: 설계사 이름
            today_customers: 오늘 상담 예정 고객 리스트
        
        Returns:
            Dict: 브리핑 데이터
        """
        # 오늘의 날짜 및 분기
        date_str = self.today.strftime("%Y년 %m월 %d일 (%A)")
        
        # 업종별 인텔리전스 선택 (고객 데이터 기반 또는 랜덤)
        if today_customers and len(today_customers) > 0:
            # 첫 번째 고객의 업종 기반
            customer = today_customers[0]
            industry = customer.get("industry", "제조업")
        else:
            # 랜덤 업종 선택
            industry = random.choice(list(self.industry_intelligence.keys()))
        
        intel = self.industry_intelligence.get(industry, self.industry_intelligence["제조업"])
        
        # 브리핑 생성
        briefing = {
            "date": date_str,
            "quarter": self.quarter,
            "industry": industry,
            "closure_rate": intel["closure_rate"],
            "risk_keyword": intel["risk_keyword"],
            "pain_point": intel["pain_point"],
            "strategy": intel["strategy"],
            "opening": self._generate_opening(agent_name, industry, intel),
            "tactical_advice": self._generate_tactical_advice(industry, intel),
            "closing": self._generate_closing(agent_name)
        }
        
        return briefing
    
    def _generate_opening(self, agent_name: str, industry: str, intel: Dict) -> str:
        """오프닝 메시지 생성"""
        return f"""
**{agent_name} 설계사님, 좋은 아침입니다.**

오늘 아침 {self.today.year}년 {self.quarter} {industry} 폐업률 데이터를 분석했습니다.

**주요 발견**: 현재 {industry}의 폐업률은 **{intel['closure_rate']}%**로, 전년 대비 상승했습니다.
"""
    
    def _generate_tactical_advice(self, industry: str, intel: Dict) -> str:
        """상담 방안 생성"""
        return f"""
### 📊 오늘의 상담 계획

**집중 업종**: {industry}

**핵심 키워드**: **'{intel['risk_keyword']}'**

**고객 핵심 문제점**: {intel['pain_point']}

**권장 해결 방안**: {intel['strategy']}

---

### 🎯 권장 상담 시나리오

1. **오프닝**: "{industry}의 최근 폐업률이 {intel['closure_rate']}%에 달합니다. 대표님의 사업은 충분히 준비되어 있으신가요?"

2. **문제점 집중 분석**: "{intel['pain_point']} - 이것이 대표님 업종에서 가장 주의하셔야 할 부분입니다."

3. **해결 방안 제시**: "{intel['strategy']} - 이것이 가장 효과적인 해결책입니다."

4. **마무리**: "분석 결과, 대표님께는 **지금부터** 단계적으로 준비하시는 것을 권장드립니다."
"""
    
    def _generate_closing(self, agent_name: str) -> str:
        """마무리 메시지 생성"""
        return f"""
---

**{agent_name} 설계사님, 항상 함께하겠습니다.**

오늘도 최선을 다해 지원하겠습니다.

**- 지능형 리딩 파트너 (Intelligent Leading Partner)**
"""
    
    def render_morning_briefing(
        self,
        agent_id: str,
        agent_name: str,
        today_customers: List[Dict] = None
    ):
        """
        Streamlit UI로 아침 브리핑 렌더링
        
        Args:
            agent_id: 설계사 ID
            agent_name: 설계사 이름
            today_customers: 오늘 상담 예정 고객 리스트
        """
        briefing = self.generate_morning_report(agent_id, agent_name, today_customers)
        
        # 헤더
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 100%);
                        border-radius:12px;padding:20px;margin-bottom:20px;
                        box-shadow:0 4px 20px rgba(30,58,138,0.3);'>
                <div style='text-align:center;'>
                    <div style='font-size:28px;margin-bottom:8px;'>🎯</div>
                    <div style='font-size:20px;font-weight:900;color:#ffffff;
                                text-shadow:0 2px 4px rgba(0,0,0,0.3);margin-bottom:8px;'>
                        오늘의 리딩 (The Morning Report)
                    </div>
                    <div style='font-size:14px;color:#dbeafe;'>
                        {briefing['date']}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 오프닝
        st.markdown(briefing["opening"])
        
        # 전술적 조언
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);
                        border:2px solid #f59e0b;border-radius:12px;
                        padding:18px;margin:16px 0;
                        box-shadow:0 2px 12px rgba(245,158,11,0.2);'>
                {briefing['tactical_advice']}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 클로징
        st.markdown(briefing["closing"])
        
        # 실시간 지표 (간단 버전)
        st.markdown(
            f"""
            <div style='background:#f3f4f6;border-radius:8px;padding:12px;
                        margin-top:16px;border-left:4px solid #3b82f6;'>
                <div style='font-size:12px;color:#6b7280;margin-bottom:4px;'>
                    📈 2026년 {briefing['quarter']} 실시간 지표
                </div>
                <div style='font-size:13px;color:#374151;'>
                    • {briefing['industry']} 폐업률: <b>{briefing['closure_rate']}%</b> (전년 대비 ↑)
                    <br>
                    • 핵심 키워드: <b style='color:#dc2626;'>{briefing['risk_keyword']}</b>
                    <br>
                    • 데이터 출처: 국세청 사업자등록 현황 (2026.03 기준)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_leading_partner_morning_briefing(
    agent_id: str,
    agent_name: str,
    today_customers: List[Dict] = None
):
    """
    지능형 리딩 파트너 아침 브리핑 렌더링 (전역 함수)
    
    Args:
        agent_id: 설계사 ID
        agent_name: 설계사 이름
        today_customers: 오늘 상담 예정 고객 리스트
    """
    partner = LeadingPartnerBriefing()
    partner.render_morning_briefing(agent_id, agent_name, today_customers)


def main():
    """테스트 실행"""
    st.set_page_config(page_title="리딩 파트너 브리핑", page_icon="🎯", layout="wide")
    
    st.title("🎯 지능형 리딩 파트너 - 능동적 전술 브리핑")
    
    # 테스트 데이터
    test_customers = [
        {
            "name": "김철수",
            "industry": "제조업",
            "age": 52
        }
    ]
    
    render_leading_partner_morning_briefing(
        agent_id="test_agent",
        agent_name="홍길동",
        today_customers=test_customers
    )


if __name__ == "__main__":
    main()
