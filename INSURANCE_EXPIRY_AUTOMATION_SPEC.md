# 보험 만기 자동 관리 시스템 구현 명세서

## 📋 시스템 개요

단기/갱신형 보험(자동차, 화재, 배상책임 등)의 만기일을 자동으로 추적하고, D-28일(4주전)과 D-14일(2주전)에 설계사에게 알림을 제공하는 시스템입니다.

---

## 🎯 핵심 기능

### 1. 데이터 감지 (Input)
- 고객의 보험 정보 입력 시 '보험종류(sub_type)'와 '보험기간(start_date - expiry_date)' 자동 감지
- `gk_policies` 테이블에 저장

### 2. 자동 태깅 & 일정 생성 (Logic)
- 만기일 기준으로 자동 태그 생성:
  - 자동차보험 → `#자동차보험만기`
  - 화재보험 → `#화재보험만기`
  - 공장화재 → `#공장화재만기`
  - 영업배상 → `#영업배상만기`
  - 특종보험 → `#특종보험만기`
- `gk_schedules` 테이블에 만기일 일정 자동 등록

### 3. 사전 알림 계산 (Trigger)
- 만기일로부터 D-28일(4주전), D-14일(2주전) 시점 계산
- `v_expiry_alerts` 뷰를 통해 알림 대상자 실시간 조회

### 4. 로그인 브리핑 (Action)
- STEP 2. 영업일정 점검 화면에 '보험만기 터치고객' 리스트 우선 표시
- 고객명, 보험 종류, 만기 D-Day, 태그 정보 제공

### 5. 에이젠틱 연동
- 만기 재가입 안내용 감성 멘트 자동 생성
- 카카오톡 발송 기능 연동

---

## 🗄️ 데이터베이스 스키마 확장

### gk_policies 테이블 확장

```sql
-- 신규 컬럼 추가
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS sub_type TEXT,      -- 보험 세부 유형
  ADD COLUMN IF NOT EXISTS start_date TEXT;    -- 보험 개시일

-- 인덱스 추가
CREATE INDEX idx_gk_policies_expiry_date ON gk_policies (expiry_date, agent_id);
CREATE INDEX idx_gk_policies_sub_type ON gk_policies (sub_type, agent_id);
```

### gk_schedules 테이블 활용

기존 `gk_schedules` 테이블 활용:
- `category = 'expiry'`: 만기 관리 일정
- `tags`: 보험 유형별 태그 배열
- `policy_id`: 계약 연결 (중도 해지 시 일정 삭제용)

---

## ⚙️ 핵심 함수 및 트리거

### 1. 태그 매핑 함수

```sql
CREATE OR REPLACE FUNCTION get_expiry_tag(p_sub_type TEXT) RETURNS TEXT
```
- 보험 세부 유형에 따라 적절한 태그 반환

### 2. 만기 일정 자동 생성 함수

```sql
CREATE OR REPLACE FUNCTION create_expiry_schedule(...)
```
- 보험 계약 정보를 받아 `gk_schedules`에 만기일 일정 등록
- 계약자 정보 조인하여 고객명 포함

### 3. 자동 생성 트리거

```sql
CREATE TRIGGER trg_gk_policies_expiry_schedule
  AFTER INSERT ON gk_policies
```
- 신규 보험 계약 입력 시 자동으로 만기 일정 생성

### 4. 만기 알림 대상자 조회 뷰

```sql
CREATE VIEW v_expiry_alerts
```
- D-28일, D-14일 알림 대상자 실시간 조회
- `alert_priority`: 1 (D-28), 2 (D-14)
- `days_until_expiry`: 만기까지 남은 일수

---

## 🐍 Python 함수 구현 (db_utils.py)

### 1. 만기 대상자 조회 함수

```python
def get_expiry_alerts(
    agent_id: str,
    days_range: int = 30,
    priority_only: bool = True
) -> list[dict]:
    """
    보험 만기 알림 대상자 조회.
    
    Args:
        agent_id: 설계사 ID
        days_range: 조회 범위 (기본 30일)
        priority_only: True이면 D-28, D-14만 조회
    
    Returns:
        만기 대상자 리스트
    """
```

### 2. 만기 재가입 멘트 생성 함수

```python
def generate_expiry_renewal_message(
    customer_name: str,
    sub_type: str,
    expiry_date: str,
    days_until: int
) -> str:
    """
    만기 재가입 안내용 감성 멘트 생성.
    
    Returns:
        카카오톡 발송용 메시지
    """
```

---

## 🎨 UI 구현 (CRM 앱)

### STEP 2. 영업일정 점검 화면

```python
# crm_app_impl.py 또는 blocks/crm_morning_routine_block.py

def render_expiry_alerts(agent_id: str):
    """
    [🚨 보험 만기 관리 대상자] 섹션 렌더링
    """
    alerts = get_expiry_alerts(agent_id, priority_only=True)
    
    if not alerts:
        return
    
    st.markdown("### 🚨 보험 만기 관리 대상자")
    
    for alert in alerts:
        priority_icon = "🔴" if alert["alert_priority"] == 2 else "🟡"
        
        with st.expander(
            f"{priority_icon} {alert['customer_name']} - "
            f"{alert['sub_type']} (D-{alert['days_until_expiry']})"
        ):
            st.write(f"**보험사:** {alert['insurance_company']}")
            st.write(f"**상품명:** {alert['product_name']}")
            st.write(f"**만기일:** {alert['expiry_date']}")
            st.write(f"**태그:** {', '.join(alert['tags'])}")
            
            # 감성 멘트 생성
            message = generate_expiry_renewal_message(
                alert['customer_name'],
                alert['sub_type'],
                alert['expiry_date'],
                alert['days_until_expiry']
            )
            
            st.text_area("📱 카톡 발송 메시지", message, height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📞 전화하기", key=f"call_{alert['schedule_id']}"):
                    st.info("전화 연결 기능 (향후 구현)")
            with col2:
                if st.button("💬 카톡 발송", key=f"kakao_{alert['schedule_id']}"):
                    # 카카오톡 발송 로직 연동
                    st.success("카카오톡 발송 완료!")
```

---

## 📊 데이터 흐름

```
[보험 계약 입력]
    ↓
[gk_policies 테이블 INSERT]
    ↓
[트리거 자동 실행]
    ↓
[create_expiry_schedule() 함수 호출]
    ↓
[gk_schedules 테이블에 만기일 일정 등록]
    ↓
[v_expiry_alerts 뷰로 실시간 조회]
    ↓
[STEP 2 화면에 알림 대상자 표시]
    ↓
[감성 멘트 생성 → 카톡 발송]
```

---

## 🔧 구현 단계

### Phase 1: DB 스키마 확장 ✅
- [x] `insurance_expiry_automation.sql` 작성 완료
- [ ] Supabase SQL Editor에서 실행

### Phase 2: Python 함수 구현
- [ ] `db_utils.py`에 `get_expiry_alerts()` 추가
- [ ] `db_utils.py`에 `generate_expiry_renewal_message()` 추가

### Phase 3: UI 구현
- [ ] `crm_app_impl.py` 또는 `blocks/` 디렉토리에 만기 알림 UI 추가
- [ ] STEP 2 화면에 통합

### Phase 4: 에이젠틱 연동
- [ ] AI 감성 멘트 생성 로직 구현
- [ ] 카카오톡 발송 기능 연동

### Phase 5: 테스트 및 배포
- [ ] 테스트 데이터로 검증
- [ ] CRM 앱 배포

---

## 📝 주의사항

### GP 제53조 준수
- 기존 `generate_followup_schedules()` 함수 보존
- 새로운 만기 관리 로직은 독립적으로 추가
- 기존 일정 관리 로직과 충돌 없도록 `category = 'expiry'`로 구분

### 데이터 보안
- `person_id`, `policy_id`는 UUID 형식 유지
- 고객 연락처 등 PII는 암호화 저장 원칙 준수

### 성능 최적화
- `v_expiry_alerts` 뷰는 인덱스 활용으로 빠른 조회 보장
- 대량 데이터 처리 시 배치 작업 고려

---

## 🎯 기대 효과

1. **설계사 업무 효율화**: 만기 관리 자동화로 누락 방지
2. **고객 만족도 향상**: 적시 재가입 안내로 보장 공백 최소화
3. **계약 유지율 증가**: 체계적인 만기 관리로 재계약률 향상
4. **AI 활용 극대화**: 감성 멘트 자동 생성으로 상담 품질 향상

---

## 📚 참고 자료

- `gk_schedules_migration.sql`: 기존 일정 관리 스키마
- `db_utils.py`: 기존 일정 관리 함수 (`generate_followup_schedules()`)
- `crm_fortress_schema.sql`: 보험 계약 데이터 구조
