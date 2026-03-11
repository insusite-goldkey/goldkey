lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
for i, ln in enumerate(lines):
    if 'SYSTEM_PROMPT' in ln or 'system_prompt' in ln or '_GP_SYSTEM' in ln or 'MASTER_PROMPT' in ln:
        if 'def ' in ln or '=' in ln or '"""' in ln:
            print(f'L{i+1}: {ln[:120].rstrip()}')
