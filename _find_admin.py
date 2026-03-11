lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
hits = []
for i, ln in enumerate(lines):
    lo = ln.lower()
    if ('admin' in lo or '관리자' in ln) and ('cur ==' in ln or 'def ' in lo or 'tab_key' in lo or 'if cur' in ln):
        hits.append(f'L{i+1}: {ln[:120].rstrip()}')
for h in hits[:40]:
    print(h)
