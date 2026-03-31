"""
가족 통합 증권 분석 엔진
16대 보장항목 매핑 및 3-Way 비교 (현재/트리니티/KB)
LLM 우회 100% 정확한 수학 연산
"""
from typing import List, Dict, Optional
from .static_data_loader import COVERAGE_16_MAPPING, KB_TRINITY_STANDARDS

class CoverageCalculator:
    """증권 분석 및 3-Way 비교 엔진"""
    
    def __init__(self):
        """초기화 - 메모리에 적재된 정적 데이터 참조"""
        self.mapping = COVERAGE_16_MAPPING
        self.standards = KB_TRINITY_STANDARDS
        
        if not self.mapping or not self.standards:
            raise RuntimeError("정적 데이터가 메모리에 로드되지 않았습니다. static_data_loader.load_static_data()를 먼저 실행하세요.")
    
    def aggregate_by_family(self, ocr_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        OCR로 추출된 여러 증권을 피보험자(가족 구성원) 기준으로 그룹화
        
        Args:
            ocr_data: OCR 추출 데이터 리스트
                [
                    {
                        "insured_name": "홍길동",
                        "insurance_company": "삼성화재",
                        "coverages": [
                            {"name": "일반암진단비", "amount": 30000000},
                            {"name": "뇌출혈진단비", "amount": 20000000}
                        ]
                    },
                    ...
                ]
        
        Returns:
            가족 구성원별 그룹화된 데이터
                {
                    "홍길동": [증권1, 증권2, ...],
                    "김영희": [증권3, ...],
                    ...
                }
        """
        family_data = {}
        
        for policy in ocr_data:
            insured_name = policy.get("insured_name", "미확인")
            if insured_name not in family_data:
                family_data[insured_name] = []
            family_data[insured_name].append(policy)
        
        return family_data
    
    def map_to_16_categories(self, coverages: List[Dict], insurance_company: str) -> Dict[str, int]:
        """
        보험사별 특약명을 16대 표준 항목으로 자동 매핑 및 합산
        
        Args:
            coverages: 특약 리스트
                [
                    {"name": "일반암진단비", "amount": 30000000},
                    {"name": "뇌출혈진단비", "amount": 20000000}
                ]
            insurance_company: 보험사명 (예: "삼성화재")
        
        Returns:
            16대 항목별 합산 금액
                {
                    "암진단비": 30000000,
                    "뇌혈관질환": 20000000,
                    ...
                }
        """
        # 16대 카테고리 초기화
        category_sums = {cat: 0 for cat in self.mapping["metadata"]["categories"]}
        
        for coverage in coverages:
            coverage_name = coverage.get("name", "")
            coverage_amount = coverage.get("amount", 0)
            
            if not coverage_name or coverage_amount == 0:
                continue
            
            # 16대 항목 중 매칭되는 카테고리 찾기
            matched = False
            
            for category, mapping_data in self.mapping["mappings"].items():
                # 1단계: 보험사별 특약명 정확 매칭 (우선순위 높음)
                company_coverages = mapping_data["insurance_companies"].get(insurance_company, [])
                if coverage_name in company_coverages:
                    category_sums[category] += coverage_amount
                    matched = True
                    break
                
                # 2단계: 키워드 매칭 (보험사 매핑에 없는 경우)
                if not matched:
                    for keyword in mapping_data["keywords"]:
                        if keyword in coverage_name:
                            category_sums[category] += coverage_amount
                            matched = True
                            break
                
                if matched:
                    break
            
            # 3단계: 매칭 실패 시 "기타"로 분류
            if not matched:
                category_sums["기타"] += coverage_amount
        
        return category_sums
    
    def calculate_3way_comparison(
        self, 
        current_data: Dict[str, int], 
        disposable_income: int
    ) -> List[Dict]:
        """
        3-Way 비교: 현재 가입금액 vs 트리니티 권장액 vs KB 스탠다드
        
        Args:
            current_data: 현재 가입금액 (16대 항목별)
                {
                    "암진단비": 30000000,
                    "뇌혈관진단비": 20000000,
                    ...
                }
            disposable_income: 가처분소득 (만원)
        
        Returns:
            3-Way 비교 결과
                [
                    {
                        "category": "암진단비",
                        "current": 30000000,
                        "trinity": 36000000,
                        "kb_standard": 50000000,
                        "shortage_vs_trinity": 6000000,
                        "shortage_vs_kb": 20000000,
                        "recommended": 50000000,
                        "shortage_rate": 40.0,
                        "priority": "중요"
                    },
                    ...
                ]
        """
        results = []
        
        # 트리니티 기준 계산: 가처분소득(만원) * 10000 * 12% = 월 보험료
        base_premium = disposable_income * 10000 * self.standards["trinity_allocation_ratio"]["base_premium_ratio"]
        
        # 카테고리 그룹 매핑 가져오기
        group_mapping = self.standards.get("category_group_mapping", {})
        allocation_ratio = self.standards["trinity_allocation_ratio"]
        
        for category in self.mapping["metadata"]["categories"]:
            current_amount = current_data.get(category, 0)
            kb_amount = self.standards["kb_standard_amounts"].get(category, 0)
            
            # 트리니티 금액 계산 (그룹별 배분)
            trinity_amount = 0
            for group_name, group_categories in group_mapping.items():
                if category in group_categories:
                    group_ratio = allocation_ratio.get(group_name, 0)
                    group_member_count = len(group_categories)
                    trinity_amount = int(base_premium * group_ratio / group_member_count)
                    break
            
            # 부족 금액 계산
            shortage_vs_trinity = max(0, trinity_amount - current_amount)
            shortage_vs_kb = max(0, kb_amount - current_amount)
            
            # 권장 금액 (KB와 트리니티 중 큰 값)
            recommended = max(kb_amount, trinity_amount)
            
            # 부족률 계산 (KB 기준)
            shortage_rate = (shortage_vs_kb / kb_amount * 100) if kb_amount > 0 else 0
            
            # 우선순위 결정
            if shortage_rate >= 70:
                priority = "긴급"
            elif shortage_rate >= 40:
                priority = "중요"
            else:
                priority = "보통"
            
            results.append({
                "category": category,
                "current": current_amount,
                "trinity": trinity_amount,
                "kb_standard": kb_amount,
                "shortage_vs_trinity": shortage_vs_trinity,
                "shortage_vs_kb": shortage_vs_kb,
                "recommended": recommended,
                "shortage_rate": round(shortage_rate, 1),
                "priority": priority
            })
        
        # 부족률 높은 순으로 정렬
        results.sort(key=lambda x: x["shortage_rate"], reverse=True)
        
        return results
    
    def analyze_family_policies(
        self, 
        ocr_data: List[Dict], 
        family_income_data: Dict[str, int]
    ) -> Dict:
        """
        가족 전체 증권 통합 분석
        
        Args:
            ocr_data: OCR 추출 데이터 리스트
                [
                    {
                        "insured_name": "홍길동",
                        "insurance_company": "삼성화재",
                        "coverages": [
                            {"name": "일반암진단비", "amount": 30000000},
                            {"name": "뇌출혈진단비", "amount": 20000000}
                        ]
                    },
                    ...
                ]
            family_income_data: 가족 구성원별 가처분소득
                {
                    "홍길동": 150,  # 만원
                    "김영희": 100,
                    ...
                }
        
        Returns:
            가족 구성원별 3-Way 비교 결과
                {
                    "홍길동": {
                        "current_coverages": {...},
                        "disposable_income": 150,
                        "3way_comparison": [...],
                        "total_shortage_vs_kb": 120000000,
                        "high_priority_items": [...]
                    },
                    ...
                }
        """
        # 1. 가족 구성원별 그룹화
        family_data = self.aggregate_by_family(ocr_data)
        
        # 2. 구성원별 분석
        family_analysis = {}
        
        for member_name, policies in family_data.items():
            # 구성원의 모든 증권 통합
            all_coverages = []
            for policy in policies:
                insurance_company = policy.get("insurance_company", "기타")
                coverages = policy.get("coverages", [])
                
                # 16대 항목으로 매핑
                mapped = self.map_to_16_categories(coverages, insurance_company)
                all_coverages.append(mapped)
            
            # 16대 항목별 합산
            total_current = {cat: 0 for cat in self.standards["metadata"]["categories"]}
            for cov in all_coverages:
                for cat, amount in cov.items():
                    total_current[cat] += amount
            
            # 3-Way 비교
            disposable_income = family_income_data.get(member_name, 150)  # 기본값 150만원
            comparison = self.calculate_3way_comparison(total_current, disposable_income)
            
            family_analysis[member_name] = {
                "current_coverages": total_current,
                "disposable_income": disposable_income,
                "3way_comparison": comparison,
                "total_shortage_vs_kb": sum(item["shortage_vs_kb"] for item in comparison),
                "high_priority_items": [item for item in comparison if item["priority"] == "긴급"]
            }
        
        return family_analysis
    
    def generate_summary_report(self, family_analysis: Dict) -> Dict:
        """
        가족 전체 요약 리포트 생성
        
        Args:
            family_analysis: analyze_family_policies() 결과
        
        Returns:
            요약 리포트
                {
                    "total_members": 3,
                    "total_shortage": 350000000,
                    "urgent_items_count": 12,
                    "family_summary": [...]
                }
        """
        total_members = len(family_analysis)
        total_shortage = sum(member["total_shortage_vs_kb"] for member in family_analysis.values())
        urgent_items_count = sum(len(member["high_priority_items"]) for member in family_analysis.values())
        
        family_summary = []
        for member_name, analysis in family_analysis.items():
            family_summary.append({
                "name": member_name,
                "disposable_income": analysis["disposable_income"],
                "total_shortage": analysis["total_shortage_vs_kb"],
                "urgent_count": len(analysis["high_priority_items"]),
                "top_3_shortages": analysis["3way_comparison"][:3]
            })
        
        return {
            "total_members": total_members,
            "total_shortage": total_shortage,
            "urgent_items_count": urgent_items_count,
            "family_summary": family_summary
        }
