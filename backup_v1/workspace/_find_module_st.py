"""
모듈 레벨(함수/클래스 밖)에서 st.write, st.error, st.markdown 등
실제 UI 렌더링 명령이 호출되는 곳을 찾는다.
@st.cache_resource 등 데코레이터는 제외.
"""
import ast

with open('app.py', encoding='utf-8') as f:
    src = f.read()

tree = ast.parse(src)

# 모듈 최상위 노드에서 st. 함수 호출 찾기
# (함수/클래스 내부는 제외)
UI_CALLS = {
    'write', 'error', 'warning', 'info', 'success',
    'markdown', 'title', 'header', 'subheader', 'text',
    'sidebar', 'columns', 'expander', 'tabs',
    'set_page_config', 'rerun', 'stop',
}

for node in tree.body:  # 모듈 최상위만
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute):
                if isinstance(func.value, ast.Name) and func.value.id == 'st':
                    if func.attr in UI_CALLS:
                        print(f"L{child.lineno}: st.{func.attr}()")
