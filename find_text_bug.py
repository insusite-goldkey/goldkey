"""
app.py에서 Python AST를 이용해
'text' 이름이 Name(Load) 컨텍스트로 쓰이는 모든 위치를 출력.
(함수 파라미터나 할당 대상이 아닌, 값으로 읽히는 곳)
"""
import ast, sys

PATH = r'd:\CascadeProjects\app.py'

with open(PATH, encoding='utf-8', errors='replace') as f:
    src = f.read()

try:
    tree = ast.parse(src)
except SyntaxError as e:
    print(f"SyntaxError: {e}")
    sys.exit(1)

lines = src.splitlines()

class TextUsageFinder(ast.NodeVisitor):
    def __init__(self):
        self.hits = []
        # 함수 스코프 스택: 각 항목은 현재 함수에서 'text'가 정의(파라미터/할당)됐는지
        self._scopes = []  # list of set(defined names)

    def _current_scope_defines(self, name):
        for scope in reversed(self._scopes):
            if name in scope:
                return True
        return False

    def visit_FunctionDef(self, node):
        defined = set()
        # 파라미터 수집
        for arg in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            defined.add(arg.arg)
        if node.args.vararg:
            defined.add(node.args.vararg.arg)
        if node.args.kwarg:
            defined.add(node.args.kwarg.arg)
        self._scopes.append(defined)
        self.generic_visit(node)
        self._scopes.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Assign(self, node):
        # 할당 대상에서 text 정의 추적
        for t in node.targets:
            if isinstance(t, ast.Name) and self._scopes:
                self._scopes[-1].add(t.id)
        self.generic_visit(node)

    def visit_AugAssign(self, node):
        if isinstance(node.target, ast.Name) and self._scopes:
            self._scopes[-1].add(node.target.id)
        self.generic_visit(node)

    def visit_NamedExpr(self, node):
        if isinstance(node.target, ast.Name) and self._scopes:
            self._scopes[-1].add(node.target.id)
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == 'text' and isinstance(node.ctx, ast.Load):
            if not self._current_scope_defines('text'):
                lineno = node.lineno
                line_content = lines[lineno-1] if lineno <= len(lines) else ''
                self.hits.append((lineno, line_content.rstrip()))
        self.generic_visit(node)

finder = TextUsageFinder()
finder.visit(tree)

print(f"Found {len(finder.hits)} 'text' Load usages with no local definition:")
for lineno, content in finder.hits[:60]:
    print(f"LINE {lineno:6d}: {content[:120]}")
