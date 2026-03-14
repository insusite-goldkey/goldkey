"""
app.py 전체 마인드맵 블록화 스캔
"""
import re

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

results = []

# 스캔 패턴 (우선순위 순)
patterns = [
    ("SECTION_HDR",   r'#\s*\[SECTION\s*\d'),
    ("DEF_FUNC",      r'^def [a-zA-Z_]'),
    ("GP_TAG",        r'#\s*\[GP[-\d\w]+\]'),
    ("ART_TAG",       r'#\s*\[ART\d'),
    ("DEMAND_TAG",    r'#\s*\[DEMAND'),
    ("SECTOR_TAG",    r'SECTOR_CODES\s*='),
    ("APP_REG",       r'APP_REGISTRY\s*='),
    ("BLOCK_SEP",     r'#\s*={30,}'),
    ("SUB_SEP",       r'#\s*-{20,}'),
    ("NAV_SECTION",   r'#\s*\[(SEC|LAW|CORP|HIRA|GP-JOB|GP64|GP200|GP100|GP101|GP102|GP103|GP110|GP120|WAR|CRM|FSS|RAG|SSO)'),
]

for i, ln in enumerate(lines):
    s = ln.strip()
    if not s:
        continue
    for tag, pat in patterns:
        if re.search(pat, ln):
            results.append((i+1, tag, ln.rstrip()))
            break

# 출력 (ASCII only label, Korean content safe)
out_lines = []
for lineno, tag, content in results:
    # encode safely
    try:
        safe = content.encode('utf-8').decode('utf-8')
    except Exception:
        safe = repr(content)
    out_lines.append(f"[{lineno:>6}] {tag:<15} | {safe[:100]}")

OUT = "D:/CascadeProjects/block_scan.txt"
with open(OUT, "w", encoding="utf-8") as f:
    f.write(f"Total lines: {len(lines)}\n")
    f.write(f"Total markers found: {len(results)}\n\n")
    f.write("\n".join(out_lines))

print(f"Done. {len(results)} markers -> block_scan.txt")
