src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# Find home section
for i, l in enumerate(lines):
    if 'if cur ==' in l and 'home' in l and '"home"' in l:
        print(f'HOME: {i+1}: {l[:80]}')

# Find _build_injury_aware_system_instruction def
for i, l in enumerate(lines):
    if '_build_injury_aware_system_instruction' in l and 'def ' in l:
        print(f'SYS_INSTR_DEF: {i+1}: {l[:80]}')

# Find the trinity_ctx injection point inside that function
for i, l in enumerate(lines):
    if 'trinity_ai_context' in l and 'session_state' in l:
        print(f'TRINITY_CTX: {i+1}: {l[:80]}')
