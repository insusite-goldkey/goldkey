import ast
lines = []
for fname in ['app.py', 'modules/smart_scanner.py']:
    try:
        src = open(fname, encoding='utf-8-sig').read()
        ast.parse(src)
        lines.append(f'SYNTAX_OK: {fname}')
    except SyntaxError as e:
        lines.append(f'SYNTAX_ERROR [{fname}] line={e.lineno} msg={e.msg} text={repr(e.text)}')

result = '\n'.join(lines)
print(result)
with open('_syntax_result.txt', 'w', encoding='utf-8') as f:
    f.write(result + '\n')
