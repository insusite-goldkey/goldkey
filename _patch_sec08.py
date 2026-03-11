with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ── 1. SECTOR_CODES에 GK-SEC-08 등록 ──────────────────────────────────────
OLD_SECTOR = '"7700": {"name": "자동차보험 전술 상담 센터"'
if OLD_SECTOR not in content:
    print("ERROR: 7700 anchor not found"); exit(1)

idx_7700 = content.find(OLD_SECTOR)
line_end = content.find('\n', idx_7700)
INSERT_SECTOR = '\n    # ── GK-SEC-08: 화재·특종보험 전술 상담 센터 ───────────────────────────────\n    "8800": {"name": "화재·특종보험 전술 상담 센터", "tab_key": "gk_sec08", "keywords": ["화재보험전술", "gk-sec-08", "화재특종센터", "화재보험상담", "건물평가엔진", "재조달가액", "시가평가", "감가상각", "실화책임법", "민758조", "화재배상책임", "특수건물신체배상", "건설공사보험", "패키지보험", "승강기보험", "가스사고배상", "음식물배상", "재난배상", "전문직배상", "80%전부보험", "비례보상", "독립책임액", "손비처리", "법인보험료"]},\n'
content = content[:line_end] + INSERT_SECTOR + content[line_end:]
print("SECTOR_CODES 8800 OK")

# ── 2. SUB_CODES에 8810~8860 등록 ─────────────────────────────────────────
OLD_SUB = '"7760": {"name": "필수 질문 리스트(FC용)"'
if OLD_SUB not in content:
    print("ERROR: 7760 sub anchor not found"); exit(1)

idx_7760 = content.find(OLD_SUB)
line_end2 = content.find('\n', idx_7760)
INSERT_SUB = '\n    # ── 8800: 화재·특종보험 전술 상담 센터 ─────────────────────────────────────\n    "8810": {"name": "건물 진단 & 가액 평가",     "tab_key": "gk_sec08", "keywords": ["건물급수판정", "재조달가액평가", "시가평가", "감가상각잔가율", "건축물대장분석"]},\n    "8820": {"name": "재물보험 전술",              "tab_key": "gk_sec08", "keywords": ["주택화재보험", "일반화재보험", "공장물건요율", "전부보험인정", "소멸성장기적립"]},\n    "8830": {"name": "배상책임 전술",              "tab_key": "gk_sec08", "keywords": ["화재배상대인대물", "특수건물신체배상", "임차인원상복구", "구상권방어상법682조"]},\n    "8840": {"name": "특종보험 체크리스트",        "tab_key": "gk_sec08", "keywords": ["의무보험체크리스트", "건설공사보험", "패키지재산종합", "업종별담보매칭"]},\n    "8850": {"name": "보상 실무 RAG",              "tab_key": "gk_sec08", "keywords": ["실화법판례", "중복보험안분", "독립책임액계산", "기왕증상계"]},\n    "8860": {"name": "기업·개인사업자 세무전략",  "tab_key": "gk_sec08", "keywords": ["보험료손비처리", "법인세무전략", "개인사업자필요경비", "종합소득세율보험"]},\n'
content = content[:line_end2] + INSERT_SUB + content[line_end2:]
print("SUB_CODES 8810-8860 OK")

# ── 3. 탭 라우터에 gk_sec08 진입점 추가 ──────────────────────────────────
OLD_ROUTER = '    # ══════════════════════════════════════════════════════════════════════\n    # [GK-SEC-07] 자동차보험 전술 상담 센터 라우터'
if OLD_ROUTER not in content:
    print("ERROR: sec07 router anchor not found"); exit(1)

INSERT_ROUTER = '    # ══════════════════════════════════════════════════════════════════════\n    # [GK-SEC-08] 화재·특종보험 전술 상담 센터 라우터\n    # ══════════════════════════════════════════════════════════════════════\n    if cur == "gk_sec08":\n        if not _auth_gate("gk_sec08"): st.stop()\n        _render_gk_sec08()\n        st.stop()\n\n    ' + OLD_ROUTER
content = content.replace(OLD_ROUTER, INSERT_ROUTER, 1)
print("Router gk_sec08 OK")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE: patch_sec08 step1 complete")
