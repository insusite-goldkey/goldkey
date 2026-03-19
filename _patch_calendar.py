"""
_patch_calendar.py  — app.py 캘린더 섹션 교체 패치
"""
SRC = 'D:/CascadeProjects/app.py'

with open(SRC, encoding='utf-8-sig') as f:
    src = f.read()

lines = src.split('\n')

# Find calendar section boundaries (0-indexed)
cal_start = None
cal_end   = None
for i, l in enumerate(lines):
    if '# ── [달력] AgentCalendarView' in l:
        cal_start = i
    if cal_start and i > cal_start and 'st.stop()' in l:
        for j in range(i + 1, min(i + 6, len(lines))):
            if lines[j].strip():
                if 'GP-HOME-RENDER' in lines[j] or '══' in lines[j]:
                    cal_end = i
                break
        if cal_end:
            break

assert cal_start is not None and cal_end is not None, f"Range not found: {cal_start}, {cal_end}"
print(f"Replacing lines {cal_start+1}–{cal_end+1}")

NEW_BLOCK = """\
    # ── [달력] 스마트 캘린더 엔진 v2 (calendar_engine.py) ─────────────────
    if cur == "calendar":
        from calendar_engine import render_smart_calendar as _render_smart_cal
        with st.spinner('Goldkey AI Masters 2026 구동중입니다. 잠시 기다려주세요!'):
            st.markdown(f\"\"\"
            <div class="gk-sky-trust gp-interactive" style="position:relative;border-radius:12px;padding:14px 20px;margin-bottom:10px;">
            {_bid('3-1-1')}
            <div class="gk-st-title">📅 스마트 상담 일정 관리</div>
            <div style="font-size:0.8rem;margin-top:4px;">고객 방문 · 계약 일정 · 해시태그 자동 분류 · 캘린더 연동</div>
            </div>\"\"\", unsafe_allow_html=True)
            _cal_back, _ = st.columns([1, 5])
            with _cal_back:
                if st.button("← 인트로", key="cal_back_btn", use_container_width=True):
                    _go_tab("intro")
            _cal_customers = []
            for _c in st.session_state.get("customers", []):
                _name = _c.get("name", "") or _c.get("cname", "")
                _cid  = _c.get("person_id", "") or _c.get("cust_id", "") or _c.get("id", "")
                if _name:
                    _cal_customers.append({"id": _cid, "name": _name, "person_id": _cid})
            _render_smart_cal(
                agent_id=st.session_state.get("agent_id", ""),
                customers=_cal_customers,
            )
        st.stop()"""

new_lines = lines[:cal_start] + NEW_BLOCK.split('\n') + lines[cal_end + 1:]
result = '\n'.join(new_lines)

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(result)

print(f"Done. Lines: {len(lines)} → {len(new_lines)}")
