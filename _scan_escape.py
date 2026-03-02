# f-string 내부에 있는 모든 단일 backslash + letter 패턴 탐지
# r"..." raw string은 제외, f"..." 또는 """...""" 내부만 체크
# 방법: py_compile로 각 라인 범위를 테스트

import py_compile, tempfile, os, shutil

with open('app.py', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
total = len(lines)

# 1000줄씩 나눠서 컴파일 — 에러 발생 구간 이진 탐색
def test_range(start, end):
    src = '\n'.join(lines[start:end])
    # 문법상 불완전할 수 있으므로 pass로 패딩
    src = 'if True:\n    pass\n' + src + '\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tf:
        tf.write(src)
        tfname = tf.name
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings('error', category=SyntaxWarning)
            py_compile.compile(tfname, doraise=True)
        return None
    except (py_compile.PyCompileError, SyntaxError) as e:
        return str(e)
    finally:
        os.unlink(tfname)

# 전체 파일 테스트
import warnings
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tf:
    tf.write(content)
    tfname = tf.name
try:
    with warnings.catch_warnings():
        warnings.filterwarnings('error', category=SyntaxWarning)
        py_compile.compile(tfname, doraise=True)
    print('FULL FILE: SYNTAX_OK')
except (py_compile.PyCompileError, SyntaxError) as e:
    print(f'FULL FILE ERROR: {e}')
finally:
    os.unlink(tfname)
