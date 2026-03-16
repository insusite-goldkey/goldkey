# 🔐 Goldkey AI Masters 2026 — 보안 & 법적 컴플라이언스 점검 보고서
**작성일:** 2026-03-16  
**점검 대상:** 내보험다보여 연동 및 보험 데이터 처리 로직 전수 조사  
**점검 범위:** app.py · crm_app.py · shared_components.py · trinity_engine.py · data_normalizer.py

---

## 1. 인증 정보 처리 (내보험다보여 로그인 세션)

### ✅ 확인된 보안 처리
| 파일 | 위치 | 처리 내용 |
|------|------|-----------|
| `data_normalizer.py` | `purge_auth_credentials()` | `del` 명령어 + 덮어쓰기로 인증 정보 즉시 파기 (Zero Trust) |
| `app.py` | `_sops_c_phone` 세션 처리 | 전화번호 원문을 session_state에서 분석 후 `st.session_state.pop()` |
| `trinity_engine.py` | `hash_contact()` | SHA-256 단방향 해시만 DB 저장 — 원문 복원 불가 |

### ⚠️ 권고사항
- **[즉시 적용 권장]** 내보험다보여 연동 완료 직후 `purge_auth_credentials()` 호출 로직을 연동 버튼 핸들러에 명시적으로 삽입할 것
- `app.py` L-SECTION(line ~38995) 내 `_sec_session_key` 관련 변수가 분석 완료 후 `del` 처리되는지 확인 필요

---

## 2. 데이터 암호화

### ✅ 확인된 보안 처리
| 파일 | 위치 | 처리 내용 |
|------|------|-----------|
| `shared_components.py` | `encrypt_pii()` / `decrypt_pii()` | Fernet(AES-128-CBC) 양방향 암호화 — 고객 연락처 저장 |
| `shared_components.py` | `get_clean_phone()` | 숫자만 추출, 정규화 후 해싱 |
| `trinity_engine.py` | `hash_contact()` | `analysis_reports` 테이블 PK = SHA-256 해시 |
| `trinity_engine.py` | `save_analysis_to_db()` | `analysis_data` 필드 → Supabase JSONB (전송 시 SSL) |
| `analysis_reports_schema.sql` | RLS 정책 | `agent_id = auth.uid()` 본인 행만 접근 가능 |

### ⚠️ 권고사항
- **[주의]** `analysis_data` JSONB 필드에 저장되는 `_gap_summary`, `_covs_list`에 원문 연락처가 포함되지 않도록 파이프라인 검증 필요
- DB 저장 전 `analysis_data` 내 PII 필드 제거 로직 추가 권장

---

## 3. 동의 프로세스 (Consent Flow)

### ✅ 확인된 항목 — `shared_components.py` `render_auth_screen()` (line ~463)
| 동의 항목 | 키 | 필수 여부 | 신설/기존 |
|-----------|-----|-----------|-----------|
| 서비스 이용약관 (제1조~제11조) | `_c1` | 필수 | 기존 |
| 개인정보 수집·이용 (개보법 제15조) | `_c2` | 필수 | 기존 |
| 개인정보 암호화·보관·파기 | `_c3` | 필수 | 기존 |
| 마케팅·서비스 개선 | `_c4` | 선택 | 기존 |
| **내보험다보여 신용정보 조회** (신용정보법 제32조) | `_c5` | 기능 필수 | **2026-03-16 신설** |

### ✅ 전체 동의 체인
- `_c5` 항목이 "전체 동의" 자동 체크 로직에 포함됨 (line ~645)
- `nibo_consent_agreed`, `nibo_consent_version`, `nibo_consent_timestamp` 세션 저장
- 안내문 팝업(expander)으로 신용정보법 제32조 고지 의무 이행

### ⚠️ 권고사항
- **[즉시]** `save_nibo_consent_log()` (`data_normalizer.py`) 호출을 로그인 성공 직후에 추가하여 DB 이력 기록 시작
- 민감정보(질병·보험금 지급 사유) 처리에 대한 별도 동의 항목 (`_c6`) 추가 고려

---

## 4. 접근 제어 (URL 파라미터 조작 방어)

### ✅ 확인된 보안 처리
| 파일 | 위치 | 처리 내용 |
|------|------|-----------|
| `app.py` | line ~37419 | `gk_sector` URL 파라미터 수신 시 `auth_token` 검증 후 세션 활성화 |
| `shared_components.py` | `verify_sso_token()` | HMAC-SHA256 토큰 검증 — 위변조 URL 차단 |
| `app.py` | `_AUTH_GUARD` 패턴 | 로그인 미완료 시 분석 섹터 접근 불가 |

### ⚠️ 권고사항
- **[즉시 적용]** L-SECTION(내보험다보여 섹션, line ~38994) 진입 전 `nibo_consent_agreed` 세션 체크 가드 로직 추가:
  ```python
  if not st.session_state.get("nibo_consent_agreed", False):
      st.warning("내보험다보여 연동 동의가 필요합니다. 로그인 화면에서 동의 후 이용해 주세요.")
      st.stop()
  ```

---

## 5. 데이터 자동 파기 로직

### 현황
| 항목 | 상태 |
|------|------|
| 분석 보고서 30일 자동 삭제 | ❌ **미구현** — Supabase scheduled function 필요 |
| 세션 인증 정보 파기 | ✅ `purge_auth_credentials()` 구현 완료 |
| analysis_reports 갱신 | ✅ `updated_at` 트리거 자동 기록 |

### 권고 SQL (Supabase Edge Function 또는 pg_cron으로 등록):
```sql
-- 30일 경과 분석 임시 데이터 자동 마스킹
UPDATE analysis_reports
SET analysis_data = '{"masked": true}'::jsonb,
    report_text   = '[30일 경과 자동 파기]',
    updated_at    = NOW()
WHERE analyzed_at < NOW() - INTERVAL '30 days'
  AND analysis_data != '{"masked": true}'::jsonb;
```

---

## 6. data_normalizer.py 매핑 품질 점검

### ✅ 구현 완료 항목
| 기능 | 상태 | 파일:함수 |
|------|------|-----------|
| 마스터 키워드 사전 (9개 카테고리, 100+ 키워드) | ✅ | `data_normalizer.py:MAPPING_MAP` |
| 억/만원/천만원 단위 정밀 처리 | ✅ | `data_normalizer.py:normalize_amount()` |
| 미매핑 항목 파일 로그 | ✅ | `data_normalizer.py:log_unmapped_item()` |
| 중복 담보 합산/최댓값 정책 | ✅ | `data_normalizer.py:transform_to_trinity_format(duplicate_policy=)` |
| 실효·해지 계약 자동 필터 | ✅ | `data_normalizer.py:transform_to_trinity_format()` |
| 트리니티 엔진 파이프라인 연결 | ✅ | `trinity_engine.py:run_trinity_analysis()` |
| 동의 이력 DB 저장 | ✅ | `data_normalizer.py:save_nibo_consent_log()` |
| 인증 정보 Zero Trust 파기 | ✅ | `data_normalizer.py:purge_auth_credentials()` |

---

## 7. 종합 취약점 등급 및 즉시 조치 목록

| 우선순위 | 항목 | 조치 |
|----------|------|------|
| 🔴 HIGH | `nibo_consent_agreed` 가드 로직 미적용 (L-SECTION 진입 시) | app.py L-SECTION 상단에 가드 추가 |
| 🔴 HIGH | `save_nibo_consent_log()` 호출 미연결 (동의 DB 이력 미기록) | 로그인 성공 핸들러에 호출 추가 |
| 🟡 MED  | 분석 데이터 30일 자동 파기 스케줄러 미구현 | Supabase pg_cron 등록 |
| 🟡 MED  | `analysis_data` JSONB 내 PII 잔류 가능성 | 저장 전 PII 필드 제거 필터 추가 |
| 🟢 LOW  | 민감정보 별도 동의 항목(`_c6`) 미구현 | 다음 업데이트에서 추가 |

---

## 8. 기존 구현 vs. 요청 사항 비교표

| 요청 항목 | 기존 상태 | 이번 구현 | 비고 |
|-----------|-----------|-----------|------|
| 내보험다보여 데이터 파서 | ❌ 없음 | ✅ `data_normalizer.py` 신설 | 9개 카테고리, 100+ 키워드 |
| 금액 단위 정밀 처리(억/만/천) | ❌ 없음 | ✅ `normalize_amount()` | 1.5억 등 소수점 억 단위 처리 |
| 미매핑 로그 기록 | ❌ 없음 | ✅ `unmapped_coverage.log` | JSON 라인 포맷, 출처 포함 |
| 트리니티 파이프라인 연결 | 부분 | ✅ 완전 연결 | `transform_to_trinity_format()` → `run_trinity_analysis()` |
| 내보험다보여 전용 동의 팝업 | ❌ 없음 | ✅ expander 팝업 | 신용정보법 제32조 고지 |
| 전체동의에 내보험다보여 포함 | ❌ 없음 | ✅ `_c5` 체크박스 | HQ/CRM 공통 |
| 동의 이력 DB 저장 | ❌ 없음 | ✅ `save_nibo_consent_log()` | 버전 관리 포함 |
| Zero Trust 인증 정보 파기 | ❌ 없음 | ✅ `purge_auth_credentials()` | `del` 명령어 사용 |
| 보안 감사 보고서 | ❌ 없음 | ✅ 이 문서 | 코드 추적(Traceability) 포함 |
| SyntaxError 수정 (app.py 38999줄) | ❌ 오류 | ✅ 수정 완료 | `_lsec_badge` 변수 분리 |

---

*본 보고서는 2026-03-16 기준 코드베이스를 기반으로 작성되었습니다.*  
*다음 점검 권장 일시: 2026-06-16 (분기별 정기 감사)*
