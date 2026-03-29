# ✅ [GP-TACTICAL-2] AI 감성 프롬프트 주입 및 다이내믹 분석 UI 고도화 완료 보고서

**작성일**: 2026-03-29 09:52  
**우선순위**: 🟢 COMPLETED — STEP 6-9 영업 친화적 UI 구현  
**적용 범위**: modules/ai_engine.py, blocks/crm_coverage_analysis_block.py

---

## 📋 요약 (Executive Summary)

고객 상세 화면 내부의 분석 결과 화면(STEP 6-9 구간)을 영업 친화적으로 고도화했습니다.

### ✅ 구현 완료 사항

1. **AI 감성 프롬프트 튜닝** — 기계적 리포트 말투 → 1:1 대화형 감성 언어 ✅
2. **3단 보장 일람표 (STEP 8)** — DataFrame 테이블로 [현재|부족|제안] 3컬럼 시각화 ✅
3. **다이내믹 필터링 UI (STEP 7)** — st.pills로 보험 종목별 즉시 필터링 ✅
4. **트리니티 수식 보존** — 기존 분석 연산 로직 완전 보존 ✅

---

## 🔧 구현 세부사항

### 1. AI 감성 프롬프트 튜닝

**파일**: `d:\CascadeProjects\modules\ai_engine.py`  
**라인**: 32-45 (system_instruction 전면 수정)

#### Before (기계적 리포트 말투)
```python
master_instruction = "당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요."
```

#### After (1:1 대화형 감성 언어)
```python
master_instruction = """당신은 30년 경력의 '마스터 AI'입니다. 

[감성 대화 원칙 - 필수 준수]
1. 기계적인 리포트 말투를 절대 사용하지 마세요.
2. 고객과 1:1로 대화하듯이 감성적이고 공감하는 언어를 사용하세요.
3. 부족한 보장을 설명할 때는 반드시 "고객님, 이 부분의 위험이 진심으로 걱정됩니다"와 같은 감성 표현을 포함하세요.
4. "~입니다", "~됩니다" 같은 딱딱한 표현보다는 "~하시면 좋겠습니다", "~해 주시길 바랍니다" 같은 부드러운 권유형 표현을 사용하세요.
5. 고객의 마음을 움직이는 화법으로 제안하되, 정중한 '하십시오체'를 유지하세요.
6. 실시간 정보를 기반으로 CFP 수준의 전문성을 유지하되, 따뜻한 감성을 잃지 마세요.

예시:
- ❌ "암 진단비 보장이 부족합니다."
- ✅ "고객님, 현재 암 진단비 보장이 많이 부족한 상황이라 진심으로 걱정됩니다. 만약의 상황에서 경제적 어려움이 가중될 수 있어 마음이 무겁습니다."
"""
```

**특징**:
- 6가지 감성 대화 원칙 명시
- 구체적인 예시 제공 (❌/✅ 비교)
- "진심으로 걱정됩니다", "마음이 무겁습니다" 등 감성 표현 강제
- 권유형 표현 ("~하시면 좋겠습니다") 권장

---

### 2. 3단 보장 일람표 (STEP 8)

**파일**: `d:\CascadeProjects\blocks\crm_coverage_analysis_block.py`  
**함수**: `render_coverage_comparison_table()` (Line 15-110)

#### 테이블 구조

| 보장 항목 | 현재 가입금액 (만원) | 부족한 금액 (만원) | AI 제안금액 (만원) | 종목 |
|----------|---------------------|-------------------|-------------------|------|
| 암 진단비 | 3,000 | 2,000 | 5,000 | 장기 |
| 뇌혈관 진단비 | 2,000 | 3,000 | 5,000 | 장기 |
| 심장 진단비 | 1,000 | 4,000 | 5,000 | 장기 |

#### 스타일링

```css
/* 헤더 - 그라디언트 배경 */
.coverage-table thead tr {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    font-weight: 700;
}

/* 금액 컬럼 색상 구분 */
.coverage-table td:nth-child(2) {
    color: #dc2626;  /* 현재 가입금액 - 빨강 */
}
.coverage-table td:nth-child(3) {
    color: #f59e0b;  /* 부족한 금액 - 주황 */
}
.coverage-table td:nth-child(4) {
    color: #059669;  /* AI 제안금액 - 초록 */
}

/* 호버 효과 */
.coverage-table tbody tr:hover {
    background-color: #f3f4f6;
}
```

**특징**:
- pandas DataFrame → HTML 테이블 변환
- 3컬럼 명확한 색상 구분 (빨강/주황/초록)
- 그라디언트 헤더 (보라색 계열)
- 금액 우측 정렬 + 천단위 콤마
- 호버 효과로 가독성 향상

---

#### 감성 메시지 자동 생성

```python
total_shortage = sum(item.get("shortage_amount", 0) for item in coverage_data)
if total_shortage > 0:
    st.markdown(
        f"<div style='background:#fef3c7;border-left:4px solid #f59e0b;"
        "border-radius:8px;padding:14px 16px;margin-top:16px;'>"
        "<div style='font-size:0.88rem;font-weight:700;color:#92400e;margin-bottom:6px;'>"
        f"💬 {customer_name}님께 드리는 진심 어린 조언</div>"
        "<div style='font-size:0.82rem;color:#78350f;line-height:1.7;'>"
        f"고객님, 현재 <b style='color:#dc2626;'>총 {total_shortage:,}만원</b>의 보장이 부족한 상황입니다. "
        "이 부분의 위험이 진심으로 걱정됩니다. 만약의 상황에서 경제적 어려움이 가중될 수 있어 "
        "마음이 무겁습니다. 아래 AI 제안금액을 참고하시어 보장을 보강해 주시길 간곡히 부탁드립니다."
        "</div></div>",
        unsafe_allow_html=True,
    )
```

**특징**:
- 부족 금액 자동 합산
- 감성 표현 자동 삽입 ("진심으로 걱정됩니다", "마음이 무겁습니다")
- 노란색 배경 + 주황색 왼쪽 보더
- 고객 이름 개인화

---

### 3. 다이내믹 필터링 UI (STEP 7)

**파일**: `d:\CascadeProjects\blocks\crm_coverage_analysis_block.py`  
**함수**: `render_insurance_type_filter()` (Line 113-165)

#### UI 구조

```
🔍 보험 종목별 필터링
아래 버튼을 선택하여 특정 종목만 보거나 전체를 볼 수 있습니다.

[전체] [장기] [자동차] [화재] [운전자] [연금] [암]
```

#### 구현 코드

```python
# st.pills 사용 (Streamlit 1.35+)
try:
    selected_types = st.pills(
        "보험 종목 선택",
        options=["전체"] + available_types,
        selection_mode="multi",
        key=filter_key,
        label_visibility="collapsed",
    )
except AttributeError:
    # st.pills 미지원 시 st.multiselect 폴백
    selected_types = st.multiselect(
        "보험 종목 선택",
        options=["전체"] + available_types,
        default=["전체"],
        key=filter_key,
        label_visibility="collapsed",
    )
```

**특징**:
- `st.pills` 우선 사용 (최신 Streamlit)
- 미지원 시 `st.multiselect` 자동 폴백
- "전체" 선택 시 모든 종목 표시
- 다중 선택 가능 (`selection_mode="multi"`)
- 세션 상태 연동 (`key=filter_key`)

---

#### 필터링 로직

```python
# 필터링된 데이터
filtered_data = [
    item for item in coverage_data
    if item.get("insurance_type") in selected_types
]

if not filtered_data:
    st.warning("선택한 종목에 해당하는 보장 데이터가 없습니다.")
    return

# 3단 일람표 렌더링
render_coverage_comparison_table(filtered_data, customer_name)
```

**특징**:
- 실시간 필터링 (버튼 클릭 즉시 반영)
- 빈 결과 처리 (경고 메시지)
- 필터링 후 즉시 테이블 렌더링

---

### 4. 통합 렌더링 함수

**함수**: `render_filtered_coverage_analysis()` (Line 168-200)

```python
def render_filtered_coverage_analysis(
    coverage_data: list[dict],
    customer_name: str = "고객",
    filter_key: str = "coverage_filter",
) -> None:
    """
    [STEP 7 + STEP 8] 통합 렌더링: 필터링 UI + 3단 일람표.
    """
    # STEP 7: 필터링 UI
    selected_types = render_insurance_type_filter(coverage_data, filter_key)
    
    # 필터링된 데이터
    filtered_data = [
        item for item in coverage_data
        if item.get("insurance_type") in selected_types
    ]
    
    # STEP 8: 3단 일람표
    render_coverage_comparison_table(filtered_data, customer_name)
```

**사용법**:
```python
from blocks.crm_coverage_analysis_block import render_filtered_coverage_analysis

# 보장 분석 데이터 준비
coverage_data = [
    {
        "category": "암 진단비",
        "current_amount": 3000,
        "shortage_amount": 2000,
        "recommended_amount": 5000,
        "insurance_type": "장기",
    },
    # ... 더 많은 데이터
]

# 통합 렌더링 (필터링 + 테이블)
render_filtered_coverage_analysis(
    coverage_data=coverage_data,
    customer_name="홍길동",
    filter_key="my_coverage_filter",
)
```

---

## 📊 샘플 데이터 생성 함수

**함수**: `generate_sample_coverage_data()` (Line 203-260)

```python
def generate_sample_coverage_data() -> list[dict]:
    """테스트용 샘플 보장 데이터 생성."""
    return [
        {
            "category": "암 진단비",
            "current_amount": 3000,
            "shortage_amount": 2000,
            "recommended_amount": 5000,
            "insurance_type": "장기",
        },
        # ... 8개 샘플 데이터
    ]
```

**사용법**:
```python
# 테스트용 샘플 데이터 생성
sample_data = generate_sample_coverage_data()

# 렌더링
render_filtered_coverage_analysis(
    coverage_data=sample_data,
    customer_name="테스트 고객",
)
```

---

## 🎯 GP 가이드라인 준수 사항

### ✅ 감성/후킹 프롬프트 튜닝

**지시사항**:
> "AI가 부족 보장을 설명할 때 기계적인 리포트 말투를 버려라. 결과 출력 시 **'고객님, 이 부분의 위험이 진심으로 걱정됩니다'**와 같은 1:1 대화형 감성 언어를 반드시 포함하도록 시스템 프롬프트(Prompt)를 전면 수정하라."

**구현**:
- ✅ system_instruction 전면 수정 (6가지 감성 대화 원칙)
- ✅ 구체적 예시 제공 (❌/✅ 비교)
- ✅ "진심으로 걱정됩니다", "마음이 무겁습니다" 등 감성 표현 강제
- ✅ 권유형 표현 권장 ("~하시면 좋겠습니다")

---

### ✅ 3단 보장 일람표 렌더링

**지시사항**:
> "분석 결과를 단순히 텍스트 줄글로 나열하지 마라. 반드시 [현재 가입금액 | 부족한 금액 | AI 제안금액] 3개 컬럼을 가진 명확한 표(DataFrame 또는 Markdown Table)로 화면에 시각화하여 노출하라."

**구현**:
- ✅ pandas DataFrame → HTML 테이블 변환
- ✅ 3컬럼 명확한 색상 구분 (빨강/주황/초록)
- ✅ 천단위 콤마 + 우측 정렬
- ✅ 그라디언트 헤더 + 호버 효과

---

### ✅ 보험 종목별 다이내믹 필터링 UI

**지시사항**:
> "일람표 상단에 [장기], [자동차], [화재], [운전자], [연금], [암] 키워드로 즉시 필터링/정렬할 수 있는 선택 버튼(st.multiselect 또는 st.pills)을 배치하라. 버튼 선택 시 하단 분석 데이터가 즉시 해당 종목만 소팅(정렬)되어 보이도록 세션 상태를 연동하라."

**구현**:
- ✅ st.pills 우선 사용 (최신 Streamlit)
- ✅ st.multiselect 폴백 (하위 호환)
- ✅ 다중 선택 가능 (`selection_mode="multi"`)
- ✅ 세션 상태 연동 (`key=filter_key`)
- ✅ 실시간 필터링 (버튼 클릭 즉시 반영)

---

### ✅ 트리니티 수식 보존

**지시사항**:
> "(주의: 트리니티 수식 등 기존 분석 연산 로직은 절대 건드리지 말고 보존할 것)"

**구현**:
- ✅ 기존 trinity_engine.py 무손상
- ✅ 기존 hq_app_impl.py KB 7대 분석 로직 무손상
- ✅ 새로운 블록 파일 생성 (crm_coverage_analysis_block.py)
- ✅ UI 렌더링만 추가, 연산 로직 변경 없음

---

## ✅ 구문 검사 완료

```
modules/ai_engine.py: SYNTAX OK
blocks/crm_coverage_analysis_block.py: SYNTAX OK
```

---

## 🚀 배포 상태

### 파일 변경 요약
- **수정**: `d:\CascadeProjects\modules\ai_engine.py` (Line 32-45)
- **신규**: `d:\CascadeProjects\blocks\crm_coverage_analysis_block.py` (260줄)

### 배포 대기
- HQ 앱: modules/ai_engine.py 포함
- CRM 앱: blocks/crm_coverage_analysis_block.py 포함

---

## 📱 사용 예시

### CRM 앱에서 통합 렌더링

```python
# crm_app_impl.py 또는 blocks/crm_trinity_block.py

from blocks.crm_coverage_analysis_block import (
    render_filtered_coverage_analysis,
    generate_sample_coverage_data,
)

# 고객 상세 화면 내부
if st.session_state.get("_crm_spa_screen") == "analysis":
    st.markdown("### 📊 보장 분석 결과")
    
    # 보장 분석 데이터 준비 (실제로는 trinity_engine.py에서 가져옴)
    coverage_data = generate_sample_coverage_data()  # 테스트용
    
    # STEP 7 + STEP 8 통합 렌더링
    render_filtered_coverage_analysis(
        coverage_data=coverage_data,
        customer_name=sel_cust.get("name", "고객"),
        filter_key="crm_coverage_filter",
    )
```

---

## 📋 UI 렌더링 상태 확인

### 필터링 UI (STEP 7)
- [ ] 파스텔 블루 배경 (#f0f9ff) 정상 렌더링
- [ ] st.pills 버튼 정상 표시 (또는 st.multiselect 폴백)
- [ ] "전체" 선택 시 모든 종목 표시
- [ ] 특정 종목 선택 시 즉시 필터링

### 3단 일람표 (STEP 8)
- [ ] 그라디언트 헤더 (보라색 계열) 표시
- [ ] 3컬럼 색상 구분 (빨강/주황/초록)
- [ ] 천단위 콤마 정상 표시
- [ ] 호버 효과 작동
- [ ] 감성 메시지 박스 (노란색 배경) 표시

### 감성 프롬프트 (AI 응답)
- [ ] "고객님, 이 부분의 위험이 진심으로 걱정됩니다" 표현 포함
- [ ] 권유형 표현 ("~하시면 좋겠습니다") 사용
- [ ] 기계적 리포트 말투 제거

---

## ✅ 결론

**AI 감성 프롬프트 주입 및 다이내믹 분석 UI 고도화 완료**:

1. ✅ **AI 감성 프롬프트** — 6가지 원칙 + 구체적 예시로 1:1 대화형 언어 강제
2. ✅ **3단 보장 일람표** — DataFrame 테이블로 [현재|부족|제안] 3컬럼 시각화
3. ✅ **다이내믹 필터링** — st.pills로 보험 종목별 즉시 필터링
4. ✅ **감성 메시지** — 부족 금액 자동 합산 + 감성 표현 자동 삽입
5. ✅ **트리니티 수식 보존** — 기존 분석 연산 로직 완전 무손상
6. ✅ **샘플 데이터** — 테스트용 샘플 생성 함수 제공

**다음 단계**:
1. CRM 앱에 통합 (crm_app_impl.py 또는 blocks/crm_trinity_block.py)
2. 실제 보장 분석 데이터 연동 (trinity_engine.py)
3. 배포 후 UI 렌더링 검증

---

**작성자**: Cascade AI  
**상태**: 🟢 구현 완료 — 통합 및 배포 대기  
**검증 필요**: 배포 후 모바일/PC 렌더링 + AI 응답 감성 표현 확인
