import re

with open('app.py', encoding='utf-8') as f:
    lines = f.readlines()

# All tab entry lines
tabs = []
for i, line in enumerate(lines, 1):
    m = re.search(r'if cur == "(\w+)"', line)
    if m:
        tabs.append((i, m.group(1)))

# For each tab, scan the next 30 lines for _bid()
print(f"{'TAB':<20} {'LINE':>6}  {'HAS_BID'}")
print("-" * 45)
for (lineno, tab) in tabs:
    # skip duplicate intro
    chunk = lines[lineno:lineno+35]
    has_bid = any('_bid(' in l for l in chunk)
    marker = "OK" if has_bid else "MISSING <<<<<"
    print(f"{tab:<20} {lineno:>6}  {marker}")
