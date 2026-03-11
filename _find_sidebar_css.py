lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['stSidebar', 'sidebar', 'triple', '트리플 보안', '가문 안보', 'stSidebarUser']):
        if any(k in s for k in ['css', 'CSS', 'style', 'markdown', 'border', 'background', 'padding', '보안 가동', '트리플']):
            print(f'L{i+1}: {s[:120]}')
