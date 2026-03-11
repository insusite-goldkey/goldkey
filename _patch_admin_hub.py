with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# ── _adm_t4 탭 교체 범위: L43967(0-based 43966) ~ L44005(0-based 44004) ──
# L43967: "            with _adm_t4:"
# L44005: "            # ══════ 탭5 주석 ══════"
# → L44006: "            with _adm_t5:"

T4_START = 43966  # 0-based (L43967)
T4_END   = 44005  # 0-based (L44006) exclusive — 탭5 시작 바로 직전

# 검증
print(f"T4 start: {repr(lines[T4_START][:80])}")
print(f"T4 end  : {repr(lines[T4_END-1][:80])}")
print(f"After T4: {repr(lines[T4_END][:80])}")

NEW_T4 = '''            with _adm_t4:
                # ══════════════════════════════════════════════════════════
                # [GP-ADMIN] RAG 인덱스 관리 — 5:5 Split Layout
                # ══════════════════════════════════════════════════════════
                _rag_left, _rag_right = st.columns([5, 5])

                # ── [좌측] 스캔앱 연동 & 문서 관리 ──────────────────────
                with _rag_left:
                    st.markdown("#### 📂 스캔앱 연동 & 문서 관리")

                    # 스캔앱 연동 모듈 상태
                    _rag_st = _svc_status["rag"]
                    st.metric("인덱싱된 파일 수", f"{_rag_st['indexed_count']}개")

                    # 로딩된 문서 목록 실시간 노출
                    st.markdown("**📋 로딩된 문서 목록**")
                    _doc_list = st.session_state.get("_rag_local_docs", {})
                    _sup_docs = _rag_st.get("products", [])

                    if _doc_list or _sup_docs:
                        _all_docs = list(_doc_list.keys()) + [
                            f"{d.get('company','')} · {d.get('product','')}" for d in _sup_docs
                        ]
                        for _di, _dn in enumerate(_all_docs[:20]):
                            import hashlib as _hl
                            _uid = _hl.md5(_dn.encode()).hexdigest()[:8].upper()
                            _dc1, _dc2, _dc3 = st.columns([5, 2, 1])
                            _dc1.caption(f"📄 {_dn[:35]}")
                            _dc2.caption(f"🔑 ID: {_uid}")
                            if _dc3.button("🗑️", key=f"adm_doc_del_{_di}",
                                           help="삭제"):
                                if _dn in _doc_list:
                                    del st.session_state["_rag_local_docs"][_dn]
                                st.rerun()
                    else:
                        st.info("업로드된 문서가 없습니다.")

                    st.divider()
                    # 파일 업로드
                    _rag_upload = st.file_uploader(
                        "📎 문서 업로드 (PDF/TXT)",
                        type=["pdf", "txt"],
                        accept_multiple_files=True,
                        key="adm_rag_upload",
                    )
                    if _rag_upload:
                        if "_rag_local_docs" not in st.session_state:
                            st.session_state["_rag_local_docs"] = {}
                        for _f in _rag_upload:
                            _content = _f.read().decode("utf-8", errors="ignore")
                            _chunks = [_content[i:i+500] for i in range(0, len(_content), 500)]
                            st.session_state["_rag_local_docs"][_f.name] = _chunks
                        st.success(f"✅ {len(_rag_upload)}개 문서 로컬 인덱싱 완료")

                    # 섹터 지정 업로드
                    _rag_sector_sel = st.selectbox(
                        "섹터 지정",
                        ["auto (자동차·과실비율)", "income (소득통계)", "terms (약관)", "disability (장해)"],
                        key="adm_rag_sector",
                    )
                    _rag_sector_key = _rag_sector_sel.split(" ")[0]

                    # ⚡ 스캔 자료 추출 개시 버튼
                    st.markdown(
                        '<div style="margin-top:10px;"></div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "⚡ 스캔 자료 추출 개시",
                        key="adm_rag_extract",
                        use_container_width=True,
                        type="primary",
                    ):
                        _uploaded_count = len(st.session_state.get("_rag_local_docs", {}))
                        if _uploaded_count > 0:
                            # Supabase rag_documents 저장 시도
                            try:
                                import datetime as _dt_rag
                                _sb_rag = st.session_state.get("_sb_client")
                                if _sb_rag is None:
                                    from database import get_supabase_client as _gsb_rag
                                    _sb_rag = _gsb_rag()
                                _saved = 0
                                for _dname, _dchunks in st.session_state["_rag_local_docs"].items():
                                    for _ci, _chunk in enumerate(_dchunks[:10]):
                                        import hashlib as _hl2
                                        _uid2 = _hl2.md5(f"{_dname}_{_ci}".encode()).hexdigest()[:12].upper()
                                        _sb_rag.table("rag_documents").upsert({
                                            "id": _uid2,
                                            "title": f"{_dname} [청크 {_ci+1}]",
                                            "content": _chunk,
                                            "source": _dname,
                                            "sector": _rag_sector_key,
                                            "page_num": str(_ci + 1),
                                            "created_at": _dt_rag.datetime.now().isoformat(),
                                        }).execute()
                                        _saved += 1
                                st.session_state["_adm_rag_last_result"] = {
                                    "status": "success",
                                    "saved": _saved,
                                    "sector": _rag_sector_key,
                                    "ts": _dt_rag.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }
                                st.success(f"✅ {_saved}개 청크 Supabase RAG 저장 완료")
                                st.rerun()
                            except Exception as _rag_ex:
                                st.session_state["_adm_rag_last_result"] = {
                                    "status": "local_only",
                                    "saved": _uploaded_count,
                                    "sector": _rag_sector_key,
                                    "ts": "",
                                    "error": str(_rag_ex),
                                }
                                st.warning(f"클라우드 저장 실패 — 로컬 세션 보관 중 ({_rag_ex})")
                        else:
                            st.warning("업로드된 문서가 없습니다.")

                # ── [우측] 스캔 결과 보고서 ──────────────────────────────
                with _rag_right:
                    st.markdown("### 📑 Goldekey_AI-Masters 스캔 결과 보고서")

                    _rag_result = st.session_state.get("_adm_rag_last_result", {})
                    if _rag_result:
                        _r_status  = _rag_result.get("status", "")
                        _r_saved   = _rag_result.get("saved", 0)
                        _r_sector  = _rag_result.get("sector", "")
                        _r_ts      = _rag_result.get("ts", "")
                        _r_err     = _rag_result.get("error", "")

                        # 1. RAG 인덱스 저장 성공 여부
                        if _r_status == "success":
                            st.success(f"✅ RAG 인덱스 저장 성공 — {_r_saved}개 청크 저장됨")
                        else:
                            st.warning(f"⚠️ 로컬 보관 ({_r_saved}개) — 클라우드 저장 실패")
                            if _r_err:
                                st.caption(f"오류: {_r_err}")

                        # 2. GCS 이동 및 경로 결과
                        _gcs_path = f"gs://goldkey-rag/{_r_sector}/{_r_ts[:10].replace('-','')}_index.json" if _r_ts else "GCS 미연동"
                        st.markdown(
                            f'<div style="border:1px dashed #000;background:#FFF9C4;border-radius:8px;'
                            f'padding:10px 14px;margin:6px 0;font-size:0.83rem;font-weight:700;">'
                            f'☁️ GCS 경로: <code>{_gcs_path}</code><br>'
                            f'섹터: <b>{_r_sector}</b> | 저장 시각: {_r_ts or "미기록"}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        # 3. 자료 보관 상태 (영구 보존)
                        _perm_ok = _r_status == "success"
                        st.markdown(
                            f'<div style="border:1px dashed #000;background:{"#E8F5E9" if _perm_ok else "#FFEBEE"};'
                            f'border-radius:8px;padding:10px 14px;margin:6px 0;font-size:0.83rem;font-weight:700;">'
                            f'{"🔒 영구 보존 활성화 — Supabase 저장 완료" if _perm_ok else "⚠️ 영구 보존 미완료 — 세션 종료 시 소실 위험"}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                        # 4. 고유 파일 ID 목록
                        st.markdown("**🔑 고유 파일 ID 목록**")
                        _local_docs = st.session_state.get("_rag_local_docs", {})
                        if _local_docs:
                            import hashlib as _hl3
                            for _dn2 in list(_local_docs.keys())[:10]:
                                _uid3 = _hl3.md5(_dn2.encode()).hexdigest()[:12].upper()
                                st.code(f"ID: {_uid3}  |  파일: {_dn2[:50]}", language=None)
                        else:
                            st.info("파일 ID 없음 — 문서 업로드 후 추출 개시하세요.")
                    else:
                        st.info("아직 스캔 결과가 없습니다. 좌측에서 문서를 업로드 후 '⚡ 스캔 자료 추출 개시'를 누르세요.")

                    st.divider()

                    # ── 지능형 문서 검색 & 편집 시스템 ────────────────────
                    st.markdown("#### 🔍 지능형 문서 검색 & 편집")
                    _search_q = st.text_input(
                        "문서 검색",
                        key="adm_doc_search_q",
                        placeholder="예) 과실비율 직진 교차로 / 암 진단비 약관 / 소득 역산 기준",
                        help="자동완성: 과실비율·약관·소득통계·장해 키워드 권장",
                    )

                    if st.button("🔍 검색", key="adm_doc_search_btn", use_container_width=True):
                        if _search_q.strip():
                            _search_results = _rag_sector_query(_search_q, sector="auto", top_k=5)
                            if not _search_results:
                                _search_results = _rag_sector_query(_search_q, sector="terms", top_k=5)
                            st.session_state["_adm_search_results"] = _search_results
                            st.session_state["_adm_search_q"] = _search_q

                    _s_results = st.session_state.get("_adm_search_results", [])
                    if _s_results:
                        st.markdown(f"**검색 결과 {len(_s_results)}건** — *\"{st.session_state.get('_adm_search_q','')}\"*")
                        for _si, _sr in enumerate(_s_results):
                            with st.expander(f"#{_si+1} {_sr['title'][:50]}", expanded=(_si==0)):
                                _edit_key = f"adm_doc_edit_{_si}"
                                _edit_content = st.text_area(
                                    "내용 (수정 가능)",
                                    value=_sr["content"],
                                    height=100,
                                    key=_edit_key,
                                )
                                _btn_c1, _btn_c2 = st.columns(2)
                                with _btn_c1:
                                    if st.button("📝 수정 저장", key=f"adm_doc_save_{_si}", type="primary"):
                                        try:
                                            _sb_edit = st.session_state.get("_sb_client")
                                            if _sb_edit:
                                                _sb_edit.table("rag_documents").update({
                                                    "content": _edit_content,
                                                }).eq("title", _sr["title"]).execute()
                                                st.success("✅ DB 수정 완료")
                                            else:
                                                # 로컬 세션 업데이트
                                                _s_results[_si]["content"] = _edit_content
                                                st.session_state["_adm_search_results"] = _s_results
                                                st.success("✅ 로컬 수정 완료")
                                        except Exception as _edit_ex:
                                            st.error(f"수정 실패: {_edit_ex}")
                                with _btn_c2:
                                    if st.button("🗑️ 삭제", key=f"adm_doc_del2_{_si}"):
                                        try:
                                            _sb_del = st.session_state.get("_sb_client")
                                            if _sb_del:
                                                _sb_del.table("rag_documents").delete().eq(
                                                    "title", _sr["title"]
                                                ).execute()
                                                st.success("✅ DB 삭제 완료")
                                                st.session_state["_adm_search_results"] = [
                                                    r for r in _s_results if r["title"] != _sr["title"]
                                                ]
                                                st.rerun()
                                        except Exception as _del_ex:
                                            st.error(f"삭제 실패: {_del_ex}")

'''

lines = lines[:T4_START] + [NEW_T4] + lines[T4_END:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE: _adm_t4 RAG index tab replaced with 5:5 layout + search/edit system")
