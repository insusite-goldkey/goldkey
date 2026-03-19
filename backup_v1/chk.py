import ast, sys
try:
    src = open('app.py', 'r', encoding='utf-8').read()
    ast.parse(src)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR line {e.lineno}: {e.msg}')
    sys.exit(1)
