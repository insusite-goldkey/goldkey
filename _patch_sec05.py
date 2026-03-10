with open('app.py', encoding='utf-8-sig') as f:
    content = f.read()

# ── 교체 대상: GK-SEC-05 섹션 헤더~F섹션 버튼 닫기까지 ──────────────────
old = '''        _pf_c1, _pf_c2, _pf_c3 = st.columns(3, gap="medium")
        with _pf_c1:
            st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#004d40,#00695c);
  border:2px solid rgba(0,200,170,0.55);box-shadow:0 8px 32px rgba(0,77,64,0.35);position:relative;">
  {_bid('1-5-1')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">A SECTION</div>
  <div class="gk-pf-title">🔬 Smart Analysis &amp; Hub</div>
  <div class="gk-pf-sub">증권분석 · 약관검색 · 스캔허브<br>리플렛 · 고객자료 · 디지털카탈로그</div>
  <span class="gk-pf-count">📦 7개 핵심 서비스</span>
</div>""", unsafe_allow_html=True)
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🔬 A섹션 — Smart Analysis", key="ag_a_enter", use_container_width=True):
                _go_tab("policy_scan")
            st.markdown('</div>', unsafe_allow_html=True)
        with _pf_c2:
            st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#00695c,#00897b);
  border:2px solid rgba(0,200,170,0.55);box-shadow:0 8px 32px rgba(0,105,92,0.35);position:relative;">
  {_bid('1-5-2')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">B SECTION</div>
  <div class="gk-pf-title">🛡️ Expert Consulting</div>
  <div class="gk-pf-sub">신규/보험금 상담 · 장해 · 자동차사고<br>암·뇌·심장 · LIFE CYCLE</div>
  <span class="gk-pf-count">📦 11개 핵심 서비스</span>
</div>""", unsafe_allow_html=True)
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🛡️ B섹션 — Expert Consulting", key="ag_b_enter", use_container_width=True):
                _go_tab("t0")
            st.markdown('</div>', unsafe_allow_html=True)
        with _pf_c3:
            st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#00695c,#26a69a);
  border:2px solid rgba(0,200,170,0.55);box-shadow:0 8px 32px rgba(0,105,92,0.35);position:relative;">
  {_bid('1-5-3')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">C SECTION</div>
  <div class="gk-pf-title">💼 Wealth &amp; Corporate</div>
  <div class="gk-pf-sub">노후·연금·상속 · 세무 · 법인<br>CEO · 비상장주식 · 화재·배상</div>
  <span class="gk-pf-count">📦 7개 핵심 서비스</span>
</div>""", unsafe_allow_html=True)
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("💼 C섹션 — Wealth & Corporate", key="ag_c_enter", use_container_width=True):
                _go_tab("t5")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _pf_d1, _pf_d2 = st.columns(2, gap="medium")
        with _pf_d1:
            st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#004d40,#00796b);
  border:2px solid rgba(0,200,170,0.55);box-shadow:0 8px 32px rgba(0,77,64,0.35);position:relative;">
  {_bid('1-5-4')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">D SECTION</div>
  <div class="gk-pf-title">🌸 Life &amp; Care</div>
  <div class="gk-pf-sub">LIFE EVENT · 맞춤 보험 상담<br>부동산 투자 · 간병비 · 의학경제학적 컨설팅</div>
  <span class="gk-pf-count">📦 4개 핵심 서비스</span>
</div>""", unsafe_allow_html=True)
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🌸 D섹션 — Life & Care", key="ag_d_enter", use_container_width=True):
                _go_tab("life_event")
            st.markdown('</div>', unsafe_allow_html=True)
        with _pf_d2:
            st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#00695c,#009688);
  border:2px solid rgba(0,200,170,0.55);box-shadow:0 8px 32px rgba(0,105,92,0.35);position:relative;">
  {_bid('1-5-5')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">E SECTION</div>
  <div class="gk-pf-title">🔍 보상 시뮬레이션</div>
  <div class="gk-pf-sub">교통사고·산재·일반상해 보상 정보<br>KCD-8 매핑 · 전문가 지원 센터</div>
  <span class="gk-pf-count">📦 통합 시뮬레이션 가이드</span>
</div>""", unsafe_allow_html=True)
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🔍 E섹션 — 보상 시뮬레이션", key="ag_e_enter", use_container_width=True):
                _go_tab("kcd_injury")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(f"""<div class="gk-pf-card" style="background:linear-gradient(145deg,#004d40,#00695c);
  border:2px solid rgba(0,230,180,0.60);box-shadow:0 8px 32px rgba(0,77,64,0.45);position:relative;">
  {_bid('1-5-6')}
  <div style="font-size:0.9rem;font-weight:700;color:#fff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:4px;">F SECTION · 가이딩 프로토콜 제6편 준수</div>
  <div class="gk-pf-title">🤖 보험봇 · InsuBot</div>
  <div class="gk-pf-sub">가이딩 프로토콜 제22조 승인 출처 기반 AI 답변<br>제23조 금지 출처 차단 · 제24조 2차 검증 · 제25조 Red Alert</div>
  <span class="gk-pf-count">📋 보험 용어 · 판례 · 사례 검색</span>
</div>""", unsafe_allow_html=True)
        st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
        if st.button("🤖 F섹션 — 보험봇 · InsuBot", key="ag_f_enter", use_container_width=True):
            _go_tab("ins_bot")
        st.markdown('</div>', unsafe_allow_html=True)'''

new = '''        # ── A~C 섹션: 3열 ──────────────────────────────────────────────────
        _pf_c1, _pf_c2, _pf_c3 = st.columns(3, gap="medium")
        with _pf_c1:
            st.markdown(f"""<div style="background:#E3F2FD;border:1.5px solid #90CAF9;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;min-height:170px;">
  {_bid('1-5-1')}
  <div style="font-size:0.78rem;font-weight:900;color:#1565C0;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### A-SECTION: Smart Analysis &amp; Hub</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>보험증권 분석</li>
    <li>약관 매칭 검색</li>
    <li>통합 스캔 허브</li>
    <li>리플렛 분류</li>
    <li>고객자료 저장함</li>
    <li>디지털 카탈로그</li>
    <li>AI 자동 리포트</li>
  </ol>
</div>""", unsafe_allow_html=True)
            if st.button("🔬 A섹션 입장 → 보험증권 분석", key="ag_a_enter", use_container_width=True):
                _go_tab("policy_scan")
        with _pf_c2:
            st.markdown(f"""<div style="background:#F3E5F5;border:1.5px solid #CE93D8;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;min-height:170px;">
  {_bid('1-5-2')}
  <div style="font-size:0.78rem;font-weight:900;color:#6A1B9A;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### B-SECTION: Expert Consulting</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>신규보험 상담</li>
    <li>보험금 청구 상담</li>
    <li>장해 산출</li>
    <li>상해 통합 관리</li>
    <li>자동차사고 상담</li>
    <li>KCD 상해 분석</li>
    <li>암·뇌·심장 질환 상담</li>
    <li>기본·통합보험 설계</li>
    <li>자동차보험 보상 실무</li>
    <li>LIFE CYCLE 설계</li>
    <li>LIFE EVENT 상담</li>
  </ol>
</div>""", unsafe_allow_html=True)
            if st.button("🛡️ B섹션 입장 → 신규보험 상담", key="ag_b_enter", use_container_width=True):
                _go_tab("t0")
        with _pf_c3:
            st.markdown(f"""<div style="background:#FFF9C4;border:1.5px solid #F9A825;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;min-height:170px;">
  {_bid('1-5-3')}
  <div style="font-size:0.78rem;font-weight:900;color:#E65100;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### C-SECTION: Wealth &amp; Corporate</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>노후·상속 설계</li>
    <li>세무 상담</li>
    <li>법인 상담</li>
    <li>CEO 플랜</li>
    <li>비상장주식 평가</li>
    <li>화재보험</li>
    <li>배상책임보험</li>
  </ol>
</div>""", unsafe_allow_html=True)
            if st.button("💼 C섹션 입장 → 노후·상속 설계", key="ag_c_enter", use_container_width=True):
                _go_tab("t5")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── D~E 섹션: 2열 ──────────────────────────────────────────────────
        _pf_d1, _pf_d2 = st.columns(2, gap="medium")
        with _pf_d1:
            st.markdown(f"""<div style="background:#FCE4EC;border:1.5px solid #F48FB1;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;">
  {_bid('1-5-4')}
  <div style="font-size:0.78rem;font-weight:900;color:#880E4F;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### D-SECTION: Life &amp; Care</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>LIFE EVENT 상담</li>
    <li>간병비 컨설팅</li>
    <li>부동산 투자</li>
    <li>의학경제학적 보장 컨설팅</li>
  </ol>
</div>""", unsafe_allow_html=True)
            if st.button("🌸 D섹션 입장 → LIFE EVENT 상담", key="ag_d_enter", use_container_width=True):
                _go_tab("life_event")
        with _pf_d2:
            st.markdown(f"""<div style="background:#E8F5E9;border:1.5px solid #A5D6A7;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;">
  {_bid('1-5-5')}
  <div style="font-size:0.78rem;font-weight:900;color:#1B5E20;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### E-SECTION: 보상 시뮬레이션</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>보상 정보 시뮬레이션 가이드</li>
    <li>교통사고 보상 가이드</li>
    <li>산재 보상 가이드</li>
    <li>일반상해 보상 가이드</li>
    <li>KCD 상해 분석</li>
  </ol>
</div>""", unsafe_allow_html=True)
            if st.button("🔍 E섹션 입장 → 보상 시뮬레이션", key="ag_e_enter", use_container_width=True):
                _go_tab("kcd_injury")

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # ── F 섹션: 풀 와이드 ───────────────────────────────────────────────
        st.markdown(f"""<div style="background:#FFF3E0;border:1.5px solid #FFCC80;
  border-radius:12px;padding:14px 14px 10px 14px;position:relative;">
  {_bid('1-5-6')}
  <div style="font-size:0.78rem;font-weight:900;color:#BF360C;letter-spacing:0.08em;
    text-transform:uppercase;margin-bottom:6px;">### F-SECTION: 보험봇 · InsuBot (가이딩 프로토콜 제6편 준수)</div>
  <ol style="font-size:0.79rem;color:#000;font-weight:700;margin:0 0 8px 16px;padding:0;line-height:1.8;">
    <li>보험 전문용어 검색 (InsuBot)</li>
    <li>가이딩 프로토콜 제22조 — 승인 출처 기반 AI 답변</li>
    <li>제23조 금지 출처 자동 차단</li>
    <li>제24조 2차 검증 · 제25조 Red Alert 시스템</li>
    <li>보험 판례 · 사례 검색</li>
  </ol>
</div>""", unsafe_allow_html=True)
        if st.button("🤖 F섹션 입장 → 보험봇 · InsuBot", key="ag_f_enter", use_container_width=True):
            _go_tab("ins_bot")'''

if old in content:
    content = content.replace(old, new, 1)
    print("SEC-05 PATCH OK")
else:
    print("SEC-05 NOT FOUND")
    # 디버그: 첫 100자 확인
    idx = content.find("_pf_c1, _pf_c2, _pf_c3 = st.columns(3, gap=\"medium\")")
    print(f"  columns line idx: {idx}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("SAVED")
