# ══════════════════════════════════════════════════════════════════════════════
# [GP-DESIGN-V4] Agentic Soft-Tech 전역 디자인 시스템
# 2026-04-01 리빌딩 — 파스텔톤 표준 + 반응형 리퀴드 UI
# ══════════════════════════════════════════════════════════════════════════════

_GP_AGENTIC_DESIGN_CSS = """<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard-dynamic-subset.css');
@import url('https://fonts.googleapis.com/icon?family=Material+Icons|Material+Symbols+Rounded');

/* ══════════════════════════════════════════════════════════════════════════
   [GP-DESIGN-V4] Agentic Soft-Tech 테마 — 2026-04-01 리빌딩
   ══════════════════════════════════════════════════════════════════════════ */

/* ── 1. CSS 변수 (Agentic Soft-Tech Palette) ────────────────────────── */
:root {
  /* 배경색 */
  --gp-bg:           #F3F4F6;
  --gp-bg-soft:      #F9FAFB;
  
  /* 기본 블록 (소프트 인디고) */
  --gp-block-base:   #E0E7FF;
  --gp-block-hover:  #C7D2FE;
  
  /* 성공/진행 (민트) */
  --gp-success:      #DCFCE7;
  --gp-success-dark: #86EFAC;
  
  /* 경고/해지 (코랄) */
  --gp-warning:      #FEE2E2;
  --gp-warning-dark: #FCA5A5;
  
  /* 텍스트 */
  --gp-text:         #374151;
  --gp-text-dark:    #1F2937;
  --gp-text-muted:   #6B7280;
  
  /* 테두리 (1px solid #374151) */
  --gp-border:       #374151;
  --gp-border-light: #D1D5DB;
  
  /* 간격 (12px 고정) */
  --gp-gap:          12px;
  
  /* 반경 */
  --gp-radius:       10px;
  --gp-radius-sm:    8px;
  
  /* 그림자 */
  --gp-shadow:       0 1px 3px rgba(0,0,0,0.08);
  --gp-shadow-lg:    0 4px 12px rgba(0,0,0,0.12);
}

/* ── 2. 전역 리셋 + 반응형 기초 ──────────────────────────────────── */
* {
  box-sizing: border-box !important;
  word-wrap: break-word !important;
  word-break: keep-all !important;
  max-width: 100% !important;
}

[data-testid="stApp"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--gp-bg) !important;
  font-family: 'Pretendard', 'Inter', 'Noto Sans KR', 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif !important;
}

[data-testid="stSidebar"] {
  background: var(--gp-bg-soft) !important;
}

/* ── 3. 유동 타이포그래피 (clamp 함수) ──────────────────────────── */
html, body,
[data-testid="stApp"] *,
[data-testid="stSidebar"] * {
  font-size: clamp(14px, 2vw, 18px) !important;
}

h1 { font-size: clamp(18px, 3vw, 26px) !important; font-weight: 900 !important; }
h2 { font-size: clamp(16px, 2.5vw, 22px) !important; font-weight: 800 !important; }
h3 { font-size: clamp(14px, 2vw, 18px) !important; font-weight: 700 !important; }

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li {
  font-size: clamp(14px, 2vw, 18px) !important;
  color: var(--gp-text) !important;
  line-height: 1.6 !important;
  word-break: keep-all !important;
  overflow-wrap: break-word !important;
}

label[data-testid="stWidgetLabel"] {
  font-size: clamp(13px, 1.8vw, 16px) !important;
  color: var(--gp-text-dark) !important;
  font-weight: 600 !important;
}

/* ── 4. Grid 시스템 (12px 고정 간격) ────────────────────────────── */
[data-testid="stVerticalBlock"] {
  gap: var(--gp-gap) !important;
}

[data-testid="stHorizontalBlock"] {
  gap: var(--gp-gap) !important;
  flex-wrap: wrap !important;
}

[data-testid="element-container"] {
  margin-bottom: var(--gp-gap) !important;
  padding: var(--gp-gap) !important;
}

/* ── 5. 리퀴드 UI (flex-wrap: wrap) ─────────────────────────────── */
[data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: var(--gp-gap) !important;
}

[data-testid="column"] {
  flex: 1 1 calc(50% - var(--gp-gap)) !important;
  min-width: 200px !important;
  max-width: 100% !important;
}

/* 모바일 (768px 이하) — 100% 수직 스태킹 */
@media (max-width: 768px) {
  [data-testid="column"] {
    flex: 1 1 100% !important;
    min-width: 100% !important;
    width: 100% !important;
  }
  
  [data-testid="stHorizontalBlock"] {
    flex-direction: column !important;
  }
}

/* 태블릿 (769px ~ 1024px) — 2열 유지 */
@media (min-width: 769px) and (max-width: 1024px) {
  [data-testid="column"] {
    flex: 1 1 calc(50% - var(--gp-gap)) !important;
    min-width: 280px !important;
  }
}

/* ── 6. 버튼 시스템 (Agentic Soft-Tech) ─────────────────────────── */
[data-testid="stButton"] > button {
  border-radius: var(--gp-radius-sm) !important;
  font-weight: 700 !important;
  font-size: clamp(12px, 1.8vw, 15px) !important;
  padding: 8px 16px !important;
  line-height: 1.4 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  transition: all 0.2s ease !important;
  box-shadow: var(--gp-shadow) !important;
  border: 1px solid var(--gp-border) !important;
}

[data-testid="stButton"] > button[kind="secondary"] {
  background: var(--gp-block-base) !important;
  color: var(--gp-text-dark) !important;
  border-color: var(--gp-border) !important;
}

[data-testid="stButton"] > button[kind="secondary"]:hover {
  background: var(--gp-block-hover) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--gp-shadow-lg) !important;
}

[data-testid="stButton"] > button[kind="primary"] {
  background: var(--gp-success) !important;
  color: var(--gp-text-dark) !important;
  border-color: var(--gp-border) !important;
  font-weight: 900 !important;
}

[data-testid="stButton"] > button[kind="primary"]:hover {
  background: var(--gp-success-dark) !important;
  transform: translateY(-1px) !important;
  box-shadow: var(--gp-shadow-lg) !important;
}

/* ── 7. Alert 시스템 ─────────────────────────────────────────────── */
.stAlert {
  border-radius: var(--gp-radius-sm) !important;
  font-size: clamp(13px, 1.8vw, 15px) !important;
  padding: var(--gp-gap) !important;
  margin: var(--gp-gap) 0 !important;
  border: 1px solid var(--gp-border) !important;
}

[data-testid="stAlert"] {
  max-width: 100% !important;
  width: 100% !important;
}

/* ── 8. 입력 필드 ────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] input {
  border: 1px solid var(--gp-border-light) !important;
  border-radius: var(--gp-radius-sm) !important;
  background: #ffffff !important;
  font-size: clamp(13px, 1.8vw, 15px) !important;
  color: var(--gp-text-dark) !important;
  padding: 8px 12px !important;
  transition: all 0.2s ease !important;
}

[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus,
[data-testid="stNumberInput"] input:focus {
  border-color: var(--gp-border) !important;
  box-shadow: 0 0 0 3px rgba(55, 65, 81, 0.1) !important;
  outline: none !important;
}

/* ── 9. 탭 시스템 ────────────────────────────────────────────────── */
[data-testid="stTabs"] [data-testid="stTab"] {
  background: var(--gp-bg-soft) !important;
  border-bottom: 2px solid transparent !important;
  color: var(--gp-text-muted) !important;
  font-weight: 700 !important;
  font-size: clamp(12px, 1.8vw, 14px) !important;
  padding: 8px 16px !important;
  border-radius: var(--gp-radius-sm) var(--gp-radius-sm) 0 0 !important;
  transition: all 0.2s !important;
}

[data-testid="stTabs"] [aria-selected="true"][data-testid="stTab"] {
  background: var(--gp-block-base) !important;
  border-bottom-color: var(--gp-border) !important;
  color: var(--gp-text-dark) !important;
  font-weight: 900 !important;
}

/* ── 10. 라디오 네비게이션 ───────────────────────────────────────── */
div[data-testid="stRadio"] > div {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: 8px !important;
  background: var(--gp-bg-soft) !important;
  padding: 8px !important;
  border-radius: var(--gp-radius) !important;
  border: 1px solid var(--gp-border-light) !important;
}

div[data-testid="stRadio"] > div > label {
  flex: 1 1 auto !important;
  text-align: center !important;
  padding: 8px 12px !important;
  border-radius: var(--gp-radius-sm) !important;
  border: 1px solid var(--gp-border-light) !important;
  background: #ffffff !important;
  font-size: clamp(11px, 1.6vw, 13px) !important;
  font-weight: 700 !important;
  cursor: pointer !important;
  white-space: nowrap !important;
  transition: all 0.2s !important;
  color: var(--gp-text) !important;
}

div[data-testid="stRadio"] > div > label:has(input:checked) {
  background: var(--gp-block-base) !important;
  color: var(--gp-text-dark) !important;
  border-color: var(--gp-border) !important;
  font-weight: 900 !important;
}

div[data-testid="stRadio"] > div > label > div:first-child {
  display: none !important;
}

/* ── 11. Placeholder 최적화 ──────────────────────────────────────── */
::placeholder,
input::placeholder,
textarea::placeholder {
  color: var(--gp-text-muted) !important;
  opacity: 0.5 !important;
  font-size: 0.9em !important;
}

input:focus::placeholder,
textarea:focus::placeholder {
  opacity: 0 !important;
}

/* ── 12. 모바일 최적화 ───────────────────────────────────────────── */
@media (max-width: 768px) {
  h1 { font-size: clamp(16px, 4vw, 20px) !important; }
  h2 { font-size: clamp(14px, 3.5vw, 18px) !important; }
  h3 { font-size: clamp(13px, 3vw, 16px) !important; }
  
  [data-testid="stButton"] > button {
    font-size: clamp(12px, 3vw, 14px) !important;
    padding: 10px 14px !important;
  }
  
  .stAlert {
    font-size: clamp(12px, 3vw, 14px) !important;
  }
}

/* ── 13. 컨테이너 박스 표준 ──────────────────────────────────────── */
.gp-box {
  background: #ffffff !important;
  border: 1px solid var(--gp-border) !important;
  border-radius: var(--gp-radius) !important;
  padding: var(--gp-gap) !important;
  margin: var(--gp-gap) 0 !important;
  box-shadow: var(--gp-shadow) !important;
}

.gp-box-success {
  background: var(--gp-success) !important;
  border-color: var(--gp-border) !important;
}

.gp-box-warning {
  background: var(--gp-warning) !important;
  border-color: var(--gp-border) !important;
}

.gp-box-info {
  background: var(--gp-block-base) !important;
  border-color: var(--gp-border) !important;
}

/* ── 14. CRM 액션 그리드 (반응형) ────────────────────────────────── */
.crm-action-grid-wrap {
  width: 100% !important;
  max-width: 100% !important;
}

.crm-action-grid-wrap [data-testid="stHorizontalBlock"] {
  display: flex !important;
  flex-wrap: wrap !important;
  gap: var(--gp-gap) !important;
}

.crm-action-grid-wrap [data-testid="column"] {
  flex: 1 1 calc(25% - var(--gp-gap)) !important;
  min-width: 150px !important;
}

@media (max-width: 768px) {
  .crm-action-grid-wrap [data-testid="column"] {
    flex: 1 1 calc(50% - var(--gp-gap)) !important;
    min-width: 140px !important;
  }
}

/* ── 15. Material Icons 보호 ─────────────────────────────────────── */
.material-icons,
.material-symbols-rounded,
.material-symbols-outlined {
  font-family: 'Material Icons', 'Material Symbols Rounded' !important;
  font-feature-settings: 'liga' !important;
  -webkit-font-feature-settings: 'liga' !important;
  text-rendering: optimizeLegibility !important;
}

/* ── 16. 가로 스크롤 방지 ────────────────────────────────────────── */
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
.main,
.element-container,
[data-testid="stMarkdownContainer"] {
  overflow-x: hidden !important;
  max-width: 100% !important;
}

/* ── 17. 폼 컨테이너 최적화 ──────────────────────────────────────── */
[data-testid="stForm"] {
  max-width: min(480px, 95vw) !important;
  margin: var(--gp-gap) auto !important;
  background: #ffffff !important;
  border: 1px solid var(--gp-border) !important;
  border-radius: var(--gp-radius) !important;
  padding: calc(var(--gp-gap) * 1.5) !important;
  box-shadow: var(--gp-shadow-lg) !important;
}

[data-testid="stFormSubmitButton"] button {
  font-size: clamp(14px, 2vw, 16px) !important;
  min-height: 44px !important;
  font-weight: 800 !important;
  border-radius: var(--gp-radius-sm) !important;
  width: 100% !important;
}

</style>"""


def inject_agentic_design() -> None:
    """
    [GP-DESIGN-V4] Agentic Soft-Tech 전역 디자인 시스템 주입.
    
    2026-04-01 리빌딩 명령:
    - Color: 배경 #F3F4F6, 블록 #E0E7FF, 성공 #DCFCE7, 경고 #FEE2E2
    - Grid: 모든 padding/margin/gap = 12px 고정
    - Typography: clamp() 함수로 반응형 자동 조절
    - Layout: flex-wrap:wrap으로 리퀴드 UI 적용
    - Border: 1px solid #374151 통일
    
    적용 대상:
    - app.py (HQ 앱)
    - crm_app.py (CRM 앱)
    """
    import streamlit as st
    st.markdown(_GP_AGENTIC_DESIGN_CSS, unsafe_allow_html=True)
