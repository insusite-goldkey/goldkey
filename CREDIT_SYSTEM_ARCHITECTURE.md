# ════════════════════════════════════════════════════════════════════════════
# [GP-BILLING] Goldkey AI Masters 2026 — 크레딧 기반 과금 시스템 아키텍처
# 런칭 타임라인 기반 베타 ➡️ 무료체험 ➡️ 유료화 전환 체계
# ════════════════════════════════════════════════════════════════════════════

## 📋 비즈니스 모델 개요

### Phase 1: 베타 테스트 (현재 ~ 2026년 8월 31일)
- **대상**: 2026년 8월 31일 이전 가입자
- **상태**: `status = 'BETA'`
- **혜택**: 매월 1일 자동으로 100 크레딧 지급
- **제한**: 크레딧 소진 시 AI 기능 사용 불가 (다음 달 갱신 대기)

### Phase 2: 무료체험 + 유료화 (2026년 9월 1일 이후)
- **대상**: 2026년 9월 1일 이후 신규 가입자
- **상태**: `status = 'TRIAL'` (가입 후 30일간)
- **혜택**: 30일간 무제한 PRO 플랜 사용 (크레딧 무제한)
- **만료**: 30일 후 `status = 'EXPIRED'` 전환 → 앱 접속 차단 (Paywall)
- **전환**: 결제 또는 관리자 승인 시 `status = 'PAID'` 전환

---

## 🗄️ DB 스키마 확장 (gk_members 테이블)

### 신규 컬럼 추가

```sql
ALTER TABLE public.gk_members
  ADD COLUMN IF NOT EXISTS plan_type              TEXT DEFAULT 'BASIC'
                                                   CHECK (plan_type IN ('BASIC', 'PRO')),
  ADD COLUMN IF NOT EXISTS status                 TEXT DEFAULT 'BETA'
                                                   CHECK (status IN ('BETA', 'TRIAL', 'PAID', 'EXPIRED')),
  ADD COLUMN IF NOT EXISTS current_credits        INTEGER DEFAULT 100,
  ADD COLUMN IF NOT EXISTS join_date              DATE DEFAULT CURRENT_DATE,
  ADD COLUMN IF NOT EXISTS monthly_renewal_date   DATE,
  ADD COLUMN IF NOT EXISTS trial_end_date         DATE;
```

### 컬럼 설명

| 컬럼명 | 타입 | 기본값 | 설명 |
|--------|------|--------|------|
| `plan_type` | TEXT | 'BASIC' | 플랜 유형 (BASIC/PRO) |
| `status` | TEXT | 'BETA' | 회원 상태 (BETA/TRIAL/PAID/EXPIRED) |
| `current_credits` | INTEGER | 100 | 잔여 크레딧 (코인) |
| `join_date` | DATE | CURRENT_DATE | 가입일 (타임라인 판단 기준) |
| `monthly_renewal_date` | DATE | NULL | 매월 크레딧 갱신일 (BETA 전용) |
| `trial_end_date` | DATE | NULL | 무료체험 종료일 (TRIAL 전용) |

---

## 🔄 상태 전환 로직 (State Machine)

```
[신규 가입]
    ↓
join_date < 2026-09-01?
    ↓ YES                    ↓ NO
[BETA]                   [TRIAL]
    ↓                        ↓
매월 1일                  가입일 + 30일
100 크레딧 지급          trial_end_date 도달
    ↓                        ↓
크레딧 소진 시           [EXPIRED]
AI 기능 차단                 ↓
    ↓                    결제/승인
다음 달 갱신                 ↓
                         [PAID]
                             ↓
                         매월 크레딧 지급
```

---

## 💰 크레딧 차감 규칙

### AI 기능별 크레딧 소비량

| 기능 | 크레딧 차감 | 설명 |
|------|------------|------|
| **OCR 스캔** | -1 | 증권 사진 스캔 |
| **트리니티 분석** | -1 | 보장 분석 (단순) |
| **에이젠틱 AI 추론** | -3 | 복합 추론 (GPT-4 등) |
| **보고서 생성** | -1 | PDF/이미지 생성 |

### 크레딧 체크 로직 (Pseudo Code)

```python
def check_and_deduct_credits(user_id: str, cost: int) -> dict:
    """
    AI 기능 실행 전 크레딧 체크 및 차감
    
    Returns:
        {"success": True/False, "message": str, "remaining": int}
    """
    user = get_user(user_id)
    
    # TRIAL 상태는 크레딧 무제한
    if user.status == 'TRIAL':
        return {"success": True, "message": "무료체험 중", "remaining": 999}
    
    # EXPIRED 상태는 차단
    if user.status == 'EXPIRED':
        return {"success": False, "message": "무료체험 종료. 결제 필요", "remaining": 0}
    
    # 크레딧 부족 체크
    if user.current_credits < cost:
        return {
            "success": False,
            "message": "이번 달 잔여 코인이 부족합니다. 다음 달 갱신을 기다리시거나 관리자에게 충전을 문의하세요.",
            "remaining": user.current_credits
        }
    
    # 크레딧 차감
    new_credits = user.current_credits - cost
    update_user_credits(user_id, new_credits)
    
    return {"success": True, "message": "차감 완료", "remaining": new_credits}
```

---

## 🎨 UI 표시 규칙

### CRM 사이드바 상단 (Credit Badge)

```python
# 상태별 표시 예시
if status == 'BETA':
    st.sidebar.markdown("🟢 **베타 진행 중**")
    st.sidebar.markdown(f"🪙 **잔여 크레딧: {current_credits} 코인**")
    
elif status == 'TRIAL':
    days_left = (trial_end_date - today).days
    st.sidebar.markdown(f"⏳ **무료 체험 {days_left}일 남음**")
    st.sidebar.markdown("🪙 **크레딧: 무제한**")
    
elif status == 'PAID':
    st.sidebar.markdown("💎 **PRO 회원**")
    st.sidebar.markdown(f"🪙 **잔여 크레딧: {current_credits} 코인**")
    
elif status == 'EXPIRED':
    st.sidebar.markdown("🔴 **무료체험 종료**")
    st.sidebar.markdown("💳 **결제가 필요합니다**")
```

### HQ 관리자 패널 (Admin Credit Control)

```python
# 관리자 전용 크레딧 통제 패널
with st.expander("🔧 크레딧 통제 패널 (Admin Only)"):
    user_search = st.text_input("회원 검색 (이름/ID)")
    
    if user_search:
        user = search_user(user_search)
        st.write(f"**현재 상태**: {user.status}")
        st.write(f"**잔여 크레딧**: {user.current_credits}")
        
        # 크레딧 충전/차감
        credit_delta = st.number_input("크레딧 변경", -100, 100, 0)
        if st.button("적용"):
            update_user_credits(user.user_id, user.current_credits + credit_delta)
        
        # 상태 강제 변경
        new_status = st.selectbox("상태 변경", ['BETA', 'TRIAL', 'PAID', 'EXPIRED'])
        if st.button("상태 변경"):
            update_user_status(user.user_id, new_status)
```

---

## 🔒 보안 및 방어 로직

### 1. 크레딧 조작 방지
- 모든 크레딧 차감은 **서버 사이드(db_utils.py)**에서만 처리
- 클라이언트(Streamlit UI)에서는 읽기 전용으로만 표시
- Supabase RLS 정책으로 일반 사용자의 직접 UPDATE 차단

### 2. 타임라인 조작 방지
- `join_date`는 가입 시 자동 설정 (사용자 수정 불가)
- `trial_end_date`는 가입 시 자동 계산 (join_date + 30일)
- 서버 시간(UTC) 기준으로 날짜 비교

### 3. 무한 크레딧 방지
- TRIAL 상태는 반드시 `trial_end_date` 체크
- 만료일 도달 시 자동으로 EXPIRED 전환 (Cron Job 또는 로그인 시 체크)

---

## 📅 월간 크레딧 갱신 로직 (BETA/PAID 전용)

### Cron Job 또는 로그인 시 체크

```python
def renew_monthly_credits_if_needed(user_id: str):
    """
    매월 1일 또는 monthly_renewal_date 도달 시 크레딧 갱신
    """
    user = get_user(user_id)
    
    # TRIAL/EXPIRED는 갱신 대상 아님
    if user.status in ['TRIAL', 'EXPIRED']:
        return
    
    today = datetime.now().date()
    
    # 갱신일이 없으면 오늘로 설정 (최초 1회)
    if not user.monthly_renewal_date:
        update_user(user_id, monthly_renewal_date=today)
        return
    
    # 갱신일 도달 체크
    if today >= user.monthly_renewal_date:
        # 크레딧 갱신
        if user.status == 'BETA':
            new_credits = 100
        elif user.status == 'PAID':
            new_credits = 200  # PRO 회원은 200 코인
        
        update_user(user_id, 
                   current_credits=new_credits,
                   monthly_renewal_date=today + relativedelta(months=1))
```

---

## 🧪 테스트 시나리오

### 1. 베타 사용자 (2026년 8월 이전 가입)
```python
# 가입일 시뮬레이션
join_date = '2026-07-15'
status = 'BETA'
current_credits = 100

# 크레딧 차감 테스트
check_and_deduct_credits(user_id, cost=1)  # ✅ 성공 (99 남음)
check_and_deduct_credits(user_id, cost=100) # ❌ 실패 (부족)

# 월간 갱신 테스트
renew_monthly_credits_if_needed(user_id)  # ✅ 100 코인 지급
```

### 2. 트라이얼 사용자 (2026년 9월 이후 가입)
```python
# 가입일 시뮬레이션
join_date = '2026-09-15'
status = 'TRIAL'
trial_end_date = '2026-10-15'

# 크레딧 체크 (무제한)
check_and_deduct_credits(user_id, cost=999)  # ✅ 성공 (무제한)

# 만료일 도달 시뮬레이션
today = '2026-10-16'
check_trial_expiry(user_id)  # ✅ status → 'EXPIRED'
```

### 3. 만료 사용자 (결제 필요)
```python
status = 'EXPIRED'

# AI 기능 차단
check_and_deduct_credits(user_id, cost=1)  # ❌ 실패 (결제 필요)

# 관리자 승인 시뮬레이션
admin_update_status(user_id, 'PAID')  # ✅ status → 'PAID'
admin_add_credits(user_id, 200)       # ✅ 200 코인 지급
```

---

## 📦 구현 파일 목록

### 1. DB 마이그레이션
- `gk_members_credit_system.sql` — 신규 컬럼 추가 SQL

### 2. 백엔드 로직
- `db_utils.py` — 크레딧 체크/차감 함수 추가
  - `check_and_deduct_credits(user_id, cost)`
  - `renew_monthly_credits_if_needed(user_id)`
  - `check_trial_expiry(user_id)`
  - `admin_update_credits(user_id, delta)`
  - `admin_update_status(user_id, new_status)`

### 3. UI 업데이트
- `crm_app_impl.py` — 사이드바 크레딧 배지 추가
- `hq_app_impl.py` — 관리자 크레딧 통제 패널 추가

### 4. AI 기능 통합
- `modules/scan_engine.py` — OCR 스캔 전 크레딧 체크
- `modules/ai_engine.py` — 트리니티 분석 전 크레딧 체크
- `expert_agent.py` — 에이젠틱 AI 전 크레딧 체크

---

## ⚠️ 주의사항

1. **타임존 통일**: 모든 날짜 비교는 UTC 기준으로 처리
2. **크레딧 음수 방지**: 차감 전 반드시 잔액 체크
3. **상태 전환 자동화**: 로그인 시 또는 Cron Job으로 TRIAL → EXPIRED 자동 전환
4. **관리자 권한 보호**: 크레딧 통제 패널은 `user_role='admin'`만 접근 가능

---

## 📊 예상 수익 모델

### 베타 기간 (2026년 8월까지)
- 무료 베타 테스터 확보 (피드백 수집)
- 월 100 크레딧 제공 (약 100회 AI 분석)

### 유료화 전환 (2026년 9월 이후)
- 30일 무료체험 → 전환율 목표 20%
- PRO 플랜: 월 29,000원 (200 크레딧)
- BASIC 플랜: 월 9,900원 (50 크레딧)

---

**최종 업데이트**: 2026-03-29  
**작성자**: Goldkey AI Masters 2026 개발팀
