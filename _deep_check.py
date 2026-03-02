"""
HF Space 환경에서만 실패하는 에러를 찾는다.
HF는 Python 3.10, 로컬은 Python 3.12 — 버전 차이로 인한 에러 검출.
"""
import sys, ast, re

with open("app.py", encoding="utf-8") as f:
    src = f.read()
    lines = src.splitlines()

print(f"Python version: {sys.version}")
print(f"Total lines: {len(lines)}")

# ── 1. match 문 (Python 3.10+ 전용) ──────────────────────────────────────
print("\n=== match 문 (Python 3.10 이상) ===")
for i, ln in enumerate(lines, 1):
    stripped = ln.strip()
    if re.match(r'^match\s+\w', stripped):
        print(f"  L{i}: {ln.rstrip()}")

# ── 2. 타입 힌트 Union | 문법 (3.10+) ──────────────────────────────────
print("\n=== X | Y 타입 힌트 (3.10+) ===")
count = 0
for i, ln in enumerate(lines, 1):
    if re.search(r':\s*\w+\s*\|\s*\w+', ln) and 'def ' in ln:
        print(f"  L{i}: {ln.rstrip()}")
        count += 1
        if count > 10:
            print("  ... (생략)")
            break

# ── 3. walrus operator := (3.8+이지만 중첩 시 3.10에서 버그 있음) ──────
# 스킵

# ── 4. ExceptionGroup (3.11+) ───────────────────────────────────────────
print("\n=== ExceptionGroup / except* (3.11+) ===")
for i, ln in enumerate(lines, 1):
    if 'ExceptionGroup' in ln or 'except*' in ln:
        print(f"  L{i}: {ln.rstrip()}")

# ── 5. 모듈 레벨에서 즉시 실행되는 외부 API/네트워크 코드 ──────────────
print("\n=== 모듈 레벨 즉시 실행 (외부 I/O 의심) ===")
tree = ast.parse(src)
# 모듈 레벨 함수 호출 중 네트워크 의심 함수명
NET_FUNCS = {'requests','httpx','urllib','socket','supabase','get','post','connect'}
for node in ast.iter_child_nodes(tree):
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        func = node.value.func
        func_name = ""
        if isinstance(func, ast.Attribute):
            func_name = func.attr
        elif isinstance(func, ast.Name):
            func_name = func.id
        if any(n in func_name.lower() for n in NET_FUNCS):
            print(f"  L{node.lineno}: {lines[node.lineno-1].rstrip()}")

# ── 6. st.set_page_config 위치 확인 (모듈 레벨이면 안됨) ───────────────
print("\n=== st.set_page_config 위치 ===")
for i, ln in enumerate(lines, 1):
    if 'set_page_config' in ln and not ln.strip().startswith('#'):
        # 해당 줄의 들여쓰기 확인
        indent = len(ln) - len(ln.lstrip())
        print(f"  L{i} (indent={indent}): {ln.rstrip()}")

# ── 7. playwright / selenium 모듈 레벨 import ───────────────────────────
print("\n=== playwright 관련 모듈 레벨 코드 ===")
for i, ln in enumerate(lines, 1):
    stripped = ln.strip()
    if 'playwright' in stripped and stripped.startswith('import'):
        print(f"  L{i}: {ln.rstrip()}")

# ── 8. @st.cache_resource 에 hash_funcs 파라미터 (1.41에서 제거됨) ──────
print("\n=== @st.cache_resource hash_funcs ===")
for i, ln in enumerate(lines, 1):
    if 'cache_resource' in ln and 'hash_funcs' in ln:
        print(f"  L{i}: {ln.rstrip()}")

# ── 9. st.experimental_* (deprecated in 1.38+) ─────────────────────────
print("\n=== st.experimental_* 잔재 ===")
for i, ln in enumerate(lines, 1):
    if 'st.experimental_' in ln and not ln.strip().startswith('#'):
        print(f"  L{i}: {ln.rstrip()}")

# ── 10. @st.fragment 사용 목록 ──────────────────────────────────────────
print("\n=== @st.fragment 사용 목록 ===")
for i, ln in enumerate(lines, 1):
    if '@st.fragment' in ln:
        print(f"  L{i}: {ln.rstrip()}")

print("\nDone.")
