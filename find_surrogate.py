# find_surrogate.py — app.py + secrets.toml surrogate 탐지
import unicodedata, sys, os

def scan_file(path):
    print(f"\n=== 스캔: {path} ===")
    if not os.path.exists(path):
        print("  파일 없음")
        return
    # 1. 바이트 레벨 스캔 (UTF-8 디코딩 오류 위치)
    with open(path, "rb") as f:
        raw = f.read()
    try:
        raw.decode("utf-8")
        print("  [바이트] UTF-8 정상")
    except UnicodeDecodeError as e:
        print(f"  [바이트] UTF-8 디코딩 오류: position={e.start}-{e.end}, reason={e.reason}")
        print(f"  해당 바이트: {raw[e.start:e.end+2].hex()}")

    # 2. surrogateescape로 읽어서 surrogate 문자 탐지
    with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
        content = f.read()
    found = []
    for i, ch in enumerate(content):
        if unicodedata.category(ch) == "Cs":
            ctx = content[max(0,i-60):i+60].encode("utf-8", errors="replace").decode("utf-8")
            line_no = content[:i].count("\n") + 1
            found.append((i, line_no, hex(ord(ch)), ctx))
    if found:
        print(f"  [surrogate] {len(found)}개 발견:")
        for pos, line, code, ctx in found:
            print(f"    char위치={pos}, 줄={line}, 코드={code}")
            print(f"    문맥: ...{ctx}...")
    else:
        print("  [surrogate] 없음 - 파일 자체는 정상")

# app.py 스캔
scan_file("D:/CascadeProjects/app.py")

# secrets.toml 스캔 (API 키 등 설정값)
scan_file("D:/CascadeProjects/.streamlit/secrets.toml")

# workspace/insurance_bot.py 스캔
scan_file("D:/CascadeProjects/workspace/insurance_bot.py")

print("\n=== 스캔 완료 ===")
