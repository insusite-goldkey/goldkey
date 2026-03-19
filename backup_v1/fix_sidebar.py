"""
미인증 분기 st.stop() 전에 with st.sidebar: render_goldkey_sidebar() 삽입
line 28903: '        st.stop()' → 앞에 사이드바 렌더 코드 추가
"""
SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8-sig") as f:
    lines = f.readlines()

print(f"총 라인: {len(lines)}")

# line 28903 (0-indexed: 28902) 확인
target_line = lines[28902]
print(f"[28903] repr: {repr(target_line)}")

# 8칸 들여쓰기 + st.stop() 라인을 찾아 앞에 사이드바 렌더 삽입
TARGET = "        st.stop()\n"
INSERT_CODE = (
    "        # ── [★근본수정] 미인증 시 사이드바 렌더 — st.stop() 전에 실행\n"
    "        with st.sidebar:\n"
    "            render_goldkey_sidebar()\n"
)

if lines[28902] == TARGET:
    lines[28902] = INSERT_CODE + TARGET
    print("삽입 완료")
    with open(SRC, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("저장 완료")
else:
    print(f"불일치. 실제값: {repr(lines[28902])}")
    print("저장하지 않음")
