import ast, sys

src_path = r'D:\CascadeProjects\app.py'
try:
    with open(src_path, encoding='utf-8') as f:
        src = f.read()
    ast.parse(src, filename=src_path)
    print('SYNTAX OK')
    sys.exit(0)
except SyntaxError as e:
    print(f'SyntaxError at line {e.lineno}: {e.msg}')
    print(f'  text: {repr(e.text)}')
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}')
    sys.exit(1)
