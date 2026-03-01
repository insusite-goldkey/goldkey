"""
app.py 내에서 'text' 변수를 정의 없이 사용하는 위치를 탐지한다.
단순 grep 기반: 함수 파라미터/로컬 할당 없이 text 를 값으로 쓰는 라인을 추출.
"""
import re

with open('d:/CascadeProjects/app.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

# 현재 함수 스코프에서 text가 파라미터/할당으로 정의됐는지 추적
in_func_with_text_param = False
text_assigned = False
results = []

for i, raw in enumerate(lines, 1):
    line = raw.rstrip()
    stripped = line.lstrip()

    # 함수 정의 감지
    if re.match(r'\s*(?:async\s+)?def\s+', raw):
        # text가 파라미터인지 확인
        in_func_with_text_param = bool(re.search(r'\btext\b\s*[,:\)]', raw) or
                                       re.search(r'\(\s*text\b', raw))
        text_assigned = in_func_with_text_param

    # 현재 라인에서 text 할당
    if re.match(r'\s*text\s*=', raw) or re.match(r'\s*text\s*\+=', raw):
        text_assigned = True

    # 코멘트 라인 스킵
    if stripped.startswith('#'):
        continue

    # text가 값으로 사용되는지 (할당 우변, 인자, f-string 등)
    # 패턴: text 뒤에 = 없고, 앞에 알파벳/점/언더바/_가 없는 경우
    if re.search(r'(?<![a-zA-Z_\.\'])\btext\b(?!\s*[=:(,\[\.])', raw):
        # 제외: 함수 정의, CSS/HTML 속성, 주석, 이미 text= 형태
        if (not re.search(r'def\s+\w+.*\btext\b', raw) and
            'text-' not in raw and
            '"text"' not in raw and
            "'text'" not in raw and
            not stripped.startswith('#')):
            if not text_assigned:
                results.append(f"LINE {i:6d} [UNDEFINED?]: {line[:120]}")

out = '\n'.join(results) if results else 'No undefined text usage found.'
print(out)
open('d:/CascadeProjects/syn_result.txt', 'w', encoding='utf-8').write(out)
