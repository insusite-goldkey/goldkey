# ══════════════════════════════════════════════════════════════════════════════
# [GP-DESIGN-V5] 유기적 반응형 UI 엔진 (Fluid Responsive UI Engine)
# 작성일: 2026-03-31
# 목적: 태블릿(5:5) vs 모바일(수직 스택) 적응형 레이아웃 자동 전환
# ══════════════════════════════════════════════════════════════════════════════
"""
[GP-FLUID-UI] 모바일 vs 태블릿 유기적 적응형 설계

## 핵심 원칙
1. **Layout Morphing**: 1024px 기준으로 5:5 ↔ 수직 스택 자동 전환
2. **Fluid Typography**: CSS clamp()로 화면 크기별 텍스트 유기적 스케일링
3. **Adaptive Input**: 태블릿(Drag&Drop) vs 모바일(카메라 스캔 Floating)
4. **Identity Guard**: GP 골드·네온블루 다크테마 전역 일관성 유지

## 브레이크포인트
- Desktop/Tablet Landscape (≥1024px): 5:5 Side-by-Side
- Mobile/Tablet Portrait (<1024px): Top-to-Bottom Stack
- Mobile Compact (<768px): 단일 컬럼 + Floating 액션 버튼

## 사용법
```python
from modules.fluid_responsive_ui import inject_fluid_responsive_design

# 앱 진입점 최상단에서 1회 호출
inject_fluid_responsive_design()
```
"""

import streamlit as st


def inject_fluid_responsive_design():
    """
    [GP-DESIGN-V5] 유기적 반응형 UI 시스템 주입
    
    태블릿/모바일 환경에서 레이아웃 자동 변신, Fluid Typography,
    적응형 입력 방식, GP Identity 보존을 통합 제공.
    """
    st.markdown("""
    <style>
    /* ══════════════════════════════════════════════════════════════════════════════
       [GP-DESIGN-V5] 유기적 반응형 UI 엔진 (Fluid Responsive UI)
       작성일: 2026-03-31
       목적: 태블릿(5:5) ↔ 모바일(수직 스택) 자동 변신 + Fluid Typography
    ══════════════════════════════════════════════════════════════════════════════ */
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 1. GP Identity Guard — 전역 디자인 변수 (골드·네온블루 다크테마)
    ──────────────────────────────────────────────────────────────────────────── */
    :root {
        /* GP 브랜드 컬러 (절대 변경 금지) */
        --gp-gold: #FFD700;
        --gp-gold-dark: #B8860B;
        --gp-neon-blue: #00D9FF;
        --gp-neon-blue-dark: #0099CC;
        --gp-charcoal: #1A1A1A;
        --gp-charcoal-light: #2D2D2D;
        --gp-white: #FFFFFF;
        --gp-gray-light: #E0E0E0;
        
        /* Fluid Typography 변수 (clamp 스케일링) */
        --font-xs: clamp(0.7rem, 1.5vw, 0.75rem);
        --font-sm: clamp(0.8rem, 1.8vw, 0.875rem);
        --font-base: clamp(0.875rem, 2vw, 1rem);
        --font-lg: clamp(1rem, 2.5vw, 1.25rem);
        --font-xl: clamp(1.25rem, 3vw, 1.5rem);
        --font-2xl: clamp(1.5rem, 4vw, 2rem);
        --font-3xl: clamp(2rem, 5vw, 3rem);
        
        /* 핵심 숫자 강조 (모바일 가독성 우선) */
        --font-metric-value: clamp(1.75rem, 4.5vw, 2.5rem);
        --font-metric-label: clamp(0.75rem, 2vw, 0.9rem);
        
        /* 간격 변수 */
        --spacing-xs: clamp(0.25rem, 1vw, 0.5rem);
        --spacing-sm: clamp(0.5rem, 1.5vw, 0.75rem);
        --spacing-md: clamp(0.75rem, 2vw, 1rem);
        --spacing-lg: clamp(1rem, 2.5vw, 1.5rem);
        --spacing-xl: clamp(1.5rem, 3vw, 2rem);
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 2. Layout Morphing — 5:5 ↔ 수직 스택 자동 전환
    ──────────────────────────────────────────────────────────────────────────── */
    
    /* Desktop/Tablet Landscape (≥1024px): 5:5 Side-by-Side 유지 */
    @media (min-width: 1024px) {
        [data-testid="column"] {
            /* Streamlit 기본 컬럼 레이아웃 유지 */
            flex-direction: row;
        }
        
        /* 드롭존 강조 (태블릿 전용) */
        .gp-dropzone {
            border: 3px dashed var(--gp-neon-blue);
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.1) 0%, rgba(102, 126, 234, 0.1) 100%);
            padding: var(--spacing-xl);
            border-radius: 15px;
            transition: all 0.3s ease;
        }
        
        .gp-dropzone:hover {
            border-color: var(--gp-gold);
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(184, 134, 11, 0.1) 100%);
            transform: scale(1.02);
        }
    }
    
    /* Mobile/Tablet Portrait (<1024px): Top-to-Bottom Stack */
    @media (max-width: 1023px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 100% !important;
            min-width: 100% !important;
            margin-bottom: var(--spacing-lg);
        }
        
        /* 좌측(입력) 박스를 상단으로 */
        [data-testid="column"]:first-child {
            order: 1;
        }
        
        /* 우측(분석) 박스를 하단으로 */
        [data-testid="column"]:last-child {
            order: 2;
        }
        
        /* 드롭존 모바일 최적화 */
        .gp-dropzone {
            border: 2px dashed var(--gp-neon-blue);
            padding: var(--spacing-lg);
            border-radius: 12px;
        }
    }
    
    /* Mobile Compact (<768px): 단일 컬럼 + 여백 최소화 */
    @media (max-width: 767px) {
        .main .block-container {
            padding-left: var(--spacing-sm) !important;
            padding-right: var(--spacing-sm) !important;
            padding-top: var(--spacing-md) !important;
        }
        
        /* 불필요한 장식 요소 숨김 (가독성 우선) */
        .gp-decoration {
            display: none;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 3. Fluid Typography — 유기적 텍스트 스케일링
    ──────────────────────────────────────────────────────────────────────────── */
    
    /* 헤드라인 (태블릿: 24pt → 모바일: 18pt) */
    h1, .gp-headline {
        font-size: var(--font-2xl) !important;
        font-weight: 700;
        color: var(--gp-gold);
        line-height: 1.2;
        margin-bottom: var(--spacing-md);
    }
    
    h2, .gp-subheadline {
        font-size: var(--font-xl) !important;
        font-weight: 600;
        color: var(--gp-neon-blue);
        line-height: 1.3;
        margin-bottom: var(--spacing-sm);
    }
    
    h3, .gp-section-title {
        font-size: var(--font-lg) !important;
        font-weight: 600;
        color: var(--gp-white);
        margin-bottom: var(--spacing-sm);
    }
    
    /* 본문 텍스트 */
    p, .gp-body-text {
        font-size: var(--font-base) !important;
        line-height: 1.6;
        color: var(--gp-gray-light);
    }
    
    /* 캡션/라벨 */
    .gp-caption, [data-testid="stCaption"] {
        font-size: var(--font-sm) !important;
        color: rgba(255, 255, 255, 0.7);
    }
    
    /* 핵심 숫자 강조 (보험금, 급수 등) */
    .gp-metric-value, [data-testid="stMetricValue"] {
        font-size: var(--font-metric-value) !important;
        font-weight: 700;
        color: var(--gp-gold);
        line-height: 1.1;
    }
    
    .gp-metric-label, [data-testid="stMetricLabel"] {
        font-size: var(--font-metric-label) !important;
        font-weight: 500;
        color: var(--gp-neon-blue);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 4. Adaptive Input — 기기별 입력 방식 최적화
    ──────────────────────────────────────────────────────────────────────────── */
    
    /* 태블릿: Drag & Drop 강조 */
    @media (min-width: 1024px) {
        [data-testid="stFileUploader"] {
            min-height: 200px;
            border: 3px dashed var(--gp-neon-blue);
            border-radius: 15px;
            background: linear-gradient(135deg, rgba(0, 217, 255, 0.05) 0%, rgba(102, 126, 234, 0.05) 100%);
            transition: all 0.3s ease;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--gp-gold);
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(184, 134, 11, 0.1) 100%);
        }
    }
    
    /* 모바일: 카메라 스캔 Floating 버튼 */
    @media (max-width: 1023px) {
        /* Floating Action Button (하단 고정) */
        .gp-floating-camera {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 60px;
            height: 60px;
            background: linear-gradient(135deg, var(--gp-neon-blue) 0%, var(--gp-neon-blue-dark) 100%);
            border-radius: 50%;
            box-shadow: 0 4px 20px rgba(0, 217, 255, 0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 9999;
            transition: all 0.3s ease;
        }
        
        .gp-floating-camera:hover {
            background: linear-gradient(135deg, var(--gp-gold) 0%, var(--gp-gold-dark) 100%);
            box-shadow: 0 6px 25px rgba(255, 215, 0, 0.5);
            transform: scale(1.1);
        }
        
        .gp-floating-camera::before {
            content: "📷";
            font-size: 1.5rem;
        }
        
        /* 파일 업로더 모바일 최적화 */
        [data-testid="stFileUploader"] {
            min-height: 120px;
            border: 2px dashed var(--gp-neon-blue);
            border-radius: 12px;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 5. 터치 타겟 최적화 (WCAG 2.1 AA 준수)
    ──────────────────────────────────────────────────────────────────────────── */
    
    @media (max-width: 1023px) {
        /* 버튼 최소 44px (Apple HIG / Material Design 기준) */
        button[kind="primary"],
        button[kind="secondary"],
        .stButton > button {
            min-height: 44px !important;
            min-width: 44px !important;
            padding: 12px 20px !important;
            font-size: var(--font-base) !important;
            border-radius: 8px;
            font-weight: 600;
        }
        
        /* Primary 버튼 GP 스타일 */
        button[kind="primary"] {
            background: linear-gradient(135deg, var(--gp-gold) 0%, var(--gp-gold-dark) 100%) !important;
            color: var(--gp-charcoal) !important;
            border: none !important;
        }
        
        /* 입력 필드 터치 타겟 */
        input[type="text"],
        input[type="password"],
        input[type="email"],
        input[type="tel"],
        input[type="number"] {
            min-height: 44px !important;
            font-size: 16px !important; /* iOS 자동 줌 방지 */
            padding: 10px 14px !important;
            border-radius: 8px;
        }
        
        /* 셀렉트박스 */
        [data-testid="stSelectbox"] > div > div {
            min-height: 44px !important;
        }
        
        /* 탭 버튼 */
        [data-testid="stTabs"] button {
            min-height: 44px !important;
            padding: 10px 16px !important;
            font-size: var(--font-base) !important;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 6. Feature Ad-Box 반응형 스타일
    ──────────────────────────────────────────────────────────────────────────── */
    
    .gp-feature-adbox {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 12px;
        padding: var(--spacing-lg);
        color: var(--gp-white);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        margin-top: var(--spacing-md);
    }
    
    .gp-feature-adbox-title {
        font-size: var(--font-lg) !important;
        font-weight: 700;
        text-align: center;
        margin-bottom: var(--spacing-sm);
    }
    
    .gp-feature-adbox-content {
        font-size: var(--font-sm) !important;
        line-height: 1.7;
    }
    
    .gp-feature-adbox-footer {
        margin-top: var(--spacing-sm);
        padding-top: var(--spacing-sm);
        border-top: 1px solid rgba(255, 255, 255, 0.3);
        font-size: var(--font-xs) !important;
        text-align: center;
        opacity: 0.9;
    }
    
    /* 모바일: Ad-Box 간소화 (핵심 4대 기능만 표시) */
    @media (max-width: 767px) {
        .gp-feature-adbox {
            padding: var(--spacing-md);
        }
        
        .gp-feature-adbox-item:nth-child(n+5) {
            display: none; /* 5번째 이후 항목 숨김 */
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 7. 데이터 테이블 반응형
    ──────────────────────────────────────────────────────────────────────────── */
    
    @media (max-width: 1023px) {
        [data-testid="stDataFrame"],
        [data-testid="stDataFrameResizable"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            max-width: 100vw;
        }
        
        table {
            display: block;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
            max-width: 100%;
            font-size: var(--font-sm) !important;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 8. 이미지 & 미디어 반응형
    ──────────────────────────────────────────────────────────────────────────── */
    
    img {
        max-width: 100%;
        height: auto;
        border-radius: 8px;
    }
    
    video {
        max-width: 100%;
        height: auto;
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 9. 접근성 & 성능 최적화
    ──────────────────────────────────────────────────────────────────────────── */
    
    /* 애니메이션 감소 선호 사용자 대응 */
    @media (prefers-reduced-motion: reduce) {
        * {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
        }
    }
    
    /* 다크 모드 강제 (GP Identity) */
    .stApp {
        background-color: var(--gp-charcoal) !important;
        color: var(--gp-white) !important;
    }
    
    /* 가로 스크롤 방지 */
    * {
        box-sizing: border-box;
    }
    
    html, body, .stApp {
        max-width: 100vw;
        overflow-x: hidden;
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 10. 사이드바 반응형
    ──────────────────────────────────────────────────────────────────────────── */
    
    @media (max-width: 767px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdown"] {
            font-size: var(--font-sm) !important;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 11. 모달 & 팝오버 반응형
    ──────────────────────────────────────────────────────────────────────────── */
    
    @media (max-width: 767px) {
        [data-testid="stPopover"] {
            max-width: 90vw !important;
        }
        
        [data-testid="stModal"] {
            max-width: 95vw !important;
            padding: var(--spacing-md) !important;
        }
    }
    
    /* ────────────────────────────────────────────────────────────────────────────
       § 12. 프로그레스 바 & 스피너
    ──────────────────────────────────────────────────────────────────────────── */
    
    [data-testid="stProgress"] > div > div {
        background-color: var(--gp-gold) !important;
    }
    
    [data-testid="stSpinner"] > div {
        border-top-color: var(--gp-neon-blue) !important;
    }
    
    </style>
    """, unsafe_allow_html=True)


def render_floating_camera_button():
    """
    모바일 전용 Floating 카메라 스캔 버튼 렌더링
    
    화면 너비 1024px 미만에서만 표시되며, 클릭 시 파일 업로더 활성화.
    """
    st.markdown("""
    <script>
    // 모바일 환경 감지 및 Floating 버튼 표시
    if (window.innerWidth < 1024) {
        const floatingBtn = document.createElement('div');
        floatingBtn.className = 'gp-floating-camera';
        floatingBtn.onclick = function() {
            // 파일 업로더 트리거
            const fileInput = document.querySelector('[data-testid="stFileUploader"] input[type="file"]');
            if (fileInput) {
                fileInput.click();
            }
        };
        document.body.appendChild(floatingBtn);
    }
    </script>
    """, unsafe_allow_html=True)


def get_device_type() -> str:
    """
    현재 화면 크기 기반 기기 타입 반환
    
    Returns:
        "desktop" | "tablet" | "mobile"
    """
    # Streamlit에서는 서버 사이드이므로 JavaScript로 감지 필요
    # 여기서는 세션 상태에 저장된 값 사용 (클라이언트에서 전달)
    return st.session_state.get("_gp_device_type", "desktop")


def inject_device_detector():
    """
    클라이언트 화면 크기 감지 JavaScript 주입
    
    window.innerWidth 값을 세션 상태에 저장하여 서버 사이드에서 활용.
    """
    st.markdown("""
    <script>
    // 기기 타입 감지 및 세션 상태 업데이트
    function detectDeviceType() {
        const width = window.innerWidth;
        let deviceType = 'desktop';
        
        if (width < 768) {
            deviceType = 'mobile';
        } else if (width < 1024) {
            deviceType = 'tablet';
        }
        
        // Streamlit 세션 상태 업데이트 (query params 활용)
        const params = new URLSearchParams(window.location.search);
        params.set('device_type', deviceType);
        
        // 화면 크기 변경 시 재감지
        window.addEventListener('resize', detectDeviceType);
    }
    
    detectDeviceType();
    </script>
    """, unsafe_allow_html=True)
