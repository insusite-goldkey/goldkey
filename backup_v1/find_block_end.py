"""
if not _is_auth_now: (line 28698) 블록의 실제 끝을 triple-quote 추적으로 찾기
"""
SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

in_triple = False
triple_char = None

for i in range(28697, 32000):
    ln = lines[i]

    # triple quote 토글 추적
    temp = ln
    while True:
        found = False
        for q in ['"""', "'''"]:
            idx = temp.find(q)
            if idx != -1:
                if not in_triple:
                    in_triple = True
                    triple_char = q
                elif triple_char == q:
                    in_triple = False
                    triple_char = None
                temp = temp[idx + 3:]
                found = True
                break
        if not found:
            break

    if in_triple:
        continue

    stripped = ln.strip()
    if not stripped or stripped.startswith('#'):
        continue

    indent = len(ln) - len(ln.lstrip())

    if i > 28698 and indent <= 4:
        print(f"블록 종료 후 첫 코드 줄: line {i+1}, indent={indent}")
        print(f"  {repr(ln[:80])}")
        print("--- 전후 문맥 ---")
        for j in range(i - 4, i + 4):
            s = len(lines[j]) - len(lines[j].lstrip())
            print(f"  [{j+1}] indent={s} | {repr(lines[j][:65])}")
        break
