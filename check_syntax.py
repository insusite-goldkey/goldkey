import ast
result = []
try:
    with open('app.py', encoding='utf-8') as f:
        src = f.read()
    ast.parse(src)
    result.append('SYNTAX OK')
except SyntaxError as e:
    result.append('SyntaxError line ' + str(e.lineno) + ': ' + str(e.msg))
    lines = src.splitlines()
    start = max(0, e.lineno - 4)
    end = min(len(lines), e.lineno + 3)
    for i in range(start, end):
        marker = '>>>' if (i + 1) == e.lineno else '   '
        result.append(marker + ' ' + str(i+1) + ': ' + lines[i])
with open('syn_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))
