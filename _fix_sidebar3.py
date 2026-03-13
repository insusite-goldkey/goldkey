with open('app.py', encoding='utf-8') as f:
    content = f.read()

OLD = '''    # ── [제53조 §CSS] 사이드바 강제 열기 CSS ──────────────────────────────
    st.markdown("""<style>
section[data-testid="stSidebar"] {
    display: flex !important;
    visibility: visible !important;
    transform: translateX(0) !important;
    min-width: 240px !important;
    left: 0 !important;
}
section[data-testid="stSidebar"][aria-expanded="false"] {
    display: flex !important;
    transform: translateX(0) !important;
    min-width: 240px !important;
}
</style>""", unsafe_allow_html=True)'''

NEW = '''    # ── [제53조 §CSS] 사이드바 강제 열기 CSS (aria-expanded 무관 항상 표시) ──
    st.markdown("""<style>
/* collapsed 버튼(☰) 완전 숨김 - 사이드바 닫기 방지 */
[data-testid="collapsedControl"],
button[data-testid="collapsedControl"] {
    display: none !important;
    width: 0 !important;
    overflow: hidden !important;
}
/* 사이드바 닫기 버튼 숨김 */
[data-testid="stSidebarCollapseButton"],
button[aria-label="Collapse sidebar"],
button[aria-label="사이드바를 열거나 닫으세요"] {
    display: none !important;
}
/* 사이드바 항상 표시 - aria-expanded 값 무관 */
section[data-testid="stSidebar"] {
    transform: none !important;
    translate: none !important;
    left: 0 !important;
    position: relative !important;
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    min-width: 244px !important;
    width: 244px !important;
    max-width: 320px !important;
    flex-shrink: 0 !important;
    pointer-events: auto !important;
}
section[data-testid="stSidebar"] > div:first-child {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    width: 100% !important;
    overflow-y: auto !important;
    overflow-x: hidden !important;
}
/* 메인 컨테이너가 사이드바 옆에 위치하도록 */
[data-testid="stAppViewContainer"] {
    flex-direction: row !important;
}
[data-testid="stMain"] {
    flex: 1 !important;
    min-width: 0 !important;
}
</style>""", unsafe_allow_html=True)'''

assert OLD in content, "교체 대상 코드를 찾을 수 없습니다"
content = content.replace(OLD, NEW, 1)
print("Fix done: 사이드바 강제 표시 CSS 교체")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("SAVED OK")
