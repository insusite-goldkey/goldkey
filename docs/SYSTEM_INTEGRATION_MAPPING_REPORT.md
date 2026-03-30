# ══════════════════════════════════════════════════════════════════════════════
# GP 시스템 통합 보고서 - 12단계 마스터플랜 전면 매핑 현황
# Goldkey AI Masters 2026 - 옵션 B 채택 완료
# 2026-03-30 작성
# ══════════════════════════════════════════════════════════════════════════════

## 🎯 **옵션 B 채택 완료 보고**

**"권한 제어 시스템(GP) 구축 및 12단계 STEP 전면 적용 완료"**

---

## 📊 **STEP 1~12 권한/코인 차감 매핑 테이블**

### **전체 구조 요약**

| STEP | 기능명 | 등급 | 코인 | 배지 | 파일 위치 |
|------|--------|------|------|------|-----------|
| 1 | 고객상담 (상담신청) | BASIC | 0🪙 | [기본사용] | `modules/consultation_manager.py` |
| 2 | 개인정보 동의 및 인증 | BASIC | 0🪙 | [기본사용] | `modules/consent_manager.py` |
| 3 | 증권 및 의무기록 스캔 | BASIC | 1🪙 | [기본사용] | `modules/scan_engine.py` |
| 4 | AI 트리니티 계산법 | BASIC | 1🪙 | [기본사용] | `modules/trinity_calculator.py` |
| 5 | KB 평균 가입금액 비교 | BASIC | 1🪙 | [기본사용] | `modules/kb_standard_analyzer.py` |
| 6 | 통합 보장 공백 진단 | BASIC | 1🪙 | [기본사용] | `modules/gap_analyzer.py` |
| 7 | 에이젠틱 AI 전략 수립 | **PRO** | **3🪙** | [⭐PRO플랜] | `modules/ai_strategy_engine.py` |
| 8 | AI 감성 제안 및 작문 | **PRO** | **3🪙** | [⭐PRO플랜] | `modules/ai_proposal_writer.py` |
| 9 | 1:1 맞춤 제안서 생성 | **PRO** | **3🪙** | [⭐PRO플랜] | `modules/proposal_generator.py` |
| 10 | 청약 진행 및 계약 등록 | BASIC | 1🪙 | [기본사용] | `modules/contract_manager.py` |
| 11 | 지능형 계약 관리 | **HYBRID** | 0~3🪙 | [하이브리드] | `modules/calendar_ai_helper.py` |
| 12 | 리워드 기반 소개 확보 | **PRO** | **3🪙** | [⭐PRO플랜] | `modules/referral_system.py` |

---

## 🏗️ **권한 제어 엔진 구축 현황**

### **파일:** `d:\CascadeProjects\modules\access_control.py`

### **핵심 구성 요소**

#### **§1. STEP 권한 매핑 테이블**

```python
STEP_ACCESS_MAP: Dict[int, Dict[str, Any]] = {
    1: {
        "name": "고객상담 (상담신청)",
        "tier": "basic",
        "coins": 0,
        "badge": "[기본사용]",
        "badge_color": "#10b981",
        "description": "기본 정보 입력",
    },
    # ... (STEP 2~12 생략)
}
```

**특징:**
- 12개 STEP 전체 매핑 완료
- 등급(tier): `basic`, `pro`, `hybrid`
- 코인 차감량(coins): 0~3🪙
- UI 배지(badge): `[기본사용]`, `[⭐PRO플랜]`, `[하이브리드]`
- 배지 색상(badge_color): 그린(#10b981), 골드(#f59e0b), 퍼플(#8b5cf6)

---

#### **§2. 사용자 등급 확인**

```python
def get_user_tier(user_id: str) -> Literal["basic", "pro"]:
    """
    사용자 등급 확인.
    
    프로 조건:
    - subscription_status == "active" (활성 구독)
    - current_credits >= 150 (150코인 이상 보유)
    """
```

**로직:**
1. Supabase `gk_members` 테이블 조회
2. `subscription_status` 또는 `current_credits` 확인
3. 프로 조건 충족 시 `"pro"` 반환, 아니면 `"basic"` 반환

---

#### **§3. 권한 검증**

```python
def check_access(
    user_id: str, 
    step_number: int, 
    report_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    STEP 권한 검증.
    
    Returns:
        {
            "allowed": bool,
            "tier": str,
            "step_info": dict,
            "user_tier": str,
            "upgrade_required": bool,
            "legacy_access": bool
        }
    """
```

**검증 로직:**
1. **하이브리드 STEP (11)**: 항상 허용 (내부에서 기능별 제어)
2. **베이직 STEP (1~6, 10)**: 모든 사용자 허용
3. **프로 STEP (7~9, 12)**: 
   - 프로 등급 → 허용
   - 베이직 등급 + 과거 PRO 리포트 → 0코인 무료 조회 허용
   - 베이직 등급 → 차단 (`upgrade_required: True`)

---

#### **§4. UI 배지 렌더링**

```python
def render_step_badge(step_number: int, inline: bool = True) -> str:
    """
    STEP 배지 HTML 생성.
    
    Example:
        <span style='background:#10b981;color:#fff;padding:3px 10px;
                     border-radius:6px;font-size:0.75rem;font-weight:700;'>
        [기본사용]
        </span>
    """
```

**사용 예시:**
```python
from modules.access_control import render_step_title

st.markdown(
    render_step_title(step_number=7, show_badge=True),
    unsafe_allow_html=True
)
# 출력: "STEP 7. 에이젠틱 AI 전략 수립 [⭐PRO플랜]"
```

---

#### **§5. 업그레이드 팝업 (3회 클릭 넛지)**

```python
def track_pro_click(user_id: str, step_number: int) -> int:
    """프로 기능 클릭 추적 (세션 상태 저장)"""

def render_upgrade_popup(click_count: int = 0, feature_name: str = "프로 전용 기능"):
    """
    3회 클릭 시 특가 팝업 렌더링.
    
    멘트:
    "🎁 오늘만 긴급 혜택: PRO플랜 특가 이벤트
    지금 PRO플랜 전환 시 50코인 즉시 추가 증정.
    전문가용 AI 점검 기능 바로 활성화됩니다."
    """
```

**로직:**
1. 베이직 사용자가 프로 기능 클릭 시 `track_pro_click()` 호출
2. 클릭 횟수 누적 (세션 상태 저장)
3. 3회 클릭 시 특가 팝업 자동 표시
4. 1~2회 클릭 시 일반 업그레이드 안내 + 남은 클릭 횟수 표시

---

#### **§6. STEP 11 하이브리드 마케팅 넛지**

```python
def render_step11_marketing_nudge(customer_name: str = "고객"):
    """
    STEP 11 하이브리드 마케팅 넛지.
    
    멘트:
    "🚀 PRO 전용: AI 상담 점검 시스템
    AI가 [고객명]님의 상담 이력을 정밀 점검하여,
    현재 놓치고 있는 보장 공백과 최적의 상담 포인트를 제안합니다.
    💡 전문가다운 완벽한 상담을 준비하세요!"
    """
```

**적용 시나리오:**
- 베이직 사용자가 달력 일정 클릭 시
- 일정 정보만 표시 (0🪙)
- 하단에 PRO 전용 AI 점검 마케팅 넛지 표시
- 프로 사용자는 AI 점검 자동 실행 (3🪙 차감)

---

## 🎨 **UI 배지 디자인 가이드**

### **배지 색상 체계**

| 등급 | 배지 텍스트 | 배경색 | 용도 |
|------|------------|--------|------|
| BASIC | `[기본사용]` | `#10b981` (그린) | STEP 1~6, 10 |
| PRO | `[⭐PRO플랜]` | `#f59e0b` (골드) | STEP 7~9, 12 |
| HYBRID | `[하이브리드]` | `#8b5cf6` (퍼플) | STEP 11 |

### **반응형 타이포그래피**

```css
/* 데스크톱 (>1024px) */
font-size: 0.75rem;
padding: 3px 10px;
margin-left: 6px;

/* 모바일 (<768px) */
font-size: 0.65rem;
padding: 2px 8px;
margin-left: 4px;
white-space: nowrap;  /* 배지 겹침 방지 */
```

---

## 📋 **STEP별 상세 매핑**

### **STEP 1~6: 베이직 플랜 (실무/관리 위주)**

#### **STEP 1. 고객상담 (상담신청)**
- **등급:** BASIC
- **코인:** 0🪙
- **배지:** [기본사용]
- **설명:** 기본 정보 입력 (이름, 연락처, 직업 등)
- **파일:** `modules/consultation_manager.py`
- **셀프 힐링:** 입력 오류 자동 복구

---

#### **STEP 2. 개인정보 동의 및 인증**
- **등급:** BASIC
- **코인:** 0🪙
- **배지:** [기본사용]
- **설명:** 약관 동의 + 본인 인증 (전화번호 SHA-256 해싱)
- **파일:** `modules/consent_manager.py`
- **셀프 힐링:** 동의 상태 자동 복구

---

#### **STEP 3. 증권 및 의무기록 스캔**
- **등급:** BASIC
- **코인:** 1🪙
- **배지:** [기본사용]
- **설명:** OCR 데이터 추출 (보험증권, 진단서, 처방전)
- **파일:** `modules/scan_engine.py`
- **4자 연동:** GCS + Supabase + Cloud Run + HQ 사령부

---

#### **STEP 4. AI 트리니티 계산법**
- **등급:** BASIC
- **코인:** 1🪙
- **배지:** [기본사용]
- **설명:** 건보료 역산 분석 (소득 추정)
- **파일:** `modules/trinity_calculator.py`
- **보호 대상:** 트리니티 수식 절대 수정 금지

---

#### **STEP 5. KB 평균 가입금액 비교**
- **등급:** BASIC
- **코인:** 1🪙
- **배지:** [기본사용]
- **설명:** 통계 기반 보장 분석 (KB 7대 스탠다드)
- **파일:** `modules/kb_standard_analyzer.py`
- **보호 대상:** KB 분석 로직 절대 수정 금지

---

#### **STEP 6. 통합 보장 공백 진단**
- **등급:** BASIC
- **코인:** 1🪙
- **배지:** [기본사용]
- **설명:** 분석 결과 리포트 (3단 일람표)
- **파일:** `modules/gap_analyzer.py`
- **출력:** PDF/이미지 다운로드 가능

---

### **STEP 7~9: 프로 플랜 (고부하 AI 지능 위주)**

#### **STEP 7. 에이젠틱 AI 전략 수립**
- **등급:** PRO
- **코인:** 3🪙
- **배지:** [⭐PRO플랜]
- **설명:** 고부하 AI 전략 연산 (Cloud Run 토큰 소모)
- **파일:** `modules/ai_strategy_engine.py`
- **권한 검증:** `check_access(user_id, step_number=7)`

---

#### **STEP 8. AI 감성 제안 및 작문**
- **등급:** PRO
- **코인:** 3🪙
- **배지:** [⭐PRO플랜]
- **설명:** AI 페르소나 작문 (감성 터치 제안서)
- **파일:** `modules/ai_proposal_writer.py`
- **권한 검증:** `check_access(user_id, step_number=8)`

---

#### **STEP 9. 1:1 맞춤 제안서 생성**
- **등급:** PRO
- **코인:** 3🪙
- **배지:** [⭐PRO플랜]
- **설명:** 리포트 정밀 렌더링 (PDF 생성)
- **파일:** `modules/proposal_generator.py`
- **권한 검증:** `check_access(user_id, step_number=9)`

---

### **STEP 10: 베이직 플랜 (계약 등록)**

#### **STEP 10. 청약 진행 및 계약 등록**
- **등급:** BASIC
- **코인:** 1🪙
- **배지:** [기본사용]
- **설명:** 데이터 요새(DB) 저장 (people, policies, policy_roles)
- **파일:** `modules/contract_manager.py`
- **CRM 연동:** 4대 테이블 설계 원칙 준수

---

### **STEP 11: 하이브리드 (달력 + AI 점검)**

#### **STEP 11. 지능형 계약 관리**
- **등급:** HYBRID
- **코인:** 0~3🪙
- **배지:** [하이브리드]
- **설명:**
  - **베이직:** 스마트 스케줄러 (달력 뷰) - 0🪙
  - **프로:** AI 전략 브리핑 + 맞춤 작문 - 3🪙
- **파일:** `modules/calendar_ai_helper.py`
- **마케팅 넛지:** `render_step11_marketing_nudge(customer_name)`

**로직:**
```python
access = check_access(user_id, step_number=11)

if access["user_tier"] == "pro":
    # AI 점검 실행 (3🪙 차감)
    run_ai_consultation_audit(customer_name)
else:
    # 달력만 표시 (0🪙)
    render_calendar_view()
    # 마케팅 넛지 표시
    render_step11_marketing_nudge(customer_name)
```

---

### **STEP 12: 프로 플랜 (리워드 시스템)**

#### **STEP 12. 리워드 기반 소개 확보**
- **등급:** PRO
- **코인:** 3🪙
- **배지:** [⭐PRO플랜]
- **설명:** 리워드 시스템 운영 (동료 소개 시 100🪙 지급)
- **파일:** `modules/referral_system.py`
- **권한 검증:** `check_access(user_id, step_number=12)`

---

## 🔧 **셀프 힐링 (자동 복구) 로직 현황**

### **적용 범위**

| STEP | 셀프 힐링 대상 | 복구 로직 |
|------|---------------|----------|
| 1 | 고객 정보 입력 오류 | 세션 상태 자동 복구 |
| 2 | 약관 동의 상태 | 동의 플래그 자동 복원 |
| 3 | OCR 스캔 실패 | 재시도 + 수동 입력 폴백 |
| 4 | 트리니티 계산 오류 | 기본값 적용 + 경고 표시 |
| 5 | KB 데이터 조회 실패 | 캐시 데이터 사용 |
| 6 | 리포트 생성 실패 | 임시 저장 복구 |
| 7~9 | AI 연산 타임아웃 | 재시도 + 부분 결과 표시 |
| 10 | DB 저장 실패 | 트랜잭션 롤백 + 재시도 |
| 11 | 달력 동기화 실패 | 로컬 캐시 사용 |
| 12 | 리워드 지급 실패 | 큐 시스템 재처리 |

### **구현 예시 (STEP 3)**

```python
def scan_document(file_path: str) -> Dict[str, Any]:
    try:
        # OCR 실행
        result = ocr_engine.extract(file_path)
        return {"success": True, "data": result}
    except OCRTimeoutError:
        # 재시도
        result = ocr_engine.extract(file_path, timeout=60)
        return {"success": True, "data": result}
    except OCRFailedError:
        # 수동 입력 폴백
        st.warning("⚠️ OCR 실패. 수동 입력으로 전환합니다.")
        return {"success": False, "fallback": "manual_input"}
```

---

## 📊 **제로-터치 로그 추적 시스템**

### **로그 레벨**

| 레벨 | 용도 | 저장 위치 |
|------|------|-----------|
| DEBUG | 개발 디버깅 | 로컬 콘솔 |
| INFO | 일반 작업 로그 | Supabase `gk_logs` |
| WARNING | 경고 (셀프 힐링 발동) | Supabase `gk_logs` |
| ERROR | 에러 (복구 실패) | Supabase `gk_logs` + Sentry |
| CRITICAL | 치명적 오류 | Supabase + Sentry + 이메일 알림 |

### **로그 구조**

```python
{
    "timestamp": "2026-03-30T09:54:00Z",
    "user_id": "uuid-1234",
    "step_number": 7,
    "action": "AI_STRATEGY_EXECUTION",
    "status": "success",
    "coins_deducted": 3,
    "execution_time_ms": 2340,
    "error": null
}
```

### **구현 예시**

```python
from modules.logger import log_action

def execute_ai_strategy(user_id: str, customer_data: dict):
    start_time = time.time()
    
    try:
        # AI 전략 실행
        result = ai_engine.generate_strategy(customer_data)
        
        # 성공 로그
        log_action(
            user_id=user_id,
            step_number=7,
            action="AI_STRATEGY_EXECUTION",
            status="success",
            coins_deducted=3,
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
        
        return result
    
    except Exception as e:
        # 에러 로그
        log_action(
            user_id=user_id,
            step_number=7,
            action="AI_STRATEGY_EXECUTION",
            status="error",
            error=str(e),
            execution_time_ms=int((time.time() - start_time) * 1000)
        )
        raise
```

---

## 🚀 **메인 화면 12단계 이정표 부착 현황**

### **HQ 앱 메인 화면**

**파일:** `d:\CascadeProjects\hq_app_impl.py`

**구조:**
```python
from modules.access_control import render_step_title, check_access

# STEP 1~12 버튼 렌더링
for step_num in range(1, 13):
    access = check_access(user_id, step_number=step_num)
    
    # 제목 + 배지
    title_html = render_step_title(step_num, show_badge=True)
    st.markdown(title_html, unsafe_allow_html=True)
    
    # 권한 확인
    if not access["allowed"]:
        st.warning(f"🔒 {access['step_info']['name']}은 PRO플랜 전용입니다.")
        
        # 3회 클릭 넛지
        click_count = track_pro_click(user_id, step_num)
        render_upgrade_popup(click_count, access['step_info']['name'])
    else:
        # 기능 실행
        execute_step(step_num, user_id)
```

**출력 예시:**
```
STEP 1. 고객상담 (상담신청) [기본사용]
STEP 2. 개인정보 동의 및 인증 [기본사용]
STEP 3. 증권 및 의무기록 스캔 [기본사용]
STEP 4. AI 트리니티 계산법 [기본사용]
STEP 5. KB 평균 가입금액 비교 [기본사용]
STEP 6. 통합 보장 공백 진단 [기본사용]
STEP 7. 에이젠틱 AI 전략 수립 [⭐PRO플랜]
STEP 8. AI 감성 제안 및 작문 [⭐PRO플랜]
STEP 9. 1:1 맞춤 제안서 생성 [⭐PRO플랜]
STEP 10. 청약 진행 및 계약 등록 [기본사용]
STEP 11. 지능형 계약 관리 [하이브리드]
STEP 12. 리워드 기반 소개 확보 [⭐PRO플랜]
```

---

## 📄 **구현 파일 목록**

| 파일 | 유형 | 내용 |
|------|------|------|
| `modules/access_control.py` | 핵심 | 권한 제어 엔진 (511줄) |
| `modules/credit_ui.py` | UI | 하드 락 화면 + 코인 충전 |
| `modules/subscription_manager.py` | 로직 | 구독 관리 + 다운그레이드 |
| `modules/downgrade_ui.py` | UI | 다운그레이드 예약 UI |
| `modules/consultation_manager.py` | STEP 1 | 고객상담 |
| `modules/consent_manager.py` | STEP 2 | 개인정보 동의 |
| `modules/scan_engine.py` | STEP 3 | 증권 스캔 |
| `modules/trinity_calculator.py` | STEP 4 | 트리니티 계산 |
| `modules/kb_standard_analyzer.py` | STEP 5 | KB 분석 |
| `modules/gap_analyzer.py` | STEP 6 | 보장 공백 진단 |
| `modules/ai_strategy_engine.py` | STEP 7 | AI 전략 수립 |
| `modules/ai_proposal_writer.py` | STEP 8 | AI 작문 |
| `modules/proposal_generator.py` | STEP 9 | 제안서 생성 |
| `modules/contract_manager.py` | STEP 10 | 계약 등록 |
| `modules/calendar_ai_helper.py` | STEP 11 | 달력 + AI 점검 |
| `modules/referral_system.py` | STEP 12 | 리워드 시스템 |

---

## 🏆 **핵심 성과**

### ✅ **완료된 작업**

1. ✅ **권한 제어 엔진 구축** (`modules/access_control.py`)
   - STEP 1~12 권한 매핑 테이블 완성
   - `check_access()` 함수 구현
   - `get_user_tier()` 함수 구현

2. ✅ **UI 배지 및 명찰 부착**
   - `render_step_badge()` 함수 구현
   - `render_step_title()` 함수 구현
   - 반응형 타이포그래피 적용

3. ✅ **3회 클릭 넛지 + 특가 팝업**
   - `track_pro_click()` 함수 구현
   - `render_upgrade_popup()` 함수 구현
   - 조사 생략형 특가 멘트 적용

4. ✅ **STEP 11 하이브리드 로직**
   - `render_step11_marketing_nudge()` 함수 구현
   - 베이직: 달력 뷰 (0🪙)
   - 프로: AI 점검 (3🪙)

5. ✅ **셀프 힐링 로직**
   - STEP 1~12 전체 적용
   - 자동 복구 + 폴백 메커니즘

6. ✅ **제로-터치 로그 추적**
   - Supabase `gk_logs` 테이블 연동
   - 5단계 로그 레벨 (DEBUG~CRITICAL)

---

## 📊 **시스템 아키텍처 다이어그램**

```
┌─────────────────────────────────────────────────────────────┐
│                    Goldkey AI Masters 2026                  │
│                     12단계 마스터플랜                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              권한 제어 엔진 (access_control.py)              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ STEP_ACCESS_MAP (1~12 매핑 테이블)                  │   │
│  │ - tier: basic / pro / hybrid                        │   │
│  │ - coins: 0~3🪙                                      │   │
│  │ - badge: [기본사용] / [⭐PRO플랜] / [하이브리드]     │   │
│  └─────────────────────────────────────────────────────┘   │
│                              │                              │
│              ┌───────────────┼───────────────┐              │
│              ▼               ▼               ▼              │
│      ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│      │  BASIC   │    │   PRO    │    │ HYBRID   │          │
│      │ STEP 1~6 │    │ STEP 7~9 │    │ STEP 11  │          │
│      │ STEP 10  │    │ STEP 12  │    │          │          │
│      └──────────┘    └──────────┘    └──────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    UI 렌더링 레이어                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ render_step_badge() - 배지 HTML 생성                │   │
│  │ render_step_title() - 제목 + 배지                   │   │
│  │ render_upgrade_popup() - 3회 클릭 넛지              │   │
│  │ render_step11_marketing_nudge() - STEP 11 마케팅    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   데이터 레이어                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Supabase (gk_members, gk_logs, gk_credit_history)  │   │
│  │ GCS (encrypted_profiles, scan_results)              │   │
│  │ Session State (세션 상태 관리)                       │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 **GP 철학 반영 현황**

### **"서버 비용이 적게 드는 실무 관리는 베이직, 고부하 AI 연산은 프로"**

| 구분 | STEP | 서버 비용 | 등급 |
|------|------|-----------|------|
| 실무/관리 | 1~6, 10 | 낮음 (DB 조회, 간단한 계산) | BASIC |
| 고부하 AI | 7~9, 12 | 높음 (Cloud Run 토큰 소모) | PRO |
| 하이브리드 | 11 | 조건부 (베이직: 낮음, 프로: 높음) | HYBRID |

### **코인 차감 정책**

- **0🪙**: 무료 기능 (STEP 1, 2)
- **1🪙**: 저비용 기능 (STEP 3~6, 10)
- **3🪙**: 고비용 AI 기능 (STEP 7~9, 12)

### **마케팅 전략**

1. **3회 클릭 넛지**: 베이직 사용자가 프로 기능을 3번 클릭하면 특가 팝업
2. **STEP 11 하이브리드**: 달력 무료 제공 → AI 점검 마케팅 넛지
3. **과거 데이터 보존**: PRO → BASIC 다운그레이드 후에도 과거 리포트 0코인 조회

---

## 📝 **보고서 작성자**
- **작성일:** 2026-03-30
- **작성자:** Windsurf AI (Cascade)
- **검토자:** 설계자 (이세윤)
- **버전:** v1.0

---

**"옵션 B 채택 완료. 권한 제어 시스템(GP) 구축 및 12단계 STEP 전면 적용이 완료되었습니다. 설계자의 GP 철학이 코드 레벨에서 강제되도록 구축되었습니다."** ✅
