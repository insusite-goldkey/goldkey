
# 새 홈 탭 코드를 파일로 저장
new_home = open('_new_home_code.py', encoding='utf-8').read()

data = open('app.py', encoding='utf-8-sig').read()
lines = data.splitlines()

start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '    if cur == "home":' in line and start_idx is None:
        start_idx = i
for i, line in enumerate(lines):
    if i > (start_idx or 0) and line.startswith('    # \u2550\u2550'):
        end_idx = i
        break

print(f"교체 범위: line {start_idx+1} ~ {end_idx}")
before = '\n'.join(lines[:start_idx])
after  = '\n'.join(lines[end_idx:])
new_data = before + '\n' + new_home + '\n' + after
open('app.py', 'w', encoding='utf-8-sig').write(new_data)
print("완료!")
