import ast, sys

src = open('app.py', encoding='utf-8').read()
tree = ast.parse(src)

# main() 함수 찾기
for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef) and node.name == 'main':
        # main() 내부에서 with st.sidebar: 찾기
        for stmt in ast.walk(node):
            if isinstance(stmt, ast.With):
                for item in stmt.items:
                    ctx = item.context_expr
                    # st.sidebar 또는 st.sidebar 형태
                    src_fragment = ast.unparse(ctx)
                    if 'sidebar' in src_fragment:
                        print(f"with st.sidebar: line {stmt.lineno} ~ {stmt.end_lineno}")
                        # 블록 내용 요약
                        for s in stmt.body:
                            print(f"  body stmt: line {s.lineno} ~ {s.end_lineno} | {type(s).__name__}: {ast.unparse(s)[:60]}")
                        sys.exit(0)
