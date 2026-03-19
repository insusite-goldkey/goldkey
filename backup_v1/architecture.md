# Goldkey AI Masters 2026 — app.py 전체 아키텍처 맵
> 작성: 2026-03-14 | 목적: 마인드맵 기반 재구성 로드맵

---

## ★ 사이드바 미노출 근본 원인 (최우선 해결 대상)

### 현재 로그인 흐름
```
앱 로드
  └─ [1~103]  스플래시 (initialized=False 시 5초 표시 → st.rerun())
  └─ [219~485] imports + 세션 초기화
  └─ [28648~] main() 호출
        └─ [28698~28742] 미인증 시: CSS로 사이드바 강제 노출 + 메인화면에 로그인폼 렌더
        └─ [32134~] with st.sidebar: → render_goldkey_sidebar() + JS 강제 열기
        └─ [33942] 미인증이면 st.stop()
```

### 문제점
1. **두 곳에 로그인 폼 중복**: `main()` 내 메인화면(28698~28842)과 사이드바(32184~) 양쪽에 로그인 폼이 존재
2. **CSS 충돌**: 스플래시 중 `[data-testid="stSidebar"] { display: none }` 주입 → `st.rerun()` 후에도 CSS 잔류 가능성
3. **`with st.sidebar` 블록이 main() 함수 안 line 32134** — 전체 59,710라인 중 절반 지점에 위치, 그 앞에서 예외 발생 시 사이드바 미도달

---

## 현재 app.py 블록 전체 맵 (59,710 라인)

### LAYER 0 — 앱 부팅 (절대 불변, 485라인 이하)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L0-A** | 1~103 | 스플래시·set_page_config·CSS 초기화 | ❌ 불변 |
| **L0-B** | 104~218 | TRADE SECRET·GHOST PROTOCOL·섹션 구조 목록 | ❌ 불변 |
| **L0-C** | 219~485 | imports + 세션 초기화 + smart_scanner 지연 로드 | ❌ 불변 |

---

### LAYER 1 — 앱 아이덴티티 & 가이딩 프로토콜 (현재 SECTION 0 + 제6편)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L1-A** | 476~485 | SECTION 0: 앱 아이덴티티 상수 (APP_NAME 등) | ⬆️ L0-C 직후 유지 |
| **L1-B** | 486~630 | 제6편: ART21~ART30 — 기본 분석 상수 | 현위치 유지 |
| **L1-C** | 631~655 | GP200 브랜딩 프로토콜 상수 | 현위치 유지 |
| **L1-D** | 656~793 | CORP-AC 법인 자동완성 DB + 인덱스 | 현위치 유지 |
| **L1-E** | 794~1079 | HIRA-KCD 질병코드 검색 엔진 | 현위치 유지 |
| **L1-F** | 1080~1447 | KCD 커버리지 맵 + render_kcd_autocomplete | 현위치 유지 |
| **L1-G** | 1448~1676 | LAW-API 법령 검색 + render_law_search | 현위치 유지 |
| **L1-H** | 1677~1932 | GP-JOB 직업 탐색기 + render_job_navigator | 현위치 유지 |
| **L1-I** | 1933~2049 | ART35 치매 단계 + 커버리지 맵 | 현위치 유지 |
| **L1-J** | 2050~2268 | ART32/ART62 계산 엔진 | 현위치 유지 |
| **L1-K** | 2269~2426 | GP64 마스터 설정 + ART34/ART38/ART39 | 현위치 유지 |
| **L1-L** | 2427~4878 | GP38/GP39 UI 렌더러 + ART34 보고서 | 현위치 유지 |

---

### LAYER 2 — 인프라 엔진 (현재 SECTION 1~2)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L2-A** | 4880~5521 | SECTION 1: 보안·암호화 엔진 | ❌ 불변 |
| **L2-B** | 5522~5579 | SECTION 1.8: Brute-force 로그인 방어 | ❌ 불변 |
| **L2-C** | 5580~5637 | SECTION 1.5: 비상장주식 평가 엔진 | ⬇️ SECTION 5300 근처로 이동 권장 |
| **L2-D** | 5638~5674 | SECTION 1.6: CEO플랜 AI 프롬프트 상수 | ⬇️ SECTION 5300 근처로 이동 권장 |
| **L2-E** | 5675~7701 | SECTION 2: DB·Supabase·회원관리 | ❌ 불변 |
| **L2-F** | 7702~8956 | SECTION 2-B: 동시접속 관리 + 구독 검증 | ❌ 불변 |

---

### LAYER 3 — 중앙 사령부 (현재 SECTION 3 내부 — 16,000라인 덩어리)
> **핵심 문제**: SECTION 3이 "유틸리티"라는 이름 하에 전체 비즈니스 로직을 담당
> 이 레이어를 디맨드별로 분리하는 것이 리팩토링의 핵심

| 블록 ID | 위치 (라인) | 역할 | 목표 위치 |
|---------|------------|------|---------|
| **L3-CORE** | 8957~9254 | SECTOR_CODES·SUB_CODES·_NAV_INTENT_MAP·APP_REGISTRY | ⬆️ LAYER 2 직후 (중앙 라우팅 사령부) |
| **L3-AI** | 9255~9810 | AI 호출 엔진·캐시·건강보험료 역산 | L3 유지 |
| **L3-GP101** | 9810~9943 | GP101 후킹 카드·GP102 Gap 카드 | → **WAR-ROOM 모듈**로 분리 |
| **L3-LIFEGAP** | 10430~10635 | render_life_gap_panel | → **개인보장 모듈**로 분리 |
| **L3-FSS** | 10635~11299 | FSS 금융상품 패널·KOSIS 대시보드 | L3 유지 (공용 엔진) |
| **L3-FORTRESS** | 11299~11730 | 데이터 요새·혈관차트·생명보험통계 | L3 유지 (공용 엔진) |
| **L3-REPORT** | 11951~12383 | render_consulting_report·KB Score 도넛 | → **개인보장 모듈**로 분리 |
| **L3-SPECIAL** | 12384~12992 | render_special_ops_sector (5단계 전략) | → **WAR-ROOM 모듈**로 분리 |
| **L3-PROFILE** | 12992~13205 | render_member_profile_settings | L3 유지 |
| **L3-ONCO** | 13205~13615 | 항암 정밀 엔진 (render_oncology_chemo_panel 등) | → **질환상담 모듈**로 분리 |
| **L3-LOSS** | 13615~13864 | render_loss_insurance_panel | → **개인보장 모듈**로 분리 |
| **L3-RISK** | 13864~14263 | _render_gk_risk·_render_gk_job | → **GK-RISK 모듈**로 분리 |
| **L3-SEC10** | 14271~15126 | _render_gk_sec10 (내보험다보여) | → **SEC10 모듈**로 분리 |
| **L3-SEC09** | 15127~15807 | _render_gk_sec09 (VVIP CEO) | → **SEC09 모듈**로 분리 |
| **L3-SEC08** | 15808~16504 | _render_gk_sec08 (화재·특종) | → **SEC08 모듈**로 분리 |
| **L3-SEC07** | 16509~17038 | _render_gk_sec07 (자동차보험) | → **SEC07 모듈**로 분리 |
| **L3-WARROOM** | 17039~17590 | show_war_room (실전 상담 전략실) | → **WAR-ROOM 모듈**로 분리 |
| **L3-NAV** | 17591~20866 | 내비게이션·오류 로깅·각종 헬퍼 | L3 유지 |
| **L3-LIFEDEF** | 20867~25030 | _life_defense_command_panel (인생방어 사령부) | → **LIFE-DEF 모듈**로 분리 |

---

### LAYER 4 — AI 프롬프트 & RAG (현재 SECTION 4~5)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L4-BRAND** | 25032~25193 | SECTION 8브랜드: 아바타 시스템 | ⬆️ SECTION 8 메인UI 앞으로 이동 |
| **L4-PROMPT** | 25194~25782 | SECTION 4: 시스템 프롬프트 | 현위치 유지 |
| **L4-FINAPI** | 25783~26127 | SECTION 4-B: 금감원 finlife API | 현위치 유지 |
| **L4-RAG** | 26128~27024 | SECTION 5: RAG SQLite 시스템 | 현위치 유지 |
| **L4-FIRE** | 27025~28359 | SECTION 5.5: 공장화재보험 로직 | ⬇️ SEC08 근처로 이동 권장 |

---

### LAYER 5 — 전문 비즈니스 로직 (현재 SECTION 6~7)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L5-INHERIT** | 28361~28617 | SECTION 6: 상속/증여 정밀 로직 | 현위치 유지 |
| **L5-PENSION** | 28618~28647 | SECTION 7: 주택연금 시뮬레이션 | 현위치 유지 |

---

### LAYER 6 — 메인 UI (현재 SECTION 8 + main())
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L6-MAIN** | 28648~33943 | main() — 인증·사이드바·탭 라우터 1차 | ❌ 불변 |
| **L6-TABS-A** | 33944~36460 | 탭 라우터 2차 (home, scan, war_room 등) | ❌ 불변 |
| **L6-TABS-B** | 36461~57710 | 탭 라우터 3차 (전체 디맨드 탭) | ❌ 불변 |

---

### LAYER 7 — 자가복구 + 진입점 (현재 SECTION 9)
| 블록 ID | 위치 (라인) | 역할 | 이동 가능 |
|---------|------------|------|---------|
| **L7-ERRLOG** | 57711~59100 | SECTION 9-A: 오류 레지스트리·자가진단 | ❌ 불변 |
| **L7-RECOVER** | 59101~59670 | SECTION 9: auto_recover·_run_safe | ❌ 불변 |
| **L7-ENTRY** | 59671~59710 | _run_safe() → main() 진입점 | ❌ 불변 |

---

## 목표 아키텍처 (마인드맵 선 끊김 없는 구조)

```
app.py
│
├── [LAYER 0] 부팅 (line 1~485) ← 절대 불변
│   ├── L0-A: 스플래시·set_page_config
│   ├── L0-B: TRADE SECRET·섹션 목록
│   └── L0-C: imports·세션 초기화
│
├── [LAYER 1] 가이딩 프로토콜 (line 486~4878) ← 현위치 유지
│   └── L1-B~L: 제6편 상수·엔진·렌더러
│
├── [LAYER 2] 인프라 (line 4879~8956) ← 현위치 유지
│   ├── L2-A~B: 보안·암호화·로그인방어
│   ├── [★이동] L2-C/D → L5 근처 (비상장주식·CEO플랜)
│   └── L2-E~F: DB·회원관리·동시접속
│
├── [LAYER 3] 중앙 사령부 — 분리 대상
│   ├── [★이동 우선] L3-CORE (SECTOR_CODES) → L2 직후
│   ├── L3-AI: AI 호출 엔진 (공용, 유지)
│   ├── [★파일 분리] demand_personal.py  ← L3-LIFEGAP, L3-REPORT, L3-LOSS
│   ├── [★파일 분리] demand_warroom.py   ← L3-GP101, L3-SPECIAL, L3-WARROOM
│   ├── [★파일 분리] demand_disease.py   ← L3-ONCO + 암·뇌·심장
│   ├── [★파일 분리] demand_sec07.py     ← L3-SEC07 (자동차)
│   ├── [★파일 분리] demand_sec08.py     ← L3-SEC08 + L4-FIRE (화재)
│   ├── [★파일 분리] demand_sec09.py     ← L3-SEC09 (VVIP CEO)
│   ├── [★파일 분리] demand_sec10.py     ← L3-SEC10 (내보험다보여)
│   └── [★파일 분리] demand_lifedef.py   ← L3-LIFEDEF (인생방어)
│
├── [LAYER 4] AI 프롬프트·RAG (line ~26127) ← 현위치 유지
│   └── [★이동] L4-BRAND → LAYER 6 직전
│
├── [LAYER 5] 전문 비즈니스 (line ~28647) ← 현위치 유지
│   └── [★이동] L2-C/D (비상장주식·CEO플랜) → 여기로
│
├── [LAYER 6] 메인 UI / 탭 라우터 (line 28648~57710) ← 불변
│   └── L4-BRAND 아바타 → 여기 직전으로
│
└── [LAYER 7] 자가복구 + 진입점 (line 57711~59710) ← 절대 불변
```

---

## 사이드바 문제 즉시 해결 체크리스트

1. **`main()` (line 28698) 미인증 분기에서 메인화면 로그인폼 → 사이드바 로그인과 중복 여부 확인**
2. **스플래시 CSS `display:none` → `st.rerun()` 후 제거되는지 확인** (현재 `initialized=True` 후 rerun → CSS 해제 정상)
3. **line 32134 `with st.sidebar:` 도달 전 예외 발생 여부** → 이 줄 이전에 에러 발생 시 사이드바 미렌더
4. **`_sc_render_auth_screen` 미정의 시 폴백 로직 확인** (line 28747)

---

## 파일 분리 순서 (영향 최소→최대)

| 순서 | 대상 | 예상 영향 | 비고 |
|------|------|---------|------|
| 1 | `demand_sec07.py` | 낮음 — 자동차보험 독립 렌더러 | L3-SEC07 |
| 2 | `demand_sec08.py` | 낮음 — 화재보험 독립 렌더러 | L3-SEC08 + L4-FIRE |
| 3 | `demand_sec09.py` | 낮음 — VVIP CEO 독립 렌더러 | L3-SEC09 |
| 4 | `demand_sec10.py` | 낮음 — 내보험다보여 독립 렌더러 | L3-SEC10 |
| 5 | `demand_lifedef.py` | 중간 — 복수 함수 의존 | L3-LIFEDEF |
| 6 | `demand_warroom.py` | 중간 — GP101/102 의존 | L3-WARROOM + L3-GP101 |
| 7 | `demand_personal.py` | 높음 — 핵심 분석 로직 | L3-REPORT + L3-LOSS 등 |
| 8 | L3-CORE 위치 이동 | 중간 — SECTOR_CODES 전역 참조 | 위치만 이동, 파일 분리 아님 |
