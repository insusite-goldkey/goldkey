# -*- coding: utf-8 -*-
"""_PHARMA_ALERT_INFO desc 필드 멀티라인 → 단일 문자열 수정"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
lines = src.split('\n')

# 깨진 패턴: 문자열 내 실제 개행 → \\n 이스케이프로 교체
# chemo desc 블록
OLD_CHEMO_DESC = (
    '        "desc": (\n'
    '            "항암제 복용이 확인되었습니다. 다음 특약의 보장 공백을 즉시 점검하세요:\n'
    '"\n'
    '            "• 암 진단비 (특정암/소액암 구분 확인)\n'
    '"\n'
    '            "• 항암 방사선·약물치료비 특약\n'
    '"\n'
    '            "• 암 수술비 / 암 입원일당\n'
    '"\n'
    '            "• 비급여 항암치료비 보장 특약 (신약·표적치료)"\n'
    '        ),'
)
NEW_CHEMO_DESC = (
    '        "desc": (\n'
    '            "항암제 복용이 확인되었습니다. 다음 특약의 보장 공백을 즉시 점검하세요:\\n"\n'
    '            "• 암 진단비 (특정암/소액암 구분 확인)\\n"\n'
    '            "• 항암 방사선·약물치료비 특약\\n"\n'
    '            "• 암 수술비 / 암 입원일당\\n"\n'
    '            "• 비급여 항암치료비 보장 특약 (신약·표적치료)"\n'
    '        ),'
)
cnt1 = src.count(OLD_CHEMO_DESC)
print(f"chemo desc count: {cnt1}")
if cnt1 == 1:
    src = src.replace(OLD_CHEMO_DESC, NEW_CHEMO_DESC, 1)
    print("✓ chemo desc 수정")

# rare desc 블록
OLD_RARE_DESC = (
    '        "desc": (\n'
    '            "희귀난치성 질환 치료제가 감지되었습니다. 다음을 즉시 확인하세요:\n'
    '"\n'
    '            "• 희귀질환 입원·수술 특약 보장 여부\n'
    '"\n'
    '            "• 중증질환(산정특례) 진단비 특약\n'
    '"\n'
    '            "• 간병인 지원 및 장기간병(LCI) 특약\n'
    '"\n'
    '            "• 실손보험 급여/비급여 본인부담금 한도"\n'
    '        ),'
)
NEW_RARE_DESC = (
    '        "desc": (\n'
    '            "희귀난치성 질환 치료제가 감지되었습니다. 다음을 즉시 확인하세요:\\n"\n'
    '            "• 희귀질환 입원·수술 특약 보장 여부\\n"\n'
    '            "• 중증질환(산정특례) 진단비 특약\\n"\n'
    '            "• 간병인 지원 및 장기간병(LCI) 특약\\n"\n'
    '            "• 실손보험 급여/비급여 본인부담금 한도"\n'
    '        ),'
)
cnt2 = src.count(OLD_RARE_DESC)
print(f"rare desc count: {cnt2}")
if cnt2 == 1:
    src = src.replace(OLD_RARE_DESC, NEW_RARE_DESC, 1)
    print("✓ rare desc 수정")

if cnt1 != 1 or cnt2 != 1:
    # 라인 단위 수정
    new_lines = []
    i = 0
    while i < len(lines):
        l = lines[i]
        # 패턴: "...한국어 텍스트 마지막" 으로 끝나는 문자열 다음 줄이 '"' 단독인 경우
        # 이는 문자열 내 개행이 실제 개행으로 삽입된 것
        if (i + 1 < len(lines) and lines[i+1].strip() == '"'
                and l.strip().startswith('"') and not l.strip().endswith('",')
                and not l.strip().endswith(')')):
            # 현재 라인의 닫는 " 제거하고 \\n" 추가
            stripped = l.rstrip()
            if stripped.endswith('"'):
                new_lines.append(stripped[:-1] + '\\n"')
            else:
                new_lines.append(l)
            i += 1
            # 다음 줄 '"' 스킵
            continue
        new_lines.append(l)
        i += 1
    src = '\n'.join(new_lines)
    print(f"✓ 라인 단위 수정 완료")

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
print(f"총 줄 수: {len(src.split(chr(10)))}")
