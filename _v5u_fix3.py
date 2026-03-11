# -*- coding: utf-8 -*-
"""SECTOR_CODES 잔여 오류 라인 제거"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# 8877~8881 (0-idx 8876~8880) 에 남은 고아(orphan) keywords 라인 제거
# 패턴: ]}, 바로 앞에 "위험분석" 등이 들어간 3줄이 있는 경우
# 해당 라인들: 
#   "        \"위험분석\", ..."
#   "        \"고위험질환\", ..."
#   "        \"고위험\", ..."
#   "    ]},"

new_lines = []
skip_next = 0
for i, l in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        print(f"  SKIP {i+1}: {repr(l[:60])}")
        continue
    
    # 고아 keywords 블록 감지: ]}, 가 나오는데 바로 앞에 "위험도분석" 라인이 있는 경우
    # i-1, i-2, i-3에 키워드 문자열이 있고, i가 ]}, 인 경우
    if l.strip() == ']},':
        # 뒤를 보면 "9900" 이 나오는 경우 — 이 블록이 고아
        j = i + 1
        while j < len(lines) and lines[j].strip() == '':
            j += 1
        if j < len(lines) and '"9900":' in lines[j]:
            # 앞 3~4줄도 고아인지 확인
            k = len(new_lines) - 1
            orphan_count = 0
            while k >= 0 and ('"위험' in new_lines[k] or '"고위험' in new_lines[k] or 
                              '"리스크' in new_lines[k] or '"전략리스크' in new_lines[k]):
                orphan_count += 1
                k -= 1
            if orphan_count > 0:
                print(f"  고아 키워드 {orphan_count}줄 제거 (line {i+1})")
                new_lines = new_lines[:k+1]  # 고아 라인들 제거
                print(f"  ]}} 라인도 제거: {repr(l[:40])}")
                continue  # ]}, 도 제거
    
    new_lines.append(l)

src = '\n'.join(new_lines)
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
print(f"총 줄 수: {len(new_lines)}")
