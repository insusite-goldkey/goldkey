"""
골드키 AI 마스터 - 음성 상담 분석 엔진
Gemini 1.5 Pro 네이티브 오디오 처리 기능을 활용한 STT 및 쟁점 분석

작성일: 2026-03-30
"""

import os
import google.generativeai as genai
from typing import Dict, Optional, List
import streamlit as st


class VoiceAnalyzer:
    """
    음성 상담 분석 엔진
    - Gemini 1.5 Pro 네이티브 오디오 처리
    - STT (Speech-to-Text) 변환
    - 핵심 쟁점 3줄 요약
    - Next Action Items 도출
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        VoiceAnalyzer 초기화
        
        Args:
            gemini_api_key: Gemini API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. 환경변수 GEMINI_API_KEY를 설정하거나 api_key 파라미터를 전달하세요.")
        
        # Gemini API 설정
        genai.configure(api_key=self.api_key)
        
        # Gemini 1.5 Pro 모델 (오디오 지원)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    
    def analyze_voice_consultation(
        self,
        audio_file_path: str,
        customer_name: str = "고객"
    ) -> Dict:
        """
        음성 상담 파일 분석
        
        Args:
            audio_file_path: 오디오 파일 경로 (MP3, M4A, WAV 등)
            customer_name: 고객 이름
        
        Returns:
            Dict: {
                "transcript": str,  # 전체 대화 스크립트
                "key_issues": List[str],  # 핵심 쟁점 3줄
                "action_items": List[str],  # Next Action Items
                "success": bool,
                "error": Optional[str]
            }
        """
        try:
            # 오디오 파일 업로드
            audio_file = genai.upload_file(path=audio_file_path)
            
            # 프롬프트 구성
            prompt = f"""
당신은 경험 많은 보험 설계사입니다. 고객({customer_name}님)과의 통화 녹음 파일을 분석하여 다음 세 가지를 도출하세요.

**요구사항**:

1. **전체 대화 스크립트 (STT)**:
   - 오디오를 텍스트로 변환하세요.
   - 가능하면 화자를 구분하여 표시하세요 (예: [설계사], [고객]).
   - 정확한 발화 내용을 그대로 기록하세요.

2. **핵심 쟁점 3줄 요약**:
   - 이 고객이 무엇을 요구하고 있는지 명확히 파악하세요.
   - 보험 실무적 쟁점(예: 실손보험 청구, 후유장해 청구, 근접사고 조사 등)을 식별하세요.
   - 3줄 이내로 간결하게 요약하세요.

3. **Next Action Items (다음 할 일)**:
   - 담당 설계사가 당장 오늘/내일 처리해야 할 업무를 체크리스트 형태로 도출하세요.
   - 구체적이고 실행 가능한 항목으로 작성하세요 (예: "○○ 병원에 진단서 발급 요청", "보험금 청구서 작성 후 전송").
   - 최대 5개 항목으로 제한하세요.

**출력 형식**:

## 📝 전체 대화 스크립트

[설계사]: 안녕하세요, {customer_name}님. 무엇을 도와드릴까요?
[고객]: 안녕하세요. 저 지난주에 넘어져서 허리를 다쳤는데요...
(전체 대화 내용)

## 💡 핵심 쟁점 3줄 요약

1. 고객이 낙상 사고로 요추 추간판 탈출증 진단을 받았으며, 실손보험 청구를 원함.
2. 가입 후 2개월 차 사고로 보험사에서 손해사정인 파견 예정. 고지의무 위반 조사 가능성 높음.
3. MRI 촬영 완료했으나 수술 여부는 아직 미정. 보존적 치료 중.

## ✅ Next Action Items

- [ ] {customer_name}님께 근접사고 현장조사 대처 가이드 카톡 전송 (서명 주의사항 포함)
- [ ] ○○ 병원에 초진 차트 사본 요청 (Slip down hx 명시 여부 확인)
- [ ] MRI 영상 CD 및 판독 소견서 수령 일정 확인
- [ ] 실손보험 청구서 작성 후 고객 확인 요청
- [ ] 보존적 치료 영수증 전체 수집 (물리치료, 약물치료)
"""
            
            # Gemini API 호출 (오디오 파일 포함)
            response = self.model.generate_content([prompt, audio_file])
            
            # 결과 파싱
            result_text = response.text.strip()
            
            # 섹션별로 분리
            transcript = ""
            key_issues = []
            action_items = []
            
            # 간단한 파싱 (섹션 구분)
            sections = result_text.split("##")
            
            for section in sections:
                if "전체 대화 스크립트" in section or "📝" in section:
                    transcript = section.replace("전체 대화 스크립트", "").replace("📝", "").strip()
                elif "핵심 쟁점" in section or "💡" in section:
                    issues_text = section.replace("핵심 쟁점 3줄 요약", "").replace("핵심 쟁점", "").replace("💡", "").strip()
                    # 줄바꿈으로 분리
                    for line in issues_text.split("\n"):
                        line = line.strip()
                        if line and (line[0].isdigit() or line.startswith("-")):
                            # 번호나 - 제거
                            clean_line = line.lstrip("0123456789.-) ").strip()
                            if clean_line:
                                key_issues.append(clean_line)
                elif "Next Action" in section or "다음 할 일" in section or "✅" in section:
                    actions_text = section.replace("Next Action Items", "").replace("다음 할 일", "").replace("✅", "").strip()
                    # 줄바꿈으로 분리
                    for line in actions_text.split("\n"):
                        line = line.strip()
                        if line and ("[ ]" in line or "[]" in line or line.startswith("-")):
                            # 체크박스 제거
                            clean_line = line.replace("[ ]", "").replace("[]", "").replace("-", "").strip()
                            if clean_line:
                                action_items.append(clean_line)
            
            return {
                "transcript": transcript if transcript else result_text,
                "key_issues": key_issues[:3] if key_issues else ["분석 결과를 파싱할 수 없습니다."],
                "action_items": action_items[:5] if action_items else ["액션 아이템을 도출할 수 없습니다."],
                "raw_result": result_text,
                "success": True,
                "error": None
            }
        
        except Exception as e:
            return {
                "transcript": "",
                "key_issues": [],
                "action_items": [],
                "raw_result": "",
                "success": False,
                "error": str(e)
            }
    
    
    def get_supported_formats(self) -> List[str]:
        """
        지원되는 오디오 파일 형식 목록 반환
        
        Returns:
            List[str]: 지원되는 파일 확장자 목록
        """
        return ["mp3", "m4a", "wav", "ogg", "flac", "aac"]


# ══════════════════════════════════════════════════════════════════════════════
# 테스트 코드
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("🎙️ 음성 상담 분석 엔진 테스트")
    print("=" * 80)
    
    # API 키 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        exit(1)
    
    # VoiceAnalyzer 초기화
    analyzer = VoiceAnalyzer(gemini_api_key=api_key)
    
    print(f"✅ VoiceAnalyzer 초기화 완료")
    print(f"✅ 지원 형식: {', '.join(analyzer.get_supported_formats())}")
    print()
    
    # 테스트 파일 경로 (실제 파일이 있어야 함)
    test_audio_path = "test_consultation.mp3"
    
    if os.path.exists(test_audio_path):
        print(f"🎧 테스트 파일 분석 중: {test_audio_path}")
        result = analyzer.analyze_voice_consultation(
            audio_file_path=test_audio_path,
            customer_name="홍길동"
        )
        
        if result["success"]:
            print("\n✅ 분석 완료!")
            print("\n📝 전체 대화 스크립트:")
            print(result["transcript"][:500] + "..." if len(result["transcript"]) > 500 else result["transcript"])
            
            print("\n💡 핵심 쟁점:")
            for i, issue in enumerate(result["key_issues"], 1):
                print(f"{i}. {issue}")
            
            print("\n✅ Next Action Items:")
            for i, action in enumerate(result["action_items"], 1):
                print(f"{i}. {action}")
        else:
            print(f"\n❌ 분석 실패: {result['error']}")
    else:
        print(f"⚠️ 테스트 파일이 없습니다: {test_audio_path}")
        print("실제 오디오 파일을 업로드하여 테스트하세요.")
