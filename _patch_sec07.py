import re

with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ── 1. SECTOR_CODES에 7700 추가 ──
OLD1 = '"9930": {"name": "나의 인생 방어 사령부"'
if OLD1 not in content:
    print("ERROR: 9930 not found")
    exit(1)

# 9930 라인 끝 + },\n} 패턴 찾기
# SECTOR_CODES 닫는 } 바로 앞에 삽입
# "9930": {...},\n} 에서 },\n} 를 },\n    "7700":...,\n} 로
SECTOR_INSERT = '''    # ── GK-SEC-07: 자동차보험 전술 상담 센터 ─────────────────────────────────
    "7700": {"name": "자동차보험 전술 상담 센터", "tab_key": "gk_sec07", "keywords": ["자동차보험전술", "gk-sec-07", "자동차전술센터", "자동차보험센터", "민사배상분석", "과실비율상담", "운전자보험상관관계", "장해판정자동차", "사고대처가이드", "fc질문리스트", "갱신관리", "dday카운트", "자동차보험갱신", "특약백과사전", "마일리지할인특약", "커넥티드할인"]},
'''

# SECTOR_CODES 블록: "9930": ... 이후 첫 번째 단독 } 찾기
idx_9930 = content.find('"9930": {"name": "나의 인생 방어 사령부"')
# 그 줄 끝 찾기
idx_line_end = content.find('\n', idx_9930)
# 다음 줄이 } 인지 확인
next_line_start = idx_line_end + 1
next_line_end = content.find('\n', next_line_start)
next_line = content[next_line_start:next_line_end].strip()
print(f"Next line after 9930: {repr(next_line)}")

if next_line == '}':
    content = content[:idx_line_end+1] + SECTOR_INSERT + content[idx_line_end+1:]
    print("SECTOR_CODES 7700 inserted OK")
else:
    print(f"ERROR: unexpected line after 9930: {repr(next_line)}")
    exit(1)

# ── 2. SUB_CODES에 7710~7760 추가 ──
OLD2 = '"9060": {"name": "전문가 지원 센터"'
if OLD2 not in content:
    print("ERROR: 9060 not found")
    exit(1)

idx_9060 = content.find('"9060": {"name": "전문가 지원 센터"')
idx_9060_end = content.find('\n', idx_9060)
next2_start = idx_9060_end + 1
next2_end = content.find('\n', next2_start)
next2_line = content[next2_start:next2_end].strip()
print(f"Next line after 9060: {repr(next2_line)}")

SUB_INSERT = '''    # ── 7700: 자동차보험 전술 상담 센터 ─────────────────────────────────────────
    "7710": {"name": "자동차보험 가입/갱신 관리", "tab_key": "gk_sec07", "keywords": ["자동차보험가입", "자동차보험갱신", "갱신일관리", "갱신디데이"]},
    "7720": {"name": "민사배상 & 담보 분석",     "tab_key": "gk_sec07", "keywords": ["민사배상담보", "대인대물분석", "민법배상책임", "배상책임자동차"]},
    "7730": {"name": "운전자보험 상관관계",       "tab_key": "gk_sec07", "keywords": ["운전자보험연계", "운전자보험비교", "자동차운전자연계"]},
    "7740": {"name": "장해 판정 기준",            "tab_key": "gk_sec07", "keywords": ["장해판정기준", "AMA맥브라이드비교", "국가장애율", "노동능력상실자동차"]},
    "7750": {"name": "사고 대처 가이드",          "tab_key": "gk_sec07", "keywords": ["사고대처", "과실비율가이드", "교통사고초동", "사고현장대응"]},
    "7760": {"name": "필수 질문 리스트(FC용)",    "tab_key": "gk_sec07", "keywords": ["fc질문", "설계사질문리스트", "자동차상담질문", "fc체크리스트"]},
'''

if next2_line == '}':
    content = content[:idx_9060_end+1] + SUB_INSERT + content[idx_9060_end+1:]
    print("SUB_CODES 7710-7760 inserted OK")
else:
    print(f"ERROR: unexpected line after 9060: {repr(next2_line)}")
    exit(1)

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: app.py patched successfully")
