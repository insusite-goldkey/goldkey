# GOLD KEY PROJECT - CORE RULES (절대 위반 금지)

## 📜 시스템 헌법 — 영구 롤백 방지 및 코드 안정성 보장

**작성일**: 2026-03-30  
**적용 범위**: Goldkey AI Masters 2026 전체 프로젝트  
**우선순위**: 최상위 (모든 GP 규칙보다 우선)

---

## 🔴 RULE 1: Session State 절대 보호

### 원칙
로그인 및 네비게이션 이동 시 `st.session_state`가 튕기거나 White Screen이 발생하지 않도록, 모든 메인 함수 최상단에 상태 초기화/유지 방어 코드를 필수 적용할 것.

### 구현 요구사항
```python
# [필수] 모든 앱 진입점 최상단에 배치
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = ""

# [필수] 세션 복구 로직 — Auto-login
if st.session_state.get("user_id") and not st.session_state.get("authenticated"):
    st.session_state["authenticated"] = True
    st.session_state["_is_auth"] = True
```

### 금지 사항
- ❌ 세션 초기화 로직 삭제 또는 주석 처리
- ❌ `st.rerun()` 호출 시 세션 상태 검증 생략
- ❌ 에러 발생 시 세션 전체 `clear()` 호출 (선택적 키 삭제만 허용)

### 적용 파일
- `hq_app_impl.py` (line 31-49)
- `crm_app_impl.py` (line 758-764)

---

## 🔴 RULE 2: HTML 렌더링 강제

### 원칙
'트리니티 계산법' 등 설명문 영역의 HTML 태그는 반드시 `st.markdown(..., unsafe_allow_html=True)`를 유지할 것. 임의로 일반 텍스트 렌더링으로 롤백 금지.

### 구현 요구사항
```python
# [필수] HTML 포함 마크다운 렌더링 시
st.markdown(
    "<div style='...'> ... </div>",
    unsafe_allow_html=True  # ← 절대 삭제 금지
)
```

### 검증 체크리스트
1. ✅ HTML 태그가 화면에 텍스트로 노출되지 않는가?
2. ✅ `st.markdown()`에 HTML이 포함된 경우 `unsafe_allow_html=True`가 설정되어 있는가?
3. ✅ 불필요한 HTML 변환 없이 Markdown 문법을 우선 사용했는가?

### 금지 사항
- ❌ `unsafe_allow_html=True` 파라미터 삭제
- ❌ HTML 코드를 일반 텍스트로 변환
- ❌ 기존 HTML 디자인을 Streamlit 네이티브 컴포넌트로 임의 교체

### 적용 파일
- `shared_components.py` (line 1139-1140, 2551, 2626)
- 모든 `st.markdown()` 호출 지점

---

## 🔴 RULE 3: GP 반응형 디자인

### 원칙
모든 AI 분석 보고서 및 컨테이너 박스는 `use_container_width=True` 및 CSS `word-wrap: break-word;`를 적용하여 모바일 화면 밖으로 뚫고 나가지 않게 가둘 것.

### 구현 요구사항

#### CSS 전역 적용 (필수)
```css
/* [DEFCON 1 - ACTION 3] 모바일 반응형 강제 적용 */
* {
  word-wrap: break-word !important;
  word-break: keep-all !important;
  max-width: 100% !important;
  box-sizing: border-box !important;
}

div[data-testid="stMarkdownContainer"],
div[data-testid="stMarkdown"],
.stMarkdown,
.element-container {
  max-width: 100% !important;
  overflow-wrap: break-word !important;
  word-wrap: break-word !important;
}
```

#### Streamlit 컴포넌트 적용 (필수)
```python
# [필수] 모든 버튼, 입력 필드, 컨테이너
st.button("버튼", use_container_width=True)
st.text_input("입력", use_container_width=True)
```

### 금지 사항
- ❌ 모바일 반응형 CSS 삭제 또는 주석 처리
- ❌ `use_container_width=True` 파라미터 제거
- ❌ 고정 너비(`width: 500px` 등) 하드코딩

### 적용 파일
- `shared_components.py` (line 2670-2694)
- 모든 UI 컴포넌트 렌더링 코드

---

## 🔴 RULE 4: Zero-Trust 파이프라인

### 원칙
외부 데이터(뉴스, OCR 등)는 반드시 4단계 검증(추출 → LLM 구조화 → Python 검증 → Human 승인)을 거칠 것.

### 4단계 검증 프로세스

#### STAGE 1: 데이터 추출 (Extraction)
- 외부 API, 웹 크롤링, OCR 등으로 원시 데이터 수집
- 로그 기록 필수

#### STAGE 2: LLM 구조화 (Structuring)
- Gemini/GPT API로 비구조화 데이터를 JSON/구조화 형태로 변환
- 프롬프트에 출력 형식 명시 필수

#### STAGE 3: Python 검증 (Validation)
```python
# [필수] 모든 외부 데이터 검증
try:
    data = json.loads(llm_output)
    assert "required_field" in data
    assert isinstance(data["required_field"], str)
except (json.JSONDecodeError, AssertionError, KeyError) as e:
    st.error(f"❌ 데이터 검증 실패: {e}")
    return None
```

#### STAGE 4: Human 승인 (Approval)
- 최종 데이터를 사용자에게 미리보기로 표시
- 사용자 확인 버튼 클릭 후 DB 저장

### 금지 사항
- ❌ 외부 데이터를 검증 없이 직접 DB 저장
- ❌ LLM 출력을 `eval()` 또는 `exec()`로 실행
- ❌ 에러 발생 시 `except: pass`로 무시

### 적용 파일
- `modules/zero_trust_validator.py`
- 모든 외부 데이터 처리 함수

---

## 🛡️ 위반 시 조치

### 자동 롤백 트리거
다음 상황 발생 시 즉시 이전 버전으로 롤백:
1. White Screen 또는 세션 마비 발생
2. HTML 태그가 화면에 텍스트로 노출
3. 모바일 화면에서 UI 요소가 화면 밖으로 이탈
4. 외부 데이터 검증 없이 DB 저장

### 보고 의무
- 위반 사항 발견 즉시 설계자에게 보고
- 롤백 완료 후 수정 내역 상세 기록

---

## 📌 AI 어시스턴트 확약 (Commit)

**본 AI 어시스턴트(Windsurf Cascade)는 다음을 확약합니다:**

1. ✅ 모든 코드 수정 작업 전 본 `GP_CORE_RULES.md` 파일을 반드시 읽고 검토
2. ✅ 4대 코어 룰 위반 여부를 스스로 검열 후 작업 진행
3. ✅ 위반 사항 발견 시 즉시 설계자에게 보고 및 롤백
4. ✅ 설계자의 명시적 승인 없이 코어 룰 수정 절대 금지

**서명**: Windsurf Cascade AI Assistant  
**날짜**: 2026-03-30  
**버전**: v1.0 (DEFCON 1 긴급 복구 완료 후 확정)

---

## 🔗 관련 규칙

- `[GP-ARCHITECT-PRIORITY]` 설계자 우선 원칙
- `[GLOBAL POLICY: STRICT CODE PERSISTENCE]` 코드 영속성 정책
- `[GP 전역 UI/UX 렌더링 헌법]` HTML 태그 노출 금지
- `GP 제53조` 코딩 원칙 및 개발 5대 수칙

---

**이 파일은 프로젝트의 최상위 헌법입니다. 어떠한 이유로도 삭제하거나 수정할 수 없습니다.**
