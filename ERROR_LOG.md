# GoldKey AI — 에러 관리 기록부
> 마지막 업데이트: 2026-02-25

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

## 🔄 자동 회복 체계

### 현재 구현된 회복 방안
1. **`push_all.ps1`**: push 실패 시 최대 3회 자동 재시도 + HEAD 불일치 감지
2. **`log_error()` 함수**: 런타임 에러 자동 기록 (`/tmp/error_log.json`, 최근 200건)
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
