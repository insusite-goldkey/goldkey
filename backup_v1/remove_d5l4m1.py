"""D5-L4-M1 dead code 삭제: line 33718~33722 (0-indexed 33717~33722)"""
with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    lines = f.readlines()

# 0-indexed: line 33718 = index 33717, line 33722 = index 33721
# line 33723 (빈줄)도 포함해서 삭제 → index 33722
START = 33717
END   = 33723  # exclusive (line 33724부터 유지)

print("START:", repr(lines[START][:80]))
print("END-1:", repr(lines[END-1][:80]))
print("END(kept):", repr(lines[END][:80]))

new_lines = lines[:START] + lines[END:]

with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"완료: {END - START}줄 제거, 총 {len(new_lines)}줄")
