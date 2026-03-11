lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()
for i, ln in enumerate(lines):
    if 'load_members' in ln or 'save_members' in ln or 'encrypt_contact' in ln:
        print(f'L{i+1}: {ln[:120].rstrip()}')
