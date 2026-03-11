lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
# 각 탭 시작 라인 찾기 (with _adm_t1 ~ _adm_t5)
for i, ln in enumerate(lines):
    if 43860 < i < 44480:
        stripped = ln.strip()
        if stripped.startswith('with _adm_t'):
            print(f'L{i+1}: {ln[:80].rstrip()}')
        if 'st.divider()' in ln and i > 44000:
            print(f'L{i+1}: DIVIDER (inner_tabs boundary)')
            break
