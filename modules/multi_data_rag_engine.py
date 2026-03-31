# -*- coding: utf-8 -*-
"""
멀티 데이터 RAG 엔진 (Multi-Data RAG Engine)
재무제표 + 의료기록 + 보험증권 통합 분석

작성일: 2026-03-31
목적: 현금 흐름 대비 보장 자산 적정성 도출
"""

from typing import Dict, List, Optional, Tuple
import json


class MultiDataRAGEngine:
    """
    멀티 데이터 RAG 엔진
    
    핵심 기능:
    1. 재무제표 + 보험증권 교차 분석
    2. 의료기록 + 보험증권 교차 분석
    3. 재무 + 의료 + 보험 통합 분석
    4. 현금 흐름 대비 보장 적정성 도출
    """
    
    def __init__(self):
        """초기화"""
        self.financial_data = None
        self.medical_data = None
        self.insurance_data = None
    
    def integrate_financial_insurance(
        self, 
        financial_statement: Dict,
        insurance_policies: List[Dict]
    ) -> Dict:
        """
        재무제표 + 보험증권 통합 분석
        
        Args:
            financial_statement: 재무제표 데이터
            insurance_policies: 보험증권 리스트
        
        Returns:
            통합 분석 결과
        """
        # 1. 현금 흐름 분석
        cash_flow = self._analyze_cash_flow(financial_statement)
        
        # 2. 보험료 부담 능력 평가
        premium_affordability = self._evaluate_premium_affordability(
            cash_flow, insurance_policies
        )
        
        # 3. 보장 적정성 평가
        coverage_adequacy = self._evaluate_coverage_adequacy(
            financial_statement, insurance_policies
        )
        
        # 4. Gap 분석
        gap_analysis = self._generate_financial_insurance_gap(
            premium_affordability, coverage_adequacy
        )
        
        return {
            "cash_flow_analysis": cash_flow,
            "premium_affordability": premium_affordability,
            "coverage_adequacy": coverage_adequacy,
            "gap_analysis": gap_analysis,
            "strategic_recommendation": self._generate_financial_recommendation(gap_analysis)
        }
    
    def integrate_medical_insurance(
        self,
        medical_records: List[Dict],
        insurance_policies: List[Dict]
    ) -> Dict:
        """
        의료기록 + 보험증권 통합 분석
        
        Args:
            medical_records: 의료기록 리스트
            insurance_policies: 보험증권 리스트
        
        Returns:
            통합 분석 결과
        """
        # 1. 질병 코드 추출
        disease_codes = self._extract_disease_codes(medical_records)
        
        # 2. 보장 공백 분석
        coverage_gaps = self._analyze_medical_coverage_gaps(
            disease_codes, insurance_policies
        )
        
        # 3. 인수 가능성 평가
        underwriting_risk = self._evaluate_underwriting_risk(
            medical_records, insurance_policies
        )
        
        return {
            "disease_codes": disease_codes,
            "coverage_gaps": coverage_gaps,
            "underwriting_risk": underwriting_risk,
            "strategic_recommendation": self._generate_medical_recommendation(
                coverage_gaps, underwriting_risk
            )
        }
    
    def integrate_all_data(
        self,
        financial_statement: Dict,
        medical_records: List[Dict],
        insurance_policies: List[Dict]
    ) -> Dict:
        """
        재무 + 의료 + 보험 통합 분석 (All-in-One)
        
        Args:
            financial_statement: 재무제표 데이터
            medical_records: 의료기록 리스트
            insurance_policies: 보험증권 리스트
        
        Returns:
            통합 분석 결과
        """
        # 1. 재무-보험 분석
        financial_insurance = self.integrate_financial_insurance(
            financial_statement, insurance_policies
        )
        
        # 2. 의료-보험 분석
        medical_insurance = self.integrate_medical_insurance(
            medical_records, insurance_policies
        )
        
        # 3. 통합 리스크 평가
        integrated_risk = self._evaluate_integrated_risk(
            financial_insurance, medical_insurance
        )
        
        # 4. 최종 전략 수립
        final_strategy = self._generate_integrated_strategy(
            financial_insurance, medical_insurance, integrated_risk
        )
        
        return {
            "financial_insurance_analysis": financial_insurance,
            "medical_insurance_analysis": medical_insurance,
            "integrated_risk_assessment": integrated_risk,
            "final_strategy": final_strategy,
            "priority_actions": self._prioritize_actions(final_strategy)
        }
    
    def _analyze_cash_flow(self, financial_statement: Dict) -> Dict:
        """현금 흐름 분석"""
        income_statement = financial_statement.get("income_statement", {})
        
        operating_income = income_statement.get("operating_income", 0)
        net_income = income_statement.get("net_income", 0)
        
        # 영업현금흐름 추정 (영업이익 * 0.8)
        operating_cash_flow = operating_income * 0.8
        
        # 잉여현금흐름 추정
        capex = financial_statement.get("capex", operating_income * 0.2)
        free_cash_flow = operating_cash_flow - capex
        
        return {
            "operating_cash_flow": operating_cash_flow,
            "free_cash_flow": free_cash_flow,
            "cash_flow_ratio": free_cash_flow / operating_cash_flow if operating_cash_flow > 0 else 0
        }
    
    def _evaluate_premium_affordability(
        self,
        cash_flow: Dict,
        policies: List[Dict]
    ) -> Dict:
        """보험료 부담 능력 평가"""
        total_premium = sum(p.get("annual_premium", 0) for p in policies)
        free_cash_flow = cash_flow.get("free_cash_flow", 0)
        
        if free_cash_flow <= 0:
            affordability = "불가"
            premium_to_cf_ratio = 999.0
        else:
            premium_to_cf_ratio = total_premium / free_cash_flow
            
            if premium_to_cf_ratio < 0.05:
                affordability = "여유"
            elif premium_to_cf_ratio < 0.15:
                affordability = "적정"
            else:
                affordability = "과다"
        
        return {
            "total_annual_premium": total_premium,
            "premium_to_cash_flow_ratio": premium_to_cf_ratio,
            "affordability": affordability
        }
    
    def _evaluate_coverage_adequacy(
        self,
        financial_statement: Dict,
        policies: List[Dict]
    ) -> Dict:
        """보장 적정성 평가"""
        equity = financial_statement.get("equity", {})
        total_equity = equity.get("total_equity", 0)
        
        # CEO 유고 시 필요 자금 산출
        inheritance_tax = total_equity * 0.5 * 0.3  # 상속세 추정 (30%)
        operating_fund = financial_statement.get("liabilities", {}).get("current_liabilities", 0)
        total_need = inheritance_tax + operating_fund
        
        # 현재 보장액 합계
        total_coverage = sum(p.get("coverage_amount", 0) for p in policies)
        
        # Gap 분석
        gap = total_need - total_coverage
        
        if gap > 0:
            adequacy = "부족"
        elif gap < -total_need * 0.3:
            adequacy = "과다"
        else:
            adequacy = "적정"
        
        return {
            "total_need": total_need,
            "inheritance_tax_estimate": inheritance_tax,
            "operating_fund_need": operating_fund,
            "total_coverage": total_coverage,
            "gap": gap,
            "adequacy": adequacy
        }
    
    def _generate_financial_insurance_gap(
        self,
        premium_affordability: Dict,
        coverage_adequacy: Dict
    ) -> Dict:
        """재무-보험 Gap 분석"""
        gaps = []
        
        # 보험료 부담 과다
        if premium_affordability["affordability"] == "과다":
            gaps.append({
                "type": "premium_overload",
                "severity": "high",
                "message": "현금 흐름 대비 보험료 부담 과다",
                "impact": f"보험료가 잉여현금흐름의 {premium_affordability['premium_to_cash_flow_ratio']*100:.1f}% 차지"
            })
        
        # 보장액 부족
        if coverage_adequacy["adequacy"] == "부족":
            gaps.append({
                "type": "coverage_shortage",
                "severity": "high",
                "message": "CEO 유고 시 필요 자금 대비 보장액 부족",
                "impact": f"{coverage_adequacy['gap']:,.0f}원 부족"
            })
        
        return {
            "gaps": gaps,
            "total_gap_count": len(gaps),
            "critical_gap_count": sum(1 for g in gaps if g["severity"] == "high")
        }
    
    def _extract_disease_codes(self, medical_records: List[Dict]) -> List[Dict]:
        """질병 코드 추출"""
        disease_codes = []
        
        for record in medical_records:
            kcd_codes = record.get("kcd_codes", [])
            diagnoses = record.get("diagnoses", [])
            
            for i, code in enumerate(kcd_codes):
                disease_codes.append({
                    "kcd_code": code,
                    "diagnosis": diagnoses[i] if i < len(diagnoses) else "",
                    "diagnosis_date": record.get("diagnosis_date", ""),
                    "record_id": record.get("id", "")
                })
        
        return disease_codes
    
    def _analyze_medical_coverage_gaps(
        self,
        disease_codes: List[Dict],
        policies: List[Dict]
    ) -> Dict:
        """의료 보장 공백 분석"""
        gaps = []
        
        # 3대 진단비 확인
        major_diseases = ["암", "뇌졸중", "급성심근경색"]
        
        for disease_code in disease_codes:
            diagnosis = disease_code.get("diagnosis", "")
            
            # 3대 질병 여부 확인
            is_major = any(major in diagnosis for major in major_diseases)
            
            if is_major:
                # 해당 질병에 대한 보장 확인
                has_coverage = any(
                    any(major in item.get("name", "") for major in major_diseases)
                    for policy in policies
                    for item in policy.get("coverage_items", [])
                )
                
                if not has_coverage:
                    gaps.append({
                        "disease": diagnosis,
                        "kcd_code": disease_code.get("kcd_code", ""),
                        "severity": "high",
                        "message": f"{diagnosis}에 대한 진단비 보장 없음"
                    })
        
        return {
            "gaps": gaps,
            "gap_probability": min(len(gaps) * 20, 100)  # 최대 100%
        }
    
    def _evaluate_underwriting_risk(
        self,
        medical_records: List[Dict],
        policies: List[Dict]
    ) -> Dict:
        """인수 위험 평가"""
        risk_factors = []
        
        for record in medical_records:
            # 수술 이력
            surgeries = record.get("surgeries", [])
            if surgeries:
                risk_factors.append({
                    "type": "surgery_history",
                    "severity": "medium",
                    "message": f"과거 수술 이력 {len(surgeries)}건"
                })
            
            # 입원 이력
            admission_info = record.get("admission_info", {})
            if admission_info:
                risk_factors.append({
                    "type": "hospitalization_history",
                    "severity": "low",
                    "message": "입원 이력 존재"
                })
        
        return {
            "risk_factors": risk_factors,
            "total_risk_count": len(risk_factors),
            "underwriting_difficulty": "high" if len(risk_factors) > 2 else "medium" if len(risk_factors) > 0 else "low"
        }
    
    def _evaluate_integrated_risk(
        self,
        financial_insurance: Dict,
        medical_insurance: Dict
    ) -> Dict:
        """통합 리스크 평가"""
        total_risk_score = 0
        
        # 재무 리스크
        financial_gaps = financial_insurance.get("gap_analysis", {}).get("critical_gap_count", 0)
        total_risk_score += financial_gaps * 30
        
        # 의료 리스크
        medical_gaps = len(medical_insurance.get("coverage_gaps", {}).get("gaps", []))
        total_risk_score += medical_gaps * 20
        
        # 인수 리스크
        underwriting_difficulty = medical_insurance.get("underwriting_risk", {}).get("underwriting_difficulty", "low")
        if underwriting_difficulty == "high":
            total_risk_score += 30
        elif underwriting_difficulty == "medium":
            total_risk_score += 15
        
        # 리스크 등급
        if total_risk_score >= 70:
            risk_level = "매우 높음"
        elif total_risk_score >= 50:
            risk_level = "높음"
        elif total_risk_score >= 30:
            risk_level = "보통"
        else:
            risk_level = "낮음"
        
        return {
            "total_risk_score": total_risk_score,
            "risk_level": risk_level,
            "financial_risk_weight": financial_gaps * 30,
            "medical_risk_weight": medical_gaps * 20
        }
    
    def _generate_financial_recommendation(self, gap_analysis: Dict) -> List[str]:
        """재무 권장사항 생성"""
        recommendations = []
        
        gaps = gap_analysis.get("gaps", [])
        
        for gap in gaps:
            if gap["type"] == "premium_overload":
                recommendations.append(
                    "현금 흐름 개선 또는 보험료 절감 방안 검토 필요"
                )
            elif gap["type"] == "coverage_shortage":
                recommendations.append(
                    "경영인정기보험 추가 가입으로 CEO 유고 대비 강화"
                )
        
        return recommendations
    
    def _generate_medical_recommendation(
        self,
        coverage_gaps: Dict,
        underwriting_risk: Dict
    ) -> List[str]:
        """의료 권장사항 생성"""
        recommendations = []
        
        gaps = coverage_gaps.get("gaps", [])
        
        if gaps:
            recommendations.append(
                "3대 진단비 특약 추가 가입 권장"
            )
        
        if underwriting_risk.get("underwriting_difficulty") == "high":
            recommendations.append(
                "부담보 조건 협상 또는 무심사 보험 검토"
            )
        
        return recommendations
    
    def _generate_integrated_strategy(
        self,
        financial_insurance: Dict,
        medical_insurance: Dict,
        integrated_risk: Dict
    ) -> Dict:
        """통합 전략 수립"""
        strategy = {
            "priority": "high" if integrated_risk["risk_level"] in ["매우 높음", "높음"] else "medium",
            "actions": [],
            "timeline": "즉시" if integrated_risk["risk_level"] == "매우 높음" else "3개월 이내"
        }
        
        # 재무 전략
        strategy["actions"].extend(
            financial_insurance.get("strategic_recommendation", [])
        )
        
        # 의료 전략
        strategy["actions"].extend(
            medical_insurance.get("strategic_recommendation", [])
        )
        
        return strategy
    
    def _prioritize_actions(self, strategy: Dict) -> List[Dict]:
        """액션 우선순위화"""
        actions = strategy.get("actions", [])
        
        prioritized = []
        
        for i, action in enumerate(actions):
            prioritized.append({
                "priority": i + 1,
                "action": action,
                "urgency": "즉시" if i < 2 else "3개월 이내"
            })
        
        return prioritized


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_multi_data_rag_demo():
    """
    멀티 데이터 RAG 데모 UI
    
    사용법:
        from modules.multi_data_rag_engine import render_multi_data_rag_demo
        render_multi_data_rag_demo()
    """
    import streamlit as st
    
    st.markdown("### 🔗 멀티 데이터 RAG 엔진")
    
    # 샘플 데이터
    sample_financial = {
        "income_statement": {
            "revenue": 5_000_000_000,
            "operating_income": 500_000_000,
            "net_income": 300_000_000
        },
        "equity": {
            "total_equity": 2_000_000_000
        },
        "liabilities": {
            "current_liabilities": 500_000_000
        },
        "capex": 100_000_000
    }
    
    sample_medical = [
        {
            "kcd_codes": ["I63.9"],
            "diagnoses": ["뇌경색"],
            "diagnosis_date": "2024-01-15",
            "surgeries": ["혈전제거술"],
            "admission_info": {"days": 14}
        }
    ]
    
    sample_insurance = [
        {
            "insurance_company": "삼성생명",
            "annual_premium": 50_000_000,
            "coverage_amount": 100_000_000,
            "coverage_items": [
                {"name": "일반사망보험금", "amount": 100_000_000}
            ]
        }
    ]
    
    if st.button("통합 분석 시작"):
        engine = MultiDataRAGEngine()
        
        result = engine.integrate_all_data(
            sample_financial,
            sample_medical,
            sample_insurance
        )
        
        st.markdown("### 📊 통합 분석 결과")
        
        # 통합 리스크 평가
        risk_assessment = result["integrated_risk_assessment"]
        st.markdown(f"**통합 리스크 등급**: {risk_assessment['risk_level']}")
        st.markdown(f"**리스크 점수**: {risk_assessment['total_risk_score']}/100")
        
        # 최종 전략
        final_strategy = result["final_strategy"]
        st.markdown("### 🎯 최종 전략")
        st.markdown(f"**우선순위**: {final_strategy['priority']}")
        st.markdown(f"**실행 시기**: {final_strategy['timeline']}")
        
        # 우선 액션
        priority_actions = result["priority_actions"]
        st.markdown("### 📋 우선 액션")
        for action in priority_actions:
            st.markdown(f"{action['priority']}. {action['action']} ({action['urgency']})")
        
        # JSON 데이터
        with st.expander("JSON 데이터", expanded=False):
            st.json(result)
