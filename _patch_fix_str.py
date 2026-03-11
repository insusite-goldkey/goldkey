# -*- coding: utf-8 -*-
"""라인 30637 unterminated string literal 수정"""

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# 손상된 패턴: report_text += "\n\n" 에서 줄바꿈이 리터럴로 들어간 경우
# 실제로는 report_text += "\n\n" + ... 가 되어야 함
BAD = 'report_text += "\n\n" + " / ".join(_annotations)'

# 파일 내 실제 손상된 부분 탐색
idx = content.find('    if _annotations:\n        report_text += "')
if idx == -1:
    print("ERROR: bad pattern not found by primary search")
    # 보조 탐색
    idx2 = content.find('report_text += "')
    print(f"Alt find at {idx2}: {repr(content[idx2:idx2+60])}")
    exit(1)

# 손상된 구간 추출 확인
snippet = content[idx:idx+120]
print("FOUND snippet:", repr(snippet))

# 손상된 내용을 올바른 내용으로 교체
# 줄바꿈 리터럴이 실제 개행으로 들어간 부분 → \\n\\n 문자열로 교체
import re

# "report_text += "\n<실제개행>\n<실제개행>" + ... 패턴
FIXED = '    if _annotations:\n        report_text += "\\n\\n" + " / ".join(_annotations)\n'

# 패턴 범위: if _annotations: 줄부터 return report_text 직전까지
END_ANCHOR = '    return report_text\n'
end_idx = content.find(END_ANCHOR, idx)
if end_idx == -1:
    print("ERROR: end anchor not found")
    exit(1)

old_block = content[idx:end_idx]
print("OLD block:", repr(old_block))

content = content[:idx] + FIXED + content[end_idx:]
print("FIXED block inserted")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: unterminated string fixed")
