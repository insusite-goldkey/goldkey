# -*- coding: utf-8 -*-
"""SECTOR_CODES 8806 구조 오류 수정 + 남은 구문 오류 일괄 수정"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# ── 문제 구조 확인 ──
# 8806(0-idx=8805): "2700": {..., "keywords": [  ← 닫힘 없이
# 8807(0-idx=8806): "0300": {...}               ← 잘못 붙어있음
# 원래 2700 블록은 다음과 같아야 함:
# "2700": {"name":..., "tab_key":"gk_risk", "keywords": [...]},

for i, l in enumerate(lines):
    if '"2700":' in l and 'gk_risk' in l:
        print(f"2700 at {i+1}: {repr(l[:100])}")
        print(f"next: {repr(lines[i+1][:100])}")
        print(f"next2: {repr(lines[i+2][:100])}")
        break

# 2700 라인과 0300 라인이 붙어있는 문제를 수정
# 패턴: "2700" 블록의 keywords 리스트가 닫히지 않고 바로 "0300" 시작
BROKEN = (
    '    "2700": {"name": "전략적 위험 분석 사령부", "tab_key": "gk_risk", "keywords": [\n'
    '    "0300": {"name": "실전 상담 전략실", "tab_key": "war_room",'
)

FIXED = (
    '    "2700": {"name": "전략적 위험 분석 사령부", "tab_key": "gk_risk", "keywords": [\n'
    '        "위험분석", "위험등급", "리스크센터", "gk-risk", "전략위험",\n'
    '        "고위험질환", "kcd위험", "위험사령부", "리스크배지", "위험배지",\n'
    '        "고위험", "위험도", "위험도분석", "전략리스크",\n'
    '    ]},\n'
    '    "0300": {"name": "실전 상담 전략실", "tab_key": "war_room",'
)

cnt = src.count(BROKEN)
print(f"BROKEN count: {cnt}")
if cnt == 1:
    src = src.replace(BROKEN, FIXED, 1)
    print("✓ 2700 블록 구조 복구")
else:
    # 라인 단위로 찾아서 수정
    new_lines = []
    i = 0
    while i < len(lines):
        l = lines[i]
        # 2700 블록이 keywords: [ 로 끝나고 다음 줄이 "0300" 으로 시작하는 경우
        if ('"2700":' in l and 'gk_risk' in l and l.rstrip().endswith('[')):
            next_l = lines[i+1] if i+1 < len(lines) else ''
            if '"0300":' in next_l:
                # 2700 블록 복구: keywords 내용 삽입 후 닫기
                new_lines.append(l)
                new_lines.append('        "위험분석", "위험등급", "리스크센터", "gk-risk", "전략위험",')
                new_lines.append('        "고위험질환", "kcd위험", "위험사령부", "리스크배지", "위험배지",')
                new_lines.append('        "고위험", "위험도", "위험도분석", "전략리스크",')
                new_lines.append('    ]},')
                i += 1
                print(f"✓ 라인 기반 수정: {i+1}")
                continue
        new_lines.append(l)
        i += 1
    src = '\n'.join(new_lines)

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
print(f"총 줄 수: {len(src.split(chr(10)))}")
