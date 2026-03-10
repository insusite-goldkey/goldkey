
data = open('app_backup_20260310_1643.py', encoding='utf-8-sig').read()
idx = data.find('if cur == "home"')
chunk = data[idx:idx+10000]
open('_tmp_home_backup.txt', 'w', encoding='utf-8').write(chunk)
print(f"idx={idx}, written {len(chunk)} chars")
