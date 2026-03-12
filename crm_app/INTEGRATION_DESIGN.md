# Goldkey AI ↔ 골드키 CRM 통합 설계 문서
> 작성일: 2026-03-13 | 버전: 2.0 (그림자 앱 방식)

---

## 1. 핵심 방향 — 그림자 앱(Shadow App) 방식

### 개념
```
사용자가 Goldkey AI 1개만 설치해도
  → 골드키 CRM이 자동으로 함께 설치됨 (번들 설치)
  → 또는 CRM만 설치해도 Goldkey AI가 함께 설치됨

두 앱은 독립 실행되지만 Supabase를 통해 데이터를 공유.
어느 쪽에서 입력해도 양쪽에 즉시 반영.
```

### 앱 역할 분담

| 구분 | Goldkey AI (모 앱) | 골드키 CRM (자 앱) |
|---|---|---|
| **주 사용 기기** | 태블릿 | 핸드폰 |
| **역할** | 전체 기능 완성 앱 | 핵심 섹션 경량 앱 |
| **기능** | AI분석·리포트·고객관리·증권·일정 전체 | 고객상담·일정·증권분석·AI리포트·내보험다보여 |
| **AI** | ✅ 자체 탑재 | 🔗 Goldkey AI 결과 pull (그림자) |
| **데이터** | Read/Write 전체 | Read/Write (동일 Supabase) |

### 그림자 섹션 (CRM이 AI에서 복사해오는 것들)
- 고객 상담 일정
- 증권 분석 결과
- AI 상담 리포트
- 내보험다보여

---

## 2. Supabase 공통 테이블 설계

### 2-1. gk_people (인물 마스터) — 기존 테이블 확장
```sql
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS birth_date   DATE;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS gender       TEXT;  -- 남성/여성
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS job          TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS company      TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS title        TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS memo         TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS tags         JSONB DEFAULT '[]';
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS is_client    BOOLEAN DEFAULT true;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS agent_id     TEXT;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS is_deleted   BOOLEAN DEFAULT false;
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS updated_at   TIMESTAMPTZ DEFAULT now();
```

### 2-2. gk_schedules (일정) — 신규 생성
```sql
CREATE TABLE IF NOT EXISTS gk_schedules (
  id           TEXT PRIMARY KEY,        -- SCH_{timestamp}_{random}
  person_id    TEXT REFERENCES gk_people(person_id),
  agent_id     TEXT,
  title        TEXT NOT NULL,
  category     TEXT,                    -- consult / appointment / follow_up
  date         DATE NOT NULL,
  start_time   TEXT,                    -- HH:MM
  end_time     TEXT,
  memo         TEXT,
  done         BOOLEAN DEFAULT false,
  source       TEXT DEFAULT 'crm',      -- 'crm' | 'ai' (입력 출처)
  is_deleted   BOOLEAN DEFAULT false,
  created_at   TIMESTAMPTZ DEFAULT now(),
  updated_at   TIMESTAMPTZ DEFAULT now()
);
```

### 2-3. gk_scan_results (증권 스캔 결과) — 신규 생성
```sql
CREATE TABLE IF NOT EXISTS gk_scan_results (
  id              TEXT PRIMARY KEY,
  person_id       TEXT REFERENCES gk_people(person_id),
  agent_id        TEXT,
  insurance_co    TEXT,
  product_name    TEXT,
  analysis_json   JSONB,               -- AI 분석 결과 전체
  raw_text        TEXT,
  source          TEXT DEFAULT 'crm',  -- 'crm' | 'ai'
  is_deleted      BOOLEAN DEFAULT false,
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. 데이터 동기화 전략

### 3-1. 양방향 동기화 원칙
- **어느 앱에서 입력해도** Supabase에 즉시 저장
- **앱 실행 시** Supabase에서 최신 데이터 pull → 로컬 merge
- **충돌 해결**: `updated_at` 최신값 우선 (Last-Write-Wins)
- **삭제**: `is_deleted: true` Soft Delete (실제 삭제 금지)

### 3-2. CRM 앱 동기화 흐름
```
앱 시작
  └─ syncFromSupabase()
       ├─ gk_people     → customerStore.customers
       ├─ gk_schedules  → customerStore.schedules
       └─ gk_scan_results → customerStore.scanResults

고객 등록/수정
  └─ upsertToSupabase(gk_people, data)
       └─ 성공 시 로컬 store도 업데이트

일정 등록/수정
  └─ upsertToSupabase(gk_schedules, data)
       └─ 성공 시 로컬 store도 업데이트
```

---

## 4. CRM 앱 구현 계획

### 4-1. 신규 파일: `src/services/supabaseService.js`
Supabase REST API 호출 전담 모듈

```javascript
// 주요 함수
fetchPeople(agentId)           // gk_people pull
upsertPerson(data)             // 고객 등록/수정
fetchSchedules(agentId)        // gk_schedules pull
upsertSchedule(data)           // 일정 등록/수정
fetchScanResults(personId)     // 증권 스캔 pull
upsertScanResult(data)         // 스캔 결과 저장
softDelete(table, id)          // is_deleted: true 처리
```

### 4-2. `customerStore.js` 수정
- `addCustomer()` → `upsertPerson()` 호출 추가
- `patchCustomer()` → `upsertPerson()` 호출 추가
- `addSchedule()` → `upsertSchedule()` 호출 추가
- 앱 시작 시 `syncFromSupabase()` 호출

### 4-3. `App.js` 수정
- `RoutingGuard` 마운트 시 `syncFromSupabase()` 실행

---

## 5. AI 앱(app.py) 연동 계획

### 5-1. 고객 등록 시
- 기존 `gk_people` INSERT 유지 (이미 구현됨)
- `agent_id` 필드 추가로 설계사별 분리

### 5-2. 일정 등록 시 (향후)
- `gk_schedules` INSERT 추가

### 5-3. 증권 분석 결과 (향후)
- `gk_scan_results` INSERT 추가
- CRM 앱에서 pull해서 "내보험다보여" 섹션 표시

---

## 6. 구현 단계 (확정 순서)

### Phase 1 — Goldkey AI Masters 2026 모바일 앱 완성 ← **현재 단계**
> CRM은 현재 골격(틀)만 유지. 모 앱이 100% 완성되면 Phase 2 시작.

| 단계 | 작업 |
|---|---|
| 1-1 | Goldkey AI Masters 2026 React Native 앱 전체 UI/UX 구현 |
| 1-2 | Supabase `gk_people` 컬럼 확장 + `gk_schedules`, `gk_scan_results` 생성 |
| 1-3 | 모 앱 ↔ Supabase 연동 100% 완성 (고객·일정·증권·AI리포트) |
| 1-4 | 인앱 CRM 설치 유도 팝업 포함 (`Linking.openURL` → Play Store) |

### Phase 2 — 모 앱 컴포넌트 CRM에 이식
> 모 앱 완성 후 시작. 컴포넌트 폴더째 복사 이식.

| 단계 | 작업 |
|---|---|
| 2-1 | `CustomerSection/` 폴더 CRM에 복사 이식 |
| 2-2 | `InsuranceView/` (증권분석·내보험다보여) 폴더 CRM에 복사 이식 |
| 2-3 | `ScheduleSection/` (일정 관리) 폴더 CRM에 복사 이식 |
| 2-4 | `AiReportSection/` (AI 상담 리포트) 폴더 CRM에 복사 이식 |
| 2-5 | Supabase 연동 서비스(`supabaseService.js`) 공유 또는 복사 |

### Phase 3 — CRM 핸드폰 레이아웃 최적화 후 배포
> 기능은 동일, 스타일(CSS/StyleSheet)만 핸드폰 화면에 맞게 조정.

| 단계 | 작업 |
|---|---|
| 3-1 | 각 이식 섹션 핸드폰 레이아웃 조정 (여백·폰트·터치 영역) |
| 3-2 | 태블릿 전용 2컬럼 레이아웃 → 핸드폰 1컬럼 전환 |
| 3-3 | Play Store AAB 빌드 + 내부 테스트 → 프로덕션 배포 |

### Phase 4 — 원클릭 생태계 구성 (단일 설치로 2개 앱)

#### 4-1. 단기 전략 — 인앱 설치 유도 팝업

Goldkey AI 모바일 앱 첫 실행 또는 설정 메뉴에서 팝업 표시:

```
┌─────────────────────────────────────────┐
│  📱 현장 관리를 더 스마트하게!           │
│                                         │
│  Goldkey AI Masters CRM을 설치하면      │
│  핸드폰에서 고객 상담·일정·증권분석을   │
│  언제 어디서나 관리할 수 있습니다.      │
│                                         │
│  [지금 설치하기]    [나중에]            │
└─────────────────────────────────────────┘
```

구현:
```javascript
// Goldkey AI 앱 내 — 첫 실행 시 또는 설정 메뉴
import { Linking } from 'react-native';

const CRM_PLAY_STORE_URL =
  'https://play.google.com/store/apps/details?id=com.goldkeycrm';

const openCrmInstall = () => Linking.openURL(CRM_PLAY_STORE_URL);
```

반대로 CRM 앱에서도 동일하게 Goldkey AI 설치 유도:
```javascript
const AI_PLAY_STORE_URL =
  'https://play.google.com/store/apps/details?id=com.goldkeyai';
```

---

#### 4-2. 중기 전략 — Play Store 앱 패밀리

- 두 앱을 동일 개발자 계정에 등록
- Play Store 각 앱 페이지 → "이 개발자의 다른 앱" 섹션 자동 노출
- 앱 설명란에 상호 교차 안내 문구 삽입

---

#### 4-3. 장기 전략 — Android App Bundle (AAB)

> Play Store의 **Android App Bundle** 기술을 활용한 궁극적 단일 패키지 배포

```
현재: 두 개의 독립 APK
       com.goldkeyai   → Goldkey AI Masters 2026
       com.goldkeycrm  → Goldkey AI Masters CRM

목표: 단일 AAB 패키지
       com.goldkeyai (메인 패키지)
         ├── base module       → 공통 코드 (Supabase, 인증, 공통 UI)
         ├── ai_module         → Goldkey AI 전체 기능
         └── crm_module        → CRM 기능 (Dynamic Feature Module)
```

**Dynamic Feature Module 방식:**
```
사용자가 Goldkey AI 설치
  → 기본 설치: base + ai_module (태블릿 최적화)
  → 앱 내 팝업: "CRM 모듈 다운로드 (12MB)"
  → 1탭으로 crm_module 다운로드 → 즉시 활성화
  → 핸드폰 아이콘에 "Goldkey AI Masters CRM" 별도 추가
```

**구현 요건:**
- React Native → Android Native Bridge 필요 (Play Feature Delivery API)
- 각 모듈 독립 빌드 설정 (`build.gradle` 분리)
- 모듈 간 공통 코드는 `base` 모듈로 통합

**단계별 접근:**
```
Step A (현재): 두 독립 앱 + 인앱 설치 유도 팝업
Step B (6개월): Play Store 앱 패밀리 교차 안내
Step C (1년+): AAB Dynamic Feature Module 통합
```

---

## 7. Play Store 심사 준비

| 항목 | Goldkey AI | Goldkey AI Masters CRM |
|---|---|---|
| **패키지명** | `com.goldkeyai` (신규) | `com.goldkeycrm` (기존) |
| **심사 시점** | Phase 1 완성 후 | Phase 2 완성 후 |
| **필수 준비물** | 개인정보처리방침 URL, 아이콘 512px, 스크린샷 5장 | 동일 |
| **심사 트랙** | 내부 테스트(20명) → 공개 프로덕션 | 동일 |
| **개발자 계정** | 동일 계정 필수 (앱 패밀리 구성) | 동일 계정 |
| **AAB 제출** | `.aab` 형식 (APK 아님) | 동일 |

---

## 8. 향후 추가 기능

- **SMS OTP 인증** — NCP(네이버 클라우드) 연동 (회원 증가 후)
- **푸시 알림** — 일정 D-1 알림 (Firebase FCM), CRM ↔ AI 양방향
- **실시간 동기화** — Supabase Realtime 구독 (폴링 → 웹소켓 업그레이드)
- **AAB Dynamic Feature** — CRM 모듈을 AI 앱에 통합 (궁극적 단일 패키지)
