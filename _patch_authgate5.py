with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# 다음 top-level def 목록 찾기 (L30714 이후)
print("=== top-level defs after L30710 ===")
for i in range(30709, min(31200, len(lines))):
    ln = lines[i]
    if ln.startswith('def ') or ln.startswith('class ') or ln.startswith('async def '):
        print(f"L{i+1}: {repr(ln[:80])}")
