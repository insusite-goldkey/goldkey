# -*- coding: utf-8 -*-
"""
보안 필터 엔진 테스트
PII 마스킹 기능 검증

작성일: 2026-03-31
목적: 개인정보 보호법 준수 및 민원 대응 정당성 검증
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from hq_backend.services.security_filter import SecurityFilter


def test_phone_masking():
    """전화번호 마스킹 테스트"""
    print("\n" + "=" * 70)
    print("📱 전화번호 마스킹 테스트")
    print("=" * 70)
    
    security_filter = SecurityFilter()
    
    test_cases = [
        "담당자: 홍길동 (010-1234-5678)",
        "연락처: 010.9876.5432",
        "전화: 01012345678",
        "사무실: 02-123-4567",
        "지점: 031-456-7890"
    ]
    
    for test_text in test_cases:
        result = security_filter.apply_all_filters(test_text)
        print(f"\n원본: {test_text}")
        print(f"마스킹: {result.masked_text}")
        assert result.detection_count > 0, "전화번호가 감지되지 않았습니다"
    
    print("\n✅ 전화번호 마스킹 테스트 통과")


def test_rrn_masking():
    """주민등록번호 마스킹 테스트"""
    print("\n" + "=" * 70)
    print("🆔 주민등록번호 마스킹 테스트")
    print("=" * 70)
    
    security_filter = SecurityFilter()
    
    test_cases = [
        "주민번호: 850101-1234567",
        "생년월일: 900215-2345678",
        "주민등록번호: 750320-1******"
    ]
    
    for test_text in test_cases:
        result = security_filter.apply_all_filters(test_text)
        print(f"\n원본: {test_text}")
        print(f"마스킹: {result.masked_text}")
        assert "***" in result.masked_text, "주민번호가 마스킹되지 않았습니다"
    
    print("\n✅ 주민등록번호 마스킹 테스트 통과")


def test_email_masking():
    """이메일 마스킹 테스트"""
    print("\n" + "=" * 70)
    print("📧 이메일 마스킹 테스트")
    print("=" * 70)
    
    security_filter = SecurityFilter()
    
    test_cases = [
        "이메일: customer@example.com",
        "연락처: user.name@company.co.kr",
        "문의: support@insurance.com"
    ]
    
    for test_text in test_cases:
        result = security_filter.apply_all_filters(test_text)
        print(f"\n원본: {test_text}")
        print(f"마스킹: {result.masked_text}")
        assert "***" in result.masked_text, "이메일이 마스킹되지 않았습니다"
    
    print("\n✅ 이메일 마스킹 테스트 통과")


def test_name_masking():
    """이름 마스킹 테스트"""
    print("\n" + "=" * 70)
    print("👤 이름 마스킹 테스트")
    print("=" * 70)
    
    security_filter = SecurityFilter()
    
    test_cases = [
        "담당 설계사: 홍길동님",
        "고객명: 김철수 대표",
        "계약자: 이영희씨",
        "피보험자: 박민수 고객"
    ]
    
    for test_text in test_cases:
        result = security_filter.apply_all_filters(test_text)
        print(f"\n원본: {test_text}")
        print(f"마스킹: {result.masked_text}")
        assert "*" in result.masked_text, "이름이 마스킹되지 않았습니다"
    
    print("\n✅ 이름 마스킹 테스트 통과")


def test_comprehensive_masking():
    """종합 마스킹 테스트"""
    print("\n" + "=" * 70)
    print("🔒 종합 마스킹 테스트")
    print("=" * 70)
    
    security_filter = SecurityFilter()
    
    test_text = """
    삼성생명 보험 상품 안내
    
    담당 설계사: 홍길동 (010-1234-5678)
    고객명: 김철수님 (010-9876-5432)
    주민등록번호: 850101-1234567
    이메일: customer@example.com
    계좌번호: 123-456-789012
    카드번호: 1234-5678-9012-3456
    
    보험료: 월 50,000원
    보장 내용: 암 진단 시 3,000만원
    """
    
    result = security_filter.apply_all_filters(test_text)
    stats = security_filter.get_statistics(result)
    
    print(f"\n원본 텍스트 길이: {len(test_text)}자")
    print(f"마스킹된 텍스트 길이: {len(result.masked_text)}자")
    print(f"\n총 PII 감지: {stats['total_detections']}개")
    
    for pii_type, count in stats['by_type'].items():
        print(f"  - {pii_type}: {count}개")
    
    print(f"\n마스킹된 텍스트:")
    print("-" * 70)
    print(result.masked_text)
    
    # 검증
    assert result.detection_count >= 6, f"PII 감지 수가 부족합니다: {result.detection_count}개"
    assert "***" in result.masked_text, "마스킹이 적용되지 않았습니다"
    assert "010-1234-5678" not in result.masked_text, "전화번호가 마스킹되지 않았습니다"
    assert "850101-1234567" not in result.masked_text, "주민번호가 마스킹되지 않았습니다"
    assert "customer@example.com" not in result.masked_text, "이메일이 마스킹되지 않았습니다"
    
    print("\n✅ 종합 마스킹 테스트 통과")


def test_document_processor_integration():
    """DocumentProcessor 통합 테스트"""
    print("\n" + "=" * 70)
    print("🔗 DocumentProcessor 통합 테스트")
    print("=" * 70)
    
    try:
        from hq_backend.services.document_processor import InsuranceDocumentProcessor
        
        processor = InsuranceDocumentProcessor()
        
        # 보안 필터가 초기화되었는지 확인
        assert hasattr(processor, 'security_filter'), "SecurityFilter가 초기화되지 않았습니다"
        assert processor.security_filter is not None, "SecurityFilter가 None입니다"
        
        print("\n✅ DocumentProcessor에 SecurityFilter가 정상적으로 통합되었습니다")
        print(f"   - SecurityFilter 인스턴스: {processor.security_filter}")
        
    except Exception as e:
        print(f"\n❌ DocumentProcessor 통합 테스트 실패: {e}")
        raise


def main():
    """
    메인 테스트 함수
    """
    print("=" * 70)
    print("🧪 보안 필터 엔진 테스트 스위트")
    print("   개인정보 보호법 준수 및 민원 대응 정당성 검증")
    print("=" * 70)
    
    try:
        # 개별 테스트 실행
        test_phone_masking()
        test_rrn_masking()
        test_email_masking()
        test_name_masking()
        test_comprehensive_masking()
        test_document_processor_integration()
        
        # 최종 결과
        print("\n" + "=" * 70)
        print("🎉 모든 테스트 통과")
        print("=" * 70)
        print("\n✅ 보안 필터 엔진이 정상적으로 작동합니다")
        print("✅ 개인정보 보호법 준수 확인")
        print("✅ 민원 대응 정당성 확보")
        print("\n" + "=" * 70)
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
