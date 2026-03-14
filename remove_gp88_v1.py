"""구버전 _gp88_hub() (line 17909~18298) 삭제 스크립트"""
with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    lines = f.readlines()

# 0-indexed: line 17909 = index 17908, line 18298 = index 18297
# 빈줄 포함 — 17908번째(comment)부터 18297번째(빈줄)까지 제거
# 실제 확인: lines[17908] 은 "# ── [가이딩 프로토콜 제88조]..."
# lines[18297] 은 빈줄 (18298번이 다음 블록 구분선)
START = 17908  # 0-indexed (line 17909) — "# ── [가이딩 프로토콜 제88조]..."
END   = 18299  # 0-indexed exclusive (line 18300 부터 유지 — "# ══ [GP94]...")

# 검증
print("START line:", repr(lines[START][:60]))
print("END-1 line:", repr(lines[END-1][:60]))
print("END line (kept):", repr(lines[END][:60]))

new_lines = lines[:START] + lines[END:]

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"완료: {END - START}줄 제거, 총 {len(new_lines)}줄")
