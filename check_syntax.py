import ast, sys
out = open('d:/CascadeProjects/syn_result.txt', 'w', encoding='utf-8')
try:
    src = open('d:/CascadeProjects/app.py', encoding='utf-8').read()
    ast.parse(src)
    out.write('SYNTAX OK\n')
except SyntaxError as e:
    out.write(f'SyntaxError at line {e.lineno}: {e.msg}\n')
    lines = src.splitlines()
    start = max(0, e.lineno - 3)
    end   = min(len(lines), e.lineno + 2)
    for i, ln in enumerate(lines[start:end], start=start+1):
        marker = ' >>>' if i == e.lineno else '    '
        out.write(f'{marker} {i:6}: {ln}\n')
out.close()
