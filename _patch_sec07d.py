# -*- coding: utf-8 -*-
"""
GK-SEC-02 med_econ 탭: 역산 결과 직후 소득통계 RAG 참조 블록 삽입
AI 보고서: _render_report_send_ui 내에 약관 페이지 주석 자동 표기 로직 추가
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ══════════════════════════════════════════════════════════════════════════════
# PATCH 1: med_econ 탭 — 역산 결과 이후 소득통계 RAG 추천 블록 삽입
# 삽입 앵커: "# ── 상세 지표 expander ─────" 바로 위
# ══════════════════════════════════════════════════════════════════════════════
ANCHOR_MECON = "            # ── 상세 지표 expander ────────────────────────────────────────\n"
if ANCHOR_MECON not in content:
    print("ERROR: med_econ expander anchor not found")
    exit(1)

RAG_MECON_BLOCK = '''            # ── [RAG-SEC-02] 소득통계 참조 — 적정 보장 금액 추천 ─────────────
            try:
                _rag_income_refs = _rag_sector_query(
                    f"월소득 {_me_r['monthly_income']//10000}만원 보장 설계",
                    sector="income", top_k=2,
                )
                if _rag_income_refs:
                    st.markdown(
                        '<div style="border:1px dashed #1565C0;background:#E3F2FD;'
                        'border-radius:8px;padding:10px 14px;margin:8px 0;'
                        'font-size:0.82rem;font-weight:700;color:#0D47A1;">'
                        '📊 <b>[RAG 소득통계 참조]</b> 동일 소득 구간 설계 가이드<br>'
                        + "".join(
                            f'<div style="margin-top:6px;padding:6px 10px;background:#fff;'
                            f'border-radius:6px;border-left:3px solid #1565C0;">'
                            f'<b>{_r["title"]}</b><br>'
                            f'<span style="font-weight:400;color:#333;">{_r["content"]}</span>'
                            f'<br><span style="font-size:0.7rem;color:#888;">출처: {_r["source"]}'
                            f'{(" · " + str(_r["page"]) + "p") if _r.get("page") else ""}</span>'
                            f'</div>'
                            for _r in _rag_income_refs
                        )
                        + '</div>',
                        unsafe_allow_html=True,
                    )
            except Exception:
                pass

'''

content = content.replace(ANCHOR_MECON, RAG_MECON_BLOCK + ANCHOR_MECON, 1)
print("PATCH 1 (med_econ RAG) OK")

# ══════════════════════════════════════════════════════════════════════════════
# PATCH 2: AI 보고서 약관 페이지 주석 자동 표기 함수 추가
# _rag_annotate_report: 보고서 텍스트에서 담보명을 감지하고 약관 근거 주석 삽입
# ══════════════════════════════════════════════════════════════════════════════
ANCHOR_REPORT_FUNC = "def _render_report_send_ui("
if ANCHOR_REPORT_FUNC not in content:
    print("WARNING: _render_report_send_ui not found, skipping report annotation patch")
else:
    REPORT_RAG_FUNC = '''
def _rag_annotate_report(report_text: str) -> str:
    """AI 보고서 텍스트에 약관 근거(몇 조, 몇 페이지) 주석을 자동 삽입.

    - 담보명 키워드를 감지하여 RAG에서 해당 약관 조항 검색
    - 결과를 [※ 약관 근거: OO조 OO페이지] 형태로 텍스트 끝에 추가
    - 매칭 없으면 원본 텍스트 그대로 반환
    """
    if not report_text or len(report_text) < 50:
        return report_text

    _COVERAGE_KEYWORDS = [
        "암진단비", "뇌혈관", "심장", "입원일당", "수술비", "후유장해",
        "사망보험금", "실손", "간병비", "치매", "장기요양",
    ]
    _found_kws = [kw for kw in _COVERAGE_KEYWORDS if kw in report_text]
    if not _found_kws:
        return report_text

    _annotations = []
    for _kw in _found_kws[:3]:  # 최대 3개 담보 주석
        try:
            _refs = _rag_sector_query(_kw + " 약관 조항", sector="terms", top_k=1)
            if _refs and _refs[0].get("source"):
                _r = _refs[0]
                _ann = f"[※ {_kw} 약관 근거: {_r['source']}"
                if _r.get("page"):
                    _ann += f" {_r['page']}페이지"
                _ann += "]"
                _annotations.append(_ann)
        except Exception:
            pass

    if _annotations:
        report_text += "\n\n" + " / ".join(_annotations)
    return report_text


'''
    idx_report = content.find(ANCHOR_REPORT_FUNC)
    content = content[:idx_report] + REPORT_RAG_FUNC + content[idx_report:]
    print("PATCH 2 (report RAG annotation) OK")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: all patches applied")
