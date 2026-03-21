import ast
for f in ["shared_components.py", "crm_app.py"]:
    ast.parse(open(f, encoding="utf-8-sig").read())
    print(f"SYNTAX OK: {f}")
