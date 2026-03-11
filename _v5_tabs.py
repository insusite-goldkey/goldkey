# -*- coding: utf-8 -*-
"""V5: 탭 5→6 확장 + _stab6 블록 추가"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# ── 탭 6개로 확장 ──
OLD_5TABS = (
    '    _stab1, _stab2, _stab3, _stab4, _stab5 = st.tabs([\n'
    '        "\U0001f3e5 실손보험 분석", "\U0001f480 생명보험 갭", "\U0001f3c6 최적 상품 추천", "\u2696\ufe0f 법령 검색", "\U0001f52c KCD 상세",\n'
    '    ])'
)
cnt = src.count(OLD_5TABS)
print(f"OLD_5TABS count: {cnt}")

# 실제 탭 라인을 직접 찾아서 교체
idx = src.find('_stab1, _stab2, _stab3, _stab4, _stab5 = st.tabs([')
if idx == -1:
    print("ERROR: tabs line not found")
else:
    # 탭 선언 블록 끝 찾기 (])')
    end_idx = src.find('])', idx)
    old_block = src[idx:end_idx+2]
    print(f"old_block: {repr(old_block)}")

    new_block = (
        '_stab1, _stab2, _stab3, _stab4, _stab5, _stab6 = st.tabs([\n'
        '        "\U0001f3e5 실손보험 분석", "\U0001f480 생명보험 갭", "\U0001f3c6 최적 상품 추천",\n'
        '        "\u2696\ufe0f 법령 검색", "\U0001f52c KCD 상세", "\U0001f3e2 사업자 조회",\n'
        '    ])'
    )
    src = src[:idx] + new_block + src[end_idx+2:]
    print("✓ 탭 6개로 확장")

# ── _stab6 블록 추가 ──
OLD_END = (
    "        else:\n"
    "            st.info(\"좌측 'KCD 질병 검색'에서 질병코드를 선택하면 상세 분석이 표시됩니다.\")\n"
    "\n\n\ndef _render_gk_job():"
)
cnt2 = src.count(OLD_END)
print(f"OLD_END count: {cnt2}")

if cnt2 == 1:
    NEW_END = (
        "        else:\n"
        "            st.info(\"좌측 'KCD 질병 검색'에서 질병코드를 선택하면 상세 분석이 표시됩니다.\")\n"
        "\n"
        "    with _stab6:\n"
        "        render_biz_status_panel(session_key=\"risk_biz\")\n"
        "\n\n\ndef _render_gk_job():"
    )
    src = src.replace(OLD_END, NEW_END, 1)
    print("✓ _stab6 블록 추가")
else:
    # 대안: 줄 기반으로 찾기
    lines = src.split('\n')
    for i, l in enumerate(lines):
        if l == "        else:":
            # 다음 줄이 KCD info인지 확인
            if i+1 < len(lines) and "KCD 질병 검색" in lines[i+1]:
                # i+1 이후 빈줄 연속 + def _render_gk_job 찾기
                j = i+2
                while j < len(lines) and lines[j].strip() == '':
                    j += 1
                if j < len(lines) and 'def _render_gk_job' in lines[j]:
                    lines.insert(i+2, '    with _stab6:')
                    lines.insert(i+3, '        render_biz_status_panel(session_key="risk_biz")')
                    src = '\n'.join(lines)
                    print(f"✓ _stab6 블록 줄 삽입 (line {i+2})")
                    break

open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(src)
print(f"OK total lines: {len(src.split(chr(10)))}")
