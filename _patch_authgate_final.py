with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# _auth_gate 시작/끝 찾기
ag_start = None
ag_end = None
for i, ln in enumerate(lines):
    if ln.startswith('def _auth_gate('):
        ag_start = i
    if ag_start and i > ag_start and ln.startswith('def ') and 'auth_gate' not in ln:
        ag_end = i
        break

print(f"_auth_gate: L{ag_start+1} ~ L{ag_end} (next def L{ag_end+1})")

# 올바른 _auth_gate 함수 교체 내용
NEW_AUTH_GATE = '''def _auth_gate(tab_key: str) -> bool:
    """로그인 상태 중앙 체크 — False 반환 시 해당 기둥 렌더 중단"""
    _GUEST_BLOCKED_TABS = {
        "customer_mgmt", "customer_docs", "leaflet", "consult_catalog",
        "digital_catalog", "know_pipe", "report43", "scan_hub",
        "life_defense", "war_room",
    }
    _is_unauthed   = "user_id" not in st.session_state
    _is_guest_role = st.session_state.get("_user_role") == "GUEST"
    _is_guest_uid  = st.session_state.get("user_id", None) == ""

    if _is_unauthed:
        st.markdown("""
<div style="background:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 100%);
  border-radius:14px;padding:28px 22px;margin:20px 0;text-align:center;">
  <div style="font-size:2.5rem;margin-bottom:10px;">🔒</div>
  <div style="color:#1e3a5f;font-size:1.15rem;font-weight:900;margin-bottom:8px;">
로그인 후 이용 가능합니다
  </div>
  <div style="color:#b3d4f5;font-size:0.85rem;">
왼쪽 사이드바 하단 <b style="color:#ffd700;">Admin Console</b>에서 로그인하세요
  </div>
</div>""", unsafe_allow_html=True)
        _ag_c1, _ag_c2 = st.columns(2)
        with _ag_c1:
            if st.button("🏠 홈으로 돌아가기", key=f"auth_gate_home_{tab_key}",
                         use_container_width=True, type="primary"):
                st.session_state.current_tab = "home"
                st.session_state["_scroll_top"] = True
                st.rerun()
        with _ag_c2:
            if st.button("🔓 로그인 열기", key=f"auth_gate_login_{tab_key}",
                         use_container_width=True):
                st.session_state["_open_sidebar"] = True
                st.rerun()
        return False

    if (_is_guest_role or _is_guest_uid) and tab_key in _GUEST_BLOCKED_TABS:
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#FFF9C4 0%,#FFF176 100%);
  border:2px solid #F9A825;border-radius:14px;padding:24px 22px;
  margin:20px 0;text-align:center;">
  <div style="font-size:2.2rem;margin-bottom:8px;">🔒</div>
  <div style="color:#000000;font-size:1.1rem;font-weight:900;margin-bottom:8px;">
정회원 전용 기능입니다
  </div>
  <div style="color:#5D4037;font-size:0.85rem;line-height:1.7;margin-bottom:10px;">
<b>고객 정보·등록·자료 관련 기능</b>은 임시/비회원에게 제공되지 않습니다.<br>
사이드바 <b>회원가입</b> 탭에서 가입 후 이용하세요.
  </div>
  <div style="font-size:0.75rem;color:#795548;">
← 사이드바 · <b>📝 회원가입</b> 탭 즉시 이용 가능
  </div>
</div>""", unsafe_allow_html=True)
        _gb_c1, _gb_c2 = st.columns(2)
        with _gb_c1:
            if st.button("🏠 홈으로 돌아가기", key=f"guest_block_home_{tab_key}",
                         use_container_width=True, type="primary"):
                st.session_state.current_tab = "home"
                st.session_state["_scroll_top"] = True
                st.rerun()
        with _gb_c2:
            if st.button("📝 회원가입 하기", key=f"guest_block_signup_{tab_key}",
                         use_container_width=True):
                st.session_state["_open_sidebar"] = True
                st.rerun()
        return False

    st.session_state["gs_last_tab"] = tab_key
    return True

'''

lines = lines[:ag_start] + [NEW_AUTH_GATE] + lines[ag_end:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE: _auth_gate replaced cleanly")
