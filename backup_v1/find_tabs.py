import re
with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, line in enumerate(lines, 1):
    m = re.search(r'if cur == "(\w+)"', line)
    if m:
        print(f'{i}: {m.group(0)}')
