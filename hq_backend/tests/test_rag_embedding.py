# -*- coding: utf-8 -*-
"""
RAG 임베딩 성능 검증 테스트 (전문가 역산 로직)
보험 전문 용어의 임베딩 무결성 검증

작성일: 2026-03-31
목적: 임베딩 모델의 보험 용어 이해도를 수학적(Cosine Similarity)으로 평가
"""

import os
import sys
from pathlib import Path
import json
import numpy as np
from typing import List, Tuple, Dict

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# OpenAI 임베딩
try:
    import openai
except ImportError:
    print("❌ openai 라이브러리가 설치되어 있지 않습니다.")
    print("pip install openai 를 실행하세요.")
    sys.exit(1)

# 환경 변수 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv가 설치되어 있지 않습니다. 환경 변수를 수동으로 설정하세요.")


def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """
    OpenAI API를 사용하여 텍스트 임베딩 생성
    
    Args:
        text: 임베딩할 텍스트
        model: 임베딩 모델 (기본값: text-embedding-3-small)
    
    Returns:
        List[float]: 임베딩 벡터
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
    
    openai.api_key = api_key
    
    try:
        response = openai.embeddings.create(
            model=model,
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        raise


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    두 벡터 간의 코사인 유사도 계산
    
    Args:
        vec1: 첫 번째 벡터
        vec2: 두 번째 벡터
    
    Returns:
        float: 코사인 유사도 (0~1)
    """
    vec1_np = np.array(vec1)
    vec2_np = np.array(vec2)
    
    # 코사인 유사도 = (A·B) / (||A|| * ||B||)
    dot_product = np.dot(vec1_np, vec2_np)
    norm_vec1 = np.linalg.norm(vec1_np)
    norm_vec2 = np.linalg.norm(vec2_np)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0
    
    return dot_product / (norm_vec1 * norm_vec2)


def load_glossary() -> List[Dict]:
    """
    glossary.json 파일 로드
    
    Returns:
        List[Dict]: 용어 사전 데이터
    """
    glossary_path = project_root / "hq_backend" / "knowledge_base" / "glossary.json"
    
    if not glossary_path.exists():
        raise FileNotFoundError(f"glossary.json 파일을 찾을 수 없습니다: {glossary_path}")
    
    with open(glossary_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_synonym_similarity(model: str = "text-embedding-3-small") -> List[Tuple[str, str, float]]:
    """
    동의어 간 유사도 테스트
    
    Args:
        model: 임베딩 모델
    
    Returns:
        List[Tuple[str, str, float]]: (용어1, 용어2, 유사도) 리스트
    """
    print("\n" + "=" * 70)
    print("📊 동의어 간 유사도 테스트 (Synonym Similarity Test)")
    print("=" * 70)
    
    glossary = load_glossary()
    results = []
    
    for entry in glossary:
        term = entry["term"]
        synonyms = entry.get("synonyms", [])
        
        if not synonyms:
            continue
        
        print(f"\n🔍 용어: {term}")
        print(f"   정의: {entry['definition']}")
        
        # 원본 용어 임베딩
        term_embedding = get_embedding(term, model)
        
        for synonym in synonyms:
            # 동의어 임베딩
            synonym_embedding = get_embedding(synonym, model)
            
            # 유사도 계산
            similarity = cosine_similarity(term_embedding, synonym_embedding)
            results.append((term, synonym, similarity))
            
            # 결과 출력
            similarity_percent = similarity * 100
            if similarity >= 0.8:
                status = "✅ 매우 높음"
            elif similarity >= 0.6:
                status = "⚠️ 보통"
            else:
                status = "❌ 낮음"
            
            print(f"   '{term}' ↔ '{synonym}': {similarity:.4f} ({similarity_percent:.2f}%) {status}")
    
    return results


def test_antonym_similarity(model: str = "text-embedding-3-small") -> List[Tuple[str, str, float]]:
    """
    반대 개념 간 유사도 테스트 (갱신형 vs 비갱신형)
    
    Args:
        model: 임베딩 모델
    
    Returns:
        List[Tuple[str, str, float]]: (용어1, 용어2, 유사도) 리스트
    """
    print("\n" + "=" * 70)
    print("📊 반대 개념 간 유사도 테스트 (Antonym Similarity Test)")
    print("=" * 70)
    
    # 반대 개념 쌍
    antonym_pairs = [
        ("갱신형", "비갱신형"),
        ("보험료 변동형", "확정 보험료"),
        ("갱신계약", "고정형")
    ]
    
    results = []
    
    for term1, term2 in antonym_pairs:
        # 임베딩 생성
        embedding1 = get_embedding(term1, model)
        embedding2 = get_embedding(term2, model)
        
        # 유사도 계산
        similarity = cosine_similarity(embedding1, embedding2)
        results.append((term1, term2, similarity))
        
        # 결과 출력
        similarity_percent = similarity * 100
        if similarity < 0.3:
            status = "✅ 명확히 구분됨"
        elif similarity < 0.6:
            status = "⚠️ 어느 정도 구분됨"
        else:
            status = "❌ 구분 불명확"
        
        print(f"\n🔍 '{term1}' ↔ '{term2}'")
        print(f"   유사도: {similarity:.4f} ({similarity_percent:.2f}%) {status}")
        print(f"   해석: 반대 개념이므로 유사도가 낮을수록 좋습니다.")
    
    return results


def test_definition_similarity(model: str = "text-embedding-3-small") -> List[Tuple[str, float]]:
    """
    용어와 정의 간 유사도 테스트
    
    Args:
        model: 임베딩 모델
    
    Returns:
        List[Tuple[str, float]]: (용어, 유사도) 리스트
    """
    print("\n" + "=" * 70)
    print("📊 용어-정의 간 유사도 테스트 (Term-Definition Similarity Test)")
    print("=" * 70)
    
    glossary = load_glossary()
    results = []
    
    for entry in glossary:
        term = entry["term"]
        definition = entry["definition"]
        
        # 임베딩 생성
        term_embedding = get_embedding(term, model)
        definition_embedding = get_embedding(definition, model)
        
        # 유사도 계산
        similarity = cosine_similarity(term_embedding, definition_embedding)
        results.append((term, similarity))
        
        # 결과 출력
        similarity_percent = similarity * 100
        if similarity >= 0.7:
            status = "✅ 높음"
        elif similarity >= 0.5:
            status = "⚠️ 보통"
        else:
            status = "❌ 낮음"
        
        print(f"\n🔍 용어: {term}")
        print(f"   정의: {definition}")
        print(f"   유사도: {similarity:.4f} ({similarity_percent:.2f}%) {status}")
    
    return results


def generate_report(
    synonym_results: List[Tuple[str, str, float]],
    antonym_results: List[Tuple[str, str, float]],
    definition_results: List[Tuple[str, float]],
    model: str
):
    """
    종합 리포트 생성
    
    Args:
        synonym_results: 동의어 유사도 결과
        antonym_results: 반대 개념 유사도 결과
        definition_results: 용어-정의 유사도 결과
        model: 임베딩 모델
    """
    print("\n" + "=" * 70)
    print("📋 종합 리포트 (Comprehensive Report)")
    print("=" * 70)
    
    print(f"\n🤖 임베딩 모델: {model}")
    
    # 동의어 평균 유사도
    if synonym_results:
        avg_synonym_sim = np.mean([sim for _, _, sim in synonym_results])
        print(f"\n✅ 동의어 평균 유사도: {avg_synonym_sim:.4f} ({avg_synonym_sim * 100:.2f}%)")
        print(f"   해석: 동의어는 유사도가 높을수록 좋습니다 (목표: 80% 이상)")
    
    # 반대 개념 평균 유사도
    if antonym_results:
        avg_antonym_sim = np.mean([sim for _, _, sim in antonym_results])
        print(f"\n✅ 반대 개념 평균 유사도: {avg_antonym_sim:.4f} ({avg_antonym_sim * 100:.2f}%)")
        print(f"   해석: 반대 개념은 유사도가 낮을수록 좋습니다 (목표: 30% 이하)")
    
    # 용어-정의 평균 유사도
    if definition_results:
        avg_definition_sim = np.mean([sim for _, sim in definition_results])
        print(f"\n✅ 용어-정의 평균 유사도: {avg_definition_sim:.4f} ({avg_definition_sim * 100:.2f}%)")
        print(f"   해석: 용어와 정의는 유사도가 높을수록 좋습니다 (목표: 70% 이상)")
    
    # 전체 평가
    print("\n" + "=" * 70)
    print("🎯 전문가 역산 로직 검증 결과")
    print("=" * 70)
    
    passed = True
    
    if synonym_results and avg_synonym_sim < 0.8:
        print("❌ 동의어 유사도가 목표치(80%)에 미달합니다.")
        passed = False
    else:
        print("✅ 동의어 유사도 검증 통과")
    
    if antonym_results and avg_antonym_sim > 0.3:
        print("❌ 반대 개념 유사도가 목표치(30%)를 초과합니다.")
        passed = False
    else:
        print("✅ 반대 개념 유사도 검증 통과")
    
    if definition_results and avg_definition_sim < 0.7:
        print("❌ 용어-정의 유사도가 목표치(70%)에 미달합니다.")
        passed = False
    else:
        print("✅ 용어-정의 유사도 검증 통과")
    
    if passed:
        print("\n🎉 임베딩 무결성 검증 완료: 모든 테스트 통과")
    else:
        print("\n⚠️ 임베딩 무결성 검증 실패: 일부 테스트 미달")
        print("   권장 사항: 임베딩 모델 변경 또는 용어 사전 보완")


def main():
    """
    메인 함수
    """
    print("=" * 70)
    print("🧪 RAG 임베딩 성능 검증 테스트")
    print("   전문가 역산 로직 기반 임베딩 무결성 검증")
    print("=" * 70)
    
    # 임베딩 모델 선택
    model = "text-embedding-3-small"
    print(f"\n🤖 사용 모델: {model}")
    
    try:
        # 1. 동의어 간 유사도 테스트
        synonym_results = test_synonym_similarity(model)
        
        # 2. 반대 개념 간 유사도 테스트
        antonym_results = test_antonym_similarity(model)
        
        # 3. 용어-정의 간 유사도 테스트
        definition_results = test_definition_similarity(model)
        
        # 4. 종합 리포트 생성
        generate_report(synonym_results, antonym_results, definition_results, model)
        
        print("\n" + "=" * 70)
        print("✅ 테스트 완료")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
