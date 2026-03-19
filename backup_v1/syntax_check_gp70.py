import ast, sys
try:
    src = open("app.py", "rb").read().decode("utf-8-sig")
    ast.parse(src)
    open("syntax_result.txt", "w").write("SYNTAX_OK\n")
except SyntaxError as e:
    open("syntax_result.txt", "w").write(
        f"SYNTAX_ERROR: line {e.lineno} --- {e.msg}\n  text: {e.text}\n"
    )
    sys.exit(1)
