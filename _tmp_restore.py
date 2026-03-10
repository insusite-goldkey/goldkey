
import subprocess

# 2ea750f 버전의 home 탭 전체 추출
result = subprocess.run(['git', 'show', '2ea750f:app.py'], capture_output=True)
data = result.stdout.decode('utf-8-sig', errors='replace')

idx_home = data.find('    if cur == "home":')
next_block = data.find('\n    # \u2550\u2550', idx_home + 100)
full_home = data[idx_home:next_block]

# 현재 버전의 home 탭 추출
cur_data = open('app.py', encoding='utf-8-sig').read()
idx_cur = cur_data.find('    if cur == "home":')
next_cur = cur_data.find('\n    # \u2550\u2550', idx_cur + 100)
cur_home = cur_data[idx_cur:next_cur]

print(f"원본: {len(full_home.splitlines())}줄")
print(f"현재: {len(cur_home.splitlines())}줄")

# 현재에 없는 부분 = 삭제된 코드
# 현재 home 탭 끝 지점 (스캔 우측 컬럼 이후)
cur_end_marker = "        st.markdown(\"<div style='height:18px'></div>\", unsafe_allow_html=True)"
idx_cur_end = cur_home.find(cur_end_marker)
print(f"\n현재 home 탭 끝 마커 위치: {idx_cur_end}")

# 원본에서 같은 마커 이후 삭제된 부분 추출
idx_orig_end = full_home.find(cur_end_marker)
deleted_part = full_home[idx_orig_end + len(cur_end_marker):]
print(f"삭제된 코드 길이: {len(deleted_part)} chars, {len(deleted_part.splitlines())}줄")

# 삭제된 코드 저장
open('_tmp_deleted_home.txt', 'w', encoding='utf-8').write(deleted_part)
print("저장 완료: _tmp_deleted_home.txt")
