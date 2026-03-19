"""
SECTION 9-A/9 자가복구 블록을 main() 내부 로컬 스코프에서
전역 스코프로 꺼내는 스크립트.

현재 상태:
  - line 58597~59482: main() 내부에 4스페이스 들여쓰기로 갇혀 있음
  - line 59483: _run_safe() 는 전역 (유지)

변환:
  - 58597~59482 범위 각 줄의 선두 4스페이스 제거
  - 단, 빈 줄(공백만)은 그대로 유지
  - line 58595~58596(빈줄 2개)는 main() 닫힘 직후가 되도록 유지
"""

with open("D:/CascadeProjects/app.py", encoding="utf-8") as f:
    lines = f.readlines()

# 0-indexed: line 58597 = index 58596, line 59482 = index 59481
START = 58596   # 0-indexed (line 58597) — "    # -----[SECTION 9-A]..."
END   = 59481   # 0-indexed inclusive (line 59482) — "                    break"

print(f"총 라인 수: {len(lines)}")
print(f"START ({START+1}):", repr(lines[START][:80]))
print(f"END   ({END+1}):",   repr(lines[END][:80]))

# 검증: 해당 범위 모두 4스페이스 들여쓰기 or 빈줄인지 확인
errors = []
for i in range(START, END + 1):
    line = lines[i]
    if line.strip() == "":
        continue  # 빈줄 OK
    if not line.startswith("    "):
        errors.append((i + 1, repr(line[:40])))

if errors:
    print(f"\n⚠️ 4스페이스 들여쓰기 없는 줄 {len(errors)}개 발견:")
    for ln, txt in errors[:10]:
        print(f"  line {ln}: {txt}")
    print("\n→ 변환을 중단합니다. 직접 확인 필요.")
else:
    print(f"\n✅ 검증 통과 — {END - START + 1}줄 전부 들여쓰기 제거 진행")
    new_lines = []
    for i, line in enumerate(lines):
        if START <= i <= END:
            if line.startswith("    "):
                new_lines.append(line[4:])  # 4스페이스 제거
            else:
                new_lines.append(line)      # 빈줄 그대로
        else:
            new_lines.append(line)

    with open("D:/CascadeProjects/app.py", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print(f"완료: {END - START + 1}줄 들여쓰기 제거, 총 {len(new_lines)}줄")
