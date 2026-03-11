# -*- coding: utf-8 -*-
"""
ai_query_block NameError 수정
- main() 안의 'def ai_query_block(...)' 블록을 추출
- 들여쓰기 4칸 제거 (indent dedent)
- main() 바로 위 모듈 레벨에 삽입
- main() 안의 원본 정의는 삭제
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')
n0 = len(lines)
print(f"원본: {n0}줄")

# ── 1. ai_query_block 범위 파악 ───────────────────────────────────────────
# 시작: '    def ai_query_block(' 첫 번째 등장 (indent=4)
def_start = next(i for i, l in enumerate(lines)
                 if l.startswith('    def ai_query_block('))

# return 문 라인
ret_line  = next(i for i in range(def_start, def_start + 6000)
                 if 'return c_name, query, hi_premium, do_analyze, _pkey' in lines[i])

# 함수 끝 = return 문 라인 (빈 줄 포함하되 다음 indent<=4 코드까지)
def_end = ret_line
# 뒤따르는 빈 줄도 함께 포함
while def_end + 1 < len(lines) and not lines[def_end + 1].strip():
    def_end += 1

print(f"ai_query_block: {def_start+1}~{def_end+1}")
print(f"  시작: {repr(lines[def_start][:70])}")
print(f"  끝:   {repr(lines[def_end][:70])}")

# ── 2. 블록 추출 및 dedent (4칸 제거) ────────────────────────────────────
block_lines = lines[def_start : def_end + 1]

dedented = []
for l in block_lines:
    if l.startswith('    '):
        dedented.append(l[4:])   # 최상위 4칸 제거
    elif l == '':
        dedented.append('')
    else:
        dedented.append(l)       # 이미 indent=0 이면 그대로 (비정상 라인)

# 모듈 레벨 함수로 변환됐는지 확인
assert dedented[0].startswith('def ai_query_block('), \
    f"dedent 실패: {repr(dedented[0][:60])}"
print(f"dedent 확인: {repr(dedented[0][:60])}")

# ── 3. main() 위치 찾기 ──────────────────────────────────────────────────
main_line = next(i for i, l in enumerate(lines) if l == 'def main():')
print(f"main() at {main_line+1}")

# ── 4. 원본에서 블록 제거 ────────────────────────────────────────────────
new_lines = lines[:def_start] + lines[def_end + 1:]
print(f"제거 후: {len(new_lines)}줄 (제거: {def_end - def_start + 1}줄)")

# main() 위치 재계산 (블록이 main() 앞에 있으므로 main_line 보정 불필요
# — def_start < main_line 이므로 main_line이 앞당겨짐)
main_line_new = main_line - (def_end - def_start + 1)
print(f"main() new position: {main_line_new+1}: {repr(new_lines[main_line_new][:60])}")

# ── 5. main() 바로 위에 모듈 레벨 함수 삽입 ──────────────────────────────
# 삽입 위치: main() 바로 앞 빈 줄 포함
separator = ['', '']
final_lines = (new_lines[:main_line_new]
               + separator
               + dedented
               + ['', '']
               + new_lines[main_line_new:])

print(f"삽입 후: {len(final_lines)}줄")

# ── 6. 저장 ──────────────────────────────────────────────────────────────
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write('\n'.join(final_lines))
print(f"OK total lines: {len(final_lines)}")

# ── 7. 검증 ──────────────────────────────────────────────────────────────
src2 = open('D:/CascadeProjects/app.py', encoding='utf-8').read()
lines2 = src2.split('\n')
# ai_query_block 이 모듈 레벨(indent=0)에 있는지
aqb_pos = [i+1 for i, l in enumerate(lines2) if l.startswith('def ai_query_block(')]
print(f"ai_query_block 모듈 레벨 위치: {aqb_pos}")
# main() 위치
main_pos = [i+1 for i, l in enumerate(lines2) if l == 'def main():']
print(f"main() 위치: {main_pos}")
