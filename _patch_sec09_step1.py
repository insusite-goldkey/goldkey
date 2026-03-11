with open('D:/CascadeProjects/app.py', encoding='utf-8') as f:
    content = f.read()

# ── 1. SECTOR_CODES에 GK-SEC-09 등록 ──
OLD_SECTOR = '"8800": {"name": "화재·특종보험 전술 상담 센터"'
if OLD_SECTOR not in content:
    print("ERROR: 8800 anchor not found"); exit(1)
idx = content.find(OLD_SECTOR)
line_end = content.find('\n', idx)
INSERT_SECTOR = '\n    # ── GK-SEC-09: VVIP CEO 통합 경영 전략 센터 ──────────────────────────────\n    "9900": {"name": "VVIP CEO 통합 경영 전략 센터", "tab_key": "gk_sec09", "keywords": ["vvip", "ceo전략센터", "gk-sec-09", "법인컨설팅", "비상장주식평가", "상증세시뮬레이터", "감자플랜", "중간배당", "임직원종신보험", "법인화재보험120%", "가지급금", "미처분이익잉여금", "단체보험갭커버", "사업주배상책임", "경영승계", "재무제표스캐너", "법인세율", "상속세율", "국세청예규", "순손익가치", "순자산가치"]},\n'
content = content[:line_end] + INSERT_SECTOR + content[line_end:]
print("SECTOR_CODES 9900 OK")

# ── 2. SUB_CODES에 9910~9960 등록 ──
OLD_SUB = '"8860": {"name": "기업·개인사업자 세무전략"'
if OLD_SUB not in content:
    print("ERROR: 8860 sub anchor not found"); exit(1)
idx2 = content.find(OLD_SUB)
line_end2 = content.find('\n', idx2)
INSERT_SUB = '\n    # ── 9900: VVIP CEO 통합 경영 전략 센터 ────────────────────────────────────\n    "9910": {"name": "조세·법령 엔진",         "tab_key": "gk_sec09", "keywords": ["법인세율조회", "소득세율조회", "상증세율조회", "국세청예규검색", "세율자동업데이트"]},\n    "9920": {"name": "Gap Cover 시뮬레이터",   "tab_key": "gk_sec09", "keywords": ["단체보험갭커버", "사업주배상책임계산", "산재부족분산출", "민750조배상책임"]},\n    "9930_ceo": {"name": "비상장주식 평가엔진", "tab_key": "gk_sec09", "keywords": ["비상장주식가치산출", "상증세법63조", "순손익가치", "순자산가치", "주당가치"]},\n    "9940": {"name": "상속세 시뮬레이터",      "tab_key": "gk_sec09", "keywords": ["ceo유고상속세", "주식상속세산출", "경영승계플랜", "감자플랜시뮬"]},\n    "9950": {"name": "법인화재보험 120%",      "tab_key": "gk_sec09", "keywords": ["120%가산가액", "최고위험요율", "재조달가액120", "인플레반영가액"]},\n    "9960": {"name": "재무제표 스캐너",        "tab_key": "gk_sec09", "keywords": ["가지급금감지", "미처분이익잉여금감지", "재무제표분석", "중간배당체크리스트"]},\n'
content = content[:line_end2] + INSERT_SUB + content[line_end2:]
print("SUB_CODES 9910-9960 OK")

# ── 3. 탭 라우터에 gk_sec09 진입점 추가 ──
OLD_ROUTER = '    # ══════════════════════════════════════════════════════════════════════\n    # [GK-SEC-08] 화재·특종보험 전술 상담 센터 라우터'
if OLD_ROUTER not in content:
    print("ERROR: sec08 router anchor not found"); exit(1)
INSERT_ROUTER = '    # ══════════════════════════════════════════════════════════════════════\n    # [GK-SEC-09] VVIP CEO 통합 경영 전략 센터 라우터\n    # ══════════════════════════════════════════════════════════════════════\n    if cur == "gk_sec09":\n        if not _auth_gate("gk_sec09"): st.stop()\n        _render_gk_sec09()\n        st.stop()\n\n    ' + OLD_ROUTER
content = content.replace(OLD_ROUTER, INSERT_ROUTER, 1)
print("Router gk_sec09 OK")

with open('D:/CascadeProjects/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("DONE step1")
