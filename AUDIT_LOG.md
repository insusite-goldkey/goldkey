# 🔍 골드키 AI 마스터 — 자가검열 감사 로그

---

## ⚠️ 절대명령 (ABSOLUTE DIRECTIVE)

> **"오류점검"** 명령이 내려지면, 아래 4인 감사팀 조건을 100% 적용하여 자동 점검을 실행한다.
> 이 명령은 어떠한 상황에서도 무시되지 않으며, 매 점검 시 아래 4개 관점을 **전부** 다룬다.

### 4인 감사팀 구성 및 점검 범위

| 역할 | 점검 항목 |
|------|-----------|
| ⚖️ **보험 전문 변호사** | 면책조항 적정성, 보험업법 위반 소지, 금융감독원 규정 적합성, 불법 손해사정 여부 |
| 🖥️ **시니어 UX 전문가** | 사용자 흐름 단절, 모바일 최적화 오류, 접근성 문제, UI 혼란·오해 요소 |
| 🔒 **풀스택 개발 보안 전문가** | 세션 취약점, 인증 우회 가능성, 데이터 누출 위험, 예외 처리 누락, XSS·인젝션 방어 |
| 🤖 **AI 로직 설계자** | 프롬프트 인젝션, 분류 오류, 응답 일관성, 금지 키워드 처리, 할루시네이션 방지 |

### 점검 실행 절차

1. `app.py` 전체 코드 구조 파악
2. 위 4개 관점에서 각각 독립적으로 점검
3. 발견된 문제를 아래 **오류 기록** 테이블에 즉시 기록
4. 심각도 분류: 🔴 긴급(즉시 수정) / 🟠 중요(금주 내) / 🟡 개선(다음 스프린트)
5. 수정 완료 시 커밋 해시 기록

---

## 감사팀 프롬프트 (매 감사 시 사용)

```
너는 이제부터 [보험 전문 변호사 / 시니어 UX 전문가 / 풀스택 개발 보안 전문가 / AI 로직 설계자]
4인으로 구성된 감사 팀이다.
현재 개발 중인 '보험 AI 에이전트 앱'의 전체 내용을 아래 4가지 관점에서 엄격히 점검하고 리포트를 제출하라.

1. [보험 전문 변호사] 면책조항, 법률 위반 소지, 보험업법 준수 여부, 금융감독원 규정 적합성
2. [시니어 UX 전문가] 사용자 흐름 단절, 접근성 문제, 모바일 최적화 오류, UI 혼란 요소
3. [풀스택 개발 보안 전문가] 세션 취약점, 인증 우회 가능성, 데이터 누출 위험, 예외 처리 누락
4. [AI 로직 설계자] 프롬프트 인젝션, 분류 오류, 응답 일관성, 금지 키워드 처리 로직
```

---

## 오류 기록

### 2026-02-25

| # | 발생 시각 | 섹션 | 증상 | 원인 | 수정 커밋 |
|---|-----------|------|------|------|-----------|
| 1 | 22:46 | 통합스캔허브(scan_hub) | 관리자 로그인 후 "로그인하라"는 화면 표시 | `auto_recover` / `_run_safe` 예외 처리 시 `st.session_state.clear()`로 `user_id` 포함 전체 삭제 | `76b59e0` |
| 2 | 22:46 | 전체 섹션 | 관리자(이세윤·박보정) 권한 없음으로 표시 | 세션 복구 후 `is_admin`이 재검증되지 않아 소실 | ✅ 완료 — `line 32973` 매 렌더 `_get_unlimited_users()` 재검증 + `auto_recover` 보존키 포함 |
| 3 | 이전 세션 | 상담 카탈로그 | 관리자 업로드 파일 목록에 미표시 | `user_files` 조회 시 본인 UID로만 필터링 | `932ecfd` |
| 4 | 이전 세션 | 업로드 라이브러리 | 업로드 후 즉시 목록 미반영 | `st.rerun()` 및 캐시 초기화 누락 | `4571383` |
| 5 | 이전 세션 | 라이브러리 박스2 | `기타` 문서가 고객서류로 잘못 분류 | 분류 로직에서 `기타` 처리 누락 | `5ce351d` |
| 6 | 23:28 | t9 AI지식베이스(REG박스) | 즉시 등록 후 AI 상담에 반영 안 됨 (자료 휘발처럼 보임) | `_rag_quick_register`는 Storage+메타만 저장 (chunk=0), 심야처리 전까지 `rag_docs`에 청크 없음 | ✅ 완료 — `btn_rag_sync`가 `_rag_db_add_document` 직접 호출로 교체 (line 52583~52653) |
| 7 | 23:28 | t9 AI지식베이스(REG박스) | 즉시 등록 후 메모리 캐시 미갱신 | `st.rerun()` 전 `_rag_sync_from_db(force=True)` 및 `LightRAGSystem()` 재초기화 누락 | ✅ 완료 — `line 52649~52650` `_rag_sync_from_db(force=True)` + `LightRAGSystem()` 적용됨 |
| 8 | 23:28 | t9 AI지식베이스(REG박스) | 심야 처리 완료 후에도 검색 엔진이 빈 상태 유지 | `_rag_process_pending()` 후 `rag_system` 세션 재초기화 누락 | ✅ 완료 — `line 52682~52685` `_rag_sync_from_db(force=True)` + `LightRAGSystem()` + `st.rerun()` 적용됨 |

---

## 보안 감사 포인트 (개발 보안 전문가 관점)

- `auto_recover` 세션 전체 초기화 → **로그인 키 보존으로 수정** (`76b59e0`)
- `is_admin` 세션 값 단일 의존 → **매 렌더 재검증으로 강화** ✅ 완료 (line 32973)
- `client_name` DB 저장 시 입력 검증 필요 (XSS 방어)
- `user_files` Supabase RLS 정책 — 관리자 파일 공유 시 다른 사용자 접근 허용 범위 재확인 필요

---

## 출력 기능 점검 체크리스트

- [x] `show_result()` 면책조항 포함 출력 — `full_text.encode("utf-8")` 다운로드 정상 (코드 검토 완료)
- [x] `show_result()` 브라우저 인쇄/PDF 저장 — `window.print()` JS `components.html()` 호출 정상
- [x] 출력 내용 텍스트영역 (`print_area_{result_key}`) key 충돌 없음 — result_key별 고유 key 사용
- [x] 다운로드 버튼 (`dl_{result_key}`) key 충돌 없음 — result_key별 고유 key 사용
- [x] 관리자 계정 로그인 시 `👑 관리자` 배지 표시 — `4c7c758` 수정 후 정상
- [ ] 실환경 테스트 필요 — HF Space 재빌드 후 실제 출력 버튼 동작 확인

### 출력 기능 잠재적 주의사항
- `full_text`에 마크다운 기호(`**`, `#`)가 그대로 포함 — 텍스트 파일로는 읽기에 문제없으나, 인쇄 시 마크다운이 렌더링되지 않는 plain text로 출력됨
- `window.print()`는 Streamlit iFrame 구조상 **전체 페이지**를 인쇄함 — 결과 부분만 출력하려면 별도 팝업 창 필요 (workspace/insurance_bot.py의 A4 PDF 방식이 더 적합)

---

---

## 작업 일지

### 2026-03-04 (화) — UI 최적화 · 스플래시 개선 · 로그인 흐름 정비

**작업 시간:** 오후 ~ 오후 11:22 (UTC+09:00)

#### ✅ B4 시리즈 — 헌법 기준 UI 블록 재검증 및 재적용

| BID | 항목 | 결과 |
|-----|------|------|
| B4_1 | 지금 가입하면 무료 블록 — 오렌지-골드 그라데이션 + 흰색 글자 | 이미 적용됨 (확인) |
| B4_2 | goldkey_Ai_masters2026 보안 로그인 박스 — 헌법 기준 스타일 | 이미 적용됨 (확인) |
| B4_3 | 이름/연락처 입력창 검정 외곽선 `border:2px solid #000000` | 이미 적용됨 (확인) |
| B4_4 | 본인 확인 완료-추가 보안인증 박스 — 밝은 그린 그라데이션 + **흰색 글자** 재수정 | ✅ 수정 완료 |
| B4_5 | 인증번호 입력창 검정 외곽선 | 이미 적용됨 (확인) |
| B4_6 | 인증번호+OTP 통합 블록 — 좌우 분할 + 검정 외곽선 | 이미 적용됨 (확인) |
| B4_7 | 처음으로 버튼 3곳 — 회색 그라데이션 블록 | 이미 적용됨 (확인) |

#### ✅ B4_8/9 — 간편로그인 기존 설정 회원 단독 중앙 배치

- Phase C 헤더: 현재 활성 인증 방식(`bio`/`pat`/`pin`) 라벨 동적 표시
- 등록된 방식이 1개뿐인 기존 회원 → fallback 버튼 숨김 (단독 중앙 배치 모드)

#### ✅ B1 — 스플래시카드 화면 크기 연동 (안드로이드 동적 연동)

- `window.innerWidth/innerHeight` + DPR 보정으로 CSS px 기준 감지
- `shortDp >= 600dp` 기준 tablet/phone 이미지 자동 선택
- 화면 회전(resize) 이벤트 대응 — 오버레이 크기 재계산
- **이미 구현 완료** (추가 수정 불필요)

#### ✅ B2 — 스플래시 로딩 시간 단축 (5초 이상 → ~1초 이내)

- JS 강제 해제 타이머: `1200ms → 800ms`
- Python DB 초기화 대기 타임아웃: `2.0초 → 1.0초`
- 최대 지연: DB 미준비 시에도 약 1초 내 강제 해제 보장

#### ✅ B3 — 핸드폰 스플래시 후 사이드바 미노출 버그 수정

- `stSidebar`에 `transform:none`, `left:0` 강제 적용 (모바일 transform 밀림 대응)
- `collapsedControl` 요소에 `display:flex` 강제
- `aria-label` 셀렉터 추가: `Close sidebar`, `Collapse sidebar`, `Show sidebar`, class 기반 selector 2개
- 기존 MutationObserver + 폴링(200ms × 25회) 방식 유지

---

## 미결 항목

- ~~Supabase `user_files` 테이블 `client_name` 컬럼 마이그레이션 SQL 실행 필요~~ **✅ 완료 (2026-03-12)**
  ```sql
  ALTER TABLE user_files ADD COLUMN IF NOT EXISTS client_name TEXT;
  ```
  → Supabase SQL Editor에서 직접 실행 완료. `client_name TEXT` 컬럼 추가됨.

---

## [UI 렌더링 버그] 전용 기록

> **용도:** 화면 깜빡임·백화현상·레이아웃 틀어짐 등 UI/UX 렌더링 결함을 기록한다.  
> 재발 발견 시 Constitution.md 제130.2조 §4 절차에 따라 아래 표에 즉시 기록할 것.  
> 원인 코드는 제130.2조 §1 표(W-01 ~ W-06)를 참조한다.

### 렌더링 버그 기록 테이블

| # | 발생 일시 | 증상 | 원인 코드 | 수정 방법 | 수정 커밋 | 상태 |
|---|-----------|------|-----------|----------|-----------|------|
| 1 | 2026-03-10 19:15 | 탭·섹터 전환 시 화면이 순간적으로 흰색으로 번쩍임 (백화현상) | W-01, W-02, W-03, W-04, W-05, W-06 | `gk-fadein` opacity 0→0.12, `transition` 제거, `color-scheme:light` 추가, 셀렉터 확대, scroll iframe→markdown 교체 | `052dc9e` | ✅ 수정 완료 |

### 자가점검 명령

> **"UI점검"** 또는 **"백화점검"** 명령이 내려지면 Constitution.md 제130.2조 §3 체크리스트 6개 항목을 전부 실행하고 결과를 이 테이블에 기록한다.

---

## 작업 일지 (최신순)

### 2026-03-24 (월·후반) — CRM 메인 재배치 · 상담센터 5:5 · 위치 기반 날씨 · 전역 TTS 클래스

| 항목 | 내용 |
|------|------|
| 메인 목록 순서 | 달력 → 고객정보입력(필터) → **왕복 네비**(`blocks/crm_nav_block`) → **8액션 그리드** → **상담 센터 5:5**(`blocks/crm_consultation_center_block`) → 고객 표 |
| 네비 | `render_crm_dual_nav` — 목록·상세 양쪽에 동일 키(peach_nav_*) 유지 |
| 상담 센터 | 좌: 건보료·트리니티·Nibo·동의·증권스캔 expander / 우: 트리니티·HQ 요약 박스 |
| 하단 | `compliance.render_feedback_button` + **[HQ] 앱으로 이동** 대형 버튼 |
| 모닝 브리핑 날씨 | `brief_lat`/`brief_lon` 세션 → IP 기반(ip-api) → 서울 폴백 (`voice_engine`) |
| 전역 TTS | `shared_components.GeminiProTTSVoice` — Zephyr 배너 문구 통일 |
| GP 규칙 | `.cursor/rules/goldkey-ai-masters.mdc` — 다중 지시 추출·보고·블록 임의 삭제 금지 |
| 후속 마무리 | `crm_app`: `render_briefing_geolocation_button` **별도 import** (voice 일부 실패 시에도 위치 버튼 가능); **고객(`customer`) 모드**에도 피드백 + **[HQ] 앱으로 이동** 푸터 추가 |

---

### 2026-03-24 (월) — GP-44 블록 모듈화 · rules 기반 CRM 액션 · 배포 트랙 문서

**작업 시간:** 오전 (UTC+09:00)

#### ✅ 사전 백업

| 항목 | 내용 |
|------|------|
| `backup_and_push.ps1` | `app.py` 스냅샷 `app_backup_*.py` 생성 → Git add/commit/push → Cloud Build(HQ) → `goldkey-ai` 배포 |

#### ✅ 코드·구조

| 항목 | 내용 |
|------|------|
| `blocks/` | 패키지 생성, `crm_action_grid_block.py` — CRM 메인 수평 액션 그리드 분리 |
| `shared_components.py` | `load_gp_rules()` (로컬 `rules.json` + `GK_RULES_JSON_URL` 병합, 60초 캐시), `get_crm_action_definitions()`, `get_crm_action_grid_title()` |
| `rules.json` | `crm_ui.action_grid_title`, `crm_ui.actions[]` (id, label, order, enabled, requires_customer) |
| `crm_app.py` | 인라인 액션 그리드 제거 → `blocks` import |
| `Dockerfile` / `Dockerfile.crm` | 레이어 캐시·`.dockerignore` 안내 주석 |
| `.dockerignore` | 신규 — 백업·workspace·RN 등 제외 |
| `.gcloudignore` | `backup_v1/`, `backups/`, `workspace/`, `GoldKeyApp/` 추가 |

#### ✅ 문서

| 파일 | 내용 |
|------|------|
| `docs/BLOCKS_AND_DEPLOY_GUIDE.md` | Track A(설정 OTA) vs Track B(코드 배포), 수정 위치 표 |

---

### 2026-03-10 (화) — 성능 최적화 · 백화현상 수정

**작업 시간:** 오후 7:00 ~ 오후 7:25 (UTC+09:00)

#### ✅ 성능 최적화 (커밋 `e47eab1`)

| 항목 | 내용 |
|------|------|
| GCS 클라이언트 싱글톤 | `@st.cache_resource` 적용 — 프로세스당 1회 인증 |
| `load_members()` 세션 캐시 | `st.session_state["_members_cache"]` 즉시 반환, TTL 120→300초 |
| `save_members()` 캐시 무효화 | 저장 후 `session_state.pop("_members_cache")` |
| Constitution.md | 제130.1조 PERFORMANCE & STABILITY PROTOCOL 추가 |

#### ✅ 백화현상 수정 (커밋 `052dc9e`)

| 원인 코드 | 수정 내용 |
|-----------|----------|
| W-01 | `gk-fadein` opacity `0` → `0.12`, 지속시간 `0.22s` → `0.18s` |
| W-02 | `transition: background-color 2s` 제거 |
| W-03 | `html/body/stApp` 계열 전체 배경 `#F8F9FA` 선점 |
| W-04 | `html { color-scheme: light !important }` 추가 |
| W-05 | `_scroll_top` `components.html()` → `st.markdown()` 인라인 교체 |
| W-06 | `stAppViewBlockContainer`, `.stApp` 셀렉터 추가 |
