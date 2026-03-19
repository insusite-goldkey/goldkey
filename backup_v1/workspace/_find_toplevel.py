"""모듈 최상위에서 실행되는 코드 중 try/except 밖 비안전 호출 찾기"""
import ast

with open('app.py', encoding='utf-8') as f:
    src = f.read()

tree = ast.parse(src)

print("=== 모듈 최상위 실행문 (함수/클래스 밖) ===")
for node in tree.body:
    # 함수/클래스 정의, import, 할당은 제외
    # Try 블록도 보호되므로 제외
    # 위험한 것: 단순 Expr (함수 호출) 중 st. 아닌 것
    if isinstance(node, ast.Expr):
        call = node.value
        if isinstance(call, ast.Call):
            ln = node.lineno
            # 함수 이름 추출
            if isinstance(call.func, ast.Name):
                fname = call.func.id
                print(f"  L{ln}: {fname}()")
            elif isinstance(call.func, ast.Attribute):
                obj = ""
                if isinstance(call.func.value, ast.Name):
                    obj = call.func.value.id + "."
                fname = obj + call.func.attr
                print(f"  L{ln}: {fname}()")
    elif isinstance(node, ast.Try):
        pass  # try 블록은 안전
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                           ast.Import, ast.ImportFrom, ast.Assign, ast.AugAssign,
                           ast.AnnAssign, ast.If, ast.For, ast.With)):
        pass  # 정상
    else:
        print(f"  L{node.lineno}: {type(node).__name__}")
