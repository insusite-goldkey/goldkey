"""
[ID-000-NAV] 사이드바 구조 근본 수정 v2

문제:
  with st.sidebar: (line 28685) 가 if not _is_auth_now: 블록 안에 있어
  로그인 후엔 사이드바가 전혀 렌더되지 않음.

해결:
  1) if not _is_auth_now: 블록 내부의 with st.sidebar: 블록을 제거
  2) _is_auth_now 조건 바로 앞에 항상-실행 with st.sidebar: 블록 삽입
     - 비로그인: 기존 비로그인 사이드바 콘텐츠 렌더
     - 로그인: _s39_render_landing_page() 내 로그인 후 사이드바 콘텐츠 직접 호출
  3) _s39_render_landing_page() 내 중복 with st.sidebar: 는 유지 (함수 내부 렌더용)

실제 구조 (0-indexed):
  line 28474 (idx 28473): if not _is_auth_now:
  line 28681 (idx 28680): 사이드바 주석
  line 28684 (idx 28683): _is_authenticated = ...
  line 28685 (idx 28684): with st.sidebar:   ← 비로그인 사이드바
  line 30628 (idx 30627): st.stop()          ← 비로그인 분기 끝
  line 30630+: 로그인 후 메인 앱 로직 시작
"""

with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    lines = f.readlines()

print(f"총 줄 수: {len(lines)}")

# ─────────────────────────────────────────────────────────────────────────────
# 핵심 수정:
# _is_auth_now 정의(line 28472) 바로 다음, if not _is_auth_now: (line 28475) 바로 앞에
# 항상-실행 with st.sidebar: 블록을 삽입.
#
# 삽입 위치: line 28474 (0-indexed 28473) = cur = st.session_state... 다음 빈줄
# 즉, 0-indexed 28474 (line 28475 = "    if not _is_auth_now:") 바로 앞
# ─────────────────────────────────────────────────────────────────────────────

INSERT_BEFORE = 28474  # 0-indexed: line 28475 "    if not _is_auth_now:"

# 검증
print(f"삽입 위치 앞: {repr(lines[INSERT_BEFORE-1][:60])}")
print(f"삽입 위치 (현재): {repr(lines[INSERT_BEFORE][:60])}")

# 새로 삽입할 사이드바 블록
SIDEBAR_NAV_BLOCK = '''\
    # ── [ID-000-NAV] 항상-실행 사이드바 — 인증 상태와 무관하게 항상 렌더 ──────────
    # 구글 제안 반영: with st.sidebar 조건문 밖으로 이동
    # 비로그인: 브랜드 아바타 + 로그인폼 + 약관
    # 로그인:   브랜드 아바타 + 브랜딩 정보 + 앱공지 + 관리자메뉴
    _is_authenticated_nav = bool(
        st.session_state.get("authenticated", False) or
        st.session_state.get("user_id", "")
    )
    with st.sidebar:
        # ── (0) 브랜드 아바타 — 항상 표시 ──────────────────────────────────
        render_goldkey_sidebar()
        if not _is_authenticated_nav:
            # ── (비로그인) 사이드바 강제 열기 JS ───────────────────────────
            import streamlit.components.v1 as _nav_comp
            _nav_comp.html("""<script>
(function(){
  function tryOpen(){
    try{
      var pd=window.parent.document;
      var sb=pd.querySelector('section[data-testid="stSidebar"]');
      if(sb && sb.getAttribute('aria-expanded')==='false'){
        var sels=['[data-testid="collapsedControl"] button',
          '[data-testid="stSidebarCollapseButton"] button',
          'button[aria-label="Open sidebar"]',
          'button[aria-label="사이드바를 열거나 닫으세요"]'];
        for(var i=0;i<sels.length;i++){
          var b=pd.querySelector(sels[i]);
          if(b){b.click();return;}
        }
      }
    }catch(e){}
  }
  setTimeout(tryOpen,200); setTimeout(tryOpen,700); setTimeout(tryOpen,1500);
})();
</script>""", height=0)
        else:
            # ── (로그인 후) 사이드바 열기 JS (_open_sidebar 플래그 소비) ───
            if st.session_state.pop("_open_sidebar", False):
                import streamlit.components.v1 as _nav_comp2
                _nav_comp2.html("""<script>
(function(){
  function tryOpen(){
    try{
      var pd=window.parent.document;
      var sb=pd.querySelector('section[data-testid="stSidebar"]');
      if(!sb||sb.getAttribute('aria-expanded')==='false'){
        var sels=['[data-testid="collapsedControl"] button',
          '[data-testid="stSidebarCollapseButton"] button',
          'button[aria-label="Open sidebar"]'];
        for(var i=0;i<sels.length;i++){
          var b=pd.querySelector(sels[i]);
          if(b){b.click();return;}
        }
      }
    }catch(e){}
  }
  setTimeout(tryOpen,150); setTimeout(tryOpen,500); setTimeout(tryOpen,1200);
})();
</script>""", height=0)
            # ── 로그인 후 사이드바 콘텐츠 ─────────────────────────────────
            _post_uname = st.session_state.get("user_name","") or st.session_state.get("user_id","마스터")
            st.markdown(f"""
<div style="background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%);
  border-radius:12px;padding:10px 10px 8px 10px;margin-bottom:6px;
  text-align:center;">
  <div style="font-size:1.0rem;font-weight:800;color:#0a1628;">Goldkey_AI_Masters2026</div>
  <div style="font-size:0.78rem;font-weight:600;color:#0d2344;">👤 {_post_uname} 마스터</div>
  <div style="font-size:0.70rem;color:#1a3a5c;">전문 보장 상담의 동반자</div>
</div>""", unsafe_allow_html=True)
            # 브랜딩 정보 입력
            st.markdown("""
<div style='background:linear-gradient(135deg,#0a1628 0%,#1a3a5c 100%);
  border-radius:10px;padding:8px 10px 6px 10px;margin:4px 0 4px 0;
  border:1px solid #D4AF37;'>
  <div style='font-size:0.82rem;font-weight:900;color:#D4AF37;margin-bottom:5px;'>
🏅 전문가 브랜딩 설정 (선택)
  </div>
  <div style='font-size:0.74rem;color:#b0cce8;line-height:1.55;'>
소속과 연락처를 입력하면 출력물에 자동 반영됩니다
  </div>
</div>""", unsafe_allow_html=True)
            _nav_co = st.text_input("🏢 회사명", value=st.session_state.get("gp200_company",""),
                                    placeholder="예: 골드키지사, 삼성생명...", key="_nav_co_raw", max_chars=60)
            if _nav_co != st.session_state.get("gp200_company",""):
                st.session_state["gp200_company"] = _nav_co
            _nav_br = st.text_input("🏬 지점/팀명", value=st.session_state.get("gp200_branch",""),
                                    placeholder="예: 강남지점", key="_nav_br_raw", max_chars=40)
            if _nav_br != st.session_state.get("gp200_branch",""):
                st.session_state["gp200_branch"] = _nav_br
            _nav_nm = st.text_input("👤 성명", value=st.session_state.get("gp200_name",""),
                                    placeholder="예: 홍길동", key="_nav_nm_raw", max_chars=30)
            if _nav_nm != st.session_state.get("gp200_name",""):
                st.session_state["gp200_name"] = _nav_nm
            _nav_ct = st.text_input("📞 연락처", value=st.session_state.get("gp200_contact",""),
                                    placeholder="예: 010-1234-5678", key="_nav_ct_raw", max_chars=20)
            if _nav_ct != st.session_state.get("gp200_contact",""):
                st.session_state["gp200_contact"] = _nav_ct
            st.markdown("---")
            # 앱 공지
            with st.expander("📢 앱 공지 · 업데이트 안내", expanded=False):
                st.markdown("""
**[2026.03 업데이트]**
- GP88 통합 상담 허브 v2 배포
- 자가복구 엔진 전역 스코프 복구
- 이용약관 전문 상시 노출 전환
- 사이드바 항상-렌더 구조 개선

**[서비스 문의]**
- insusite@gmail.com
- 010-3074-2616
""")
            # 관리자·계정 관리
            _nav_is_admin = st.session_state.get("is_admin", False)
            with st.expander("⚙️ 관리자 · 계정 관리", expanded=False):
                if _nav_is_admin:
                    st.success("✅ 관리자 권한으로 로그인됨")
                    st.caption("메인 화면 → 관리자 탭에서 회원/지시/헬스체크 관리")
                else:
                    st.info("👤 일반 회원으로 로그인됨")
                    st.caption("이름/연락처 변경: 메인 화면 → 내 정보 탭")

'''

# 기존 비로그인 사이드바 블록(28682~28685+내용) 을 제거할 필요 없이
# 단순히 앞에 삽입하면 Streamlit은 with st.sidebar: 가 여러 번 호출되어도
# 동일 사이드바에 콘텐츠를 누적함 → 중복 렌더 발생
# 따라서 기존 with st.sidebar: 블록(28681~30337 범위) 을 제거하고 새 블록만 사용

# ─────────────────────────────────────────────────────────────────────────────
# 제거할 범위:
#   (A) 비로그인 사이드바 주석+변수+블록: line 28682~28685 시작 부분
#       → 실제로는 with st.sidebar: 전체를 제거하면 너무 크고 위험
#       → 대신: if not _is_authenticated: 내부 열기JS + render_goldkey_sidebar() 만 남기고
#              login_form 부분은 그대로 유지 (단, with st.sidebar 없이)
#
# 가장 안전한 방법:
#   1) 새 항상-실행 sidebar 블록을 if not _is_auth_now: 바로 앞에 삽입
#   2) 기존 with st.sidebar: (28685) 제거 → 내용은 들여쓰기 4스페이스 감소
#   3) 중복 render_goldkey_sidebar() 제거
# ─────────────────────────────────────────────────────────────────────────────

# 실제 수정: 기존 코드 내 with st.sidebar 블록 헤더 제거 (comment+variable+with 3줄)
# 그리고 하위 코드 들여쓰기 4스페이스 감소 (28685~30628 이전까지)

# 먼저 새 블록 삽입
new_lines = lines[:INSERT_BEFORE] + [SIDEBAR_NAV_BLOCK] + lines[INSERT_BEFORE:]
print(f"삽입 완료: 총 {len(new_lines)}줄")

# ─────────────────────────────────────────────────────────────────────────────
# 다음: 기존 with st.sidebar: 블록(원본 기준 28682~28684+28685) 제거
# 삽입 후 라인번호가 밀렸으므로 SIDEBAR_NAV_BLOCK 줄 수만큼 오프셋 추가
offset = SIDEBAR_NAV_BLOCK.count('\n')
print(f"삽입 블록 줄 수: {offset}")

# 원본 28681(idx) = 새 idx 28681+offset
# 원본 28684(idx) = "    with st.sidebar:\n"  → 이 4줄 제거
# 원본 idx: 28681, 28682, 28683, 28684 (4줄: 주석2+변수1+with1)
REMOVE_START = 28681 + offset   # "    # ── 사이드바 ──..."
REMOVE_END   = 28685 + offset   # "    with st.sidebar:\n" 포함 (exclusive)

print(f"\n제거 범위 ({REMOVE_START+1}~{REMOVE_END}):")
for i in range(REMOVE_START, REMOVE_END):
    print(f"  {i+1}: {repr(new_lines[i][:70])}")

print(f"\n다음 줄 (유지): {repr(new_lines[REMOVE_END][:70])}")

new_lines2 = new_lines[:REMOVE_START] + new_lines[REMOVE_END:]
print(f"\n제거 완료: 총 {len(new_lines2)}줄")

# ─────────────────────────────────────────────────────────────────────────────
# 기존 with st.sidebar: 내부 코드(8스페이스 indent) → 4스페이스로 변환
# 범위: REMOVE_START ~ 비로그인 st.stop() 직전
# 단, render_goldkey_sidebar() 와 비로그인 열기JS는 중복이므로 제거
# ─────────────────────────────────────────────────────────────────────────────
# with st.sidebar: 제거 후, 원래 8스페이스 indent 코드들이 노출됨
# 이 코드들은 if not _is_auth_now: 블록 내부이므로 4스페이스 indent가 맞음
# 8스페이스 → 4스페이스 변환 대신:
# 기존 with st.sidebar 내부는 "        " (8스페이스) → "    " (4스페이스) 으로 감소
# 하지만 그 안에 중첩된 코드는 상대 indent 유지

# 정확한 범위 파악: REMOVE_START 에서 시작해 st.stop() (원본 28680+offset-4) 까지
# 먼저 st.stop() 위치 재탐색
stop_line = -1
for i in range(REMOVE_START, REMOVE_START + 3000):
    if i >= len(new_lines2): break
    if new_lines2[i].rstrip() == '        st.stop()':  # 8스페이스 indent
        stop_line = i
        break

print(f"\nst.stop() (8-space indent) at line {stop_line+1}")
if stop_line > 0:
    print(repr(new_lines2[stop_line][:60]))

# render_goldkey_sidebar() 중복 제거: REMOVE_START 에서 가장 가까운 render_goldkey_sidebar() 1줄
rgs_line = -1
for i in range(REMOVE_START, REMOVE_START + 5):
    if '        render_goldkey_sidebar()' in new_lines2[i]:
        rgs_line = i
        break
print(f"\nrender_goldkey_sidebar() at line {rgs_line+1}: {repr(new_lines2[rgs_line][:60]) if rgs_line>=0 else 'NOT FOUND'}")

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines2)
print("\n중간 저장 완료 (구문 검사 후 2단계 진행)")
