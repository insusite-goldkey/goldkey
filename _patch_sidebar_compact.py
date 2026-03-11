with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# H1: 사이드바 전역 반응형 CSS — 박스 모델 + fluid width + overflow 제어
# 위치: L23041 세션당 1회 주입 CSS 블록 교체
# ══════════════════════════════════════════════════════════════════════════════
OLD_SIDEBAR_SCROLL_CSS = '''<style>
section[data-testid="stSidebar"] > div:first-child {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-bottom: 40px !important;
    overscroll-behavior-y: auto !important;
    scroll-behavior: auto !important;
    -webkit-overflow-scrolling: touch !important;
}
section[data-testid="stSidebar"] {
    overscroll-behavior: auto !important;
}
</style>'''

NEW_SIDEBAR_SCROLL_CSS = '''<style>
/* ── [SIDEBAR RESPONSIVE §1] 전역 박스 모델 + 반응형 레이아웃 ── */
section[data-testid="stSidebar"] > div:first-child {
    overflow-y: auto !important;
    overflow-x: hidden !important;
    padding-bottom: 40px !important;
    overscroll-behavior-y: auto !important;
    scroll-behavior: auto !important;
    -webkit-overflow-scrolling: touch !important;
}
section[data-testid="stSidebar"] {
    overscroll-behavior: auto !important;
}
/* ── [SIDEBAR RESPONSIVE §2] 사이드바 내 모든 커스텀 블록 fluid width ── */
[data-testid="stSidebarUserContent"] *,
section[data-testid="stSidebar"] * {
    box-sizing: border-box !important;
}
[data-testid="stSidebarUserContent"] div[style],
section[data-testid="stSidebar"] div[style] {
    max-width: 100% !important;
    overflow-x: hidden !important;
    word-break: break-all;
    white-space: normal;
}
/* ── [SIDEBAR RESPONSIVE §3] 텍스트 크기 최적화 ── */
[data-testid="stSidebarUserContent"] .gk-sidebar-menu-text {
    font-size: 0.85rem !important;
}
[data-testid="stSidebarUserContent"] .gk-sidebar-security-text {
    font-size: 0.75rem !important;
}
/* ── [SIDEBAR RESPONSIVE §4] 버튼 패딩 슬림화 ── */
section[data-testid="stSidebar"] div[data-testid="stTabs"] button[data-baseweb="tab"] {
    padding: 4px 8px !important;
}
section[data-testid="stSidebar"] .stButton button {
    padding: 4px 8px !important;
    font-size: 0.85rem !important;
}
</style>'''

if OLD_SIDEBAR_SCROLL_CSS in content:
    content = content.replace(OLD_SIDEBAR_SCROLL_CSS, NEW_SIDEBAR_SCROLL_CSS, 1)
    print("H1: 사이드바 전역 반응형 CSS 교체 OK")
else:
    print("WARNING H1: 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H2: 탭 CSS — 탭 폰트크기 0.85rem + 패딩 4px 8px 슬림화
# ══════════════════════════════════════════════════════════════════════════════
OLD_TAB_CSS = '''section[data-testid="stSidebar"] div[data-testid="stTabs"] button[data-baseweb="tab"] {
  border: 1.5px solid #000000 !important;
  border-radius: 8px !important;
  margin: 0 !important;
  font-weight: 700 !important;
  color: #000000 !important;
  font-size: 0.82rem !important;
  padding: 6px 4px !important;
  text-align: center !important;
  justify-content: center !important;
}'''

NEW_TAB_CSS = '''section[data-testid="stSidebar"] div[data-testid="stTabs"] button[data-baseweb="tab"] {
  border: 1.5px solid #000000 !important;
  border-radius: 8px !important;
  margin: 0 !important;
  font-weight: 700 !important;
  color: #000000 !important;
  font-size: 0.85rem !important;
  padding: 4px 8px !important;
  text-align: center !important;
  justify-content: center !important;
  white-space: normal !important;
  word-break: keep-all !important;
  line-height: 1.3 !important;
}'''

if OLD_TAB_CSS in content:
    content = content.replace(OLD_TAB_CSS, NEW_TAB_CSS, 1)
    print("H2: 탭 CSS 슬림화 OK")
else:
    print("WARNING H2: 탭 CSS 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H3-A: 트리플 보안 박스 — 패딩 축소 + width:100% + word-break 강화
# ══════════════════════════════════════════════════════════════════════════════
OLD_TRIPLE_BOX = '''    <div style='background:#FFFFFF;border-radius:12px;
      padding:10px 16px 10px 20px;margin-top:12px;margin-bottom:14px;text-align:center;
      border:1px solid #004D40;
      border-left:4px solid #D4AF37;
      box-shadow:0 2px 6px rgba(0,77,64,0.10);
      position:relative;box-sizing:border-box;'>
      <div style='color:#004D40;font-size:0.8rem;font-weight:700;letter-spacing:0.08em;'>🛡️ 가문 안보를 위한 트리플 보안 가동 중</div>
    </div>'''

NEW_TRIPLE_BOX = '''    <div style='background:#FFFFFF;border-radius:10px;
      padding:6px 10px 6px 12px;margin-top:6px;margin-bottom:8px;text-align:center;
      border:1px dashed #004D40;
      border-left:3px solid #D4AF37;
      box-shadow:0 1px 4px rgba(0,77,64,0.08);
      position:relative;box-sizing:border-box;
      width:100%;max-width:100%;overflow:hidden;'>
      <div style='color:#004D40;font-size:0.75rem;font-weight:700;letter-spacing:0.04em;
        word-break:keep-all;white-space:normal;line-height:1.4;'>🛡️ 가문 안보를 위한 트리플 보안 가동 중</div>
    </div>'''

if OLD_TRIPLE_BOX in content:
    content = content.replace(OLD_TRIPLE_BOX, NEW_TRIPLE_BOX, 1)
    print("H3-A: 트리플 보안 박스 슬림화 OK")
else:
    print("WARNING H3-A: 트리플 보안 박스 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H3-B: 로그인 블루 박스 — 패딩·마진 축소 + width:100%
# ══════════════════════════════════════════════════════════════════════════════
OLD_LOGIN_BLUE_BOX = '''    <div style='background:#E3F2FD;border-radius:15px;
      padding:18px 20px;margin-bottom:24px;text-align:center;
      border:1.5px solid #90CAF9;
      box-shadow:0 2px 12px rgba(33,150,243,0.12);
      position:relative;box-sizing:border-box;'>
      <div style='font-size:2rem;margin-bottom:6px;'>🛡️</div>
      <div style='color:#000000;font-size:1.05rem;font-weight:800;'>goldkey_Ai_masters2026 보안 로그인</div>
      <div style='color:#000000;font-size:0.78rem;margin-top:4px;opacity:0.72;'>가입 시 등록한 정보로 본인 확인 후 OTP를 발급합니다</div>
    </div>'''

NEW_LOGIN_BLUE_BOX = '''    <div style='background:#E3F2FD;border-radius:12px;
      padding:10px 12px 8px 12px;margin-bottom:10px;text-align:center;
      border:1px solid #90CAF9;
      box-shadow:0 1px 6px rgba(33,150,243,0.10);
      position:relative;box-sizing:border-box;
      width:100%;max-width:100%;overflow:hidden;'>
      <div style='font-size:1.5rem;margin-bottom:3px;'>🛡️</div>
      <div style='color:#000000;font-size:0.92rem;font-weight:800;'>goldkey_Ai_masters2026 보안 로그인</div>
      <div style='color:#000000;font-size:0.72rem;margin-top:2px;opacity:0.72;
        word-break:keep-all;white-space:normal;'>가입 시 등록한 정보로 본인 확인 후 OTP를 발급합니다</div>
    </div>'''

if OLD_LOGIN_BLUE_BOX in content:
    content = content.replace(OLD_LOGIN_BLUE_BOX, NEW_LOGIN_BLUE_BOX, 1)
    print("H3-B: 로그인 블루 박스 슬림화 OK")
else:
    print("WARNING H3-B: 로그인 블루 박스 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H2-B: 로그인 후 프로필 박스 — 패딩·마진 축소
# ══════════════════════════════════════════════════════════════════════════════
OLD_PROFILE_BOX = '''<div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);
  border-radius:15px;padding:16px 14px 12px 14px;margin-bottom:10px;
  box-shadow:0 4px 20px rgba(79,172,254,0.28);text-align:center;">'''

NEW_PROFILE_BOX = '''<div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);
  border-radius:12px;padding:10px 10px 8px 10px;margin-bottom:6px;
  box-shadow:0 2px 10px rgba(79,172,254,0.20);text-align:center;
  width:100%;max-width:100%;box-sizing:border-box;overflow:hidden;">'''

if OLD_PROFILE_BOX in content:
    content = content.replace(OLD_PROFILE_BOX, NEW_PROFILE_BOX, 1)
    print("H2-B: 프로필 박스 슬림화 OK")
else:
    print("WARNING H2-B: 프로필 박스 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H2-C: 전문가 브랜딩 박스 — 패딩·마진 축소
# ══════════════════════════════════════════════════════════════════════════════
OLD_BRAND_BOX = '''<div style='background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);
  border-radius:12px;padding:12px 14px 10px 14px;margin:8px 0 6px 0;
  border:1.5px solid #D4AF37;box-shadow:0 2px 8px rgba(10,22,40,0.18);'>'''

NEW_BRAND_BOX = '''<div style='background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);
  border-radius:10px;padding:8px 10px 6px 10px;margin:4px 0 4px 0;
  border:1px solid #D4AF37;box-shadow:0 1px 5px rgba(10,22,40,0.15);
  width:100%;max-width:100%;box-sizing:border-box;overflow:hidden;'>'''

if OLD_BRAND_BOX in content:
    content = content.replace(OLD_BRAND_BOX, NEW_BRAND_BOX, 1)
    print("H2-C: 브랜딩 박스 슬림화 OK")
else:
    print("WARNING H2-C: 브랜딩 박스 앵커 미발견")

# ══════════════════════════════════════════════════════════════════════════════
# H2-D: 임시/비회원 접속 텍스트 폰트 크기 + 여백 조정
# ══════════════════════════════════════════════════════════════════════════════
OLD_GUEST_TEXT = '''                        st.markdown(
                            "<div style='font-size:0.85rem;font-weight:900;color:#000000;"
                            "text-align:center;margin-bottom:6px;'>"
                            "👁️ 임시/비회원 빠른 접속</div>"
                            "<div style='font-size:0.72rem;color:#555555;text-align:center;"
                            "margin-bottom:8px;'>1일 1회 / 누적 최대 10회 이용 가능</div>",
                            unsafe_allow_html=True
                        )'''

NEW_GUEST_TEXT = '''                        st.markdown(
                            "<div style='font-size:0.85rem;font-weight:900;color:#000000;"
                            "text-align:center;margin-bottom:3px;word-break:keep-all;'>"
                            "👁️ 임시/비회원 빠른 접속</div>"
                            "<div style='font-size:0.72rem;color:#555555;text-align:center;"
                            "margin-bottom:4px;'>1일 1회 / 누적 최대 10회 이용 가능</div>",
                            unsafe_allow_html=True
                        )'''

if OLD_GUEST_TEXT in content:
    content = content.replace(OLD_GUEST_TEXT, NEW_GUEST_TEXT, 1)
    print("H2-D: 임시/비회원 텍스트 슬림화 OK")
else:
    print("WARNING H2-D: 임시/비회원 텍스트 앵커 미발견")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\nDONE: sidebar compact patch applied")
