# 데이터 흐름 중심 아키텍처 보고서

**Goldkey AI Masters 2026 — CRM·HQ·Supabase·GCS·AI 엔진 통합 데이터 파이프라인**  
**작성일**: 2026-03-30  
**목적**: 전체 시스템의 데이터 흐름을 추적하고, 각 컴포넌트 간 데이터 전달 경로, 암호화 규칙, 동기화 메커니즘을 상세히 문서화

---

## 📋 목차

1. [시스템 아키텍처 개요](#시스템-아키텍처-개요)
2. [데이터 레이어 구조](#데이터-레이어-구조)
3. [CRM → Supabase 데이터 흐름](#crm--supabase-데이터-흐름)
4. [CRM → GCS 데이터 흐름](#crm--gcs-데이터-흐름)
5. [CRM → HQ SSO 데이터 흐름](#crm--hq-sso-데이터-흐름)
6. [HQ → Supabase 데이터 흐름](#hq--supabase-데이터-흐름)
7. [HQ → AI 엔진 데이터 흐름](#hq--ai-엔진-데이터-흐름)
8. [AI 엔진 → Supabase 데이터 흐름](#ai-엔진--supabase-데이터-흐름)
9. [GCS → HQ 데이터 흐름](#gcs--hq-데이터-흐름)
10. [Supabase → CRM 동기화](#supabase--crm-동기화)
11. [세션 상태 관리](#세션-상태-관리)
12. [암호화 및 보안 파이프라인](#암호화-및-보안-파이프라인)
13. [에러 핸들링 및 재시도 로직](#에러-핸들링-및-재시도-로직)
14. [성능 최적화 전략](#성능-최적화-전략)

---

## 시스템 아키텍처 개요

### 전체 구조도
```
┌─────────────────────────────────────────────────────────────────┐
│                         사용자 레이어                              │
├─────────────────────────────────────────────────────────────────┤
│  설계사 (CRM 앱)                    │  설계사 (HQ 앱)              │
│  - 모바일 최적화                     │  - 데스크톱 최적화            │
│  - 현장 영업                         │  - 정밀 분석                 │
└──────────┬──────────────────────────┴──────────┬─────────────────┘
           │                                     │
           │ SSO 토큰                             │
           │ (HMAC-SHA256)                       │
           │                                     │
┌──────────▼─────────────────────────────────────▼─────────────────┐
│                      애플리케이션 레이어                            │
├─────────────────────────────────────────────────────────────────┤
│  CRM 앱 (crm_app.py)              │  HQ 앱 (app.py)              │
│  - Streamlit                      │  - Streamlit                 │
│  - 17개 블록                       │  - 70+ 탭                    │
│  - 고객 관리                       │  - 분석 엔진                  │
└──────────┬──────────────────────────┬──────────┬─────────────────┘
           │                          │          │
           │ REST API                 │          │ AI API
           │                          │          │
┌──────────▼──────────────────────────▼──────────▼─────────────────┐
│                      데이터 레이어                                  │
├─────────────────────────────────────────────────────────────────┤
│  Supabase (PostgreSQL)            │  GCS (암호화 스토리지)         │
│  - people                         │  - goldkey-scan-vault        │
│  - policies                       │  - Fernet 암호화             │
│  - gk_unified_reports             │  - 메타데이터 태깅            │
│  - gk_scan_files                  │                              │
└──────────┬──────────────────────────┴──────────────────────────┬─┘
           │                                                      │
           │ 실시간 동기화                                         │
           │                                                      │
┌──────────▼──────────────────────────────────────────────────────▼─┐
│                      AI 엔진 레이어                                 │
├─────────────────────────────────────────────────────────────────┤
│  Gemini 1.5 Pro    │  GPT-4    │  Claude 3.5    │  Vision API   │
│  - 전략 수립        │  - 감성    │  - 작문        │  - OCR        │
└─────────────────────────────────────────────────────────────────┘
```

### 핵심 원칙
1. **물리적 분리**: CRM과 HQ는 독립된 앱 (goldkey-crm, goldkey-ai)
2. **통합 인증 (SSO)**: HMAC-SHA256 토큰으로 앱 간 인증
3. **중앙 집중식 DB**: Supabase가 단일 진실 공급원 (Single Source of Truth)
4. **암호화 스토리지**: GCS에 Fernet 암호화로 파일 저장
5. **세션 휘발성 방어**: 핵심 데이터는 즉시 Supabase 저장

---

## 데이터 레이어 구조

### Supabase 테이블 구조
```sql
-- 고객 정보
people (person_id, name, birth_date, gender, contact_hash, ...)

-- 가족 관계
relationships (relationship_id, person_id, related_person_id, relationship_type)

-- 보험 증권
policies (policy_id, person_id, insurance_company, product_name, monthly_premium, ...)

-- 담보 상세
policy_coverages (coverage_id, policy_id, coverage_name, coverage_amount, ...)

-- 통합 리포트
gk_unified_reports (report_id, person_id, report_type, report_data, created_at)

-- 스캔 파일 메타데이터
gk_scan_files (file_id, person_id, agent_id, doc_type, gcs_path, ocr_result, ...)

-- 상담 이력
consultation_history (consultation_id, person_id, agent_id, memo, result, ...)

-- 설계사 정보
members (user_id, name, email, tier, coins, ...)
```

### GCS 버킷 구조
```
goldkey-scan-vault/
├── {agent_id_1}/
│   ├── {person_id_1}/
│   │   ├── policy/
│   │   │   ├── 20260330_100000.enc
│   │   │   └── 20260330_110000.enc
│   │   ├── medical/
│   │   │   └── 20260330_120000.enc
│   │   └── claim/
│   │       └── 20260330_130000.enc
│   └── {person_id_2}/
│       └── ...
└── {agent_id_2}/
    └── ...
```

---

## CRM → Supabase 데이터 흐름

### 1. 고객 등록 (STEP 1)
```python
# CRM 앱: shared_components.py
def customer_input_form(user_id: str) -> str:
    """고객 정보 입력 폼 → 즉시 Supabase 저장."""
    
    with st.form("customer_form"):
        name = st.text_input("이름*", key="cust_name")
        birth_date = st.date_input("생년월일*", key="cust_birth")
        gender = st.selectbox("성별*", ["남", "여"], key="cust_gender")
        contact = st.text_input("연락처*", key="cust_contact")
        
        submitted = st.form_submit_button("등록")
        
        if submitted:
            # 연락처 해시화 (GP-SEC §1)
            contact_hash = hashlib.sha256(contact.encode()).hexdigest()
            
            # Supabase 즉시 저장
            person_data = {
                "name": name,
                "birth_date": birth_date,
                "gender": gender,
                "contact_hash": contact_hash,
                "created_by": user_id
            }
            
            person_id = supabase.table("people").insert(person_data).execute().data[0]["person_id"]
            
            # 세션 상태 저장
            st.session_state.selected_person_id = person_id
            
            return person_id
```

**데이터 흐름**:
```
CRM 입력 폼
    ↓ (즉시 저장)
Supabase people 테이블
    ↓ (person_id 반환)
Session State (selected_person_id)
    ↓ (HQ 동기화 시)
HQ 앱 (person_id로 조회)
```

### 2. 트리니티 결과 저장 (STEP 2)
```python
# CRM 앱: crm_trinity_block.py
def save_trinity_result(person_id: str, trinity_data: dict) -> None:
    """트리니티 결과를 Supabase에 저장."""
    
    report_data = {
        "person_id": person_id,
        "report_type": "trinity_result",
        "report_data": {
            "monthly_income": trinity_data["monthly_income"],
            "fixed_cost": trinity_data["fixed_cost"],
            "disposable_income": trinity_data["disposable_income"],
            "recommended_premium": trinity_data["recommended_premium"]
        }
    }
    
    supabase.table("gk_unified_reports").insert(report_data).execute()
```

**데이터 흐름**:
```
CRM 트리니티 입력
    ↓
계산 로직 (Python)
    ↓
Supabase gk_unified_reports 테이블
    ↓
HQ 앱 조회 가능
```

---

## CRM → GCS 데이터 흐름

### 스캔 파일 업로드 (STEP 3)
```python
# CRM 앱: crm_scan_block.py
def upload_scan_file(
    uploaded_file: UploadedFile,
    person_id: str,
    agent_id: str,
    doc_type: str
) -> dict:
    """스캔 파일을 GCS에 암호화하여 업로드."""
    
    # 1. 파일 읽기
    file_bytes = uploaded_file.read()
    
    # 2. Fernet 암호화 (GP-SEC §1)
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    encrypted_data = cipher.encrypt(file_bytes)
    
    # 3. GCS 경로 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    blob_name = f"{agent_id}/{person_id}/{doc_type}/{timestamp}.enc"
    
    # 4. GCS 업로드
    bucket = storage_client.bucket("goldkey-scan-vault")
    blob = bucket.blob(blob_name)
    
    # 5. 메타데이터 태깅 (GP-SEC §4)
    blob.metadata = {
        "agent_id": agent_id,
        "person_id": person_id,
        "doc_type": doc_type,
        "uploaded_at": timestamp,
        "original_filename": uploaded_file.name,
        "mime_type": uploaded_file.type
    }
    
    blob.upload_from_string(encrypted_data)
    gcs_path = f"gs://goldkey-scan-vault/{blob_name}"
    
    # 6. Supabase 메타데이터 등록
    file_metadata = {
        "person_id": person_id,
        "agent_id": agent_id,
        "doc_type": doc_type,
        "gcs_path": gcs_path,
        "file_size_bytes": len(file_bytes),
        "mime_type": uploaded_file.type,
        "ocr_status": "pending"
    }
    
    result = supabase.table("gk_scan_files").insert(file_metadata).execute()
    file_id = result.data[0]["file_id"]
    
    return {
        "file_id": file_id,
        "gcs_path": gcs_path
    }
```

**데이터 흐름**:
```
CRM 파일 업로드
    ↓
Fernet 암호화
    ↓
GCS goldkey-scan-vault/{agent_id}/{person_id}/{doc_type}/{timestamp}.enc
    ↓ (메타데이터)
Supabase gk_scan_files 테이블
    ↓ (file_id 반환)
HQ 앱에서 file_id로 GCS 파일 조회
```

---

## CRM → HQ SSO 데이터 흐름

### SSO 토큰 생성 및 전달 (GP-SEC §2)
```python
# CRM 앱: crm_trinity_block.py
def generate_sso_handoff(user_id: str, person_id: str, hq_app_url: str) -> str:
    """HQ 앱으로 SSO 핸드오프."""
    
    # 1. HMAC-SHA256 토큰 생성
    secret = get_env_secret("SSO_SECRET_KEY")
    timestamp = int(time.time())
    message = f"{user_id}:{person_id}:{timestamp}"
    
    auth_token = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # 2. HQ URL 생성 (person_id + auth_token만 전달)
    hq_url = f"{hq_app_url}?auth_token={auth_token}&user_id={user_id}&person_id={person_id}"
    
    return hq_url
```

```python
# HQ 앱: app.py
def verify_sso_token() -> bool:
    """SSO 토큰 검증."""
    
    # 1. URL 파라미터에서 토큰 추출
    auth_token = st.query_params.get("auth_token")
    user_id = st.query_params.get("user_id")
    person_id = st.query_params.get("person_id")
    
    if not auth_token:
        return False
    
    # 2. 토큰 검증 (5분 유효)
    secret = get_env_secret("SSO_SECRET_KEY")
    # ... 검증 로직 ...
    
    if token_valid:
        # 3. 세션 활성화
        st.session_state.authenticated = True
        st.session_state.user_id = user_id
        st.session_state.selected_person_id = person_id
        
        # 4. URL 파라미터 삭제 (GP-SEC §2)
        st.query_params.clear()
        
        return True
    
    return False
```

**데이터 흐름**:
```
CRM 앱
    ↓
HMAC-SHA256 토큰 생성 (user_id + person_id + timestamp)
    ↓
HQ URL 생성 (auth_token + user_id + person_id)
    ↓
사용자 클릭 → HQ 앱 리다이렉트
    ↓
HQ 앱 토큰 검증
    ↓
세션 활성화 (st.session_state.authenticated = True)
    ↓
URL 파라미터 삭제 (st.query_params.clear())
    ↓
HQ 메인 화면 렌더링
```

---

## HQ → Supabase 데이터 흐름

### 1. 증권 파싱 결과 저장 (STEP 4)
```python
# HQ 앱: policy_ocr_engine.py
def save_parsed_policy(person_id: str, parsed_data: dict) -> str:
    """파싱된 증권 데이터를 Supabase에 저장."""
    
    # 1. policies 테이블에 저장
    policy_data = {
        "person_id": person_id,
        "insurance_company": parsed_data["insurance_company"],
        "product_name": parsed_data["product_name"],
        "policy_number": parsed_data["policy_number"],
        "start_date": parsed_data["start_date"],
        "end_date": parsed_data["end_date"],
        "monthly_premium": parsed_data["monthly_premium"]
    }
    
    policy_result = supabase.table("policies").insert(policy_data).execute()
    policy_id = policy_result.data[0]["policy_id"]
    
    # 2. policy_coverages 테이블에 담보 저장
    for coverage in parsed_data["coverages"]:
        coverage_data = {
            "policy_id": policy_id,
            "coverage_name": coverage["name"],
            "coverage_amount": coverage["amount"],
            "coverage_type": coverage["type"]
        }
        supabase.table("policy_coverages").insert(coverage_data).execute()
    
    return policy_id
```

**데이터 흐름**:
```
HQ OCR 처리
    ↓
Google Vision API (텍스트 추출)
    ↓
Gemini 1.5 Pro (구조화된 데이터 파싱)
    ↓
Supabase policies 테이블
    ↓
Supabase policy_coverages 테이블
    ↓
CRM 앱에서 조회 가능
```

### 2. 보장 분석 결과 저장 (STEP 6)
```python
# HQ 앱: engines/kb_scoring_system.py
def save_coverage_analysis(person_id: str, gap_analysis: list) -> None:
    """보장 분석 결과를 Supabase에 저장."""
    
    report_data = {
        "person_id": person_id,
        "report_type": "coverage_analysis",
        "report_data": {
            "gap_analysis": gap_analysis,
            "total_shortage": sum(item["shortage"] for item in gap_analysis),
            "priority_items": [item for item in gap_analysis if item["shortage_rate"] > 70]
        }
    }
    
    supabase.table("gk_unified_reports").insert(report_data).execute()
```

---

## HQ → AI 엔진 데이터 흐름

### 1. AI 전략 수립 (STEP 7)
```python
# HQ 앱: modules/ai_engine.py
def generate_consultation_strategy(person_id: str) -> dict:
    """AI 상담 전략 생성."""
    
    # 1. Supabase에서 데이터 수집
    customer = supabase.table("people").select("*").eq("person_id", person_id).execute().data[0]
    trinity = supabase.table("gk_unified_reports").select("*").eq("person_id", person_id).eq("report_type", "trinity_result").execute().data[0]
    gap_analysis = supabase.table("gk_unified_reports").select("*").eq("person_id", person_id).eq("report_type", "coverage_analysis").execute().data[0]
    
    # 2. Gemini 1.5 Pro 프롬프트 생성
    prompt = f"""
    고객 정보:
    - 이름: {customer['name']}
    - 연령: {calculate_age(customer['birth_date'])}세
    - 월 소득: {trinity['report_data']['monthly_income']}만원
    
    보장 공백:
    {json.dumps(gap_analysis['report_data']['gap_analysis'], ensure_ascii=False, indent=2)}
    
    상담 전략을 수립하세요.
    """
    
    # 3. AI 엔진 호출
    response = gemini_client.generate_content(prompt)
    strategy = parse_strategy_response(response.text)
    
    # 4. Supabase에 저장
    report_data = {
        "person_id": person_id,
        "report_type": "ai_strategy",
        "report_data": strategy
    }
    supabase.table("gk_unified_reports").insert(report_data).execute()
    
    return strategy
```

**데이터 흐름**:
```
HQ 앱
    ↓
Supabase 데이터 수집 (customer, trinity, gap_analysis)
    ↓
Gemini 1.5 Pro API 호출
    ↓
AI 응답 파싱
    ↓
Supabase gk_unified_reports 저장 (report_type: 'ai_strategy')
    ↓
HQ 화면에 표시
```

### 2. 감성 제안 작문 (STEP 8)
```python
# HQ 앱: modules/ai_engine.py
def generate_emotional_proposal(person_id: str, strategy: dict) -> dict:
    """GPT-4로 감성 제안 작문."""
    
    # 1. 고객 정보 조회
    customer = get_customer_info(person_id)
    
    # 2. GPT-4 호출
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "당신은 보험 설계사의 감성적인 제안서를 작성하는 AI입니다."},
            {"role": "user", "content": f"고객: {customer['name']}, 전략: {strategy['summary']}"}
        ]
    )
    
    emotional_message = response.choices[0].message.content
    
    # 3. Supabase 저장
    report_data = {
        "person_id": person_id,
        "report_type": "emotional_proposal",
        "report_data": {"message": emotional_message}
    }
    supabase.table("gk_unified_reports").insert(report_data).execute()
    
    return {"message": emotional_message}
```

---

## AI 엔진 → Supabase 데이터 흐름

### AI 분석 결과 저장 패턴
```python
# 공통 패턴
def save_ai_result(person_id: str, report_type: str, ai_result: dict) -> None:
    """AI 분석 결과를 Supabase에 저장."""
    
    report_data = {
        "person_id": person_id,
        "report_type": report_type,
        "report_data": ai_result,
        "ai_model": ai_result.get("model", "unknown"),
        "ai_tokens_used": ai_result.get("tokens", 0)
    }
    
    supabase.table("gk_unified_reports").insert(report_data).execute()
```

**지원되는 report_type**:
- `trinity_result`: 트리니티 결과
- `coverage_analysis`: 보장 분석
- `ai_strategy`: AI 전략
- `emotional_proposal`: 감성 제안
- `auto_report`: 자동 리포트

---

## GCS → HQ 데이터 흐름

### 스캔 파일 다운로드 및 복호화
```python
# HQ 앱: modules/gcs_utils.py
def download_and_decrypt_scan(file_id: str) -> bytes:
    """GCS에서 스캔 파일 다운로드 및 복호화."""
    
    # 1. Supabase에서 GCS 경로 조회
    file_meta = supabase.table("gk_scan_files").select("*").eq("file_id", file_id).execute().data[0]
    gcs_path = file_meta["gcs_path"]
    
    # 2. GCS에서 다운로드
    blob_name = gcs_path.replace("gs://goldkey-scan-vault/", "")
    bucket = storage_client.bucket("goldkey-scan-vault")
    blob = bucket.blob(blob_name)
    encrypted_data = blob.download_as_bytes()
    
    # 3. Fernet 복호화
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    decrypted_data = cipher.decrypt(encrypted_data)
    
    return decrypted_data
```

**데이터 흐름**:
```
HQ 앱 (file_id)
    ↓
Supabase gk_scan_files 조회 (gcs_path)
    ↓
GCS 다운로드 (암호화된 파일)
    ↓
Fernet 복호화
    ↓
HQ 화면에 표시 또는 OCR 처리
```

---

## Supabase → CRM 동기화

### 실시간 데이터 조회
```python
# CRM 앱: crm_data_fetchers.py
def get_customer_summary(person_id: str) -> dict:
    """고객 요약 정보 조회 (HQ에서 저장한 데이터 포함)."""
    
    # 1. 고객 기본 정보
    customer = supabase.table("people").select("*").eq("person_id", person_id).execute().data[0]
    
    # 2. 보험 계약 목록
    policies = supabase.table("policies").select("*").eq("person_id", person_id).execute().data
    
    # 3. 최신 분석 결과 (HQ에서 저장)
    latest_analysis = supabase.table("gk_unified_reports") \
        .select("*") \
        .eq("person_id", person_id) \
        .order("created_at", desc=True) \
        .limit(1) \
        .execute().data
    
    return {
        "customer": customer,
        "policies": policies,
        "latest_analysis": latest_analysis[0] if latest_analysis else None
    }
```

**데이터 흐름**:
```
CRM 앱 요청
    ↓
Supabase 조회 (people, policies, gk_unified_reports)
    ↓
CRM 화면에 표시
```

---

## 세션 상태 관리

### CRM 세션 상태
```python
# CRM 앱: crm_app.py
def initialize_crm_session():
    """CRM 세션 초기화."""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "selected_person_id" not in st.session_state:
        st.session_state.selected_person_id = None
    
    if "scan_result" not in st.session_state:
        st.session_state.scan_result = None
```

### HQ 세션 상태
```python
# HQ 앱: app.py
def initialize_hq_session():
    """HQ 세션 초기화."""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    
    if "selected_person_id" not in st.session_state:
        st.session_state.selected_person_id = None
    
    if "current_tab" not in st.session_state:
        st.session_state.current_tab = "1000"  # 홈 화면
```

### 세션 휘발성 방어 (GP-SEC §3)
```python
# 핵심 데이터는 즉시 Supabase 저장
def save_critical_data(person_id: str, data: dict) -> None:
    """세션 휘발성 방어: 즉시 Supabase 저장."""
    
    # 세션에만 저장 금지
    # st.session_state.customer_data = data  # ❌ 금지
    
    # 반드시 Supabase 즉시 저장
    supabase.table("people").update(data).eq("person_id", person_id).execute()  # ✅ 올바름
    
    # 세션은 보조적으로만 사용
    st.session_state.customer_data = data
```

---

## 암호화 및 보안 파이프라인

### 1. PII 암호화 (GP-SEC §1)
```python
# 단방향 해시 (인증용)
def hash_contact(contact: str) -> str:
    """연락처 SHA-256 해시."""
    return hashlib.sha256(contact.encode()).hexdigest()

# 양방향 암호화 (복호화 필요)
def encrypt_pii(pii_data: str) -> str:
    """PII Fernet 암호화."""
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    return cipher.encrypt(pii_data.encode()).decode()

def decrypt_pii(encrypted_data: str) -> str:
    """PII Fernet 복호화."""
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    return cipher.decrypt(encrypted_data.encode()).decode()
```

### 2. 파일 암호화 (GP-SEC §4)
```python
def encrypt_file(file_bytes: bytes) -> bytes:
    """파일 Fernet 암호화."""
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    return cipher.encrypt(file_bytes)

def decrypt_file(encrypted_bytes: bytes) -> bytes:
    """파일 Fernet 복호화."""
    cipher = Fernet(get_env_secret("ENCRYPTION_KEY"))
    return cipher.decrypt(encrypted_bytes)
```

---

## 에러 핸들링 및 재시도 로직

### Supabase 에러 핸들링
```python
def safe_supabase_insert(table: str, data: dict, max_retries: int = 3) -> dict:
    """Supabase 삽입 with 재시도."""
    
    for attempt in range(max_retries):
        try:
            result = supabase.table(table).insert(data).execute()
            return result.data[0]
        except Exception as e:
            logging.error(f"Supabase insert error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 지수 백오프
```

### GCS 에러 핸들링
```python
def safe_gcs_upload(blob: Blob, data: bytes, max_retries: int = 3) -> bool:
    """GCS 업로드 with 재시도."""
    
    for attempt in range(max_retries):
        try:
            blob.upload_from_string(data)
            return True
        except Exception as e:
            logging.error(f"GCS upload error (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2 ** attempt)
```

---

## 성능 최적화 전략

### 1. 데이터 캐싱
```python
@st.cache_data(ttl=300)  # 5분 캐시
def get_customer_policies(person_id: str) -> list:
    """고객 보험 목록 조회 (캐싱)."""
    return supabase.table("policies").select("*").eq("person_id", person_id).execute().data
```

### 2. 배치 처리
```python
def batch_insert_coverages(coverages: list[dict]) -> None:
    """담보 배치 삽입."""
    
    # 한 번에 여러 건 삽입
    supabase.table("policy_coverages").insert(coverages).execute()
```

### 3. 비동기 처리
```python
import asyncio

async def async_ocr_processing(file_ids: list[str]) -> list[dict]:
    """비동기 OCR 처리."""
    
    tasks = [process_ocr(file_id) for file_id in file_ids]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 데이터 흐름 요약

### 전체 워크플로우 데이터 흐름
```
1. 고객 등록
   CRM 입력 → Supabase people → Session State

2. 트리니티 산출
   CRM 입력 → 계산 → Supabase gk_unified_reports

3. 증권 스캔
   CRM 업로드 → Fernet 암호화 → GCS → Supabase gk_scan_files

4. OCR 파싱
   HQ → GCS 다운로드 → 복호화 → Vision API → Gemini → Supabase policies

5. KB 비교
   HQ → Supabase policies 조회 → KB 기준 비교 → 계산

6. 보장 공백 진단
   HQ → 분석 → Supabase gk_unified_reports

7. AI 전략
   HQ → Supabase 데이터 수집 → Gemini → Supabase gk_unified_reports

8. 감성 제안
   HQ → GPT-4 → Supabase gk_unified_reports

9. 제안서 생성
   HQ → PDF 생성 → GCS 업로드 → Supabase 메타데이터

10. 카카오톡 전송
    CRM → Kakao API → 전송 이력 Supabase

11. 스케줄링
    CRM → Supabase consultation_history

12. 계약 관리
    CRM → Supabase policies 업데이트
```

---

## 다음 단계

이 보고서는 `REPORT_1_TAB_DETAILS.md`, `REPORT_2_CRM_BLOCKS.md`, `REPORT_3_MASTERPLAN_MAPPING.md`와 함께 전체 시스템 문서화를 구성합니다.

**4개 보고서 완성**:
1. ✅ REPORT_1_TAB_DETAILS.md (HQ 탭별 상세 분석)
2. ✅ REPORT_2_CRM_BLOCKS.md (CRM 블록 기술 명세)
3. ✅ REPORT_3_MASTERPLAN_MAPPING.md (12단계 마스터플랜)
4. ✅ REPORT_4_DATA_FLOW.md (데이터 흐름 아키텍처)
