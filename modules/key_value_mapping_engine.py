# -*- coding: utf-8 -*-
"""
Key-Value 매핑 엔진 (Key-Value Mapping Engine)
보험증권 담보명-금액 구조화 추출

작성일: 2026-03-31
목적: OCR 텍스트 → 구조화된 보험 데이터 변환
"""

import re
from typing import Dict, List, Optional, Tuple
import json


class KeyValueMappingEngine:
    """
    Key-Value 매핑 엔진
    
    핵심 기능:
    1. 보험증권 담보명-금액 추출
    2. 계약 정보 구조화 (보험사, 계약일, 만기일)
    3. 보장 내역 테이블 파싱
    4. KB 7대 스탠다드 자동 분류
    """
    
    def __init__(self):
        """초기화"""
        self.coverage_patterns = self._build_coverage_patterns()
        self.company_patterns = self._build_company_patterns()
        self.amount_patterns = self._build_amount_patterns()
    
    def _build_coverage_patterns(self) -> List[str]:
        """담보명 패턴 정의"""
        return [
            # 사망 관련
            r"(일반|질병|상해)?사망보험금",
            r"(재해|교통재해)?사망",
            r"사망담보",
            
            # 진단비 관련
            r"(암|뇌졸중|급성심근경색)진단비",
            r"3대질병진단비",
            r"(일반암|유사암|소액암)진단비",
            r"(뇌출혈|뇌경색)진단비",
            
            # 수술/입원 관련
            r"수술급여금",
            r"입원일당",
            r"입원급여금",
            r"통원치료비",
            
            # 실손 관련
            r"실손의료비",
            r"실손보험금",
            r"의료실비",
            
            # 배상책임
            r"배상책임보험금",
            r"대인배상",
            r"대물배상",
            
            # 기타
            r"장해급여금",
            r"골절진단비",
            r"화상진단비",
            r"치아보험금",
            r"치매진단비",
            r"간병비",
        ]
    
    def _build_company_patterns(self) -> List[str]:
        """보험사명 패턴 정의"""
        return [
            r"삼성생명", r"삼성화재",
            r"한화생명", r"한화손해보험",
            r"KB생명", r"KB손해보험",
            r"메리츠화재", r"메리츠생명",
            r"현대해상", r"현대라이프",
            r"AIA생명", r"AIA",
            r"교보생명", r"교보라이프플래닛",
            r"신한생명", r"신한라이프",
            r"DB생명", r"DB손해보험",
            r"흥국생명", r"흥국화재",
            r"동양생명", r"동부화재",
        ]
    
    def _build_amount_patterns(self) -> List[str]:
        """금액 패턴 정의"""
        return [
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*원",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*만원",
            r"(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*억원",
        ]
    
    def extract_insurance_policy_data(self, ocr_text: str) -> Dict:
        """
        보험증권 데이터 추출 (Main Entry Point)
        
        Args:
            ocr_text: OCR 추출 텍스트
        
        Returns:
            구조화된 보험 데이터
        """
        result = {
            "insurance_company": self._extract_company(ocr_text),
            "contract_info": self._extract_contract_info(ocr_text),
            "coverage_items": self._extract_coverage_items(ocr_text),
            "kb_standard_classification": {},
            "total_coverage_amount": 0
        }
        
        # KB 7대 스탠다드 자동 분류
        result["kb_standard_classification"] = self._classify_kb_standard(
            result["coverage_items"]
        )
        
        # 총 보장액 계산
        result["total_coverage_amount"] = sum(
            item["amount"] for item in result["coverage_items"]
        )
        
        return result
    
    def _extract_company(self, text: str) -> Optional[str]:
        """보험사명 추출"""
        for pattern in self.company_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_contract_info(self, text: str) -> Dict:
        """계약 정보 추출"""
        contract_info = {
            "contract_number": None,
            "contract_date": None,
            "maturity_date": None,
            "insured_name": None,
            "contractor_name": None
        }
        
        # 증권번호
        contract_num_match = re.search(
            r"증권번호[:\s]*([A-Z0-9\-]+)", text
        )
        if contract_num_match:
            contract_info["contract_number"] = contract_num_match.group(1)
        
        # 계약일
        contract_date_match = re.search(
            r"계약일[:\s]*(\d{4})[.-](\d{1,2})[.-](\d{1,2})", text
        )
        if contract_date_match:
            contract_info["contract_date"] = f"{contract_date_match.group(1)}-{contract_date_match.group(2).zfill(2)}-{contract_date_match.group(3).zfill(2)}"
        
        # 만기일
        maturity_date_match = re.search(
            r"만기일[:\s]*(\d{4})[.-](\d{1,2})[.-](\d{1,2})", text
        )
        if maturity_date_match:
            contract_info["maturity_date"] = f"{maturity_date_match.group(1)}-{maturity_date_match.group(2).zfill(2)}-{maturity_date_match.group(3).zfill(2)}"
        
        # 피보험자
        insured_match = re.search(r"피보험자[:\s]*([가-힣]{2,4})", text)
        if insured_match:
            contract_info["insured_name"] = insured_match.group(1)
        
        # 계약자
        contractor_match = re.search(r"계약자[:\s]*([가-힣]{2,4})", text)
        if contractor_match:
            contract_info["contractor_name"] = contractor_match.group(1)
        
        return contract_info
    
    def _extract_coverage_items(self, text: str) -> List[Dict]:
        """담보 항목 추출"""
        coverage_items = []
        
        # 텍스트를 줄 단위로 분리
        lines = text.split('\n')
        
        for line in lines:
            # 각 담보 패턴 매칭
            for pattern in self.coverage_patterns:
                match = re.search(pattern, line)
                if match:
                    coverage_name = match.group(0)
                    
                    # 해당 줄에서 금액 추출
                    amount = self._extract_amount_from_line(line)
                    
                    if amount > 0:
                        coverage_items.append({
                            "name": coverage_name,
                            "amount": amount,
                            "original_text": line.strip()
                        })
        
        return coverage_items
    
    def _extract_amount_from_line(self, line: str) -> int:
        """줄에서 금액 추출"""
        # 억원 단위
        billion_match = re.search(r"(\d+(?:\.\d+)?)\s*억", line)
        if billion_match:
            return int(float(billion_match.group(1)) * 100_000_000)
        
        # 만원 단위
        ten_thousand_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*만원", line)
        if ten_thousand_match:
            amount_str = ten_thousand_match.group(1).replace(',', '')
            return int(amount_str) * 10_000
        
        # 원 단위
        won_match = re.search(r"(\d{1,3}(?:,\d{3})*)\s*원", line)
        if won_match:
            amount_str = won_match.group(1).replace(',', '')
            return int(amount_str)
        
        return 0
    
    def _classify_kb_standard(self, coverage_items: List[Dict]) -> Dict:
        """
        KB 7대 스탠다드 자동 분류
        
        1. 질병/상해 사망
        2. 3대 진단비 (암·뇌졸중·급성심근경색)
        3. 수술/입원비
        4. 실손의료비
        5. 운전자/배상책임
        6. 치아/치매/간병
        7. 연금/저축
        """
        kb_classification = {
            "1_death": [],
            "2_three_major_diagnosis": [],
            "3_surgery_hospitalization": [],
            "4_actual_medical_expense": [],
            "5_driver_liability": [],
            "6_dental_dementia_care": [],
            "7_pension_savings": []
        }
        
        for item in coverage_items:
            name = item["name"]
            
            # 1. 사망
            if re.search(r"사망", name):
                kb_classification["1_death"].append(item)
            
            # 2. 3대 진단비
            elif re.search(r"(암|뇌졸중|급성심근경색)진단비", name):
                kb_classification["2_three_major_diagnosis"].append(item)
            
            # 3. 수술/입원
            elif re.search(r"(수술|입원)", name):
                kb_classification["3_surgery_hospitalization"].append(item)
            
            # 4. 실손
            elif re.search(r"실손", name):
                kb_classification["4_actual_medical_expense"].append(item)
            
            # 5. 운전자/배상책임
            elif re.search(r"(배상|운전자)", name):
                kb_classification["5_driver_liability"].append(item)
            
            # 6. 치아/치매/간병
            elif re.search(r"(치아|치매|간병)", name):
                kb_classification["6_dental_dementia_care"].append(item)
        
        return kb_classification
    
    def generate_coverage_summary(self, policy_data: Dict) -> str:
        """
        보장 내역 요약 생성
        
        Args:
            policy_data: extract_insurance_policy_data() 결과
        
        Returns:
            요약 텍스트
        """
        summary_lines = []
        
        # 보험사 및 계약 정보
        if policy_data["insurance_company"]:
            summary_lines.append(f"**보험사**: {policy_data['insurance_company']}")
        
        contract_info = policy_data["contract_info"]
        if contract_info["contract_number"]:
            summary_lines.append(f"**증권번호**: {contract_info['contract_number']}")
        if contract_info["contract_date"]:
            summary_lines.append(f"**계약일**: {contract_info['contract_date']}")
        
        # 총 보장액
        total_amount = policy_data["total_coverage_amount"]
        summary_lines.append(f"\n**총 보장액**: {total_amount:,}원")
        
        # KB 7대 스탠다드 분류별 요약
        summary_lines.append("\n### KB 7대 스탠다드 분류")
        
        kb_labels = {
            "1_death": "1. 질병/상해 사망",
            "2_three_major_diagnosis": "2. 3대 진단비",
            "3_surgery_hospitalization": "3. 수술/입원비",
            "4_actual_medical_expense": "4. 실손의료비",
            "5_driver_liability": "5. 운전자/배상책임",
            "6_dental_dementia_care": "6. 치아/치매/간병",
            "7_pension_savings": "7. 연금/저축"
        }
        
        kb_classification = policy_data["kb_standard_classification"]
        
        for key, label in kb_labels.items():
            items = kb_classification.get(key, [])
            if items:
                summary_lines.append(f"\n**{label}**")
                for item in items:
                    summary_lines.append(f"- {item['name']}: {item['amount']:,}원")
        
        return "\n".join(summary_lines)


# ══════════════════════════════════════════════════════════════════════════════
# Streamlit UI 통합 함수
# ══════════════════════════════════════════════════════════════════════════════

def render_key_value_mapping_demo():
    """
    Key-Value 매핑 데모 UI
    
    사용법:
        from modules.key_value_mapping_engine import render_key_value_mapping_demo
        render_key_value_mapping_demo()
    """
    import streamlit as st
    
    st.markdown("### 🔑 Key-Value 매핑 엔진")
    
    # 샘플 OCR 텍스트
    sample_text = """
    삼성생명 보험증권
    
    증권번호: SL-2020-123456
    계약일: 2020-01-15
    만기일: 2040-01-15
    피보험자: 홍길동
    계약자: 홍길동
    
    보장내역
    
    1. 일반사망보험금: 1억원
    2. 암진단비: 5,000만원
    3. 뇌졸중진단비: 3,000만원
    4. 급성심근경색진단비: 3,000만원
    5. 수술급여금: 500만원
    6. 입원일당: 10만원
    7. 실손의료비: 5,000만원
    8. 치아보험금: 100만원
    """
    
    ocr_text = st.text_area(
        "OCR 추출 텍스트 입력",
        value=sample_text,
        height=300,
        key="kv_mapping_demo"
    )
    
    if st.button("분석 시작", key="kv_mapping_analyze"):
        # Key-Value 매핑 적용
        engine = KeyValueMappingEngine()
        policy_data = engine.extract_insurance_policy_data(ocr_text)
        
        # 결과 표시
        st.markdown("### 📊 분석 결과")
        
        # JSON 형식
        with st.expander("JSON 데이터", expanded=False):
            st.json(policy_data)
        
        # 요약 텍스트
        summary = engine.generate_coverage_summary(policy_data)
        st.markdown(summary)
