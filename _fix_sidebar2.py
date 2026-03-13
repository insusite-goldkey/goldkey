with open('app.py', encoding='utf-8') as f:
    content = f.read()

# 1. layout 항상 wide 고정
old = '    _layout_mode = "wide" if (st.session_state.get("user_id") or st.session_state.get("authenticated")) else "centered"'
new = '    _layout_mode = "wide"'
assert old in content, "패턴1 미발견"
content = content.replace(old, new, 1)
print("Fix1 done: layout always wide")

# 2. 충돌하는 collapsedControl display:none CSS 블록 제거
old2 = (
    '[data-testid="collapsedControl"] {\n'
    '    display: none !important;\n'
    '}\n'
    '</style>""", unsafe_allow_html=True)\n'
)
new2 = '</style>""", unsafe_allow_html=True)\n'
assert old2 in content, "패턴2 미발견"
content = content.replace(old2, new2, 1)
print("Fix2 done: removed collapsedControl display:none conflict")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SAVED OK")
