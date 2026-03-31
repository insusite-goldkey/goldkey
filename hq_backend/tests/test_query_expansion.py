# -*- coding: utf-8 -*-
"""
Query Expansion Engine 테스트
질의 확장 기능 검증

작성일: 2026-03-31
목적: RAG 검색 정확도 향상 검증
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from hq_backend.services.query_expansion_engine import QueryExpansionEngine


def test_colloquial_expansion():
    """구어체 확장 테스트"""
    print("\n" + "=" * 70)
    print("🗣️  구어체 → 전문 용어 확장 테스트")
    print("=" * 70)
    
    engine = QueryExpansionEngine()
    
    test_cases = [
        ("나중에 보험료 올라?", ["갱신형", "보험료 변동형", "갱신계약"]),
        ("보험료 안 올라?", ["비갱신형", "확정 보험료", "고정형"]),
        ("추가로 넣는 거 있어?", ["특약", "특별약관", "Rider"]),
        ("암 걸리면 얼마 받아?", ["암 진단금", "암 보장", "암 특약"])
    ]
    
    for query, expected_keywords in test_cases:
        result = engine.expand_query(query)
        
        print(f"\n📝 원본: {query}")
        print(f"🔍 확장: {result.expanded_query}")
        print(f"🏷️  키워드: {result.meta_keywords}")
        
        # 검증: 예상 키워드 중 하나 이상 포함
        has_expected = any(keyword in result.meta_keywords for keyword in expected_keywords)
        assert has_expected, f"예상 키워드가 포함되지 않았습니다: {expected_keywords}"
    
    print("\n✅ 구어체 확장 테스트 통과")


def test_glossary_matching():
    """Glossary 용어 매칭 테스트"""
    print("\n" + "=" * 70)
    print("📚 Glossary 용어 매칭 테스트")
    print("=" * 70)
    
    engine = QueryExpansionEngine()
    
    test_cases = [
        ("특약 추가하면 얼마야?", "특약"),
        ("갱신형이 뭐야?", "갱신형"),
        ("비갱신형으로 바꿀 수 있어?", "비갱신형")
    ]
    
    for query, expected_term in test_cases:
        result = engine.expand_query(query)
        
        print(f"\n📝 원본: {query}")
        print(f"✅ 매칭된 용어: {[t['standard_term'] for t in result.matched_terms]}")
        
        # 검증: 예상 용어 매칭
        matched_standard_terms = [t['standard_term'] for t in result.matched_terms]
        assert expected_term in matched_standard_terms, f"예상 용어가 매칭되지 않았습니다: {expected_term}"
    
    print("\n✅ Glossary 용어 매칭 테스트 통과")


def test_query_expansion_accuracy():
    """쿼리 확장 정확도 테스트"""
    print("\n" + "=" * 70)
    print("🎯 쿼리 확장 정확도 테스트")
    print("=" * 70)
    
    engine = QueryExpansionEngine()
    
    # 복합 쿼리 테스트
    query = "나중에 보험료 올라? 특약도 추가할 수 있어?"
    result = engine.expand_query(query)
    
    print(f"\n📝 원본 쿼리: {query}")
    print(f"🔍 확장된 쿼리: {result.expanded_query}")
    print(f"🏷️  메타 키워드 ({result.expansion_count}개):")
    for keyword in result.meta_keywords:
        print(f"   - {keyword}")
    
    # 검증: 메타 키워드가 추가되었는지 확인
    assert result.expansion_count > 0, "메타 키워드가 추가되지 않았습니다"
    assert len(result.expanded_query) > len(result.original_query), "쿼리가 확장되지 않았습니다"
    
    # 검증: "갱신형" 또는 "특약" 관련 키워드 포함
    has_renewal_keywords = any(
        keyword in ["갱신형", "보험료 변동형", "갱신계약"]
        for keyword in result.meta_keywords
    )
    has_rider_keywords = any(
        keyword in ["특약", "특별약관", "Rider", "부가특약"]
        for keyword in result.meta_keywords
    )
    
    assert has_renewal_keywords, "갱신형 관련 키워드가 없습니다"
    assert has_rider_keywords, "특약 관련 키워드가 없습니다"
    
    print("\n✅ 쿼리 확장 정확도 테스트 통과")


def test_expansion_statistics():
    """확장 통계 테스트"""
    print("\n" + "=" * 70)
    print("📊 확장 통계 테스트")
    print("=" * 70)
    
    engine = QueryExpansionEngine()
    
    query = "갱신형 특약 추가하면 보험료 얼마나 올라?"
    result = engine.expand_query(query)
    stats = engine.get_expansion_statistics(result)
    
    print(f"\n📝 원본 쿼리: {query}")
    print(f"\n📊 통계 정보:")
    print(f"   - 원본 길이: {stats['original_length']}자")
    print(f"   - 확장 길이: {stats['expanded_length']}자")
    print(f"   - 확장 키워드 수: {stats['expansion_count']}개")
    print(f"   - 매칭된 용어 수: {stats['matched_terms_count']}개")
    
    # 검증
    assert stats['expanded_length'] >= stats['original_length'], "확장 길이가 원본보다 짧습니다"
    assert stats['expansion_count'] > 0, "확장 키워드가 없습니다"
    
    print("\n✅ 확장 통계 테스트 통과")


def test_no_expansion_case():
    """확장 불필요 케이스 테스트"""
    print("\n" + "=" * 70)
    print("⏭️  확장 불필요 케이스 테스트")
    print("=" * 70)
    
    engine = QueryExpansionEngine()
    
    # 일반적인 질문 (보험 용어 없음)
    query = "안녕하세요"
    result = engine.expand_query(query)
    
    print(f"\n📝 원본 쿼리: {query}")
    print(f"🔍 확장된 쿼리: {result.expanded_query}")
    print(f"🏷️  메타 키워드: {result.meta_keywords}")
    
    # 검증: 확장이 없어도 정상 작동
    assert result.original_query == query, "원본 쿼리가 변경되었습니다"
    
    print("\n✅ 확장 불필요 케이스 테스트 통과")


def main():
    """
    메인 테스트 함수
    """
    print("=" * 70)
    print("🧪 Query Expansion Engine 테스트 스위트")
    print("   RAG 검색 정확도 향상 검증")
    print("=" * 70)
    
    try:
        # 개별 테스트 실행
        test_colloquial_expansion()
        test_glossary_matching()
        test_query_expansion_accuracy()
        test_expansion_statistics()
        test_no_expansion_case()
        
        # 최종 결과
        print("\n" + "=" * 70)
        print("🎉 모든 테스트 통과")
        print("=" * 70)
        print("\n✅ Query Expansion Engine이 정상적으로 작동합니다")
        print("✅ 구어체 → 전문 용어 변환 확인")
        print("✅ Glossary 기반 용어 매칭 확인")
        print("✅ RAG 검색 정확도 향상 준비 완료")
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
