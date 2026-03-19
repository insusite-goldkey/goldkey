"""
with st.sidebar 블록 구조 및 st.stop() 위치 AST 분석
main() 내 with st.sidebar: 블록들의 정확한 위치와 그 안의 st.stop() 파악
"""
import ast

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    src = f.read()

tree = ast.parse(src)

main_func = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "main":
        main_func = node
        break

print(f"main() line {main_func.lineno}~{main_func.end_lineno}")
print()

# main() body 최상위 statement 목록 (indent=4 수준)
print("=== main() 최상위 statement 목록 (line 28648~35000) ===")
for stmt in main_func.body:
    if stmt.lineno > 35000:
        break
    stype = type(stmt).__name__
    # With 블록이면 context 표현도 출력
    extra = ""
    if isinstance(stmt, ast.With):
        for item in stmt.items:
            extra += ast.unparse(item.context_expr)[:40]
    elif isinstance(stmt, ast.If):
        extra = ast.unparse(stmt.test)[:40]
    
    # 내부에 st.stop() 있는지 확인
    has_stop = False
    for sub in ast.walk(stmt):
        if isinstance(sub, ast.Expr) and isinstance(sub.value, ast.Call):
            fn = sub.value.func
            if isinstance(fn, ast.Attribute) and fn.attr == "stop":
                has_stop = True
                break
    
    stop_marker = " ← ST.STOP!" if has_stop else ""
    print(f"  line {stmt.lineno:>6}~{stmt.end_lineno:<6} | {stype:<8} | {extra[:40]}{stop_marker}")
