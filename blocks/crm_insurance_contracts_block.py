# [BLOCK] crm_insurance_contracts_block.py — 보험 가입 관리 3파트 파이프라인
import streamlit as st
import datetime
import uuid

_CSS = """<style>
.ic-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;max-height:220px;overflow-y:auto;border:1px dashed #000;border-radius:8px;margin-bottom:8px;}
.ic-table{border-collapse:collapse;width:max-content;min-width:100%;font-size:clamp(0.68rem,2vw,0.78rem);}
.ic-table th{position:sticky;top:0;z-index:2;background:#dbeafe;color:#1e3a8a;padding:5px 9px;font-weight:900;white-space:nowrap;border-bottom:2px solid #93c5fd;}
.ic-table td{padding:4px 9px;white-space:nowrap;border-bottom:1px solid #e2e8f0;color:#334155;max-width:180px;overflow:hidden;text-overflow:ellipsis;}
.ic-table tr:nth-child(even) td{background:#f8fafc;}
.ic-date-cell{color:#dc2626!important;font-weight:900!important;min-width:96px;}
[data-testid="stExpander"] [data-testid="stForm"]{max-width:100%!important;margin:0!important;box-shadow:none!important;border:1px dashed #000!important;border-radius:8px!important;padding:10px 14px!important;}
</style>"""

_CH = ["계약자","피보험자","보험회사","상품명","증권번호","계약년월","만기년월","월보험료","비고"]
_CF = ["policyholder","insured","insurer","product_name","policy_no","contract_ym","expiry_ym","monthly_premium","memo"]

def _load(sb, agent_id, person_id):
    try:
        return (sb.table("gk_insurance_contracts").select("*")
                .eq("agent_id",agent_id).eq("person_id",person_id)
                .order("created_at").execute()).data or []
    except Exception:
        return []

def _upsert(sb, row):
    try:
        sb.table("gk_insurance_contracts").upsert(row).execute()
        return True
    except Exception as e:
        st.error(f"저장 오류: {e}"); return False

def _move(sb, cid, agent_id, new_part, terminated_at=None):
    try:
        u = {"part": new_part, "updated_at": datetime.datetime.utcnow().isoformat()}
        if terminated_at: u["terminated_at"] = str(terminated_at)
        elif new_part != "C": u["terminated_at"] = None
        sb.table("gk_insurance_contracts").update(u).eq("id",cid).eq("agent_id",agent_id).execute()
        st.cache_data.clear(); return True
    except Exception as e:
        st.error(f"이동 오류: {e}"); return False

def _tbl(rows, is_c=False):
    if not rows:
        return "<div style='font-size:0.78rem;color:#94a3b8;padding:12px;'>등록된 계약이 없습니다.</div>"
    hdrs = (["🗓 해지확인일"]+_CH) if is_c else _CH
    flds = (["terminated_at"]+_CF) if is_c else _CF
    ths = "".join(f"<th>{h}</th>" for h in hdrs)
    trs = ""
    for r in rows:
        tds = "".join(f'<td{"  class=\"ic-date-cell\"" if f=="terminated_at" else ""}>{r.get(f) or ""}</td>' for f in flds)
        trs += f"<tr>{tds}</tr>"
    return f"<div class='ic-wrap'><table class='ic-table'><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table></div>"

def _add_form(sb, agent_id, person_id, part, kpfx):
    lbl = "➕ 해지/승환 계약 직접 등록" if part=="C" else f"➕ 새 {part}파트 계약 추가"
    with st.expander(lbl):
        with st.form(f"ic_add_{part}_{kpfx}"):
            _tdc = None
            if part == "C":
                _tdc = st.date_input("🗓 해지/승환 확인일 (필수)", value=datetime.date.today(), key=f"ic_tdc_{kpfx}")
            c1, c2 = st.columns(2)
            with c1:
                _pc  = st.text_input("계약자",  placeholder="계약자명",   key=f"ic_pc_{kpfx}")
                _ins = st.text_input("피보험자", placeholder="피보험자명", key=f"ic_ins_{kpfx}")
                _co  = st.text_input("보험회사", placeholder="삼성생명",   key=f"ic_co_{kpfx}")
                _pn  = st.text_input("상품명",   placeholder="종신/암 등", key=f"ic_pn_{kpfx}")
            with c2:
                _no  = st.text_input("증권번호", placeholder="선택입력",   key=f"ic_no_{kpfx}")
                _cym = st.text_input("계약년월", placeholder="2023-01",    key=f"ic_cym_{kpfx}")
                _eym = st.text_input("만기년월", placeholder="100세만기",  key=f"ic_eym_{kpfx}")
                _mp  = st.text_input("월보험료", placeholder="120,000원",  key=f"ic_mp_{kpfx}")
            _memo = st.text_input("비고", placeholder="메모", key=f"ic_memo_{kpfx}")
            if st.form_submit_button("💾 저장", type="primary", use_container_width=True):
                row = {"id":str(uuid.uuid4()),"agent_id":agent_id,"person_id":person_id,
                       "part":part,"policyholder":_pc,"insured":_ins,"insurer":_co,
                       "product_name":_pn,"policy_no":_no,"contract_ym":_cym,
                       "expiry_ym":_eym,"monthly_premium":_mp,"memo":_memo,
                       "terminated_at":str(_tdc) if _tdc else None,
                       "created_at":datetime.datetime.utcnow().isoformat(),
                       "updated_at":datetime.datetime.utcnow().isoformat()}
                if _upsert(sb, row):
                    st.success("✅ 저장 완료!"); st.rerun()

def _actions(rows, sb, agent_id, part, kpfx):
    if not rows: return
    st.markdown("<div style='font-size:0.7rem;color:#94a3b8;margin-bottom:4px;'>※ 아래 버튼으로 파트 이동·해지 처리</div>", unsafe_allow_html=True)
    for i, r in enumerate(rows):
        cid  = r.get("id","")
        sfx  = f"{kpfx}_{i}_{cid[:6]}"
        lbl  = f"[{i+1}] {r.get('insurer','')} {(r.get('product_name') or '')[:10]}"
        if part in ("A","B"):
            c0,c1,c2 = st.columns([4,1,1])
            with c0: st.caption(lbl)
            with c1:
                dest = "B" if part=="A" else "A"
                if st.button(f"→{dest}", key=f"ic_mv_{sfx}", use_container_width=True):
                    if _move(sb,cid,agent_id,dest): st.success(f"{dest}파트 이동!"); st.rerun()
            with c2:
                with st.popover("🚫해지", use_container_width=True):
                    _td = st.date_input("해지/승환 확인일", value=datetime.date.today(), key=f"ic_td_{sfx}")
                    if st.button("✅ C파트 이관", key=f"ic_term_{sfx}", type="primary", use_container_width=True):
                        if _move(sb,cid,agent_id,"C",_td): st.success("C파트 이관 완료!"); st.rerun()
        else:  # C part
            c0,c1 = st.columns([5,2])
            with c0: st.caption(f"[{i+1}] 🗓{r.get('terminated_at','')} {r.get('insurer','')} {(r.get('product_name') or '')[:8]}")
            with c1:
                with st.popover("↩복구", use_container_width=True):
                    _tgt = st.radio("복구 파트", ["A","B"], key=f"ic_rtgt_{sfx}", horizontal=True)
                    if st.button("✅ 복구 확정", key=f"ic_rr_{sfx}", type="primary", use_container_width=True):
                        if _move(sb,cid,agent_id,_tgt): st.success(f"{_tgt}파트 복구!"); st.rerun()

def render_insurance_contracts(person_id: str, agent_id: str, sb, person_name: str = "") -> None:
    """보험 가입 관리 — 3파트(A취급/B타부점/C해지) UI"""
    st.markdown(_CSS, unsafe_allow_html=True)
    _nm = f" — {person_name}" if person_name else ""
    st.markdown(
        f"<div style='font-size:clamp(0.8rem,3vw,0.92rem);font-weight:900;color:#1e3a8a;"
        f"border-bottom:2px solid #bfdbfe;padding-bottom:4px;margin-bottom:10px;'>"
        f"📋 보험 가입 관리{_nm}</div>",
        unsafe_allow_html=True,
    )
    if not person_id:
        st.info("좌측에서 고객을 선택하면 보험 계약 목록이 나타납니다.")
        return

    all_c = _load(sb, agent_id, person_id)
    pa = [c for c in all_c if c.get("part")=="A"]
    pb = [c for c in all_c if c.get("part")=="B"]
    pc = sorted([c for c in all_c if c.get("part")=="C"],
                key=lambda x: x.get("terminated_at") or "", reverse=True)
    kp = f"{agent_id[:4]}{person_id[:4]}"

    ta, tb, tc = st.tabs([
        f"🟦 A파트 · 내 취급계약 ({len(pa)}건)",
        f"🟨 B파트 · 타부점 계약 ({len(pb)}건)",
        f"🔴 C파트 · 해지/승환 ({len(pc)}건)",
    ])
    with ta:
        st.markdown(_tbl(pa), unsafe_allow_html=True)
        _actions(pa, sb, agent_id, "A", kp+"a")
        _add_form(sb, agent_id, person_id, "A", kp+"fa")
    with tb:
        st.markdown(_tbl(pb), unsafe_allow_html=True)
        _actions(pb, sb, agent_id, "B", kp+"b")
        _add_form(sb, agent_id, person_id, "B", kp+"fb")
    with tc:
        st.markdown(_tbl(pc, is_c=True), unsafe_allow_html=True)
        _actions(pc, sb, agent_id, "C", kp+"c")
        _add_form(sb, agent_id, person_id, "C", kp+"fc")
