import re

with open(r"D:\CascadeProjects\app.py", encoding="utf-8-sig") as f:
    lines = f.readlines()

# 찾을 라인 번호 범위 (0-indexed: 28706~28714)
start = 28706  # 0-indexed
end   = 28715  # exclusive (line 28715 is the comment, also replace)

# 확인
print("=== 치환 대상 라인 ===")
for i in range(start, end):
    print(f"{i+1}: {repr(lines[i])}")

new_block = '''\
        # ── [메인 화면 로그인 폼] 사이드바 의존 완전 제거 ──
        st.markdown(
            "<div style='text-align:center;padding:20px 20px 10px;'>"
            "<div style='font-size:2.0rem;font-weight:900;color:#1e3a8a;margin-bottom:6px;'>\\U0001f3c6 Goldkey AI Masters 2026</div>"
            "<div style='font-size:0.95rem;color:#374151;'>아래에서 로그인하세요</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        _mc1, _mc2, _mc3 = st.columns([1, 2, 1])
        with _mc2:
            if _sc_render_auth_screen:
                _main_agreed = _sc_render_auth_screen(
                    app_name="Goldkey AI Masters 2026",
                    app_icon="\\U0001f3c6",
                    terms_agree_key="_gp_terms_agreed",
                )
            else:
                _main_agreed = st.checkbox(
                    "이용약관 및 개인정보 처리방침에 동의합니다.",
                    value=st.session_state.get("_gp_terms_agreed", False),
                    key="_gp_terms_agreed",
                )
            if _main_agreed:
                _tab_l, _tab_s, _tab_pw, _tab_nm = st.tabs(["\\U0001f511 로그인", "\\U0001f4dd 회원가입", "\\U0001f512 비번변경", "\\U0000270f\\ufe0f 이름변경"])
                with _tab_l:
                    import random as _rnd2
                    _lp2 = st.session_state.get("_main_login_phase", "A")
                    if _lp2 == "A":
                        _tr2 = st.session_state.setdefault("_main_tr", {})
                        _tr2["t1"] = st.checkbox("\\u2705 [필수] 개인정보 수집·이용 동의",      value=_tr2.get("t1", False), key="_main_t1")
                        _tr2["t2"] = st.checkbox("\\u2705 [필수] 서비스 이용약관 동의",          value=_tr2.get("t2", False), key="_main_t2")
                        _tr2["t3"] = st.checkbox("\\u2705 [필수] 암호화 보관·영구보관 동의",     value=_tr2.get("t3", False), key="_main_t3")
                        _tr2["t4"] = st.checkbox("\\u2705 [필수] 서비스 면책 및 이용 안내 동의", value=_tr2.get("t4", False), key="_main_t4")
                        _all2 = _tr2.get("t1") and _tr2.get("t2") and _tr2.get("t3") and _tr2.get("t4")
                        _name2    = st.text_input("\\U0001f464 이름",   key="main_login_name",    placeholder="가입 시 등록한 이름",        label_visibility="collapsed")
                        _contact2 = st.text_input("\\U0001f4f1 연락처", type="password", key="main_login_contact", placeholder="연락처 (숫자만, - 제외)", label_visibility="collapsed")
                        if not _all2:
                            st.warning("\\u26a0\\ufe0f 필수 항목 4개 모두 동의 후 로그인 가능합니다.")
                        if st.button("\\U0001f510 AI 마스터 로그인", key="main_login_btn", use_container_width=True, type="primary", disabled=not bool(_all2)):
                            _n2  = (_name2    or "").strip()
                            _c2v = (_contact2 or "").strip()
                            if not _n2 or len(_n2) < 2:
                                st.error("\\u26a0\\ufe0f 이름을 2자 이상 입력해 주세요.")
                            elif not _c2v:
                                st.error("\\u26a0\\ufe0f 연락처를 입력해 주세요.")
                            else:
                                _mbs2 = load_members()
                                if _n2 not in _mbs2:
                                    st.error("\\u274c 등록되지 않은 이름입니다. 회원가입 탭에서 가입해주세요.")
                                elif _mbs2[_n2].get("pin_hash", "") != hashlib.sha256(_c2v.encode()).hexdigest():
                                    st.error("\\u274c 연락처가 일치하지 않습니다.")
                                else:
                                    _otp2 = str(_rnd2.randint(100000, 999999))
                                    st.session_state["_main_otp"]         = _otp2
                                    st.session_state["_main_login_name"]  = _n2
                                    st.session_state["_main_login_phase"] = "B"
                                    st.info(f"\\u2705 인증번호: **{_otp2}** (아래 입력창에 입력하세요)")
                                    st.rerun()
                    elif _lp2 == "B":
                        _otp_inp2 = st.text_input("\\U0001f522 인증번호 6자리", key="main_otp_input", placeholder="화면의 6자리 숫자 입력")
                        if st.button("\\u2705 인증 완료", key="main_otp_confirm", use_container_width=True, type="primary"):
                            if (_otp_inp2 or "").strip() == st.session_state.get("_main_otp", ""):
                                _ln2  = st.session_state.get("_main_login_name", "")
                                _mbs3 = load_members()
                                _m2   = _mbs3.get(_ln2, {})
                                st.session_state["user_id"]       = _m2.get("user_id", _ln2)
                                st.session_state["user_name"]     = _ln2
                                st.session_state["authenticated"] = True
                                st.session_state["_is_auth"]      = True
                                st.session_state["is_admin"]      = (_ln2 in _get_unlimited_users())
                                st.session_state.pop("_main_login_phase", None)
                                st.session_state.pop("_main_otp", None)
                                st.rerun()
                            else:
                                st.error("\\u274c 인증번호가 틀렸습니다.")
                        if st.button("\\u21a9\\ufe0f 다시 입력", key="main_otp_back"):
                            st.session_state["_main_login_phase"] = "A"
                            st.rerun()
                with _tab_s:
                    with st.form("main_signup_form"):
                        _su_name    = st.text_input("이름",    key="main_su_name",    label_visibility="collapsed", placeholder="이름 (2자 이상)")
                        _su_contact = st.text_input("연락처", type="password", key="main_su_contact", label_visibility="collapsed", placeholder="연락처 (숫자만)")
                        if st.form_submit_button("\\u2705 가입하기", use_container_width=True):
                            _sn  = (_su_name    or "").strip()
                            _sc2 = (_su_contact or "").strip()
                            if not _sn or len(_sn) < 2:
                                st.error("이름을 2자 이상 입력해주세요.")
                            elif not _sc2 or len(_sc2) < 4:
                                st.error("연락처를 입력해주세요.")
                            else:
                                _mbs_su = load_members()
                                if _sn in _mbs_su:
                                    st.error("이미 등록된 이름입니다.")
                                else:
                                    _sb_su = _get_sb_client()
                                    if _sb_su:
                                        _h_su   = hashlib.sha256(_sc2.encode()).hexdigest()
                                        _uid_su = hashlib.md5(f"{_sn}{_sc2}".encode()).hexdigest()[:12]
                                        try:
                                            _sb_su.table("gk_members").insert({
                                                "name": _sn, "user_id": _uid_su, "pin_hash": _h_su,
                                                "join_date": dt.now().strftime("%Y-%m-%d"),
                                                "is_active": True, "status": "active"
                                            }).execute()
                                            load_members(force=True)
                                            st.success(f"\\u2705 가입 완료! '{_sn}'님, 로그인 탭에서 로그인하세요.")
                                        except Exception as _e_su:
                                            st.error(f"가입 실패: {_e_su}")
                                    else:
                                        st.error("서버 연결 오류. 잠시 후 다시 시도해주세요.")
                with _tab_pw:
                    with st.form("main_pw_form"):
                        _pw_name = st.text_input("이름",           key="main_pw_name", label_visibility="collapsed", placeholder="이름")
                        _pw_old  = st.text_input("기존 연락처",    type="password", key="main_pw_old",  label_visibility="collapsed", placeholder="기존 연락처")
                        _pw_new1 = st.text_input("새 연락처",      type="password", key="main_pw_new1", label_visibility="collapsed", placeholder="새 연락처")
                        _pw_new2 = st.text_input("새 연락처 확인", type="password", key="main_pw_new2", label_visibility="collapsed", placeholder="새 연락처 재입력")
                        if st.form_submit_button("\\U0001f504 변경", use_container_width=True):
                            _pn = (_pw_name or "").strip(); _po = (_pw_old  or "").strip()
                            _p1 = (_pw_new1 or "").strip(); _p2 = (_pw_new2 or "").strip()
                            if not all([_pn, _po, _p1, _p2]):
                                st.error("모든 항목을 입력해주세요.")
                            elif _p1 != _p2:
                                st.error("새 연락처가 일치하지 않습니다.")
                            else:
                                _mbs_pw = load_members()
                                if _pn not in _mbs_pw:
                                    st.error("등록되지 않은 이름입니다.")
                                elif _mbs_pw[_pn].get("pin_hash", "") != hashlib.sha256(_po.encode()).hexdigest():
                                    st.error("기존 연락처가 일치하지 않습니다.")
                                else:
                                    _sb_pw = _get_sb_client()
                                    if _sb_pw:
                                        try:
                                            _sb_pw.table("gk_members").update({"pin_hash": hashlib.sha256(_p1.encode()).hexdigest()}).eq("name", _pn).execute()
                                            load_members(force=True)
                                            st.success("\\u2705 변경 완료!")
                                        except Exception as _e_pw:
                                            st.error(f"변경 실패: {_e_pw}")
                with _tab_nm:
                    with st.form("main_nm_form"):
                        _nm_old  = st.text_input("현재 이름",    key="main_nm_old",  label_visibility="collapsed", placeholder="현재 이름")
                        _nm_pw   = st.text_input("연락처",       type="password", key="main_nm_pw",   label_visibility="collapsed", placeholder="연락처")
                        _nm_new  = st.text_input("새 이름",      key="main_nm_new",  label_visibility="collapsed", placeholder="새 이름")
                        _nm_new2 = st.text_input("새 이름 확인", key="main_nm_new2", label_visibility="collapsed", placeholder="새 이름 재입력")
                        if st.form_submit_button("\\U0001f504 변경", use_container_width=True):
                            _no  = (_nm_old  or "").strip(); _np  = (_nm_pw   or "").strip()
                            _n1  = (_nm_new  or "").strip(); _n2b = (_nm_new2 or "").strip()
                            if not all([_no, _np, _n1, _n2b]):
                                st.error("모든 항목을 입력해주세요.")
                            elif _n1 != _n2b:
                                st.error("새 이름이 일치하지 않습니다.")
                            else:
                                _mbs_nm = load_members()
                                if _no not in _mbs_nm:
                                    st.error("등록되지 않은 이름입니다.")
                                elif _mbs_nm[_no].get("pin_hash", "") != hashlib.sha256(_np.encode()).hexdigest():
                                    st.error("연락처가 일치하지 않습니다.")
                                else:
                                    _sb_nm = _get_sb_client()
                                    if _sb_nm:
                                        try:
                                            _sb_nm.table("gk_members").update({"name": _n1}).eq("name", _no).execute()
                                            load_members(force=True)
                                            st.success("\\u2705 이름 변경 완료!")
                                        except Exception as _e_nm:
                                            st.error(f"변경 실패: {_e_nm}")
        st.stop()
'''

lines[start:end] = [new_block]

with open(r"D:\CascadeProjects\app.py", "w", encoding="utf-8") as f:
    f.writelines(lines)

print("PATCH OK")
