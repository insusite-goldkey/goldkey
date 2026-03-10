    if cur == "home":
        # ── 심야 배치 워커 트리거 (02~04 KST, 세션당 1회) ────────────────
        if not st.session_state.get('home_rendered'):
            st.session_state.home_rendered = True
        if not st.session_state.get('_art38_night_ran_today'):
            import datetime as _dt_nw
            _nw_kst = _dt_nw.datetime.now(tz=_dt_nw.timezone(_dt_nw.timedelta(hours=9)))
            _nw_min = _nw_kst.hour * 60 + _nw_kst.minute
            if 120 <= _nw_min < 240:
                import threading as _th_nw
                _th_nw.Thread(target=_art38_night_worker, daemon=True).start()
                st.session_state['_art38_night_ran_today'] = True

        # ── [MASTER HUB 2026] 전역 CSS ──────────────────────────────────
        st.markdown("""
<style>
.gk-sec {
  border: 2px solid #FF0000;
  border-radius: 14px;
  padding: 18px 18px 14px 18px;
  margin-bottom: 18px;
  background: #ffffff;
  box-shadow: 0 2px 12px rgba(255,0,0,0.08);
}
.gk-sec-title {
  font-size: 0.78rem; font-weight: 900; color: #ffffff;
  background: #CC0000; border-radius: 20px;
  padding: 3px 14px; display: inline-block;
  margin-bottom: 12px; letter-spacing: 0.08em; text-transform: uppercase;
}
.gk-ai-output-box {
  border: 2px solid #FF0000; border-radius: 12px;
  padding: 16px 18px; background: #E3F2FD;
  min-height: 260px; max-height: 420px;
  overflow-y: auto; box-sizing: border-box;
}
.gk-scan-output {
  border: 2px solid #FF0000; border-radius: 12px;
  padding: 16px 18px; background: #E3F2FD;
  min-height: 260px; max-height: 420px;
  overflow-y: auto; box-sizing: border-box;
}
.gk-scan-controller {
  border: 2px solid #FF0000; border-radius: 12px;
  padding: 16px 14px; background: #ffffff;
}
.gk-pf-card {
  border-radius: 14px; padding: 20px 18px 16px 18px;
  margin-bottom: 6px; box-sizing: border-box;
  transition: transform 0.15s, box-shadow 0.15s;
}
.gk-pf-card:hover { transform: translateY(-2px); box-shadow: 0 8px 28px rgba(0,0,0,0.22); }
.gk-pf-title { font-size: 1.3rem; font-weight: 900; color: #ffffff; line-height: 1.25; margin-bottom: 6px; }
.gk-pf-sub   { font-size: 0.84rem; font-weight: 700; color: #ffffff; line-height: 1.55; margin-bottom: 10px; }
.gk-pf-count { font-size: 0.78rem; font-weight: 700; color: #ffffff;
  background: rgba(255,255,255,0.18); border-radius: 16px; padding: 3px 10px; display: inline-block; }
.gk-rb-btn > div > button {
  background: #E3F2FD !important; color: #000000 !important;
  font-weight: 800 !important; border: 2px solid #FF0000 !important;
  border-radius: 10px !important;
}
.gk-rb-btn > div > button:hover {
  background: #BBDEFB !important; border-color: #CC0000 !important;
}
.gk-dash-box { box-sizing: border-box; overflow-y: auto; }
.gk-dash-box::-webkit-scrollbar { width: 4px; }
.gk-dash-box::-webkit-scrollbar-thumb { background: rgba(255,0,0,0.35); border-radius: 4px; }
.gk-save-btn-marker + div[data-testid="stButton"] > button {
  background: #BAE6FD !important; border: 2px solid #0284C7 !important;
  color: #000000 !important; font-weight: 800 !important;
}
@media (max-width: 768px) { .gk-pf-card { margin-bottom: 12px; } }
</style>""", unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════════
        # [TOP] 히어로 배너
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div style="position:relative;height:0;">{_bid("GK-HOME-01")}</div>', unsafe_allow_html=True)
        if not st.session_state.get("_gp45_splash_shown"):
            st.session_state["_gp45_splash_shown"] = True
            try:
                import base64 as _b64
                _splash_path = "image_da52b7.jpg"
                import os as _os
                if _os.path.exists(_splash_path):
                    with open(_splash_path, "rb") as _sf:
                        _SPLASH_SRC = "data:image/jpeg;base64," + _b64.b64encode(_sf.read()).decode()
                else:
                    _SPLASH_SRC = ""
            except Exception:
                _SPLASH_SRC = ""
            if _SPLASH_SRC:
                st.markdown(f"""
<div style="width:100%;margin:0 0 16px 0;border-radius:16px;overflow:hidden;
  box-shadow:0 4px 20px rgba(0,0,0,0.18);position:relative;">
  <img src="{_SPLASH_SRC}" loading="lazy"
    style="width:100%;max-height:260px;object-fit:cover;object-position:center top;
    display:block;border-radius:16px;" alt="GOLDKEY AI MASTER" />
  <div style="position:absolute;bottom:10px;right:14px;
    font-size:0.62rem;color:rgba(255,255,255,0.75);font-weight:600;letter-spacing:0.05em;">
    ※ 본 분석은 AI 시뮬레이션입니다. 보험금 지급 여부는 보험사 심사 및 손해사정사 판단에 따릅니다.
  </div>
</div>""", unsafe_allow_html=True)

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-01] 고객 마스터 데이터 및 통합 상담
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-01")}<span class="gk-sec-title">① 고객 마스터 데이터 &amp; 통합 상담</span></div>', unsafe_allow_html=True)

        if 'user_id' in st.session_state:
            # ── 그룹 A: 기본 정보 ─────────────────────────────────────
            st.markdown("**👤 그룹 A — 고객 기본 정보**")
            _uid_for_cust = st.session_state.get("user_id", "")
            _cust_cache_key  = f"_cust_rows_{_uid_for_cust}"
            _cust_cache_ts   = f"_cust_rows_ts_{_uid_for_cust}"
            _cust_cache_valid = (
                _cust_cache_key in st.session_state
                and (time.time() - st.session_state.get(_cust_cache_ts, 0)) < 60
            )
            if _cust_cache_valid:
                _cust_rows = st.session_state[_cust_cache_key]
            else:
                try:
                    from customer_mgmt import load_customers as _load_cust
                    _sb_cust = _get_sb_client() if _SB_PKG_OK else None
                    _cust_rows = _load_cust(_uid_for_cust, _sb_cust) if (_sb_cust and _uid_for_cust) else []
                    st.session_state[_cust_cache_key] = _cust_rows
                    st.session_state[_cust_cache_ts]  = time.time()
                except Exception:
                    _cust_rows = st.session_state.get(_cust_cache_key, [])

            def _cust_label(row):
                _n = row.get("name", "")
                _dob = (row.get("profile") or {}).get("dob", "")
                return f"{_n}  ({_dob})" if _dob else _n

            _cust_options_map = {"✏️ 고객 입력 & 검색": None}
            for _cr in _cust_rows:
                _cust_options_map[_cust_label(_cr)] = _cr
            _search_label = st.session_state.get("_home_selected_cust_label", "✏️ 고객 입력 & 검색")
            if _search_label not in _cust_options_map:
                _search_label = "✏️ 고객 입력 & 검색"

            _srch_col1, _srch_col2 = st.columns([3, 1])
            with _srch_col1:
                _selected_label = st.selectbox(
                    "고객 선택 (이름 검색)",
                    options=list(_cust_options_map.keys()),
                    index=list(_cust_options_map.keys()).index(_search_label),
                    key="home_cust_selectbox",
                    help="등록된 고객 이름으로 검색·선택하면 아래 정보가 자동 채워집니다"
                )
            with _srch_col2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🔍 새로고침", key="btn_cust_search", use_container_width=True):
                    st.session_state.pop("_home_selected_cust_label", None)
                    _uid_inv = st.session_state.get("user_id", "")
                    st.session_state.pop(f"_cust_rows_{_uid_inv}", None)
                    st.session_state.pop(f"_cust_rows_ts_{_uid_inv}", None)
                    st.rerun()

            _selected_row = _cust_options_map.get(_selected_label)
            if _selected_row and _selected_label != "✏️ 고객 입력 & 검색":
                st.session_state["_home_selected_cust_label"] = _selected_label
                st.session_state["selected_customer_id"] = _selected_row.get("id")
                _prof = _selected_row.get("profile") or {}
                _auto_map = {
                    "scan_client_name":  _selected_row.get("name", ""),
                    "scan_client_dob":   _prof.get("dob", ""),
                    "scan_client_job":   _prof.get("job", ""),
                    "scan_client_sick":  _prof.get("sick", "해당없음"),
                    "scan_client_items": _prof.get("items", []),
                }
                for _k, _v in _auto_map.items():
                    if st.session_state.get(_k) != _v:
                        st.session_state[_k] = _v
                st.success(f"✅ [{_selected_row.get('name','')}] 자동 로드 완료")
            else:
                st.session_state["selected_customer_id"] = None
                st.session_state["_home_selected_cust_label"] = "✏️ 고객 입력 & 검색"

            st.markdown("<hr style='margin:10px 0;border-color:#ffcccc;'>", unsafe_allow_html=True)

            _SICK_OPTIONS = [
                "해당없음",
                "심사필요(3개월이내 치료 있음)",
                "유병자(입원·수술이력 있음)",
                "유병자(당뇨·고혈압·심장 등 약 투약중)",
                "유병자(암·중풍 발병 있음)",
            ]
            _SICK_GUIDE = {
                "해당없음":                             "✅ 일반·건강체 보험가입 설계 가능",
                "심사필요(3개월이내 치료 있음)":          "⚠️ 최종 통원일 경과 후 신규보험 상담 진행. 유병자 운전자보험은 1개월 경과 후 심사 요청 가능",
                "유병자(입원·수술이력 있음)":            "📋 유병자보험 3.0.5~3.5.5 — 병력에 따라 구분 가입 상담",
                "유병자(당뇨·고혈압·심장 등 약 투약중)": "📋 유병자보험 3.0.5~3.5.5 — 병력에 따라 구분 가입 상담",
                "유병자(암·중풍 발병 있음)":             "⚠️ 최종 통원일 이후 5년 경과 후 암 상담. 향후 유병자 신규 상품 가입 가능 여부 확인",
            }
            _cur_sick = st.session_state.get("scan_client_sick", "해당없음")
            if _cur_sick not in _SICK_OPTIONS:
                _cur_sick = "해당없음"

            _ga1, _ga2 = st.columns([1, 1])
            with _ga1:
                _si_name = st.text_input("성명", value=st.session_state.get("scan_client_name", ""),
                                         placeholder="예) 홍길동", key="home_si_name")
                _si_dob  = st.text_input("생년월일 (YYYYMMDD)", value=st.session_state.get("scan_client_dob", ""),
                                         placeholder="예) 19800101", max_chars=8, key="home_si_dob")
            with _ga2:
                _si_job  = st.text_input("직업", value=st.session_state.get("scan_client_job", ""),
                                         placeholder="예) 회사원", key="home_si_job")
                _si_sick = st.selectbox("유병자 여부", _SICK_OPTIONS,
                                        index=_SICK_OPTIONS.index(_cur_sick), key="home_si_sick")
            _sick_guide_text = _SICK_GUIDE.get(_si_sick, "")
            if _sick_guide_text:
                _sick_color = "#9a3412" if "⚠️" in _sick_guide_text else "#14532d"
                _sick_bg    = "#fff7ed" if "⚠️" in _sick_guide_text else "#f0fdf4"
                _sick_bdr   = "#f97316" if "⚠️" in _sick_guide_text else "#22c55e"
                st.markdown(
                    f'<div style="background:{_sick_bg};border:1.5px solid {_sick_bdr};border-radius:8px;'
                    f'padding:8px 12px;font-size:0.82rem;font-weight:700;color:{_sick_color};'
                    f'white-space:pre-line;margin-bottom:8px;">{_sick_guide_text}</div>',
                    unsafe_allow_html=True)

            _si_items = st.multiselect(
                "상담 항목 (복수 선택)",
                ["신규보험상담", "보험증권 분석", "보험금 청구", "장해 산출", "암·뇌·심장",
                 "리플렛 분류", "약관 검색", "부동산 투자", "간병비", "노후설계", "법인상담"],
                default=st.session_state.get("scan_client_items", []), key="home_si_items"
            )
            st.markdown('<div class="gk-save-btn-marker" style="display:none;"></div>', unsafe_allow_html=True)
            if st.button("💾 고객 정보 저장 (전체 탭 자동 연동)", key="btn_save_client_info", use_container_width=True):
                st.session_state["scan_client_name"]  = _si_name
                st.session_state["scan_client_dob"]   = _si_dob
                st.session_state["scan_client_job"]   = _si_job
                st.session_state["scan_client_sick"]  = _si_sick
                st.session_state["scan_client_items"] = _si_items
                _cid_save = st.session_state.get("selected_customer_id")
                if _cid_save:
                    try:
                        from customer_mgmt import update_profile as _upd_prof
                        _sb_s = st.session_state.get("supabase_client") or st.session_state.get("sb")
                        _upd_prof(_cid_save, {
                            "dob": _si_dob, "job": _si_job,
                            "sick": _si_sick, "items": _si_items,
                        }, _sb_s)
                    except Exception:
                        pass
                st.success(f"✅ {_si_name} 저장 완료 — 모든 탭에 자동 연동됩니다.")

            # ── 그룹 B: 오늘 할 일 · 오늘의 약속 · 상담 대기 ───────────
            st.markdown("<hr style='margin:12px 0;border-color:#ffcccc;'>", unsafe_allow_html=True)
            st.markdown("**📊 그룹 B — 오늘의 업무 현황**")

            if "_agent_todo" not in st.session_state:
                st.session_state["_agent_todo"] = [
                    {"done": False, "text": "김○○ 고객 암보험 설계서 발송"},
                    {"done": False, "text": "이○○ 고객 청구서류 취합"},
                    {"done": True,  "text": "월간 실적 보고서 제출"},
                ]
            if "_agent_appt" not in st.session_state:
                st.session_state["_agent_appt"] = [
                    {"time": "10:30", "name": "박○○", "type": "신규상담"},
                    {"time": "14:00", "name": "최○○", "type": "갱신안내"},
                ]
            if "_agent_wait" not in st.session_state:
                st.session_state["_agent_wait"] = [
                    {"name": "정○○", "status": "서류검토중"},
                    {"name": "강○○", "status": "심사대기"},
                    {"name": "윤○○", "status": "출금확인"},
                ]

            _todo_list = st.session_state["_agent_todo"]
            _appt_list = st.session_state["_agent_appt"]
            _wait_list = st.session_state["_agent_wait"]

            _todo_html = "".join(
                f'<div style="padding:3px 0;border-bottom:1px solid #f0f0f0;font-size:0.82rem;'
                f'font-weight:700;color:{"#94a3b8" if t["done"] else "#000000"};'
                f'text-decoration:{"line-through" if t["done"] else "none"};">'
                f'{"✅" if t["done"] else "⬜"} {t["text"]}</div>'
                for t in _todo_list
            )
            _appt_html = "".join(
                f'<div style="padding:3px 0;border-bottom:1px solid #f0f0f0;font-size:0.82rem;font-weight:700;color:#000000;">'
                f'<span style="color:#dc2626;font-weight:900;">{a["time"]}</span>'
                f' {a["name"]} <span style="color:#6b7280;">· {a["type"]}</span></div>'
                for a in _appt_list
            )
            _wait_html = "".join(
                f'<div style="padding:3px 0;border-bottom:1px solid #f0f0f0;font-size:0.82rem;font-weight:700;color:#000000;">'
                f'{w["name"]} <span style="color:#0369a1;">{w["status"]}</span></div>'
                for w in _wait_list
            )

            _gb1, _gb2, _gb3 = st.columns(3, gap="small")
            with _gb1:
                st.markdown(
                    f'<div class="gk-dash-box" style="border:2px solid #FF0000;border-radius:10px;'
                    f'padding:10px 12px;min-height:120px;max-height:180px;">'
                    f'<div style="font-size:0.75rem;font-weight:900;color:#CC0000;margin-bottom:6px;">📋 오늘 할 일</div>'
                    f'{_todo_html}</div>', unsafe_allow_html=True)
            with _gb2:
                st.markdown(
                    f'<div class="gk-dash-box" style="border:2px solid #FF0000;border-radius:10px;'
                    f'padding:10px 12px;min-height:120px;max-height:180px;">'
                    f'<div style="font-size:0.75rem;font-weight:900;color:#CC0000;margin-bottom:6px;">🕐 오늘의 약속</div>'
                    f'{_appt_html}</div>', unsafe_allow_html=True)
            with _gb3:
                st.markdown(
                    f'<div class="gk-dash-box" style="border:2px solid #FF0000;border-radius:10px;'
                    f'padding:10px 12px;min-height:120px;max-height:180px;">'
                    f'<div style="font-size:0.75rem;font-weight:900;color:#CC0000;margin-bottom:6px;">⏳ 상담 대기</div>'
                    f'{_wait_html}</div>', unsafe_allow_html=True)

            # ── 그룹 C: 상담노트(좌) / 보험가입상담(우) ─────────────────
            st.markdown("<hr style='margin:12px 0;border-color:#ffcccc;'>", unsafe_allow_html=True)
            st.markdown("**📝 그룹 C — 실전 상담**")
            _gc_left, _gc_right = st.columns([5, 5], gap="medium")

            with _gc_left:
                st.markdown("**상담 노트** — 고객 상담 내용 전체 기록")
                with st.expander("📝 상담노트 입력", expanded=False):
                    with st.form(key="form_consult_note", clear_on_submit=True):
                        _nd_col1, _nd_col2 = st.columns([1, 2])
                        with _nd_col1:
                            _note_date = st.date_input("상담 일자", key="form_note_date")
                        with _nd_col2:
                            _note_summary = st.text_input(
                                "상담 요약", placeholder="예) 암보험상담", key="form_note_summary")
                        _note_text = st.text_area(
                            "상담 내용 (상세)",
                            placeholder="고객과 관련된 모든 상담 내용을 입력하세요...",
                            height=140, key="form_note_text")
                        _note_submitted = st.form_submit_button("💾 상담노트 저장", use_container_width=True)
                        if _note_submitted:
                            _cid = st.session_state.get("selected_customer_id")
                            _cname = st.session_state.get("scan_client_name", "")
                            _sb_saved = save_home_note(
                                st.session_state.get("user_id", ""),
                                _cid, _cname, str(_note_date), _note_summary, _note_text,
                                device_uuid=st.session_state.get("_device_uuid", ""),
                            )
                            _notes = st.session_state.get("consult_notes", [])
                            _notes.insert(0, {
                                "date": str(_note_date), "summary": _note_summary,
                                "content": _note_text, "customer_id": _cid, "customer_name": _cname,
                            })
                            st.session_state["consult_notes"] = _notes
                            if _sb_saved:
                                st.success(f"✅ [{_note_date}] 저장됨 (영구저장✔️)")
                            else:
                                st.warning("⚠️ 임시저장됨 — Supabase 연결 확인 필요")
                _cur_cid = st.session_state.get("selected_customer_id")
                _uid_now = st.session_state.get("user_id", "")
                _notes_saved = load_home_notes(_uid_now, _cur_cid) if _uid_now else []
                if not _notes_saved:
                    _notes_all = st.session_state.get("consult_notes", [])
                    _notes_saved = ([_n for _n in _notes_all if _n.get("customer_id") == _cur_cid]
                                    if _cur_cid else _notes_all)
                if _notes_saved:
                    _cname_disp = st.session_state.get("scan_client_name", "")
                    st.markdown(
                        f"**📋 저장된 상담 노트{' — ' + _cname_disp if _cname_disp else ''} (최근순)**")
                    for _n in _notes_saved[:5]:
                        st.markdown(
                            f'<div style="border:1px solid #fca5a5;border-radius:6px;padding:8px 12px;'
                            f'margin-bottom:5px;background:#fff5f5;">'
                            f'<span style="font-weight:900;color:#000000;font-size:0.85rem;">{_n["date"]}</span>'
                            f'{(" | <b>" + _n.get("summary","") + "</b>") if _n.get("summary") else ""}'
                            f'<br><span style="color:#374151;font-size:0.8rem;">'
                            f'{_n.get("content","")[:120]}{"..." if len(_n.get("content",""))>120 else ""}'
                            f'</span></div>', unsafe_allow_html=True)

            with _gc_right:
                st.markdown("**보험 가입 상담** — 청약·설계 기록")
                with st.expander("🛡️ 보험 가입 상담 입력", expanded=False):
                    with st.form(key="form_ins_consult", clear_on_submit=True):
                        _id_col1, _id_col2 = st.columns([1, 2])
                        with _id_col1:
                            _ins_date = st.date_input("가입 일자", key="form_ins_date")
                        with _id_col2:
                            _ins_product = st.text_input(
                                "상품명", placeholder="예) ○○생명 통합보험", key="form_ins_product")
                        _ins_bg = st.text_area(
                            "청약 배경", height=90, key="form_ins_bg",
                            placeholder="고지항목 병력 등 청약 배경 입력")
                        _ins_special = st.text_area(
                            "특이사항", height=90, key="form_ins_special",
                            placeholder="판촉물, 심사 결과 특이사항 등")
                        _ins_submitted = st.form_submit_button("💾 보험가입 상담 저장", use_container_width=True)
                        if _ins_submitted:
                            _cid = st.session_state.get("selected_customer_id")
                            _cname = st.session_state.get("scan_client_name", "")
                            _sb_saved2 = save_home_ins(
                                st.session_state.get("user_id", ""),
                                _cid, _cname, str(_ins_date), _ins_product, _ins_bg, _ins_special,
                                device_uuid=st.session_state.get("_device_uuid", ""),
                            )
                            _ins_list = st.session_state.get("insurance_consults", [])
                            _ins_list.insert(0, {
                                "date": str(_ins_date), "product": _ins_product,
                                "background": _ins_bg, "special": _ins_special,
                                "customer_id": _cid, "customer_name": _cname,
                            })
                            st.session_state["insurance_consults"] = _ins_list
                            if _sb_saved2:
                                st.success(f"✅ [{_ins_date}] 저장됨 (영구저장✔️)")
                            else:
                                st.warning("⚠️ 임시저장됨")
                _cur_cid2 = st.session_state.get("selected_customer_id")
                _uid_now2 = st.session_state.get("user_id", "")
                _ins_saved = load_home_ins(_uid_now2, _cur_cid2) if _uid_now2 else []
                if not _ins_saved:
                    _ins_all = st.session_state.get("insurance_consults", [])
                    _ins_saved = ([_i for _i in _ins_all if _i.get("customer_id") == _cur_cid2]
                                  if _cur_cid2 else _ins_all)
                if _ins_saved:
                    _cname_ins = st.session_state.get("scan_client_name", "")
                    st.markdown(
                        f"**📋 저장된 보험가입 상담{' — ' + _cname_ins if _cname_ins else ''} (최근순)**")
                    for _ins in _ins_saved[:5]:
                        st.markdown(
                            f'<div style="border:1px solid #bfdbfe;border-radius:6px;padding:8px 12px;'
                            f'margin-bottom:5px;background:#eff6ff;">'
                            f'<span style="font-weight:900;color:#000000;font-size:0.85rem;">{_ins["date"]}</span>'
                            f'{(" | <b>" + _ins.get("product","") + "</b>") if _ins.get("product") else ""}'
                            f'<br><span style="color:#374151;font-size:0.78rem;">배경: '
                            f'{_ins.get("background","")[:80]}{"..." if len(_ins.get("background",""))>80 else ""}'
                            f'</span></div>', unsafe_allow_html=True)
        else:
            st.markdown("**로그인 후 고객 정보 관리 기능이 활성화됩니다.**")

        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-01 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-02] 가처분 소득 기반 3단계 솔루션
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-02")}<span class="gk-sec-title">② 가처분 소득 기반 3단계 솔루션</span></div>', unsafe_allow_html=True)

        st.markdown("**암진단 · 뇌·심장 · 고객문서함 · 보장공백** 바로가기 및 종목별 최소/표준/적정 매트릭스")
        _s2_c1, _s2_c2, _s2_c3, _s2_c4 = st.columns(4, gap="small")
        with _s2_c1:
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🔴 암 진단", key="sec02_cancer", use_container_width=True):
                _go_tab("t1")
            st.markdown('</div>', unsafe_allow_html=True)
        with _s2_c2:
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🧠 뇌·심장", key="sec02_brain", use_container_width=True):
                _go_tab("t2")
            st.markdown('</div>', unsafe_allow_html=True)
        with _s2_c3:
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("📁 고객 문서함", key="sec02_docs", use_container_width=True):
                _go_tab("customer_mgmt")
            st.markdown('</div>', unsafe_allow_html=True)
        with _s2_c4:
            st.markdown('<div class="gk-rb-btn">', unsafe_allow_html=True)
            if st.button("🕳️ 보장 공백", key="sec02_gap", use_container_width=True):
                _go_tab("policy_scan")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        _s2_items = [
            ("암 진단비",     "1,000만원",  "3,000만원",  "5,000만원+"),
            ("뇌혈관 진단비", "500만원",    "2,000만원",  "3,000만원+"),
            ("심장 진단비",   "500만원",    "2,000만원",  "3,000만원+"),
            ("치매 진단비",   "500만원",    "2,000만원",  "3,000만원+"),
            ("운전자보험",    "가입 확인",  "상해사망 1억", "형사합의금 3천"),
            ("입원일당",      "1만원/일",   "3만원/일",   "5만원/일"),
            ("실손보험",      "4세대",      "3세대",      "1·2세대 유지"),
        ]
        _tbl_html = (
            '<div style="overflow-x:auto;">'
            '<table style="width:100%;border-collapse:collapse;font-size:0.83rem;">'
            '<thead><tr>'
            '<th style="background:#CC0000;color:#fff;font-weight:900;padding:7px 10px;text-align:left;">종목</th>'
            '<th style="background:#dc2626;color:#fff;font-weight:900;padding:7px 10px;text-align:center;">최소</th>'
            '<th style="background:#b91c1c;color:#fff;font-weight:900;padding:7px 10px;text-align:center;">표준</th>'
            '<th style="background:#991b1b;color:#fff;font-weight:900;padding:7px 10px;text-align:center;">적정</th>'
            '</tr></thead><tbody>'
        )
        for _i2, (_name2, _mn, _stv, _opt) in enumerate(_s2_items):
            _bg2 = "#fff5f5" if _i2 % 2 == 0 else "#ffffff"
            _tbl_html += (
                f'<tr style="background:{_bg2};">'
                f'<td style="padding:6px 10px;font-weight:900;color:#000000;border-bottom:1px solid #fecaca;">{_name2}</td>'
                f'<td style="padding:6px 10px;text-align:center;font-weight:700;color:#374151;border-bottom:1px solid #fecaca;">{_mn}</td>'
                f'<td style="padding:6px 10px;text-align:center;font-weight:700;color:#000000;border-bottom:1px solid #fecaca;">{_stv}</td>'
                f'<td style="padding:6px 10px;text-align:center;font-weight:900;color:#CC0000;border-bottom:1px solid #fecaca;">{_opt}</td>'
                f'</tr>'
            )
        _tbl_html += '</tbody></table></div>'
        st.markdown(_tbl_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-02 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-03] 보험금 상담 및 용어 센터 (5:5)
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-03")}<span class="gk-sec-title">③ 보험금 상담 &amp; 용어 센터</span></div>', unsafe_allow_html=True)
        st.markdown("질문 입력(좌) / AI 답변 3단계 구조 출력(우)")

        _s3_left, _s3_right = st.columns([5, 5], gap="medium")
        with _s3_left:
            _s3_q = st.text_area(
                "보험 용어 · 보험금 질문 입력",
                placeholder="예) 실손의료비, 맥브라이드 장해율, KCD코드, 입원일당 청구 기준...",
                height=120, key="sec03_query")
            if st.button("🔍 AI 답변 생성", key="sec03_search", use_container_width=True, type="primary"):
                if _s3_q and _s3_q.strip():
                    with st.spinner("AI 분석 중..."):
                        try:
                            _s3_cli = get_client()
                            _s3_sys = (
                                "당신은 보험 전문가입니다. 답변은 반드시 아래 3단계 구조로 작성하세요:\n"
                                "### 📘 (1) 용어 해설\n[용어 정의]\n\n"
                                "### 🔧 (2) 적용\n[실무 적용 방법]\n\n"
                                "### 💡 (3) 사용 사례\n[구체적 사례]"
                            )
                            _s3_resp = _s3_cli.chat.completions.create(
                                model=st.session_state.get("model_name", "gemini-2.0-flash"),
                                messages=[
                                    {"role": "system", "content": _s3_sys},
                                    {"role": "user", "content": _s3_q.strip()},
                                ],
                                max_tokens=1500,
                            )
                            st.session_state["sec03_result"] = _s3_resp.choices[0].message.content
                            st.session_state["sec03_scroll"] = True
                        except Exception as _s3_err:
                            st.session_state["sec03_result"] = f"⚠️ 오류: {_s3_err}"
                else:
                    st.warning("질문을 입력해 주세요.")
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            _nav_input_val = st.text_input(
                "🔊 코드/용어 네비게이션",
                placeholder="코드(예: 3000, 1220) 또는 용어(예: 보장공백·맥브라이드) 입력",
                key="voice_nav_input")
            if _nav_input_val and _nav_input_val.strip():
                _dest = _voice_navigate(_nav_input_val.strip())
                if _dest and isinstance(_dest, str):
                    _sc_info = SECTOR_CODES.get(_dest, {})
                    st.success(f"🔍 → [{_dest}] {_sc_info.get('name', '')}")
                    if st.button(f"➡️ 이동", key="sec03_nav_go"):
                        _go_tab(_sc_info.get("tab_key", "home"))
                        st.rerun()
                elif _dest and isinstance(_dest, list):
                    st.info("여러 항목 매칭 — 선택하세요:")
                    _amb_cols = st.columns(min(len(_dest), 3))
                    for _ai, _amb in enumerate(_dest):
                        _amb_sc = SECTOR_CODES.get(_amb.get("code", ""), {})
                        with _amb_cols[_ai % len(_amb_cols)]:
                            if st.button(
                                f"[{_amb.get('code','')}] {_amb_sc.get('name','')}",
                                key=f"sec03_amb_{_amb.get('code','')}",
                            ):
                                _go_tab(_amb_sc.get("tab_key", "home"))
                                st.rerun()
                else:
                    st.warning(f"'{_nav_input_val.strip()}' 항목을 찾지 못했습니다.")

        with _s3_right:
            _s3_scroll = st.session_state.pop("sec03_scroll", False)
            if _s3_scroll:
                import streamlit.components.v1 as _s3c
                _s3c.html(
                    '<script>(function(){var e=document.getElementById("sec03-anchor");'
                    'if(e)e.scrollIntoView({behavior:"smooth",block:"start"})})();</script>',
                    height=0)
            st.markdown(
                '<div id="sec03-anchor" style="font-size:0.9rem;font-weight:900;color:#CC0000;margin-bottom:8px;">'
                '🤖 AI 답변 (3단계: 용어해설 · 적용 · 사용사례)</div>',
                unsafe_allow_html=True)
            _s3_result = st.session_state.get("sec03_result")
            _s3_out = st.empty()
            with _s3_out.container():
                if _s3_result:
                    st.markdown(
                        f'<div class="gk-ai-output-box">'
                        f'<div style="color:#000000;font-size:0.87rem;line-height:1.8;font-weight:700;">'
                        f'{_s3_result}</div></div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<div class="gk-ai-output-box">'
                        '<div style="color:#94a3b8;font-size:0.85rem;text-align:center;'
                        'padding-top:50px;line-height:2.0;font-weight:700;">'
                        '📖 좌측에 질문을 입력하면<br>여기에 3단계 구조 답변이 표시됩니다.'
                        '</div></div>',
                        unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-03 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-04] 스마트 스캔 분석 허브 (5:5)
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-04")}<span class="gk-sec-title">④ 스마트 스캔 분석 허브</span></div>', unsafe_allow_html=True)
        st.markdown("스마트 스캔 — 보험금 청구 서류, 의무기록, 약관을 업로드하면 AI가 즉시 분석합니다.")

        _scan_left, _scan_right = st.columns([5, 5], gap="medium")
        with _scan_left:
            st.markdown('<div class="gk-scan-controller">', unsafe_allow_html=True)
            st.markdown(
                '<p style="font-size:0.88rem;font-weight:700;color:#000000;margin:0 0 10px 0;">'
                '📂 <strong>스마트 스캔 컨트롤러</strong>: PDF·JPG·PNG 업로드 또는 카메라 촬영. '
                '📱 모바일: 카메라 앱과 즉시 연동됩니다.</p>',
                unsafe_allow_html=True)
            _home_scan_file = st.file_uploader(
                "파일 업로드", type=["pdf", "jpg", "jpeg", "png", "webp"],
                key="home_scan_uploader", label_visibility="collapsed",
                help="최대 10MB · PDF/이미지 · 드래그 앤 드롭 가능",
                accept_multiple_files=False,
            )
            if _home_scan_file:
                _fsize_mb = len(_home_scan_file.getvalue()) / (1024 * 1024)
                if _fsize_mb > 10:
                    st.warning(f"⚠️ 파일 크기({_fsize_mb:.1f}MB) 초과")
                else:
                    st.success(f"✅ {_home_scan_file.name} ({_fsize_mb:.1f}MB) — 분석 준비 완료")
                    st.session_state["home_scan_file"] = _home_scan_file
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("⚡ 자료 추출 및 분석 시작", key="btn_home_scan_start",
                         use_container_width=True, type="primary"):
                _f = st.session_state.get("home_scan_file")
                if not _f:
                    st.warning("먼저 파일을 업로드해 주세요.")
                else:
                    with st.spinner("🔍 AI 분석 중..."):
                        try:
                            from modules.scan_engine import extract_and_analyze as _sea
                            _sea_result = _sea(
                                file_bytes=_f.getvalue(), filename=_f.name,
                                client=get_client(), session_state=st.session_state,
                            )
                            st.session_state["home_scan_result"] = _sea_result
                            st.session_state["gs_last_result"] = str(_sea_result)[:2000]
                            st.session_state["home_scan_scroll_trigger"] = True
                        except Exception:
                            try:
                                _raw = extract_pdf_chunks(_f, char_limit=8000)
                                _cli = get_client()
                                _resp = _cli.chat.completions.create(
                                    model=st.session_state.get("model_name", "gemini-2.0-flash"),
                                    messages=[{"role": "user", "content":
                                               f"다음 보험 서류를 분석하세요:\n\n{_raw}\n\n"
                                               "1. 문서 유형 및 핵심 내용 요약\n"
                                               "2. 보험금 청구 적정성 평가\n"
                                               "3. 주요 쟁점 및 대응 방안"}],
                                    max_tokens=2000,
                                )
                                _fb_text = _resp.choices[0].message.content
                                st.session_state["home_scan_result"] = _fb_text
                                st.session_state["gs_last_result"] = _fb_text[:2000]
                                st.session_state["home_scan_scroll_trigger"] = True
                            except Exception as _fb_err:
                                st.session_state["home_scan_result"] = f"⚠️ 분석 오류: {_fb_err}"
            st.markdown('</div>', unsafe_allow_html=True)

        with _scan_right:
            _scan_scroll = st.session_state.pop("home_scan_scroll_trigger", False)
            if _scan_scroll:
                import streamlit.components.v1 as _scan_c
                _scan_c.html(
                    '<script>(function(){var e=document.getElementById("home-scan-result-anchor");'
                    'if(e)e.scrollIntoView({behavior:"smooth",block:"start"})})();</script>',
                    height=0)
            st.markdown(
                '<div id="home-scan-result-anchor" style="font-size:0.9rem;font-weight:900;'
                'color:#CC0000;margin-bottom:8px;">🤖 AI 분석 스캔파일 요약</div>',
                unsafe_allow_html=True)
            _scan_result = st.session_state.get("home_scan_result")
            _scan_out = st.empty()
            with _scan_out.container():
                if _scan_result:
                    st.markdown(
                        f'<div class="gk-scan-output">'
                        f'<div style="color:#000000;font-size:0.87rem;line-height:1.8;'
                        f'font-weight:700;white-space:pre-wrap;">{_scan_result}</div></div>',
                        unsafe_allow_html=True)
                else:
                    st.markdown(
                        '<div class="gk-scan-output">'
                        '<div style="color:#94a3b8;font-size:0.85rem;text-align:center;'
                        'padding-top:50px;line-height:2.0;font-weight:700;">'
                        '📄 파일 업로드 후<br>'
                        '<strong style="color:#CC0000;">⚡ 분석 시작</strong>을 누르세요.<br><br>'
                        '<span style="font-size:0.78rem;color:#b0bec5;">'
                        '· 보험금 청구 적정성<br>· 법리적 쟁점 시뮬레이션<br>· 의무기록 핵심 키워드 요약'
                        '</span></div></div>',
                        unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-04 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-05] 네비게이션 게이트웨이
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-05")}<span class="gk-sec-title">⑤ 네비게이션 게이트웨이</span></div>', unsafe_allow_html=True)
        st.markdown("상세 컨설팅 및 AI 분석은 아래 섹션 카드에서 즉시 시작하세요.")

        _pf_c1, _pf_c2, _pf_c3 = st.columns(3, gap="medium")
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
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-05 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-06] 보험사 컨택 센터
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-06")}<span class="gk-sec-title">⑥ 보험사 컨택 센터</span></div>', unsafe_allow_html=True)

        _ins_contacts = [
            ("삼성생명",   "1588-3114", "https://www.samsunglife.com"),
            ("한화생명",   "1588-6363", "https://www.hanwhalife.com"),
            ("교보생명",   "1588-1001", "https://www.kyobo.co.kr"),
            ("NH농협생명", "1588-2100", "https://www.nhlife.co.kr"),
            ("신한라이프", "1588-5580", "https://www.shinhanlife.co.kr"),
            ("삼성화재",   "1588-5114", "https://www.samsungfire.com"),
            ("현대해상",   "1588-5656", "https://www.hi.co.kr"),
            ("DB손해보험", "1588-0100", "https://www.idbins.com"),
            ("KB손해보험", "1588-0114", "https://www.kbinsure.co.kr"),
            ("메리츠화재", "1566-7711", "https://www.meritzfire.com"),
        ]
        _contact_html = (
            '<div style="display:flex;flex-wrap:wrap;gap:8px;padding:4px 0;">'
        )
        for _cn, _cp, _cu in _ins_contacts:
            _contact_html += (
                f'<div style="border:1.5px solid #fca5a5;border-radius:8px;padding:8px 12px;'
                f'background:#fff5f5;min-width:140px;flex:1;">'
                f'<div style="font-weight:900;color:#000000;font-size:0.85rem;">{_cn}</div>'
                f'<div style="color:#CC0000;font-weight:700;font-size:0.82rem;">{_cp}</div>'
                f'</div>'
            )
        _contact_html += '</div>'
        st.markdown(_contact_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-06 닫기

        # ═══════════════════════════════════════════════════════════════
        # [GK-SEC-07] 관리자 게이트
        # ═══════════════════════════════════════════════════════════════
        st.markdown(f'<div class="gk-sec"><div style="position:relative;">{_bid("GK-SEC-07")}<span class="gk-sec-title">⑦ 관리자 게이트</span></div>', unsafe_allow_html=True)

        _adm_c1, _adm_c2 = st.columns([1, 1])
        with _adm_c1:
            if st.session_state.get("is_admin") or st.session_state.get("user_type") == "admin":
                st.markdown("**🔐 관리자 로그인 상태**")
                if st.button("⚙️ 관리자 패널", key="sec07_admin_panel", use_container_width=True):
                    _go_tab("admin")
            else:
                st.markdown("관리자 전용 — 권한 있는 계정으로 로그인하세요.")
        with _adm_c2:
            _show_bid_now = st.session_state.get("show_block_ids", False)
            if st.toggle("🔢 섹션 ID 표시", value=_show_bid_now, key="sec07_bid_toggle"):
                st.session_state["show_block_ids"] = True
            else:
                st.session_state["show_block_ids"] = False

        st.markdown('</div>', unsafe_allow_html=True)  # GK-SEC-07 닫기

