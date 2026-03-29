# ════════════════════════════════════════════════════════════════════════════
# [GP-BILLING] 크레딧 기반 과금 시스템 구축 완료 보고서
# Goldkey AI Masters 2026 — 런칭 타임라인 기반 베타 ➡️ 유료화 전환
# ════════════════════════════════════════════════════════════════════════════

**작성일**: 2026-03-29  
**작성자**: Cascade AI Development Team  
**상태**: ✅ Phase 1 완료 (백엔드 구축) / 🔄 Phase 2 대기 (UI 통합)

---

## 📋 구현 완료 항목

### ✅ 1. 아키텍처 설계 문서
**파일**: `CREDIT_SYSTEM_ARCHITECTURE.md`

- 비즈니스 모델 정의 (BETA → TRIAL → PAID/EXPIRED)
- 타임라인 기반 상태 전환 로직 (2026-09-01 기준)
- 크레딧 차감 규칙 (OCR: -1, 트리니티: -1, 에이젠틱: -3)
- UI 표시 규칙 및 관리자 패널 설계
- 보안 및 방어 로직 명세

### ✅ 2. Supabase DB 스키마 확장
**파일**: `gk_members_credit_system.sql`

#### 신규 컬럼 추가 (gk_members 테이블)
```sql
- plan_type              TEXT (BASIC/PRO)
- status                 TEXT (BETA/TRIAL/PAID/EXPIRED)
- current_credits        INTEGER (잔여 크레딧)
- join_date              DATE (가입일)
- monthly_renewal_date   DATE (월간 갱신일)
- trial_end_date         DATE (무료체험 종료일)
```

#### 신규 테이블 생성
```sql
- gk_credit_history      감사 추적용 크레딧 히스토리 테이블
  - id, user_id, action_type, amount, before_balance, after_balance
  - reason, admin_id, created_at
```

#### 헬퍼 함수 생성 (Supabase Functions)
```sql
- deduct_user_credits(user_id, amount, reason)
- renew_monthly_credits(user_id)
- check_trial_expiry(user_id)
```

### ✅ 3. 백엔드 크레딧 시스템 함수 (db_utils.py)

#### 신규 함수 6개 추가

1. **`initialize_user_billing_status(user_id, join_date)`**
   - 신규 회원 가입 시 타임라인 기반 상태 초기화
   - 2026-08-31 이전: BETA (100 크레딧)
   - 2026-09-01 이후: TRIAL (30일 무료체험)

2. **`check_and_deduct_credits(user_id, cost, reason)`**
   - AI 기능 실행 전 크레딧 체크 및 차감
   - TRIAL: 무제한 허용
   - EXPIRED: 차단
   - 크레딧 부족 시: 에러 메시지 반환

3. **`renew_monthly_credits_if_needed(user_id)`**
   - 매월 크레딧 갱신 체크 (BETA/PAID 전용)
   - 로그인 시 자동 호출
   - BETA: 100 코인, PAID PRO: 200 코인, PAID BASIC: 50 코인

4. **`check_trial_expiry(user_id)`**
   - 트라이얼 만료 체크 및 EXPIRED 전환
   - 로그인 시 자동 호출
   - 만료일 도달 시 자동 상태 전환

5. **`admin_update_credits(user_id, delta, admin_id)`**
   - 관리자 전용 크레딧 충전/차감
   - 히스토리 기록 포함

6. **`admin_update_status(user_id, new_status, admin_id)`**
   - 관리자 전용 회원 상태 강제 변경
   - BETA/TRIAL/PAID/EXPIRED 전환

---

## 🔄 다음 단계: UI 통합 (Phase 2)

### 1️⃣ CRM 앱 사이드바 크레딧 배지 추가

**파일**: `crm_app_impl.py`  
**위치**: 사이드바 최상단 (로그인 후)

```python
# 로그인 후 사용자 정보 조회
_user_id = st.session_state.get("crm_user_id", "")
_user_data = _du_get_member_by_id(_user_id)  # 또는 get_member() 사용

if _user_data:
    status = _user_data.get("status", "BETA")
    current_credits = _user_data.get("current_credits", 0)
    trial_end_date = _user_data.get("trial_end_date")
    
    # 크레딧 갱신 체크 (로그인 시 1회)
    if not st.session_state.get("_credit_renewed_checked"):
        from db_utils import renew_monthly_credits_if_needed, check_trial_expiry
        renew_monthly_credits_if_needed(_user_id)
        check_trial_expiry(_user_id)
        st.session_state["_credit_renewed_checked"] = True
    
    # 사이드바 상단 배지
    st.sidebar.markdown("---")
    
    if status == "BETA":
        st.sidebar.markdown("🟢 **베타 진행 중**")
        st.sidebar.markdown(f"🪙 **잔여 크레딧: {current_credits} 코인**")
    
    elif status == "TRIAL":
        from datetime import datetime
        if trial_end_date:
            end_date = datetime.strptime(trial_end_date, "%Y-%m-%d").date()
            days_left = (end_date - datetime.now().date()).days
            st.sidebar.markdown(f"⏳ **무료 체험 {days_left}일 남음**")
        st.sidebar.markdown("🪙 **크레딧: 무제한**")
    
    elif status == "PAID":
        st.sidebar.markdown("💎 **PRO 회원**")
        st.sidebar.markdown(f"🪙 **잔여 크레딧: {current_credits} 코인**")
    
    elif status == "EXPIRED":
        st.sidebar.error("🔴 **무료체험 종료**")
        st.sidebar.error("💳 **결제가 필요합니다**")
        st.stop()  # 앱 접속 차단
    
    st.sidebar.markdown("---")
```

### 2️⃣ HQ 앱 관리자 크레딧 통제 패널

**파일**: `hq_app_impl.py`  
**위치**: 관리자 전용 섹션

```python
# 관리자 권한 체크
if st.session_state.get("user_role") == "admin":
    with st.expander("🔧 크레딧 통제 패널 (Admin Only)", expanded=False):
        st.markdown("### 회원 검색 및 크레딧 관리")
        
        user_search = st.text_input("회원 검색 (이름 또는 ID)", key="admin_credit_search")
        
        if user_search:
            from db_utils import get_member, admin_update_credits, admin_update_status
            
            # 회원 조회
            user = get_member(user_search)
            
            if user:
                st.success(f"✅ 회원 찾음: {user.get('name', '')}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**현재 상태**: {user.get('status', 'N/A')}")
                    st.write(f"**플랜**: {user.get('plan_type', 'N/A')}")
                    st.write(f"**잔여 크레딧**: {user.get('current_credits', 0)}")
                    st.write(f"**가입일**: {user.get('join_date', 'N/A')}")
                
                with col2:
                    # 크레딧 충전/차감
                    st.markdown("#### 크레딧 변경")
                    credit_delta = st.number_input(
                        "변경량 (양수=충전, 음수=차감)",
                        min_value=-1000,
                        max_value=1000,
                        value=0,
                        step=10,
                        key="admin_credit_delta"
                    )
                    
                    if st.button("💰 크레딧 적용", key="admin_apply_credit"):
                        result = admin_update_credits(
                            user.get("user_id"),
                            credit_delta,
                            st.session_state.get("user_id", "admin")
                        )
                        if result["success"]:
                            st.success(f"✅ {result['message']} (새 잔액: {result['new_balance']})")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['message']}")
                    
                    # 상태 강제 변경
                    st.markdown("#### 상태 변경")
                    new_status = st.selectbox(
                        "새 상태",
                        ["BETA", "TRIAL", "PAID", "EXPIRED"],
                        key="admin_new_status"
                    )
                    
                    if st.button("🔄 상태 변경", key="admin_apply_status"):
                        result = admin_update_status(
                            user.get("user_id"),
                            new_status,
                            st.session_state.get("user_id", "admin")
                        )
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                            st.rerun()
                        else:
                            st.error(f"❌ {result['message']}")
            else:
                st.warning("⚠️ 회원을 찾을 수 없습니다.")
```

### 3️⃣ AI 기능 실행 전 크레딧 체크 통합

**적용 대상 파일**:
- `modules/scan_engine.py` (OCR 스캔)
- `modules/ai_engine.py` (트리니티 분석)
- `expert_agent.py` (에이젠틱 AI)

**통합 패턴**:

```python
# AI 기능 실행 전
from db_utils import check_and_deduct_credits

def run_ai_analysis(user_id, ...):
    # 크레딧 체크 (비용: 스캔=1, 에이젠틱=3)
    credit_check = check_and_deduct_credits(user_id, cost=1, reason="OCR 스캔")
    
    if not credit_check["success"]:
        st.error(f"❌ {credit_check['message']}")
        st.info(f"💡 잔여 크레딧: {credit_check['remaining']} 코인")
        return None
    
    # 크레딧 차감 성공 → AI 기능 실행
    st.info(f"✅ 크레딧 차감 완료 (잔여: {credit_check['remaining']} 코인)")
    
    # ... AI 분석 로직 ...
```

### 4️⃣ 회원 가입 시 타임라인 기반 초기화

**파일**: `crm_app_impl.py` 또는 `hq_app_impl.py`  
**위치**: 회원 가입 완료 후

```python
# 회원 가입 성공 후
from db_utils import initialize_user_billing_status

# 신규 회원 billing 상태 초기화
billing_result = initialize_user_billing_status(
    user_id=new_user_id,
    join_date=None  # None이면 오늘 날짜 자동 설정
)

if billing_result["success"]:
    st.success(f"✅ {billing_result['message']}")
    st.info(f"📊 상태: {billing_result['status']} / 크레딧: {billing_result['credits']}")
```

---

## 🧪 테스트 시나리오

### 시나리오 1: 베타 사용자 (2026년 8월 이전 가입)

```python
# 가입일 시뮬레이션
from db_utils import initialize_user_billing_status, check_and_deduct_credits

# 베타 사용자 초기화
result = initialize_user_billing_status("test_user_1", join_date="2026-07-15")
print(result)
# {'success': True, 'status': 'BETA', 'credits': 100, ...}

# 크레딧 차감 테스트
check_and_deduct_credits("test_user_1", cost=1, reason="OCR 스캔")
# {'success': True, 'remaining': 99, ...}

# 크레딧 소진 테스트
for i in range(100):
    check_and_deduct_credits("test_user_1", cost=1)

check_and_deduct_credits("test_user_1", cost=1)
# {'success': False, 'message': '이번 달 잔여 코인이 부족합니다...', 'remaining': 0}
```

### 시나리오 2: 트라이얼 사용자 (2026년 9월 이후 가입)

```python
# 트라이얼 사용자 초기화
result = initialize_user_billing_status("test_user_2", join_date="2026-09-15")
print(result)
# {'success': True, 'status': 'TRIAL', 'trial_end_date': '2026-10-15', ...}

# 크레딧 체크 (무제한)
check_and_deduct_credits("test_user_2", cost=999)
# {'success': True, 'message': '무료체험 중 (크레딧 무제한)', 'remaining': 999}

# 만료일 도달 시뮬레이션 (수동으로 trial_end_date를 과거로 변경 후)
from db_utils import check_trial_expiry
check_trial_expiry("test_user_2")
# {'success': True, 'expired': True, 'message': '무료체험 종료 → EXPIRED 전환'}

# EXPIRED 상태에서 AI 기능 차단
check_and_deduct_credits("test_user_2", cost=1)
# {'success': False, 'message': '무료체험 종료. 결제가 필요합니다.', 'remaining': 0}
```

### 시나리오 3: 관리자 크레딧 통제

```python
from db_utils import admin_update_credits, admin_update_status

# 크레딧 충전
admin_update_credits("test_user_1", delta=50, admin_id="admin_001")
# {'success': True, 'message': '크레딧 충전 완료', 'new_balance': 50}

# 상태 변경 (BETA → PAID)
admin_update_status("test_user_1", new_status="PAID", admin_id="admin_001")
# {'success': True, 'message': '상태 변경 완료: PAID'}
```

---

## 📦 배포 체크리스트

### ✅ Phase 1: 백엔드 구축 (완료)
- [x] 아키텍처 설계 문서 작성
- [x] Supabase SQL 마이그레이션 파일 생성
- [x] db_utils.py 크레딧 시스템 함수 추가
- [x] 구현 보고서 작성

### 🔄 Phase 2: Supabase 설치 (대기 중)
- [ ] Supabase SQL Editor에서 `gk_members_credit_system.sql` 실행
- [ ] gk_members 테이블 확장 확인
- [ ] gk_credit_history 테이블 생성 확인
- [ ] 헬퍼 함수 3개 생성 확인

### 🔄 Phase 3: UI 통합 (대기 중)
- [ ] CRM 사이드바 크레딧 배지 추가
- [ ] HQ 관리자 패널 추가
- [ ] 회원 가입 시 billing 초기화 통합
- [ ] AI 기능 실행 전 크레딧 체크 통합
  - [ ] OCR 스캔 (modules/scan_engine.py)
  - [ ] 트리니티 분석 (modules/ai_engine.py)
  - [ ] 에이젠틱 AI (expert_agent.py)

### 🔄 Phase 4: 테스트 및 검증 (대기 중)
- [ ] 베타 사용자 시나리오 테스트
- [ ] 트라이얼 사용자 시나리오 테스트
- [ ] 만료 사용자 차단 테스트
- [ ] 관리자 크레딧 통제 테스트
- [ ] 월간 갱신 로직 테스트

### 🔄 Phase 5: 배포 (대기 중)
- [ ] HQ 앱 배포 (backup_and_push.ps1)
- [ ] CRM 앱 배포 (deploy_crm.ps1)
- [ ] 프로덕션 환경 검증

---

## ⚠️ 중요 주의사항

### 1. Supabase SQL 마이그레이션 필수
**반드시 먼저 실행**: `gk_members_credit_system.sql`

이 파일을 실행하지 않으면 백엔드 함수들이 작동하지 않습니다.

### 2. 기존 회원 데이터 처리
SQL 마이그레이션 실행 시 기존 회원들은 자동으로 BETA 상태로 전환됩니다.
- status = 'BETA'
- current_credits = 100
- monthly_renewal_date = 다음 달 1일

### 3. 타임존 통일
모든 날짜 비교는 서버 시간(UTC) 기준으로 처리됩니다.

### 4. EXPIRED 상태 처리
EXPIRED 상태 회원은 앱 접속 시 즉시 차단되므로, UI에서 `st.stop()` 호출 필수.

### 5. 크레딧 히스토리 테이블
`gk_credit_history` 테이블이 없어도 크레딧 시스템은 작동하지만, 감사 추적이 불가능합니다.

---

## 📊 예상 수익 모델

### 베타 기간 (현재 ~ 2026년 8월)
- 무료 베타 테스터 확보 (피드백 수집)
- 월 100 크레딧 제공 (약 100회 AI 분석)
- 목표: 100명 베타 테스터

### 유료화 전환 (2026년 9월 이후)
- 30일 무료체험 → 전환율 목표 20%
- **PRO 플랜**: 월 29,000원 (200 크레딧)
- **BASIC 플랜**: 월 9,900원 (50 크레딧)
- 예상 월 매출: 20명 × 29,000원 = 580,000원 (최소)

---

## 🔗 관련 파일

### 신규 생성 파일
1. `CREDIT_SYSTEM_ARCHITECTURE.md` — 아키텍처 설계 문서
2. `gk_members_credit_system.sql` — Supabase SQL 마이그레이션
3. `GP_BILLING_IMPLEMENTATION_REPORT.md` — 본 보고서

### 수정된 파일
1. `db_utils.py` — 크레딧 시스템 함수 6개 추가 (Line 1251-1621)

### 다음 수정 예정 파일
1. `crm_app_impl.py` — 사이드바 크레딧 배지 + 회원가입 초기화
2. `hq_app_impl.py` — 관리자 크레딧 통제 패널
3. `modules/scan_engine.py` — OCR 스캔 전 크레딧 체크
4. `modules/ai_engine.py` — 트리니티 분석 전 크레딧 체크
5. `expert_agent.py` — 에이젠틱 AI 전 크레딧 체크

---

## 📞 다음 조치 사항

### 즉시 실행 필요
1. **Supabase SQL Editor 접속**
2. **`gk_members_credit_system.sql` 파일 내용 복사**
3. **SQL Editor에서 실행**
4. **실행 결과 확인** (✅ 메시지 확인)

### 이후 작업 순서
1. UI 통합 코드 작성 (CRM 사이드바 + HQ 관리자 패널)
2. AI 기능 크레딧 체크 통합
3. 테스트 시나리오 실행
4. 배포

---

**최종 업데이트**: 2026-03-29 11:41 AM  
**다음 단계**: Supabase SQL 마이그레이션 실행 후 UI 통합 작업 시작
