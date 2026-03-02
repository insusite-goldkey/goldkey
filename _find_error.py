"""앱 코드에서 실제 런타임 에러 위치를 찾는 스크립트"""
import sys, os, re
os.chdir(r"D:\CascadeProjects")

with open("app.py", encoding="utf-8") as f:
    lines = f.readlines()

src = "".join(lines)

# 1. st.fragment 관련 - run_every 파라미터 타입 확인
print("=== @st.fragment run_every 파라미터 ===")
for i, line in enumerate(lines, 1):
    if "st.fragment" in line and "run_every" in line:
        print(f"  L{i}: {line.rstrip()}")

# 2. st.cache_data ttl 파라미터 확인
print("\n=== @st.cache_data ttl 파라미터 ===")
for i, line in enumerate(lines, 1):
    if "st.cache_data" in line and "ttl" in line:
        print(f"  L{i}: {line.rstrip()}")

# 3. httpx import 위치 확인
print("\n=== httpx import 위치 ===")
for i, line in enumerate(lines, 1):
    if "import httpx" in line or "httpx" in line and "import" in line:
        print(f"  L{i}: {line.rstrip()}")

# 4. streamlit_js_eval 잔재 확인
print("\n=== streamlit_js_eval 잔재 ===")
for i, line in enumerate(lines, 1):
    if "streamlit_js_eval" in line or "get_geolocation" in line:
        print(f"  L{i}: {line.rstrip()}")

# 5. weather_bar_fragment 호출 위치
print("\n=== weather_bar_fragment 호출 ===")
for i, line in enumerate(lines, 1):
    if "weather_bar_fragment" in line:
        print(f"  L{i}: {line.rstrip()}")

# 6. st.set_page_config 위치 (한 번만 호출되어야 함)
print("\n=== st.set_page_config ===")
for i, line in enumerate(lines, 1):
    if "set_page_config" in line:
        print(f"  L{i}: {line.rstrip()}")

# 7. IndentationError 가능성 - def 뒤 빈 함수체 확인
import ast
try:
    tree = ast.parse(src)
    # 빈 함수 body 찾기
    empty_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if len(node.body) == 0:
                empty_funcs.append(f"L{node.lineno}: {node.name}")
    if empty_funcs:
        print(f"\n=== 빈 함수 ({len(empty_funcs)}개) ===")
        for f in empty_funcs:
            print(f"  {f}")
    else:
        print("\n=== 빈 함수: 없음 ===")
except Exception as e:
    print(f"\nAST 에러: {e}")

print("\nDone.")
