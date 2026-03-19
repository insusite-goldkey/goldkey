"""앱 코드 구문 체크"""
import sys, os, ast, traceback
os.chdir(r"D:\CascadeProjects")

with open("app.py", encoding="utf-8-sig") as f:
    src = f.read()

try:
    ast.parse(src)
    with open("_syntax_result.txt","w",encoding="utf-8") as out:
        out.write("SYNTAX OK\n")
    sys.exit(0)
except SyntaxError as e:
    msg = f"SyntaxError line {e.lineno}: {e.msg}\n  text: {repr(e.text)}\n"
    with open("_syntax_result.txt","w",encoding="utf-8") as out:
        out.write(msg)
    sys.exit(0)
except Exception as e:
    with open("_syntax_result.txt","w",encoding="utf-8") as out:
        out.write(traceback.format_exc())
    sys.exit(0)

