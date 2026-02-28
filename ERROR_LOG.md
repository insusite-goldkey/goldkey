# GoldKey AI — 에러 관리 기록부
> 마지막 업데이트: 2026-02-28

---

## 📋 에러 이력

### [E001] tab_home_btn 내 st.stop() — 모든 탭 내용 차단
- **발생일**: 2026-02-25
- **커밋**: `073dd53`
- **증상**: 홈에서 카테고리 클릭 → 탭 화면이 아무것도 표시되지 않음
- **원인**: `tab_home_btn()` 함수 마지막에 `st.stop()` 삽입 (lazy-dispatch 의도)
  - `tab_home_btn()`은 탭 맨 위에서 호출됨
  - `st.stop()` = 이후 모든 코드 실행 차단
  - → 홈 버튼만 표시되고 탭 전체 내용이 렌더링되지 않음
- **수정**: `st.stop()` 한 줄 제거
- **예방책**:
  - `tab_home_btn()`처럼 공통 헬퍼 함수에는 절대 `st.stop()` 사용 금지
  - `st.stop()`은 탭 최하단(렌더 완료 후)에만 사용

---

### [E002] _render_cards referenced before assignment
- **발생일**: 2026-02-25
- **커밋**: `3ee8caf`
- **증상**: 홈 화면 로드 시 `UnboundLocalError: local variable '_render_cards' referenced before assignment`
- **원인**: `_render_cards` 함수 정의(5841줄)가 첫 호출(5826줄)보다 뒤에 위치
  - Python은 함수가 실행 흐름상 호출보다 앞에 정의되어야 함
- **수정**: 함수 정의 블록을 첫 호출 바로 앞으로 이동
- **예방책**:
  - 동일 스코프 내 함수는 항상 사용 전 정의
  - 홈 화면처럼 복잡한 블록 수정 시 함수 정의/호출 순서 확인

---

### [E003] HF Space push 누락 — 앱이 업데이트되지 않는 문제
- **발생일**: 2026-02-25 (누적 반복)
- **커밋**: `707c851` (자동화 스크립트)
- **증상**: 코드 수정 후 push했으나 HF Space 앱이 변경되지 않음
- **원인**: `git push origin main`만 실행 → GitHub에만 반영, HuggingFace Space에는 별도 push 필요
- **수정**: `push_all.ps1` 생성 — GitHub + HF 동시 push + 재시도 3회 + HEAD 검증 + 빌드 polling
- **예방책**:
  - **앞으로 모든 push는 `push_all.ps1`만 사용**
  - `git push origin main` 단독 명령 사용 금지

---

### [E004] requirements.txt 누락 패키지 — 앱 런타임 크래시
- **발생일**: 2026-02-25
- **커밋**: `c584762`
- **증상**: 스캔허브 Excel 다운로드 / PDF 암호화 시 `ModuleNotFoundError`
- **원인**: `openpyxl`, `pypdf` 패키지가 코드에서 사용되나 requirements.txt 미등록
- **수정**: requirements.txt에 `openpyxl>=3.1.0`, `pypdf>=4.0.0` 추가
- **예방책**:
  - 새 패키지 `import` 추가 시 즉시 requirements.txt 동시 업데이트
  - `try: import X` 패턴 사용 시에도 requirements.txt 등록 필수

---

### [E005] 스크롤 아래로 내린 후 위로 올라가지 않는 문제 ⚠️ 반복 3회 이상
- **발생일**: 2026-02-28 (누적 반복 — 3차 이상 수정 지시)
- **증상**: 앱을 아래로 스크롤한 뒤 위로 다시 올라가지 않음 (스크롤 잠금)
- **원인**: Pull-to-Refresh 차단 목적으로 삽입한 `touchmove` 이벤트 리스너
  - `{passive: false}` + `e.preventDefault()` 조합이 위 방향 스크롤까지 차단
  - 조건: `y > lastY && scrollY === 0` → 최상단이 아닐 때도 간섭 발생
- **수정 이력**:
  - 1차: CSS `overflow-y: auto` 추가 — 미해결
  - 2차: `overscroll-behavior-y: contain` CSS 추가 — 미해결
  - 3차 (2026-02-28): `touchmove` 리스너 완전 제거 → CSS `overscroll-behavior-y: contain` 단독 적용
- **현재 상태**: ✅ 3차 수정 적용 완료 (`app.py` line ~5826)
- **예방책**:
  - **`touchmove` + `passive:false` + `e.preventDefault()` 조합 절대 사용 금지**
  - Pull-to-Refresh 차단은 CSS `overscroll-behavior-y: contain` 만 사용
  - 스크롤 관련 JS 수정 시 상하 양방향 테스트 필수

---

### [E006] 로그인 입력창 "Press Enter to submit form" 영문 툴팁 노출
- **발생일**: 2026-02-28
- **증상**: 이름·전화번호 입력창 클릭 시 "Press Enter to submit form" 영문 툴팁 출력
- **원인**: Streamlit이 `st.form` 내 `st.text_input`에 `title` 속성 자동 주입
  - CSS로는 `title` 속성 tooltip 제어 불가 (HTML 표준 브라우저 동작)
- **수정**: JavaScript `MutationObserver`로 `input[title]` 속성 실시간 제거
  - `app.py` line ~6890 — 로그인 탭 렌더 직후 `components.html` 삽입
- **현재 상태**: ✅ 수정 완료
- **예방책**:
  - `st.form` 내 `st.text_input` 사용 시 title 자동 주입 인지
  - `label_visibility="collapsed"` + JS title 제거 조합 표준으로 유지

---

### [E007] 음성 네비게이션 — 탭 이동 실패 (텍스트 매칭 오류)
- **발생일**: 2026-02-28
- **증상**: 음성 인식 후 정확히 인식되나 탭 이동 버튼이 동작하지 않음
- **원인**:
  1. JS→Python 통신: `components.html` 방식은 `setComponentValue` 미지원
  2. 키워드 매핑 테이블(`_NAV_INTENT_MAP`)이 하드코딩 리스트로 관리 → 수정 시 JS/Python 불일치 발생
  3. `_vnav_css` 문자열이 닫히지 않아 Python 코드가 CSS 문자열 안에 삽입되는 파싱 오류
- **수정 (2026-02-28)**:
  1. `st.components.v2.component` + `setTriggerValue` 방식으로 JS→Python 직접 통신 구현
  2. **전사적 섹터 ID 관리 시스템** 도입:
     - `SECTOR_CODES` 상수 (4자리 분류체계, 1000~8300번대) 모듈 레벨 정의
     - `_NAV_INTENT_MAP` → `SECTOR_CODES`에서 자동 생성 (수동 편집 제거)
  3. `_voice_navigate()` 0순위 로직 추가: 4자리 ID 직접 매칭 (`\b\d{4}\b`)
  4. `log_error()` 함수 추가: 오류 발생 시 섹터 ID·이름 포함 기록
- **섹터 ID 체계**:
  ```
  1000번대: 홈/스캔/분석 허브  (1000 홈, 1100 스캔, 1200 증권분석, 1300 약관)
  2000번대: 상해·청구·장해     (2000 신규, 2100 상해, 2200 청구, 2300 장해)
  3000번대: 질환 상담          (3000 암, 3100 뇌, 3200 심장)
  4000번대: 보험 설계          (4000 기본, 4100 통합, 4200 자동차사고)
  5000번대: 자산/세무/법인     (5000 노후, 5100 세무, 5200 법인, 5300 CEO, 5400 비상장)
  6000번대: 전문 보험          (6000 화재, 6100 배상, 6200 간병, 6300 부동산)
  7000번대: 라이프 플랜        (7000 LIFECYCLE, 7100 LIFEEVENT)
  8000번대: 콘텐츠/자료        (8000 리플렛, 8100 카탈로그, 8200 고객자료, 8300 디지털)
  ```
- **예방책**:
  - 신규 섹터 추가 시 반드시 `SECTOR_CODES`에 먼저 등록 (`_NAV_INTENT_MAP` 자동 갱신)
  - 오류 발생 시 `log_error(msg, sector_id="XXXX")` 호출로 즉시 섹터 추적
  - `st.components.v2.component`는 동일 `name` 재등록 시 경고 발생 → 고유명 유지

---

## 🔄 자동 회복 체계

### 현재 구현된 회복 방안
1. **`push_all.ps1`**: push 실패 시 최대 3회 자동 재시도 + HEAD 불일치 감지
2. **`log_error()` 함수**: 런타임 에러 자동 기록 (`/tmp/gk_error_log.json`, 최근 300건, **섹터 ID 포함**)
3. **t9 관리자탭 에러 로그**: 실시간 에러 확인 및 원클릭 삭제
4. **자가진단 엔진**: 알려진 버그 패턴 자동 감지 + 수정 버튼

### 추가 권장 회복 방안
| 상황 | 대응 |
|---|---|
| 탭 내용 미표시 | `tab_home_btn`에 `st.stop()` 여부 확인 |
| 앱 수정 미반영 | `push_all.ps1` 실행 후 HF polling 확인 |
| 패키지 오류 | requirements.txt + app.py import 동시 점검 |
| 문법 오류 | `python -c "import ast; ast.parse(...)"` 검증 후 push |

---

## 🛡️ 배포 전 체크리스트

```
[ ] 문법 검증: python -c "import ast; ast.parse(open('app.py','r',encoding='utf-8').read())"
[ ] push_all.ps1 사용 (origin + hf 동시)
[ ] HF 빌드 polling 확인 (RUNNING 상태 확인)
[ ] 탭 내용 표시 여부 브라우저 확인
```
