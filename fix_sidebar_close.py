"""
사이드바 강제 닫힘 문제 근본 해결:
1) _auto_close_sidebar = True 5곳 → False로 변경 (닫힘 트리거 제거)
2) _auto_close_sidebar close JS 블록 자체 비활성화
"""

with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    content = f.read()

changes = 0

# ── 1) _auto_close_sidebar = True → False (5곳 전체) ───────────────────────
OLD_CLOSE = 'st.session_state["_auto_close_sidebar"] = True'
NEW_CLOSE = 'st.session_state["_auto_close_sidebar"] = False'
count = content.count(OLD_CLOSE)
if count > 0:
    content = content.replace(OLD_CLOSE, NEW_CLOSE)
    changes += count
    print(f"✅ _auto_close_sidebar = True → False ({count}곳)")
else:
    print("❌ _auto_close_sidebar = True 미발견")

# ── 2) close JS 블록 비활성화: pop() 후 JS 실행 조건을 False로 ───────────────
# 현재: if st.session_state.pop("_auto_close_sidebar", False):
# 변경: if False and st.session_state.pop("_auto_close_sidebar", False):
OLD_CLOSE_IF = '    if st.session_state.pop("_auto_close_sidebar", False):'
NEW_CLOSE_IF = '    if False and st.session_state.pop("_auto_close_sidebar", False):  # [비활성화] 로그인 후 사이드바 유지'
if OLD_CLOSE_IF in content:
    content = content.replace(OLD_CLOSE_IF, NEW_CLOSE_IF, 1)
    changes += 1
    print("✅ auto_close JS 블록 비활성화")
else:
    print("❌ auto_close JS if 블록 미발견")

print(f"\n총 {changes}건 수정 완료")

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("파일 저장 완료")
