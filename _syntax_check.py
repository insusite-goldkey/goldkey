import ast
for fname in ['app.py', 'modules/smart_scanner.py']:
    try:
        src = open(fname, encoding='utf-8-sig').read()
        ast.parse(src)
        print(f'SYNTAX_OK: {fname}')
    except SyntaxError as e:
        print(f'SYNTAX_ERROR [{fname}] line={e.lineno} msg={e.msg} text={repr(e.text)}')
