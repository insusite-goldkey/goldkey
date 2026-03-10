
import subprocess

# 2ea750f 버전의 home 탭 전체 추출
result = subprocess.run(['git', 'show', '2ea750f:app.py'], capture_output=True)
orig_data = result.stdout.decode('utf-8-sig', errors='replace')

idx_home_orig = orig_data.find('    if cur == "home":')
next_block_orig = orig_data.find('\n    # \u2550\u2550', idx_home_orig + 100)
full_home_orig = orig_data[idx_home_orig:next_block_orig]

# 현재 버전
cur_data = open('app.py', encoding='utf-8-sig').read()
idx_cur = cur_data.find('    if cur == "home":')
next_cur = cur_data.find('\n    # \u2550\u2550', idx_cur + 100)
cur_home = cur_data[idx_cur:next_cur]

# 현재 home 탭의 끝 마커
end_marker = "        st.markdown(\"<div style='height:18px'></div>\", unsafe_allow_html=True)"

# 현재 home 탭에서 끝 마커 이후에 붙어있는 삭제된 주석 찾기
cur_after_marker = cur_home[cur_home.find(end_marker) + len(end_marker):]
print(f"현재 끝 마커 이후 내용:\n{cur_after_marker[:200]}")

# 원본에서 끝 마커 이후 삭제된 코드
orig_after_marker = full_home_orig[full_home_orig.find(end_marker) + len(end_marker):]
print(f"\n원본 끝 마커 이후 내용 (처음 200자):\n{orig_after_marker[:200]}")
print(f"\n복원할 코드: {len(orig_after_marker)} chars, {orig_after_marker.count(chr(10))}줄")
