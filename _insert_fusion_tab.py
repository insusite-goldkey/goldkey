# -*- coding: utf-8 -*-
"""GK-SEC-10 diagnosis 구간에 법령·KCD 융합 탭을 삽입하고,
   전역 CSS에 word-break:keep-all + box-sizing 추가"""
import sys

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# ─── 1. 면책 문구 앞에 융합 탭 삽입 ──────────────────────────────────────
ANCHOR_LAW = "        # ── 면책 문구 ──"
assert src.count(ANCHOR_LAW) == 1, f"anchor count: {src.count(ANCHOR_LAW)}"

FUSION_TAB = '''        # ── 법령·KCD 융합 탭 ─────────────────────────────────────────────────
        st.markdown("<hr style='border:none;border-top:2px dashed #000;margin:24px 0;'>",
                    unsafe_allow_html=True)
        st.markdown(
            "<div style='font-size:1.0rem;font-weight:900;color:#1e1b4b;margin-bottom:8px;'>"
            "⚖️🔬 법령 &amp; 질병코드 융합 사령부</div>"
            "<div style='font-size:0.78rem;color:#64748b;margin-bottom:12px;word-break:keep-all;'>"
            "의학 진단(KCD) + 관련 법령·판례가 한 화면에 연결됩니다. "
            "질병 코드 선택 시 연관 법령이 자동으로 연결되며, "
            "법령 검색창에서 직접 보험업법·상법 조문을 검색할 수 있습니다."
            "</div>",
            unsafe_allow_html=True,
        )

        _kcd_from_scan = st.session_state.get("scan_client_kcd_code", "")
        _kcd_name_from_scan = st.session_state.get("scan_client_kcd_name", "")

        _fu_c1, _fu_c2 = st.columns([1, 1], gap="medium")
        with _fu_c1:
            st.markdown(
                "<div style='background:#f0fdf4;border:1px dashed #000;border-radius:10px;"
                "padding:12px 16px;margin-bottom:8px;'>"
                "<div style='font-size:0.86rem;font-weight:900;color:#166534;margin-bottom:6px;'>"
                "🔬 KCD 질병코드 조회</div>",
                unsafe_allow_html=True,
            )
            if _kcd_from_scan:
                st.markdown(
                    f"<div style='font-size:0.8rem;color:#0369a1;background:#dbeafe;"
                    f"border-radius:6px;padding:4px 10px;margin-bottom:6px;word-break:keep-all;'>"
                    f"🔗 GK-SEC-01 연동 — KCD: <b>{_kcd_from_scan}</b>"
                    f"{(' · ' + _kcd_name_from_scan) if _kcd_name_from_scan else ''}</div>",
                    unsafe_allow_html=True,
                )
            _fu_kcd_sel = render_kcd_autocomplete(
                label="질병 검색 (KCD 자동완성)",
                session_key="sec10_fusion_kcd",
                placeholder="예) 유방암, 뇌경색, C50, I21…",
                autofill_kcd_key="sec10_fusion_kcd_code",
                show_coverage=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

        with _fu_c2:
            _fu_kcd_code = st.session_state.get(
                "sec10_fusion_kcd_code",
                _kcd_from_scan or "",
            )
            render_law_search(
                session_key="sec10_law",
                kcd_code=_fu_kcd_code,
                show_linked=True,
            )

'''

new_src = src.replace(ANCHOR_LAW, FUSION_TAB + ANCHOR_LAW, 1)
assert new_src != src, "fusion tab replace had no effect"

# ─── 2. 전역 CSS 블록에 word-break:keep-all + box-sizing 추가 ────────────
# main() 내부 첫 st.markdown CSS 블록 — Streamlit 기본 UI 숨김 바로 뒤
CSS_ANCHOR = "st.session_state[\"_lp_landing\"] = True"
assert new_src.count(CSS_ANCHOR) >= 1

GLOBAL_CSS = """
    st.markdown(\"\"\"<style>
/* [GP-44] 전역 반응형 + 태블릿 최적화 CSS */
*, *::before, *::after { box-sizing: border-box !important; }
html, body { overflow-x: hidden !important; }
* { word-break: keep-all; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.18); border-radius: 4px; }
::-webkit-scrollbar-track { background: transparent; }
@media (max-width: 900px) {
    .stColumns > div { min-width: 0 !important; }
    .element-container { padding: 0 2px !important; }
}
</style>\"\"\", unsafe_allow_html=True)
    """

# CSS가 이미 삽입됐는지 확인 (중복 방지)
if "box-sizing: border-box !important" not in new_src:
    # _lp_landing 라인 바로 다음에 삽입
    new_src = new_src.replace(
        CSS_ANCHOR,
        CSS_ANCHOR + "\n" + GLOBAL_CSS,
        1,
    )

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(new_src)
lines = new_src.split('\n')
print(f"OK total lines: {len(lines)}")
