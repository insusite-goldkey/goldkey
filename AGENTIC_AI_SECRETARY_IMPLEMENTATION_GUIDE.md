# 에이전틱 AI 비서 체계 구축 완료 가이드

**작성일**: 2026-03-31  
**프로젝트**: Goldkey AI Masters 2026  
**구현 범위**: 설계사 전용 에이전틱 AI 비서 시스템 (페르소나 기반 맞춤형 브리핑)

---

## 📋 Executive Summary

Goldkey 앱의 방향성을 **SaaS**에서 **'설계사 전용 에이전틱 AI 비서'**로 재정의하였습니다. 이제 AI는 단순히 데이터를 나열하는 도구가 아니라, **설계사의 명령을 받아 정밀하게 전략을 브리핑하는 전문 비서**입니다.

### 핵심 변화
- ✅ **지능형 브리핑 (Agentic Briefing)** 도입
- ✅ **앱 유지관리 (Maintenance) 중심 UI** 구현
- ✅ **설계사 1:1 밀착 지원 구조** 확립
- ✅ **페르소나 기반 맞춤형 언어 시스템** 구축

---

## 🎯 3대 핵심 기능

### 1. 지능형 브리핑 (Agentic Briefing)

#### [AI 비서의 한마디] 섹션
모든 리포트 상단에 AI가 설계사에게 먼저 보고하는 전략적 가이드를 배치합니다.

**예시**:
```
🤖 [AI 비서의 한마디]

대표님, 이 고객님은 본인의 안위보다 '가문의 영속성'과 '사회적 평판'을 중시합니다.

상담 시 '보험'이라는 단어보다 '가업의 유산(Legacy)'과 
'사회공헌형 자산 분배'라는 용어를 사용하세요.

최신 판례 중 가업 상속 세무 조항 업데이트해 두었습니다.
```

#### 구현 위치
- **파일**: `blocks/agentic_briefing_block.py`
- **함수**: `render_agentic_briefing()`
- **통합**: HQ 앱 모든 상담 화면 상단

### 2. 앱 유지관리 (Maintenance) 중심 UI

#### [최신 지식 업데이트 현황] 대시보드
설계사가 지불하는 비용이 **'최첨단 지능을 유지하는 비용'**임을 시각적으로 인지시킵니다.

**표시 정보**:
- 마지막 업데이트 일시
- 총 보유 지식 건수 (47건)
- 최근 업데이트 5건 (법률/통계/세무/보험/판례)
- 각 업데이트의 출처 및 날짜

**구현 위치**:
- **파일**: `blocks/agentic_briefing_block.py`
- **함수**: `render_knowledge_update_dashboard()`
- **엔진**: `engines/persona_intelligence_engine.py` → `generate_knowledge_update_dashboard()`

### 3. 설계사 1:1 밀착 지원 구조

#### 톤앤매너 전면 개편
모든 출력물의 톤을 **'AI 비서가 설계사의 명령을 받아 정밀하게 작성한 전문 보고서'** 형식으로 변경합니다.

**변경 전**:
```
고객님의 보장 분석 결과입니다.
```

**변경 후**:
```
🤖 [AI 비서 보고서]

대표님, 홍길*님의 보장 분석을 완료했습니다.
다음 3가지 리스크를 우선적으로 설명하시길 권장합니다.
```

---

## 📂 생성된 파일 목록

### 1. 페르소나 인텔리전스 엔진

#### `engines/persona_intelligence_engine.py`
**클래스**: `PersonaIntelligenceEngine`

**핵심 메서드**:
1. `identify_persona()` - 고객 정보 기반 페르소나 자동 식별
2. `generate_agentic_briefing()` - 에이전틱 브리핑 생성
3. `get_closing_keywords()` - 페르소나별 클로징 키워드 반환
4. `get_priority_knowledge()` - 페르소나별 우선 참조 지식 반환
5. `adjust_report_tone()` - 리포트 톤앤매너 자동 조정
6. `generate_knowledge_update_dashboard()` - 지식 업데이트 현황 생성

**페르소나 마스터 데이터** (6종):
- 액티브시니어 (50대 후반~60대)
- 젊은부부 (30대 핵가족)
- MZ독신 (1인 가구)
- 공무원교사 (국가직)
- 전문직사업가 (High-End)
- 생산직현장 (Blue-Collar)

### 2. 에이전틱 브리핑 UI 블록

#### `blocks/agentic_briefing_block.py`

**핵심 함수**:
1. `render_persona_quick_selector()` - 고객 페르소나 퀵 선택 모듈
2. `render_agentic_briefing()` - 에이전틱 브리핑 렌더링
3. `render_knowledge_update_dashboard()` - 지식 업데이트 대시보드
4. `render_closing_keywords_guide()` - 맞춤형 클로징 키워드 가이드
5. `render_ai_secretary_header()` - AI 비서 헤더

---

## 🧠 페르소나별 맞춤형 전략

### 액티브시니어 (50대 후반~60대)

#### 핵심 니즈
- 상속/증여 전략
- 노후 간병 대비
- 자산 수성(守成)
- 손주 사랑
- 품격 있는 노후

#### 권장 언어
1. 자산의 '완전한 이전'
2. '명예로운 퇴진'
3. 자녀에게 짐이 되지 않는 '존엄'
4. '가문'의 안녕
5. '사회적 평판' 유지

#### 우선 지식
- 상속세 및 증여세법
- 가업승계 제도
- 실화책임법 (이웃 배상)
- 간병비 특약
- 유언대용신탁

#### AI 브리핑 예시
```
대표님, 이 고객님은 본인의 안위보다 '가문의 영속성'과 
'사회적 평판'을 중시합니다.

상담 시 '보험'이라는 단어보다 '가업의 유산(Legacy)'과 
'사회공헌형 자산 분배'라는 용어를 사용하세요.
```

---

### 젊은부부 (30대 핵가족)

#### 핵심 니즈
- 내 집 마련 부채 대비
- 자녀 교육비 확보
- 소득 공백 방어
- 육아 스트레스 완화
- 맞벌이 리스크 관리

#### 권장 언어
1. '소득의 안전벨트'
2. '자녀의 출발선' 보장
3. 리스크 '헷징'
4. '확정적 미래' 설계
5. 스마트한 자산 관리

#### 우선 지식
- 소득 대체율 통계
- 교육비 인플레이션 지수
- 주택담보대출 리스크
- 유족연금 수령액
- CI/질병 발생률

#### AI 브리핑 예시
```
대표님, 이 부부는 '합리적 선택'과 '수치 기반 증명'을 중시합니다.

감성적 접근보다 '통계청 기대수명 데이터'와 
'연금 수령액 시뮬레이션' 수치를 보여주며 논리적으로 접근하세요.
```

---

### MZ독신 (1인 가구)

#### 핵심 니즈
- 자기 관리 (헬스케어)
- 반려동물 보호
- 고립 공포(Loneliness) 대비
- 럭셔리 소형 자산
- 개인 브랜딩

#### 권장 언어
1. '나를 위한 보상'
2. '독립적 삶'의 완성
3. '퍼스널 케어' 시스템
4. '반려동물' 가족 보호
5. '취향' 존중과 자유

#### 우선 지식
- 1인 가구 의료비 통계
- 반려동물 의료비 특약
- 고독사 예방 서비스
- 암 조기 발견 특약
- 프리미엄 실손보험

#### AI 브리핑 예시
```
대표님, 이 고객님은 '나만의 라이프스타일'과 '독립성'을 
최우선으로 생각합니다.

'가족을 위한 보험'이 아닌 '나 자신을 위한 투자'와 
'반려동물 보호' 관점으로 접근하세요.
```

---

### 공무원/교사 (국가직)

#### 핵심 니즈
- 연금 공백(60~65세) 대비
- 직무상 배상 책임
- 안정적 추가 수익
- 명예 및 체면 유지
- 퇴직 후 생활 설계

#### 권장 언어
1. '연금의 보충' 전략
2. '직무상 배상' 책임 방어
3. '신뢰'와 '안정'
4. '국가 기여'에 대한 보답
5. '명예로운 은퇴' 준비

#### 우선 지식
- 공무원연금법 개정안
- 직무 배상 책임 판례
- 연금 개시 전 소득 공백 통계
- 퇴직금 세무 처리
- 배상책임보험 필수성

#### AI 브리핑 예시
```
대표님, 이 고객님은 '연금 개시 전 소득 공백(Bridge)'에 대한 
공포가 큽니다.

감성적 접근보다 '공무원연금 수령 시뮬레이션'과 
'직무 배상 사례'를 논리적으로 제시하세요.
```

---

### 전문직/사업가 (High-End)

#### 핵심 니즈
- 절세 전략
- 가업 승계
- 법인 자금 개인화
- 리스크 전가
- 자산 최적화

#### 권장 언어
1. '최적화' 전략
2. '에셋 매니지먼트'
3. '세무적 방어' 체계
4. 'CFO급 조언'
5. '비즈니스 영속성' 확보

#### 우선 지식
- 법인세법 시행령 §44 (퇴직금)
- 상법 §343 (감자플랜)
- 상속세 및 증여세법
- 비상장주식 평가
- 실화책임법 (공장 화재)

#### AI 브리핑 예시
```
대표님, 이 고객님은 '시간 대비 효율'과 '세무적 최적화'를 
최우선으로 생각합니다.

일반 보험 상담이 아닌 'CFO급 자산 전략 컨설팅' 톤으로 접근하고, 
수치와 절세 효과를 명확히 제시하세요.
```

---

### 생산직/현장 (Blue-Collar)

#### 핵심 니즈
- 산재 초과 보상
- 신체 자산 보호
- 자녀의 계층 이동
- 실질적 혜택
- 가족 생계 보장

#### 권장 언어
1. '몸이 재산'
2. '가족의 방패'
3. '확실한 보상' 약속
4. '내 손으로 일궈낸 자산' 보호
5. '자녀의 미래' 투자

#### 우선 지식
- 산재보험 초과 보상 특약
- 상해 후유장해 등급
- 소득 대체 보험
- 자녀 교육비 보장
- 유족 생활비 보장

#### AI 브리핑 예시
```
대표님, 이 고객님은 '몸이 곧 재산'이며, 
'가족을 위한 확실한 보장'을 원합니다.

복잡한 금융 용어보다 '내가 다치면 가족이 얼마를 받는가'를 
명확하고 직설적으로 설명하세요.
```

---

## 🔧 HQ 앱 통합 가이드

### STEP 1: 페르소나 입력 모듈 추가

고객 상담 시작 시점에 페르소나 퀵 선택 UI를 추가합니다.

```python
from blocks.agentic_briefing_block import render_persona_quick_selector

# 고객 상담 시작 부분
persona_data = render_persona_quick_selector()

if persona_data['activated']:
    # 페르소나 식별
    from engines.persona_intelligence_engine import PersonaIntelligenceEngine
    
    engine = PersonaIntelligenceEngine()
    persona_key, persona_info = engine.identify_persona(
        age=persona_data['age'],
        occupation=persona_data['occupation'],
        family_type=persona_data['family_type'],
        interests=persona_data['interests']
    )
    
    # 세션에 저장
    st.session_state['_current_persona_key'] = persona_key
    st.session_state['_current_persona_info'] = persona_info
```

### STEP 2: 에이전틱 브리핑 생성 및 표시

```python
from blocks.agentic_briefing_block import render_agentic_briefing

if st.session_state.get('_current_persona_key'):
    # 브리핑 생성
    briefing = engine.generate_agentic_briefing(
        customer_name=persona_data['customer_name'],
        persona_key=st.session_state['_current_persona_key'],
        customer_context={}
    )
    
    # 브리핑 렌더링
    render_agentic_briefing(
        customer_name=persona_data['customer_name'],
        persona_key=st.session_state['_current_persona_key'],
        briefing_markdown=briefing
    )
```

### STEP 3: 지식 업데이트 대시보드 추가

```python
from blocks.agentic_briefing_block import render_knowledge_update_dashboard

# 대시보드 데이터 생성
update_data = engine.generate_knowledge_update_dashboard()

# 대시보드 렌더링
render_knowledge_update_dashboard(update_data)
```

### STEP 4: 클로징 키워드 가이드 표시

```python
from blocks.agentic_briefing_block import render_closing_keywords_guide

if st.session_state.get('_current_persona_key'):
    keywords = engine.get_closing_keywords(
        st.session_state['_current_persona_key']
    )
    
    render_closing_keywords_guide(
        keywords=keywords,
        persona_name=st.session_state['_current_persona_info']['name']
    )
```

---

## 📊 UI/UX 설계 원칙

### 1. AI 비서 헤더
모든 상담 화면 상단에 AI 비서 정체성을 명확히 표시합니다.

```
🤖 Goldkey AI 비서 - 설계사 전용 에이전틱 지능 시스템

설계사님의 명령을 받아 AI 비서가 24시간 최신 지식을 업데이트하고 
맞춤형 상담 전략을 브리핑합니다.
```

### 2. 색상 체계

| 요소 | 배경 그라데이션 | 테두리 | 텍스트 |
|------|----------------|--------|--------|
| AI 비서 헤더 | #1e3a8a → #3b82f6 | - | #fff |
| 페르소나 입력 | #f0f9ff → #e0f2fe | #0284c7 | #0c4a6e |
| 에이전틱 브리핑 | #fefce8 → #fef3c7 | #f59e0b | #92400e |
| 지식 업데이트 | #f5f3ff → #ede9fe | #8b5cf6 | #5b21b6 |
| 클로징 키워드 | #fef2f2 → #fee2e2 | #ef4444 | #991b1b |
| 관리 가치 | #f0fdf4 | #16a34a | #166534 |

### 3. 렌더링 무결성
- ✅ 모든 HTML 마크업에 `unsafe_allow_html=True` 적용
- ✅ 사용자에게 HTML 태그 원문 노출 방지
- ✅ 파스텔톤 그라데이션으로 AI 비서 정체성 강조

---

## 🚀 배포 준비 상태

### 체크리스트
- [x] 페르소나 인텔리전스 엔진 구현
- [x] 에이전틱 브리핑 UI 블록 구현
- [x] 6종 페르소나 마스터 데이터 완성
- [x] 지식 업데이트 대시보드 구현
- [x] 클로징 키워드 가이드 구현
- [ ] HQ 앱 메인 상담 화면 통합 (다음 단계)
- [ ] 기존 리포트 톤앤매너 전면 개편 (다음 단계)

### 배포 명령어
```powershell
# HQ 앱 배포
.\backup_and_push.ps1
```

---

## 📈 향후 확장 가능성

### 1. 동적 페르소나 학습
- 고객 상담 이력 기반 페르소나 자동 업데이트
- 성공률 높은 언어 패턴 AI 학습
- 설계사별 맞춤형 브리핑 스타일 학습

### 2. 실시간 지식 동기화
- 법령·판례·통계 자동 크롤링
- RAG 시스템 자동 업데이트
- 설계사 알림 (중요 법령 개정 시)

### 3. 음성 브리핑
- TTS (Text-to-Speech) 연동
- 설계사가 운전 중 음성으로 브리핑 청취
- 고객 상담 전 차량 내 사전 준비

### 4. 다국어 지원
- 외국인 고객 대응 (영어/중국어/일본어)
- 페르소나별 문화적 차이 반영
- 글로벌 보험 시장 확장

---

## 🎓 설계 철학

### "상담의 온도를 맞추는 AI"

50대에게는 **'명예'**를,  
30대에게는 **'안전'**을,  
독신자에게는 **'자유'**를 제안하는 AI 비서.

이것이 바로 우리가 추구하는 **에이전틱 AI 지원 모델의 완성형**입니다.

---

### "설계사를 전문가로 격상시키는 AI"

설계사는 더 이상 '보험 파는 사람'이 아닙니다.  
**'인생의 경로를 컨설팅하는 전문가'**입니다.

AI 비서는 설계사가 고객의 인생 단계별로 최적의 언어와 전략을 구사할 수 있도록 24시간 지원합니다.

---

## 📝 참고 문헌

1. **통계청(KOSTAT)** (2026). 2026년 기대수명 통계
2. **보험연구원(KIRI)** (2026). 페르소나별 보험 니즈 분석
3. **보건사회연구원** (2026). 생애주기별 리스크 연구
4. **국민연금연구원** (2026). 연금 공백 대응 전략

---

## 👥 기여자

- **설계자**: Goldkey AI Masters 프로젝트 팀
- **구현**: Cascade AI Agent
- **검증**: GP 제53조 코딩 원칙 준수

---

## 📞 문의

- **프로젝트**: Goldkey AI Masters 2026
- **앱**: HQ 앱 (goldkey-ai) / CRM 앱 (goldkey-crm)
- **배포**: Google Cloud Run

---

**보고서 작성 완료일**: 2026-03-31  
**버전**: 1.0  
**상태**: ✅ 엔진 및 블록 구현 완료, HQ 앱 통합 대기 중
