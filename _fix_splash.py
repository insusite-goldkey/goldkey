with open('app.py', encoding='utf-8') as f:
    content = f.read()

# 비로그인 시 메인 영역: 기존 "삼선메뉴 터치" 안내 + st.stop() 전체를 스플래시 화면으로 교체
OLD = '''    if not _is_logged_in:
        st.markdown("""
<style>
.gk-login-guide {
  max-width: 460px; margin: 60px auto 0 auto;
  margin-left: max(320px, 22vw);
  background: #FFFDE7;
  border: 2.5px solid #E53935; border-radius: 20px;
  padding: 36px 28px 32px 28px; text-align: center;
  box-shadow: 0 8px 32px rgba(229,57,53,0.14);
}
.gk-login-guide .gk-lg-title {
  font-size: 1.6rem; font-weight: 900; color: #000000;
  margin-bottom: 14px; letter-spacing: -0.01em;
}
.gk-login-guide .gk-lg-sub {
  font-size: 1.05rem; font-weight: 700; color: #212121;
  margin-bottom: 0; line-height: 1.85;
}
.gk-login-guide .gk-lg-kw {
  color: #FF0000; font-weight: 900;
}
.gk-login-guide .gk-lg-arrow {
  font-size: 5rem; color: #E53935; margin-top: 16px; margin-bottom: 0;
  animation: gk-bounce 1.2s infinite;
  display: block;
}
@keyframes gk-bounce {
  0%,100%{transform:translateX(-8px)} 50%{transform:translateX(4px)}
}
</style>
<div class="gk-login-guide">
  <div class="gk-lg-title">🏆 Goldkey AI 마스터</div>
  <div class="gk-lg-sub">
    👉 화면 <span class="gk-lg-kw">왼쪽상단 삼선메뉴(☰)</span>를 터치하세요.<br>
    <span class="gk-lg-kw">로그인/회원가입</span>을 바로 진행할 수 있습니다.
  </div>
  <span class="gk-lg-arrow">👈</span>
</div>""", unsafe_allow_html=True)
        st.stop()'''

NEW = '''    if not _is_logged_in:
        # ── [제49조 §스플래시] 비로그인 시 메인 영역 = 스플래시 화면 ──────────
        # 사이드바(로그인 폼)와 스플래시가 동시 노출 → 로그인 시 자동 전환
        _splash_av = get_goldkey_avatar()
        _splash_av_html = (
            f\'<img src="{_splash_av}" width="130" height="130" loading="eager"\' +
            \' style="border-radius:50%;border:4px solid #D4AF37;\' +
            \'box-shadow:0 4px 24px rgba(212,175,55,0.35);object-fit:cover;\' +
            \'display:block;margin:0 auto 22px auto;" />\' if _splash_av else
            \'<div style="width:130px;height:130px;border-radius:50%;\' +
            \'background:linear-gradient(135deg,#4facfe,#00f2fe);\' +
            \'margin:0 auto 22px auto;box-shadow:0 4px 24px rgba(79,172,254,0.4);"></div>\'
        )
        st.markdown(f"""
<style>
.gk-splash-wrap {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 70vh;
    padding: 40px 20px;
}}
.gk-splash-card {{
    background: linear-gradient(160deg, #0a1628 0%, #1a3a5c 60%, #0d2344 100%);
    border-radius: 24px;
    padding: 48px 40px 40px 40px;
    text-align: center;
    max-width: 480px;
    width: 100%;
    box-shadow: 0 12px 48px rgba(10,22,40,0.32);
    border: 1.5px solid rgba(212,175,55,0.35);
}}
.gk-splash-title {{
    font-size: 1.9rem;
    font-weight: 900;
    color: #D4AF37;
    letter-spacing: 0.02em;
    margin-bottom: 8px;
    line-height: 1.2;
}}
.gk-splash-sub {{
    font-size: 1.0rem;
    font-weight: 600;
    color: #b0cce8;
    margin-bottom: 20px;
    line-height: 1.6;
}}
.gk-splash-divider {{
    border: none;
    border-top: 1px solid rgba(212,175,55,0.25);
    margin: 20px 0;
}}
.gk-splash-guide {{
    font-size: 0.95rem;
    font-weight: 700;
    color: #FFD700;
    background: rgba(212,175,55,0.12);
    border: 1.5px solid rgba(212,175,55,0.3);
    border-radius: 12px;
    padding: 14px 18px;
    line-height: 1.8;
    margin-top: 4px;
}}
.gk-splash-arrow {{
    font-size: 2.8rem;
    display: block;
    margin-top: 18px;
    animation: gk-arrow-bounce 1.1s infinite;
}}
@keyframes gk-arrow-bounce {{
    0%,100%{{transform:translateX(-10px);opacity:0.7}}
    50%{{transform:translateX(6px);opacity:1}}
}}
</style>
<div class="gk-splash-wrap">
  <div class="gk-splash-card">
    {_splash_av_html}
    <div class="gk-splash-title">Goldkey AI Masters 2026</div>
    <div class="gk-splash-sub">초개인화 AI 기반 전문 보장 상담 시스템</div>
    <hr class="gk-splash-divider"/>
    <div class="gk-splash-guide">
      🔐 <b>왼쪽 사이드바</b>에서<br>
      <b style="color:#FFD700;">로그인 / 회원가입</b>을 진행하세요
      <span class="gk-splash-arrow">👈</span>
    </div>
  </div>
</div>""", unsafe_allow_html=True)
        st.stop()'''

assert OLD in content, "교체 대상 코드를 찾을 수 없습니다"
content = content.replace(OLD, NEW, 1)
print("스플래시 화면 교체 완료")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SAVED OK")
