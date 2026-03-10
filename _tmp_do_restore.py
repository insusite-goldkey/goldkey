
import subprocess

# 2ea750f 버전의 home 탭 전체 추출
result = subprocess.run(['git', 'show', '2ea750f:app.py'], capture_output=True)
orig_data = result.stdout.decode('utf-8-sig', errors='replace')

idx_home_orig = orig_data.find('    if cur == "home":')
next_block_orig = orig_data.find('\n    # \u2550\u2550', idx_home_orig + 100)
full_home_orig = orig_data[idx_home_orig:next_block_orig]

# 현재 버전
cur_data = open('app.py', encoding='utf-8-sig').read()

# 끝 마커
end_marker = "        st.markdown(\"<div style='height:18px'></div>\", unsafe_allow_html=True)"

# 원본에서 끝 마커 이후 삭제된 코드 추출
orig_after_marker = full_home_orig[full_home_orig.find(end_marker) + len(end_marker):]

# 현재에서 끝 마커 이후의 삭제 주석 블록
cur_after_marker_start = "        # ── [GP220 그룹9 삭제됨 — 보험사 연락처·청구 안내 블럭 제거] ──────────"

# 현재 파일에서 삽입 위치 = end_marker 직후
insert_after = end_marker
idx_insert = cur_data.find(insert_after)
if idx_insert < 0:
    print("ERROR: 삽입 위치를 찾을 수 없습니다!")
    exit(1)

insert_pos = idx_insert + len(insert_after)
print(f"삽입 위치: {insert_pos} (라인 ~{cur_data[:insert_pos].count(chr(10))+1})")

# 복원: end_marker 이후에 원본 코드 삽입
# 현재 파일의 end_marker 이후 내용 (삭제된 주석 포함) 제거하고 원본으로 대체
# 현재 end_marker 다음에 오는 GP220 그룹9 삭제 주석 위치 찾기
after_cur = cur_data[insert_pos:]
grp9_marker = "\n\n\n\n\n        # ── [GP220 그룹9 삭제됨"
idx_grp9 = after_cur.find(grp9_marker)
print(f"그룹9 마커 위치: {idx_grp9}")

if idx_grp9 >= 0:
    # end_marker ~ 그룹9 마커 사이에 orig 코드 삽입
    new_data = (
        cur_data[:insert_pos]
        + orig_after_marker
        + after_cur[idx_grp9:]  # 그룹9 주석 이후 (원래 있던 빈줄들과 주석 유지)
    )
else:
    # 그냥 뒤에 붙이기
    new_data = cur_data[:insert_pos] + orig_after_marker + after_cur

print(f"원본 파일: {len(cur_data)} chars")
print(f"복원 파일: {len(new_data)} chars")
print(f"추가된 chars: {len(new_data) - len(cur_data)}")

open('app.py', 'w', encoding='utf-8-sig').write(new_data)
print("복원 완료!")
