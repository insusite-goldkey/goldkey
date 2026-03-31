# 12단계 마스터플랜 매핑 보고서

**Goldkey AI Masters 2026 — 워크플로우·코인 차감·티어 구분 완전 분석**  
**작성일**: 2026-03-30  
**목적**: 12단계 마스터플랜의 각 단계별 기능, 코인 차감 규칙, Basic/Pro 티어 구분, 연결된 탭/블록/DB/AI 엔진을 상세히 문서화

---

## 📋 목차

1. [12단계 마스터플랜 개요](#12단계-마스터플랜-개요)
2. [STEP 1: 고객 등록 및 기본 정보 입력](#step-1-고객-등록-및-기본-정보-입력)
3. [STEP 2: 트리니티 가처분소득 산출](#step-2-트리니티-가처분소득-산출)
4. [STEP 3: 증권 및 의무기록 스캔](#step-3-증권-및-의무기록-스캔)
5. [STEP 4: OCR 자동 파싱 및 데이터 추출](#step-4-ocr-자동-파싱-및-데이터-추출)
6. [STEP 5: KB 평균 가입금액 비교](#step-5-kb-평균-가입금액-비교)
7. [STEP 6: 통합 보장 공백 진단](#step-6-통합-보장-공백-진단)
8. [STEP 7: 에이젠틱 AI 전략 수립](#step-7-에이젠틱-ai-전략-수립)
9. [STEP 8: AI 감성 제안 및 작문](#step-8-ai-감성-제안-및-작문)
10. [STEP 9: 1:1 맞춤 제안서 생성](#step-9-11-맞춤-제안서-생성)
11. [STEP 10: 카카오톡 자동 전송](#step-10-카카오톡-자동-전송)
12. [STEP 11: 후속 관리 스케줄링](#step-11-후속-관리-스케줄링)
13. [STEP 12: 계약 체결 및 사후 관리](#step-12-계약-체결-및-사후-관리)
14. [코인 차감 규칙 요약](#코인-차감-규칙-요약)
15. [티어별 기능 접근 권한](#티어별-기능-접근-권한)

---

## 12단계 마스터플랜 개요

### 전체 워크플로우
```
고객 등록 → 소득 산출 → 증권 스캔 → 보장 분석 → AI 전략 → 제안서 생성 → 전송 → 계약 → 사후 관리
```

### 설계 철학
1. **단계별 독립성**: 각 단계는 독립적으로 실행 가능
2. **데이터 누적**: 이전 단계 데이터가 다음 단계에 자동 전달
3. **코인 경제**: Pro 기능은 코인 차감으로 과금
4. **AI 중심**: 7~9단계는 AI 엔진 집중 활용
5. **자동화**: 10~12단계는 자동화 워크플로우

### 참여 시스템
- **CRM 앱**: STEP 1~3, 10~12 (현장 영업)
- **HQ 앱**: STEP 4~9 (정밀 분석)
- **Supabase**: 전 단계 데이터 저장
- **GCS**: 파일 암호화 저장
- **AI 엔진**: Gemini 1.5 Pro, GPT-4, Claude 3.5

---

## STEP 1: 고객 등록 및 기본 정보 입력

### 기본 정보
- **단계명**: 고객 등록 및 기본 정보 입력
- **주요 앱**: CRM
- **접근 권한**: Basic (무료)
- **코인 차감**: 0🪙

### 주요 기능
1. **고객 기본 정보 입력**
   - 이름 (필수)
   - 생년월일 (필수)
   - 성별 (필수)
   - 연락처 (필수, SHA-256 해시 저장)
   - 주소 (선택)
   - 직업 (선택)

2. **가족 관계 등록**
   - 배우자, 자녀, 부모 등록
   - 관계 타입 설정
   - 가족 네트워크 구성

3. **약관 동의**
   - 개인정보 수집·이용 동의
   - 암호화 저장 동의
   - 영구 보관 동의

### 연결된 CRM 블록
- `crm_list_inline_panel_block.py`: 고객 목록 표시
- `shared_components.py`: `customer_input_form()` 함수

### 연결된 HQ 탭
- 0100: 홈 포털
- 1000: 홈 화면

### DB 테이블
```sql
-- people 테이블
CREATE TABLE people (
    person_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    birth_date DATE,
    gender VARCHAR(10),
    contact_hash VARCHAR(64), -- SHA-256 해시
    address TEXT,
    occupation VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- relationships 테이블
CREATE TABLE relationships (
    relationship_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(person_id),
    related_person_id UUID REFERENCES people(person_id),
    relationship_type VARCHAR(50), -- 'spouse', 'child', 'parent'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 데이터 흐름
```
CRM 입력 폼 → Supabase people 테이블 → Session State → HQ 동기화
```

### 보안 규칙 (GP-SEC §1)
- 연락처는 SHA-256 단방향 해시로만 저장
- 복호화 필요 시 Fernet 양방향 암호화 사용
- URL 파라미터에 PII 원문 절대 포함 금지

### 사용 시나리오
1. 설계사가 CRM 앱 로그인
2. "신규 고객 등록" 버튼 클릭
3. 고객 정보 입력 폼 작성
4. 약관 동의 체크
5. "등록" 버튼 클릭
6. Supabase에 즉시 저장
7. Session State에 person_id 저장

### 에러 핸들링
```python
try:
    person_id = insert_customer(customer_data)
    st.session_state.selected_person_id = person_id
    st.success("✅ 고객 등록 완료!")
except Exception as e:
    st.error(f"❌ 등록 실패: {str(e)}")
    logging.error(f"Customer registration error: {e}", exc_info=True)
```

---

## STEP 2: 트리니티 가처분소득 산출

### 기본 정보
- **단계명**: 트리니티 가처분소득 산출
- **주요 앱**: CRM
- **접근 권한**: Basic (무료)
- **코인 차감**: 0🪙

### 주요 기능
1. **소득 정보 입력**
   - 월 소득 (만원)
   - 고정비 (주거비 + 교육비 + 생활비)
   - 기타 수입

2. **가처분소득 자동 계산**
   ```python
   disposable_income = monthly_income - fixed_cost
   ```

3. **보험료 적정 비율 제안**
   ```python
   recommended_premium = disposable_income * 0.12  # 12% 권장
   min_premium = disposable_income * 0.10  # 최소 10%
   max_premium = disposable_income * 0.15  # 최대 15%
   ```

4. **소득 역산 연산기**
   - 목표 보험료 입력 시 필요 소득 역산
   ```python
   required_income = target_premium / 0.12
   ```

### 연결된 CRM 블록
- `crm_trinity_block.py`: `render_crm_trinity_block()`

### 연결된 HQ 탭
- 0300: 실전 상담 전략실 (소득 역산 기능)

### DB 테이블
```sql
-- gk_unified_reports 테이블 (trinity_result)
{
    "report_type": "trinity_result",
    "person_id": "uuid",
    "report_data": {
        "monthly_income": 300,
        "fixed_cost": 150,
        "disposable_income": 150,
        "recommended_premium": 18,
        "min_premium": 15,
        "max_premium": 22.5
    },
    "created_at": "2026-03-30T10:00:00Z"
}
```

### 데이터 흐름
```
CRM 입력 → 계산 로직 → Supabase 저장 → Session State → HQ 조회
```

### UI 컴포넌트
```python
col1, col2 = st.columns(2)
with col1:
    monthly_income = st.number_input("월 소득 (만원)", min_value=0, value=300, step=10)
with col2:
    fixed_cost = st.number_input("고정비 (만원)", min_value=0, value=150, step=10)

disposable_income = monthly_income - fixed_cost
recommended_premium = disposable_income * 0.12

st.metric("가처분소득", f"{disposable_income:,}만원")
st.metric("권장 보험료", f"{recommended_premium:,.0f}만원")

# 게이지 차트
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=recommended_premium,
    domain={'x': [0, 1], 'y': [0, 1]},
    title={'text': "권장 보험료 (만원)"},
    gauge={'axis': {'range': [0, 50]}}
))
st.plotly_chart(fig)
```

### 사용 시나리오
1. STEP 1에서 고객 등록 완료
2. CRM에서 "트리니티 산출" 버튼 클릭
3. 월 소득 및 고정비 입력
4. 자동 계산 결과 확인
5. Supabase에 저장
6. 상담 브리핑 카드에 표시

---

## STEP 3: 증권 및 의무기록 스캔

### 기본 정보
- **단계명**: 증권 및 의무기록 스캔
- **주요 앱**: CRM
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 1🪙 (증권), 1🪙 (의무기록), 3🪙 (통합 분석)

### 주요 기능
1. **서류 종류 선택**
   - 보험증권 (1🪙)
   - 의무기록 (1🪙)
   - 지급결의서 (1🪙)
   - 사고확인서 (1🪙)
   - 기타 서류 (1🪙)

2. **이미지 업로드**
   - 사진 촬영 또는 파일 선택
   - 지원 포맷: JPG, PNG, PDF
   - 최대 파일 크기: 10MB

3. **GCS 암호화 저장**
   - 경로: `gs://goldkey-scan-vault/{agent_id}/{person_id}/{doc_type}/{timestamp}.enc`
   - Fernet 암호화 적용
   - 메타데이터 태깅 (agent_id, person_id)

4. **Supabase 메타데이터 등록**
   - 테이블: `gk_scan_files`
   - 스캔 이력 추적

### 연결된 CRM 블록
- `crm_scan_block.py`: `render_crm_scan_block()`
- `crm_hq_scan_bridge.py`: HQ 동기화

### 연결된 HQ 탭
- 1100: 통합 스캔 허브
- 1200: 보험증권 분석

### DB 테이블
```sql
-- gk_scan_files 테이블
CREATE TABLE gk_scan_files (
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(person_id),
    agent_id UUID REFERENCES members(user_id),
    doc_type VARCHAR(50), -- 'policy', 'medical', 'claim'
    gcs_path TEXT NOT NULL,
    file_size_bytes INTEGER,
    mime_type VARCHAR(100),
    ocr_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    ocr_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### GCS 저장 규칙 (GP-SEC §4)
```python
def upload_scan_to_gcs(
    file_bytes: bytes,
    agent_id: str,
    person_id: str,
    doc_type: str
) -> str:
    """스캔 파일을 GCS에 암호화하여 업로드."""
    # Fernet 암호화
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    encrypted_data = cipher.encrypt(file_bytes)
    
    # GCS 업로드
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_name = f"{agent_id}/{person_id}/{doc_type}/{timestamp}.enc"
    bucket = storage_client.bucket("goldkey-scan-vault")
    blob = bucket.blob(blob_name)
    
    # 메타데이터 태깅
    blob.metadata = {
        "agent_id": agent_id,
        "person_id": person_id,
        "doc_type": doc_type,
        "uploaded_at": timestamp
    }
    
    blob.upload_from_string(encrypted_data)
    return f"gs://goldkey-scan-vault/{blob_name}"
```

### 코인 차감 로직
```python
def deduct_coins_for_scan(user_id: str, doc_type: str) -> bool:
    """스캔 시 코인 차감."""
    coin_cost = {
        "policy": 1,
        "medical": 1,
        "claim": 1,
        "accident": 1,
        "other": 1,
        "unified_analysis": 3
    }
    
    cost = coin_cost.get(doc_type, 1)
    current_coins = get_user_coins(user_id)
    
    if current_coins < cost:
        st.error(f"❌ 코인 부족 (필요: {cost}🪙, 보유: {current_coins}🪙)")
        return False
    
    # 코인 차감
    update_user_coins(user_id, current_coins - cost)
    
    # 사용 로그 기록
    log_coin_usage(user_id, cost, f"scan_{doc_type}")
    
    st.success(f"✅ 코인 {cost}🪙 차감 완료")
    return True
```

### 사용 시나리오
1. STEP 2 완료 후 CRM에서 "증권 스캔" 버튼 클릭
2. 서류 종류 선택 (보험증권)
3. 사진 촬영 또는 파일 업로드
4. 코인 1🪙 차감 확인
5. GCS 암호화 저장
6. Supabase 메타데이터 등록
7. HQ 앱에 동기화 알림

---

## STEP 4: OCR 자동 파싱 및 데이터 추출

### 기본 정보
- **단계명**: OCR 자동 파싱 및 데이터 추출
- **주요 앱**: HQ
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 0🪙 (STEP 3에서 이미 차감)

### 주요 기능
1. **Google Vision API OCR**
   - 텍스트 자동 추출
   - 구조화된 데이터 파싱
   - 신뢰도 점수 계산

2. **보험증권 파싱**
   - 보험사명
   - 상품명
   - 증권번호
   - 가입일
   - 만기일
   - 월 보험료
   - 담보 목록

3. **의무기록 파싱**
   - 진료 날짜
   - 병원명
   - 진단명 (KCD 코드)
   - 처방 내역
   - 진료비

### 연결된 HQ 탭
- 1200: 보험증권 분석
- 1300: 약관 매칭

### AI 엔진
- **Google Vision API**: OCR 텍스트 추출
- **Gemini 1.5 Pro**: 구조화된 데이터 파싱

### DB 테이블
```sql
-- policies 테이블
CREATE TABLE policies (
    policy_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id UUID REFERENCES people(person_id),
    insurance_company VARCHAR(100),
    product_name VARCHAR(200),
    policy_number VARCHAR(100),
    start_date DATE,
    end_date DATE,
    monthly_premium INTEGER,
    scan_file_id UUID REFERENCES gk_scan_files(file_id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- policy_coverages 테이블
CREATE TABLE policy_coverages (
    coverage_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id UUID REFERENCES policies(policy_id),
    coverage_name VARCHAR(200),
    coverage_amount BIGINT,
    coverage_type VARCHAR(50), -- 'diagnosis', 'hospitalization', 'surgery'
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 파싱 로직
```python
def parse_policy_ocr(ocr_text: str, person_id: str) -> dict:
    """보험증권 OCR 텍스트를 구조화된 데이터로 파싱."""
    
    # Gemini 1.5 Pro로 구조화
    prompt = f"""
    다음 보험증권 OCR 텍스트를 분석하여 JSON 형식으로 추출하세요:
    
    {ocr_text}
    
    추출 항목:
    - insurance_company: 보험사명
    - product_name: 상품명
    - policy_number: 증권번호
    - start_date: 가입일 (YYYY-MM-DD)
    - end_date: 만기일 (YYYY-MM-DD)
    - monthly_premium: 월 보험료 (숫자만)
    - coverages: [
        {{"name": "암진단비", "amount": 3000, "type": "diagnosis"}},
        ...
      ]
    """
    
    response = gemini_client.generate_content(prompt)
    parsed_data = json.loads(response.text)
    
    # Supabase에 저장
    policy_id = insert_policy(person_id, parsed_data)
    
    for coverage in parsed_data['coverages']:
        insert_coverage(policy_id, coverage)
    
    return parsed_data
```

### 사용 시나리오
1. STEP 3에서 증권 스캔 완료
2. HQ 앱에서 자동으로 OCR 처리 시작
3. Google Vision API로 텍스트 추출
4. Gemini 1.5 Pro로 구조화된 데이터 파싱
5. policies 및 policy_coverages 테이블에 저장
6. 파싱 결과 화면에 표시

---

## STEP 5: KB 평균 가입금액 비교

### 기본 정보
- **단계명**: KB 평균 가입금액 비교
- **주요 앱**: HQ
- **접근 권한**: Basic (무료)
- **코인 차감**: 0🪙

### 주요 기능
1. **KB 7대 스탠다드 기준**
   - 암진단비: 5,000만원
   - 뇌혈관질환 진단비: 3,000만원
   - 허혈성심장질환 진단비: 3,000만원
   - 일반상해 사망: 1억원
   - 일반상해 후유장해: 1억원
   - 질병 입원일당: 5만원
   - 상해 입원일당: 5만원

2. **현재 가입 금액 합산**
   - 동일 담보 자동 합산
   - 중복 보장 제거

3. **부족 금액 계산**
   ```python
   shortage = kb_standard - current_amount
   shortage_rate = (shortage / kb_standard) * 100
   ```

### 연결된 HQ 탭
- 1200: 보험증권 분석
- 4000: 기본보험 상담

### 분석 엔진
- `engines/kb_scoring_system.py`: `calculate_kb_gap()`

### 분석 로직
```python
def calculate_kb_gap(person_id: str) -> dict:
    """KB 평균 가입금액 대비 부족 금액 계산."""
    
    # KB 7대 스탠다드
    kb_standards = {
        "암진단비": 50000000,
        "뇌혈관질환": 30000000,
        "허혈성심장질환": 30000000,
        "일반상해사망": 100000000,
        "일반상해후유장해": 100000000,
        "질병입원일당": 50000,
        "상해입원일당": 50000
    }
    
    # 현재 가입 금액 조회
    current_coverages = get_person_coverages(person_id)
    
    # 담보별 합산
    coverage_sum = {}
    for cov in current_coverages:
        cov_type = normalize_coverage_type(cov['coverage_name'])
        coverage_sum[cov_type] = coverage_sum.get(cov_type, 0) + cov['coverage_amount']
    
    # 부족 금액 계산
    gap_analysis = []
    for category, standard in kb_standards.items():
        current = coverage_sum.get(category, 0)
        shortage = max(0, standard - current)
        shortage_rate = (shortage / standard) * 100
        
        gap_analysis.append({
            "category": category,
            "kb_standard": standard,
            "current": current,
            "shortage": shortage,
            "shortage_rate": shortage_rate,
            "status": "충족" if shortage == 0 else "부족"
        })
    
    return gap_analysis
```

### 사용 시나리오
1. STEP 4에서 증권 파싱 완료
2. HQ에서 "KB 비교 분석" 버튼 클릭
3. 자동으로 KB 기준과 비교
4. 부족 금액 시각화
5. 결과를 gk_unified_reports에 저장

---

## STEP 6: 통합 보장 공백 진단

### 기본 정보
- **단계명**: 통합 보장 공백 진단
- **주요 앱**: HQ
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 2🪙

### 주요 기능
1. **3단 일람표 생성**
   - 현재 보장: 기존 증권 합산
   - 부족 금액: KB 평균 - 현재
   - 권장 금액: KB 평균

2. **보장 공백 우선순위**
   - 부족률 70% 이상: 긴급
   - 부족률 40~70%: 중요
   - 부족률 40% 미만: 보통

3. **시각화**
   - 막대 그래프
   - 히트맵
   - 레이더 차트

### 연결된 CRM 블록
- `crm_coverage_analysis_block.py`: `render_coverage_comparison_table()`

### 연결된 HQ 탭
- 1200: 보험증권 분석
- 4100: 통합보험 설계

### 코인 차감
```python
if st.button("🔍 보장 공백 진단 시작 (2🪙)", type="primary"):
    if deduct_coins(user_id, 2):
        with st.spinner("AI가 보장 공백을 분석 중입니다..."):
            gap_analysis = analyze_coverage_gap(person_id)
            st.session_state.gap_analysis = gap_analysis
```

### 사용 시나리오
1. STEP 5 완료 후 "보장 공백 진단" 버튼 클릭
2. 코인 2🪙 차감
3. AI가 보장 공백 분석
4. 3단 일람표 생성
5. 우선순위 표시
6. CRM에서도 조회 가능

---

## STEP 7: 에이젠틱 AI 전략 수립

### 기본 정보
- **단계명**: 에이젠틱 AI 전략 수립
- **주요 앱**: HQ
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 3🪙

### 주요 기능
1. **고객 프로필 분석**
   - 연령, 직업, 소득, 가족 구성
   - 현재 보장 현황
   - 보장 공백 우선순위

2. **상담 전략 생성**
   - 후킹 스크립트
   - 거절 대응 시나리오
   - 심리 전략

3. **제안 상품 추천**
   - 보장 공백 기반 상품 매칭
   - 보험사별 추천 상품
   - 월 보험료 시뮬레이션

### 연결된 HQ 탭
- 0300: 실전 상담 전략실
- 9920: 실전 상담 전략실 (War Room)

### AI 엔진
- **Gemini 1.5 Pro**: 전략 생성
- **GPT-4**: 심리 분석
- **Claude 3.5**: 스크립트 작문

### 전략 생성 로직
```python
def generate_consultation_strategy(person_id: str, gap_analysis: dict) -> dict:
    """에이젠틱 AI 상담 전략 생성."""
    
    # 고객 정보 조회
    customer = get_customer_info(person_id)
    trinity_data = get_trinity_result(person_id)
    
    # Gemini 1.5 Pro 프롬프트
    prompt = f"""
    다음 고객의 상담 전략을 수립하세요:
    
    [고객 정보]
    - 이름: {customer['name']}
    - 연령: {customer['age']}세
    - 직업: {customer['occupation']}
    - 월 소득: {trinity_data['monthly_income']}만원
    - 가처분소득: {trinity_data['disposable_income']}만원
    - 권장 보험료: {trinity_data['recommended_premium']}만원
    
    [보장 공백]
    {json.dumps(gap_analysis, ensure_ascii=False, indent=2)}
    
    다음 항목을 포함한 상담 전략을 작성하세요:
    1. 후킹 스크립트 (첫 30초)
    2. 보장 공백 설명 (2분)
    3. 제안 상품 소개 (3분)
    4. 예상 거절 사유 3가지 및 대응 방안
    5. 클로징 멘트
    """
    
    response = gemini_client.generate_content(prompt)
    strategy = parse_strategy_response(response.text)
    
    # Supabase에 저장
    save_strategy(person_id, strategy)
    
    return strategy
```

### 코인 차감
```python
if st.button("🧠 AI 전략 수립 (3🪙)", type="primary"):
    if deduct_coins(user_id, 3):
        strategy = generate_consultation_strategy(person_id, gap_analysis)
        st.session_state.strategy = strategy
```

---

## STEP 8: AI 감성 제안 및 작문

### 기본 정보
- **단계명**: AI 감성 제안 및 작문
- **주요 앱**: HQ
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 2🪙

### 주요 기능
1. **감성 메시지 작성**
   - 고객 맞춤형 감성 문구
   - 스토리텔링 기법 적용
   - 공감 포인트 강조

2. **제안서 텍스트 생성**
   - 보장 분석 요약
   - 추천 이유 설명
   - 혜택 강조

3. **카카오톡 메시지 템플릿**
   - 짧은 버전 (100자)
   - 긴 버전 (500자)
   - 이미지 + 텍스트 조합

### AI 엔진
- **GPT-4**: 감성 작문
- **Claude 3.5**: 스토리텔링

### 작문 로직
```python
def generate_emotional_proposal(person_id: str, strategy: dict) -> dict:
    """AI 감성 제안 작문."""
    
    customer = get_customer_info(person_id)
    
    prompt = f"""
    다음 고객에게 보낼 감성적인 보험 제안 메시지를 작성하세요:
    
    [고객 정보]
    - 이름: {customer['name']}
    - 연령: {customer['age']}세
    - 가족: {customer['family_members']}
    
    [상담 전략]
    {strategy['summary']}
    
    요구사항:
    1. 고객의 가족을 생각하는 마음 강조
    2. 현재 보장의 위험성 부드럽게 지적
    3. 미래의 안정감 강조
    4. 따뜻하고 신뢰감 있는 톤
    5. 200자 이내
    """
    
    response = gpt4_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    
    emotional_message = response.choices[0].message.content
    
    return {
        "short_message": emotional_message[:100],
        "long_message": emotional_message,
        "kakao_template": format_kakao_message(emotional_message)
    }
```

---

## STEP 9: 1:1 맞춤 제안서 생성

### 기본 정보
- **단계명**: 1:1 맞춤 제안서 생성
- **주요 앱**: HQ
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 3🪙

### 주요 기능
1. **PDF 제안서 생성**
   - 표지 (고객명, 설계사명)
   - 보장 분석 요약
   - 3단 일람표
   - 추천 상품 상세
   - 월 보험료 시뮬레이션
   - 가입 혜택

2. **이미지 생성**
   - 보장 분석 차트
   - 가족 보호 일러스트
   - QR 코드 (온라인 제안서 링크)

3. **다운로드 및 공유**
   - PDF 다운로드
   - 카카오톡 전송
   - 이메일 전송

### 연결된 HQ 탭
- 1400: AI 자동 리포트
- 4100: 통합보험 설계

### 제안서 생성 로직
```python
def generate_proposal_pdf(person_id: str, strategy: dict, emotional_message: dict) -> str:
    """1:1 맞춤 제안서 PDF 생성."""
    
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    
    customer = get_customer_info(person_id)
    gap_analysis = get_gap_analysis(person_id)
    
    # PDF 생성
    pdf_path = f"/tmp/proposal_{person_id}.pdf"
    c = canvas.Canvas(pdf_path, pagesize=A4)
    
    # 표지
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 750, f"{customer['name']}님을 위한")
    c.drawString(100, 720, "맞춤형 보장 분석 제안서")
    
    # 보장 분석 요약
    c.setFont("Helvetica", 12)
    y = 650
    for item in gap_analysis:
        c.drawString(100, y, f"{item['category']}: {item['shortage']:,}원 부족")
        y -= 20
    
    # 감성 메시지
    c.setFont("Helvetica-Oblique", 14)
    c.drawString(100, y-50, emotional_message['long_message'])
    
    c.save()
    
    # GCS 업로드
    gcs_path = upload_proposal_to_gcs(pdf_path, person_id)
    
    return gcs_path
```

---

## STEP 10: 카카오톡 자동 전송

### 기본 정보
- **단계명**: 카카오톡 자동 전송
- **주요 앱**: CRM
- **접근 권한**: Pro (프로 전용)
- **코인 차감**: 1🪙

### 주요 기능
1. **메시지 전송**
   - 텍스트 메시지
   - 이미지 첨부
   - 링크 첨부

2. **전송 이력 관리**
   - 전송 일시
   - 수신 확인
   - 재전송 기능

### 연결된 CRM 블록
- `crm_kakao_share_block.py`: `render_kakao_share_ui()`

---

## STEP 11: 후속 관리 스케줄링

### 기본 정보
- **단계명**: 후속 관리 스케줄링
- **주요 앱**: CRM
- **접근 권한**: Basic (무료)
- **코인 차감**: 0🪙

### 주요 기능
1. **다음 상담 일정 등록**
2. **알림 설정**
3. **만기 알림 자동화**

### 연결된 CRM 블록
- `crm_expiry_alerts_block.py`: `render_expiry_alerts()`

---

## STEP 12: 계약 체결 및 사후 관리

### 기본 정보
- **단계명**: 계약 체결 및 사후 관리
- **주요 앱**: CRM
- **접근 권한**: Basic (무료)
- **코인 차감**: 0🪙

### 주요 기능
1. **계약 정보 등록**
2. **청약서 업로드**
3. **계약 완료 알림**
4. **사후 관리 스케줄링**

---

## 코인 차감 규칙 요약

| STEP | 기능 | 코인 |
|------|------|------|
| 1 | 고객 등록 | 0🪙 |
| 2 | 트리니티 산출 | 0🪙 |
| 3 | 증권 스캔 | 1🪙 |
| 3 | 의무기록 스캔 | 1🪙 |
| 3 | 통합 분석 | 3🪙 |
| 4 | OCR 파싱 | 0🪙 |
| 5 | KB 비교 | 0🪙 |
| 6 | 보장 공백 진단 | 2🪙 |
| 7 | AI 전략 수립 | 3🪙 |
| 8 | 감성 제안 | 2🪙 |
| 9 | 제안서 생성 | 3🪙 |
| 10 | 카카오톡 전송 | 1🪙 |
| 11 | 스케줄링 | 0🪙 |
| 12 | 계약 관리 | 0🪙 |

**전체 워크플로우 완료 시 최대 코인**: 16🪙

---

## 티어별 기능 접근 권한

### Basic (무료)
- STEP 1: 고객 등록 ✅
- STEP 2: 트리니티 산출 ✅
- STEP 5: KB 비교 ✅
- STEP 11: 스케줄링 ✅
- STEP 12: 계약 관리 ✅

### Pro (유료)
- STEP 3: 증권 스캔 ✅
- STEP 4: OCR 파싱 ✅
- STEP 6: 보장 공백 진단 ✅
- STEP 7: AI 전략 수립 ✅
- STEP 8: 감성 제안 ✅
- STEP 9: 제안서 생성 ✅
- STEP 10: 카카오톡 전송 ✅

---

## 다음 단계

이 보고서는 `REPORT_1_TAB_DETAILS.md`, `REPORT_2_CRM_BLOCKS.md`, `REPORT_4_DATA_FLOW.md`와 함께 전체 시스템 문서화를 구성합니다.
