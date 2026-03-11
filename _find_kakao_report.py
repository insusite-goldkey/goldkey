lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
# SYSTEM_PROMPT 끝 위치
in_sys = False
for i, ln in enumerate(lines):
    if i == 19214:
        in_sys = True
    if in_sys and i > 19214:
        if ln.strip() == '"""' or (ln.startswith('"""') and i > 19220):
            print(f'SYSTEM_PROMPT END: L{i+1}')
            in_sys = False
            break

# 카카오톡 보고서 관련 함수
for i, ln in enumerate(lines):
    if any(k in ln for k in ['카카오', 'kakao', 'KakaoTalk', '_send_report', 'kakao_report',
                              '_build_kakao', '_render_report_send', 'send_msg', '_format_report']):
        if any(k in ln.lower() for k in ['def ', 'report', 'send', 'format', 'build', 'text']):
            print(f'L{i+1}: {ln[:120].rstrip()}')
