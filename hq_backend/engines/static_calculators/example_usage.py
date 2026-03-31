"""
증권 분석 엔진 사용 예제
"""
from coverage_calculator import CoverageCalculator

# 예제 데이터: OCR로 추출된 가족 증권 정보
sample_ocr_data = [
    {
        "insured_name": "홍길동",
        "insurance_company": "삼성화재",
        "coverages": [
            {"name": "일반암진단비", "amount": 30000000},
            {"name": "뇌출혈진단비", "amount": 20000000},
            {"name": "급성심근경색진단비", "amount": 15000000},
            {"name": "일반상해사망", "amount": 50000000},
            {"name": "질병입원일당", "amount": 30000}
        ]
    },
    {
        "insured_name": "홍길동",
        "insurance_company": "현대해상",
        "coverages": [
            {"name": "암진단금", "amount": 20000000},
            {"name": "상해후유장해보험금", "amount": 30000000}
        ]
    },
    {
        "insured_name": "김영희",
        "insurance_company": "KB손해보험",
        "coverages": [
            {"name": "일반암", "amount": 40000000},
            {"name": "뇌경색", "amount": 25000000},
            {"name": "심근경색", "amount": 25000000},
            {"name": "입원일당", "amount": 50000}
        ]
    }
]

# 가족 구성원별 가처분소득 (만원)
family_income = {
    "홍길동": 200,  # 월 200만원
    "김영희": 150   # 월 150만원
}

def main():
    """메인 실행 함수"""
    
    print("=" * 80)
    print("가족 통합 증권 분석 엔진 테스트")
    print("=" * 80)
    
    # 1. 엔진 초기화
    calculator = CoverageCalculator()
    print("\n✅ 증권 분석 엔진 초기화 완료")
    
    # 2. 가족 전체 분석
    print("\n[단계 1] 가족 전체 증권 분석 시작...")
    family_analysis = calculator.analyze_family_policies(sample_ocr_data, family_income)
    
    # 3. 구성원별 결과 출력
    for member_name, analysis in family_analysis.items():
        print(f"\n{'=' * 80}")
        print(f"📋 {member_name}님 보장 분석 결과")
        print(f"{'=' * 80}")
        print(f"가처분소득: {analysis['disposable_income']:,}만원")
        print(f"총 부족 금액: {analysis['total_shortage_vs_kb']:,}원")
        print(f"긴급 보완 항목: {len(analysis['high_priority_items'])}개")
        
        print(f"\n[현재 가입 현황]")
        for category, amount in analysis['current_coverages'].items():
            if amount > 0:
                print(f"  - {category}: {amount:,}원")
        
        print(f"\n[3-Way 비교 결과 (상위 5개)]")
        print(f"{'항목':<15} {'현재':<12} {'트리니티':<12} {'KB기준':<12} {'부족률':<8} {'우선순위'}")
        print("-" * 80)
        
        for item in analysis['3way_comparison'][:5]:
            print(f"{item['category']:<15} "
                  f"{item['current']:>10,}원 "
                  f"{item['trinity']:>10,}원 "
                  f"{item['kb_standard']:>10,}원 "
                  f"{item['shortage_rate']:>6.1f}% "
                  f"{item['priority']}")
    
    # 4. 가족 전체 요약
    print(f"\n{'=' * 80}")
    print("📊 가족 전체 요약")
    print(f"{'=' * 80}")
    
    summary = calculator.generate_summary_report(family_analysis)
    print(f"총 구성원: {summary['total_members']}명")
    print(f"가족 전체 부족 금액: {summary['total_shortage']:,}원")
    print(f"긴급 보완 항목 수: {summary['urgent_items_count']}개")
    
    print(f"\n[구성원별 요약]")
    for member in summary['family_summary']:
        print(f"\n{member['name']}님:")
        print(f"  - 가처분소득: {member['disposable_income']:,}만원")
        print(f"  - 부족 금액: {member['total_shortage']:,}원")
        print(f"  - 긴급 항목: {member['urgent_count']}개")
        print(f"  - 최우선 보완 항목:")
        for item in member['top_3_shortages']:
            print(f"    · {item['category']}: {item['shortage_vs_kb']:,}원 부족 ({item['shortage_rate']:.1f}%)")

if __name__ == "__main__":
    main()
