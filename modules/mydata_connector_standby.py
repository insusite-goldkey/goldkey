# =============================================================================
# [GP-MYDATA] 마이데이터 연동 커넥터 모듈
# 실제 운영 시 COOCON / CODEF API 키를 secrets.toml 또는 환경변수에 등록
# =============================================================================
#
# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  🦁 STRATEGIC STANDBY MODE (전략적 대기 모드)                              ║
# ╠═══════════════════════════════════════════════════════════════════════════╣
# ║  Status: PAUSED (일시 중지)                                                ║
# ║  Reason: Business Pivot - Focus on OCR & Expert Analysis                 ║
# ║  Date:   2026-03-31                                                       ║
# ║                                                                           ║
# ║  MyData(Credit4u) engine is paused for business pivot.                   ║
# ║  Re-activate after API Key acquisition and business approval.            ║
# ║                                                                           ║
# ║  이 모듈은 삭제되지 않았습니다. 향후 API 키 확보 시 즉시 재활성화 가능.    ║
# ║  전체 코드(530줄)는 자산으로 보존되며, 주석 해제만으로 복구됩니다.         ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
#
# =============================================================================
#
# ── 연동 경로 조사 요약 ────────────────────────────────────────────────────────
#
# 1) 쿠콘(COOCON) — https://www.coocon.co.kr
#    - 제공: 금융마이데이터 중계 API (마이데이터 사업자 허가 필요)
#    - 인증: REST API + OAuth 2.0 Bearer Token
#    - 핵심 엔드포인트:
#        POST /v1/auth/token            → 액세스 토큰 발급
#        GET  /v1/insurance/contracts   → 보험계약 목록 조회
#        GET  /v1/insurance/coverages   → 담보·보장내역 조회
#    - Python: requests 라이브러리로 직접 호출 (전용 SDK 없음)
#    - 주의: 개인정보보호법상 본인인증(통신사 PASS 또는 공동인증서) 사전 완료 필수
#
# 2) 코드에프(CODEF) — https://codef.io
#    - 제공: 스크래핑 기반 금융 정보 API (별도 마이데이터 허가 불필요)
#    - 인증: RSA 공개키 암호화 + API ID/PW
#    - 핵심 엔드포인트:
#        POST /v1/kr/insurance/p/nhis/insurance-list  → 국민건강보험공단 보험가입내역
#        POST /v1/kr/insurance/p/손해보험협회/list    → 손해보험 계약조회
#        POST /v1/kr/insurance/p/생명보험협회/list    → 생명보험 계약조회
#    - Python SDK: pip install codef-sdk
#    - 주의: 스크래핑 방식이므로 보험사 서버 응답속도에 의존
#
# 3) 한국신용정보원 '내보험다보여' 직접 연동
#    - URL: https://cont.insure.or.kr
#    - 공개 API 없음 — 마이데이터 사업자 허가 + 전용 인터페이스 계약 필요
#    - 대안: COOCON/CODEF가 동 데이터를 중계하므로 위 2개 경로로 접근 가능
#
# 4) 금감원 통합 비교공시 (FINLIFE) — 이미 app.py에 연동됨
#    - URL: https://finlife.fss.or.kr
#    - API 키: FINLIFE_API_KEY (secrets.toml 등록)
#    - 보험 공시: annuitySavingProductsSearch (연금저축보험)
#
# ── 본인인증 흐름 (통신사 PASS 기반) ──────────────────────────────────────────
#
#  [고객] 성함 + 전화번호 입력
#       ↓
#  [앱] COOCON/CODEF 인증 요청 API 호출
#       ↓ (SMS/PASS 앱 발송)
#  [고객] PASS 앱 승인 또는 SMS 인증번호 입력
#       ↓
#  [앱] 인증 완료 토큰 수신 → 보험 계약 조회 API 호출
#       ↓
#  [앱] 결과 AES-256 암호화 → GCS 저장 / 세션 로드
#
# =============================================================================


# =============================================================================
# 🦁 STRATEGIC STANDBY: 아래 전체 코드는 비즈니스 피벗으로 일시 중지됨
# =============================================================================

# """
# # ═══════════════════════════════════════════════════════════════════════════
# # 🦁 STRATEGIC STANDBY: 아래 전체 코드는 비즈니스 피벗으로 일시 중지됨
# # ═══════════════════════════════════════════════════════════════════════════
# 
# import os
# import json
# import hashlib
# import base64
# import urllib.request as _urlreq
# import urllib.parse  as _urlparse
# from typing import Optional
# 
# 
# # ── 환경변수/Secrets 로더 ──────────────────────────────────────────────────
# def _get_secret(key: str, default: str = "") -> str:
#     """secrets.toml 또는 환경변수에서 키 읽기"""
#     try:
#         import streamlit as st
#         val = st.secrets.get(key, "")
#         if val:
#             return str(val)
#     except Exception:
#         pass
#     return os.environ.get(key, default)
# 
# 
# # ══════════════════════════════════════════════════════════════════════════════
# # [COOCON] REST API 커넥터
# # secrets.toml 등록 항목:
# #   COOCON_CLIENT_ID     = "..."
# #   COOCON_CLIENT_SECRET = "..."
# #   COOCON_BASE_URL      = "https://api.coocon.co.kr"  (샌드박스 별도)
# # ══════════════════════════════════════════════════════════════════════════════
# 
# _COOCON_BASE = "https://api.coocon.co.kr"  # 운영 URL (샌드박스: https://sandbox-api.coocon.co.kr)
# 
# 
# def coocon_get_token() -> dict:
#     """
#     COOCON OAuth 2.0 액세스 토큰 발급.
#     반환: {"access_token": str, "expires_in": int, "error": str|None}
#     """
#     client_id     = _get_secret("COOCON_CLIENT_ID")
#     client_secret = _get_secret("COOCON_CLIENT_SECRET")
#     base_url      = _get_secret("COOCON_BASE_URL", _COOCON_BASE)
# 
#     if not client_id or not client_secret:
#         return {"access_token": "", "error": "COOCON_CLIENT_ID / COOCON_CLIENT_SECRET 미설정"}
# 
#     try:
#         data = _urlparse.urlencode({
#             "grant_type":    "client_credentials",
#             "client_id":     client_id,
#             "client_secret": client_secret,
#             "scope":         "insurance",
#         }).encode("utf-8")
#         req = _urlreq.Request(
#             f"{base_url}/v1/auth/token",
#             data=data,
#             headers={"Content-Type": "application/x-www-form-urlencoded"},
#             method="POST",
#         )
#         with _urlreq.urlopen(req, timeout=10) as resp:
#             body = json.loads(resp.read().decode("utf-8"))
#         return {
#             "access_token": body.get("access_token", ""),
#             "expires_in":   body.get("expires_in", 3600),
#             "error":        None,
#         }
#     except Exception as e:
#         return {"access_token": "", "error": str(e)[:200]}
# 
# 
# def coocon_fetch_insurance(
#     access_token: str,
#     ci_hash: str,       # 연계정보(CI) 해시값 — 본인인증 완료 후 발급
#     org_code: str = "",  # 보험사 기관코드 (빈값 = 전체)
# ) -> dict:
#     """
#     COOCON 보험계약 목록 조회.
#     반환: {"contracts": [...], "error": str|None}
#     계약 항목: company_name, product_name, contract_no, premium, status, coverages[]
#     """
#     base_url = _get_secret("COOCON_BASE_URL", _COOCON_BASE)
#     if not access_token:
#         return {"contracts": [], "error": "액세스 토큰 없음"}
#     try:
#         params = _urlparse.urlencode({"ci": ci_hash, "orgCode": org_code})
#         req = _urlreq.Request(
#             f"{base_url}/v1/insurance/contracts?{params}",
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-Type":  "application/json",
#                 "Accept":        "application/json",
#             },
#             method="GET",
#         )
#         with _urlreq.urlopen(req, timeout=15) as resp:
#             body = json.loads(resp.read().decode("utf-8"))
#         return {"contracts": body.get("data", []), "error": None}
#     except Exception as e:
#         return {"contracts": [], "error": str(e)[:200]}
# 
# 
# # ══════════════════════════════════════════════════════════════════════════════
# # [CODEF] 스크래핑 기반 보험 계약 조회
# # secrets.toml 등록 항목:
# #   CODEF_CLIENT_ID     = "..."
# #   CODEF_CLIENT_SECRET = "..."
# #   CODEF_PUBLIC_KEY    = "MIIBIjAN..."  (RSA 공개키, 대시보드에서 발급)
# # ══════════════════════════════════════════════════════════════════════════════
# 
# _CODEF_BASE = "https://api.codef.io"
# 
# 
# def _codef_rsa_encrypt(plain_text: str) -> str:
#     """
#     CODEF RSA 공개키로 평문 암호화.
#     실제 운영 시 cryptography 라이브러리 필요:
#         pip install cryptography
#     반환: base64 인코딩된 암호문
#     """
#     try:
#         from cryptography.hazmat.primitives import serialization, hashes
#         from cryptography.hazmat.primitives.asymmetric import padding
#         pub_key_pem = _get_secret("CODEF_PUBLIC_KEY")
#         if not pub_key_pem:
#             return ""
#         # PEM 헤더/푸터 보정
#         if not pub_key_pem.startswith("-----"):
#             pub_key_pem = (
#                 "-----BEGIN PUBLIC KEY-----\n"
#                 + pub_key_pem
#                 + "\n-----END PUBLIC KEY-----"
#             )
#         pub_key = serialization.load_pem_public_key(pub_key_pem.encode())
#         ciphertext = pub_key.encrypt(
#             plain_text.encode("utf-8"),
#             padding.OAEP(
#                 mgf=padding.MGF1(algorithm=hashes.SHA1()),
#                 algorithm=hashes.SHA1(),
#                 label=None,
#             ),
#         )
#         return base64.b64encode(ciphertext).decode("utf-8")
#     except ImportError:
#         return f"[cryptography 라이브러리 필요: pip install cryptography] {plain_text}"
#     except Exception as e:
#         return f"[RSA 암호화 오류: {e}]"
# 
# 
# def codef_get_token() -> dict:
#     """CODEF OAuth 토큰 발급"""
#     client_id     = _get_secret("CODEF_CLIENT_ID")
#     client_secret = _get_secret("CODEF_CLIENT_SECRET")
#     if not client_id or not client_secret:
#         return {"access_token": "", "error": "CODEF_CLIENT_ID / CODEF_CLIENT_SECRET 미설정"}
#     try:
#         _cred = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
#         data  = _urlparse.urlencode({"grant_type": "client_credentials", "scope": "read"}).encode()
#         req   = _urlreq.Request(
#             "https://oauth.codef.io/oauth/token",
#             data=data,
#             headers={
#                 "Authorization": f"Basic {_cred}",
#                 "Content-Type":  "application/x-www-form-urlencoded",
#             },
#             method="POST",
#         )
#         with _urlreq.urlopen(req, timeout=10) as resp:
#             body = json.loads(resp.read().decode("utf-8"))
#         return {"access_token": body.get("access_token", ""), "error": None}
#     except Exception as e:
#         return {"access_token": "", "error": str(e)[:200]}
# 
# 
# def codef_fetch_insurance_life(
#     access_token: str,
#     id_no_enc: str,      # RSA 암호화된 주민번호
#     password_enc: str,   # RSA 암호화된 인증서 비밀번호 (공동인증서)
#     cert_file: str = "", # 인증서 파일 경로 (선택)
# ) -> dict:
#     """
#     CODEF 생명보험협회 계약 조회.
#     반환: {"contracts": [...], "error": str|None}
#     """
#     if not access_token:
#         return {"contracts": [], "error": "CODEF 토큰 없음"}
#     try:
#         payload = json.dumps({
#             "organization": "0001",  # 생명보험협회
#             "id":           id_no_enc,
#             "password":     password_enc,
#         }).encode("utf-8")
#         req = _urlreq.Request(
#             f"{_CODEF_BASE}/v1/kr/insurance/p/card/contract-list",
#             data=payload,
#             headers={
#                 "Authorization": f"Bearer {access_token}",
#                 "Content-Type":  "application/json",
#             },
#             method="POST",
#         )
#         with _urlreq.urlopen(req, timeout=20) as resp:
#             body = json.loads(resp.read().decode("utf-8"))
#         return {"contracts": body.get("data", []), "error": None}
#     except Exception as e:
#         return {"contracts": [], "error": str(e)[:200]}
# 
# 
# # ══════════════════════════════════════════════════════════════════════════════
# # [통합] 마이데이터 소환 메인 함수 (COOCON → CODEF → 시뮬레이션 폴백)
# # ══════════════════════════════════════════════════════════════════════════════
# 
# def fetch_mydata_insurance(
#     client_name:  str,
#     phone:        str = "",
#     ci_hash:      str = "",   # COOCON용 CI 해시
#     id_no:        str = "",   # CODEF용 주민번호 (암호화 전)
#     use_simulate: bool = True, # API 키 없을 때 시뮬레이션 폴백
# ) -> dict:
#     """
#     [GP-MYDATA 메인] 마이데이터 보험 소환 통합 함수.
#     1순위: COOCON API (ci_hash 있을 때)
#     2순위: CODEF API (id_no 있을 때)
#     3순위: 시뮬레이션 (use_simulate=True)
# 
#     반환:
#     {
#         "source":         "coocon" | "codef" | "simulate",
#         "insurance_list": [...],
#         "coverage_analysis": [...],
#         "error":          str | None,
#     }
#     """
#     # 1순위: COOCON
#     coocon_id = _get_secret("COOCON_CLIENT_ID")
#     if coocon_id and ci_hash:
#         _tok = coocon_get_token()
#         if not _tok["error"]:
#             _res = coocon_fetch_insurance(_tok["access_token"], ci_hash)
#             if not _res["error"]:
#                 _ins = _normalize_coocon_contracts(_res["contracts"])
#                 return {
#                     "source":            "coocon",
#                     "insurance_list":    _ins,
#                     "coverage_analysis": _build_coverage_analysis(_ins),
#                     "error":             None,
#                 }
# 
#     # 2순위: CODEF
#     codef_id = _get_secret("CODEF_CLIENT_ID")
#     if codef_id and id_no:
#         _tok2 = codef_get_token()
#         if not _tok2["error"]:
#             _id_enc = _codef_rsa_encrypt(id_no)
#             _res2   = codef_fetch_insurance_life(_tok2["access_token"], _id_enc, "")
#             if not _res2["error"]:
#                 _ins2 = _normalize_codef_contracts(_res2["contracts"])
#                 return {
#                     "source":            "codef",
#                     "insurance_list":    _ins2,
#                     "coverage_analysis": _build_coverage_analysis(_ins2),
#                     "error":             None,
#                 }
# 
#     # 3순위: 시뮬레이션 폴백
#     if use_simulate:
#         from modules.mydata_connector import _simulate_insurance
#         _sim = _simulate_insurance(client_name)
#         return {
#             "source":            "simulate",
#             "insurance_list":    _sim["insurance_list"],
#             "coverage_analysis": _sim["coverage_analysis"],
#             "error":             None,
#         }
# 
#     return {
#         "source":            "none",
#         "insurance_list":    [],
#         "coverage_analysis": [],
#         "error":             "API 키 미설정 + 시뮬레이션 비활성화",
#     }
# 
# 
# def _normalize_coocon_contracts(contracts: list) -> list:
#     """COOCON 응답 → 내부 표준 형식 변환"""
#     result = []
#     for c in contracts:
#         result.append({
#             "company":  c.get("companyName", c.get("company_name", "")),
#             "product":  c.get("productName", c.get("product_name", "")),
#             "coverage": ", ".join(c.get("coverages", [])) or "─",
#             "premium":  f"월 {int(c.get('monthlyPremium', 0)):,}원" if c.get("monthlyPremium") else "─",
#             "status":   {"01": "유지", "02": "실효", "03": "만기"}.get(c.get("contractStatus", ""), "확인필요"),
#         })
#     return result
# 
# 
# def _normalize_codef_contracts(contracts: list) -> list:
#     """CODEF 응답 → 내부 표준 형식 변환"""
#     result = []
#     for c in contracts:
#         result.append({
#             "company":  c.get("resCompanyNm", ""),
#             "product":  c.get("resProductNm", ""),
#             "coverage": c.get("resCoverage", "─"),
#             "premium":  c.get("resPremium", "─"),
#             "status":   {"정상": "유지", "실효": "실효", "만기": "만기"}.get(c.get("resContractStatus", ""), "확인필요"),
#         })
#     return result
# 
# 
# def _build_coverage_analysis(ins_list: list) -> list:
#     """
#     보험 내역 → 보장 과부족 분석 생성.
#     담보명 키워드 매칭으로 가입 금액 추정.
#     """
#     _COVERAGE_TARGETS = [
#         {"category": "암 진단",  "name": "일반암진단비",       "recommended_amt": 50000000,  "keywords": ["암진단", "일반암", "암"]},
#         {"category": "뇌혈관",   "name": "뇌졸중진단비",       "recommended_amt": 50000000,  "keywords": ["뇌졸중", "뇌혈관", "뇌경색"]},
#         {"category": "심장",     "name": "급성심근경색진단비", "recommended_amt": 30000000,  "keywords": ["심근경색", "심장", "급성심"]},
#         {"category": "수술비",   "name": "1~5종 수술비",       "recommended_amt": 5000000,   "keywords": ["수술비", "수술"]},
#         {"category": "입원일당", "name": "질병 입원일당",      "recommended_amt": 100000,    "keywords": ["입원일당", "입원"]},
#         {"category": "실손",     "name": "실손의료비",         "recommended_amt": 1,         "keywords": ["실손", "의료비"]},
#         {"category": "사망",     "name": "일반사망보험금",     "recommended_amt": 300000000, "keywords": ["사망", "종신"]},
#     ]
#     # 전체 담보 텍스트 수집
#     all_coverages = " ".join([
#         f"{i.get('product','')} {i.get('coverage','')}" for i in ins_list
#     ]).lower()
# 
#     result = []
#     for tgt in _COVERAGE_TARGETS:
#         _matched = any(kw in all_coverages for kw in tgt["keywords"])
#         _enrolled = tgt["recommended_amt"] if _matched else 0
#         _status   = "충분" if _enrolled >= tgt["recommended_amt"] else ("부족" if _enrolled > 0 else "미가입")
#         result.append({
#             "category":         tgt["category"],
#             "name":             tgt["name"],
#             "recommended_amt":  tgt["recommended_amt"],
#             "enrolled_amt":     _enrolled,
#             "status":           _status,
#         })
#     return result
# 
# 
# def _simulate_insurance(client_name: str) -> dict:
#     """개발/데모용 시뮬레이션 데이터"""
#     import random
#     _companies = ["삼성생명", "한화생명", "교보생명", "DB손해보험", "현대해상", "KB손해보험", "메리츠화재"]
#     _products  = [
#         ("종신보험", "사망·CI", "월 12.3만"),
#         ("암보험", "암진단비", "월 4.8만"),
#         ("실손보험", "입원·통원", "월 8.1만"),
#         ("건강보험", "뇌·심장·암", "월 15.6만"),
#         ("운전자보험", "교통사고", "월 2.4만"),
#     ]
#     random.seed(abs(hash(client_name)) % 9999)
#     _ins_list = []
#     for _ in range(random.randint(2, 5)):
#         _co = random.choice(_companies)
#         _prod, _cov, _prem = random.choice(_products)
#         _ins_list.append({
#             "company": _co, "product": _prod,
#             "coverage": _cov, "premium": _prem,
#             "status": random.choice(["유지", "유지", "유지", "실효", "만기"]),
#         })
#     _coverage_items = [
#         {"category": "암 진단",  "name": "일반암진단비",       "recommended_amt": 50000000,  "enrolled_amt": random.choice([0, 20000000, 30000000, 50000000])},
#         {"category": "뇌혈관",   "name": "뇌졸중진단비",       "recommended_amt": 50000000,  "enrolled_amt": random.choice([0, 10000000, 20000000, 50000000])},
#         {"category": "심장",     "name": "급성심근경색진단비", "recommended_amt": 30000000,  "enrolled_amt": random.choice([0, 10000000, 30000000])},
#         {"category": "수술비",   "name": "1~5종 수술비",       "recommended_amt": 5000000,   "enrolled_amt": random.choice([0, 1000000, 3000000, 5000000])},
#         {"category": "입원일당", "name": "질병 입원일당",      "recommended_amt": 100000,    "enrolled_amt": random.choice([0, 30000, 50000, 100000])},
#         {"category": "실손",     "name": "실손의료비",         "recommended_amt": 1,         "enrolled_amt": random.choice([0, 1])},
#         {"category": "사망",     "name": "일반사망보험금",     "recommended_amt": 300000000, "enrolled_amt": random.choice([0, 100000000, 200000000])},
#     ]
#     for _ci in _coverage_items:
#         _r, _e = _ci["recommended_amt"], _ci["enrolled_amt"]
#         _ci["status"] = "충분" if _e >= _r else ("부족" if _e > 0 else "미가입")
#     return {"insurance_list": _ins_list, "coverage_analysis": _coverage_items}
# 
# 
# # ══════════════════════════════════════════════════════════════════════════════
# # [FSS] 보험 공시 비교 — 고객 가입 보험 vs 금감원 최신 연금저축 공시
# # ══════════════════════════════════════════════════════════════════════════════
# 
# _FSS_INS_PRODUCT_TYPES = {
#     "060000": "생명보험사 연금저축",
#     "060001": "손해보험사 연금저축",
#     "060002": "은행·증권사 연금저축",
# }
# 
# 
# def fss_compare_annuity(customer_ins_list: list, finlife_api_key: str = "") -> dict:
#     """
#     [FSS 비교] 고객 가입 연금/저축 보험을 금감원 공시 최저보험료 상품과 비교.
#     반환:
#     {
#         "customer_products": [...],    # 고객 가입 보험 중 연금류
#         "market_best":       [...],    # 금감원 공시 상위 5개 상품
#         "comparison":        [...],    # 고객 상품별 시장 최저 대비 분석
#         "error":             str|None,
#     }
#     """
#     if not finlife_api_key:
#         finlife_api_key = _get_secret("FINLIFE_API_KEY")
# 
#     # 고객 보험 중 연금/저축보험 필터링
#     _annuity_keywords = ["연금", "저축", "종신", "변액", "유니버셜"]
#     _customer_annuity = [
#         ins for ins in customer_ins_list
#         if any(kw in ins.get("product", "") for kw in _annuity_keywords)
#         and ins.get("status") == "유지"
#     ]
# 
#     # FSS 공시 조회
#     if not finlife_api_key:
#         return {
#             "customer_products": _customer_annuity,
#             "market_best":       [],
#             "comparison":        [],
#             "error":             "FINLIFE_API_KEY 미설정 — secrets.toml에 등록 필요",
#         }
# 
#     try:
#         import urllib.request as _req
#         import urllib.parse   as _prs
#         params = _prs.urlencode({
#             "auth":         finlife_api_key,
#             "topFinGrpNo":  "060000",  # 생명보험사
#             "pageNo":       1,
#         })
#         url = f"https://finlife.fss.or.kr/finlifeapi/annuitySavingProductsSearch.json?{params}"
#         with _req.urlopen(url, timeout=10) as resp:
#             data = json.loads(resp.read().decode("utf-8"))
# 
#         _base_list = data.get("result", {}).get("baseList", [])
#         _opt_list  = data.get("result", {}).get("optionList", [])
# 
#         # 수익률/공시이율 기준 상위 5개 파싱
#         _market_best = []
#         for prod in _base_list[:10]:
#             _opts = [o for o in _opt_list if o.get("fin_prdt_cd") == prod.get("fin_prdt_cd")]
#             _best_rate = max([float(o.get("dcls_rate", 0) or 0) for o in _opts], default=0)
#             _market_best.append({
#                 "company":      prod.get("kor_co_nm", ""),
#                 "product_name": prod.get("fin_prdt_nm", ""),
#                 "rate":         _best_rate,
#                 "join_way":     prod.get("join_way", ""),
#                 "etc_note":     prod.get("etc_note", "")[:60] if prod.get("etc_note") else "",
#             })
#         _market_best.sort(key=lambda x: x["rate"], reverse=True)
#         _market_best = _market_best[:5]
# 
#         # 고객 상품 vs 시장 최적 비교
#         _comparison = []
#         for c_ins in _customer_annuity:
#             _best = _market_best[0] if _market_best else None
#             _comparison.append({
#                 "customer_product": c_ins.get("product", ""),
#                 "customer_company": c_ins.get("company", ""),
#                 "customer_premium": c_ins.get("premium", ""),
#                 "market_best_product": _best["product_name"] if _best else "─",
#                 "market_best_company": _best["company"] if _best else "─",
#                 "market_best_rate":    f"{_best['rate']:.2f}%" if _best else "─",
#                 "action": "유지 검토" if not _best or _best["rate"] < 3.0 else "시장 비교 권장",
#             })
# 
#         return {
#             "customer_products": _customer_annuity,
#             "market_best":       _market_best,
#             "comparison":        _comparison,
#             "error":             None,
#         }
#     except Exception as e:
#         return {
#             "customer_products": _customer_annuity,
#             "market_best":       [],
#             "comparison":        [],
#             "error":             str(e)[:200],
#         }
# 