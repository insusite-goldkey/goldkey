# -*- coding: utf-8 -*-
"""
ai_query_block NameError 수정 v2:
- return 문이 with _ftab2/_ftab3/_ftab4 블록들보다 앞에 잘못 위치됨
- return 을 _ftab4 블록 끝 이후로 이동
- with _ftab2/3/4 들이 ai_query_block 함수 내부 (indent=8) 에 속하도록 확인
"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')
n0 = len(lines)
print(f"원본: {n0}줄")

# ── 핵심 라인 위치 확인 ─────────────────────────────────────────────────────
ret_idx   = next(i for i,l in enumerate(lines)
                 if l == '    return c_name, query, hi_premium, do_analyze, _pkey')
ftab2_idx = next(i for i,l in enumerate(lines) if l == '        with _ftab2:')
ftab3_idx = next(i for i,l in enumerate(lines) if l == '        with _ftab3:')
ftab4_idx = next(i for i,l in enumerate(lines) if l == '        with _ftab4:')

print(f"return at {ret_idx+1}, ftab2 at {ftab2_idx+1}, ftab3 at {ftab3_idx+1}, ftab4 at {ftab4_idx+1}")

assert ret_idx < ftab2_idx, "이미 올바른 순서입니다."

# ── with _ftab4: 블록 끝 위치 파악 ─────────────────────────────────────────
# ftab4 블록은 indent=8 로 시작, 다음 indent<=8 비공백 코드 전까지
# (multiline string 내부의 indent=0 라인은 넘어가야 하므로
#  실제 Python 토큰 기준 대신 '다음 indent=4 이하 Python 코드' 기준 사용)
# → _pkey 할당 라인과 return 라인이 indent=4이고 이미 ret_idx에 있으므로
#   ret_idx 바로 전이 ftab4 블록의 마지막 실질 내용
# 즉, 현재 순서: [ftab1 block] ... [ftab2 block]...[ftab3 block]...[ftab4 block]
#                 return (잘못된 위치: ftab2 앞)
# 올바른 순서: [ftab2 block] ... [ftab3 block] ... [ftab4 block] ... return

# return 라인과 그 직전 빈 줄들 추출
# ret_idx-1, ret_idx-2 등이 빈줄인지 확인
pre_ret_blanks = 0
for i in range(ret_idx-1, ret_idx-5, -1):
    if lines[i].strip() == '':
        pre_ret_blanks += 1
    else:
        break

# _pkey 할당 라인 (return 바로 앞)
pkey_idx = ret_idx - 1 - pre_ret_blanks
# pkey 라인 확인
print(f"pkey line at {pkey_idx+1}: {repr(lines[pkey_idx][:70])}")
assert '_pkey = st.session_state' in lines[pkey_idx]

# ── 제거: return 바로 앞 _pkey + return + 앞 빈줄들 ─────────────────────────
# 제거 범위: pkey_idx ~ ret_idx (inclusive)
remove_start = pkey_idx
remove_end   = ret_idx
print(f"제거 범위: {remove_start+1}~{remove_end+1}")

# 제거 전 내용 백업
removed_lines = lines[remove_start:remove_end+1]
print(f"제거 내용: {removed_lines}")

# ── 삽입 위치: ftab4 블록 끝 ─────────────────────────────────────────────────
# ftab4 이후 remove_start 이전 구간에서 indent<=8 Python 코드 마지막 라인
# → 이미 ret_idx < ftab4_idx 이므로 ftab4 이후에 삽입
# ftab4_idx 이후에서 실제 with _ftab4: 블록이 끝나는 위치 파악
# 블록 끝 = ftab4 이후 나오는 indent<=4 비공백 라인 (multiline string 무시)
# 가장 안전한 방법: 현재 파일 끝 방향으로 진행하며 indent=4 라인 처음 찾기
# (단, ftab4 자체의 내용이 multiline string을 포함하므로 파이썬 토크나이저 필요)
# → 간단히: _blk_tags 코드 바로 앞이 ftab4 관련 코드이고,
#   remove_start(pkey_idx) 앞에 ftab4 블록의 마지막 indent=8 코드가 있음

# pkey_idx 앞의 첫 번째 비공백 라인 확인
for i in range(remove_start-1, remove_start-10, -1):
    if lines[i].strip():
        print(f"before pkey: {i+1}: {repr(lines[i][:80])}")
        break

# ── 새 파일 구성 ─────────────────────────────────────────────────────────────
# 1. remove_start~remove_end 제거
# 2. remove_end 다음 (즉 with _ftab2: 직전의 빈줄들 이후) 를 탐색하여
#    ftab2/3/4 블록이 끝나는 지점 파악
# 3. 그 지점 이후에 removed_lines 삽입

# 제거 후 새 라인 목록
new_lines = lines[:remove_start] + lines[remove_end+1:]
print(f"제거 후: {len(new_lines)}줄")

# ftab4 블록 끝 찾기 (제거 후 인덱스 기준)
# ftab4_idx는 제거 전 기준 → 제거 후 보정
ftab4_new = ftab4_idx - (remove_end - remove_start + 1)
print(f"ftab4 new idx: {ftab4_new+1}: {repr(new_lines[ftab4_new][:60])}")

# ftab4 블록 뒤에서 indent=4 이하 비공백 파이썬 라인 찾기
# multiline string 안 내용(indent=0)을 건너뛰어야 하므로
# 실제로는 "다음 def/class/if __name__ 또는 indent=4 파이썬 코드"를 찾음
# 가장 안전: return 이 있어야 할 위치 = ftab4 블록 뒤 첫 번째 indent=4 코드

# 현재 상태에서 ftab4 이후 indent=4 코드 찾기
insert_before = None
for i in range(ftab4_new+1, ftab4_new+5000):
    l = new_lines[i]
    if not l.strip():
        continue
    ind = len(l) - len(l.lstrip())
    if ind == 4:
        print(f"first indent=4 after ftab4: {i+1}: {repr(l[:80])}")
        insert_before = i
        break
    if ind == 0 and not l.strip().startswith('#'):
        # 모듈 레벨 코드 만남 — 그 앞에 삽입
        print(f"module-level code at {i+1}: {repr(l[:80])}")
        insert_before = i
        break

assert insert_before is not None

# ── 삽입 ─────────────────────────────────────────────────────────────────────
final_lines = new_lines[:insert_before] + removed_lines + new_lines[insert_before:]
print(f"삽입 후: {len(final_lines)}줄")

# ── 저장 ─────────────────────────────────────────────────────────────────────
open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write('\n'.join(final_lines))
print("저장 완료")
