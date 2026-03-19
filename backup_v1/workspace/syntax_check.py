import ast, sys
try:
    src = open('app.py', encoding='utf-8-sig').read()
    ast.parse(src)
    msg = 'SYNTAX OK'
    open('syntax_result.txt','w').write(msg)
    print(msg)
except SyntaxError as e:
    msg = f'SYNTAX ERROR line {e.lineno}: {e.msg} | text: {repr(e.text)}'
    open('syntax_result.txt','w').write(msg)
    print(msg)
    sys.exit(1)
except Exception as e:
    msg = f'ERROR: {e}'
    open('syntax_result.txt','w').write(msg)
    print(msg)
    sys.exit(1)
