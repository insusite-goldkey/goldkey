# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - 무입력 상황 인지 (Zero-Touch Vision)
OCR + Context 자동 분석으로 설계사의 입력 피로도를 제로로 만드는 시스템

작성일: 2026-03-31
목적: 사진 한 장으로 증권 분석 및 전략 제시 완료
"""

import streamlit as st
from typing import Dict, Optional, List
from datetime import datetime
import re


class ZeroTouchVision:
    """
    지능형 리딩 파트너 - 무입력 상황 인지
    
    핵심 기능:
    1. OCR 자동 데이터 추출
    2. Context 기반 페르소나 매칭
    3. 즉시 전략 제시
    4. 1인칭 주도형 분석 보고
    """
    
    def __init__(self):
        """초기화"""
        self.analysis_timestamp = datetime.now()
    
    def analyze_insurance_certificate(
        self,
        ocr_text: str,
        image_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        증권 사진 자동 분석
        
        Args:
            ocr_text: OCR 추출 텍스트
            image_metadata: 이미지 메타데이터
        
        Returns:
            Dict: 분석 결과
        """
        # 1. 보험사 식별
        insurance_company = self._extract_insurance_company(ocr_text)
        
        # 2. 보험 종류 식별
        insurance_type = self._extract_insurance_type(ocr_text)
        
        # 3. 가입 금액 추출
        coverage_amount = self._extract_coverage_amount(ocr_text)
        
        # 4. 가입 일자 추출
        contract_date = self._extract_contract_date(ocr_text)
        
        # 5. 물가 상승률 반영 여부 판단
        inflation_adjusted = self._check_inflation_adjustment(contract_date, coverage_amount)
        
        # 6. 전략 키워드 생성
        strategy_keyword = self._generate_strategy_keyword(
            insurance_type,
            coverage_amount,
            inflation_adjusted
        )
        
        # 7. 리딩 파트너 분석 보고
        analysis_report = self._generate_analysis_report(
            insurance_company,
            insurance_type,
            coverage_amount,
            contract_date,
            inflation_adjusted,
            strategy_keyword
        )
        
        return {
            "insurance_company": insurance_company,
            "insurance_type": insurance_type,
            "coverage_amount": coverage_amount,
            "contract_date": contract_date,
            "inflation_adjusted": inflation_adjusted,
            "strategy_keyword": strategy_keyword,
            "analysis_report": analysis_report,
            "timestamp": self.analysis_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _extract_insurance_company(self, text: str) -> str:
        """보험사 추출"""
        companies = [
            "삼성생명", "한화생명", "교보생명", "신한라이프", "KB생명",
            "메리츠화재", "현대해상", "DB손해보험", "삼성화재", "KB손해보험"
        ]
        
        for company in companies:
            if company in text:
                return company
        
        return "미확인"
    
    def _extract_insurance_type(self, text: str) -> str:
        """보험 종류 추출"""
        types = {
            "종신보험": ["종신", "평생"],
            "정기보험": ["정기", "갱신"],
            "CI보험": ["CI", "중대질병", "암보험"],
            "실손보험": ["실손", "의료비"],
            "연금보험": ["연금", "노후"]
        }
        
        for insurance_type, keywords in types.items():
            for keyword in keywords:
                if keyword in text:
                    return insurance_type
        
        return "일반보험"
    
    def _extract_coverage_amount(self, text: str) -> int:
        """가입 금액 추출"""
        # 정규식으로 금액 패턴 추출
        patterns = [
            r'(\d{1,3}(?:,\d{3})*)\s*만원',
            r'(\d{1,3}(?:,\d{3})*)\s*억',
            r'보험가입금액[:\s]*(\d{1,3}(?:,\d{3})*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                amount_str = match.group(1).replace(',', '')
                amount = int(amount_str)
                
                # 단위 변환
                if '억' in text:
                    return amount * 100_000_000
                elif '만원' in text:
                    return amount * 10_000
                else:
                    return amount
        
        return 0
    
    def _extract_contract_date(self, text: str) -> Optional[str]:
        """가입 일자 추출"""
        # 날짜 패턴 추출
        patterns = [
            r'(\d{4})[년.-](\d{1,2})[월.-](\d{1,2})',
            r'가입일[:\s]*(\d{4})[년.-](\d{1,2})[월.-](\d{1,2})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        return None
    
    def _check_inflation_adjustment(
        self,
        contract_date: Optional[str],
        coverage_amount: int
    ) -> bool:
        """물가 상승률 반영 여부 판단"""
        if not contract_date:
            return False
        
        try:
            contract_year = int(contract_date.split('-')[0])
            current_year = datetime.now().year
            years_passed = current_year - contract_year
            
            # 5년 이상 경과 + 가입금액 1억 미만 = 물가 미반영
            if years_passed >= 5 and coverage_amount < 100_000_000:
                return False
            
            return True
        
        except:
            return False
    
    def _generate_strategy_keyword(
        self,
        insurance_type: str,
        coverage_amount: int,
        inflation_adjusted: bool
    ) -> str:
        """전략 키워드 생성"""
        if not inflation_adjusted:
            return "박제된 계약 (Frozen Contract)"
        
        if coverage_amount < 50_000_000:
            return "과소 보장 (Under-Coverage)"
        
        if insurance_type == "실손보험":
            return "갱신 리스크 (Renewal Risk)"
        
        return "정상 범위 (Normal Range)"
    
    def _generate_analysis_report(
        self,
        insurance_company: str,
        insurance_type: str,
        coverage_amount: int,
        contract_date: Optional[str],
        inflation_adjusted: bool,
        strategy_keyword: str
    ) -> str:
        """분석 보고서 생성"""
        report = f"""
### 🔍 분석 결과

**보험사**: {insurance_company}  
**보험 종류**: {insurance_type}  
**가입 금액**: {coverage_amount:,}원  
**가입 일자**: {contract_date or '미확인'}

---

### ⚠️ 주의하실 점

"""
        
        if not inflation_adjusted:
            report += f"""
**분석 결과**: 이 증권은 물가 상승률이 반영되지 않아 **'{strategy_keyword}'** 상태입니다.

{contract_date or '과거'}에 가입한 {coverage_amount:,}원은 현재 가치로 환산하면 **실질 보장액이 30% 이상 감소**한 상태입니다.

**권장 조치**: 현재 가치에 맞춰 보장 금액을 조정하시는 것을 권장드립니다.
"""
        elif coverage_amount < 50_000_000:
            report += f"""
**분석 결과**: 현재 가입 금액 {coverage_amount:,}원은 **'{strategy_keyword}'** 상태입니다.

2026년 기준 평균 의료비 및 생활비를 고려하면, 최소 1억원 이상의 보장이 필요합니다.

**권장 조치**: 추가 보장 설계를 검토하시는 것을 권장드립니다.
"""
        else:
            report += f"""
**분석 결과**: 현재 증권은 **'{strategy_keyword}'**에 해당합니다.

다만, 최신 상품과 비교 분석이 필요합니다.

**권장 조치**: 포트폴리오 최적화 상담을 진행하시는 것을 권장드립니다.
"""
        
        report += f"""

---

**분석 완료 시각**: {self.analysis_timestamp.strftime("%Y년 %m월 %d일 %H:%M:%S")}  
**분석자**: 지능형 리딩 파트너 (Intelligent Leading Partner)
"""
        
        return report
    
    def render_zero_touch_analysis(
        self,
        ocr_text: str,
        image_metadata: Optional[Dict] = None
    ):
        """
        Streamlit UI로 무입력 분석 렌더링
        
        Args:
            ocr_text: OCR 추출 텍스트
            image_metadata: 이미지 메타데이터
        """
        # 분석 실행
        result = self.analyze_insurance_certificate(ocr_text, image_metadata)
        
        # 헤더
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#059669 0%,#10b981 100%);
                        border-radius:12px;padding:20px;margin-bottom:20px;
                        box-shadow:0 4px 20px rgba(5,150,105,0.3);'>
                <div style='text-align:center;'>
                    <div style='font-size:28px;margin-bottom:8px;'>📸</div>
                    <div style='font-size:20px;font-weight:900;color:#ffffff;
                                text-shadow:0 2px 4px rgba(0,0,0,0.3);margin-bottom:8px;'>
                        무입력 상황 인지 (Zero-Touch Vision)
                    </div>
                    <div style='font-size:14px;color:#d1fae5;'>
                        사진 한 장으로 분석 완료
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 분석 보고서
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);
                        border:2px solid #f59e0b;border-radius:12px;
                        padding:18px;margin:16px 0;
                        box-shadow:0 2px 12px rgba(245,158,11,0.2);'>
                {result['analysis_report']}
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # 전략 키워드 강조
        keyword_color = "#dc2626" if not result['inflation_adjusted'] else "#059669"
        
        st.markdown(
            f"""
            <div style='background:#f3f4f6;border-radius:8px;padding:16px;
                        margin-top:16px;border-left:4px solid {keyword_color};'>
                <div style='font-size:14px;color:#374151;margin-bottom:8px;'>
                    <b>전략 키워드</b>
                </div>
                <div style='font-size:18px;font-weight:900;color:{keyword_color};'>
                    {result['strategy_keyword']}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


def render_zero_touch_vision_analysis(
    ocr_text: str,
    image_metadata: Optional[Dict] = None
):
    """
    무입력 상황 인지 분석 렌더링 (전역 함수)
    
    Args:
        ocr_text: OCR 추출 텍스트
        image_metadata: 이미지 메타데이터
    """
    vision = ZeroTouchVision()
    vision.render_zero_touch_analysis(ocr_text, image_metadata)


def main():
    """테스트 실행"""
    st.set_page_config(page_title="무입력 상황 인지", page_icon="📸", layout="wide")
    
    st.title("📸 지능형 리딩 파트너 - 무입력 상황 인지")
    
    # 테스트 OCR 텍스트
    test_ocr = """
    삼성생명보험주식회사
    종신보험증권
    
    보험가입금액: 5,000만원
    가입일: 2018년 03월 15일
    피보험자: 김철수
    """
    
    render_zero_touch_vision_analysis(test_ocr)


if __name__ == "__main__":
    main()
