import ast, sys

result_path = 'D:/CascadeProjects/_syntax_result.txt'
src_path    = 'D:/CascadeProjects/app.py'

try:
    with open(src_path, encoding='utf-8') as f:
        src = f.read()
    ast.parse(src, filename=src_path)
    msg = 'SYNTAX OK\n'
except SyntaxError as e:
    msg = f'SyntaxError line {e.lineno}: {e.msg}\n  >>> {repr(e.text)}\n'
except Exception as e:
    msg = f'Error: {e}\n'

with open(result_path, 'w', encoding='utf-8') as out:
    out.write(msg)

print(msg, end='')
