import ast, sys
try:
    src = open('app.py', encoding='utf-8-sig').read()
    ast.parse(src)
    print('SYNTAX OK')
except SyntaxError as e:
    print(f'SYNTAX ERROR: {e}')
    sys.exit(1)
