# Goldkey AI Masters 2026 — 설계자 컨텍스트 (SSOT 요약)

> **목적:** Windsurf·Cursor·설계자가 공유하는 **단일 참조**입니다.  
> **로컬 SSOT:** `d:\CascadeProjects`  
> **GP 원문:** `Constitution.md` · **코드 내 주석:** `app.py`(HQ), `crm_app.py`(CRM)  
> **Windsurf→Cursor 인계:** `docs/CURSOR_HANDOVER_REPORT.md`

---

## 시스템 핵심 페르소나 및 역할 (요약)

- **HQ (`goldkey-ai`, `app.py`):** **정밀 분석 사령부** — 설계사 대면 상담·심화 리포트 생성 엔진. 레이아웃: **`layout="wide"`**, 사이드바 expanded.
- **CRM (`goldkey-crm`, `crm_app.py`):** **초경량 현장 기동대** — 모바일·현장 최적화, 일정·메시지·기동성 중심. 레이아웃 의도: **`layout="wide"`**, 사이드바 **collapsed** (`set_page_config`는 파일 상단 규칙에 맞게 단일화 권장).

---

## 1. 앱 페르소나 (제품 역할 · 상세)

| 앱 | 서비스명 | 페르소나 | 핵심 |
|----|-----------|----------|------|
| **HQ** | `goldkey-ai` (`app.py`) | **정밀 분석 사령부** | 대면·심화 상담, 트리니티·증권·리포트·탭 라우터 (`home`, `t3`, `gk_sec10`, `gk_risk`, `war_room`, `policy_scan`, `claim_scanner`, `report43` 등) |
| **CRM** | `goldkey-crm` (`crm_app.py`) | **초경량 현장 기동대** | 목록·일정·내보험다보여·카카오·AI 브리핑·HQ 딥링크; **정밀 계산은 HQ 위임** |

---

## 2. 보안 및 CRM ↔ HQ 연결 (아키텍처)

- **SSO 핸드오프:** HMAC-SHA256 기반 인증 토큰 검증 — `shared_components`의 `build_sso_handoff_to_hq`, `verify_sso_token` 등; 타임스탬프·TTL은 구현상 **약 300초(5분)** 대역으로 리플레이 완화(세부는 코드 주석 준수).
- **SSO / 딥링크:** `build_deeplink_to_hq`, `build_deeplink_to_crm`, CRM `_check_sso_token` — 수신 후 URL 파라미터 정리.
- **REST API 브릿지:** CRM → HQ **`POST …/api/v1/analysis/trigger`** — `modules/hq_analysis_api.py`, CRM `request_hq_analysis_trigger`, 헤더 `X-GK-Bridge-Key`(`GK_ANALYSIS_BRIDGE_SECRET`).
- **데이터 생존 (GHOST PROTOCOL / GP-IMMORTAL):** `app.py` 상단 — **session_state + Supabase + GCS** 3중 저장 원칙; 상세는 코드 주석·`Constitution.md`.
- **공유 DB:** `db_utils.py` — Supabase (양앱 공통).
- **Dual Write (고객 스냅샷):** `schedule_gcs_customer_profile_async` + `crm_fortress.upsert_person` 경로.
- **Cloud Run:** `Dockerfile` / `Dockerfile.crm`; **시크릿은 Git에 없음** — 환경변수·Secret Manager.

---

## 3. 부속 파일·폴더 (로컬 구조)

| 구분 | 경로 | 비고 |
|------|------|------|
| 메인 실행 | `app.py`, `crm_app.py` | HQ / CRM |
| 공통 | `shared_components.py`, `db_utils.py`, `calendar_engine.py`, `components.py` | |
| HQ 엔진 | 루트 `trinity_engine.py`, `expert_agent.py`, … 및 `engines/`, `modules/` | |
| CRM 요새 | `crm_fortress.py`, `crm_fortress_ui.py`, `voice_engine.py`, … | |
| 대용량 보관 | `backup_v1/`, `workspace/`, `crm_app/`(React Native) | 과거본·실험·모바일 — **배포 Docker에 항상 포함되지는 않음** |
| 배포 | `Dockerfile`, `docker/`, `deploy/` | |
| GP·문서 | `Constitution.md`, `docs/` | |

---

## 4. 민감 파일 (Git·이미지 미포함 가능)

- `.streamlit/secrets.toml`, `.env`, 서비스 계정 키, `assets/금융감독원API키.txt` 등 → **로컬 또는 Secret Manager만**

---

## 5. GP(가이딩 프로토콜)와의 관계 · 최신 개정 반영

- **헌법급 원문:** `Constitution.md`
- **실행 시 주석:** `app.py` 상단 GHOST PROTOCOL, 가이딩 프로토콜 조항 번호, `GP_ID_*` 블록
- **CRM:** `GP-84` CSS, `GP-SEC`, `GP-SPA`, `GP 마스터-그림자` 등 — 파일 내 주석
- **디자인 (2026-03-18 Bright Corporate UI/UX):** 전역 배경·타이포·프리미엄 박스 등 — `Constitution.md` 제2장(제6~11조) 및 `inject_global_gp_design` 계열; **#FFFFFF / Fluid Typography** 등 세부는 헌법 조문 준수.
- **품질 (제23조 Zero Tolerance):** 유튜브·블로그·카페·지식인 등 **비승인 출처 인용 금지** — 답변·리포트 생성 시 `app.py` 가이딩 프로토콜 제21~28조 구간과 정합.
- 상세 조항 표·인덱스는 팀 내부 GP 전체 보고서와 **이 문서를 함께** 유지

---

## 6. 설계자 워크플로 (Windsurf ↔ Cursor)

- **`docs/DESIGNER_WORKFLOW.md`** — 체크리스트·제약  
- **`docs/CURSOR_HANDOVER_REPORT.md`** — 무엇을 Git/docs로 넘길지·배포 이름 참조

---

*기준일: 2026-03-24 · 설계자·Cursor 공유용*
