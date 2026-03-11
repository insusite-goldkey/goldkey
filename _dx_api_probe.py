# -*- coding: utf-8 -*-
"""HIRA + FSS 정확한 엔드포인트 탐색"""

import sys, io, json, urllib.request as req, urllib.parse as up
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HIRA_KEY = "f48e5dc280e98997350a81ea547f2c3ad357a02c7a3407050d114149272dfc71"
FSS_KEY  = "ae6f53ce0983196f3044439c3e9a039d"

print("=" * 60)
print("[HIRA] 엔드포인트 탐색")
print("=" * 60)

# 심평원 공공API 목록에서 가장 많이 쓰는 질병통계 / 심사기준 엔드포인트들
HIRA_ENDPOINTS = [
    # 질병분류코드(KCD) 검색
    ("getDissInfo-v2",
     "https://apis.data.go.kr/B551182/msInfrm/getDissInfo",
     {"serviceKey": HIRA_KEY, "numOfRows": "3", "pageNo": "1",
      "searchText": "당뇨", "_type": "json"}),
    # getIcd10Info
    ("getIcd10Info",
     "https://apis.data.go.kr/B551182/msInfrm/getIcd10Info",
     {"serviceKey": HIRA_KEY, "numOfRows": "3", "pageNo": "1",
      "searchText": "당뇨", "_type": "json"}),
    # 요양기관 약가정보 아닌 KCD 전용 다른 서비스
    ("getDiagnosisInfo",
     "https://apis.data.go.kr/B551182/msInfrm/getDiagnosisInfo",
     {"serviceKey": HIRA_KEY, "numOfRows": "3", "pageNo": "1",
      "sickNm": "당뇨", "_type": "json"}),
    # 공공데이터포털 KCD 코드 조회 (다른 기관)
    ("kcd-data.go.kr",
     "https://apis.data.go.kr/1352000/ODMS_CD_03/callCd03Api",
     {"serviceKey": HIRA_KEY, "pageNo": "1", "numOfRows": "3",
      "type": "json", "CD_NM": "당뇨"}),
]

for name, url, params in HIRA_ENDPOINTS:
    try:
        full_url = f"{url}?{up.urlencode(params)}"
        r = req.urlopen(full_url, timeout=5)
        code = r.getcode()
        raw = r.read().decode("utf-8", errors="replace")
        print(f"  {name}: HTTP {code} — {raw[:150]}")
    except Exception as e:
        print(f"  {name}: ❌ {type(e).__name__}: {str(e)[:80]}")

print()
print("=" * 60)
print("[FSS] 엔드포인트 탐색")
print("=" * 60)

FSS_ENDPOINTS = [
    ("lifeInsuranceList-json",
     "https://finlife.fss.or.kr/finlifeapi/lifeInsuranceList.json",
     {"auth": FSS_KEY, "menuCode": "M001", "col": "l"}),
    ("lifeInsuranceList-xml",
     "https://finlife.fss.or.kr/finlifeapi/lifeInsuranceList.xml",
     {"auth": FSS_KEY, "menuCode": "M001", "col": "l"}),
    # FSS 신 공개 API
    ("fss-openapi-v1",
     "https://api.fss.or.kr/fss/lifeInsrDscl/getLifeInsrPrdtBasInfoList/v1",
     {"authKey": FSS_KEY, "pageNo": "1", "numOfRows": "3", "resultType": "json"}),
    # 금융위 금융상품한눈에
    ("finlife-v2",
     "https://finlife.fss.or.kr/finlifeapi/lifeInsuranceList.json",
     {"auth": FSS_KEY, "menuCode": "M001", "col": "l", "pageNo": "1", "numOfRows": "3"}),
    # 공공데이터포털 금융위 보험상품
    ("data.go.kr-fss",
     "https://apis.data.go.kr/1160100/service/GetInsuranceProductInfoService/getInsuranceProductList",
     {"serviceKey": FSS_KEY, "pageNo": "1", "numOfRows": "3", "_type": "json"}),
]

for name, url, params in FSS_ENDPOINTS:
    try:
        full_url = f"{url}?{up.urlencode(params)}"
        r = req.urlopen(full_url, timeout=5)
        code = r.getcode()
        raw = r.read().decode("utf-8", errors="replace")
        print(f"  {name}: HTTP {code} — {raw[:150]}")
    except Exception as e:
        print(f"  {name}: ❌ {type(e).__name__}: {str(e)[:80]}")
