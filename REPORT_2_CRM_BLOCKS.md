# CRM 블록별 기술 명세서

**Goldkey AI Masters 2026 — 17개 CRM 블록 상세 분석**  
**작성일**: 2026-03-30  
**목적**: 각 CRM 블록의 기술 스펙, 함수 시그니처, UI 컴포넌트, DB 연동, GCS 연동을 상세히 문서화

---

## 📋 목차

1. [crm_scan_block.py](#1-crm_scan_blockpy)
2. [crm_trinity_block.py](#2-crm_trinity_blockpy)
3. [crm_coverage_analysis_block.py](#3-crm_coverage_analysis_blockpy)
4. [crm_analysis_screen_block.py](#4-crm_analysis_screen_blockpy)
5. [crm_consultation_center_block.py](#5-crm_consultation_center_blockpy)
6. [crm_kakao_share_block.py](#6-crm_kakao_share_blockpy)
7. [crm_nibo_screen_block.py](#7-crm_nibo_screen_blockpy)
8. [crm_phase1_network_block.py](#8-crm_phase1_network_blockpy)
9. [crm_action_grid_block.py](#9-crm_action_grid_blockpy)
10. [crm_insurance_contracts_block.py](#10-crm_insurance_contracts_blockpy)
11. [crm_policy_cancellation_block.py](#11-crm_policy_cancellation_blockpy)
12. [crm_expiry_alerts_block.py](#12-crm_expiry_alerts_blockpy)
13. [crm_list_inline_panel_block.py](#13-crm_list_inline_panel_blockpy)
14. [crm_scan_vault_viewer.py](#14-crm_scan_vault_viewerpy)
15. [crm_hq_scan_bridge.py](#15-crm_hq_scan_bridgepy)
16. [crm_nav_block.py](#16-crm_nav_blockpy)
17. [zombie_tables_crud.py](#17-zombie_tables_crudpy)

---

## 1. crm_scan_block.py

### 기본 정보
- **파일명**: `crm_scan_block.py`
- **주요 함수**: `render_crm_scan_block()`
- **라인 수**: ~900줄
- **용도**: CRM 통합 스캔 사령부 (GCS-Supabase-HQ 4자 연동)

### 함수 시그니처
```python
def render_crm_scan_block(
    sel_pid: str,
    user_id: str,
    customer_name: str = ""
) -> None:
    """
    CRM 통합 스캔 사령부 블록 (GCS-Supabase-HQ 4자 연동).
    
    Args:
        sel_pid: 선택된 고객 person_id
        user_id: 현재 로그인한 설계사 ID
        customer_name: 고객 이름 (선택)
    """
```

### 주요 기능
1. **서류 종류 선택**
   - 보험증권
   - 의무기록
   - 지급결의서
   - 사고확인서
   - 기타 서류

2. **이미지 업로드**
   - `st.file_uploader()` 사용
   - 지원 포맷: JPG, PNG, PDF
   - 최대 파일 크기: 10MB

3. **OCR 처리**
   - Google Vision API 연동
   - 텍스트 자동 추출
   - 구조화된 데이터 파싱

4. **GCS 암호화 저장**
   - 경로: `gs://goldkey-scan-vault/{agent_id}/{person_id}/{doc_type}/{timestamp}.enc`
   - Fernet 암호화 적용
   - 메타데이터 태깅

5. **Supabase 메타데이터 등록**
   - 테이블: `gk_scan_files`
   - 필드: file_id, person_id, agent_id, doc_type, gcs_path, created_at

6. **HQ 동기화**
   - 스캔 완료 후 HQ 앱에 알림
   - `st.query_params` 통해 person_id 전달

### UI 컴포넌트
```python
# 서류 선택 라디오 버튼
doc_type = st.radio(
    "📄 서류 종류",
    ["보험증권", "의무기록", "지급결의서", "사고확인서", "기타"],
    horizontal=True
)

# 파일 업로더
uploaded_file = st.file_uploader(
    "📸 사진 촬영 또는 파일 선택",
    type=["jpg", "jpeg", "png", "pdf"],
    key=f"scan_uploader_{sel_pid}"
)

# 스캔 버튼
if st.button("🔍 AI 스캔 시작", type="primary"):
    with st.spinner("AI가 서류를 분석 중입니다..."):
        result = process_scan(uploaded_file, doc_type, sel_pid, user_id)
```

### 연결된 DB 테이블
- **gk_scan_files**: 스캔 파일 메타데이터
  - `file_id` (PK)
  - `person_id` (FK → people)
  - `agent_id` (FK → members)
  - `doc_type` (varchar)
  - `gcs_path` (text)
  - `ocr_result` (jsonb)
  - `created_at` (timestamp)

- **gk_unified_reports**: 분석 결과 저장
  - `report_id` (PK)
  - `person_id` (FK)
  - `report_type` (varchar: 'scan_result')
  - `report_data` (jsonb)

### GCS 연동
```python
def upload_scan_to_gcs(
    file_bytes: bytes,
    agent_id: str,
    person_id: str,
    doc_type: str
) -> str:
    """
    스캔 파일을 GCS에 암호화하여 업로드.
    
    Returns:
        gcs_path: gs://goldkey-scan-vault/...
    """
    # Fernet 암호화
    encrypted_data = cipher.encrypt(file_bytes)
    
    # GCS 업로드
    blob_name = f"{agent_id}/{person_id}/{doc_type}/{timestamp}.enc"
    bucket.blob(blob_name).upload_from_string(encrypted_data)
    
    return f"gs://goldkey-scan-vault/{blob_name}"
```

### 12단계 마스터플랜 연결
- **STEP 3**: 증권 및 의무기록 스캔
- **STEP 4**: OCR 자동 파싱
- **코인 차감**: 1🪙 (증권), 1🪙 (의무기록), 3🪙 (통합 분석)

### 에러 핸들링
```python
try:
    result = process_scan(uploaded_file, doc_type, sel_pid, user_id)
    st.success("✅ 스캔 완료!")
except Exception as e:
    st.error(f"❌ 스캔 실패: {str(e)}")
    logging.error(f"Scan error: {e}", exc_info=True)
```

### 세션 상태 관리
```python
if "scan_result" not in st.session_state:
    st.session_state.scan_result = None

if "scan_history" not in st.session_state:
    st.session_state.scan_history = []
```

---

## 2. crm_trinity_block.py

### 기본 정보
- **파일명**: `crm_trinity_block.py`
- **주요 함수**: `render_crm_trinity_block()`
- **라인 수**: ~500줄
- **용도**: 트리니티 가처분소득 산출기 + AI 청약 결과 리포트

### 함수 시그니처
```python
def render_crm_trinity_block(
    sel_cust: dict,
    sel_pid: str,
    user_id: str,
    ks_render_send_ui=None,
    kakao_sender_ok: bool = False,
    hq_app_url: str = "http://localhost:8501"
) -> None:
    """
    트리니티 산출기 블록.
    
    Args:
        sel_cust: 선택된 고객 정보 dict
        sel_pid: person_id
        user_id: 설계사 ID
        ks_render_send_ui: 카카오톡 전송 UI 렌더링 함수
        kakao_sender_ok: 카카오톡 전송 가능 여부
        hq_app_url: HQ 앱 URL (SSO 링크용)
    """
```

### 주요 기능
1. **트리니티 소득 계산**
   - 월 소득 입력
   - 고정비 입력 (주거비, 교육비, 생활비)
   - 가처분소득 자동 계산
   - 보험료 적정 비율 제안 (가처분소득의 10~15%)

2. **AI 청약 결과 리포트**
   - 고객 기본 정보 요약
   - 현재 가입 보험 현황
   - 월 보험료 합계
   - 관리 등급 (A/B/C/D)
   - AI 추천 보장 항목

3. **상담 브리핑 카드**
   - 고객명, 연령, 직업
   - 월 보험료
   - 계약 건수
   - 관리 등급

4. **HQ 연동 버튼**
   - "HQ에서 상세 분석" 버튼
   - SSO 토큰 생성
   - HQ 앱으로 리다이렉트

5. **카카오톡 전송**
   - 상담 결과 카카오톡 전송
   - 이미지 + 텍스트 조합

### UI 컴포넌트
```python
# 트리니티 입력 폼
with st.expander("💰 트리니티 소득 산출", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        monthly_income = st.number_input(
            "월 소득 (만원)",
            min_value=0,
            value=300,
            step=10
        )
    with col2:
        fixed_cost = st.number_input(
            "고정비 (만원)",
            min_value=0,
            value=150,
            step=10
        )
    
    disposable_income = monthly_income - fixed_cost
    recommended_premium = disposable_income * 0.12
    
    st.metric("가처분소득", f"{disposable_income:,}만원")
    st.metric("권장 보험료", f"{recommended_premium:,.0f}만원")

# 상담 브리핑 카드
st.markdown(f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px; border-radius: 15px; color: white;">
    <h3>📋 상담 브리핑</h3>
    <p><strong>고객명:</strong> {sel_cust['name']}</p>
    <p><strong>월 보험료:</strong> {total_premium:,}원</p>
    <p><strong>계약 건수:</strong> {contract_count}건</p>
    <p><strong>관리 등급:</strong> {tier}</p>
</div>
""", unsafe_allow_html=True)

# HQ 연동 버튼
if st.button("🔗 HQ에서 상세 분석", type="primary"):
    auth_token = generate_sso_token(user_id)
    hq_url = f"{hq_app_url}?auth_token={auth_token}&person_id={sel_pid}"
    st.markdown(f'<a href="{hq_url}" target="_blank">HQ 앱 열기</a>', 
                unsafe_allow_html=True)
```

### 연결된 DB 테이블
- **people**: 고객 기본 정보
- **policies**: 가입 보험 목록
- **gk_unified_reports**: 트리니티 결과 저장
  - `report_type`: 'trinity_result'
  - `report_data`: jsonb (월소득, 고정비, 가처분소득, 권장보험료)

### 12단계 마스터플랜 연결
- **STEP 2**: 트리니티 소득 산출
- **STEP 7**: AI 전략 수립
- **코인 차감**: 0🪙 (계산기), 3🪙 (AI 리포트 생성)

### SSO 토큰 생성
```python
def generate_sso_token(user_id: str) -> str:
    """
    HQ 앱 SSO 토큰 생성 (HMAC-SHA256).
    
    Returns:
        32자 hex 토큰
    """
    secret = get_env_secret("SSO_SECRET_KEY")
    message = f"{user_id}:{int(time.time())}"
    token = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return token
```

---

## 3. crm_coverage_analysis_block.py

### 기본 정보
- **파일명**: `crm_coverage_analysis_block.py`
- **주요 함수**: `render_coverage_comparison_table()`
- **라인 수**: ~400줄
- **용도**: 3단 보장 일람표 렌더링 (현재/부족/권장)

### 함수 시그니처
```python
def render_coverage_comparison_table(
    coverage_data: list[dict],
    customer_name: str = "고객"
) -> None:
    """
    [STEP 8] 3단 보장 일람표 렌더링.
    
    Args:
        coverage_data: 보장 분석 결과 리스트
            [
                {
                    "category": "암진단비",
                    "current": 3000,
                    "shortage": 2000,
                    "recommended": 5000
                },
                ...
            ]
        customer_name: 고객 이름
    """
```

### 주요 기능
1. **3단 일람표 생성**
   - 현재 보장: 기존 가입 증권 합산
   - 부족 금액: KB 평균 - 현재 보장
   - 권장 금액: KB 평균 가입금액

2. **보장 카테고리**
   - 암진단비
   - 뇌혈관질환 진단비
   - 허혈성심장질환 진단비
   - 일반상해 사망
   - 일반상해 후유장해
   - 질병 입원일당
   - 상해 입원일당

3. **시각화**
   - 막대 그래프 (현재/부족/권장)
   - 색상 코딩 (빨강: 부족, 초록: 충족)
   - 퍼센트 표시

### UI 컴포넌트
```python
# 3단 일람표 테이블
st.markdown(f"### 📊 {customer_name}님 보장 분석")

df = pd.DataFrame(coverage_data)
df['부족률'] = (df['shortage'] / df['recommended'] * 100).round(1)

# 스타일링
def highlight_shortage(val):
    if val > 50:
        return 'background-color: #ffcccc'
    elif val > 20:
        return 'background-color: #fff4cc'
    else:
        return 'background-color: #ccffcc'

styled_df = df.style.applymap(
    highlight_shortage,
    subset=['부족률']
)

st.dataframe(styled_df, use_container_width=True)

# 막대 그래프
fig = go.Figure()
fig.add_trace(go.Bar(
    name='현재',
    x=df['category'],
    y=df['current'],
    marker_color='lightblue'
))
fig.add_trace(go.Bar(
    name='부족',
    x=df['category'],
    y=df['shortage'],
    marker_color='salmon'
))
fig.add_trace(go.Bar(
    name='권장',
    x=df['category'],
    y=df['recommended'],
    marker_color='lightgreen'
))

st.plotly_chart(fig, use_container_width=True)
```

### 연결된 DB 테이블
- **gk_unified_reports**: 보장 분석 결과
  - `report_type`: 'coverage_analysis'
  - `report_data`: jsonb (coverage_data)

### 12단계 마스터플랜 연결
- **STEP 6**: 통합 보장 공백 진단
- **STEP 8**: AI 감성 제안

---

## 4. crm_analysis_screen_block.py

### 기본 정보
- **파일명**: `crm_analysis_screen_block.py`
- **주요 함수**: `render_crm_analysis_screen()`
- **라인 수**: ~350줄
- **용도**: CRM 분석 화면 (고객 전체 현황 요약)

### 주요 기능
1. **고객 요약 카드**
   - 이름, 연령, 성별
   - 직업, 연락처
   - 최근 상담 일자

2. **보험 현황 요약**
   - 총 계약 건수
   - 월 보험료 합계
   - 보험사별 분포

3. **보장 분석 요약**
   - 주요 보장 항목별 충족률
   - 부족 항목 강조

4. **최근 활동 타임라인**
   - 스캔 이력
   - 상담 이력
   - 리포트 생성 이력

### UI 컴포넌트
```python
# 고객 요약 카드
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 계약", f"{contract_count}건")
with col2:
    st.metric("월 보험료", f"{total_premium:,}원")
with col3:
    st.metric("관리 등급", tier)

# 보장 충족률 게이지
fig = go.Figure(go.Indicator(
    mode="gauge+number+delta",
    value=coverage_rate,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "보장 충족률"},
    delta={'reference': 80},
    gauge={
        'axis': {'range': [None, 100]},
        'bar': {'color': "darkblue"},
        'steps': [
            {'range': [0, 50], 'color': "lightgray"},
            {'range': [50, 80], 'color': "gray"}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 80
        }
    }
))
st.plotly_chart(fig)
```

---

## 5. crm_consultation_center_block.py

### 기본 정보
- **파일명**: `crm_consultation_center_block.py`
- **주요 함수**: `render_consultation_center()`
- **라인 수**: ~450줄
- **용도**: 상담 센터 (상담 이력 관리 + 메모 작성)

### 주요 기능
1. **상담 이력 조회**
   - 날짜별 상담 목록
   - 상담 내용 요약
   - 상담 결과 (계약/보류/거절)

2. **상담 메모 작성**
   - 실시간 메모 저장
   - Supabase 즉시 동기화
   - 음성 메모 녹음 (선택)

3. **다음 상담 일정**
   - 캘린더 연동
   - 알림 설정

4. **상담 통계**
   - 월별 상담 건수
   - 계약 전환율
   - 평균 상담 시간

### 연결된 DB 테이블
- **consultation_history**: 상담 이력
  - `consultation_id` (PK)
  - `person_id` (FK)
  - `agent_id` (FK)
  - `consultation_date` (date)
  - `memo` (text)
  - `result` (varchar: 'contract'/'pending'/'rejected')
  - `next_contact_date` (date)

---

## 6. crm_kakao_share_block.py

### 기본 정보
- **파일명**: `crm_kakao_share_block.py`
- **주요 함수**: `render_kakao_share_ui()`
- **라인 수**: ~400줄
- **용도**: 카카오톡 메시지 전송 (텍스트 + 이미지)

### 주요 기능
1. **메시지 템플릿**
   - 상담 결과 요약
   - 보장 분석 리포트
   - 제안서 링크

2. **이미지 첨부**
   - GCS에서 이미지 로드
   - 리사이징 및 최적화
   - Base64 인코딩

3. **카카오톡 API 연동**
   - REST API 호출
   - 토큰 관리
   - 전송 결과 확인

### 함수 시그니처
```python
def render_kakao_share_ui(
    message: str,
    image_url: str = None,
    recipient_phone: str = None
) -> bool:
    """
    카카오톡 메시지 전송 UI.
    
    Returns:
        성공 여부
    """
```

---

## 7. crm_nibo_screen_block.py

### 기본 정보
- **파일명**: `crm_nibo_screen_block.py`
- **주요 함수**: `render_nibo_analysis()`
- **라인 수**: ~650줄
- **용도**: 니보 분석 (네트워크 기반 보험 최적화)

### 주요 기능
1. **가족 네트워크 분석**
   - 가족 구성원 보험 통합 분석
   - 중복 보장 탐지
   - 가족 전체 보험료 최적화

2. **보장 공유 전략**
   - 가족 단위 보장 설계
   - 비용 절감 방안

3. **시각화**
   - 가족 네트워크 그래프
   - 보장 중복 히트맵

---

## 8. crm_phase1_network_block.py

### 기본 정보
- **파일명**: `crm_phase1_network_block.py`
- **주요 함수**: `render_network_graph()`
- **라인 수**: ~700줄
- **용도**: 고객 네트워크 시각화 (인맥 관리)

### 주요 기능
1. **인맥 네트워크 그래프**
   - 고객 간 관계 시각화
   - 추천인 추적
   - 영향력 분석

2. **추천 시스템**
   - 잠재 고객 발굴
   - 교차 판매 기회 탐지

---

## 9. crm_action_grid_block.py

### 기본 정보
- **파일명**: `crm_action_grid_block.py`
- **주요 함수**: `render_action_grid()`
- **라인 수**: ~100줄
- **용도**: 빠른 실행 버튼 그리드

### 주요 기능
- 주요 기능 버튼 배치
- 아이콘 + 텍스트 조합
- 클릭 시 해당 블록으로 이동

---

## 10. crm_insurance_contracts_block.py

### 기본 정보
- **파일명**: `crm_insurance_contracts_block.py`
- **주요 함수**: `render_contracts_list()`
- **라인 수**: ~280줄
- **용도**: 보험 계약 목록 표시

### 주요 기능
- 계약 목록 테이블
- 필터링 (보험사, 상품명)
- 정렬 (가입일, 보험료)

---

## 11. crm_policy_cancellation_block.py

### 기본 정보
- **파일명**: `crm_policy_cancellation_block.py`
- **주요 함수**: `render_cancellation_scheduler()`
- **라인 수**: ~310줄
- **용도**: 해지 예정 계약 관리

### 주요 기능
- 해지 예정 목록
- 해지 사유 입력
- 해지 환급금 계산

---

## 12. crm_expiry_alerts_block.py

### 기본 정보
- **파일명**: `crm_expiry_alerts_block.py`
- **주요 함수**: `render_expiry_alerts()`
- **라인 수**: ~210줄
- **용도**: 만기 알림 (갱신 대상 계약)

### 주요 기능
- 만기 임박 계약 목록
- 자동 알림 설정
- 갱신 제안 생성

---

## 13. crm_list_inline_panel_block.py

### 기본 정보
- **파일명**: `crm_list_inline_panel_block.py`
- **주요 함수**: `render_inline_customer_list()`
- **라인 수**: ~140줄
- **용도**: 인라인 고객 목록 패널

### 주요 기능
- 사이드바 고객 목록
- 빠른 검색
- 클릭 시 고객 선택

---

## 14. crm_scan_vault_viewer.py

### 기본 정보
- **파일명**: `crm_scan_vault_viewer.py`
- **주요 함수**: `render_scan_vault()`
- **라인 수**: ~250줄
- **용도**: GCS 스캔 파일 뷰어

### 주요 기능
- GCS 파일 목록 조회
- 파일 다운로드
- 썸네일 미리보기

---

## 15. crm_hq_scan_bridge.py

### 기본 정보
- **파일명**: `crm_hq_scan_bridge.py`
- **주요 함수**: `sync_scan_to_hq()`
- **라인 수**: ~85줄
- **용도**: CRM → HQ 스캔 동기화

### 주요 기능
- 스캔 완료 시 HQ 알림
- SSO 토큰 전달
- person_id 동기화

---

## 16. crm_nav_block.py

### 기본 정보
- **파일명**: `crm_nav_block.py`
- **주요 함수**: `render_crm_nav()`
- **라인 수**: ~65줄
- **용도**: CRM 네비게이션 바

### 주요 기능
- 상단 메뉴 바
- 로고 표시
- 로그아웃 버튼

---

## 17. zombie_tables_crud.py

### 기본 정보
- **파일명**: `zombie_tables_crud.py`
- **주요 함수**: `manage_zombie_tables()`
- **라인 수**: ~470줄
- **용도**: 좀비 테이블 관리 (임시 데이터 정리)

### 주요 기능
- 임시 테이블 조회
- 오래된 데이터 삭제
- 스토리지 최적화

---

## 통계 요약

| 블록 유형 | 개수 | 평균 라인 수 |
|---------|------|------------|
| 핵심 기능 블록 | 8 | 500줄 |
| UI 컴포넌트 블록 | 6 | 200줄 |
| 유틸리티 블록 | 3 | 150줄 |
| **합계** | **17** | **350줄** |

---

## 다음 단계

이 보고서는 `REPORT_1_TAB_DETAILS.md`, `REPORT_3_MASTERPLAN_MAPPING.md`, `REPORT_4_DATA_FLOW.md`와 함께 전체 시스템 문서화를 구성합니다.
