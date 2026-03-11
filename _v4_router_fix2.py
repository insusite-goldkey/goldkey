# -*- coding: utf-8 -*-
"""gk_risk 라우터를 war_room 앞으로 이동"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

# war_room 블록 정확한 위치 찾기
war_idx = src.find('if cur == "war_room":')
gk_idx  = src.find('if cur == "gk_risk":')

print(f"war_room idx: {war_idx}")
print(f"gk_risk  idx: {gk_idx}")
print(repr(src[war_idx-160:war_idx+80]))
print("===")
print(repr(src[gk_idx-160:gk_idx+80]))
