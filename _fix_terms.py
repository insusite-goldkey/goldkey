import re

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.splitlines(keepends=True)

# 22912~22970 (0-indexed: 22911~22969) 구간을 교체
# 실제 인덴테이션: 16칸 (0-indexed line 22911 기준)
start = 22911  # 0-indexed, "                # ── 4개 항목 세로 배치"
end   = 22970  # 0-indexed, "                    st.success(...)  중복행

# 교체할 새 코드 (12칸 인덴테이션)
new_block = '''\
            # ── 4개 항목 세로 배치 + 구분선 ──────────────────────────────
            _terms_list = [
                ("t1", "[필수]", "서비스 이용약관 동의",              "#ef4444", "#1e293b"),
                ("t2", "[필수]", "개인정보 수집 및 이용 동의",        "#ef4444", "#1e293b"),
                ("t3", "[필수]", "민감정보(의료·건강기록) AI 분석 동의", "#ef4444", "#0369a1"),
                ("t4", "[필수]", "맞춤형 보험·건강 정보 알림 수신 동의", "#ef4444", "#475569"),
            ]
            _terms_changed_top = False
            for _i, (_ttk, _tbadge, _ttitle, _tbadge_color, _tcolor) in enumerate(_terms_list):
                _tcb_col, _tlbl_col = st.columns([1, 7], gap="small")
                with _tcb_col:
                    _tcv = st.checkbox("", value=bool(_tr_top.get(_ttk, False)),
                                       key=f"_terms_top_cb_{_ttk}",
                                       label_visibility="collapsed")
                with _tlbl_col:
                    _is_checked = _tcv
                    _row_bg = "#E3F2FD" if _is_checked else "transparent"
                    st.markdown(
                        f"<div style='padding:3px 6px;border-radius:6px;"
                        f"background:{_row_bg};"
                        f"transition:background 0.2s ease;"
                        f"font-size:0.82rem;color:#000000;font-weight:700;line-height:1.5;'>"
                        f"<span style='color:#e53e3e;font-size:0.70rem;"
                        f"font-weight:800;margin-right:4px;'>{_tbadge}</span>"
                        f"{_ttitle}</div>",
                        unsafe_allow_html=True,
                    )
                if _tcv != bool(_tr_top.get(_ttk, False)):
                    st.session_state["_lp_terms"][_ttk] = _tcv
                    _terms_changed_top = True
                if _i < len(_terms_list) - 1:
                    st.markdown("<hr style='border:none;border-top:1px solid rgba(200,200,200,0.7);margin:5px 0 5px 0;'>",
                                unsafe_allow_html=True)
            if _terms_changed_top:
                st.rerun()

            # ── [가이딩 프로토콜 제130조] 데이터 보호 특칙 고지 ──────────────
            st.markdown("<hr style='border:none;border-top:1px solid rgba(0,77,64,0.25);margin:10px 0 4px 0;'>", unsafe_allow_html=True)
            with st.expander("🔒 제130조 데이터 보호 특칙 (의료 데이터 보안 고지)", expanded=False):
                st.markdown("""
<div style='font-size:0.71rem;color:#1e3a5f;line-height:1.65;'>
  회사는 이용자가 업로드하는 <strong>의무기록 및 진단서의 민감정보</strong>를 보호하기 위해,
  수집 단계에서 <strong>성명 및 주민등록번호 뒷자리를 자동 비식별화(Masking)</strong> 처리합니다.<br>
  모든 의료 데이터는 국제 표준인 <strong>AES-256 방식으로 암호화</strong>되어 외부와 격리된
  <strong>보안 스토리지(GCS Security Bucket)</strong>에 저장되며, 엄격한 접근 권한 통제를 통해
  <strong>마스터 본인 외에는 누구도 열람할 수 없음</strong>을 보장합니다.
  <div style='font-size:0.68rem;color:#374151;margin-top:6px;text-align:right;font-style:italic;'>
    📋 goldkey_Ai_masters2026 가이딩 프로토콜 제130조 §1~§3 준수
  </div>
</div>""", unsafe_allow_html=True)

            # ── 통합 박스 닫기 ────────────────────────────────────────────
            st.markdown("</div>", unsafe_allow_html=True)

            # ── 약관동의 완료 시에만 탭 표시 ─────────────────────────────
            if _req_agreed_top:
                if st.session_state.pop("_terms_agreed_notify", False):
                    st.success("✅ 동의 완료! 아래 로그인 탭에서 로그인하세요.", icon="🔓")
'''

before = ''.join(lines[:start])
after  = ''.join(lines[end:])
result = before + new_block + '\n' + after

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(result)
print(f"DONE: replaced lines {start+1}~{end} ({end-start} lines) with {new_block.count(chr(10))} lines")
