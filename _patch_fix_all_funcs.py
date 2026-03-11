"""
bulk reindent가 놓친 함수들 수정:
- top-level def 이후 본문 첫 줄이 0칸인 함수를 모두 4칸으로 복원
- 범위: 전체 파일 (RANGE_START 제한 없이)
- 단, main() 내부 중첩함수는 건드리지 않음 (main은 이미 4칸 들여쓰기 본문)
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

# top-level def 위치 수집
top_level_defs = []
for i, ln in enumerate(lines):
    if (ln.startswith('def ') or ln.startswith('async def ')):
        top_level_defs.append(i)

print(f"Total top-level defs: {len(top_level_defs)}")

# 각 함수 검사: 본문 첫 비어있지 않은 줄이 0칸이면 수정
fixes = 0
# 역순으로 처리 (인덱스 유지)
for idx in range(len(top_level_defs) - 1, -1, -1):
    fi = top_level_defs[idx]
    # 다음 top-level def 위치 = 본문 끝
    if idx + 1 < len(top_level_defs):
        fe = top_level_defs[idx + 1]
    else:
        fe = len(lines)

    bs = fi + 1  # 본문 시작

    # 첫 비어있지 않은 줄 찾기
    first_nonempty = None
    for j in range(bs, fe):
        if lines[j].strip():
            first_nonempty = j
            break

    if first_nonempty is None:
        continue

    indent = len(lines[first_nonempty]) - len(lines[first_nonempty].lstrip())

    if indent == 0:
        # 0칸 → 4칸 추가
        fixed_body = []
        for j in range(bs, fe):
            ln = lines[j]
            if ln.strip() == '':
                fixed_body.append('\n')
            else:
                fixed_body.append('    ' + ln)
        lines = lines[:bs] + fixed_body + lines[fe:]
        fixes += 1
        print(f"  FIXED L{fi+1}: {lines[fi][:60].rstrip()}")

print(f"\nTotal fixes: {fixes}")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE")
