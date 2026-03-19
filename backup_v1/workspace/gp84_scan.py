import re

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.splitlines()

dark_bg_pat = re.compile(
    r'background(?:-color)?[:\s]*["\']?\s*'
    r'(#(?:0[0-9a-fA-F]{5}|1[0-9a-fA-F]{5}|2[0-9a-fA-F]{5}|3[0-9a-fA-F]{5}|4[0-4][0-9a-fA-F]{4})'
    r'|#000|#111|#222|#333|#444|black)',
    re.IGNORECASE
)
dark_txt_pat = re.compile(
    r'(?<![a-z])color\s*:\s*["\']?\s*'
    r'(#(?:0[0-9a-fA-F]{5}|1[0-9a-fA-F]{5}|2[0-9a-fA-F]{5}|3[0-9a-fA-F]{5}|4[0-4][0-9a-fA-F]{4})'
    r'|#000|#111|#222|#333|#444|black)',
    re.IGNORECASE
)

results = []
for i, line in enumerate(lines, 1):
    m = dark_bg_pat.search(line)
    if m:
        results.append(('BG', i, m.group(0)[:60].strip(), line.strip()[:90]))
    m2 = dark_txt_pat.search(line)
    if m2:
        results.append(('TXT', i, m2.group(0)[:60].strip(), line.strip()[:90]))

with open('D:/CascadeProjects/gp84_scan_result.txt', 'w', encoding='utf-8') as out:
    out.write(f'총 발견: {len(results)}건\n\n')
    for typ, ln, match, ctx in results[:100]:
        out.write(f'[{typ}] L{ln}: {match} | {ctx}\n')
    if len(results) > 100:
        out.write(f'\n... 이하 {len(results)-100}건 생략\n')
