import ast, sys
try:
    src = open('app.py', encoding='utf-8-sig').read()
    lines = src.splitlines()
    ast.parse(src)
    result = 'AST OK\n'
except SyntaxError as e:
    ln = e.lineno or 0
    ctx = '\n'.join(
        f'  {i+1}: {lines[i]}'
        for i in range(max(0, ln-4), min(len(lines), ln+3))
    )
    result = f'SyntaxError line {ln}: {e.msg}\nText: {e.text}\nContext:\n{ctx}\n'
with open('ast_result2.txt', 'w', encoding='utf-8') as f:
    f.write(result)
