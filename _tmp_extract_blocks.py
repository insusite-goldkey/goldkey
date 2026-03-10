
data = open('app.py', encoding='utf-8-sig').read()
lines = data.splitlines()

# home 탭 범위
start_line = None
end_line = None
for i, line in enumerate(lines):
    if '    if cur == "home":' in line and start_line is None:
        start_line = i
for i, line in enumerate(lines):
    if i > (start_line or 0) and line.startswith('    # \u2550\u2550'):
        end_line = i
        break

chunk_lines = lines[start_line:end_line]

# 주요 섹션 마커 찾기
markers = [
    'gk-g220-customer', '고객 정보', '고객 검색',
    '상담노트', 'consult_notes', '상담 노트',
    '보험 가입 상담', 'insurance_consults',
    '_agent_todo', '_agent_appt', '_agent_wait',
    'gk-g220-term', '보험 용어', '_voice_navigate',
    'gk-g220-gateway', '포트폴리오', '_go_tab',
    'gk-g220-contact', '보험사', '연락처',
    '_gp68', '_gp71', '3단계', '매트릭스',
    'gk-g220-nav', '통합 검색',
]

for marker in markers:
    for i, line in enumerate(chunk_lines):
        if marker in line:
            print(f"[{marker}] L{start_line+i+1}: {line[:100]}")
            break
