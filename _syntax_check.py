import ast
try:
    ast.parse(open('app.py', encoding='utf-8').read())
    print('SYNTAX_OK')
except SyntaxError as e:
    print(f'SYNTAX_ERROR|line={e.lineno}|msg={e.msg}|text={repr(e.text)}')
