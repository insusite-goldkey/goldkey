# Native Credential 통합 가이드

**작성일**: 2026-03-31  
**목적**: 모바일/태블릿 Native Credential 통합 및 Cross-Device Sync 시스템 구축  
**전략**: Device-Adaptive Auth + Cross-Device Sync + UI Feedback

---

## 🎯 시스템 개요

### 핵심 철학
> "모바일과 태블릿의 보안 환경을 'Native Credential'로 완전 통합하라."

### 3대 핵심 기능

#### 1. Device-Adaptive Auth (기기 적응형 인증)
- 기기 유형(Phone/Tablet/Desktop) 자동 감지
- 최우선 보안 수단(지문/Face ID/도형/PIN) 즉시 호출
- 보안 세션 관리 (30분 타임아웃)

#### 2. Cross-Device Sync (기기 간 동기화)
- Supabase Realtime 기반 상태 동기화
- Draft Report, 분석 중인 담보, 고객 정보 자동 저장
- 기기 전환 시 즉시 복원

#### 3. UI Feedback (사용자 피드백)
- 보안 확인 메시지: "지능형 리딩 파트너가 보안을 확인했습니다"
- 복원 메시지: "분석 리포트를 복원합니다"
- 신뢰도 향상

---

## 📦 생성된 모듈

### ① Device-Adaptive Auth 모듈

**파일**: `modules/device_adaptive_auth.py`

**핵심 기능**:
- 기기 유형 자동 감지 (JavaScript 연동)
- Native Credential 요청 및 검증
- 인증 상태 관리 및 타임아웃
- 보안 배지 렌더링

**사용 예시**:
```python
from modules.device_adaptive_auth import render_device_adaptive_auth

# CRM 앱 로그인 화면
if not st.session_state.get("user_id"):
    # 인증 화면 렌더링
    is_authenticated = render_device_adaptive_auth(
        user_id="temp_user",
        on_success_callback=lambda: st.success("로그인 성공!")
    )
    
    if not is_authenticated:
        st.stop()  # 인증 전까지 진행 차단
```

**기기별 인증 수단**:
- **Phone**: 지문 인식 (Fingerprint) 우선
- **Tablet**: Face ID 우선
- **Desktop**: 비밀번호

**JavaScript 기기 감지**:
```javascript
function detectDevice() {
    const width = window.innerWidth;
    const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    
    let deviceType = 'desktop';
    
    if (isTouchDevice) {
        if (width <= 768) {
            deviceType = 'phone';
        } else if (width <= 1024) {
            deviceType = 'tablet';
        }
    }
    
    return deviceType;
}
```

---

### ② Cross-Device Sync 모듈

**파일**: `modules/cross_device_sync.py`

**핵심 기능**:
- 작업 상태 자동 저장 (Draft Report, 분석 진행, 고객 정보)
- Supabase Realtime 동기화
- 기기 전환 시 복원 알림
- 복원 데이터 관리

**사용 예시**:
```python
from modules.cross_device_sync import (
    render_cross_device_sync_notification,
    auto_save_work_state
)

# 1. 로그인 직후 복원 알림
restored_data = render_cross_device_sync_notification(
    user_id=user_id,
    state_type="draft_report",
    supabase_client=supabase
)

if restored_data:
    # 복원된 데이터 사용
    customer_id = restored_data.get("customer_id")
    report_data = restored_data.get("report_data")

# 2. 작업 중 자동 저장
auto_save_work_state(
    user_id=user_id,
    state_type="draft_report",
    state_data={
        "customer_id": customer_id,
        "report_data": current_report
    },
    supabase_client=supabase
)
```

**상태 유형**:
- `draft_report`: 작성 중이던 리포트
- `analysis_in_progress`: 분석 중이던 담보
- `customer_form`: 입력 중이던 고객 정보

---

## 🗄️ Supabase 테이블 스키마

### agent_work_state 테이블

```sql
CREATE TABLE agent_work_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    state_type TEXT NOT NULL,
    state_data JSONB NOT NULL,
    device_id TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, state_type)
);

-- 인덱스
CREATE INDEX idx_agent_work_state_user_id ON agent_work_state(user_id);
CREATE INDEX idx_agent_work_state_state_type ON agent_work_state(state_type);
CREATE INDEX idx_agent_work_state_updated_at ON agent_work_state(updated_at DESC);

-- RLS (Row Level Security)
ALTER TABLE agent_work_state ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own work state"
    ON agent_work_state FOR SELECT
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can insert their own work state"
    ON agent_work_state FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

CREATE POLICY "Users can update their own work state"
    ON agent_work_state FOR UPDATE
    USING (auth.uid()::text = user_id);

CREATE POLICY "Users can delete their own work state"
    ON agent_work_state FOR DELETE
    USING (auth.uid()::text = user_id);
```

---

## 🚀 CRM 앱 통합 방법

### 1. 로그인 화면에 Device-Adaptive Auth 적용

**위치**: `crm_app_impl.py` - 로그인 화면

```python
from modules.device_adaptive_auth import render_device_adaptive_auth

# 기존 로그인 로직 대체
if not st.session_state.get("user_id"):
    # Device-Adaptive Auth 렌더링
    is_authenticated = render_device_adaptive_auth(
        user_id="guest",
        on_success_callback=lambda: handle_login_success()
    )
    
    if not is_authenticated:
        st.stop()
```

### 2. 대시보드에 Cross-Device Sync 적용

**위치**: `crm_app_impl.py` - 대시보드 상단

```python
from modules.cross_device_sync import render_cross_device_sync_notification

# 로그인 직후 복원 알림
if _user_id:
    # Draft Report 복원
    restored_report = render_cross_device_sync_notification(
        user_id=_user_id,
        state_type="draft_report",
        supabase_client=supabase
    )
    
    # 분석 진행 상태 복원
    restored_analysis = render_cross_device_sync_notification(
        user_id=_user_id,
        state_type="analysis_in_progress",
        supabase_client=supabase
    )
```

### 3. 작업 중 자동 저장

**위치**: `blocks/crm_scan_block.py` - 분석 진행 중

```python
from modules.cross_device_sync import auto_save_work_state

# 분석 진행 중 자동 저장 (5초마다)
if analysis_in_progress:
    auto_save_work_state(
        user_id=user_id,
        state_type="analysis_in_progress",
        state_data={
            "customer_id": customer_id,
            "analysis_data": {
                "current_step": "리스크 계산 중",
                "progress": 65,
                "ocr_result": ocr_result
            }
        },
        supabase_client=supabase
    )
```

### 4. 리포트 작성 중 자동 저장

**위치**: `hq_app_impl.py` - 리포트 작성

```python
from modules.cross_device_sync import auto_save_work_state

# Draft Report 자동 저장
if report_draft:
    auto_save_work_state(
        user_id=user_id,
        state_type="draft_report",
        state_data={
            "customer_id": customer_id,
            "report_data": {
                "sections": report_sections,
                "total_risk": total_risk,
                "recommendations": recommendations
            }
        },
        supabase_client=supabase
    )
```

---

## 🎨 UI/UX 가이드라인

### 1. 보안 확인 메시지

**인증 성공 시**:
```
✅ 지능형 리딩 파트너가 보안을 확인했습니다
```

**복원 시**:
```
🔄 지능형 리딩 파트너가 보안을 확인했습니다
   작성 중이던 리포트를 복원합니다
```

### 2. 기기 정보 표시

```
📱 PHONE 기기에서 접속 중
📲 TABLET 기기에서 접속 중
💻 DESKTOP 기기에서 접속 중
```

### 3. 인증 수단별 메시지

- **지문 인식**: "지문 인식을 통해 보안을 확인해주세요"
- **Face ID**: "Face ID를 통해 보안을 확인해주세요"
- **도형 패턴**: "도형 패턴을 입력해주세요"
- **PIN**: "PIN 번호를 입력해주세요"
- **비밀번호**: "비밀번호를 입력해주세요"

### 4. 복원 알림 UI

```
┌─────────────────────────────────────────┐
│   🔄                                    │
│   지능형 리딩 파트너가 보안을 확인했습니다  │
│   작성 중이던 리포트를 복원합니다          │
│                                         │
│   [✅ 복원하기]  [❌ 새로 시작]          │
└─────────────────────────────────────────┘
```

---

## 🔄 작동 시나리오

### 시나리오 1: 모바일에서 리포트 작성 → 태블릿으로 전환

1. **모바일 (Phone)**
   - 지문 인식으로 로그인
   - 고객 분석 리포트 작성 중 (50% 완료)
   - 자동 저장 (5초마다)

2. **태블릿 (Tablet)**
   - Face ID로 로그인
   - 복원 알림 표시: "작성 중이던 리포트를 복원합니다"
   - [✅ 복원하기] 클릭
   - 50% 완료 상태에서 이어서 작성

### 시나리오 2: 태블릿에서 분석 진행 → 데스크톱으로 전환

1. **태블릿 (Tablet)**
   - Face ID로 로그인
   - 증권 스캔 및 분석 진행 중 (OCR 완료, 리스크 계산 중)
   - 자동 저장

2. **데스크톱 (Desktop)**
   - 비밀번호로 로그인
   - 복원 알림 표시: "분석 중이던 담보를 복원합니다"
   - [✅ 복원하기] 클릭
   - OCR 결과 및 리스크 계산 상태 복원

### 시나리오 3: 고객 정보 입력 중 앱 종료 → 재접속

1. **모바일 (Phone) - 첫 번째 세션**
   - 고객 정보 입력 중 (이름, 나이, 업종 입력 완료)
   - 앱 종료 (의도치 않은 종료)

2. **모바일 (Phone) - 두 번째 세션**
   - 지문 인식으로 재로그인
   - 복원 알림 표시: "입력 중이던 고객 정보를 복원합니다"
   - [✅ 복원하기] 클릭
   - 이름, 나이, 업종 자동 입력 상태로 복원

---

## 🧪 테스트 방법

### 1. Device-Adaptive Auth 테스트

```bash
streamlit run modules/device_adaptive_auth.py
```

**테스트 항목**:
- ✅ 기기 유형 감지 (Phone/Tablet/Desktop)
- ✅ 인증 수단 자동 선택
- ✅ 인증 성공/실패 처리
- ✅ 보안 배지 표시
- ✅ 30분 타임아웃

### 2. Cross-Device Sync 테스트

```bash
streamlit run modules/cross_device_sync.py
```

**테스트 항목**:
- ✅ Draft Report 자동 저장
- ✅ 분석 진행 상태 저장
- ✅ 고객 정보 저장
- ✅ 복원 알림 표시
- ✅ 복원 데이터 로드

### 3. 통합 테스트 (CRM 앱)

**테스트 시나리오**:
1. 모바일에서 로그인 → 지문 인식 확인
2. 고객 정보 입력 → 자동 저장 확인
3. 앱 종료 후 재접속 → 복원 알림 확인
4. 태블릿으로 전환 → Face ID 인증 확인
5. 복원 데이터 로드 → 이어서 작업 확인

---

## 📊 기대 효과

### 1. 보안 강화
- ✅ Native Credential 통합으로 보안 수준 향상
- ✅ 기기별 최적 인증 수단 자동 선택
- ✅ 30분 타임아웃으로 세션 보안 유지

### 2. 사용자 경험 향상
- ✅ 기기 전환 시 작업 상태 즉시 복원
- ✅ 입력 피로도 감소 (자동 저장)
- ✅ 신뢰도 향상 (리딩 파트너 메시지)

### 3. 생산성 향상
- ✅ 작업 중단 없이 기기 전환 가능
- ✅ Draft Report 손실 방지
- ✅ 분석 진행 상태 보존

### 4. 브랜드 차별화
- ✅ "지능형 리딩 파트너" Identity 강화
- ✅ 최첨단 보안 시스템 구축
- ✅ Cross-Device 경험 제공

---

## 🎉 결론

**Native Credential 통합 시스템**이 성공적으로 구축되었습니다.

**핵심 성과**:
- ✅ Device-Adaptive Auth (기기 적응형 인증)
- ✅ Cross-Device Sync (기기 간 동기화)
- ✅ UI Feedback (사용자 피드백)

**최종 메시지**:
> "모바일과 태블릿의 보안 환경을 'Native Credential'로 완전 통합했습니다. 지능형 리딩 파트너가 항상 당신의 작업을 보호하고 복원합니다."

**다음 단계**: CRM 앱에 통합 및 실전 배포

---

## 📂 생성된 파일 목록

### 모듈
1. `modules/device_adaptive_auth.py` - 기기 적응형 인증 (425줄)
2. `modules/cross_device_sync.py` - 기기 간 동기화 (434줄)

### 문서
3. `NATIVE_CREDENTIAL_INTEGRATION_GUIDE.md` - 통합 가이드 (본 문서)

### SQL 스키마
4. `agent_work_state` 테이블 스키마 (가이드 내 포함)

---

**작성자**: goldkey_Ai_masters2026 프로젝트 팀  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
