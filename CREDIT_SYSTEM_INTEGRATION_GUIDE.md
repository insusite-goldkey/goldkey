# 제14조 크레딧 과금 시스템 통합 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [credit_manager.py 함수 사용법](#credit_managerpy-함수-사용법)
3. [UI 버튼 통합 방법](#ui-버튼-통합-방법)
4. [12단계 파이프라인 적용 예시](#12단계-파이프라인-적용-예시)
5. [코인 차감 규칙](#코인-차감-규칙)

---

## 시스템 개요

### 제14조 약관 기반 과금 정책

#### 1코인 구간 (베이직 플랜)
- 신규 고객 증권 스캔
- 최초 3단 일람표 생성
- 데이터 추출 및 계산

#### 3코인 구간 (프로 플랜)
- 에이젠틱 AI 기반 영업 전략 생성
- 카톡 오프닝 멘트 작문
- AI 추천 타겟팅

#### 0코인 (평생 무료 조회)
- 이미 코인을 지불하여 분석이 완료되고 DB에 저장된 고객의 결과 데이터를 다시 열람하는 행위

---

## credit_manager.py 함수 사용법

### 1. 기본 크레딧 확인 및 차감

```python
from modules.credit_manager import check_and_deduct_credit

# 코인 확인 및 차감
if check_and_deduct_credit(
    user_id=agent_id,
    required_coins=1,
    reason="증권 스캔 및 3단 일람표 생성"
):
    # 코인 차감 성공 → 기능 실행
    result = perform_scan_analysis()
else:
    # 코인 부족 → 하드 락 (자동으로 에러 메시지 표시됨)
    return
```

### 2. 0코인 방어 로직 (기존 결과 조회)

```python
from modules.credit_manager import get_existing_analysis, save_analysis_result

# 1. 기존 분석 결과 확인
existing = get_existing_analysis(
    person_id=customer_id,
    analysis_type='SCAN',
    agent_id=agent_id
)

if existing:
    st.success("✅ 저장된 분석 데이터를 무료로 불러왔습니다. (🪙 0 차감)")
    display_result(existing['result_data'])
    return

# 2. 없으면 코인 차감 후 분석
if check_and_deduct_credit(agent_id, 1, "증권 스캔"):
    result = perform_scan_analysis()
    
    # 3. 결과 저장 (다음엔 무료)
    save_analysis_result(
        person_id=customer_id,
        agent_id=agent_id,
        analysis_type='SCAN',
        result_data=result,
        coins_used=1
    )
    
    display_result(result)
```

### 3. 통합 분석 실행 함수 (권장)

```python
from modules.credit_manager import run_analysis_with_credit_control

# 0코인 방어 + 차감 + 저장을 한 번에 처리
result = run_analysis_with_credit_control(
    user_id=agent_id,
    person_id=customer_id,
    analysis_type='TRINITY',
    analysis_function=perform_trinity_analysis,
    required_coins=3,
    reason="에이젠틱 AI 전략 생성",
    # analysis_function에 전달할 파라미터
    customer_data=customer_data,
    policy_data=policy_data
)

if result:
    display_result(result)
```

---

## UI 버튼 통합 방법

### 방법 1: render_coin_button() 사용 (권장)

```python
from modules.credit_manager import render_coin_button

# 1코인 버튼
if render_coin_button(
    label="🔍 스캔 및 분석하기",
    required_coins=1,
    key="btn_scan_analysis",
    button_type="secondary"
):
    # 버튼 클릭됨 → 분석 실행
    run_scan_analysis()

# 3코인 버튼
if render_coin_button(
    label="🤖 에이젠틱 AI 전략 생성",
    required_coins=3,
    key="btn_ai_strategy",
    button_type="primary"
):
    # 버튼 클릭됨 → AI 전략 생성
    run_ai_strategy()
```

**자동 처리 사항**:
- ✅ 코인 부족 시 버튼 자동 비활성화 (`disabled=True`)
- ✅ 버튼 라벨에 코인 표시 자동 추가 (`🪙 -1`, `🪙 -3`)
- ✅ 부족 시 `🔒` 아이콘 및 부족 수량 표시

### 방법 2: 수동 구현

```python
import streamlit as st

current_credits = st.session_state.get('current_credits', 0)
required_coins_1 = 1
is_locked_1 = current_credits < required_coins_1

if st.button(
    f"🔍 스캔 및 분석하기 (🪙 -{required_coins_1})",
    disabled=is_locked_1,
    key="btn_scan"
):
    # 버튼 클릭 시 로직
    if check_and_deduct_credit(agent_id, required_coins_1, "스캔 분석"):
        run_scan_analysis()
```

---

## 12단계 파이프라인 적용 예시

### STEP 4: 통합 스캔 (1코인)

```python
# blocks/crm_scan_block.py 또는 해당 UI 컴포넌트

from modules.credit_manager import render_coin_button, run_analysis_with_credit_control

def render_scan_interface(agent_id: str, person_id: str):
    st.markdown("### 📸 증권 스캔 및 분석")
    
    # 1코인 버튼
    if render_coin_button(
        label="🔍 스캔 시작",
        required_coins=1,
        key="btn_start_scan"
    ):
        # 0코인 방어 + 차감 + 저장 자동 처리
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='SCAN',
            analysis_function=perform_ocr_scan,
            required_coins=1,
            reason="증권 OCR 스캔 및 3단 일람표 생성",
            uploaded_file=uploaded_file
        )
        
        if result:
            st.success("✅ 스캔 완료!")
            display_scan_result(result)
```

### STEP 5: AI 3중 분석 (3코인)

```python
# modules/analysis_hub.py 또는 해당 분석 모듈

from modules.credit_manager import run_analysis_with_credit_control

def render_trinity_analysis(agent_id: str, person_id: str):
    st.markdown("### 🤖 AI 트리니티 분석")
    
    # 3코인 버튼
    if render_coin_button(
        label="🎯 AI 분석 시작",
        required_coins=3,
        key="btn_trinity_analysis",
        button_type="primary"
    ):
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='TRINITY',
            analysis_function=run_trinity_engine,
            required_coins=3,
            reason="AI 트리니티 엔진 분석",
            customer_data=get_customer_data(person_id)
        )
        
        if result:
            st.balloons()
            display_trinity_result(result)
```

### STEP 9: 감성 제안 (3코인)

```python
# modules/closing_engine.py

from modules.credit_manager import render_coin_button, check_and_deduct_credit

def render_emotional_proposal(agent_id: str, person_id: str):
    st.markdown("### 💌 감성 제안서 생성")
    
    if render_coin_button(
        label="✨ 감성 제안서 작성",
        required_coins=3,
        key="btn_emotional_proposal"
    ):
        # 기존 결과 확인
        existing = get_existing_analysis(person_id, 'EMOTIONAL_PROPOSAL', agent_id)
        
        if existing:
            st.success("✅ 저장된 제안서를 불러왔습니다. (🪙 0)")
            display_proposal(existing['result_data'])
        else:
            # 코인 차감 (이미 render_coin_button에서 확인됨)
            if check_and_deduct_credit(agent_id, 3, "감성 제안서 생성"):
                proposal = generate_emotional_proposal(person_id)
                save_analysis_result(person_id, agent_id, 'EMOTIONAL_PROPOSAL', proposal, 3)
                display_proposal(proposal)
```

### STEP 10: 카톡 1초 발송 (3코인)

```python
# modules/kakao_service.py

from modules.credit_manager import render_coin_button, run_analysis_with_credit_control

def render_kakao_message_generator(agent_id: str, person_id: str):
    st.markdown("### 💬 카카오톡 오프닝 멘트")
    
    if render_coin_button(
        label="📱 카톡 멘트 생성",
        required_coins=3,
        key="btn_kakao_message"
    ):
        result = run_analysis_with_credit_control(
            user_id=agent_id,
            person_id=person_id,
            analysis_type='KAKAO_MESSAGE',
            analysis_function=generate_kakao_opening_message,
            required_coins=3,
            reason="카카오톡 오프닝 멘트 AI 작문",
            customer_name=get_customer_name(person_id)
        )
        
        if result:
            st.text_area("생성된 메시지", value=result['message'], height=200)
            
            if st.button("📤 카카오톡 발송"):
                send_kakao_message(person_id, result['message'])
```

---

## 코인 차감 규칙

### 분석 유형별 코인 매핑

| 분석 유형 | analysis_type | 코인 | 설명 |
|----------|---------------|------|------|
| 증권 스캔 | `SCAN` | 1 | OCR 스캔 및 데이터 추출 |
| 3단 일람표 | `TABLE_3STEP` | 1 | 기초 보장 분석표 생성 |
| 트리니티 분석 | `TRINITY` | 3 | AI 3중 분석 엔진 |
| AI 타겟 추천 | `AI_TARGETING` | 3 | 에이젠틱 AI 타겟팅 |
| 감성 제안서 | `EMOTIONAL_PROPOSAL` | 3 | AI 감성 제안서 작문 |
| 카톡 멘트 | `KAKAO_MESSAGE` | 3 | 카카오톡 오프닝 멘트 |
| 비교 전략 | `COMPARISON_STRATEGY` | 3 | 보험사 비교 전략 생성 |

### 0코인 무료 조회 조건

**다음 조건을 모두 만족하면 0코인**:
1. `analysis_reports` 테이블에 해당 `person_id` + `analysis_type` 레코드 존재
2. 동일 `agent_id`로 조회 (본인이 이전에 분석한 고객)
3. `created_at` 기준 최신 레코드 조회

**예외 (코인 재차감)**:
- 다른 설계사가 동일 고객 분석 시 → 각자 코인 차감
- 고객 정보 변경 후 재분석 요청 시 → 새로운 분석으로 간주 (선택적)

---

## 하드 락 화면 예시

### 코인 부족 시 자동 표시

```python
# check_and_deduct_credit() 함수 내부에서 자동 처리

st.error(
    f"🚨 **잔여 코인이 부족합니다.**\n\n"
    f"• 필요 코인: **{required_coins} 🪙**\n"
    f"• 현재 잔액: **{current_credits} 🪙**\n\n"
    f"플랜을 업그레이드하거나 코인을 충전해 주세요."
)
```

### 충전 화면 연동

```python
from modules.credit_ui import render_hard_lock_screen

# 코인 부족 시 충전 화면 표시
if current_credits < required_coins:
    render_hard_lock_screen(
        user_id=agent_id,
        current_credits=current_credits,
        required_credits=required_coins,
        feature_name="AI 트리니티 분석"
    )
    return
```

---

## 세션 상태 관리

### 초기화

```python
# 로그인 시 또는 앱 시작 시
from modules.credit_manager import get_current_credits

if 'current_credits' not in st.session_state:
    st.session_state['current_credits'] = get_current_credits(user_id)
```

### 실시간 업데이트

```python
# 코인 차감/충전 시 자동으로 세션 업데이트됨
# check_and_deduct_credit() 내부에서 처리:
st.session_state['current_credits'] = new_credits
```

### 강제 새로고침

```python
# DB에서 최신 잔액 강제 조회
credits = get_current_credits(user_id, force_refresh=True)
```

---

## 배포 체크리스트

### 1. DB 스키마 확인

```sql
-- analysis_reports 테이블 존재 확인
SELECT table_name FROM information_schema.tables 
WHERE table_name = 'analysis_reports';

-- 필수 컬럼 확인
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'analysis_reports';
```

**필수 컬럼**:
- `person_id` (TEXT)
- `agent_id` (TEXT)
- `analysis_type` (TEXT)
- `result_data` (JSONB)
- `coins_used` (INTEGER)
- `created_at` (TIMESTAMPTZ)

### 2. 기존 코드 마이그레이션

**변경 전**:
```python
if st.button("🔍 스캔 시작"):
    result = perform_scan()
    display_result(result)
```

**변경 후**:
```python
if render_coin_button("🔍 스캔 시작", required_coins=1, key="btn_scan"):
    result = run_analysis_with_credit_control(
        user_id=agent_id,
        person_id=person_id,
        analysis_type='SCAN',
        analysis_function=perform_scan,
        required_coins=1,
        reason="증권 스캔"
    )
    if result:
        display_result(result)
```

### 3. 테스트 시나리오

1. ✅ 코인 충분 → 버튼 활성화 → 클릭 → 차감 → 결과 표시
2. ✅ 코인 부족 → 버튼 비활성화 → 경고 메시지
3. ✅ 기존 분석 존재 → 0코인 무료 조회
4. ✅ 분석 실패 → 코인 자동 환불
5. ✅ 충전 후 → 즉시 UI 갱신

---

## 📞 문의

**개발자**: 이세윤  
**이메일**: insusite@gmail.com  
**전화**: 010-3074-2616

**최종 업데이트**: 2026년 3월 29일
