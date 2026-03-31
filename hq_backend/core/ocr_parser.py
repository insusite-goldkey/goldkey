"""
OCR 파서 모듈
Google Vision API + Gemini 1.5 Pro를 통한 증권 이미지 파싱
16대 카테고리 매핑 키워드 기반 정규화
"""
import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import google.generativeai as genai
from google.cloud import vision
from google.cloud import storage

# 정적 데이터 로더 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))
from engines.static_calculators.static_data_loader import COVERAGE_16_MAPPING

class OCRParser:
    """증권 이미지 OCR 파싱 및 구조화"""
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        초기화
        
        Args:
            gemini_api_key: Gemini API 키 (없으면 환경변수에서 로드)
        """
        # Gemini 설정
        api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")
        
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Google Vision API 클라이언트
        self.vision_client = vision.ImageAnnotatorClient()
        
        # GCS 클라이언트
        self.gcs_client = storage.Client()
        
        # 16대 카테고리 매핑 로드
        self.category_mapping = COVERAGE_16_MAPPING
        
        if not self.category_mapping:
            raise RuntimeError("16대 카테고리 매핑 데이터가 로드되지 않았습니다.")
    
    def extract_text_from_gcs(self, gcs_uri: str) -> str:
        """
        GCS에 저장된 이미지에서 텍스트 추출 (Google Vision API)
        
        Args:
            gcs_uri: GCS URI (예: gs://bucket-name/path/to/image.jpg)
        
        Returns:
            추출된 텍스트
        """
        try:
            image = vision.Image()
            image.source.image_uri = gcs_uri
            
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Vision API 오류: {response.error.message}")
            
            if texts:
                return texts[0].description
            else:
                return ""
        
        except Exception as e:
            print(f"❌ Vision API 텍스트 추출 실패: {e}")
            return ""
    
    def build_gemini_prompt(self, raw_text: str) -> str:
        """
        Gemini 프롬프트 생성 (16대 카테고리 키워드 포함)
        
        Args:
            raw_text: Vision API로 추출한 원본 텍스트
        
        Returns:
            Gemini 프롬프트
        """
        # 16대 카테고리 키워드 추출
        category_keywords = {}
        for category, data in self.category_mapping["mappings"].items():
            category_keywords[category] = data["keywords"]
        
        prompt = f"""
당신은 보험증권 분석 전문가입니다. 아래 OCR로 추출된 보험증권 텍스트를 분석하여 JSON 형식으로 구조화하세요.

**중요 지시사항:**
1. 추출된 담보명은 반드시 아래 16대 표준 카테고리 키워드를 참고하여 정규화(Normalize)된 텍스트로 반환하세요.
2. 보험사명, 피보험자명, 계약자명, 증권번호, 가입일자를 정확히 추출하세요.
3. 각 담보(특약)의 가입금액을 숫자로 변환하세요 (예: "5천만원" → 50000000).
4. 담보명이 16대 카테고리 키워드와 유사하면 해당 카테고리명으로 정규화하세요.

**16대 표준 카테고리 및 키워드:**
{json.dumps(category_keywords, ensure_ascii=False, indent=2)}

**OCR 추출 텍스트:**
{raw_text}

**출력 형식 (JSON):**
{{
  "insurance_company": "보험사명",
  "policy_number": "증권번호",
  "insured_name": "피보험자명",
  "contractor_name": "계약자명",
  "contract_date": "YYYY-MM-DD",
  "coverages": [
    {{
      "name": "정규화된 담보명 (16대 카테고리 키워드 기반)",
      "amount": 가입금액(숫자),
      "original_name": "원본 담보명"
    }}
  ]
}}

**주의:** JSON만 출력하고 다른 설명은 포함하지 마세요.
"""
        return prompt
    
    def parse_with_gemini(self, raw_text: str) -> Dict:
        """
        Gemini로 텍스트 구조화
        
        Args:
            raw_text: Vision API로 추출한 원본 텍스트
        
        Returns:
            구조화된 증권 데이터
        """
        try:
            prompt = self.build_gemini_prompt(raw_text)
            
            response = self.gemini_model.generate_content(prompt)
            result_text = response.text.strip()
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # JSON 파싱
            parsed_data = json.loads(result_text)
            
            return parsed_data
        
        except json.JSONDecodeError as e:
            print(f"❌ Gemini JSON 파싱 실패: {e}")
            print(f"응답 텍스트: {result_text[:500]}")
            return {}
        except Exception as e:
            print(f"❌ Gemini 구조화 실패: {e}")
            return {}
    
    def normalize_coverage_names(self, coverages: List[Dict]) -> List[Dict]:
        """
        담보명을 16대 카테고리로 추가 정규화
        
        Args:
            coverages: Gemini가 추출한 담보 리스트
        
        Returns:
            정규화된 담보 리스트
        """
        normalized = []
        
        for coverage in coverages:
            coverage_name = coverage.get("name", "")
            original_name = coverage.get("original_name", coverage_name)
            amount = coverage.get("amount", 0)
            
            # 16대 카테고리 매칭
            matched_category = None
            
            for category, data in self.category_mapping["mappings"].items():
                keywords = data["keywords"]
                
                # 키워드 매칭
                for keyword in keywords:
                    if keyword in coverage_name or keyword in original_name:
                        matched_category = category
                        break
                
                if matched_category:
                    break
            
            # 매칭된 카테고리로 정규화
            if matched_category:
                normalized.append({
                    "name": matched_category,
                    "amount": amount,
                    "original_name": original_name
                })
            else:
                # 매칭 실패 시 원본 유지
                normalized.append({
                    "name": coverage_name,
                    "amount": amount,
                    "original_name": original_name
                })
        
        return normalized
    
    def parse_policy_image(self, gcs_uri: str) -> Dict:
        """
        증권 이미지 전체 파싱 파이프라인
        
        Args:
            gcs_uri: GCS URI (예: gs://bucket-name/path/to/policy.jpg)
        
        Returns:
            파싱된 증권 데이터
                {
                    "insurance_company": "삼성화재",
                    "policy_number": "12345678",
                    "insured_name": "홍길동",
                    "contractor_name": "홍길동",
                    "contract_date": "2023-01-15",
                    "coverages": [
                        {
                            "name": "암진단비",
                            "amount": 50000000,
                            "original_name": "일반암진단비"
                        }
                    ]
                }
        """
        print(f"📄 증권 이미지 파싱 시작: {gcs_uri}")
        
        # 1단계: Vision API로 텍스트 추출
        print("  [1/3] Vision API 텍스트 추출...")
        raw_text = self.extract_text_from_gcs(gcs_uri)
        
        if not raw_text:
            print("  ❌ 텍스트 추출 실패")
            return {}
        
        print(f"  ✅ 텍스트 추출 완료 ({len(raw_text)}자)")
        
        # 2단계: Gemini로 구조화
        print("  [2/3] Gemini 구조화...")
        parsed_data = self.parse_with_gemini(raw_text)
        
        if not parsed_data:
            print("  ❌ 구조화 실패")
            return {}
        
        print(f"  ✅ 구조화 완료 (담보 {len(parsed_data.get('coverages', []))}개)")
        
        # 3단계: 담보명 정규화
        print("  [3/3] 담보명 정규화...")
        if "coverages" in parsed_data:
            parsed_data["coverages"] = self.normalize_coverage_names(parsed_data["coverages"])
        
        print(f"  ✅ 정규화 완료")
        print(f"✅ 파싱 완료: {parsed_data.get('insured_name', '미확인')}님 증권")
        
        return parsed_data
    
    def parse_multiple_policies(self, gcs_uris: List[str]) -> List[Dict]:
        """
        여러 증권 이미지 일괄 파싱
        
        Args:
            gcs_uris: GCS URI 리스트
        
        Returns:
            파싱된 증권 데이터 리스트
        """
        results = []
        
        for i, gcs_uri in enumerate(gcs_uris, 1):
            print(f"\n{'='*80}")
            print(f"증권 {i}/{len(gcs_uris)} 파싱")
            print(f"{'='*80}")
            
            parsed = self.parse_policy_image(gcs_uri)
            
            if parsed:
                results.append(parsed)
        
        print(f"\n{'='*80}")
        print(f"✅ 전체 파싱 완료: {len(results)}/{len(gcs_uris)}개 성공")
        print(f"{'='*80}")
        
        return results
