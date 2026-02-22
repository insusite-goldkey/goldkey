# find_surrogate.py — app.py 내 surrogate 문자 위치 탐지
import unicodedata, sys

with open("D:/CascadeProjects/app.py", "r", encoding="utf-8", errors="surrogateescape") as f:
    content = f.read()

found = []
for i, ch in enumerate(content):
    if unicodedata.category(ch) == "Cs":
        # 전후 문맥 40자
        ctx = content[max(0,i-40):i+40]
        ctx_safe = ctx.encode("utf-8", errors="replace").decode("utf-8")
        # 해당 줄 번호 계산
        line_no = content[:i].count("\n") + 1
        found.append((i, line_no, hex(ord(ch)), ctx_safe))

if found:
    print(f"[발견] surrogate 문자 {len(found)}개:")
    for pos, line, code, ctx in found:
        print(f"  위치 {pos} / 줄 {line} / 코드 {code}")
        print(f"  문맥: ...{ctx}...")
        print()
else:
    print("[정상] app.py 파일 내 surrogate 문자 없음")
    print("→ 오류는 런타임 중 외부 입력(PDF, AI응답, 사용자입력)에서 발생")
    print("→ 발생 시점: Gemini API 호출 또는 PDF 처리 중")
