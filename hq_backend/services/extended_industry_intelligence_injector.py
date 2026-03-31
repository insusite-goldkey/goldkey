# -*- coding: utf-8 -*-
"""
확장 업종별 지능 주입 서비스
유통/의료/IT/의료종합병원 특화 리스크 시나리오를 RAG 시스템에 주입

작성일: 2026-03-31
목적: 확장 업종별 동적 리스크 산출 및 압박형 브리핑 지식 임베딩
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


class ExtendedIndustryIntelligenceInjector:
    """
    확장 업종별 지능 주입 서비스
    
    핵심 기능:
    1. 유통/의료/IT/의료종합병원 리스크 시나리오 로드
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
        """확장 업종별 리스크 지능 데이터 로드"""
        json_path = Path(__file__).parent.parent / "knowledge_base" / "extended_industry_risk_intelligence.json"
        
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
        
        # 유통/물류업 지식 청크
        dist = self.intelligence_data["industries"]["distribution"]
        
        chunks.append({
            "title": "유통/물류업 CEO 페르소나: 재고라는 이름의 덩어리와 마르는 현금",
            "content": f"""
업종: {dist['name']}
페르소나: {dist['persona']}

핵심 문제:
{dist['core_problem']}

은유적 표현:
- 자산: {dist['metaphors']['asset']}
- 위기: {dist['metaphors']['crisis']}
- 결과: {dist['metaphors']['consequence']}

유통업은 겉으로는 매출 규모가 크지만, 실상은 **재고와 미수금**이라는 늪에 빠져 있습니다. CEO 유고 시 공급망이 흔들리면 재고는 순식간에 **악성 폐기물**이 됩니다.

동적 리스크 공식:
{dist['dynamic_risk_formula']}
""",
            "category": "industry_distribution",
            "industry": "유통/물류업"
        })
        
        chunks.append({
            "title": "유통/물류업 은유적 후킹 언어",
            "content": f"""
오프닝:
{dist['hooking_phrases']['opening']}

위기 강조:
{dist['hooking_phrases']['crisis']}

솔루션:
{dist['hooking_phrases']['solution']}

압박형 결론:
{dist['hooking_phrases']['pressure']}

전략적 포지셔닝:
- Primary: {dist['strategic_positioning']['primary']}
- Secondary: {dist['strategic_positioning']['secondary']}
- Tertiary: {dist['strategic_positioning']['tertiary']}
""",
            "category": "industry_distribution",
            "industry": "유통/물류업"
        })
        
        # 의료/병의원 지식 청크
        med = self.intelligence_data["industries"]["medical"]
        
        chunks.append({
            "title": "의료/병의원 CEO 페르소나: 면허는 승계되지 않고 빚만 남는 수술대",
            "content": f"""
업종: {med['name']}
페르소나: {med['persona']}

핵심 문제:
{med['core_problem']}

은유적 표현:
- 자산: {med['metaphors']['asset']}
- 위기: {med['metaphors']['crisis']}
- 결과: {med['metaphors']['consequence']}

의료업은 대표자(원장)의 **인적 전문성**에 100% 의존하는 구조입니다. 원장 유고 시 병원 면허는 즉시 소멸하며, 병원의 가치는 권리금 없이 기계값(중고가)으로 폭락합니다.

동적 리스크 공식:
{med['dynamic_risk_formula']}
""",
            "category": "industry_medical",
            "industry": "의료/병의원"
        })
        
        chunks.append({
            "title": "의료/병의원 법적 리스크",
            "content": f"""
{chr(10).join([f"{risk['law']} ({risk['article']}): {risk['penalty']}\nCEO 부재 시 영향: {risk['ceo_absence_impact']}\n보험 포지셔닝: {risk['insurance_positioning']}" for risk in med['legal_risks']])}

의료법 제33조에 따라 원장 사망 시 병원 면허는 자동 소멸됩니다. 하지만 원장이 졌던 거액의 대출은 가족에게 그대로 상속됩니다.
""",
            "category": "industry_medical",
            "industry": "의료/병의원"
        })
        
        chunks.append({
            "title": "의료/병의원 은유적 후킹 언어",
            "content": f"""
오프닝:
{med['hooking_phrases']['opening']}

위기 강조:
{med['hooking_phrases']['crisis']}

솔루션:
{med['hooking_phrases']['solution']}

압박형 결론:
{med['hooking_phrases']['pressure']}

전략적 포지셔닝:
- Primary: {med['strategic_positioning']['primary']}
- Secondary: {med['strategic_positioning']['secondary']}
- Tertiary: {med['strategic_positioning']['tertiary']}
""",
            "category": "industry_medical",
            "industry": "의료/병의원"
        })
        
        # IT/지식서비스업 지식 청크
        it = self.intelligence_data["industries"]["it_service"]
        
        chunks.append({
            "title": "IT/지식서비스업 CEO 페르소나: 코드만 남고 지능이 증발한 서버실",
            "content": f"""
업종: {it['name']}
페르소나: {it['persona']}

핵심 문제:
{it['core_problem']}

은유적 표현:
- 자산: {it['metaphors']['asset']}
- 위기: {it['metaphors']['crisis']}
- 결과: {it['metaphors']['consequence']}

IT 업계는 무형 자산이 핵심이지만, 상속 시에는 **과거의 수익력**이 독이 되어 돌아옵니다. CEO 유고 시 핵심 인력(Keyman)이 이탈하면 기업 가치는 제로(0)가 되지만, 상속세는 **잘나가던 시절의 가치**를 기준으로 청구됩니다.

동적 리스크 공식:
{it['dynamic_risk_formula']}
""",
            "category": "industry_it",
            "industry": "IT/지식서비스업"
        })
        
        chunks.append({
            "title": "IT/지식서비스업 은유적 후킹 언어",
            "content": f"""
오프닝:
{it['hooking_phrases']['opening']}

위기 강조:
{it['hooking_phrases']['crisis']}

솔루션:
{it['hooking_phrases']['solution']}

압박형 결론:
{it['hooking_phrases']['pressure']}

전략적 포지셔닝:
- Primary: {it['strategic_positioning']['primary']}
- Secondary: {it['strategic_positioning']['secondary']}
- Tertiary: {it['strategic_positioning']['tertiary']}

현금 없는 IT 법인에게 상속은 곧 **합법적 폐업**입니다.
""",
            "category": "industry_it",
            "industry": "IT/지식서비스업"
        })
        
        # 의료종합병원 지식 청크
        mg = self.intelligence_data["industries"]["medical_group"]
        
        chunks.append({
            "title": "의료종합병원 페르소나: 각자 대출의 덫과 분할 채무의 공포",
            "content": f"""
업종: {mg['name']}
페르소나: {mg['persona']}

핵심 문제:
{mg['core_problem']}

은유적 표현:
- 자산: {mg['metaphors']['asset']}
- 위기: {mg['metaphors']['crisis']}
- 결과: {mg['metaphors']['consequence']}

병원 총액을 만들기 위해 각자 명의로 받은 대출은 서류상 독립적이나, 운영 실무상 운명 공동체입니다. 한 의사가 질병이나 사망으로 대열에서 이탈하는 순간, 병원 수익은 급감하는데 그가 책임지던 대출 원리금은 남겨진 동료들이 n분의 1로 떠안아야 합니다.

동적 리스크 공식:
{mg['dynamic_risk_formula']}
""",
            "category": "industry_medical_group",
            "industry": "의료종합병원"
        })
        
        chunks.append({
            "title": "의료종합병원 은유적 후킹 언어 및 생명줄 전략",
            "content": f"""
오프닝:
{mg['hooking_phrases']['opening']}

위기 강조:
{mg['hooking_phrases']['crisis']}

솔루션:
{mg['hooking_phrases']['solution']}

압박형 결론:
{mg['hooking_phrases']['pressure']}

전략적 포지셔닝:
- Primary: {mg['strategic_positioning']['primary']}
- Secondary: {mg['strategic_positioning']['secondary']}
- Tertiary: {mg['strategic_positioning']['tertiary']}

의료법인 계약자 플랜:
계약자를 의료법인으로 하십시오. 사망보험금은 법인으로 유입되어 낙오된 원장님의 대출금을 즉시 상계합니다. 이는 동료들에게는 **채무 전가 차단**을, 유가족에게는 **부채 없는 자산 승계**를 보장하는 유일한 길입니다.

내가 확인한 결과, 이 병원은 한 명의 낙오만으로도 전체가 수렁에 빠지는 **각자 대출의 늪**에 있습니다. 대표님, **동료를 향한 마지막 예의**이자 **가족을 위한 생명줄**이라는 프레임으로 클로징하십시오.
""",
            "category": "industry_medical_group",
            "industry": "의료종합병원"
        })
        
        # 업종별 공통 경고 문구
        chunks.append({
            "title": "업종별 공통 경고 문구",
            "content": """
당신의 업종에서 상속은 단순한 세금이 아니라 **사업의 장례식**이 될 수 있습니다.

업종별 결핍(Pain Point):
- 유통업: 재고 현금화 불가
- 의료업: 부채 상속 (면허 소멸)
- IT업: 고평가 주식 (무형자산 증발)
- 의료종합병원: 각자 대출의 채무 도미노

능동적 전략 보고:
이 대표는 현재 **가짜 자산(재고/면허/코드)**에 속고 있습니다. 진짜 자산인 **현금(보험금)**의 필요성을 1인칭으로 압박하십시오.
""",
            "category": "industry_common",
            "industry": "공통"
        })
        
        return chunks
    
    def inject_knowledge(self) -> Dict[str, int]:
        """
        RAG 시스템에 지식 주입
        
        Returns:
            Dict: 주입 결과 통계
        """
        print(f"\n{'='*70}")
        print(f"🏢 확장 업종별 지능 주입 시작")
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
                    "document_name": f"확장 업종별 리스크 지능 - {chunk['industry']}",
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
        print(f"🎉 확장 업종별 지능 주입 완료")
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
    print("🏢 확장 업종별 지능 주입 서비스")
    print("=" * 70)
    
    injector = ExtendedIndustryIntelligenceInjector()
    
    # 지식 주입
    result = injector.inject_knowledge()
    
    print(f"\n📊 주입 결과:")
    print(f"- 생성된 청크: {result['total_chunks']}개")
    print(f"- 임베딩 완료: {result['embedded_chunks']}개")
    print(f"- 저장 성공: {result['success_count']}개")


if __name__ == "__main__":
    main()
