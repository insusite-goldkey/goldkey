# [GP-PHASE2] 트리니티/KB 분석 결과 영구 DB화 — 통합 가이드

**작성일**: 2026-03-28  
**목적**: 세션 휘발 방지 — 분석 결과를 DB에 영구 저장하여 HQ에서 조회 가능

---

## 📋 목차

1. [개요](#개요)
2. [구현 완료 항목](#구현-완료-항목)
3. [통합 방법](#통합-방법)
4. [CRM 앱 통합](#crm-앱-통합)
5. [HQ 앱 통합](#hq-앱-통합)
6. [테스트 시나리오](#테스트-시나리오)
7. [문제 해결](#문제-해결)

---

## 개요

### 해결하는 문제

**"치명적 단절 지점 1번"** — 분석 결과가 세션에만 저장되어 휘발되는 문제

- ❌ **기존**: CRM에서 트리니티/KB 분석 → 세션 저장 → 새로고침 시 소실
- ✅ **개선**: CRM에서 분석 → **DB 영구 저장** → HQ에서 언제든지 조회 가능

### 핵심 기능

1. **트리니티 분석 결과 DB화**: `gk_trinity_analysis` 테이블에 저장
2. **KB 분석 결과 DB화**: `gk_kb_analysis` 테이블에 저장
3. **통합 분석 결과 DB화**: `gk_integrated_analysis` 테이블에 저장
4. **HQ 뷰어**: M-SECTION에서 과거 분석 이력 조회 가능

---

## 구현 완료 항목

### ✅ 1. DB 스키마 (SQL)

**파일**: `phase2_analysis_persistence_schema.sql`

**3개 테이블 생성**:
- `gk_trinity_analysis` — 트리니티 분석 결과 (건보료 역산 × KB 표준)
- `gk_kb_analysis` — KB 7대 스탠다드 분석 결과
- `gk_integrated_analysis` — 통합 분석 결과 (트리니티 + KB + NIBO)

**트리거**: `updated_at` 자동 갱신  
**RLS**: service_role 전용 정책

### ✅ 2. DB 함수 (Python)

**파일**: `db_utils.py` (§23-§25 추가, +339줄)

**§23 트리니티 분석** (3개 함수):
- `save_trinity_analysis()` — 분석 결과 저장
- `get_trinity_analysis_history()` — 이력 조회
- `get_latest_trinity_analysis()` — 최신 분석 조회

**§24 KB 분석** (3개 함수):
- `save_kb_analysis()` — 분석 결과 저장
- `get_kb_analysis_history()` — 이력 조회
- `get_latest_kb_analysis()` — 최신 분석 조회

**§25 통합 분석** (3개 함수):
- `save_integrated_analysis()` — 통합 결과 저장
- `get_integrated_analysis_history()` — 이력 조회
- `get_latest_integrated_analysis()` — 최신 분석 조회

### ✅ 3. HQ UI 뷰어 (Python)

**파일**: `hq_phase2_analysis_viewer.py` (총 580줄)

**렌더링 함수**:
- `render_analysis_history_dashboard()` — 통합 대시보드 (3개 탭)
- `render_trinity_history()` — 트리니티 분석 이력
- `render_kb_history()` — KB 분석 이력
- `render_integrated_history()` — 통합 분석 이력
- `render_quick_analysis_summary()` — 빠른 요약 위젯

---

## 통합 방법

### [1단계] Supabase SQL 실행

```bash
# Supabase Dashboard → SQL Editor
# phase2_analysis_persistence_schema.sql 전체 실행
```

**확인 쿼리**:
```sql
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('gk_trinity_analysis', 'gk_kb_analysis', 'gk_integrated_analysis');
```

### [2단계] CRM 앱 통합

CRM 앱에서 분석 완료 시 DB 저장 로직 추가.

---

## CRM 앱 통합

### 통합 위치 1: 트리니티 분석 (shared_components.py 또는 CRM 분석 화면)

**기존 코드 (세션 저장만)**:
```python
# 트리니티 분석 실행
_t_result = calculate_trinity_metrics(_run_nhi)
st.session_state["_trinity_calc_result"] = _t_result
```

**개선 코드 (DB 저장 추가)**:
```python
import db_utils as du

# 트리니티 분석 실행
_t_result = calculate_trinity_metrics(_run_nhi)
st.session_state["_trinity_calc_result"] = _t_result

# [GP-PHASE2] DB 영구 저장
if _run_pid and _run_aid:  # person_id, agent_id 확보 시
    _income_meta = _t_result.get("_income_meta", {})
    
    analysis_id = du.save_trinity_analysis(
        person_id=_run_pid,
        agent_id=_run_aid,
        nhis_premium=_run_nhi,
        analysis_data=_t_result,
        monthly_required=_income_meta.get("m_req", 0),
        gross_monthly=_income_meta.get("gross_monthly", 0),
        gross_annual=_income_meta.get("gross_annual", 0),
        net_annual=_income_meta.get("net_annual", 0),
        deduction_rate=_income_meta.get("deduction_rate", 0),
        income_breakdown=_income_meta.get("breakdown", {}),
        coverage_needs=_income_meta.get("coverage_needs", {}),
        kb7_metadata=_t_result.get("_kb7_meta", []),
        employment_type="직장",
        ltc_included=False,
    )
    
    if analysis_id:
        st.success(f"✅ 트리니티 분석 결과가 DB에 저장되었습니다. (ID: {analysis_id[:8]}...)")
```

### 통합 위치 2: KB 분석 (hq_app_impl.py 또는 CRM KB 화면)

**기존 코드 (세션 저장만)**:
```python
# KB 분석 실행
_kb_report = run_kb_analysis(_kb_items_for_run, age=_run_age, gender=_run_gender)
st.session_state["_kb_report"] = _kb_report
```

**개선 코드 (DB 저장 추가)**:
```python
import db_utils as du

# KB 분석 실행
_kb_report = run_kb_analysis(_kb_items_for_run, age=_run_age, gender=_run_gender)
st.session_state["_kb_report"] = _kb_report

# [GP-PHASE2] DB 영구 저장
if _run_pid and _run_aid and _kb_report:
    analysis_id = du.save_kb_analysis(
        person_id=_run_pid,
        agent_id=_run_aid,
        analysis_data=_kb_report.to_dict() if hasattr(_kb_report, 'to_dict') else {},
        kb_total_score=_kb_report.total_score if hasattr(_kb_report, 'total_score') else 0,
        kb_grade=_kb_report.grade if hasattr(_kb_report, 'grade') else "",
        customer_age=_run_age,
        customer_gender=_run_gender,
        category_scores=_kb_report.categories if hasattr(_kb_report, 'categories') else [],
        raw_coverages=_kb_items_for_run,
    )
    
    if analysis_id:
        st.success(f"✅ KB 분석 결과가 DB에 저장되었습니다. (ID: {analysis_id[:8]}...)")
```

### 통합 위치 3: 통합 분석 (engines/analysis_hub.py)

**기존 코드 (세션 저장만)**:
```python
# 통합 분석 실행
report = execute_integrated_analysis(...)
session_state["integrated_report"] = report
session_state["n_section_bridge"] = report.to_bridge_packet()
```

**개선 코드 (DB 저장 추가)**:
```python
import db_utils as du

# 통합 분석 실행
report = execute_integrated_analysis(...)
session_state["integrated_report"] = report
session_state["n_section_bridge"] = report.to_bridge_packet()

# [GP-PHASE2] DB 영구 저장
if person_id and agent_id:
    # 개별 분석 ID 저장
    trinity_id = ""
    kb_id = ""
    
    if report.trinity:
        trinity_id = du.save_trinity_analysis(
            person_id=person_id,
            agent_id=agent_id,
            nhis_premium=report.trinity.get("nhis_premium", 0),
            analysis_data=report.trinity,
            monthly_required=report.trinity.get("monthly_required", 0),
            # ... 기타 파라미터
        )
    
    if report.kb:
        kb_id = du.save_kb_analysis(
            person_id=person_id,
            agent_id=agent_id,
            analysis_data=report.kb,
            kb_total_score=report.kb.get("total_score", 0),
            kb_grade=report.kb.get("grade", ""),
            # ... 기타 파라미터
        )
    
    # 통합 분석 저장
    integrated_id = du.save_integrated_analysis(
        person_id=person_id,
        agent_id=agent_id,
        analysis_type="full",
        trinity_analysis_id=trinity_id,
        kb_analysis_id=kb_id,
        integrated_report=report.to_dict(),
        bridge_packet=report.to_bridge_packet(),
        nibo_status="done" if report.nibo else "pending",
        nibo_data=report.nibo,
    )
```

---

## HQ 앱 통합

### 통합 위치: M-SECTION 또는 고객 대시보드

**파일**: `hq_app_impl.py`

```python
# ═══════════════════════════════════════════════════════════════
# [GP-PHASE2] HQ 분석 이력 뷰어 통합
# ═══════════════════════════════════════════════════════════════

from hq_phase2_analysis_viewer import (
    render_analysis_history_dashboard,
    render_quick_analysis_summary
)

def render_m_section_customer_dashboard(person_id: str, agent_id: str):
    """
    [GP-PHASE2] M-SECTION 고객 대시보드 — 분석 이력 통합.
    """
    if not person_id or not agent_id:
        st.warning("⚠️ 고객 정보가 없습니다.")
        return
    
    # 기존 대시보드 (Key Metrics, 가족관계도, 보장공백 등)
    # ... 기존 UI ...
    
    st.markdown("---")
    
    # [GP-PHASE2] 빠른 분석 요약 (상단 배치)
    st.markdown("## 📊 최신 분석 요약")
    render_quick_analysis_summary(person_id, agent_id)
    
    st.markdown("---")
    
    # [GP-PHASE2] 전체 분석 이력 대시보드
    st.markdown("## 📈 분석 이력 상세")
    render_analysis_history_dashboard(person_id, agent_id, key_prefix="_hq_m_analysis")
```

### 호출 예시

```python
# hq_app_impl.py의 M-SECTION 내부
if current_sector == "m_section":
    if st.session_state.get("selected_customer_id"):
        person_id = st.session_state["selected_customer_id"]
        agent_id = st.session_state.get("user_id", "")
        
        # [GP-PHASE2] 분석 이력 포함 대시보드 렌더링
        render_m_section_customer_dashboard(person_id, agent_id)
```

---

## 테스트 시나리오

### 시나리오 1: 트리니티 분석 → DB 저장 → HQ 조회

1. **CRM 앱 접속**
2. 고객 선택 → 트리니티 분석 화면
3. 건보료 입력 (예: 150,000원) → "분석 실행" 클릭
4. **확인**: "✅ 트리니티 분석 결과가 DB에 저장되었습니다." 메시지 표시
5. **HQ 앱 접속**
6. 동일 고객 선택 → M-SECTION
7. "📊 최신 분석 요약" 위젯 확인
8. **확인**: 필요 월소득, 분석 일시 표시됨
9. "📈 분석 이력 상세" → "🎯 트리니티 분석" 탭
10. **확인**: 최신 분석 카드에 건보료 역산 결과, 담보별 Gap 분석 표시

### 시나리오 2: KB 분석 → DB 저장 → HQ 조회

1. **CRM 앱** → KB 분석 화면
2. 담보 입력 (암진단비 3천만원, 뇌졸중 2천만원 등)
3. 나이/성별 입력 → "분석 실행" 클릭
4. **확인**: "✅ KB 분석 결과가 DB에 저장되었습니다." 메시지 표시
5. **HQ 앱** → M-SECTION
6. "📊 최신 분석 요약" 위젯 확인
7. **확인**: KB 등급 (S/A/B/C/D/F), 종합 점수 표시됨
8. "📈 분석 이력 상세" → "📋 KB 분석" 탭
9. **확인**: 최신 분석 카드에 등급, 점수, 카테고리별 점수 차트 표시

### 시나리오 3: 통합 분석 → DB 저장 → HQ 조회

1. **CRM 앱** → 통합 분석 화면 (트리니티 + KB + NIBO)
2. 전체 분석 실행
3. **확인**: 3개 분석 결과 모두 DB 저장 메시지 표시
4. **HQ 앱** → M-SECTION
5. "📈 분석 이력 상세" → "🔗 통합 분석" 탭
6. **확인**: 통합 분석 카드에 트리니티/KB/NIBO 포함 여부 표시

### 시나리오 4: 세션 휘발 방지 확인

1. **CRM 앱**에서 트리니티 분석 실행
2. 브라우저 새로고침 (F5)
3. **기존**: 세션 소실로 분석 결과 사라짐
4. **개선**: HQ 앱에서 여전히 조회 가능
5. **확인**: DB에 영구 저장되어 언제든지 조회 가능

---

## 문제 해결

### Q1: DB 저장이 실패합니다.

**확인**:
1. Supabase SQL 실행 완료 여부
   ```sql
   SELECT tablename FROM pg_tables 
   WHERE tablename IN ('gk_trinity_analysis', 'gk_kb_analysis', 'gk_integrated_analysis');
   ```
2. `person_id`, `agent_id` 파라미터가 정상 전달되는지 확인
3. `db_utils.py`의 `save_trinity_analysis()` 함수 import 확인

### Q2: HQ에서 분석 이력이 표시되지 않습니다.

**확인**:
1. `hq_phase2_analysis_viewer.py` 파일 존재 확인
2. `hq_app_impl.py`에 import 추가 확인
   ```python
   from hq_phase2_analysis_viewer import render_analysis_history_dashboard
   ```
3. `person_id`, `agent_id` 파라미터 정상 전달 확인
4. Supabase RLS 정책 확인 (service_role 접근 가능 여부)

### Q3: JSON 필드가 파싱되지 않습니다.

**확인**:
1. `db_utils.py`의 조회 함수에서 JSON 파싱 로직 확인
   ```python
   for json_field in ["analysis_data", "income_breakdown", ...]:
       if r.get(json_field) and isinstance(r[json_field], str):
           r[json_field] = json.loads(r[json_field])
   ```
2. DB에 저장된 데이터가 유효한 JSON 형식인지 확인

### Q4: 분석 결과가 중복 저장됩니다.

**원인**: `UNIQUE` 제약 조건이 `(person_id, agent_id, analyzed_at)`로 설정되어 있어, 동일 시간에 여러 번 저장 시 중복 가능

**해결**:
- 분석 실행 전 중복 체크 로직 추가
- 또는 `analyzed_at`를 초 단위가 아닌 밀리초 단위로 저장

---

## 완료 보고

### ✅ 구현 완료 항목

1. **DB 스키마**: 3개 테이블 + 3개 트리거 생성
2. **DB 함수**: 9개 CRUD 함수 추가 (§23-§25)
3. **HQ UI**: 분석 이력 뷰어 5개 함수
4. **통합 코드**: CRM/HQ 통합 예시 코드 작성

### 📦 생성된 파일

- `phase2_analysis_persistence_schema.sql` — SQL 스키마 (280줄)
- `db_utils.py` (§23-§25 추가, +339줄) — DB 함수
- `hq_phase2_analysis_viewer.py` — HQ UI 뷰어 (580줄)
- `PHASE2_INTEGRATION_GUIDE.md` — 통합 가이드 (본 문서)

### 🚀 배포 준비 완료

**다음 단계**:
1. Supabase SQL 실행
2. CRM 앱 통합 코드 추가
3. HQ 앱 통합 코드 추가
4. 테스트 시나리오 검증
5. 배포 스크립트 실행

---

**작성자**: Cascade AI  
**검토자**: 설계자 승인 필요  
**배포일**: 2026-03-28 (예정)
