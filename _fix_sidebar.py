with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

# 28560줄 (0-indexed: 28559) = '</style>""", unsafe_allow_html=True)' 확인
print('Target line:', repr(lines[28559][:80]))

css_inject = (
    '\n'
    '    # ── [제53조 §CSS] 사이드바 강제 열기 CSS ──────────────────────────────\n'
    '    st.markdown("""<style>\n'
    'section[data-testid="stSidebar"] {\n'
    '    display: flex !important;\n'
    '    visibility: visible !important;\n'
    '    transform: translateX(0) !important;\n'
    '    min-width: 240px !important;\n'
    '    left: 0 !important;\n'
    '}\n'
    'section[data-testid="stSidebar"][aria-expanded="false"] {\n'
    '    display: flex !important;\n'
    '    transform: translateX(0) !important;\n'
    '    min-width: 240px !important;\n'
    '}\n'
    '[data-testid="collapsedControl"] {\n'
    '    display: none !important;\n'
    '}\n'
    '</style>""", unsafe_allow_html=True)\n'
    '\n'
)

lines.insert(28560, css_inject)

with open('app.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print('DONE - inserted at 28561, total lines:', len(lines))
