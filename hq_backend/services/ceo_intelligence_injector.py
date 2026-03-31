# -*- coding: utf-8 -*-
"""
CEO 경영인 지능 주입 서비스
RAG 시스템에 상속세 유동성 방어 전략 지식 주입

작성일: 2026-03-31
목적: CEO 경영인정기보험 전문 지식을 RAG 시스템에 임베딩
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


class CEOIntelligenceInjector:
    """
    CEO 경영인 지능 주입 서비스
    
    핵심 기능:
    1. ceo_succession_intelligence.json 로드
    2. 화법 전환 (상속세 재원 → 현금 성벽)
    3. 은유적 후킹 언어 임베딩
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
        """CEO 경영인 지능 데이터 로드"""
        json_path = Path(__file__).parent.parent / "knowledge_base" / "ceo_succession_intelligence.json"
        
        if not json_path.exists():
            raise FileNotFoundError(f"지능 데이터 파일을 찾을 수 없습니다: {json_path}")
        
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def convert_phrase(self, original_phrase: str) -> str:
        """
        화법 전환
        
        Args:
            original_phrase: 원본 문구
        
        Returns:
            str: 전환된 문구
        """
        conversion_map = {
            "상속세 재원을 마련하세요": "국세청에 회사를 뺏기지 않을 '현금 성벽'을 쌓으십시오",
            "경영인정기보험에 가입하시면 상속세를 낼 수 있습니다": "대표님의 성(Castle)에 현금이라는 다리를 놓아, 유가족이 경영권을 지킬 수 있게 하겠습니다",
            "법인 돈으로 보험료를 내면 됩니다": "법인의 비용을 국세청이 아닌 대표님 가족의 상속 재원으로 치환하는 합법적 절세 전략입니다",
            "보험금으로 상속세를 내세요": "보험금은 상속세 전용 비상금이자, 유가족이 회사를 지킬 최후의 보루입니다"
        }
        
        return conversion_map.get(original_phrase, original_phrase)
    
    def generate_knowledge_chunks(self) -> List[Dict[str, str]]:
        """
        지식 청크 생성
        
        Returns:
            List[Dict]: 임베딩할 지식 청크 리스트
        """
        chunks = []
        
        # 1. 페르소나 정의
        persona = self.intelligence_data["persona"]
        chunks.append({
            "title": "CEO 경영인정기보험 페르소나: 황금 감옥에 갇힌 성주",
            "content": f"""
타겟: {persona['target']}

핵심 문제:
{persona['core_problem']}

은유:
{persona['metaphor']}

이들은 자산의 90%가 법인 주식과 공장 부지에 묶여 있어, 유고 시 유가족이 상속세를 낼 현금이 없어 회사를 헐값에 매각하거나 국가에 상납해야 하는 위기에 처해 있습니다.
""",
            "category": "persona"
        })
        
        # 2. 상속세 시스템
        tax_system = self.intelligence_data["inheritance_tax_system"]
        chunks.append({
            "title": "대한민국 상속세 시스템",
            "content": f"""
최고세율: {tax_system['max_rate'] * 100}%

누진세율표:
{chr(10).join([f"- {bracket['range']}: {bracket['rate'] * 100}% (공제 {bracket['deduction']:,}원)" for bracket in tax_system['tax_brackets']])}

최대주주 할증:
- 지분 50% 이상 또는 경영권 보유 시 {tax_system['additional_tax']['largest_shareholder_premium'] * 100}% 추가 과세
- 설명: {tax_system['additional_tax']['description']}

은유적 표현:
"대표님의 사후에 도착할 **국세청의 청구서**입니다. 그것은 상속이 아니라 대표님의 평생을 건 **마지막 세무조사**가 될 것입니다."
""",
            "category": "tax_system"
        })
        
        # 3. 비상장주식 평가
        valuation = self.intelligence_data["unlisted_stock_valuation"]
        chunks.append({
            "title": "비상장주식 가치 평가 방법",
            "content": f"""
보충적 평가 방식:
- 순손익가치 60% + 순자산가치 40%

순손익가치 계산:
{valuation['methods'][0]['formula']}
가중치: {valuation['methods'][0]['weight']}
환원율: {valuation['methods'][0]['discount_rate']}

순자산가치 계산:
{valuation['methods'][1]['formula']}
가중치: {valuation['methods'][1]['weight']}

예시:
회사: {valuation['example']['company']}
연 순이익: {valuation['example']['annual_profit']:,}원
순자산: {valuation['example']['net_assets']:,}원
평가액: {valuation['example']['valuation']:,}원
계산 과정: {valuation['example']['note']}
""",
            "category": "valuation"
        })
        
        # 4. 유동성 위기 시나리오
        crisis = self.intelligence_data["liquidity_crisis_scenario"]["case_study"]
        chunks.append({
            "title": "CEO 유동성 위기 시나리오",
            "content": f"""
사례 연구:
- CEO 나이: {crisis['ceo_age']}세
- 법인 가치: {crisis['company_value']:,}원
- 지분율: {crisis['ownership'] * 100}%
- 보유 현금: {crisis['liquid_assets']:,}원
- 추정 상속세: {crisis['inheritance_tax_estimate']:,}원
- 현금 부족액: {crisis['cash_shortage']:,}원
- 결과: {crisis['consequence']}

은유적 표현:
"대표님의 성(Castle)은 웅장하지만, 성문 밖으로 나갈 **현금**이라는 다리가 끊겨 있습니다."
""",
            "category": "crisis_scenario"
        })
        
        # 5. 은유적 후킹 언어
        hooking = self.intelligence_data["metaphorical_hooking_language"]
        chunks.append({
            "title": "CEO 경영인정기보험 은유적 후킹 언어",
            "content": f"""
상속세에 대한 표현:
{hooking['inheritance_tax']}

경영인정기보험에 대한 표현:
{hooking['executive_insurance']}

유동성 부족에 대한 표현:
{hooking['liquidity_shortage']}

세금 최적화에 대한 표현:
{hooking['tax_optimization']}

정관 변경에 대한 표현:
{hooking['corporate_shield']}
""",
            "category": "hooking_language"
        })
        
        # 6. 전략적 프레임워크
        framework = self.intelligence_data["strategic_framework"]
        
        # Step 7: 가상 상속세 시뮬레이션
        chunks.append({
            "title": "STEP 7: 가상 상속세 시뮬레이션",
            "content": f"""
{framework['step_7_simulation']['title']}

설명:
{framework['step_7_simulation']['description']}

계산 공식:
{framework['step_7_simulation']['formula']}

출력:
{framework['step_7_simulation']['output']}

핵심 메시지:
"단순히 보험료를 뽑지 않습니다. 내가 현재 대표님의 법인 가치를 평가하여, 유고 시 발생할 **현금 부족액**을 1원 단위까지 추정하여 보고하겠습니다."
""",
            "category": "strategy"
        })
        
        # Step 8: 비용 처리의 명분
        chunks.append({
            "title": "STEP 8: 비용 처리의 명분",
            "content": f"""
{framework['step_8_expense_justification']['title']}

핵심 메시지:
{framework['step_8_expense_justification']['key_message']}

법인세 절감 효과:
- 계산식: {framework['step_8_expense_justification']['corporate_tax_benefit']['premium_expense']}
- 예시: {framework['step_8_expense_justification']['corporate_tax_benefit']['example']}

전략적 포지셔닝:
"이 보험료는 지출이 아닌 **자산의 이동**입니다. 국가에 낼 세금을 대표님 가족의 상속 재원으로 치환하는 과정입니다."
""",
            "category": "strategy"
        })
        
        # Step 9: 정관 변경의 칼날
        chunks.append({
            "title": "STEP 9: 정관 변경의 칼날 (이중 엔진 전략)",
            "content": f"""
{framework['step_9_articles_amendment']['title']}

핵심 메시지:
{framework['step_9_articles_amendment']['key_message']}

이중 엔진 전략:

엔진 1: {framework['step_9_articles_amendment']['dual_engine'][0]['engine']}
- 메커니즘: {framework['step_9_articles_amendment']['dual_engine'][0]['mechanism']}
- 법적 근거: {framework['step_9_articles_amendment']['dual_engine'][0]['legal_basis']}

엔진 2: {framework['step_9_articles_amendment']['dual_engine'][1]['engine']}
- 메커니즘: {framework['step_9_articles_amendment']['dual_engine'][1]['mechanism']}
- 법적 근거: {framework['step_9_articles_amendment']['dual_engine'][1]['legal_basis']}

비판적 진단:
"많은 설계사들이 단순히 '법인 돈으로 개인 상속세 낸다'고만 말합니다. 이는 세무조사의 타겟이 되기 딱 좋은 **게으른 화법**입니다. 보험금이 법인으로 들어오고, 그 돈이 어떻게 합법적으로 유가족에게 전달되는지의 마지막 1인치까지 코딩해야 합니다."
""",
            "category": "strategy"
        })
        
        # 7. 화법 전환 예시
        conversion = self.intelligence_data["conversion_phrases"]
        chunks.append({
            "title": "CEO 경영인정기보험 화법 전환",
            "content": f"""
기존 화법 (금지):
{conversion['before']}

전환 화법 (권장):
{conversion['after']}

구체적 예시:

{chr(10).join([f"❌ 기존: {ex['before']}{chr(10)}✅ 전환: {ex['after']}{chr(10)}" for ex in conversion['examples']])}

핵심 원칙:
상속세 재원 → 현금 성벽
법인 비용 → 자산의 이동
보험 가입 → 정관 방패 수선
""",
            "category": "conversion"
        })
        
        return chunks
    
    def inject_knowledge(self) -> Dict[str, int]:
        """
        RAG 시스템에 지식 주입
        
        Returns:
            Dict: 주입 결과 통계
        """
        print(f"\n{'='*70}")
        print(f"🧠 CEO 경영인 지능 주입 시작")
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
                    "document_name": "CEO 경영인정기보험 지능 데이터베이스",
                    "content": chunk["content"],
                    "embedding": embedding,
                    "company": "goldkey_Ai_masters2026",
                    "reference_date": "2026-03",
                    "category": chunk["category"],
                    "title": chunk["title"],
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
        print(f"🎉 CEO 경영인 지능 주입 완료")
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
    print("🧠 CEO 경영인 지능 주입 서비스")
    print("=" * 70)
    
    injector = CEOIntelligenceInjector()
    
    # 지식 주입
    result = injector.inject_knowledge()
    
    print(f"\n📊 주입 결과:")
    print(f"- 생성된 청크: {result['total_chunks']}개")
    print(f"- 임베딩 완료: {result['embedded_chunks']}개")
    print(f"- 저장 성공: {result['success_count']}개")


if __name__ == "__main__":
    main()
