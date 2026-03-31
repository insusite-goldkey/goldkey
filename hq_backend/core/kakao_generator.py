"""
[Phase 4] 카카오톡 세일즈 멘트 생성기

Gemini 1.5 Pro를 사용하여 최종 승인된 데이터를 바탕으로
고객에게 보낼 감성적인 카카오톡 메시지를 자동 작성
"""
from __future__ import annotations
from typing import Dict, List, Any
import os

try:
    import google.generativeai as genai
except ImportError:
    print("[WARNING] google-generativeai not installed. Install with: pip install google-generativeai")


class KakaoMessageGenerator:
    """카카오톡 세일즈 멘트 생성기"""
    
    def __init__(self, gemini_api_key: str = None):
        """
        Args:
            gemini_api_key: Gemini API 키 (None이면 환경변수에서 로드)
        """
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        else:
            self.model = None
            print("[WARNING] GEMINI_API_KEY not found. Using fallback template.")
    
    def generate_message(
        self,
        customer_name: str,
        urgent_items: List[Dict[str, Any]],
        total_shortage: int
    ) -> str:
        """
        카카오톡 세일즈 멘트 생성
        
        Args:
            customer_name: 고객명
            urgent_items: 긴급 보완 항목 리스트
            total_shortage: 총 부족 금액
        
        Returns:
            str: 300자 이내의 감성적인 카카오톡 메시지
        """
        if not self.model:
            return self._fallback_template(customer_name, urgent_items, total_shortage)
        
        prompt = self._build_prompt(customer_name, urgent_items, total_shortage)
        
        try:
            response = self.model.generate_content(prompt)
            message = response.text.strip()
            
            # 300자 제한
            if len(message) > 300:
                message = message[:297] + "..."
            
            return message
        
        except Exception as e:
            print(f"[ERROR] Gemini API 호출 실패: {e}")
            return self._fallback_template(customer_name, urgent_items, total_shortage)
    
    def _build_prompt(
        self,
        customer_name: str,
        urgent_items: List[Dict[str, Any]],
        total_shortage: int
    ) -> str:
        """Gemini 프롬프트 구성"""
        
        urgent_summary = "\n".join([
            f"- {item.get('category', '항목')}: {item.get('shortage', 0):,}원 부족"
            for item in urgent_items[:2]  # 상위 2개만
        ])
        
        prompt = f"""
당신은 보험 설계사입니다. 고객에게 보낼 카카오톡 메시지를 작성해주세요.

[고객 정보]
- 이름: {customer_name}님
- 총 부족 금액: {total_shortage:,}원
- 긴급 보완 항목:
{urgent_summary}

[작성 규칙]
1. 인사말로 시작 (따뜻하고 친근하게)
2. 핵심 부족 보장 1~2가지를 부드럽게 지적 (협박 금지, 걱정하는 톤)
3. 첨부된 PDF 제안서 확인 요청
4. 마무리 인사 (언제든 연락 가능하다는 메시지)
5. **300자 이내**로 작성
6. 이모지 적절히 사용
7. 존댓말 사용

[출력 형식]
카카오톡 메시지 본문만 출력 (추가 설명 없이)
"""
        return prompt
    
    def _fallback_template(
        self,
        customer_name: str,
        urgent_items: List[Dict[str, Any]],
        total_shortage: int
    ) -> str:
        """Gemini API 실패 시 대체 템플릿"""
        
        top_item = urgent_items[0] if urgent_items else {'category': '보장', 'shortage': 0}
        
        message = f"""
안녕하세요, {customer_name}님! 😊

오늘 분석해드린 가족 보험 리포트를 보내드립니다.

현재 '{top_item.get('category')}' 항목이 {top_item.get('shortage', 0):,}원 부족한 상황이라 조금 걱정이 되네요. 혹시 모를 상황에 대비하시면 더 안심하실 수 있을 것 같습니다.

첨부된 PDF 제안서 확인해보시고, 궁금하신 점 있으시면 언제든 연락 주세요! 🙏

감사합니다.
"""
        return message.strip()


if __name__ == "__main__":
    # 테스트 코드
    generator = KakaoMessageGenerator()
    
    test_urgent = [
        {'category': '질병수술비_1_5종', 'shortage': 10000000},
        {'category': '상해사망후유장해', 'shortage': 70000000}
    ]
    
    message = generator.generate_message(
        customer_name="홍길동",
        urgent_items=test_urgent,
        total_shortage=185050000
    )
    
    print("=" * 50)
    print("[생성된 카카오톡 멘트]")
    print("=" * 50)
    print(message)
    print("=" * 50)
    print(f"글자 수: {len(message)}자")
