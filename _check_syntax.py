import py_compile, sys

out = open('D:/CascadeProjects/_syntax_result.txt', 'w', encoding='utf-8')
try:
    py_compile.compile('D:/CascadeProjects/app.py', doraise=True)
    out.write('SYNTAX OK\n')
except py_compile.PyCompileError as e:
    out.write('ERROR: ' + str(e) + '\n')
except SyntaxError as e:
    out.write(f'SyntaxError line {e.lineno}: {e.msg}\n')
out.close()
