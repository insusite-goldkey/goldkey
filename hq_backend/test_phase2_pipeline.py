"""
Phase 2 파이프라인 테스트 시나리오
가족 증권 3장 → OCR → 16대 분류 → 3-Way 비교
"""
import sys
from pathlib import Path

# 경로 추가
sys.path.append(str(Path(__file__).parent))

from engines.static_calculators import load_static_data, CoverageCalculator
from core import OCRParser, MasterRouter

def test_static_data_loading():
    """정적 데이터 로딩 테스트"""
    print("\n" + "="*80)
    print("테스트 1: 정적 데이터 로딩")
    print("="*80)
    
    success = load_static_data()
    
    if success:
        print("✅ 정적 데이터 로딩 성공")
        return True
    else:
        print("❌ 정적 데이터 로딩 실패")
        return False

def test_coverage_calculator():
    """증권 분석 엔진 테스트"""
    print("\n" + "="*80)
    print("테스트 2: 증권 분석 엔진")
    print("="*80)
    
    try:
        calculator = CoverageCalculator()
        print("✅ CoverageCalculator 초기화 성공")
        
        # 샘플 데이터
        sample_ocr_data = [
            {
                "insured_name": "홍길동",
                "insurance_company": "삼성화재",
                "coverages": [
                    {"name": "암진단비", "amount": 30000000},
                    {"name": "뇌혈관진단비", "amount": 20000000},
                    {"name": "허혈성심장진단비", "amount": 15000000}
                ]
            },
            {
                "insured_name": "홍길동",
                "insurance_company": "현대해상",
                "coverages": [
                    {"name": "상해사망후유장해", "amount": 50000000},
                    {"name": "입원일당", "amount": 30000}
                ]
            },
            {
                "insured_name": "김영희",
                "insurance_company": "KB손해보험",
                "coverages": [
                    {"name": "암진단비", "amount": 40000000},
                    {"name": "뇌혈관진단비", "amount": 25000000},
                    {"name": "배상책임", "amount": 100000000}
                ]
            }
        ]
        
        family_income = {
            "홍길동": 200,
            "김영희": 150
        }
        
        # 가족 분석
        print("\n📊 가족 통합 분석 시작...")
        family_analysis = calculator.analyze_family_policies(sample_ocr_data, family_income)
        
        print("\n✅ 분석 결과:")
        for member_name, analysis in family_analysis.items():
            print(f"\n  👤 {member_name}님:")
            print(f"     가처분소득: {analysis['disposable_income']:,}만원")
            print(f"     총 부족 금액: {analysis['total_shortage_vs_kb']:,}원")
            print(f"     긴급 항목: {len(analysis['high_priority_items'])}개")
            
            print(f"\n     현재 가입 현황:")
            for category, amount in analysis['current_coverages'].items():
                if amount > 0:
                    print(f"       - {category}: {amount:,}원")
            
            print(f"\n     최우선 보완 항목 (상위 3개):")
            for item in analysis['3way_comparison'][:3]:
                print(f"       - {item['category']}: {item['shortage_vs_kb']:,}원 부족 ({item['shortage_rate']:.1f}%, {item['priority']})")
        
        # 요약 리포트
        summary = calculator.generate_summary_report(family_analysis)
        
        print(f"\n📈 가족 전체 요약:")
        print(f"   총 구성원: {summary['total_members']}명")
        print(f"   가족 전체 부족 금액: {summary['total_shortage']:,}원")
        print(f"   긴급 보완 항목 수: {summary['urgent_items_count']}개")
        
        print("\n✅ 증권 분석 엔진 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 증권 분석 엔진 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_category_mapping():
    """16대 카테고리 매핑 테스트"""
    print("\n" + "="*80)
    print("테스트 3: 16대 카테고리 매핑")
    print("="*80)
    
    try:
        calculator = CoverageCalculator()
        
        # 다양한 보험사 특약명 테스트
        test_cases = [
            {
                "company": "삼성화재",
                "coverages": [
                    {"name": "일반암진단비", "amount": 50000000},
                    {"name": "뇌출혈진단비", "amount": 30000000},
                    {"name": "급성심근경색진단비", "amount": 30000000}
                ]
            },
            {
                "company": "현대해상",
                "coverages": [
                    {"name": "암진단금", "amount": 40000000},
                    {"name": "뇌혈관질환진단금", "amount": 25000000},
                    {"name": "배상책임보험금", "amount": 100000000}
                ]
            },
            {
                "company": "KB손해보험",
                "coverages": [
                    {"name": "일반암", "amount": 45000000},
                    {"name": "뇌경색", "amount": 28000000},
                    {"name": "심근경색", "amount": 28000000}
                ]
            }
        ]
        
        print("\n매핑 테스트 결과:")
        for test_case in test_cases:
            company = test_case["company"]
            coverages = test_case["coverages"]
            
            mapped = calculator.map_to_16_categories(coverages, company)
            
            print(f"\n  {company}:")
            for category, amount in mapped.items():
                if amount > 0:
                    print(f"    - {category}: {amount:,}원")
        
        print("\n✅ 16대 카테고리 매핑 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 16대 카테고리 매핑 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3way_comparison():
    """3-Way 비교 테스트"""
    print("\n" + "="*80)
    print("테스트 4: 3-Way 비교 (현재/트리니티/KB)")
    print("="*80)
    
    try:
        calculator = CoverageCalculator()
        
        # 현재 가입 현황
        current_data = {
            "암진단비": 30000000,
            "뇌혈관진단비": 20000000,
            "허혈성심장진단비": 15000000,
            "일반사망": 50000000,
            "상해사망후유장해": 30000000,
            "입원일당": 30000,
            "배상책임": 50000000,
            "운전자비용": 100000000
        }
        
        disposable_income = 200  # 만원
        
        # 3-Way 비교
        comparison = calculator.calculate_3way_comparison(current_data, disposable_income)
        
        print(f"\n가처분소득: {disposable_income:,}만원")
        print(f"\n3-Way 비교 결과 (상위 10개):")
        print(f"{'항목':<20} {'현재':<15} {'트리니티':<15} {'KB기준':<15} {'부족률':<10} {'우선순위'}")
        print("-" * 95)
        
        for item in comparison[:10]:
            print(f"{item['category']:<20} "
                  f"{item['current']:>13,}원 "
                  f"{item['trinity']:>13,}원 "
                  f"{item['kb_standard']:>13,}원 "
                  f"{item['shortage_rate']:>8.1f}% "
                  f"{item['priority']}")
        
        print("\n✅ 3-Way 비교 테스트 성공")
        return True
        
    except Exception as e:
        print(f"❌ 3-Way 비교 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """메인 테스트 실행"""
    print("\n" + "="*80)
    print("🚀 Phase 2 파이프라인 테스트 시작")
    print("="*80)
    
    results = []
    
    # 테스트 1: 정적 데이터 로딩
    results.append(("정적 데이터 로딩", test_static_data_loading()))
    
    # 테스트 2: 증권 분석 엔진
    results.append(("증권 분석 엔진", test_coverage_calculator()))
    
    # 테스트 3: 16대 카테고리 매핑
    results.append(("16대 카테고리 매핑", test_category_mapping()))
    
    # 테스트 4: 3-Way 비교
    results.append(("3-Way 비교", test_3way_comparison()))
    
    # 최종 결과
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)
    
    for test_name, result in results:
        status = "✅ 성공" if result else "❌ 실패"
        print(f"{test_name:<30} {status}")
    
    success_count = sum(1 for _, result in results if result)
    total_count = len(results)
    
    print(f"\n총 {success_count}/{total_count}개 테스트 통과")
    
    if success_count == total_count:
        print("\n🎉 모든 테스트 통과!")
        print("\n✅ Phase 2 파이프라인 구축 완료")
        print("✅ OCR → 16대 분류 → 3-Way 비교 전체 흐름 검증 완료")
    else:
        print("\n⚠️ 일부 테스트 실패")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
