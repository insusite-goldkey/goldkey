"""
마스터 라우터 모듈
OCR 파싱 → 정적 엔진 → 3-Way 비교 전체 파이프라인 라우팅
"""
from typing import Dict, List, Optional
from pathlib import Path
import sys

# 정적 엔진 임포트
sys.path.append(str(Path(__file__).parent.parent))
from engines.static_calculators import CoverageCalculator
from .ocr_parser import OCRParser

class MasterRouter:
    """증권 분석 마스터 라우터 (Phase 1~5 통합)"""
    
    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        enable_rag: bool = False,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        openai_api_key: Optional[str] = None
    ):
        """
        초기화
        
        Args:
            gemini_api_key: Gemini API 키
            enable_rag: RAG 엔진 활성화 여부 (Phase 5)
            supabase_url: Supabase URL (RAG용)
            supabase_key: Supabase 키 (RAG용)
            openai_api_key: OpenAI API 키 (RAG 임베딩용)
        """
        # OCR 파서 초기화
        self.ocr_parser = OCRParser(gemini_api_key)
        
        # 증권 분석 엔진 초기화 (Phase 1)
        self.coverage_calculator = CoverageCalculator()
        
        # RAG 엔진 초기화 (Phase 5)
        self.rag_engine = None
        if enable_rag:
            try:
                from ..engines.rag_engine import RAGEngine
                self.rag_engine = RAGEngine(
                    supabase_url=supabase_url,
                    supabase_key=supabase_key,
                    openai_api_key=openai_api_key,
                    gemini_api_key=gemini_api_key
                )
                print("✅ RAG 엔진 활성화")
            except Exception as e:
                print(f"⚠️ RAG 엔진 초기화 실패: {str(e)}")
                self.rag_engine = None
        
        print("✅ 마스터 라우터 초기화 완료")
    
    def process_family_policies(
        self,
        gcs_uris: List[str],
        family_income_data: Dict[str, int]
    ) -> Dict:
        """
        가족 증권 전체 파이프라인 처리
        
        Args:
            gcs_uris: GCS URI 리스트
            family_income_data: 가족 구성원별 가처분소득
                {
                    "홍길동": 200,  # 만원
                    "김영희": 150
                }
        
        Returns:
            가족 분석 결과
                {
                    "ocr_results": [...],
                    "family_analysis": {...},
                    "summary": {...}
                }
        """
        print(f"\n{'='*80}")
        print(f"🚀 가족 증권 분석 파이프라인 시작")
        print(f"{'='*80}")
        print(f"증권 수: {len(gcs_uris)}개")
        print(f"가족 구성원: {len(family_income_data)}명")
        print(f"{'='*80}\n")
        
        # 1단계: OCR 파싱
        print("📋 [단계 1/3] OCR 파싱 시작...")
        ocr_results = self.ocr_parser.parse_multiple_policies(gcs_uris)
        
        if not ocr_results:
            print("❌ OCR 파싱 실패")
            return {
                "error": "OCR 파싱 실패",
                "ocr_results": [],
                "family_analysis": {},
                "summary": {}
            }
        
        print(f"✅ OCR 파싱 완료: {len(ocr_results)}개 증권")
        
        # 2단계: 가족 통합 분석
        print(f"\n📊 [단계 2/3] 가족 통합 분석 시작...")
        family_analysis = self.coverage_calculator.analyze_family_policies(
            ocr_results,
            family_income_data
        )
        
        print(f"✅ 가족 통합 분석 완료")
        
        # 3단계: 요약 리포트 생성
        print(f"\n📈 [단계 3/3] 요약 리포트 생성...")
        summary = self.coverage_calculator.generate_summary_report(family_analysis)
        
        print(f"✅ 요약 리포트 생성 완료")
        
        # 최종 결과
        result = {
            "ocr_results": ocr_results,
            "family_analysis": family_analysis,
            "summary": summary
        }
        
        print(f"\n{'='*80}")
        print(f"✅ 전체 파이프라인 완료")
        print(f"{'='*80}")
        print(f"총 구성원: {summary['total_members']}명")
        print(f"총 부족 금액: {summary['total_shortage']:,}원")
        print(f"긴급 항목: {summary['urgent_items_count']}개")
        print(f"{'='*80}\n")
        
        return result
    
    def process_single_policy(
        self,
        gcs_uri: str,
        disposable_income: int
    ) -> Dict:
        """
        단일 증권 분석
        
        Args:
            gcs_uri: GCS URI
            disposable_income: 가처분소득 (만원)
        
        Returns:
            분석 결과
        """
        print(f"\n{'='*80}")
        print(f"🚀 단일 증권 분석 시작")
        print(f"{'='*80}\n")
        
        # OCR 파싱
        ocr_result = self.ocr_parser.parse_policy_image(gcs_uri)
        
        if not ocr_result:
            return {
                "error": "OCR 파싱 실패",
                "ocr_result": {},
                "analysis": {}
            }
        
        # 16대 항목 매핑
        insurance_company = ocr_result.get("insurance_company", "기타")
        coverages = ocr_result.get("coverages", [])
        
        mapped_coverages = self.coverage_calculator.map_to_16_categories(
            coverages,
            insurance_company
        )
        
        # 3-Way 비교
        comparison = self.coverage_calculator.calculate_3way_comparison(
            mapped_coverages,
            disposable_income
        )
        
        result = {
            "ocr_result": ocr_result,
            "mapped_coverages": mapped_coverages,
            "3way_comparison": comparison
        }
        
        print(f"\n{'='*80}")
        print(f"✅ 단일 증권 분석 완료")
        print(f"{'='*80}\n")
        
        return result
    
    def query_knowledge_base(
        self,
        user_query: str,
        category: Optional[str] = None
    ) -> Dict:
        """
        RAG 지식베이스 질의 (Phase 5)
        
        Args:
            user_query: 사용자 질의
            category: 카테고리 필터 (예: "법인컨설팅", "화재보험", "배상책임")
        
        Returns:
            RAG 결과
                {
                    "query": "...",
                    "answer": "...",
                    "sources": [...],
                    "confidence": "high"
                }
        """
        if not self.rag_engine:
            return {
                "error": "RAG 엔진이 활성화되지 않았습니다",
                "query": user_query,
                "answer": "RAG 기능을 사용하려면 enable_rag=True로 초기화하세요",
                "sources": [],
                "confidence": "none"
            }
        
        return self.rag_engine.query(
            user_query=user_query,
            category=category,
            match_threshold=0.7,
            match_count=5,
            temperature=0.0  # 환각 차단
        )
    
    def route_request(
        self,
        request_type: str,
        **kwargs
    ) -> Dict:
        """
        요청 타입에 따라 적절한 엔진으로 라우팅
        
        Args:
            request_type: 요청 타입
                - "policy_analysis": 증권 분석 (Cat 1, 8) → coverage_calculator
                - "knowledge_query": 지식베이스 질의 (Cat 5, 7) → rag_engine
            **kwargs: 각 엔진에 필요한 파라미터
        
        Returns:
            처리 결과
        """
        print(f"\n{'='*80}")
        print(f"🚦 마스터 라우터 분기")
        print(f"{'='*80}")
        print(f"요청 타입: {request_type}")
        print(f"{'='*80}\n")
        
        if request_type == "policy_analysis":
            # 증권 분석 라우팅 (Phase 1)
            if "gcs_uris" in kwargs and "family_income_data" in kwargs:
                return self.process_family_policies(
                    kwargs["gcs_uris"],
                    kwargs["family_income_data"]
                )
            elif "gcs_uri" in kwargs and "disposable_income" in kwargs:
                return self.process_single_policy(
                    kwargs["gcs_uri"],
                    kwargs["disposable_income"]
                )
            else:
                return {"error": "증권 분석에 필요한 파라미터가 부족합니다"}
        
        elif request_type == "knowledge_query":
            # RAG 지식베이스 질의 (Phase 5)
            if "user_query" in kwargs:
                return self.query_knowledge_base(
                    kwargs["user_query"],
                    kwargs.get("category")
                )
            else:
                return {"error": "지식베이스 질의에 user_query가 필요합니다"}
        
        else:
            return {"error": f"알 수 없는 요청 타입: {request_type}"}
