lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
# t9 관리자 섹터 내부 st.tabs 위치 찾기
in_t9 = False
for i, ln in enumerate(lines):
    if 'if cur == "t9"' in ln:
        in_t9 = True
    if in_t9 and i > 43361:
        if 'st.tabs(' in ln or 'adm_tab' in ln.lower() or 'admin.*tab' in ln:
            print(f'L{i+1}: {ln[:120].rstrip()}')
        # 다음 if cur == 또는 st.stop()
        if i > 43361 and ('if cur ==' in ln or (ln.strip() == 'st.stop()' and i > 43370)):
            if i > 43500:
                print(f'--- END at L{i+1} ---')
                break
