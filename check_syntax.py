import ast, traceback
result = []
try:
    src = open('d:/CascadeProjects/app.py', encoding='utf-8-sig', errors='replace').read()
    try:
        ast.parse(src)
        result.append('SYNTAX OK')
    except SyntaxError as e:
        result.append(f'SyntaxError at line {e.lineno}: {e.msg}')
        lines = src.splitlines()
        start = max(0, e.lineno - 3)
        end   = min(len(lines), e.lineno + 2)
        for i, ln in enumerate(lines[start:end], start=start+1):
            marker = ' >>>' if i == e.lineno else '    '
            result.append(f'{marker} {i:6}: {ln}')
except Exception:
    result.append('SCRIPT ERROR:')
    result.append(traceback.format_exc())
open('d:/CascadeProjects/syn_result.txt', 'w', encoding='utf-8').write('\n'.join(result))
