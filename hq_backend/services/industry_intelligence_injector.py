# -*- coding: utf-8 -*-
"""
업종별 지능 주입 서비스
제조업/건설업 특화 리스크 시나리오를 RAG 시스템에 주입

작성일: 2026-03-31
목적: 업종별 동적 리스크 산출 및 압박형 브리핑 지식 임베딩
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional

try:
    import openai
except ImportError:
    print("❌ openai 라이브러리가 설치되어 있지 않습니다.")
    raise

try:
    from supabase import create_client, Client
except ImportError:
    print("❌ supabase 라이브러리가 설치되어 있지 않습니다.")
    raise


class IndustryIntelligenceInjector:
    """
    업종별 지능 주입 서비스
    
    핵심 기능:
    1. 제조업/건설업 리스크 시나리오 로드
    2. 은유적 후킹 언어 임베딩
    3. 압박형 브리핑 문구 생성
    4. RAG 시스템에 지식 주입
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Args:
            openai_api_key: OpenAI API Key
            supabase_url: Supabase URL
            supabase_key: Supabase Service Key
        """
        # OpenAI 초기화
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        openai.api_key = self.openai_api_key
        
        # Supabase 초기화
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL 또는 SUPABASE_SERVICE_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # 지식 데이터 로드
        self.intelligence_data = self._load_intelligence_data()
    
    def _load_intelligence_data(self) -> Dict:
        """업종별 리스크 지능 데이터 로드"""
        json_path = Path(__file__).parent.parent / "knowledge_base" / "industry_risk_intelligence.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"지능 데이터 파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def generate_knowledge_chunks(self) -> List[Dict[str, str]]:
        """
        지식 청크 생성
        
        Returns:
            List[Dict]: 임베딩할 지식 청크 리스트
        """
        chunks = []
        
        # 제조업 지식 청크
        mfg = self.intelligence_data["industries"]["manufacturing"]
        
        # 1. 제조업 페르소나
        chunks.append({
            "title": "제조업 CEO 페르소나: 멈춰버린 기계와 중대재해의 올가미",
            "content": f"""
업종: {mfg['name']}
페르소나: {mfg['persona']}

핵심 문제:
{mfg['core_problem']}

은유적 표현:
- 자산: {mfg['metaphors']['asset']}
- 위기: {mfg['metaphors']['crisis']}
- 결과: {mfg['metaphors']['consequence']}

제조업 CEO의 자산은 공장과 기계에 박혀 있습니다. 그가 사라지면 공장은 가동을 멈추는 것이 아니라, **청산의 대상**으로 변합니다.
""",
            "category": "industry_manufacturing",
            "industry": "제조업"
        })
        
        # 2. 제조업 리스크 지표
        risk_metrics_content = "제조업 CEO 핵심 위험 지표:\n\n"
        for metric in mfg["risk_metrics"]:
            risk_metrics_content += f"""
{metric['metric']}:
- 설명: {metric['description']}
- 임계값: {metric['threshold']}
- 경고: {metric['warning']}
"""
        
        chunks.append({
            "title": "제조업 위험 지표 및 임계값",
            "content": risk_metrics_content,
            "category": "industry_manufacturing",
            "industry": "제조업"
        })
        
        # 3. 제조업 법적 리스크
        legal_content = "제조업 CEO 법적 리스크:\n\n"
        for risk in mfg["legal_risks"]:
            legal_content += f"""
{risk['law']} (시행: {risk.get('enacted', 'N/A')}):
- 처벌: {risk['penalty']}
- CEO 부재 시 영향: {risk['ceo_absence_impact']}
- 보험 포지셔닝: {risk['insurance_positioning']}
"""
        
        chunks.append({
            "title": "제조업 법적 리스크 (중대재해처벌법)",
            "content": legal_content,
            "category": "industry_manufacturing",
            "industry": "제조업"
        })
        
        # 4. 제조업 은유적 후킹 언어
        chunks.append({
            "title": "제조업 은유적 후킹 언어",
            "content": f"""
오프닝:
{mfg['hooking_phrases']['opening']}

위기 강조:
{mfg['hooking_phrases']['crisis']}

솔루션:
{mfg['hooking_phrases']['solution']}

압박형 결론:
{mfg['hooking_phrases']['pressure']}
""",
            "category": "industry_manufacturing",
            "industry": "제조업"
        })
        
        # 5. 제조업 동적 리스크 계산
        mfg_calc = self.intelligence_data["dynamic_risk_calculation"]["manufacturing"]
        chunks.append({
            "title": "제조업 동적 리스크 계산 공식",
            "content": f"""
{mfg_calc['formula']}

구성 요소:
{chr(10).join([f"- {comp['name']}: {comp['calculation']}" for comp in mfg_calc['components']])}

제조업 CEO의 총 리스크는 단순 상속세가 아닙니다. 중대재해 합의금(평균 5억원)과 설비 경매 손실(30%)을 반드시 포함해야 합니다.
""",
            "category": "industry_manufacturing",
            "industry": "제조업"
        })
        
        # 건설업 지식 청크
        const = self.intelligence_data["industries"]["construction"]
        
        # 6. 건설업 페르소나
        chunks.append({
            "title": "건설업 CEO 페르소나: 부러진 비계와 면허 취소의 단두대",
            "content": f"""
업종: {const['name']}
페르소나: {const['persona']}

핵심 문제:
{const['core_problem']}

은유적 표현:
- 자산: {const['metaphors']['asset']}
- 위기: {const['metaphors']['crisis']}
- 결과: {const['metaphors']['consequence']}

건설업은 유동성이 생명입니다. CEO의 유고는 곧 **신용 등급의 추락**이며, 이는 곧 프로젝트 중단과 면허 취소로 이어집니다.
""",
            "category": "industry_construction",
            "industry": "건설업"
        })
        
        # 7. 건설업 리스크 지표
        const_risk_metrics = "건설업 CEO 핵심 위험 지표:\n\n"
        for metric in const["risk_metrics"]:
            const_risk_metrics += f"""
{metric['metric']}:
- 설명: {metric['description']}
- 임계값: {metric['threshold']}
- 경고: {metric['warning']}
"""
        
        chunks.append({
            "title": "건설업 위험 지표 및 임계값",
            "content": const_risk_metrics,
            "category": "industry_construction",
            "industry": "건설업"
        })
        
        # 8. 건설업 법적 리스크
        const_legal = "건설업 CEO 법적 리스크:\n\n"
        for risk in const["legal_risks"]:
            const_legal += f"""
{risk['law']} ({risk['article']}):
- 처벌: {risk['penalty']}
- CEO 부재 시 영향: {risk['ceo_absence_impact']}
- 보험 포지셔닝: {risk['insurance_positioning']}
"""
        
        chunks.append({
            "title": "건설업 법적 리스크 (건설산업기본법)",
            "content": const_legal,
            "category": "industry_construction",
            "industry": "건설업"
        })
        
        # 9. 건설업 은유적 후킹 언어
        chunks.append({
            "title": "건설업 은유적 후킹 언어",
            "content": f"""
오프닝:
{const['hooking_phrases']['opening']}

위기 강조:
{const['hooking_phrases']['crisis']}

솔루션:
{const['hooking_phrases']['solution']}

압박형 결론:
{const['hooking_phrases']['pressure']}
""",
            "category": "industry_construction",
            "industry": "건설업"
        })
        
        # 10. 건설업 동적 리스크 계산
        const_calc = self.intelligence_data["dynamic_risk_calculation"]["construction"]
        chunks.append({
            "title": "건설업 동적 리스크 계산 공식",
            "content": f"""
{const_calc['formula']}

구성 요소:
{chr(10).join([f"- {comp['name']}: {comp['calculation']}" for comp in const_calc['components']])}

건설업 CEO의 총 리스크는 상속세뿐만 아니라 면허 유지 자본금과 연대보증 채무를 반드시 포함해야 합니다. 상속세 납부를 위한 배당은 실질자본금 부족을 야기하여 면허 취소로 이어집니다.
""",
            "category": "industry_construction",
            "industry": "건설업"
        })
        
        return chunks
    
    def inject_knowledge(self) -> Dict[str, int]:
        """
        RAG 시스템에 지식 주입
        
        Returns:
            Dict: 주입 결과 통계
        """
        print(f"\n{'='*70}")
        print(f"🏭 업종별 지능 주입 시작")
        print(f"{'='*70}")
        
        # 지식 청크 생성
        print(f"\n📝 [1/3] 지식 청크 생성 중...")
        chunks = self.generate_knowledge_chunks()
        print(f"✅ {len(chunks)}개 청크 생성 완료")
        
        # 임베딩 생성
        print(f"\n🤖 [2/3] 임베딩 생성 중...")
        embedded_chunks = []
        
        for idx, chunk in enumerate(chunks, 1):
            try:
                # OpenAI 임베딩 생성
                response = openai.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk["content"]
                )
                
                embedding = response.data[0].embedding
                
                embedded_chunks.append({
                    "document_name": f"업종별 리스크 지능 - {chunk['industry']}",
                    "content": chunk["content"],
                    "embedding": embedding,
                    "company": "goldkey_Ai_masters2026",
                    "reference_date": "2026-03",
                    "category": chunk["category"],
                    "title": chunk["title"],
                    "industry": chunk["industry"],
                    "is_active": True
                })
                
                print(f"   {idx}/{len(chunks)}: {chunk['title'][:50]}...")
            
            except Exception as e:
                print(f"❌ 임베딩 생성 실패 ({chunk['title']}): {e}")
        
        print(f"✅ {len(embedded_chunks)}개 임베딩 생성 완료")
        
        # Supabase 저장
        print(f"\n💾 [3/3] Supabase 저장 중...")
        success_count = 0
        
        for idx, chunk in enumerate(embedded_chunks, 1):
            try:
                self.supabase.table("gk_knowledge_base").insert(chunk).execute()
                success_count += 1
                print(f"   {idx}/{len(embedded_chunks)}: 저장 완료")
            
            except Exception as e:
                print(f"❌ 저장 실패 ({chunk['title']}): {e}")
        
        print(f"\n{'='*70}")
        print(f"🎉 업종별 지능 주입 완료")
        print(f"{'='*70}")
        print(f"✅ 총 {success_count}개 지식 청크 주입 완료")
        
        return {
            "total_chunks": len(chunks),
            "embedded_chunks": len(embedded_chunks),
            "success_count": success_count
        }


def main():
    """테스트 실행"""
    print("=" * 70)
    print("🏭 업종별 지능 주입 서비스")
    print("=" * 70)
    
    injector = IndustryIntelligenceInjector()
    
    # 지식 주입
    result = injector.inject_knowledge()
    
    print(f"\n📊 주입 결과:")
    print(f"- 생성된 청크: {result['total_chunks']}개")
    print(f"- 임베딩 완료: {result['embedded_chunks']}개")
    print(f"- 저장 성공: {result['success_count']}개")


if __name__ == "__main__":
    main()
