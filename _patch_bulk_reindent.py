"""
_patch_authgate3.py 가 main() 이전 전체를 4칸 dedent 했기 때문에
L30710 ~ main() 사이의 모든 top-level 함수 본문이 0칸으로 망가졌다.
이를 일괄 복원한다:
  - 각 top-level 함수(def foo(...):) 를 찾아
  - 본문 첫 줄이 0칸이면 → 해당 함수 끝까지 4칸 추가
  - 단, 이미 4칸인 함수는 건드리지 않는다
범위: 수정 시작 지점(L30710, 0-based 30709) ~ 파일 끝
"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    lines = f.readlines()

RANGE_START = 30709  # 0-based

def get_func_body_range(lines, func_idx):
    """func_idx(0-based): def 선언 라인 → (body_start, body_end) 0-based 반환"""
    body_start = func_idx + 1
    body_end = len(lines)
    for i in range(body_start, len(lines)):
        ln = lines[i]
        if ln.strip() == '':
            continue
        # 다음 top-level 코드
        if not ln[0].isspace() and (
            ln.startswith('def ') or ln.startswith('class ') or
            ln.startswith('async def ') or ln.startswith('@') or
            ln.startswith('#') or ln.startswith('_') or ln.startswith('"') or
            ln[0].isalpha()
        ):
            body_end = i
            break
    return body_start, body_end

# top-level def 목록 수집 (RANGE_START 이후)
func_indices = []
for i in range(RANGE_START, len(lines)):
    ln = lines[i]
    if ln.startswith('def ') or ln.startswith('async def '):
        func_indices.append(i)

print(f"Found {len(func_indices)} top-level funcs from L{RANGE_START+1}")
for fi in func_indices[:10]:
    print(f"  L{fi+1}: {lines[fi][:60].rstrip()}")

# 각 함수 본문 첫 줄 들여쓰기 확인 후 수정
fixes = 0
# 역순으로 처리해야 인덱스 변화 없음
for fi in reversed(func_indices):
    bs, be = get_func_body_range(lines, fi)
    # 본문에서 첫 비어있지 않은 줄 찾기
    first_body_idx = None
    for j in range(bs, be):
        if lines[j].strip():
            first_body_idx = j
            break
    if first_body_idx is None:
        continue
    indent = len(lines[first_body_idx]) - len(lines[first_body_idx].lstrip())
    if indent == 0:
        # 0칸 → 4칸 추가
        fixed = []
        for j in range(bs, be):
            ln = lines[j]
            if ln.strip() == '':
                fixed.append('\n')
            else:
                fixed.append('    ' + ln)
        lines = lines[:bs] + fixed + lines[be:]
        fixes += 1
        print(f"  FIXED L{fi+1}: {lines[fi][:50].rstrip()} (body indent was 0)")

print(f"\nTotal fixes: {fixes}")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("DONE")
