# -*- coding: utf-8 -*-
"""6대 엔진 백엔드 연결 진단 스크립트"""

import sys, io, json, urllib.request as req, urllib.parse as up, re, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HIRA_KEY = "f48e5dc280e98997350a81ea547f2c3ad357a02c7a3407050d114149272dfc71"
LAW_OC   = "goldkey"
LAW_USER = "insusite@gmail.com"
FSS_KEY  = "ae6f53ce0983196f3044439c3e9a039d"

print("=" * 60)
print("[테스트 A] HIRA 질병마스터 API — 당뇨 검색")
print("=" * 60)
try:
    params = up.urlencode({
        "serviceKey": HIRA_KEY,
        "numOfRows": "5",
        "pageNo": "1",
        "sickType": "1",
        "medTp": "1",
        "searchText": "당뇨",
        "_type": "json",
    })
    url = f"https://apis.data.go.kr/B551182/msInfrm/getDissInfo?{params}"
    r = req.urlopen(url, timeout=6)
    raw = json.loads(r.read().decode("utf-8"))
    items = (raw.get("response", {}).get("body", {}).get("items", {}).get("item", []))
    if isinstance(items, dict): items = [items]
    if items:
        print(f"  ✅ HIRA API 연결 성공 — {len(items)}건 반환")
        for it in items[:3]:
            print(f"     KCD: {it.get('sickCd','?'):8s}  명칭: {it.get('sickNm','?')}")
    else:
        print(f"  ⚠ HIRA API 응답 있으나 결과 없음: {json.dumps(raw, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"  ❌ HIRA API 실패: {type(e).__name__}: {e}")

# HIRA 협심증 테스트
print()
try:
    params2 = up.urlencode({
        "serviceKey": HIRA_KEY, "numOfRows": "5", "pageNo": "1",
        "sickType": "1", "medTp": "1", "searchText": "협심증", "_type": "json",
    })
    url2 = f"https://apis.data.go.kr/B551182/msInfrm/getDissInfo?{params2}"
    r2 = req.urlopen(url2, timeout=6)
    raw2 = json.loads(r2.read().decode("utf-8"))
    items2 = raw2.get("response", {}).get("body", {}).get("items", {}).get("item", [])
    if isinstance(items2, dict): items2 = [items2]
    if items2:
        print(f"  ✅ 협심증 검색 성공 — {len(items2)}건")
        for it in items2[:3]:
            print(f"     KCD: {it.get('sickCd','?'):8s}  명칭: {it.get('sickNm','?')}")
    else:
        print(f"  ⚠ 협심증 결과 없음")
        # 대안 API 엔드포인트 시도
        params3 = up.urlencode({
            "serviceKey": HIRA_KEY, "numOfRows": "5", "pageNo": "1",
            "searchText": "협심증", "_type": "json",
        })
        url3 = f"https://apis.data.go.kr/B551182/msInfrm/getIcd10Info?{params3}"
        r3 = req.urlopen(url3, timeout=6)
        raw3 = json.loads(r3.read().decode("utf-8"))
        print(f"  대안 엔드포인트: {json.dumps(raw3, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"  ❌ 협심증 검색 실패: {e}")

print()
print("=" * 60)
print("[테스트 B] 국가법령정보센터 API — 보험업법 검색")
print("=" * 60)
try:
    params_law = up.urlencode({
        "OC": LAW_OC, "target": "law", "type": "JSON",
        "query": "보험업법", "display": "5",
    })
    url_law = f"https://www.law.go.kr/DRF/lawSearch.do?{params_law}"
    r_law = req.urlopen(url_law, timeout=8)
    raw_law = json.loads(r_law.read().decode("utf-8"))
    laws = raw_law.get("LawSearch", {}).get("law", [])
    if isinstance(laws, dict): laws = [laws]
    if laws:
        print(f"  ✅ 법령 API 연결 성공 — {len(laws)}건")
        for law in laws[:3]:
            print(f"     법령명: {law.get('법령명한글','?')}")
    else:
        print(f"  ⚠ 법령 결과 없음: {json.dumps(raw_law, ensure_ascii=False)[:300]}")
except Exception as e:
    print(f"  ❌ 법령 API 실패: {type(e).__name__}: {e}")

# 판례 검색
print()
try:
    params_prec = up.urlencode({
        "OC": LAW_OC, "target": "prec", "type": "JSON",
        "query": "암보험", "display": "3",
    })
    url_prec = f"https://www.law.go.kr/DRF/lawSearch.do?{params_prec}"
    r_prec = req.urlopen(url_prec, timeout=8)
    raw_prec = json.loads(r_prec.read().decode("utf-8"))
    precs = raw_prec.get("PrecSearch", {}).get("prec", [])
    if isinstance(precs, dict): precs = [precs]
    if precs:
        print(f"  ✅ 판례 API 연결 성공 — {len(precs)}건")
        for p in precs[:3]:
            print(f"     사건명: {p.get('사건명','?')[:50]}")
    else:
        print(f"  ⚠ 판례 결과 없음: {json.dumps(raw_prec, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"  ❌ 판례 API 실패: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("[테스트 C] 국세청 사업자 상태조회 API")
print("=" * 60)
# 테스트용 공개 사업자번호 (삼성전자: 1248100998)
BIZ_NO = "1248100998"
try:
    url_biz = "https://api.odcloud.kr/api/nts-businessman/v1/status"
    params_biz = up.urlencode({"serviceKey": HIRA_KEY, "returnType": "JSON"})
    body = json.dumps({"b_no": [BIZ_NO]}).encode("utf-8")
    request = req.Request(
        f"{url_biz}?{params_biz}", data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    r_biz = req.urlopen(request, timeout=6)
    raw_biz = json.loads(r_biz.read().decode("utf-8"))
    data = raw_biz.get("data", [{}])
    if data:
        d = data[0]
        print(f"  ✅ 국세청 API 연결 성공")
        print(f"     사업자: {BIZ_NO}  상태: {d.get('b_stt','?')}({d.get('b_stt_cd','?')})")
        print(f"     상호: {d.get('b_nm','?')}  대표: {d.get('p_nm','?')}")
    else:
        print(f"  ⚠ 국세청 응답 data 없음: {json.dumps(raw_biz, ensure_ascii=False)[:300]}")
except Exception as e:
    print(f"  ❌ 국세청 API 실패: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("[테스트 D] FSS 금감원 API")
print("=" * 60)
try:
    params_fss = up.urlencode({
        "auth": FSS_KEY, "menuCode": "M001", "col": "l", "responseType": "json",
    })
    url_fss = f"https://finlife.fss.or.kr/finlifeapi/lifeInsuranceList.json?{params_fss}"
    r_fss = req.urlopen(url_fss, timeout=6)
    raw_fss = json.loads(r_fss.read().decode("utf-8"))
    items_fss = raw_fss.get("result", {}).get("baseList", [])
    if items_fss:
        print(f"  ✅ FSS API 연결 성공 — {len(items_fss)}건")
        for it in items_fss[:2]:
            print(f"     {it.get('kor_co_nm','?')} / {it.get('fin_prdt_nm','?')[:40]}")
    else:
        err_cd = raw_fss.get("result", {}).get("err_cd", "?")
        err_msg = raw_fss.get("result", {}).get("err_msg", "?")
        print(f"  ⚠ FSS 결과 없음: err_cd={err_cd} msg={err_msg}")
        print(f"     raw: {json.dumps(raw_fss, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"  ❌ FSS API 실패: {type(e).__name__}: {e}")

print()
print("=" * 60)
print("진단 완료")
print("=" * 60)
