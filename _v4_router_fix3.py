# -*- coding: utf-8 -*-
"""gk_risk 라우터를 war_room 앞으로 이동 — 바이트 오프셋 기반"""

src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()

war_idx = src.find('if cur == "war_room":')
gk_idx  = src.find('if cur == "gk_risk":')

# war_room 이미 gk_risk보다 앞에 있음 → 교환 필요
print(f"war_room at {war_idx}, gk_risk at {gk_idx}")
if war_idx < gk_idx:
    # war_room 블록 앞 코멘트 시작점 찾기 (# ══ 라인)
    war_block_start = src.rfind('\n    # ═', 0, war_idx)
    war_block_end   = src.find('\n    # ═', war_idx)  # 다음 블록 시작

    gk_block_start  = src.rfind('\n    # ═', 0, gk_idx)
    gk_block_end    = src.find('\n    # ═', gk_idx)    # 다음 블록 시작

    war_block = src[war_block_start:war_block_end]
    gk_block  = src[gk_block_start:gk_block_end]

    print(f"war_block: {war_block_start}~{war_block_end} ({len(war_block)}chars)")
    print(f"gk_block:  {gk_block_start}~{gk_block_end} ({len(gk_block)}chars)")
    print("war_block:", repr(war_block[:120]))
    print("gk_block:",  repr(gk_block[:120]))

    # 두 블록을 교환: war_block + gk_block → gk_block + war_block
    # war_block이 먼저 오므로: src[...war_block_start] + gk_block + war_block + src[gk_block_end...]
    new_src = (
        src[:war_block_start]
        + gk_block.replace("전략적 위험 분석 사령부 라우터", "전략적 위험 분석 사령부 라우터 — ★ 최우선")
        + war_block
        + src[gk_block_end:]
    )
    open('D:/CascadeProjects/app.py', 'w', encoding='utf-8').write(new_src)
    print(f"✓ 교환 완료. 총 줄 수: {len(new_src.split(chr(10)))}")
else:
    print("이미 gk_risk가 war_room 앞에 있음 — 교환 불필요")
