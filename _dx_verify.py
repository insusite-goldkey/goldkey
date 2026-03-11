# -*- coding: utf-8 -*-
"""로컬 폴백 DB 검증"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# _KCD_FALLBACK_DATA 블록 추출
start = next(i for i, l in enumerate(lines) if '_KCD_FALLBACK_DATA: list = [' in l)
end   = next(i for i in range(start + 1, len(lines)) if lines[i].startswith(']') and not lines[i].startswith('    '))
chunk = '\n'.join(lines[start:end + 1])

ns = {}
exec(chunk, ns)
db = ns['_KCD_FALLBACK_DATA']
print(f'DB size: {len(db)}')

tests = ['당뇨', '협심증', '뇌경색', '암', '치매', '고혈압', '폐암', '심근경색']
for q in tests:
    ql = q.lower()
    hits = []
    for r in db:
        kws = r.get('keywords', [])
        if (ql in r['name'].lower() or ql in r['kcd'].lower()
                or any(ql in kw.lower() for kw in kws)):
            hits.append(r)
        if len(hits) >= 3:
            break
    names = [(h['kcd'], h['name'][:16]) for h in hits]
    print(f"  {q}: {len(hits)}건 -> {names}")
