"""
Streamlit 없이 app.py의 모든 import + 모듈레벨 코드 실행 에러를 잡는다.
st를 mock으로 대체해서 모듈레벨 코드가 실행될 때 에러를 포착.
"""
import sys, os, traceback, types
os.chdir(r"D:\CascadeProjects")
sys.path.insert(0, r"D:\CascadeProjects")

# ── st mock 생성 ──────────────────────────────────────────────────────────
class _MockDecorator:
    def __call__(self, *a, **kw):
        if len(a) == 1 and callable(a[0]):
            return a[0]  # @st.cache_data 처럼 인자 없이 사용
        def wrapper(fn): return fn
        return wrapper
    def __getattr__(self, name): return _MockDecorator()

class _MockSt:
    def __getattr__(self, name): return _MockDecorator()
    cache_data = _MockDecorator()
    cache_resource = _MockDecorator()
    fragment = _MockDecorator()

sys.modules['streamlit'] = _MockSt()

# ── 실제 실행 ─────────────────────────────────────────────────────────────
try:
    with open("app.py", encoding="utf-8") as f:
        src = f.read()
    code = compile(src, "app.py", "exec")
    glob = {"__name__": "__main__", "__file__": "app.py"}
    exec(code, glob)
    print("EXEC OK — 모듈 레벨 에러 없음")
except SyntaxError as e:
    print(f"SyntaxError L{e.lineno}: {e.msg}")
    print(f"  text: {e.text}")
except Exception as e:
    tb = traceback.format_exc()
    print(f"RuntimeError: {type(e).__name__}: {e}")
    # 마지막 10줄만 출력
    lines = tb.strip().splitlines()
    for l in lines[-20:]:
        print(l)
