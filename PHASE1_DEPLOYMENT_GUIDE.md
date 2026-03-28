# [GP-PHASE1] 다중 관계망 태깅 및 철통 보안 구축 — 배포 가이드

**작성일**: 2026-03-28  
**목적**: 8가지 관계망 태깅 + 보험계약 이력 + 상담일정 + 이중화 백업 시스템 구축

---

## 📋 목차

1. [개요](#개요)
2. [구현 완료 항목](#구현-완료-항목)
3. [배포 순서](#배포-순서)
4. [SQL 스키마 실행](#sql-스키마-실행)
5. [CRM 앱 통합](#crm-앱-통합)
6. [HQ 앱 통합](#hq-앱-통합)
7. [테스트 시나리오](#테스트-시나리오)
8. [보안 체크리스트](#보안-체크리스트)

---

## 개요

### 핵심 기능
- **8가지 관계망 태깅**: 상담자, 계약자, 피보험자, 가족, 소개자, 동일법인, 동일단체, 친인척
- **보험계약 이력**: 자사계약, 타부점계약, 해지계약 분류 관리
- **상담 일정**: 초회상담, 보장분석, 증권점검, 계약체결, 사후관리 기록
- **이중화 백업**: gk_people 테이블 자동 미러링 (정보보호법 준수)
- **PII 암호화**: Fernet(AES-128-CBC) 양방향 암호화 적용

### 아키텍처 원칙
- **CRM 앱**: 데이터 입력/수정 전담 (CRUD)
- **HQ 앱**: 데이터 조회/시각화 전담 (Read-Only)
- **DB 레이어**: db_utils.py 공통 함수 사용
- **보안**: 모든 PII는 암호화 저장, 백업 테이블 자동 생성

---

## 구현 완료 항목

### ✅ 1. DB 스키마 (SQL)
- **파일**: `phase1_multi_tagging_security_schema.sql`
- **테이블**:
  - `gk_people_backup` — 고객 정보 이중화 백업
  - `gk_relationship_tags` — 8가지 관계망 태깅
  - `gk_insurance_contracts_detail` — 보험계약 상세 이력
  - `gk_consultation_schedule` — 상담 일정 및 내용
- **트리거**: `gk_people_auto_backup()` — INSERT/UPDATE 시 자동 백업
- **RLS**: 모든 테이블에 Row Level Security 적용

### ✅ 2. 암호화 로직 (Python)
- **파일**: `shared_components.py` (기존)
- **함수**:
  - `encrypt_pii(plaintext)` — Fernet 양방향 암호화
  - `decrypt_pii(ciphertext)` — Fernet 복호화
- **적용 대상**: 이름, 연락처, 주소, 계약자명, 피보험자명

### ✅ 3. DB 유틸리티 함수 (Python)
- **파일**: `db_utils.py` (§19-§22 추가)
- **함수**:
  - **관계망 태깅**: `add_relationship_tag()`, `get_relationship_tags()`, `remove_relationship_tag()`, `get_network_summary()`
  - **보험계약**: `add_insurance_contract()`, `get_insurance_contracts()`, `update_insurance_contract()`, `delete_insurance_contract()`
  - **상담일정**: `add_consultation_schedule()`, `get_consultation_schedules()`, `complete_consultation()`
  - **백업 조회**: `get_backup_history()`, `restore_from_backup()`

### ✅ 4. CRM UI 블록 (Python)
- **파일**: `blocks/crm_phase1_network_block.py`
- **함수**:
  - `render_network_tagging_panel()` — 8가지 태그 입력/관리
  - `render_insurance_contracts_panel()` — 보험계약 이력 입력
  - `render_consultation_schedule_panel()` — 상담 일정 입력

### ✅ 5. HQ UI 뷰어 (Python)
- **파일**: `hq_phase1_network_viewer.py`
- **함수**:
  - `render_network_dashboard()` — 8가지 관계망 시각화
  - `render_backup_history_panel()` — 백업 이력 조회

---

## 배포 순서

### [1단계] Supabase SQL 실행

```bash
# Supabase SQL Editor에서 실행
1. phase1_multi_tagging_security_schema.sql 전체 복사
2. Supabase Dashboard → SQL Editor → New Query
3. 붙여넣기 후 Run
4. 성공 확인: 4개 테이블 + 1개 트리거 생성
```

**확인 쿼리**:
```sql
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('gk_people_backup', 'gk_relationship_tags', 
                    'gk_insurance_contracts_detail', 'gk_consultation_schedule');
```

### [2단계] db_utils.py 배포

```bash
# 이미 완료됨 (§19-§22 추가됨)
# 확인: db_utils.py 파일 하단에 VALID_TAG_TYPES 상수 존재 확인
```

### [3단계] CRM 앱 통합

**파일**: `crm_app_impl.py` 또는 고객 상세 화면 파일

```python
# Import 추가
from blocks.crm_phase1_network_block import (
    render_network_tagging_panel,
    render_insurance_contracts_panel,
    render_consultation_schedule_panel
)

# 고객 상세 페이지에 추가 (예: contact 탭 내부)
def render_customer_detail(person_id, agent_id):
    # ... 기존 고객 정보 표시 ...
    
    st.markdown("---")
    
    # [GP-PHASE1] 8가지 관계망 태깅
    with st.expander("🏷️ 관계망 태깅", expanded=False):
        render_network_tagging_panel(person_id, agent_id, key_prefix="_crm_net")
    
    # [GP-PHASE1] 보험계약 이력
    with st.expander("📋 보험계약 이력", expanded=False):
        render_insurance_contracts_panel(person_id, agent_id, key_prefix="_crm_ins")
    
    # [GP-PHASE1] 상담 일정
    with st.expander("📅 상담 일정", expanded=False):
        render_consultation_schedule_panel(person_id, agent_id, key_prefix="_crm_sch")
```

### [4단계] HQ 앱 통합

**파일**: `hq_app_impl.py` — M-SECTION 또는 고객 대시보드

```python
# Import 추가
from hq_phase1_network_viewer import (
    render_network_dashboard,
    render_backup_history_panel
)

# M-SECTION 또는 고객 상세 화면에 추가
def render_customer_dashboard_hq(person_id, agent_id):
    # ... 기존 대시보드 ...
    
    st.markdown("---")
    
    # [GP-PHASE1] 관계망 네트워크 대시보드
    render_network_dashboard(person_id, agent_id, key_prefix="_hq_net")
    
    st.markdown("---")
    
    # [GP-PHASE1] 백업 이력 (관리자 전용)
    with st.expander("🔒 백업 이력 조회", expanded=False):
        render_backup_history_panel(person_id, key_prefix="_hq_backup")
```

### [5단계] 배포 실행

```powershell
# CRM 배포
powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\deploy_crm.ps1"

# HQ 배포
powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\backup_and_push.ps1"
```

---

## SQL 스키마 실행

### 실행 방법

1. **Supabase Dashboard 접속**
   - https://supabase.com/dashboard
   - 프로젝트 선택

2. **SQL Editor 열기**
   - 좌측 메뉴 → SQL Editor
   - New Query 클릭

3. **스키마 실행**
   ```sql
   -- phase1_multi_tagging_security_schema.sql 내용 전체 붙여넣기
   -- Run 버튼 클릭
   ```

4. **실행 결과 확인**
   ```sql
   -- 테이블 생성 확인
   SELECT tablename FROM pg_tables 
   WHERE schemaname = 'public' 
     AND tablename LIKE 'gk_%';
   
   -- 트리거 확인
   SELECT tgname FROM pg_trigger 
   WHERE tgname = 'trg_gk_people_auto_backup';
   ```

### 예상 결과

```
✅ gk_people_backup (테이블)
✅ gk_relationship_tags (테이블)
✅ gk_insurance_contracts_detail (테이블)
✅ gk_consultation_schedule (테이블)
✅ trg_gk_people_auto_backup (트리거)
✅ RLS 정책 4개 생성
```

---

## CRM 앱 통합

### 통합 위치

**파일**: `crm_app_impl.py` 또는 `blocks/crm_contact_detail_block.py`

### 통합 코드

```python
# ═══════════════════════════════════════════════════════════════
# [GP-PHASE1] 고객 상세 페이지 확장
# ═══════════════════════════════════════════════════════════════

from blocks.crm_phase1_network_block import (
    render_network_tagging_panel,
    render_insurance_contracts_panel,
    render_consultation_schedule_panel
)

def render_customer_detail_extended(person_id: str, agent_id: str):
    """
    [GP-PHASE1] 고객 상세 페이지 — 8가지 관계망 태깅 통합.
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    # 기존 고객 정보 표시
    customer = du.get_customer(person_id, agent_id)
    if not customer:
        st.error("❌ 고객을 찾을 수 없습니다.")
        return
    
    # ... 기존 UI (이름, 연락처, 직업 등) ...
    
    st.markdown("---")
    st.markdown("### 🏷️ [GP-PHASE1] 고급 관리 기능")
    
    # 탭으로 분리
    tab1, tab2, tab3 = st.tabs(["🏷️ 관계망 태깅", "📋 보험계약 이력", "📅 상담 일정"])
    
    with tab1:
        render_network_tagging_panel(person_id, agent_id, key_prefix="_crm_net")
    
    with tab2:
        render_insurance_contracts_panel(person_id, agent_id, key_prefix="_crm_ins")
    
    with tab3:
        render_consultation_schedule_panel(person_id, agent_id, key_prefix="_crm_sch")
```

### 호출 예시

```python
# crm_app_impl.py의 contact 탭 내부
if current_tab == "contact":
    if st.session_state.get("selected_customer_id"):
        person_id = st.session_state["selected_customer_id"]
        agent_id = st.session_state.get("user_id", "")
        
        # [GP-PHASE1] 확장 고객 상세 페이지 렌더링
        render_customer_detail_extended(person_id, agent_id)
```

---

## HQ 앱 통합

### 통합 위치

**파일**: `hq_app_impl.py` — M-SECTION 또는 고객 대시보드

### 통합 코드

```python
# ═══════════════════════════════════════════════════════════════
# [GP-PHASE1] HQ 고객 대시보드 확장
# ═══════════════════════════════════════════════════════════════

from hq_phase1_network_viewer import (
    render_network_dashboard,
    render_backup_history_panel
)

def render_hq_customer_dashboard(person_id: str, agent_id: str):
    """
    [GP-PHASE1] HQ 고객 대시보드 — 8가지 관계망 네트워크 시각화.
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    # 기존 대시보드 (Key Metrics, 가족관계도, 보장공백 등)
    # ... 기존 UI ...
    
    st.markdown("---")
    st.markdown("## 🕸️ [GP-PHASE1] 관계망 네트워크 분석")
    
    # 관계망 대시보드
    render_network_dashboard(person_id, agent_id, key_prefix="_hq_net")
    
    st.markdown("---")
    
    # 백업 이력 (관리자 전용)
    if st.session_state.get("is_admin", False):
        with st.expander("🔒 시스템 백업 이력 조회", expanded=False):
            render_backup_history_panel(person_id, key_prefix="_hq_backup")
```

### 호출 예시

```python
# hq_app_impl.py의 M-SECTION 내부
if current_sector == "m_section":
    if st.session_state.get("selected_customer_id"):
        person_id = st.session_state["selected_customer_id"]
        agent_id = st.session_state.get("user_id", "")
        
        # [GP-PHASE1] HQ 대시보드 렌더링
        render_hq_customer_dashboard(person_id, agent_id)
```

---

## 테스트 시나리오

### 시나리오 1: 관계망 태깅

1. **CRM 앱 접속**
2. 고객 선택 → contact 탭
3. "🏷️ 관계망 태깅" 확장
4. 태그 추가:
   - 태그 유형: "상담자"
   - 관계 대상: (없음)
   - 메모: "2026년 3월 초회 상담 진행"
   - "🏷️ 태그 추가" 클릭
5. **확인**: 태그가 목록에 표시됨
6. **HQ 앱 접속**
7. 동일 고객 선택
8. "🕸️ 관계망 네트워크 분석" 섹션 확인
9. **확인**: "상담자" 태그 카운트 1, 상세 내용 표시됨

### 시나리오 2: 보험계약 이력

1. **CRM 앱** → "📋 보험계약 이력" 탭
2. "➕ 계약 추가" 탭 선택
3. 입력:
   - 계약 상태: "자사계약"
   - 보험회사: "삼성생명"
   - 보험상품명: "삼성생명 무배당 종신보험"
   - 계약년월: "202601"
   - 월납입보험료: 150000
   - 비고: "암진단비 3천만원 특약 포함"
4. "💾 계약 저장" 클릭
5. **확인**: "🏢 자사계약" 탭에 표시됨
6. **HQ 앱** → "📋 보험계약 이력 요약" 확인
7. **확인**: 자사계약 1건, 최근 계약 이력에 표시됨

### 시나리오 3: 상담 일정

1. **CRM 앱** → "📅 상담 일정" 탭
2. "➕ 일정 추가" 선택
3. 입력:
   - 상담 유형: "보장분석"
   - 상담 예정일: "20260405"
   - 상담 시간: "1400"
   - 상담 내용 요약: "KB 7대 보장 분석 예정"
   - 다음 액션: "분석 결과 리포트 발송"
4. "📅 일정 저장" 클릭
5. **확인**: "⏳ 예정 상담" 탭에 표시됨
6. **HQ 앱** → "📅 상담 일정 요약" 확인
7. **확인**: 예정 상담 1건 표시

### 시나리오 4: 이중화 백업

1. **CRM 앱**에서 고객 정보 수정 (이름, 연락처 등)
2. "저장" 클릭
3. **Supabase SQL Editor**에서 확인:
   ```sql
   SELECT * FROM gk_people_backup 
   WHERE person_id = 'xxx-xxx-xxx' 
   ORDER BY backup_created_at DESC 
   LIMIT 1;
   ```
4. **확인**: 최신 백업 레코드 생성됨
5. **HQ 앱** → "🔒 백업 이력 조회" 확장
6. **확인**: 백업 이력 목록에 표시됨

---

## 보안 체크리스트

### ✅ PII 암호화

- [ ] `gk_people.name` — Fernet 암호화 적용
- [ ] `gk_people.contact` — Fernet 암호화 적용
- [ ] `gk_people.address` — Fernet 암호화 적용
- [ ] `gk_insurance_contracts_detail.contractor_name` — Fernet 암호화 적용
- [ ] `gk_insurance_contracts_detail.insured_name` — Fernet 암호화 적용

### ✅ 이중화 백업

- [ ] `gk_people_auto_backup()` 트리거 정상 작동 확인
- [ ] INSERT 시 백업 생성 확인
- [ ] UPDATE 시 백업 생성 확인
- [ ] 백업 테이블 RLS 정책 적용 확인

### ✅ RLS (Row Level Security)

- [ ] `gk_people_backup` — service_role만 접근 가능
- [ ] `gk_relationship_tags` — service_role만 접근 가능
- [ ] `gk_insurance_contracts_detail` — service_role만 접근 가능
- [ ] `gk_consultation_schedule` — service_role만 접근 가능

### ✅ URL 파라미터 보안

- [ ] URL에 PII(이름, 전화번호) 원문 포함 금지
- [ ] person_id (UUID)만 사용
- [ ] 암호화된 cid 또는 token 사용

### ✅ 로그 보안

- [ ] 로그에 PII 평문 출력 금지
- [ ] 디버그 로그에 암호화된 값만 출력
- [ ] 에러 메시지에 민감 정보 포함 금지

---

## 문제 해결 (Troubleshooting)

### Q1: 트리거가 작동하지 않습니다.

**확인**:
```sql
-- 트리거 존재 확인
SELECT tgname, tgenabled FROM pg_trigger 
WHERE tgname = 'trg_gk_people_auto_backup';

-- 트리거 재생성
DROP TRIGGER IF EXISTS trg_gk_people_auto_backup ON gk_people;
CREATE TRIGGER trg_gk_people_auto_backup
    AFTER INSERT OR UPDATE ON gk_people
    FOR EACH ROW EXECUTE FUNCTION gk_people_auto_backup();
```

### Q2: 암호화된 데이터가 복호화되지 않습니다.

**확인**:
1. `ENCRYPTION_KEY` 환경변수 설정 확인
2. `shared_components.py`의 `encrypt_pii()`, `decrypt_pii()` 함수 정상 작동 확인
3. Fernet 키 형식 확인 (32바이트 base64 인코딩)

### Q3: CRM UI 블록이 표시되지 않습니다.

**확인**:
1. `blocks/crm_phase1_network_block.py` 파일 존재 확인
2. `crm_app_impl.py`에 import 추가 확인
3. `render_network_tagging_panel()` 호출 확인
4. Streamlit 재시작

### Q4: HQ에서 데이터가 조회되지 않습니다.

**확인**:
1. `hq_phase1_network_viewer.py` 파일 존재 확인
2. `hq_app_impl.py`에 import 추가 확인
3. `person_id`, `agent_id` 파라미터 정상 전달 확인
4. Supabase RLS 정책 확인

---

## 완료 보고

### ✅ 구현 완료 항목

1. **DB 스키마**: 4개 테이블 + 1개 트리거 생성
2. **암호화 로직**: Fernet 양방향 암호화 적용
3. **이중화 로직**: 자동 백업 트리거 구현
4. **DB 함수**: 8가지 관계망 + 보험계약 + 상담일정 CRUD 함수
5. **CRM UI**: 3개 패널 (관계망 태깅, 보험계약, 상담일정)
6. **HQ UI**: 관계망 대시보드 + 백업 이력 조회

### 📦 생성된 파일

- `phase1_multi_tagging_security_schema.sql` — SQL 스키마
- `db_utils.py` (§19-§22 추가) — DB 유틸리티 함수
- `blocks/crm_phase1_network_block.py` — CRM UI 블록
- `hq_phase1_network_viewer.py` — HQ UI 뷰어
- `db_utils_phase1_extension.py` — 확장 함수 참고용
- `PHASE1_DEPLOYMENT_GUIDE.md` — 배포 가이드 (본 문서)

### 🚀 배포 준비 완료

**다음 단계**:
1. Supabase SQL 실행
2. CRM 앱 통합 코드 추가
3. HQ 앱 통합 코드 추가
4. 배포 스크립트 실행
5. 테스트 시나리오 검증

---

**작성자**: Cascade AI  
**검토자**: 설계자 승인 필요  
**배포일**: 2026-03-28 (예정)
