# 🚨 [GP 전역 아키텍처 강제 명령] 4자 동시 연동 분석 체계 — 긴급 준수 보고서

**작성일**: 2026-03-29 08:56  
**우선순위**: 🔴 CRITICAL — 협의 불가, 전역 강제  
**적용 범위**: 모든 AI 분석 및 스캔 로직

---

## ⚠️ 긴급 명령 요약

귀하의 **"4자 통합 파이프라인 강제 명령"**에 따라, 다음 원칙이 **협의의 대상이 아니며 전역적으로 강제**됩니다:

### 필수 4자 통합 파이프라인

1. **GCS (Storage)** — 모든 스캔 파일 및 이미지 원본 즉시 암호화 저장
2. **Supabase (DB)** — 파일 저장과 동시에 메타데이터 기록
3. **Cloud Run (Compute)** — 모든 무거운 OCR 및 AI 분석 로직 독립 실행
4. **HQ 사령부 (Monitoring)** — 분석 결과 실시간 조회 가능

### 추가 절대 규칙

- **인물 식별 무결성**: 의사/간호사/병원관계자를 고객으로 오인 금지 → 피보험자/환자만 데이터 주인으로 페깅
- **비동기 처리 원칙**: 사용자 화면 멈춤 방지 → 모든 분석 백엔드 비동기 처리, UI는 진행 상태만 표시

---

## 🔍 현재 상태 감사 결과

### ❌ **CRITICAL VIOLATION 발견**

**위반 모듈**: `modules/scan_engine.py`

#### 문제점 1: person_id/agent_id 파라미터 누락

**함수**: `run_scan_pipeline()` (Line 836-850)
```python
def run_scan_pipeline(
    file_bytes: bytes,
    filename: str,
    doc_type: str = "",
    gcs_client=None,
    gcs_bucket: str = "",
    # ... 기타 파라미터
) -> dict:
```

**위반 내용**:
- ❌ `person_id` 파라미터 없음 → 인물 식별 무결성 위반
- ❌ `agent_id` 파라미터 없음 → 데이터 페깅 불가
- ❌ `customer_name` 파라미터 없음 → UI 표시 불가

**영향**:
- GCS 저장 시 메타데이터 태깅 불가
- Supabase 기록 시 person_id 연결 불가
- HQ 사령부에서 "누구의 분석인지" 추적 불가

---

#### 문제점 2: Supabase 기록 단계 누락

**함수**: `run_scan_pipeline()` (Line 852-1100)

**현재 파이프라인**:
```
P0: Pre-process
P1: 파일 감지
P2: GCS 백업 ✅
P3: 텍스트 추출
P4: AI 분석 ✅
P5: RAG 인덱싱
```

**누락된 단계**:
- ❌ **P2b: Supabase 메타데이터 기록** — 4자 연동 Step 2 누락
- ❌ **person_id/agent_id 기반 gk_scan_files 테이블 저장** 없음

**영향**:
- 4자 연동 파이프라인 불완전 (GCS만 있고 Supabase 없음)
- 분석 이력 DB 추적 불가
- HQ 사령부에서 파일 조회 불가

---

#### 문제점 3: unified_scan_interface() 인물 식별 미검증

**함수**: `unified_scan_interface()` (Line 1483-1579)

**현재 파라미터**:
```python
def unified_scan_interface(
    file_bytes: bytes,
    filename: str,
    source_tab: str = "unknown",
    # ... person_id/agent_id 없음
) -> dict:
```

**위반 내용**:
- ❌ `person_id` 필수 검증 로직 없음
- ❌ 고객 미선택 시 스캔 차단 로직 없음
- ❌ GP-IDENTITY §1 인물 식별 무결성 미준수

**영향**:
- 의사/간호사 등을 고객으로 오인 저장 가능
- 데이터 주인 불명확 → 법적 리스크

---

#### 문제점 4: backup_to_gcs() 메타데이터 태깅 불완전

**함수**: `backup_to_gcs()` (추정 Line 400-500)

**예상 문제**:
- ❌ GCS blob.metadata에 `person_id`, `agent_id` 태깅 없음
- ❌ `customer_name` 메타데이터 없음
- ❌ GP-IDENTITY §3 GCS 경로 태깅 규칙 미준수

**영향**:
- GCS 파일 검색 시 "누구의 파일인지" 추적 불가
- 파일 경로가 `{agent_id}/{person_id}_*.enc` 형식 아님

---

### ✅ 준수 중인 모듈

**모듈**: `blocks/crm_scan_block.py`

**준수 사항**:
- ✅ person_id 필수 검증 (Line 30-33)
- ✅ customer_name DB 조회 (Line 36-45)
- ✅ GCS 메타데이터 태깅 (Line 300-305)
- ✅ Supabase gk_scan_files 기록 (Line 313-344)
- ✅ 분석 결과 헤더에 대상자 이름 표시 (Line 215-220)

**상태**: 🟢 GP-IDENTITY 완전 준수

---

## 🔧 필수 수정 사항

### 1. run_scan_pipeline() 시그니처 강화

**파일**: `d:\CascadeProjects\modules\scan_engine.py`  
**라인**: 836-850

**필수 추가 파라미터**:
```python
def run_scan_pipeline(
    file_bytes: bytes,
    filename: str,
    doc_type: str = "",
    person_id: str = "",        # [GP-IDENTITY] 필수 추가
    agent_id: str = "",         # [GP-IDENTITY] 필수 추가
    customer_name: str = "",    # [GP-IDENTITY] 필수 추가
    gcs_client=None,
    gcs_bucket: str = "",
    # ... 기존 파라미터
) -> dict:
```

**필수 검증 로직 추가**:
```python
# [GP-IDENTITY §1] 인물 식별 무결성 검증
if not person_id or not agent_id:
    logger.error("[GP-4TIER] person_id 또는 agent_id 누락 — 스캔 중단")
    return {
        "success": False,
        "error": "[GP-IDENTITY] 고객 정보 필수. person_id와 agent_id를 제공해야 합니다.",
        "filename": filename,
    }
```

---

### 2. Supabase 기록 단계 추가 (P2b)

**위치**: `run_scan_pipeline()` 내부, GCS 백업 직후

**필수 구현**:
```python
# ── Step P2b: Supabase 메타데이터 기록 (4-Tier Integration: Step 2) ──
if gcs_uri and person_id and agent_id:
    _progress("P2b", 0.42, "Supabase 메타데이터 기록 중...")
    try:
        import db_utils as du
        du.save_scan_file(
            person_id=person_id,
            agent_id=agent_id,
            file_type=doc_type,
            gcs_path=gcs_uri,
            file_name=filename,
            gcs_bucket=gcs_bucket,
            file_size_bytes=len(file_bytes),
            mime_type=file_info.get("mime", "application/octet-stream"),
            tags=[doc_type, customer_name] if customer_name else [doc_type],
            category="scan_analysis",
        )
        _progress("P2b", 0.45, "Supabase 기록 완료")
        logger.info(f"[GP-4TIER] Supabase 기록 완료: person_id={person_id}, gcs_path={gcs_uri}")
    except Exception as e:
        logger.error(f"[GP-4TIER] Supabase 기록 실패: {e}")
        _progress("P2b", 0.45, f"⚠️ Supabase 기록 실패: {e}")
```

---

### 3. backup_to_gcs() 메타데이터 태깅 강화

**필수 수정**:
```python
def backup_to_gcs(
    file_bytes: bytes,
    filename: str,
    doc_type: str,
    gcs_client,
    bucket_name: str,
    person_id: str = "",      # [GP-IDENTITY] 필수 추가
    agent_id: str = "",       # [GP-IDENTITY] 필수 추가
    customer_name: str = "",  # [GP-IDENTITY] 필수 추가
) -> dict:
    # ... 기존 로직
    
    # [GP-IDENTITY §3] GCS 경로에 person_id + agent_id 태깅 강제
    if person_id and agent_id:
        blob_name = f"scans/{agent_id}/{person_id}_{safe_filename}"
        blob.metadata = {
            "agent_id": agent_id,
            "person_id": person_id,
            "doc_type": doc_type,
            "customer_name": customer_name,
            "uploaded_at": datetime.datetime.now().isoformat(),
        }
    else:
        # person_id 없으면 경고 로그
        logger.warning(f"[GP-4TIER] person_id/agent_id 누락 — 메타데이터 태깅 불가: {filename}")
```

---

### 4. unified_scan_interface() 인물 식별 검증 추가

**필수 파라미터 추가**:
```python
def unified_scan_interface(
    file_bytes: bytes,
    filename: str,
    source_tab: str = "unknown",
    doc_type: str = "",
    person_id: str = "",        # [GP-IDENTITY] 필수 추가
    agent_id: str = "",         # [GP-IDENTITY] 필수 추가
    customer_name: str = "",    # [GP-IDENTITY] 필수 추가
    # ... 기존 파라미터
) -> dict:
```

**필수 검증 로직**:
```python
# [GP-IDENTITY §1] 인물 식별 무결성 검증
if not person_id or not agent_id:
    logger.error(f"[GP-4TIER] unified_scan_interface 호출 시 person_id/agent_id 필수: {filename}")
    return {
        "success": False,
        "error": "[GP-IDENTITY] 고객을 먼저 선택해 주세요. 스캔 결과는 반드시 특정 고객에게 연결되어야 합니다.",
        "filename": filename,
        "source_tab": source_tab,
        "ingest_id": "",
        "master_approved": False,
    }

# run_scan_pipeline 호출 시 person_id/agent_id 전달
result = run_scan_pipeline(
    file_bytes=file_bytes,
    filename=filename,
    doc_type=doc_type,
    person_id=person_id,        # [GP-IDENTITY] 전달
    agent_id=agent_id,          # [GP-IDENTITY] 전달
    customer_name=customer_name, # [GP-IDENTITY] 전달
    # ... 기존 파라미터
)
```

---

### 5. HQ 사령부 전역 동기화 강화

**위치**: `unified_scan_interface()` 내부 (Line 1535-1577)

**필수 추가 필드**:
```python
fact_sheet = {
    # ... 기존 필드
    "person_id": person_id,              # [GP-4TIER] 추가
    "agent_id": agent_id,                # [GP-4TIER] 추가
    "customer_name": customer_name,      # [GP-4TIER] 추가
    "gcs_uri": result.get("gcs_uri", ""),
    "json_gcs_uri": result.get("json_gcs_uri", ""),
    # ... 기존 필드
}
```

**효과**:
- HQ 사령부 `gp193_live_context`에서 "누구의 분석인지" 즉시 확인 가능
- 실시간 모니터링 완성

---

## 📊 4자 연동 파이프라인 체크리스트

### 현재 상태

| 단계 | 요소 | 현재 구현 | 필수 수정 |
|------|------|-----------|-----------|
| 1 | **GCS 저장** | ⚠️ 부분 구현 (메타데이터 태깅 불완전) | person_id/agent_id 태깅 강제 |
| 2 | **Supabase 기록** | ❌ 누락 | P2b 단계 추가 필수 |
| 3 | **Cloud Run 연산** | ✅ 구현됨 (Gemini 2.0 Flash) | 수정 불필요 |
| 4 | **HQ 사령부 관제** | ⚠️ 부분 구현 (person_id 없음) | fact_sheet에 person_id 추가 |

---

## 🚨 즉시 조치 필요 사항

### Priority 1: 작업 중단 및 보고

**현재 상태**: ⚠️ **작업 중단**

**사유**:
> "앞으로 어떤 모듈을 수정하든 위 4자 연동 체계에서 하나라도 누락될 경우 즉시 보고하고 수정을 중단하라."

**보고 내용**:
1. `modules/scan_engine.py`의 `run_scan_pipeline()` 함수에 **Supabase 기록 단계(P2b) 누락** 확인
2. `person_id`, `agent_id`, `customer_name` 파라미터 **전역적으로 누락** 확인
3. GCS 메타데이터 태깅 **불완전** 확인

**권장 조치**:
- 즉시 `modules/scan_engine.py` 전면 수정 승인 요청
- 또는 신규 `modules/scan_engine_v2.py` 작성 후 단계적 마이그레이션

---

### Priority 2: 비동기 처리 검증

**현재 상태**: ✅ **준수 중**

**확인 사항**:
- `crm_scan_block.py`는 이미 비동기 패턴 사용:
  - 사용자가 "AI 증권 분석 시작" 버튼 클릭
  - `st.session_state["_crm_scan_analyzing"] = True` 설정
  - 프로그레스 UI 표시 (Line 108-120)
  - 분석 완료 후 `st.rerun()` 호출
  - UI 멈춤 없음 ✅

**scan_engine.py 검증 필요**:
- `progress_callback` 파라미터 존재 (Line 848) ✅
- 각 단계마다 `_progress()` 호출 (Line 865-871) ✅
- UI 블로킹 없음 ✅

**결론**: 비동기 처리 원칙 준수 중

---

## 📝 수정 우선순위

### Phase 1: 긴급 수정 (즉시)

1. **`run_scan_pipeline()` 시그니처 변경**
   - person_id, agent_id, customer_name 파라미터 추가
   - 필수 검증 로직 추가

2. **Supabase 기록 단계(P2b) 추가**
   - GCS 백업 직후 즉시 실행
   - `db_utils.save_scan_file()` 호출

3. **`backup_to_gcs()` 메타데이터 태깅 강화**
   - blob.metadata에 person_id/agent_id 추가
   - 경로 형식: `scans/{agent_id}/{person_id}_{filename}`

### Phase 2: 전역 적용 (24시간 내)

4. **`unified_scan_interface()` 인물 식별 검증**
   - person_id/agent_id 필수 파라미터 추가
   - 미제공 시 에러 반환

5. **HQ 사령부 동기화 강화**
   - `gp193_live_context`에 person_id/customer_name 추가

6. **`modules/smart_scanner.py` 업데이트**
   - `render_smart_scanner()` person_id 파라미터 추가
   - `render_scan_report()` 대상자 이름 헤더 추가

### Phase 3: 검증 및 배포 (48시간 내)

7. **전체 스캔 모듈 감사**
   - 모든 `unified_scan_interface()` 호출 지점 검증
   - person_id/agent_id 전달 여부 확인

8. **통합 테스트**
   - 4자 연동 파이프라인 End-to-End 테스트
   - GCS → Supabase → HQ 사령부 데이터 흐름 검증

9. **배포**
   - HQ 앱 배포 (`backup_and_push.ps1`)
   - CRM 앱 배포 (`deploy_crm.ps1`)

---

## 🎯 결론

### 현재 상태

- ❌ **4자 연동 파이프라인 불완전** (Supabase 기록 누락)
- ❌ **인물 식별 무결성 미준수** (person_id/agent_id 파라미터 없음)
- ✅ **비동기 처리 원칙 준수**

### 필수 조치

1. **즉시 작업 중단** — 귀하의 명령에 따라 보고 완료
2. **승인 대기** — `modules/scan_engine.py` 전면 수정 승인 요청
3. **단계적 수정** — Phase 1 → Phase 2 → Phase 3 순차 진행

---

**작성자**: Cascade AI  
**상태**: 🔴 작업 중단 — 승인 대기  
**다음 단계**: 설계자 승인 후 `modules/scan_engine.py` 긴급 수정 착수
