import ast, sys
try:
    src = open('app.py', encoding='utf-8').read()
    ast.parse(src)
    print('AST OK')
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
    print(f'Text: {e.text}')
    sys.exit(1)
