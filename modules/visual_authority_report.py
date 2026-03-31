# -*- coding: utf-8 -*-
"""
지능형 리딩 파트너 - 시각적 권위의 완성 (Visual Authority)
금융 자산 감정서 수준의 고품격 리포트 생성 시스템

작성일: 2026-03-31
목적: 인포그래픽 중심의 권위 있는 디지털 감정서 발행
"""

import streamlit as st
from typing import Dict, List, Optional
from datetime import datetime
import base64
from io import BytesIO


class VisualAuthorityReport:
    """
    지능형 리딩 파트너 - 시각적 권위의 완성
    
    핵심 기능:
    1. 자산 감정서 톤의 리포트 디자인
    2. 인포그래픽 중심 시각화
    3. 수치와 그래프로 압도
    4. 리딩 파트너 정밀 분석본 타이틀
    """
    
    def __init__(self):
        """초기화"""
        self.report_timestamp = datetime.now()
        self.report_id = self._generate_report_id()
    
    def _generate_report_id(self) -> str:
        """리포트 고유 ID 생성"""
        return f"LP-{self.report_timestamp.strftime('%Y%m%d%H%M%S')}"
    
    def generate_authority_report(
        self,
        customer_name: str,
        customer_age: int,
        industry: str,
        analysis_data: Dict
    ) -> Dict:
        """
        권위 있는 분석 리포트 생성
        
        Args:
            customer_name: 고객 이름
            customer_age: 고객 나이
            industry: 업종
            analysis_data: 분석 데이터
        
        Returns:
            Dict: 리포트 데이터
        """
        report = {
            "report_id": self.report_id,
            "timestamp": self.report_timestamp.strftime("%Y년 %m월 %d일 %H:%M"),
            "customer_name": customer_name,
            "customer_age": customer_age,
            "industry": industry,
            "header": self._generate_header(),
            "executive_summary": self._generate_executive_summary(analysis_data),
            "risk_assessment": self._generate_risk_assessment(analysis_data),
            "strategic_recommendation": self._generate_strategic_recommendation(analysis_data),
            "footer": self._generate_footer()
        }
        
        return report
    
    def _generate_header(self) -> str:
        """리포트 헤더 생성"""
        return f"""
<div style='background:linear-gradient(135deg,#1e3a8a 0%,#3b82f6 50%,#60a5fa 100%);
            border-radius:16px;padding:32px;margin-bottom:24px;
            box-shadow:0 8px 32px rgba(30,58,138,0.4);
            border:2px solid #1e40af;'>
    <div style='text-align:center;'>
        <div style='font-size:48px;margin-bottom:12px;
                    filter:drop-shadow(0 4px 8px rgba(0,0,0,0.3));'>
            🏆
        </div>
        <div style='font-size:28px;font-weight:900;color:#ffffff;
                    text-shadow:0 3px 6px rgba(0,0,0,0.4);
                    letter-spacing:1px;margin-bottom:8px;'>
            지능형 리딩 파트너 정밀 분석본
        </div>
        <div style='font-size:16px;color:#dbeafe;
                    text-shadow:0 2px 4px rgba(0,0,0,0.3);
                    font-weight:600;'>
            Intelligent Leading Partner - Precision Analysis Report
        </div>
        <div style='margin-top:16px;padding-top:16px;
                    border-top:1px solid rgba(255,255,255,0.3);'>
            <div style='font-size:14px;color:#bfdbfe;'>
                리포트 ID: {self.report_id}
            </div>
            <div style='font-size:13px;color:#93c5fd;margin-top:4px;'>
                발행일시: {self.report_timestamp.strftime("%Y년 %m월 %d일 %H:%M:%S")}
            </div>
        </div>
    </div>
</div>
"""
    
    def _generate_executive_summary(self, analysis_data: Dict) -> str:
        """핵심 요약 생성"""
        total_risk = analysis_data.get("total_risk", 0)
        inheritance_tax = analysis_data.get("inheritance_tax", 0)
        additional_risks = analysis_data.get("additional_risks", {})
        
        return f"""
### 📊 핵심 요약

<div style='background:#ffffff;border:3px solid #3b82f6;
            border-radius:12px;padding:24px;margin:16px 0;
            box-shadow:0 4px 16px rgba(59,130,246,0.2);'>
    
    <div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
                gap:16px;margin-bottom:20px;'>
        
        <div style='background:linear-gradient(135deg,#fee2e2 0%,#fecaca 100%);
                    border-radius:10px;padding:16px;
                    border-left:5px solid #dc2626;'>
            <div style='font-size:12px;color:#991b1b;font-weight:700;
                        margin-bottom:6px;'>총 리스크 규모</div>
            <div style='font-size:26px;font-weight:900;color:#dc2626;'>
                {total_risk:,}
            </div>
            <div style='font-size:11px;color:#991b1b;margin-top:4px;'>원</div>
        </div>
        
        <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);
                    border-radius:10px;padding:16px;
                    border-left:5px solid #f59e0b;'>
            <div style='font-size:12px;color:#92400e;font-weight:700;
                        margin-bottom:6px;'>상속세 예상액</div>
            <div style='font-size:26px;font-weight:900;color:#f59e0b;'>
                {inheritance_tax:,}
            </div>
            <div style='font-size:11px;color:#92400e;margin-top:4px;'>원</div>
        </div>
        
        <div style='background:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 100%);
                    border-radius:10px;padding:16px;
                    border-left:5px solid #3b82f6;'>
            <div style='font-size:12px;color:#1e40af;font-weight:700;
                        margin-bottom:6px;'>추가 리스크</div>
            <div style='font-size:26px;font-weight:900;color:#3b82f6;'>
                {len(additional_risks)}
            </div>
            <div style='font-size:11px;color:#1e40af;margin-top:4px;'>건</div>
        </div>
        
    </div>
    
    <div style='background:#f9fafb;border-radius:8px;padding:14px;
                border-left:4px solid #6366f1;'>
        <div style='font-size:13px;color:#374151;line-height:1.6;'>
            <b style='color:#1e40af;'>분석 결과</b>, 현재 대표님께서 준비하셔야 할 금액은 총 
            <b style='color:#dc2626;'>{total_risk:,}원</b>입니다.
            <br><br>
            이는 상속세 <b>{inheritance_tax:,}원</b>과 
            사업 운영 자금 <b>{len(additional_risks)}건</b>을 합친 금액입니다.
            <br><br>
            <b style='color:#dc2626;'>지금부터 단계적으로 준비하시는 것을 권장드립니다.</b>
        </div>
    </div>
    
</div>
"""
    
    def _generate_risk_assessment(self, analysis_data: Dict) -> str:
        """위험 요소 평가 생성"""
        additional_risks = analysis_data.get("additional_risks", {})
        
        risk_items = ""
        for risk_name, risk_amount in additional_risks.items():
            risk_items += f"""
        <div style='background:#ffffff;border-radius:8px;padding:14px;
                    margin-bottom:10px;border-left:4px solid #ef4444;
                    box-shadow:0 2px 8px rgba(239,68,68,0.1);'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div style='font-size:14px;color:#374151;font-weight:600;'>
                    {risk_name.replace('_', ' ')}
                </div>
                <div style='font-size:18px;color:#dc2626;font-weight:900;'>
                    {risk_amount:,}원
                </div>
            </div>
        </div>
"""
        
        return f"""
### ⚠️ 위험 요소 평가

<div style='background:linear-gradient(135deg,#fef2f2 0%,#fee2e2 100%);
            border:2px solid #dc2626;border-radius:12px;
            padding:20px;margin:16px 0;
            box-shadow:0 4px 16px rgba(220,38,38,0.2);'>
    
    <div style='font-size:15px;color:#991b1b;font-weight:700;
                margin-bottom:16px;padding-bottom:12px;
                border-bottom:2px solid #fca5a5;'>
        📋 세부 리스크 항목
    </div>
    
    {risk_items}
    
    <div style='background:#7f1d1d;color:#ffffff;border-radius:8px;
                padding:14px;margin-top:16px;
                text-shadow:0 2px 4px rgba(0,0,0,0.3);'>
        <div style='font-size:13px;line-height:1.6;'>
            <b>💡 주의하실 점</b>
            <br><br>
            이러한 항목들은 경영자 부재 시 <b>바로 발생하는 비용</b>입니다.
            <br>
            충분한 현금이 없다면 사업을 계속 운영하기 어려울 수 있습니다.
        </div>
    </div>
    
</div>
"""
    
    def _generate_strategic_recommendation(self, analysis_data: Dict) -> str:
        """권장 해결 방안 생성"""
        strategy = analysis_data.get("strategy", "CEO 경영인정기보험 설계")
        
        return f"""
### 🎯 권장 해결 방안

<div style='background:linear-gradient(135deg,#ecfdf5 0%,#d1fae5 100%);
            border:2px solid #059669;border-radius:12px;
            padding:20px;margin:16px 0;
            box-shadow:0 4px 16px rgba(5,150,105,0.2);'>
    
    <div style='font-size:15px;color:#065f46;font-weight:700;
                margin-bottom:16px;'>
        💡 권장 해결 방안
    </div>
    
    <div style='background:#ffffff;border-radius:8px;padding:16px;
                border-left:4px solid #10b981;margin-bottom:14px;'>
        <div style='font-size:14px;color:#374151;line-height:1.7;'>
            <b style='color:#059669;'>핵심 방안</b>: {strategy}
            <br><br>
            이 방법은 상속세 납부 자금을 마련하면서 
            사업도 안정적으로 이어갈 수 있는 <b style='color:#dc2626;'>효과적인 해결책</b>입니다.
        </div>
    </div>
    
    <div style='background:#065f46;color:#ffffff;border-radius:8px;
                padding:16px;text-shadow:0 2px 4px rgba(0,0,0,0.3);'>
        <div style='font-size:14px;font-weight:700;margin-bottom:10px;'>
            📌 실행 단계
        </div>
        <div style='font-size:13px;line-height:1.8;'>
            <b>STEP 1</b>: 리스크 규모 확정 (완료)<br>
            <b>STEP 2</b>: 보험 설계 시뮬레이션<br>
            <b>STEP 3</b>: 계약자/수익자 구조 최적화<br>
            <b>STEP 4</b>: 즉시 실행
        </div>
    </div>
    
</div>
"""
    
    def _generate_footer(self) -> str:
        """리포트 푸터 생성"""
        return f"""
<div style='background:#f3f4f6;border-radius:10px;padding:20px;
            margin-top:24px;border-top:3px solid #3b82f6;'>
    <div style='text-align:center;'>
        <div style='font-size:13px;color:#6b7280;margin-bottom:8px;'>
            본 리포트는 <b style='color:#1e40af;'>지능형 리딩 파트너</b>가 
            정밀 분석하여 발행한 공식 문서입니다.
        </div>
        <div style='font-size:12px;color:#9ca3af;'>
            Intelligent Leading Partner - Precision Analysis System
        </div>
        <div style='font-size:11px;color:#d1d5db;margin-top:8px;'>
            © 2026 goldkey_Ai_masters2026. All rights reserved.
        </div>
    </div>
</div>
"""
    
    def render_authority_report(
        self,
        customer_name: str,
        customer_age: int,
        industry: str,
        analysis_data: Dict
    ):
        """
        Streamlit UI로 권위 리포트 렌더링
        
        Args:
            customer_name: 고객 이름
            customer_age: 고객 나이
            industry: 업종
            analysis_data: 분석 데이터
        """
        report = self.generate_authority_report(
            customer_name,
            customer_age,
            industry,
            analysis_data
        )
        
        # 헤더
        st.markdown(report["header"], unsafe_allow_html=True)
        
        # 고객 정보
        st.markdown(
            f"""
            <div style='background:#ffffff;border:2px solid #e5e7eb;
                        border-radius:10px;padding:16px;margin-bottom:20px;'>
                <div style='font-size:14px;color:#6b7280;margin-bottom:8px;'>
                    <b>분석 대상</b>
                </div>
                <div style='font-size:16px;color:#111827;font-weight:700;'>
                    {customer_name} 고객님 ({customer_age}세, {industry})
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Executive Summary
        st.markdown(report["executive_summary"], unsafe_allow_html=True)
        
        # Risk Assessment
        st.markdown(report["risk_assessment"], unsafe_allow_html=True)
        
        # Strategic Recommendation
        st.markdown(report["strategic_recommendation"], unsafe_allow_html=True)
        
        # Footer
        st.markdown(report["footer"], unsafe_allow_html=True)


def render_visual_authority_report(
    customer_name: str,
    customer_age: int,
    industry: str,
    analysis_data: Dict
):
    """
    시각적 권위 리포트 렌더링 (전역 함수)
    
    Args:
        customer_name: 고객 이름
        customer_age: 고객 나이
        industry: 업종
        analysis_data: 분석 데이터
    """
    report_gen = VisualAuthorityReport()
    report_gen.render_authority_report(customer_name, customer_age, industry, analysis_data)


def main():
    """테스트 실행"""
    st.set_page_config(page_title="시각적 권위 리포트", page_icon="🏆", layout="wide")
    
    st.title("🏆 지능형 리딩 파트너 - 시각적 권위의 완성")
    
    # 테스트 데이터
    test_analysis = {
        "total_risk": 450_000_000,
        "inheritance_tax": 300_000_000,
        "additional_risks": {
            "재고_덤핑_손실": 100_000_000,
            "미수금_회수_불능액": 50_000_000
        },
        "strategy": "CEO 경영인정기보험 + 유동성 확보 플랜"
    }
    
    render_visual_authority_report(
        customer_name="김철수",
        customer_age=52,
        industry="유통업",
        analysis_data=test_analysis
    )


if __name__ == "__main__":
    main()
