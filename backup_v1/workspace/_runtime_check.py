"""
앱의 모듈 레벨 코드를 실행해서 런타임 에러를 찾는 스크립트.
실제 Streamlit 없이 import-only 레벨 에러를 잡는다.
"""
import sys, os, traceback

os.chdir(r"D:\CascadeProjects")

# 1) ast parse
import ast
with open("app.py", encoding="utf-8") as f:
    src = f.read()

try:
    tree = ast.parse(src)
    print("AST: OK")
except SyntaxError as e:
    print(f"AST SyntaxError line={e.lineno}: {e.msg}")
    print(f"  text: {e.text}")
    sys.exit(1)

# 2) 모든 함수 정의 검사 (indent 에러 등)
print(f"Total lines: {src.count(chr(10))}")
print(f"Total functions: {sum(1 for n in ast.walk(tree) if isinstance(n, ast.FunctionDef))}")

# 3) 특정 패턴 검사
import re
# @st.fragment 데코레이터가 붙은 함수 찾기
frag_funcs = []
for m in re.finditer(r'@st\.fragment[^\n]*\ndef (\w+)', src):
    frag_funcs.append(m.group(1))
print(f"@st.fragment functions: {frag_funcs}")

# @st.cache_data가 붙은 함수 찾기
cache_funcs = []
for m in re.finditer(r'@st\.cache_data[^\n]*\ndef (\w+)', src):
    cache_funcs.append(m.group(1))
print(f"@st.cache_data functions: {cache_funcs}")

# weather 관련 함수 검사
for func_name in ["get_location_by_ip", "fetch_weather_data", "weather_bar_fragment"]:
    count = src.count(f"def {func_name}")
    calls = src.count(f"{func_name}(")
    print(f"  {func_name}: def={count}, calls={calls}")

print("\nDone.")
