"""
건물 화재 급수 자동 판정 시스템 (Building Fire Grade Analyzer)
Gemini Vision + 건축물대장 OCR + 화재보험 요율 테이블 연동

[GP-SCAN-BUILDING] 우선순위 3 권고사항 구현
- Gemini Vision으로 건물 외관 사진 → 구조 분류 (철근콘크리트/목조/철골)
- 건축물대장 OCR → 용도·면적·준공연도 추출
- 화재보험 요율 테이블 연동 → 1급~5급 자동 판정
"""

from typing import Dict, List, Optional, Tuple
import os
import re
from pathlib import Path
import google.generativeai as genai
from google.cloud import vision
from google.cloud import storage
import json


class BuildingGradeAnalyzer:
    """건물 화재 급수 자동 판정 엔진"""
    
    # 건물 구조 분류 (Structure Classification)
    STRUCTURE_TYPES = {
        "RC": "철근콘크리트조",
        "STEEL": "철골조",
        "WOOD": "목조",
        "BRICK": "벽돌조",
        "STONE": "석조",
        "MIXED": "혼합구조"
    }
    
    # 화재 급수 매핑 테이블 (Structure × Usage → Fire Grade)
    FIRE_GRADE_TABLE = {
        # 철근콘크리트조
        ("RC", "주택"): 1,
        ("RC", "아파트"): 1,
        ("RC", "오피스텔"): 1,
        ("RC", "상가"): 2,
        ("RC", "공장"): 2,
        ("RC", "창고"): 2,
        ("RC", "병원"): 1,
        ("RC", "학교"): 1,
        
        # 철골조
        ("STEEL", "주택"): 2,
        ("STEEL", "상가"): 2,
        ("STEEL", "공장"): 2,
        ("STEEL", "창고"): 3,
        ("STEEL", "물류센터"): 3,
        
        # 목조
        ("WOOD", "주택"): 4,
        ("WOOD", "상가"): 5,
        ("WOOD", "창고"): 5,
        
        # 벽돌조
        ("BRICK", "주택"): 3,
        ("BRICK", "상가"): 3,
        ("BRICK", "공장"): 3,
        
        # 기타
        ("STONE", "주택"): 2,
        ("MIXED", "주택"): 3,
    }
    
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
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro-vision')
        
        # Google Vision API 클라이언트
        self.vision_client = vision.ImageAnnotatorClient()
        
        # GCS 클라이언트
        self.gcs_client = storage.Client()
    
    def analyze_building_structure_from_photo(
        self, 
        image_path: str
    ) -> Dict[str, any]:
        """
        건물 외관 사진에서 구조 분류
        
        Args:
            image_path: 건물 사진 경로 (로컬 또는 GCS URI)
        
        Returns:
            {
                'structure_type': 'RC',
                'structure_name': '철근콘크리트조',
                'confidence': 0.95,
                'reasoning': 'AI 판단 근거'
            }
        """
        print(f"🏗️ 건물 구조 분석 시작: {image_path}")
        
        # 이미지 로드
        if image_path.startswith("gs://"):
            # GCS에서 이미지 다운로드
            bucket_name = image_path.split("/")[2]
            blob_path = "/".join(image_path.split("/")[3:])
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_path)
            image_bytes = blob.download_as_bytes()
        else:
            # 로컬 파일 읽기
            with open(image_path, "rb") as f:
                image_bytes = f.read()
        
        # Gemini Vision 프롬프트
        prompt = """
당신은 건축 구조 전문가입니다. 이 건물 사진을 분석하여 다음 정보를 JSON 형식으로 출력하세요.

**분석 항목:**
1. 건물 구조 (철근콘크리트조, 철골조, 목조, 벽돌조, 석조, 혼합구조 중 선택)
2. 판단 근거 (외벽 재질, 기둥 형태, 창문 구조 등)
3. 신뢰도 (0.0~1.0)

**출력 형식 (JSON):**
{
  "structure_type": "RC | STEEL | WOOD | BRICK | STONE | MIXED",
  "reasoning": "판단 근거 상세 설명",
  "confidence": 0.0~1.0
}

**주의:** JSON만 출력하고 다른 설명은 포함하지 마세요.
"""
        
        try:
            # Gemini Vision 호출
            response = self.gemini_model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_bytes}
            ])
            
            result_text = response.text.strip()
            
            # JSON 추출
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            
            result_text = result_text.strip()
            
            # JSON 파싱
            parsed = json.loads(result_text)
            
            structure_type = parsed.get("structure_type", "MIXED")
            structure_name = self.STRUCTURE_TYPES.get(structure_type, "혼합구조")
            
            print(f"  ✅ 구조 분석 완료: {structure_name} (신뢰도: {parsed.get('confidence', 0):.2f})")
            
            return {
                'structure_type': structure_type,
                'structure_name': structure_name,
                'confidence': parsed.get('confidence', 0.0),
                'reasoning': parsed.get('reasoning', '')
            }
        
        except Exception as e:
            print(f"  ❌ 구조 분석 실패: {e}")
            return {
                'structure_type': 'MIXED',
                'structure_name': '혼합구조',
                'confidence': 0.0,
                'reasoning': f'분석 실패: {str(e)}'
            }
    
    def parse_building_registry(
        self, 
        registry_image_path: str
    ) -> Dict[str, any]:
        """
        건축물대장 OCR 파싱
        
        Args:
            registry_image_path: 건축물대장 이미지 경로
        
        Returns:
            {
                'usage': '주택',
                'area': 120.5,
                'completion_year': 2015,
                'floors': 3,
                'raw_text': 'OCR 원본 텍스트'
            }
        """
        print(f"📄 건축물대장 파싱 시작: {registry_image_path}")
        
        try:
            # Vision API로 텍스트 추출
            if registry_image_path.startswith("gs://"):
                image = vision.Image()
                image.source.image_uri = registry_image_path
            else:
                with open(registry_image_path, "rb") as f:
                    content = f.read()
                image = vision.Image(content=content)
            
            response = self.vision_client.text_detection(image=image)
            texts = response.text_annotations
            
            if response.error.message:
                raise Exception(f"Vision API 오류: {response.error.message}")
            
            raw_text = texts[0].description if texts else ""
            
            print(f"  ✅ OCR 완료 ({len(raw_text)}자)")
            
            # 정규식으로 주요 정보 추출
            usage = self._extract_usage(raw_text)
            area = self._extract_area(raw_text)
            completion_year = self._extract_completion_year(raw_text)
            floors = self._extract_floors(raw_text)
            
            return {
                'usage': usage,
                'area': area,
                'completion_year': completion_year,
                'floors': floors,
                'raw_text': raw_text
            }
        
        except Exception as e:
            print(f"  ❌ 건축물대장 파싱 실패: {e}")
            return {
                'usage': '기타',
                'area': 0.0,
                'completion_year': 0,
                'floors': 0,
                'raw_text': ''
            }
    
    def _extract_usage(self, text: str) -> str:
        """용도 추출"""
        usage_keywords = {
            "주택": ["단독주택", "다가구주택", "주택"],
            "아파트": ["공동주택", "아파트"],
            "오피스텔": ["오피스텔"],
            "상가": ["근린생활시설", "상가", "점포"],
            "공장": ["공장", "제조업소"],
            "창고": ["창고", "물류"],
            "병원": ["의료시설", "병원"],
            "학교": ["교육연구시설", "학교"]
        }
        
        for usage, keywords in usage_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return usage
        
        return "기타"
    
    def _extract_area(self, text: str) -> float:
        """면적 추출 (㎡)"""
        # 패턴: 123.45㎡, 123.45m2, 123.45평
        patterns = [
            r"(\d+\.?\d*)\s*㎡",
            r"(\d+\.?\d*)\s*m2",
            r"(\d+\.?\d*)\s*평"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                area = float(match.group(1))
                # 평 → ㎡ 변환
                if "평" in pattern:
                    area = area * 3.3058
                return area
        
        return 0.0
    
    def _extract_completion_year(self, text: str) -> int:
        """준공연도 추출"""
        # 패턴: 2015년, 2015.03.15
        patterns = [
            r"(\d{4})년",
            r"(\d{4})\.\d{1,2}\.\d{1,2}"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return 0
    
    def _extract_floors(self, text: str) -> int:
        """층수 추출"""
        # 패턴: 3층, 지상 3층
        patterns = [
            r"지상\s*(\d+)\s*층",
            r"(\d+)\s*층"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        return 0
    
    def determine_fire_grade(
        self, 
        structure_type: str,
        usage: str
    ) -> Tuple[int, str]:
        """
        화재 급수 판정
        
        Args:
            structure_type: 구조 타입 (RC, STEEL, WOOD 등)
            usage: 용도 (주택, 상가, 공장 등)
        
        Returns:
            (화재급수, 설명)
        """
        # 정확한 매칭
        key = (structure_type, usage)
        if key in self.FIRE_GRADE_TABLE:
            grade = self.FIRE_GRADE_TABLE[key]
            return (grade, f"{self.STRUCTURE_TYPES.get(structure_type, '기타')} × {usage} → {grade}급")
        
        # 구조만 매칭 (기본 급수)
        default_grades = {
            "RC": 2,
            "STEEL": 2,
            "WOOD": 4,
            "BRICK": 3,
            "STONE": 2,
            "MIXED": 3
        }
        
        grade = default_grades.get(structure_type, 3)
        return (grade, f"{self.STRUCTURE_TYPES.get(structure_type, '기타')} (기본) → {grade}급")
    
    def analyze_building_comprehensive(
        self,
        building_photo_path: str,
        registry_image_path: Optional[str] = None
    ) -> Dict[str, any]:
        """
        건물 종합 분석 (사진 + 대장)
        
        Args:
            building_photo_path: 건물 외관 사진 경로
            registry_image_path: 건축물대장 이미지 경로 (선택)
        
        Returns:
            {
                'structure': {...},
                'registry': {...},
                'fire_grade': 2,
                'fire_grade_description': '철근콘크리트조 × 주택 → 1급',
                'recommendation': '화재보험 가입 권고사항'
            }
        """
        print(f"\n{'='*80}")
        print("🏢 건물 화재 급수 종합 분석")
        print(f"{'='*80}\n")
        
        # 1단계: 건물 구조 분석
        structure_result = self.analyze_building_structure_from_photo(building_photo_path)
        
        # 2단계: 건축물대장 파싱 (선택)
        registry_result = {}
        if registry_image_path:
            registry_result = self.parse_building_registry(registry_image_path)
        else:
            registry_result = {
                'usage': '기타',
                'area': 0.0,
                'completion_year': 0,
                'floors': 0,
                'raw_text': ''
            }
        
        # 3단계: 화재 급수 판정
        structure_type = structure_result['structure_type']
        usage = registry_result['usage']
        
        fire_grade, grade_description = self.determine_fire_grade(structure_type, usage)
        
        # 4단계: 권고사항 생성
        recommendation = self._generate_recommendation(
            fire_grade, 
            structure_result, 
            registry_result
        )
        
        print(f"\n{'='*80}")
        print(f"✅ 분석 완료: 화재 {fire_grade}급")
        print(f"{'='*80}\n")
        
        return {
            'structure': structure_result,
            'registry': registry_result,
            'fire_grade': fire_grade,
            'fire_grade_description': grade_description,
            'recommendation': recommendation
        }
    
    def _generate_recommendation(
        self,
        fire_grade: int,
        structure_result: Dict,
        registry_result: Dict
    ) -> str:
        """화재보험 가입 권고사항 생성"""
        
        structure_name = structure_result['structure_name']
        usage = registry_result['usage']
        area = registry_result['area']
        
        recommendation = f"""
## 🔥 화재보험 가입 권고사항

### 건물 정보
- **구조**: {structure_name}
- **용도**: {usage}
- **면적**: {area:.1f}㎡
- **화재 급수**: {fire_grade}급

### 위험도 평가
"""
        
        if fire_grade <= 2:
            recommendation += """
✅ **저위험 등급**
- 철근콘크리트조 또는 철골조로 화재 위험이 낮습니다.
- 기본 화재보험 가입으로 충분합니다.
"""
        elif fire_grade == 3:
            recommendation += """
⚠️ **중위험 등급**
- 화재 확산 가능성이 있습니다.
- 충분한 보험가입금액 설정을 권장합니다.
"""
        else:
            recommendation += """
🚨 **고위험 등급**
- 목조 또는 가연성 재료로 화재 위험이 높습니다.
- 재조달가액의 130% 이상 가입을 강력히 권장합니다.
- 소화기·스프링클러 설치 시 할인 혜택이 있습니다.
"""
        
        return recommendation.strip()


# 사용 예시
if __name__ == "__main__":
    analyzer = BuildingGradeAnalyzer()
    
    # 건물 종합 분석
    result = analyzer.analyze_building_comprehensive(
        building_photo_path="path/to/building_photo.jpg",
        registry_image_path="path/to/registry.jpg"
    )
    
    print(result['recommendation'])
