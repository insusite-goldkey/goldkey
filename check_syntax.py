import ast, sys

files = [
    "D:/CascadeProjects/app.py",
    "D:/CascadeProjects/customer_mgmt.py",
    "D:/CascadeProjects/modules/auth.py",
]

all_ok = True
for path in files:
    try:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        ast.parse(src)
        print(f"OK : {path}")
    except SyntaxError as e:
        print(f"ERR: {path}  line {e.lineno}: {e.msg}")
        all_ok = False
    except Exception as e:
        print(f"ERR: {path}  {e}")
        all_ok = False

print("---")
print("RESULT: ALL OK" if all_ok else "RESULT: ERRORS FOUND")
sys.exit(0 if all_ok else 1)
