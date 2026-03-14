
with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("TOTAL LINES:", len(lines))
print("LINE 39167:", repr(lines[39166][:80]))
print("LINE 39572:", repr(lines[39571][:80]))
print("LINE 39573:", repr(lines[39572][:80]))
