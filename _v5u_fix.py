# -*- coding: utf-8 -*-
"""V5U 구문 오류 수정 — 10932줄 f-string 따옴표 충돌"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# 문제 라인 찾아서 교체
for i, l in enumerate(lines):
    if "font-size:0.68rem;color:#fca5a5;font-weight:700;margin-bottom:6px;" in l and ">종합 위험등급</div>" in l:
        print(f"Found at line {i+1}: {repr(l[:100])}")
        # 따옴표 불일치 수정: style 값 닫는 ' 추가 후 > 분리
        lines[i] = (
            "        f\"<div style='font-size:0.68rem;color:#fca5a5;"
            "font-weight:700;margin-bottom:6px;'>\"\n"
            "        f\"종합 위험등급</div>\""
        )
        print(f"Fixed: {repr(lines[i][:100])}")
        break

src = '\n'.join(lines)
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
print(f"총 줄 수: {len(lines)}")
