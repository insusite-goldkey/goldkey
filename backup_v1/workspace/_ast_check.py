import ast, sys
try:
    ast.parse(open('app.py', encoding='utf-8-sig').read())
    print('AST OK')
except SyntaxError as e:
    print(f'SyntaxError line {e.lineno}: {e.msg}')
    print(f'  text: {repr(e.text)}')
    sys.exit(1)
