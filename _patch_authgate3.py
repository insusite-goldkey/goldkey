with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

DEDENT_START = 30709

main_line = None
for i in range(DEDENT_START, len(lines)):
    if lines[i].startswith('def main():') or lines[i].startswith('def main() ->'):
        main_line = i
        break

if main_line is None:
    for i in range(DEDENT_START, len(lines)):
        if lines[i].startswith('def _run_safe('):
            main_line = i
            break

if main_line is None:
    print("ERROR: main not found")
    exit(1)

print(f"dedent L{DEDENT_START+1}~L{main_line}, main at L{main_line+1}")

fixed = []
for i in range(DEDENT_START, main_line):
    ln = lines[i]
    if ln.strip() == '':
        fixed.append('\n')
    elif ln.startswith('    '):
        fixed.append(ln[4:])
    else:
        fixed.append(ln)

lines = lines[:DEDENT_START] + fixed + lines[main_line:]

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE")
