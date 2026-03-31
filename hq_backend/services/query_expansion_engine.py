# -*- coding: utf-8 -*-
"""
Query Expansion Engine (질의 확장 엔진)
사용자의 쉬운 질문을 전문적인 검색어로 변환

작성일: 2026-03-31
목적: RAG 벡터 검색 정확도 향상을 위한 질의 확장
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExpandedQuery:
    """확장된 쿼리 결과"""
    original_query: str
    expanded_query: str
    meta_keywords: List[str]
    matched_terms: List[Dict[str, str]]
    expansion_count: int


class QueryExpansionEngine:
    """
    질의 확장 엔진
    
    핵심 기능:
    1. glossary.json 기반 용어 매칭
    2. 동의어 자동 확장
    3. 구어체 → 전문 용어 변환
    4. 메타 키워드 추출
    """
    
    # 구어체 → 전문 용어 매핑
    COLLOQUIAL_MAPPING = {
        "나중에 보험료 올라": ["갱신형", "보험료 변동형", "갱신계약"],
        "보험료 안 올라": ["비갱신형", "확정 보험료", "고정형"],
        "추가로 넣는 거": ["특약", "특별약관", "Rider", "부가특약"],
        "기본 보험": ["주계약", "주보험", "기본계약"],
        "나중에 바꿀 수 있어": ["전환", "변경", "전환특약"],
        "중간에 해지하면": ["중도해지", "해약", "해지환급금"],
        "돈 돌려받는 거": ["만기환급금", "만기보험금", "환급형"],
        "돈 안 돌려받는 거": ["순수보장형", "소멸형", "비환급형"],
        "암 걸리면": ["암 진단금", "암 보장", "암 특약"],
        "입원하면": ["입원비", "입원급여금", "입원특약"],
        "수술하면": ["수술비", "수술급여금", "수술특약"],
        "사망하면": ["사망보험금", "사망보장", "유족급여"],
        "다쳤을 때": ["상해", "재해", "상해보험"],
        "아플 때": ["질병", "질병보험", "질병보장"],
        "나이 들면": ["노후", "연금", "연금보험"],
        "애들 교육비": ["자녀교육", "교육보험", "학자금"],
        "집 살 때": ["주택자금", "주택담보", "주택마련"],
        "차 사고": ["자동차보험", "자동차사고", "대인배상", "대물배상"],
        "회사 그만두면": ["퇴직", "퇴직금", "퇴직연금"],
        "세금 아끼는": ["절세", "세액공제", "소득공제"]
    }
    
    def __init__(self, glossary_path: Optional[str] = None):
        """
        Args:
            glossary_path: glossary.json 파일 경로
        """
        # glossary.json 경로 설정
        if glossary_path is None:
            project_root = Path(__file__).parent.parent.parent
            self.glossary_path = project_root / "hq_backend" / "knowledge_base" / "glossary.json"
        else:
            self.glossary_path = Path(glossary_path)
        
        # glossary 로드
        self.glossary = self._load_glossary()
        
        # 용어 인덱스 생성 (빠른 검색용)
        self.term_index = self._build_term_index()
    
    def _load_glossary(self) -> List[Dict]:
        """
        glossary.json 파일 로드
        
        Returns:
            List[Dict]: 용어 사전 데이터
        """
        if not self.glossary_path.exists():
            print(f"⚠️ glossary.json 파일을 찾을 수 없습니다: {self.glossary_path}")
            return []
        
        try:
            with open(self.glossary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ glossary.json 로드 실패: {e}")
            return []
    
    def _build_term_index(self) -> Dict[str, Dict]:
        """
        용어 인덱스 생성 (용어 + 동의어)
        
        Returns:
            Dict[str, Dict]: {용어: 용어 정보}
        """
        index = {}
        
        for entry in self.glossary:
            term = entry["term"]
            
            # 주 용어 인덱싱
            index[term.lower()] = entry
            
            # 동의어 인덱싱
            for synonym in entry.get("synonyms", []):
                index[synonym.lower()] = entry
        
        return index
    
    def extract_terms_from_query(self, query: str) -> List[Dict[str, str]]:
        """
        쿼리에서 용어 추출
        
        Args:
            query: 사용자 질문
        
        Returns:
            List[Dict[str, str]]: 매칭된 용어 리스트
        """
        matched_terms = []
        query_lower = query.lower()
        
        # glossary 용어 매칭
        for term, entry in self.term_index.items():
            if term in query_lower:
                matched_terms.append({
                    "matched_text": term,
                    "standard_term": entry["term"],
                    "definition": entry["definition"],
                    "synonyms": entry.get("synonyms", [])
                })
        
        return matched_terms
    
    def expand_colloquial_terms(self, query: str) -> List[str]:
        """
        구어체 용어를 전문 용어로 확장
        
        Args:
            query: 사용자 질문
        
        Returns:
            List[str]: 확장된 전문 용어 리스트
        """
        expanded_terms = []
        
        for colloquial, professional_terms in self.COLLOQUIAL_MAPPING.items():
            if colloquial in query:
                expanded_terms.extend(professional_terms)
        
        return expanded_terms
    
    def extract_meta_keywords(
        self,
        matched_terms: List[Dict[str, str]],
        colloquial_expansions: List[str]
    ) -> List[str]:
        """
        메타 키워드 추출
        
        Args:
            matched_terms: 매칭된 용어
            colloquial_expansions: 구어체 확장 용어
        
        Returns:
            List[str]: 메타 키워드 리스트
        """
        meta_keywords = []
        
        # 매칭된 용어의 표준 용어 추가
        for term_info in matched_terms:
            meta_keywords.append(term_info["standard_term"])
            # 동의어도 추가
            meta_keywords.extend(term_info.get("synonyms", []))
        
        # 구어체 확장 용어 추가
        meta_keywords.extend(colloquial_expansions)
        
        # 중복 제거
        meta_keywords = list(set(meta_keywords))
        
        return meta_keywords
    
    def expand_query(self, query: str) -> ExpandedQuery:
        """
        쿼리 확장 (Query Expansion)
        
        Args:
            query: 원본 사용자 질문
        
        Returns:
            ExpandedQuery: 확장된 쿼리 결과
        """
        # 1. glossary 용어 매칭
        matched_terms = self.extract_terms_from_query(query)
        
        # 2. 구어체 → 전문 용어 확장
        colloquial_expansions = self.expand_colloquial_terms(query)
        
        # 3. 메타 키워드 추출
        meta_keywords = self.extract_meta_keywords(matched_terms, colloquial_expansions)
        
        # 4. 확장된 쿼리 생성
        expanded_query = query
        if meta_keywords:
            # 원본 쿼리 + 메타 키워드 병합
            expanded_query = f"{query} {' '.join(meta_keywords)}"
        
        return ExpandedQuery(
            original_query=query,
            expanded_query=expanded_query,
            meta_keywords=meta_keywords,
            matched_terms=matched_terms,
            expansion_count=len(meta_keywords)
        )
    
    def get_expansion_statistics(self, result: ExpandedQuery) -> Dict:
        """
        확장 통계 정보
        
        Args:
            result: 확장된 쿼리 결과
        
        Returns:
            Dict: 통계 정보
        """
        return {
            "original_length": len(result.original_query),
            "expanded_length": len(result.expanded_query),
            "expansion_count": result.expansion_count,
            "matched_terms_count": len(result.matched_terms),
            "meta_keywords": result.meta_keywords
        }


def main():
    """
    테스트 및 예제 실행
    """
    print("=" * 70)
    print("🔍 Query Expansion Engine (질의 확장 엔진)")
    print("=" * 70)
    
    # Query Expansion Engine 초기화
    engine = QueryExpansionEngine()
    
    print(f"\n📚 Glossary 로드: {len(engine.glossary)}개 용어")
    print(f"📇 용어 인덱스: {len(engine.term_index)}개 (용어 + 동의어)")
    
    # 테스트 쿼리
    test_queries = [
        "나중에 보험료 올라?",
        "특약 추가하면 얼마나 더 내야 해?",
        "갱신형이랑 비갱신형 차이가 뭐야?",
        "암 걸리면 얼마 받아?",
        "중간에 해지하면 돈 돌려받을 수 있어?",
        "나이 들면 보험료 더 내야 돼?"
    ]
    
    print("\n" + "=" * 70)
    print("🧪 Query Expansion 테스트")
    print("=" * 70)
    
    for query in test_queries:
        result = engine.expand_query(query)
        stats = engine.get_expansion_statistics(result)
        
        print(f"\n📝 원본 쿼리: {result.original_query}")
        print(f"🔍 확장된 쿼리: {result.expanded_query}")
        print(f"🏷️  메타 키워드 ({stats['expansion_count']}개): {', '.join(result.meta_keywords)}")
        
        if result.matched_terms:
            print(f"✅ 매칭된 용어:")
            for term_info in result.matched_terms:
                print(f"   - {term_info['matched_text']} → {term_info['standard_term']}")
    
    print("\n" + "=" * 70)
    print("✅ Query Expansion 테스트 완료")
    print("=" * 70)
    
    print("\n💡 사용 예시:")
    print("""
    from hq_backend.services.query_expansion_engine import QueryExpansionEngine
    
    # 엔진 초기화
    engine = QueryExpansionEngine()
    
    # 쿼리 확장
    result = engine.expand_query("나중에 보험료 올라?")
    
    # 확장된 쿼리 사용
    expanded_query = result.expanded_query
    meta_keywords = result.meta_keywords
    
    # RAG 검색 시 확장된 쿼리 사용
    # search_results = rag_search(expanded_query)
    """)


if __name__ == "__main__":
    main()
