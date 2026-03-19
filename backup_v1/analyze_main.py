"""
main() 함수 내 if not _is_auth_now: 블록의 실제 AST 구조 분석
"""
import ast

SRC = "D:/CascadeProjects/app.py"

with open(SRC, encoding="utf-8") as f:
    src = f.read()

tree = ast.parse(src)

# main() 함수 찾기
main_func = None
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == "main":
        main_func = node
        break

if not main_func:
    print("main() 못 찾음")
    exit()

print(f"main() 위치: line {main_func.lineno}~{main_func.end_lineno}")

# main() 내 if not _is_auth_now: 블록 찾기
for stmt in ast.walk(main_func):
    if isinstance(stmt, ast.If):
        # 조건이 'not _is_auth_now' 형태인지 확인
        cond = stmt.test
        if isinstance(cond, ast.UnaryOp) and isinstance(cond.op, ast.Not):
            name = getattr(cond.operand, 'id', None)
            if name == '_is_auth_now':
                print(f"\nif not _is_auth_now: line {stmt.lineno}~{stmt.end_lineno}")
                print(f"  body 첫 줄: {stmt.body[0].lineno}")
                print(f"  body 마지막 줄: {stmt.body[-1].end_lineno}")
                
                # body 마지막 5개 statement
                print("\n  body 마지막 5개 statement:")
                for s in stmt.body[-5:]:
                    print(f"    line {s.lineno}~{s.end_lineno}: {type(s).__name__} | {ast.dump(s)[:80]}")
