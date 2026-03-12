content = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# ── 문제: for _cr in _cust_rows: 루프 안에 _sick_guide 코드가 혼입됨
# 원래 올바른 코드:
#   for _cr in _cust_rows:
#       _cust_options_map[_cust_label(_cr)] = _cr
# 현재 잘못된 코드:
#   for _cr in _cust_rows:
#       _sick_color = ...
#       _sick_bg    = ...
#       ...
#       st.markdown(...)

# 잘못된 for 루프 내용 전체 교체
OLD = '''            _cust_options_map = {"✏️ 고객 입력 & 검색": None}
            for _cr in _cust_rows:
                _sick_color = "#9a3412" if "⚠️" in _sick_guide_text else "#14532d"
                _sick_bg    = "#fff7ed" if "⚠️" in _sick_guide_text else "#f0fdf4"
                _sick_bdr   = "#f97316" if "⚠️" in _sick_guide_text else "#22c55e"
                st.markdown(
                    f\'<div style="background:{_sick_bg};border:1.5px solid {_sick_bdr};border-radius:8px;\'
                    f\'padding:8px 12px;font-size:0.82rem;font-weight:700;color:{_sick_color};\'
                    f\'white-space:pre-line;margin-bottom:8px;">{_sick_guide_text}</div>\',
                    unsafe_allow_html=True)'''

NEW = '''            _cust_options_map = {"✏️ 고객 입력 & 검색": None}
            for _cr in _cust_rows:
                _cust_options_map[_cust_label(_cr)] = _cr'''

if OLD in content:
    content = content.replace(OLD, NEW)
    open('D:/CascadeProjects/app.py', 'w', encoding='utf-8-sig').write(content)
    print('FIXED: for loop restored')
else:
    # 부분 확인
    idx = content.find('_cust_options_map = {"✏️ 고객 입력 & 검색": None}')
    if idx != -1:
        line = content[:idx].count('\n') + 1
        snip = content[idx:idx+400]
        print(f'Found at L{line}:')
        print(repr(snip))
    else:
        print('NOT FOUND — check manually')
