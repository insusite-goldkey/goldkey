"""
골드키 AI 마스터 - RAG 실전 보상 데이터베이스 자동 구축기
한국인 다빈도 질병 30개 + 상해 30개 = 총 60개 표준 실무 매뉴얼 자동 생성

작성일: 2026-03-30
"""

import os
import time
import google.generativeai as genai
from pathlib import Path
from typing import List, Dict


# ══════════════════════════════════════════════════════════════════════════════
# 한국인 다빈도 질병 30개 (보험 청구 상위)
# ══════════════════════════════════════════════════════════════════════════════

DISEASES = [
    "백내장",
    "갑상선암",
    "추간판탈출증 (디스크)",
    "치핵 (치질)",
    "대장용종",
    "위암",
    "유방암",
    "폐암",
    "간암",
    "대장암",
    "전립선암",
    "자궁근종",
    "난소낭종",
    "담석증",
    "충수돌기염 (맹장염)",
    "슬관절 반월상연골 파열",
    "회전근개 파열",
    "척추관협착증",
    "퇴행성 관절염",
    "류마티스 관절염",
    "당뇨병성 망막병증",
    "녹내장",
    "뇌경색 (허혈성 뇌졸중)",
    "뇌출혈",
    "협심증",
    "심근경색",
    "부정맥",
    "만성 신부전",
    "간경화",
    "췌장염"
]


# ══════════════════════════════════════════════════════════════════════════════
# 한국인 다빈도 상해 30개 (사고 및 후유장해 청구 상위)
# ══════════════════════════════════════════════════════════════════════════════

INJURIES = [
    "척추 압박골절",
    "전방십자인대 (ACL) 파열",
    "콜레스 골절 (손목 골절)",
    "발목 골절",
    "쇄골 골절",
    "늑골 골절 (갈비뼈 골절)",
    "대퇴골 골절",
    "경골 골절",
    "상완골 골절",
    "요골 골절",
    "척추 골절 (흉추, 요추)",
    "경추 염좌 (목 디스크)",
    "요추 염좌 (허리 디스크)",
    "슬개골 골절",
    "아킬레스건 파열",
    "회전근개 파열 (외상성)",
    "슬관절 반월상연골 파열 (외상성)",
    "뇌진탕",
    "외상성 뇌출혈",
    "경막외 출혈",
    "경막하 출혈",
    "안와 골절 (눈 주위 골절)",
    "비골 골절",
    "중족골 골절 (발등 골절)",
    "수근골 골절 (손목뼈 골절)",
    "척수 손상",
    "말초신경 손상",
    "화상 (2도, 3도)",
    "열상 (깊은 상처)",
    "치아 파절 및 탈구"
]


# ══════════════════════════════════════════════════════════════════════════════
# Gemini 프롬프트 템플릿
# ══════════════════════════════════════════════════════════════════════════════

def generate_prompt(case_name: str, case_type: str) -> str:
    """
    질병/상해별 표준 실무 매뉴얼 생성 프롬프트
    
    Args:
        case_name: 질병명 또는 상해명
        case_type: "질병" 또는 "상해"
    
    Returns:
        str: Gemini 프롬프트
    """
    
    prompt = f"""
당신은 대한민국 보험 실무 전문가입니다. **{case_name}**에 대한 표준 실무 매뉴얼을 작성하세요.

**요구사항**:
1. 실제 보험 청구 현장에서 바로 사용할 수 있는 실용적인 내용
2. 의학 용어는 한글과 영문을 병기
3. 보험사 의료자문 및 고지의무 위반 방어 논리 포함
4. 고객에게 바로 전달할 수 있는 친절한 안내문 포함

**출력 형식**:

# {case_name} - 보험 실무 표준 매뉴얼

## 1. 가상 초진기록지 (영문 의무기록)

**Chief Complaint (C/C)**:
(환자의 주요 호소 증상을 영문으로 작성)

**Present Illness (P/I)**:
(현재 질병/상해의 발생 경위 및 증상 진행 과정을 영문으로 작성)

**Past History**:
(과거 병력, 특히 이번 질병/상해와 관련될 수 있는 병력)

**Physical Examination**:
(신체 검사 소견)

**Impression (Imp)**:
(진단명을 영문으로 작성)

**Plan**:
(치료 계획: 약물, 물리치료, 수술 등)

---

## 2. 의무기록 해석 및 보험 실무 쟁점

### 의학 용어 해석
- (주요 의학 용어를 한글로 풀어서 설명)

### 보험 실무 핵심 쟁점
1. **사고 기여도 (외상성 vs 퇴행성)**:
   - (이 질병/상해가 사고로 인한 것인지, 퇴행성 변화인지 구분하는 기준)
   
2. **고지의무 위반 리스크**:
   - (가입 전 병력이 있었는지 확인해야 할 사항)
   
3. **의료자문 방어 논리**:
   - (보험사 자문의가 불리한 소견을 낼 경우 대응 논리)

---

## 3. 보험금 청구 필수 서류

### 실손보험 청구
- [ ] 보험금 청구서
- [ ] 개인정보 수집·이용 동의서
- [ ] 진단서 (한글, "{case_name}" 명시)
- [ ] (추가 필수 서류 나열)

### 진단비 청구 (암, 뇌졸중, 심근경색 등)
- [ ] 진단서 (조직검사 결과 포함)
- [ ] (추가 필수 서류 나열)

### 후유장해 청구
- [ ] 후유장해 진단서 (장해 등급 명시)
- [ ] (추가 필수 서류 나열)

---

## 4. 손해사정인 현장조사 대처법

### {case_name} 특유의 함정
- (이 질병/상해에서 보험사가 자주 문제 삼는 포인트)

### 서명 주의사항
- ⭕ 서명 가능: 개인정보 동의서, 병원명 명시된 의무기록 열람 위임장
- ❌ 서명 금지: 건강보험공단 조회, 국세청 조회, 의료자문 동의서

### 병원 진료 시 주의사항
- 절대 금지 발언: "예전부터 아팠다", "몇 년 전에도 비슷한 증상이 있었다"
- 권장 표현: "이번 사고/진단 후 처음 증상이 시작되었다"

---

## 5. 고객 안내문 (카카오톡 전송용)

📋 [{case_name}] 보험금 청구 안내

안녕하세요, 고객님.
{case_name} 진단/사고로 보험금 청구를 도와드리겠습니다.

1️⃣ **필수 서류 준비**
- (핵심 서류 3-5개 나열)

2️⃣ **병원 진료 시 주의사항**
- (초진 차트 방어 핵심 포인트)

3️⃣ **보험금 청구 예상 금액**
- 실손보험: (예상 금액 범위)
- 진단비: (해당 시)
- 후유장해: (해당 시)

궁금하신 점 있으시면 언제든 연락 주세요!

---

**작성일**: 2026-03-30  
**카테고리**: {case_type}  
**질병/상해명**: {case_name}
"""
    
    return prompt


# ══════════════════════════════════════════════════════════════════════════════
# 메인 함수
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    RAG 실전 보상 데이터베이스 자동 구축 메인 함수
    """
    
    print("=" * 80)
    print("골드키 AI 마스터 - RAG 실전 보상 데이터베이스 자동 구축기")
    print("=" * 80)
    print()
    
    # Gemini API 키 확인
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 GEMINI_API_KEY를 설정하거나 환경변수로 등록하세요.")
        return
    
    # Gemini API 설정
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    print(f"✅ Gemini 1.5 Pro 모델 초기화 완료")
    print()
    
    # 출력 디렉토리 생성
    output_dir = Path("d:/CascadeProjects/source_docs/보상실무_표준케이스")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ 출력 디렉토리 생성: {output_dir}")
    print()
    
    # 총 케이스 수
    total_cases = len(DISEASES) + len(INJURIES)
    current_case = 0
    
    print(f"📊 총 {total_cases}개 케이스 생성 시작")
    print(f"   - 질병: {len(DISEASES)}개")
    print(f"   - 상해: {len(INJURIES)}개")
    print()
    print("⏱️  예상 소요 시간: 약 {:.0f}분 (케이스당 5초 딜레이)".format(total_cases * 5 / 60))
    print()
    print("=" * 80)
    print()
    
    # ═══ 질병 30개 생성 ═══
    print("🏥 질병 케이스 생성 시작...")
    print()
    
    for i, disease in enumerate(DISEASES, 1):
        current_case += 1
        
        print(f"[{current_case}/{total_cases}] 질병_{i:02d}_{disease} 생성 중...")
        
        try:
            # 프롬프트 생성
            prompt = generate_prompt(disease, "질병")
            
            # Gemini API 호출
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # 파일 저장
            filename = f"질병_{i:02d}_{disease}.md"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"   ✅ 저장 완료: {filename}")
            print()
            
            # API rate limit 방지
            if current_case < total_cases:
                time.sleep(5)
        
        except Exception as e:
            print(f"   ❌ 생성 실패: {e}")
            print()
    
    # ═══ 상해 30개 생성 ═══
    print("🚑 상해 케이스 생성 시작...")
    print()
    
    for i, injury in enumerate(INJURIES, 1):
        current_case += 1
        
        print(f"[{current_case}/{total_cases}] 상해_{i:02d}_{injury} 생성 중...")
        
        try:
            # 프롬프트 생성
            prompt = generate_prompt(injury, "상해")
            
            # Gemini API 호출
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            # 파일 저장
            filename = f"상해_{i:02d}_{injury}.md"
            filepath = output_dir / filename
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            print(f"   ✅ 저장 완료: {filename}")
            print()
            
            # API rate limit 방지
            if current_case < total_cases:
                time.sleep(5)
        
        except Exception as e:
            print(f"   ❌ 생성 실패: {e}")
            print()
    
    # ═══ 완료 ═══
    print("=" * 80)
    print("✅ RAG 실전 보상 데이터베이스 자동 구축 완료!")
    print("=" * 80)
    print()
    print(f"📁 생성된 파일 위치: {output_dir}")
    print(f"📊 생성된 파일 수: {len(list(output_dir.glob('*.md')))}개")
    print()
    print("🚀 다음 단계:")
    print("   1. RAG 임베딩 실행: python run_intelligent_rag.py")
    print("   2. CRM 앱에서 RAG 채팅으로 테스트")
    print()


# ══════════════════════════════════════════════════════════════════════════════
# 실행
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
