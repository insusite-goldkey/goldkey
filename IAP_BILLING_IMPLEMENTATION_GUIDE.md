# Google Play Billing 인앱 결제 시스템 구현 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [데이터베이스 스키마](#데이터베이스-스키마)
3. [백엔드 검증 로직](#백엔드-검증-로직)
4. [프론트엔드 UI](#프론트엔드-ui)
5. [테스트 방법](#테스트-방법)
6. [배포 체크리스트](#배포-체크리스트)

---

## 시스템 개요

### 핵심 기능
- ✅ Google Play 영수증 실시간 검증
- ✅ 중복 결제 방지 (purchase_token 기반)
- ✅ 원자적 트랜잭션 (코인 충전 + 내역 기록)
- ✅ 하드 락(Hard Lock) 화면 자동 표시
- ✅ 충전 즉시 UI 반영 (1초 이내)

### 아키텍처
```
[사용자 결제] 
    ↓
[Google Play Store]
    ↓ (purchase_token)
[Streamlit App]
    ↓
[payment_handler.py] → Google Play Developer API 검증
    ↓
[Supabase RPC: grant_coins_from_iap()]
    ↓
[gk_purchases + gk_members + gk_credit_history]
    ↓
[UI 즉시 갱신 + st.balloons()]
```

---

## 데이터베이스 스키마

### 1. 결제 중복 방지 테이블 (gk_purchases)

**파일**: `gk_iap_billing_schema.sql`

```sql
CREATE TABLE public.gk_purchases (
    purchase_token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    status TEXT DEFAULT 'COMPLETED',
    coins_granted INTEGER NOT NULL DEFAULT 0,
    platform TEXT DEFAULT 'google_play',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**역할**:
- `purchase_token`을 PK로 사용하여 동일 영수증 중복 처리 차단
- 해킹 시도 또는 네트워크 재시도로 인한 중복 코인 지급 방지

### 2. 코인 충전 내역 테이블 (gk_credit_history)

```sql
CREATE TABLE public.gk_credit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    description TEXT,
    purchase_token TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**action_type 종류**:
- `IAP_RECHARGE`: 인앱 결제 충전
- `USAGE`: 기능 사용으로 인한 차감
- `REFUND`: 환불
- `MONTHLY_GRANT`: 월간 정기 지급

### 3. 코인 충전 함수 (grant_coins_from_iap)

```sql
CREATE OR REPLACE FUNCTION public.grant_coins_from_iap(
    p_user_id TEXT,
    p_purchase_token TEXT,
    p_product_id TEXT,
    p_coins INTEGER
)
RETURNS JSON
```

**처리 순서**:
1. 중복 결제 확인 (`gk_purchases` 조회)
2. 현재 코인 조회 (`gk_members`)
3. 코인 충전 (UPDATE)
4. 결제 기록 저장 (INSERT into `gk_purchases`)
5. 내역 기록 (INSERT into `gk_credit_history`)
6. JSON 응답 반환

---

## 백엔드 검증 로직

### 파일 구조
```
modules/
├── payment_handler.py  # 결제 검증 및 코인 충전 핸들러
└── credit_ui.py        # 코인 충전 UI 컴포넌트
```

### payment_handler.py 주요 함수

#### 1. verify_google_play_purchase()
```python
def verify_google_play_purchase(
    package_name: str,
    product_id: str,
    purchase_token: str
) -> Dict:
    """
    Google Play Developer API를 통한 영수증 검증.
    
    Returns:
        {
            'valid': bool,
            'purchase_state': int,
            'consumption_state': int,
            'order_id': str
        }
    """
```

**필수 환경 변수**:
- `GOOGLE_PLAY_CREDENTIALS_PATH`: 서비스 계정 JSON 키 파일 경로

#### 2. process_iap_recharge()
```python
def process_iap_recharge(
    user_id: str,
    purchase_token: str,
    product_id: str,
    package_name: str = "com.goldkey.ai.masters"
) -> Dict:
    """
    인앱 결제 검증 후 코인 충전 처리.
    
    Returns:
        {
            'success': bool,
            'coins_granted': int,
            'balance_after': int,
            'message': str
        }
    """
```

**상품별 코인 매핑**:
```python
PRODUCT_COINS = {
    'basic_monthly': 50,
    'pro_monthly': 300,
    'basic_addon_50': 50,
    'pro_addon_300': 300,
}
```

#### 3. simulate_test_purchase() (개발용)
```python
def simulate_test_purchase(
    user_id: str,
    product_id: str = 'basic_monthly'
) -> Dict:
    """
    테스트용 가상 결제 시뮬레이션.
    실제 Google Play API 호출 없이 코인 충전.
    """
```

---

## 프론트엔드 UI

### credit_ui.py 주요 함수

#### 1. render_hard_lock_screen()
```python
def render_hard_lock_screen(
    user_id: str,
    current_credits: int = 0,
    required_credits: int = 1,
    feature_name: str = "이 기능"
) -> None:
    """
    코인 부족 시 하드 락 화면 렌더링.
    - 현재 잔액 표시
    - 플랜 안내
    - 충전 버튼 (베이직/프로)
    """
```

**UI 구성**:
- 🔒 코인 부족 헤더
- 💰 현재 보유 코인 표시
- 📦 플랜 안내 (베이직/프로)
- 💳 즉시 충전 버튼

#### 2. check_credits_and_lock()
```python
def check_credits_and_lock(
    user_id: str,
    required_credits: int = 1,
    feature_name: str = "이 기능"
) -> bool:
    """
    코인 잔액 확인 및 부족 시 하드 락 화면 표시.
    
    Returns:
        True: 코인 충분 (기능 사용 가능)
        False: 코인 부족 (하드 락 화면 표시됨)
    """
```

**사용 예시**:
```python
# 기능 진입 전 코인 체크
if not check_credits_and_lock(user_id, required_credits=3, feature_name="AI 타겟 추천"):
    return  # 하드 락 화면 표시됨

# 코인 충분 → 기능 실행
run_ai_targeting_feature()

# 기능 사용 후 코인 차감
deduct_credits(user_id, amount=3, description="AI 타겟 추천 사용")
```

#### 3. deduct_credits()
```python
def deduct_credits(user_id: str, amount: int, description: str = "") -> bool:
    """
    코인 차감 처리.
    - gk_members.current_credits 차감
    - gk_credit_history에 내역 기록
    - 세션 상태 업데이트
    """
```

---

## 테스트 방법

### 1. 데이터베이스 스키마 적용

**Supabase SQL Editor에서 실행**:
```bash
d:\CascadeProjects\gk_iap_billing_schema.sql
```

**확인**:
```sql
-- 테이블 생성 확인
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('gk_purchases', 'gk_credit_history');

-- 함수 생성 확인
SELECT routine_name FROM information_schema.routines 
WHERE routine_schema = 'public' 
  AND routine_name = 'grant_coins_from_iap';
```

### 2. 시뮬레이션 테스트 실행

**테스트 스크립트 실행**:
```bash
python test_iap_simulation.py
```

**예상 출력**:
```
[STEP 1] 초기 코인 잔액 조회
✅ 현재 잔액: 0 코인

[STEP 2] 베이직 플랜 충전 시뮬레이션 (+50 코인)
✅ 충전 성공!
   - 충전 코인: 50 코인
   - 충전 전: 0 코인
   - 충전 후: 50 코인

[STEP 3] 중복 결제 방지 테스트
✅ 중복 결제 차단 성공!
   - 에러 메시지: 이미 처리된 결제입니다.

[STEP 4] 프로 플랜 충전 시뮬레이션 (+300 코인)
✅ 충전 성공!
   - 충전 후: 350 코인
```

### 3. UI 통합 테스트

**CRM 앱에서 테스트**:
```python
# crm_app_impl.py 또는 해당 기능 화면

from modules.credit_ui import check_credits_and_lock, deduct_credits

def render_ai_targeting_feature(user_id: str):
    # 코인 체크 (3코인 필요)
    if not check_credits_and_lock(user_id, required_credits=3, feature_name="AI 타겟 추천"):
        return  # 하드 락 화면 자동 표시
    
    # 기능 실행
    st.write("AI 타겟 추천 기능 실행 중...")
    
    # 코인 차감
    if deduct_credits(user_id, amount=3, description="AI 타겟 추천 사용"):
        st.success("✅ 3 코인이 차감되었습니다.")
```

---

## 배포 체크리스트

### 1. 환경 변수 설정

**Cloud Run 환경 변수**:
```bash
GOOGLE_PLAY_CREDENTIALS_PATH=/path/to/service-account-key.json
```

**서비스 계정 권한**:
- Google Play Developer API 활성화
- `androidpublisher` 스코프 권한 부여

### 2. Supabase RLS 정책

```sql
-- gk_purchases 테이블 RLS
ALTER TABLE public.gk_purchases ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own purchases"
ON public.gk_purchases FOR SELECT
USING (user_id = auth.uid());

-- gk_credit_history 테이블 RLS
ALTER TABLE public.gk_credit_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own credit history"
ON public.gk_credit_history FOR SELECT
USING (user_id = auth.uid());
```

### 3. 보안 체크

- ✅ purchase_token PK 제약으로 중복 방지
- ✅ Supabase RPC 함수로 원자적 트랜잭션 보장
- ✅ Google Play API 서비스 계정 키 안전 보관
- ✅ 클라이언트에서 purchase_token만 전송 (민감 정보 제외)

### 4. 모니터링

**로그 확인 항목**:
- 결제 검증 실패율
- 중복 결제 시도 횟수
- 코인 충전 평균 처리 시간
- 하드 락 화면 노출 빈도

---

## 🎯 핵심 포인트

### 중복 방지 메커니즘
```
purchase_token (PK) → 동일 토큰 재사용 시 DB 제약 위반 → 충전 차단
```

### 원자적 트랜잭션
```sql
BEGIN;
  UPDATE gk_members SET current_credits = current_credits + 50;
  INSERT INTO gk_purchases (...);
  INSERT INTO gk_credit_history (...);
COMMIT;
```

### 실시간 UI 반영
```python
# 충전 성공 시
st.session_state['current_credits'] = new_balance
st.balloons()  # 폭죽 효과
st.rerun()     # 화면 새로고침 → 하드 락 해제
```

---

## 📞 문의

**개발자**: 이세윤  
**이메일**: insusite@gmail.com  
**전화**: 010-3074-2616

**최종 업데이트**: 2026년 3월 29일
