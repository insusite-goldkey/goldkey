# CRM 분석 3대 블록 — Cursor 마이그레이션 보고서
# Goldkey AI Masters 2026

> **목적:** `crm_app.py`에 인라인으로 작성된 분석 3대 섹션을  
> `blocks/` 독립 모듈로 추출하여 Cursor 마이그레이션 준비를 완료한다.  
> **기준일:** 2026-03-24  
> **추출 대상 원본:** `crm_app.py`

---

## 1. 추출 대상 3대 섹션 요약

| # | 원본 스크린 | 원본 라인 | 새 블록 파일 | 핵심 기능 |
|---|---|---|---|---|
| **A** | `contact` RIGHT PANE 섹션 A·B | L1660–L1870 | `blocks/crm_trinity_block.py` | 트리니티 가처분 소득 산출기 |
| **B** | SCREEN 3 `_spa_screen == "nibo"` | L2363–L2472 | `blocks/crm_nibo_screen_block.py` | 내보험다보여 동의·상태·HQ 바로가기 |
| **C** | SCREEN 4 `_spa_screen == "analysis"` | L2473–L2650 | `blocks/crm_analysis_screen_block.py` | 증권분석 발사대·GCS Raw Data |

---

## 2. 블록 A — 트리니티 산출기 (`crm_trinity_block.py`)

### 역할
건보료 역산 공식(`calculate_trinity_metrics`)으로 필요 보험가액 7항목을 즉시 산출하고,
카카오 발송 파이프라인 Step 2(AI 가입결과 보고서)를 실행하는 단독 UI 컴포넌트.

### 함수 시그니처
```python
render_crm_trinity_block(
    sel_cust: dict,
    sel_pid: str,
    user_id: str,
    ks_render_send_ui=None,     # kakao_sender.render_send_ui
    kakao_sender_ok: bool = False,
) -> None
```

### 내부 구성 (섹션)

| 섹션 | 내용 |
|---|---|
| **섹션 A — 상담 브리핑 카드** | 총 월납보험료, 유지 계약수, 관리등급, 주요 리스크 요약 |
| **섹션 B — 트리니티 산출기** | 월 건보료 입력 → `calculate_trinity_metrics()` → 7항목 결과 카드 |
| **후유장해 2-Track 카드** | 총 필요금액 / 산재 적용 최소 대비액 |
| **암 5년 일실수익 카드** | 연소득×5년 기준 최저 진단비 결론 |
| **카카오 발송 (Step 2)** | `ks_render_send_ui()` — AI 가입결과 보고서 발송 |
| **Supabase 자동 저장** | `upsert_analysis_report()` — [GP-IMMORTAL §3] 즉시 영구 보존 |

### 의존 모듈
- `shared_components.calculate_trinity_metrics`
- `shared_components.build_deeplink_to_hq`
- `shared_components.decrypt_pii`
- `db_utils.upsert_analysis_report`
- `kakao_sender.render_send_ui` (선택)

### crm_app.py 호출 방법 (마이그레이션 후)
```python
from blocks.crm_trinity_block import render_crm_trinity_block

# contact 스크린 RIGHT PANE 안에서:
render_crm_trinity_block(
    sel_cust=_sel_cust,
    sel_pid=_sel_pid,
    user_id=_user_id,
    ks_render_send_ui=_ks_render_send_ui if _KAKAO_SENDER_OK else None,
    kakao_sender_ok=_KAKAO_SENDER_OK,
)
```

---

## 3. 블록 B — 내보험다보여 스크린 (`crm_nibo_screen_block.py`)

### 역할
신용정보법 제32조 기반 동의 수집 UI + HQ 크롤링 상태 실시간 배지 +
동의 완료 시 HQ 5대 빠른 바로가기 버튼 렌더링.

### 함수 시그니처
```python
render_crm_nibo_screen(
    sel_cust: dict | None,
    sel_pid: str,
    user_id: str,
    hq_app_url: str = "http://localhost:8501",
) -> None
```

### 내부 구성

| 섹션 | 내용 |
|---|---|
| **크롤링 상태 배지** | `get_crawl_status()` → idle / running / done / error 4단계 색상 표시 |
| **신용정보 동의 UI** | `_NIBO_CONSENT_HTML` 약관 + 즉석 체크박스 동의 |
| **동의 완료 안내** | HQ `GK-SEC-10` 센터로 JSON 주입 안내 |
| **HQ 빠른 바로가기 ×5** | gk_sec10 / t3(KB7) / t2(실손) / cancer / fire 딥링크 |

### 의존 모듈
- `db_utils.get_crawl_status`
- `shared_components._NIBO_CONSENT_HTML`, `_NIBO_CONSENT_VERSION`
- `shared_components.build_deeplink_to_hq`

### crm_app.py 호출 방법
```python
from blocks.crm_nibo_screen_block import render_crm_nibo_screen

elif _spa_screen == "nibo":
    render_crm_nibo_screen(
        sel_cust=_sel_cust,
        sel_pid=_sel_pid,
        user_id=_user_id,
        hq_app_url=HQ_APP_URL,
    )
```

---

## 4. 블록 C — 증권분석 스크린 (`crm_analysis_screen_block.py`)

### 역할
HQ 정밀 분석 섹터 선택 발사대(딥링크 + REST API 트리거) +
GCS 고객 원시 데이터 3탭(기본정보/증권목록/관계망) 조회 UI.

### 함수 시그니처
```python
render_crm_analysis_screen(
    sel_cust: dict | None,
    sel_pid: str,
    user_id: str,
    hq_app_url: str = "http://localhost:8501",
) -> None
```

### 내부 구성

| 섹션 | 내용 |
|---|---|
| **HQ 발사대 (좌측)** | 8개 섹터 selectbox → `build_deeplink_to_hq()` → 새 탭 이동 |
| **API 트리거** | `request_hq_analysis_trigger()` → Cloud Run 분석 API 호출 |
| **헬스 확인** | `/health` 엔드포인트 응답 확인 |
| **GCS 기본정보 (우측)** | 고객 상세 필드 13개 카드 뷰 |
| **GCS 증권 목록** | `get_person_policies()` → pandas DataFrame 표 |
| **GCS 관계망** | `get_person_relationships()` → from→관계→to 카드 |

### 의존 모듈
- `shared_components.build_deeplink_to_hq`
- `shared_components.get_hq_api_base`
- `shared_components.request_hq_analysis_trigger`
- `db_utils.get_person_policies`
- `db_utils.get_person_relationships`

### crm_app.py 호출 방법
```python
from blocks.crm_analysis_screen_block import render_crm_analysis_screen

elif _spa_screen == "analysis":
    render_crm_analysis_screen(
        sel_cust=_sel_cust,
        sel_pid=_sel_pid,
        user_id=_user_id,
        hq_app_url=HQ_APP_URL,
    )
```

---

## 5. 현재 `blocks/` 디렉토리 전체 구조

```
blocks/
├── __init__.py
├── crm_action_grid_block.py        # 대시보드 8대 업무 바로가기 그리드
├── crm_nav_block.py                # 메인 대시보드 ↔ 고객 상세 듀얼 네비
├── crm_consultation_center_block.py # 상담 센터 (공통)
├── crm_trinity_block.py            # ★ 신규 — 트리니티 산출기
├── crm_nibo_screen_block.py        # ★ 신규 — 내보험다보여 스크린
└── crm_analysis_screen_block.py    # ★ 신규 — 증권분석 스크린
```

---

## 6. 마이그레이션 적용 체크리스트 (crm_app.py 기준)

- [ ] `contact` RIGHT PANE 섹션 A·B (L1660–L1870) → `render_crm_trinity_block()` 호출로 교체
- [ ] SCREEN 3 `nibo` 블록 (L2363–L2472) → `render_crm_nibo_screen()` 호출로 교체
- [ ] SCREEN 4 `analysis` 블록 (L2473–L2650) → `render_crm_analysis_screen()` 호출로 교체
- [ ] `crm_app.py` 상단 import 섹션에 3개 블록 import 추가
- [ ] 각 블록 내 `db_utils` 함수명 (`get_crawl_status`, `get_person_policies`, `get_person_relationships`) 실제 함수명과 일치 여부 확인
- [ ] Git commit & push → Cursor에서 `blocks/` 디렉토리 인식 확인

---

## 7. Cursor 인수인계 시 주의사항

| 항목 | 내용 |
|---|---|
| **세션 키 네이밍** | `crm_trinity_res_{person_id}`, `crm_nhis__{person_id}` — person_id 접미사로 고객별 격리 |
| **GP-IMMORTAL §3 준수** | 트리니티 결과 산출 즉시 `upsert_analysis_report()` Supabase 저장 필수 |
| **nibo 동의 세션 키** | `nibo_consent_agreed`, `nibo_consent_version`, `nibo_consent_timestamp` — 세션 휘발 주의 |
| **GC(Garbage Collection)** | `crm_app.py` 탭 전환 시 `nibo_raw_data`, `analysis_result_cache` 자동 GC — 블록 내부에서 추가 GC 금지 |
| **HQ 미배포 상태** | `request_hq_analysis_trigger()` — HQ API 미배포 시 `{"ok": False}` 반환, 블록은 `st.error` 처리 내장 |

---

*기준일: 2026-03-24 | 추출: Windsurf Cascade → Cursor 인계용*
