# ══════════════════════════════════════════════════════════════════════════════
# GP 다운그레이드 예약 시스템 구현 보고서
# Goldkey AI Masters 2026 - 유연한 플랜 전환 및 자산 보존
# 2026-03-30 작성
# ══════════════════════════════════════════════════════════════════════════════

## 📊 **구현 완료 현황**

### ✅ **1. 데이터베이스 스키마 확장**

**파일:** `d:\CascadeProjects\sql\gk_members_downgrade_schema.sql`

#### **next_plan_type 컬럼 추가**
```sql
ALTER TABLE gk_members
ADD COLUMN IF NOT EXISTS next_plan_type TEXT DEFAULT NULL;

COMMENT ON COLUMN gk_members.next_plan_type IS 
'다음 결제일부터 적용될 플랜 타입 (예약 다운그레이드용). 
NULL=변경 없음, BASIC=베이직 전환 예약, PRO=프로 전환 예약';
```

**핵심 특징:**
- 기본값: `NULL` (변경 없음)
- 값: `'BASIC'` 또는 `'PRO'`
- 인덱스: `idx_gk_members_next_plan_type` (월간 갱신 성능 최적화)

---

### ✅ **2. 다운그레이드 예약 함수 구현**

**파일:** `d:\CascadeProjects\modules\subscription_manager.py`

#### **A. schedule_downgrade() - 다운그레이드 예약**

**기능:**
- PRO → BASIC 플랜 전환 예약
- 즉시 권한을 뺏지 않고 `next_plan_type` 업데이트
- 다음 갱신일부터 자동 적용

**로직:**
```python
def schedule_downgrade(user_id: str, target_plan: str = "BASIC"):
    # 1. 현재 플랜 확인
    # 2. 유효성 검증 (활성 구독만 가능)
    # 3. next_plan_type 업데이트
    # 4. 예약 내역 기록 (gk_credit_history)
```

**반환값:**
```python
{
    "success": True,
    "renewal_date": "2026-04-30",
    "current_plan": "PRO",
    "target_plan": "BASIC",
    "message": "예약 완료: 2026-04-30까지 PRO 유지 → 다음 결제일부터 BASIC 전환"
}
```

---

#### **B. cancel_downgrade() - 예약 취소**

**기능:**
- 다운그레이드 예약 취소
- `next_plan_type`을 `NULL`로 설정

**로직:**
```python
def cancel_downgrade(user_id: str):
    # 1. next_plan_type = NULL
    # 2. 취소 내역 기록
```

---

### ✅ **3. 월간 갱신 엔진 업데이트**

**파일:** `d:\CascadeProjects\modules\subscription_manager.py`

#### **check_and_renew_subscription() 수정**

**추가된 로직:**

##### **STEP 1: next_plan_type 조회**
```python
result = sb.table('gk_members').select(
    'subscription_status, monthly_renewal_date, current_credits, 
     plan_type, next_plan_type'  # ← 추가
).eq('user_id', user_id).execute()

next_plan_type = member.get('next_plan_type')  # 다운그레이드 예약
```

##### **STEP 2: 갱신일 도래 시 플랜 전환**
```python
if today > renewal_date:
    # [GP-DOWNGRADE] next_plan_type이 있으면 플랜 전환 처리
    if next_plan_type:
        new_plan = next_plan_type
        coin_cost = 50 if new_plan == 'BASIC' else 150
        
        if current_credits >= coin_cost:
            # 코인 차감 후 플랜 전환
            new_credits = current_credits - coin_cost
            new_renewal = today + timedelta(days=30)
            
            sb.table('gk_members').update({
                'plan_type': new_plan,
                'next_plan_type': None,  # 예약 해제
                'subscription_status': 'active',
                'monthly_renewal_date': new_renewal.strftime('%Y-%m-%d'),
                'current_credits': new_credits
            }).eq('user_id', user_id).execute()
```

**핵심 특징:**
- 코인 부족 시 만료 처리 (플랜 전환 실패)
- 플랜 전환 내역 자동 기록 (`gk_credit_history`)
- 예약 자동 해제 (`next_plan_type = NULL`)

---

### ✅ **4. 과거 데이터 0코인 조회 권한 보존**

**파일:** `d:\CascadeProjects\modules\access_control.py`

#### **check_access() 함수 확장**

**추가된 파라미터:**
```python
def check_access(
    user_id: str, 
    step_number: int, 
    report_id: Optional[str] = None  # ← 추가
) -> Dict[str, Any]:
```

**Zero-Coin Legacy 로직:**
```python
# 프로 기능 검증
if required_tier == "pro":
    # 현재 프로 등급이면 허용
    if user_tier == "pro":
        return {"allowed": True, "legacy_access": False}
    
    # [GP-DOWNGRADE] 베이직이지만 과거 PRO 시절 생성한 리포트 조회는 허용
    if report_id and _check_legacy_report_access(user_id, report_id):
        return {
            "allowed": True,
            "legacy_access": True,  # ← 과거 데이터 접근
            "message": "과거 PRO 시절 생성한 리포트 (0코인 무료 조회)"
        }
```

---

#### **_check_legacy_report_access() - 과거 리포트 확인**

**검증 로직:**
```python
def _check_legacy_report_access(user_id: str, report_id: str) -> bool:
    # 1. gk_unified_reports 테이블에서 리포트 조회
    # 2. 본인이 생성한 리포트인지 확인
    # 3. PRO 전용 리포트 타입인지 확인
    #    - 'ai_strategy', 'ai_proposal', 'custom_report'
    # 4. 과거 데이터인지 확인 (created_at 존재 여부)
```

**보호 대상 리포트:**
- STEP 7: AI 전략 수립 리포트
- STEP 8: AI 감성 제안 리포트
- STEP 9: 1:1 맞춤 제안서

---

### ✅ **5. 다운그레이드 UI 모듈**

**파일:** `d:\CascadeProjects\modules\downgrade_ui.py`

#### **A. render_downgrade_ui() - 메인 UI**

**UI 구성:**

##### **1) 현재 구독 정보 표시**
```
📊 현재 구독 정보
• 현재 플랜: PRO
• 다음 갱신일: 2026-04-30
• 보유 코인: 250🪙
• 남은 기간: 15일
```

##### **2) 예약 상태에 따른 분기**

**Case A: 예약 없음 (PRO 사용자)**
```
💡 베이직 플랜으로 변경하시겠습니까?

베이직 플랜은 기본 상담 및 분석 기능을 제공하며, 
월 구독료가 50🪙으로 저렴합니다.

[⬇️ 베이직 플랜으로 변경 예약]
```

**Case B: 예약 완료**
```
✅ 다운그레이드 예약 완료

2026-04-30까지는 PRO 플랜 혜택이 유지되며,
다음 결제일부터 BASIC 플랜으로 자동 전환됩니다.

💡 BASIC 플랜 월 구독료: 50🪙 (현재 보유: 250🪙)

[🔄 다운그레이드 예약 취소]
```

---

#### **B. render_legacy_report_badge() - 과거 리포트 배지**

**UI:**
```html
<span style='background:linear-gradient(135deg,#dbeafe,#bfdbfe);
             color:#1e40af;padding:3px 10px;border-radius:6px;'>
🔓 과거 PRO 리포트 (0🪙 무료 조회)
</span>
```

---

#### **C. check_and_show_legacy_access() - 접근 권한 확인**

**베이직 사용자가 과거 PRO 리포트 조회 시:**
```
ℹ️ 과거 PRO 시절 생성한 리포트입니다

베이직 플랜으로 전환하셨지만, PRO 시절 생성한 리포트는 
0코인 무료 조회가 가능합니다. 자산이 보존됩니다! 🎉
```

---

## 🎯 **사용자 경험 시나리오**

### **시나리오 1: PRO → BASIC 다운그레이드 예약**

#### **Step 1: 마이페이지 접속**
- 사용자: PRO 플랜 (월 150🪙)
- 갱신일: 2026-04-30 (15일 남음)
- 보유 코인: 250🪙

#### **Step 2: 다운그레이드 예약 버튼 클릭**
```
[⬇️ 베이직 플랜으로 변경 예약]
```

#### **Step 3: 예약 완료 알림**
```
✅ 예약 완료: 2026-04-30까지 PRO 유지 → 다음 결제일부터 BASIC 전환

• 현재 플랜: PRO
• 전환 예정: BASIC
• 적용일: 2026-04-30

💡 2026-04-30까지는 PRO 플랜 혜택이 계속 유지됩니다.
```

#### **Step 4: 갱신일 도래 (2026-04-30)**
- 자동 실행: `check_and_renew_subscription()`
- 플랜 전환: PRO → BASIC
- 코인 차감: 50🪙 (BASIC 월 구독료)
- 새 갱신일: 2026-05-30
- 보유 코인: 200🪙 (250 - 50)

---

### **시나리오 2: 과거 PRO 리포트 무료 조회**

#### **Step 1: 베이직 플랜으로 전환 완료**
- 사용자: BASIC 플랜
- 과거: PRO 시절 AI 전략 리포트 10개 생성

#### **Step 2: 과거 리포트 목록 조회**
```
📊 내 리포트 목록

1. [AI 전략] 홍길동님 보장 분석 (2026-03-15)
   🔓 과거 PRO 리포트 (0🪙 무료 조회)
   
2. [AI 제안서] 김철수님 맞춤 제안 (2026-03-20)
   🔓 과거 PRO 리포트 (0🪙 무료 조회)
```

#### **Step 3: 리포트 클릭 시**
```
ℹ️ 과거 PRO 시절 생성한 리포트입니다

베이직 플랜으로 전환하셨지만, PRO 시절 생성한 리포트는 
0코인 무료 조회가 가능합니다. 자산이 보존됩니다! 🎉

[리포트 내용 전체 표시 - 코인 차감 없음]
```

---

## 📋 **수정/생성된 파일 목록**

| 파일 | 유형 | 내용 |
|------|------|------|
| `sql/gk_members_downgrade_schema.sql` | 신규 | next_plan_type 컬럼 추가 SQL |
| `modules/subscription_manager.py` | 수정 | 다운그레이드 예약/취소 함수 + 월간 갱신 로직 |
| `modules/access_control.py` | 수정 | 과거 리포트 0코인 조회 권한 |
| `modules/downgrade_ui.py` | 신규 | 다운그레이드 UI 모듈 |

---

## 🔧 **기술 스택**

### **A. 데이터베이스 스키마**
```sql
-- gk_members 테이블
next_plan_type TEXT DEFAULT NULL  -- 예약 플랜

-- gk_credit_history 테이블 (action_type 추가)
'PLAN_DOWNGRADE_SCHEDULED'  -- 다운그레이드 예약
'PLAN_DOWNGRADE_CANCELLED'  -- 예약 취소
'PLAN_CHANGED'              -- 플랜 전환 완료
```

### **B. 월간 갱신 로직**
```python
# 갱신일 도래 시
if today > renewal_date and next_plan_type:
    # 1. 코인 확인 (BASIC=50, PRO=150)
    # 2. 코인 차감 후 플랜 전환
    # 3. next_plan_type = NULL (예약 해제)
    # 4. 새 갱신일 설정 (30일 후)
```

### **C. 권한 검증 로직**
```python
# 베이직 사용자가 PRO 리포트 조회 시
if report_id and _check_legacy_report_access(user_id, report_id):
    # 과거 PRO 시절 생성 → 0코인 무료 조회 허용
    return {"allowed": True, "legacy_access": True}
```

---

## 📊 **자산 보존 정책**

### **보존 대상**
1. **코인 잔액**: 100% 보존 (다운그레이드 후에도 유지)
2. **과거 PRO 리포트**: 0코인 무료 조회 영구 허용
3. **고객 데이터**: 전체 보존 (people, policies, relationships)
4. **상담 이력**: 전체 보존 (gk_schedules, gk_consultations)

### **보존되지 않는 것**
1. **PRO 기능 신규 사용**: 차단 (업그레이드 필요)
2. **AI 전략 수립**: 신규 생성 불가
3. **AI 제안서**: 신규 생성 불가

---

## 🎨 **UI 디자인 가이드**

### **색상 체계**

| 상태 | 배경색 | 테두리색 | 용도 |
|------|--------|----------|------|
| 현재 구독 정보 | `#f0f9ff` → `#e0f2fe` | `#0ea5e9` | 정보 전달 |
| 예약 완료 | `#fef3c7` → `#fde68a` | `#f59e0b` | 성공 알림 |
| 과거 리포트 배지 | `#dbeafe` → `#bfdbfe` | `#93c5fd` | 자산 보존 강조 |

### **버튼 디자인**
- 예약 버튼: `type="primary"` (파란색)
- 취소 버튼: `type="secondary"` (회색)
- 전체 폭: `use_container_width=True`

---

## 🏆 **핵심 성과**

### ✅ **완료된 작업**
1. ✅ `next_plan_type` 컬럼 추가 (SQL 스키마)
2. ✅ 다운그레이드 예약/취소 함수 구현
3. ✅ 월간 갱신 엔진 업데이트 (자동 플랜 전환)
4. ✅ 과거 데이터 0코인 조회 권한 보존
5. ✅ 다운그레이드 UI 모듈 생성
6. ✅ 코인 잔액 100% 보존 검증

### 🎯 **설계자 의도 반영**
- **"즉시 권한을 뺏지 않고"** → 갱신일까지 PRO 혜택 유지
- **"자산 보존"** → 과거 리포트 0코인 무료 조회
- **"유연한 다운그레이드"** → 예약/취소 자유롭게 가능

---

## 🚀 **향후 작업 (TODO)**

### **A. 마이페이지 통합**
```python
# my_page.py 또는 구독 관리 모듈에 추가
from modules.downgrade_ui import render_downgrade_ui

def render_my_page(user_id):
    st.title("마이페이지")
    
    # 구독 관리 섹션
    with st.expander("📊 구독 관리", expanded=True):
        render_downgrade_ui(user_id)
```

### **B. 리포트 목록에 배지 추가**
```python
from modules.downgrade_ui import render_legacy_report_badge

# 리포트 목록 렌더링 시
for report in reports:
    st.markdown(f"**{report['title']}**")
    if is_legacy_report(report['id']):
        render_legacy_report_badge()
```

### **C. Cloud Function 배포**
- 자정 자동 갱신 로직 Cloud Scheduler 연동
- `check_and_renew_subscription()` 전체 회원 대상 실행

---

## 📝 **보고서 작성자**
- **작성일:** 2026-03-30
- **작성자:** Windsurf AI (Cascade)
- **검토자:** 설계자 (이세윤)
- **버전:** v1.0

---

**"유연한 다운그레이드와 자산 보존 로직이 완성되었습니다. 프로 사용자가 베이직 변경을 예약했을 때의 UI 흐름이 구현되었습니다."** ✅
