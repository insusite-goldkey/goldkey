import ast, os, traceback

base = r'D:\CascadeProjects'
path = os.path.join(base, 'app.py')
out  = os.path.join(base, 'syn2.txt')

out_lines = []
try:
    src = open(path, encoding='utf-8').read()
    try:
        ast.parse(src)
        out_lines.append('SYNTAX OK')
    except SyntaxError as e:
        out_lines.append('SyntaxError line ' + str(e.lineno) + ': ' + str(e.msg))
        lines = src.splitlines()
        start = max(0, e.lineno - 4)
        end   = min(len(lines), e.lineno + 3)
        for i in range(start, end):
            marker = '>>>' if (i + 1) == e.lineno else '   '
            out_lines.append(marker + ' ' + str(i+1) + ': ' + lines[i])
except Exception:
    out_lines.append(traceback.format_exc())

result = '\n'.join(out_lines)
open(out, 'w', encoding='utf-8').write(result)
print('Written to ' + out)
