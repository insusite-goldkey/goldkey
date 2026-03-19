import ast, sys
try:
    src = open('app.py', 'r', encoding='utf-8-sig').read()
    ast.parse(src)
    with open('syn_result.txt', 'w') as f:
        f.write('PASS')
except SyntaxError as e:
    with open('syn_result.txt', 'w') as f:
        f.write(f'FAIL: {e}')
    sys.exit(1)
