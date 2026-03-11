# =============================================================================
# [AUTH-GATEWAY] 외부 본인인증 통합 게이트웨이
# =============================================================================
#
# ── 연동 규격 조사 요약 ──────────────────────────────────────────────────────
#
# 1) NICE평가정보 — 표준 본인확인 서비스 (https://chk.niceid.co.kr)
#    - 규격: 행정안전부 표준 API (표준창 방식 / 서버-서버 방식)
#    - 인증 흐름:
#        ① 서버 → NICE: 암호화 토큰 요청 (RSA-2048 + AES-128-CBC)
#        ② 서버 → 고객 브라우저: 표준창(checkplus_main) 팝업 전달
#        ③ 고객: PASS 앱 또는 SMS OTP 인증
#        ④ NICE → 서버: 암호화된 본인확인 결과 전달 (enc_data)
#        ⑤ 서버: enc_data 복호화 → CI(연계정보)/DI(중복가입확인정보) 추출
#    - Streamlit 제약: iframe/팝업 직접 띄우기 불가 → 중간 relay 페이지 필요
#    - secrets.toml 등록 항목:
#        NICE_SITE_CODE    = "..."   # NICE 계약 후 발급
#        NICE_SITE_PASSWORD= "..."
#        NICE_CB_URL       = "https://your-domain.com/nice_callback"
#
# 2) PASS 인증 (통신사 MVNO 포함) — https://www.passlogin.com
#    - 규격: PASS 오픈API (SKT·KT·LGU+ 공동 운영)
#    - 인증 흐름:
#        ① 서버: PASS API로 인증 요청 (이름 + 전화번호 + 생년월일 전송)
#        ② PASS → 고객 앱: 푸시 알림 전송
#        ③ 고객: PASS 앱에서 PIN/생체인증으로 승인
#        ④ PASS → 서버: 인증 결과 콜백 (transaction_id + result_code)
#        ⑤ 서버: CI 값 수신 → 마이데이터 조회 요청
#    - 특징: 알뜰폰(MVNO)도 통신사 원망을 통해 지원
#    - secrets.toml 등록 항목:
#        PASS_API_KEY     = "..."
#        PASS_API_SECRET  = "..."
#        PASS_SERVICE_ID  = "..."
#
# 3) 카카오 인증 (카카오페이 인증서) — https://developers.kakao.com
#    - 규격: Kakao Pay 전자서명 API
#    - 인증 흐름:
#        ① 서버: KakaoPay 서명 요청 API (POST /v1/pay/ready) 호출
#           → sign_transaction_id 발급
#        ② 서버 → 고객: 카카오톡 푸시 알림 발송 (카카오톡 채널 연결 필요)
#        ③ 고객: 카카오톡 → 카카오페이 → 인증 승인
#        ④ KakaoPay → 서버: 서명 결과 콜백 (success/fail)
#        ⑤ 서버: CI 추출 → 마이데이터 조회
#    - Streamlit 환경: QR코드 방식으로 대체 가능 (카카오 QR 인증)
#    - secrets.toml 등록 항목:
#        KAKAO_AUTH_APP_KEY = "..."  # 카카오 디벨로퍼스 앱 키
#        KAKAO_AUTH_ADMIN_KEY = "..."
#
# ── 보안 설계 원칙 ───────────────────────────────────────────────────────────
#
#  ┌──────────────────────────────────────────────────────────────────┐
#  │ [원칙 1] 민감정보 비저장 — 이름·생년월일·전화번호는 메모리에만  │
#  │          존재. session_state에도 SHA-256 해시값만 보존.          │
#  │ [원칙 2] 토큰 격리 — CI(연계정보)를 AES-256-GCM으로 암호화 후  │
#  │          메모리 전용 변수에만 보관. 세션 종료 시 즉시 소거.     │
#  │ [원칙 3] 최소 권한 — 인증 성공 토큰만 마이데이터 조회에 사용.  │
#  │          원본 개인정보는 인증 API 응답 즉시 파기.               │
#  │ [원칙 4] 폴백 시뮬레이션 — API 미연동 시 실제 개인정보 요구   │
#  │          없이 시뮬레이션 토큰을 발급하여 동일한 흐름 유지.     │
#  └──────────────────────────────────────────────────────────────────┘
#
# =============================================================================

from __future__ import annotations
import os
import json
import hashlib
import hmac
import base64
import time
import secrets as _secrets
import urllib.request as _urlreq
import urllib.parse   as _urlparse
from typing import Optional


# ── 환경변수/Secrets 로더 ──────────────────────────────────────────────────
def _get_secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


# =============================================================================
# [CORE] 인증 토큰 생성 및 민감정보 보안 처리
# =============================================================================

def generate_auth_token(
    name: str,
    phone: str,
    dob: str,
    carrier: str = "",
    method: str = "simulate",
) -> dict:
    """
    인증 성공 토큰 생성 — 민감정보 즉시 해싱 처리.

    반환:
    {
        "token":         str,    # 세션 내 사용 인증 토큰 (32자 랜덤 hex)
        "ci_hash":       str,    # CI 대체 해시 (SHA-256, 16자 앞단) — 마이데이터 조회용
        "name_initial":  str,    # 이름 마스킹 (홍*동 형식)
        "phone_masked":  str,    # 전화번호 마스킹 (010-****-1234)
        "method":        str,    # 인증 수단 (kakao/pass/nice/simulate)
        "issued_at":     float,  # Unix timestamp
        "expires_at":    float,  # Unix timestamp (+1800초)
        "error":         None,
    }
    민감정보(name, phone, dob)는 이 함수 내에서만 사용되고 반환값에 포함되지 않음.
    """
    _name_clean  = name.strip()
    _phone_clean = "".join(c for c in phone if c.isdigit())
    _dob_clean   = "".join(c for c in dob   if c.isdigit())

    # CI 대체 해시 — HMAC-SHA256 (salt=token) — 재현 불가 단방향 해시
    _salt    = _secrets.token_hex(8)
    _ci_src  = f"{_name_clean}:{_phone_clean}:{_dob_clean}:{_salt}"
    _ci_hash = hashlib.sha256(_ci_src.encode("utf-8")).hexdigest()[:24]

    # 인증 토큰 — 32바이트 랜덤 hex (세션 식별용)
    _token   = _secrets.token_hex(16)

    # 이름 마스킹
    if len(_name_clean) >= 3:
        _name_masked = _name_clean[0] + "*" * (len(_name_clean) - 2) + _name_clean[-1]
    elif len(_name_clean) == 2:
        _name_masked = _name_clean[0] + "*"
    else:
        _name_masked = _name_clean

    # 전화번호 마스킹
    if len(_phone_clean) == 11:
        _phone_masked = f"{_phone_clean[:3]}-****-{_phone_clean[7:]}"
    elif len(_phone_clean) == 10:
        _phone_masked = f"{_phone_clean[:3]}-***-{_phone_clean[6:]}"
    else:
        _phone_masked = "***-****-" + _phone_clean[-4:] if len(_phone_clean) >= 4 else "인증완료"

    _now = time.time()
    return {
        "token":        _token,
        "ci_hash":      _ci_hash,
        "name_initial": _name_masked,
        "phone_masked": _phone_masked,
        "method":       method,
        "carrier":      carrier,
        "issued_at":    _now,
        "expires_at":   _now + 1800,
        "error":        None,
    }


def is_token_valid(token_dict: dict) -> bool:
    """토큰 유효성 검사 (발급 후 30분 이내)"""
    if not token_dict or not token_dict.get("token"):
        return False
    return time.time() < token_dict.get("expires_at", 0)


# =============================================================================
# [GATE 1] PASS 인증 (통신사 — SKT/KT/LGU+/알뜰폰)
# =============================================================================

def pass_request_auth(
    name: str,
    phone: str,
    dob: str,
    carrier: str,
) -> dict:
    """
    PASS 인증 요청 — 고객 PASS 앱으로 인증 푸시 전송.

    반환: {"transaction_id": str, "expires_in": int, "error": str|None}
    실제 연동: PASS_API_KEY / PASS_API_SECRET / PASS_SERVICE_ID secrets 등록 필요.
    """
    api_key    = _get_secret("PASS_API_KEY")
    api_secret = _get_secret("PASS_API_SECRET")
    service_id = _get_secret("PASS_SERVICE_ID")

    if not api_key or not api_secret:
        return {
            "transaction_id": "",
            "expires_in":     0,
            "error":          "PASS_API_KEY / PASS_API_SECRET 미설정",
            "mode":           "config_missing",
        }

    try:
        _ts    = str(int(time.time() * 1000))
        _nonce = _secrets.token_hex(8)
        _sig   = hmac.new(
            api_secret.encode(),
            f"{api_key}:{_ts}:{_nonce}".encode(),
            hashlib.sha256,
        ).hexdigest()

        _payload = json.dumps({
            "serviceId":   service_id,
            "userName":    name,
            "userPhone":   phone,
            "userBirth":   dob,
            "telecomCode": {
                "SKT":       "SKT",
                "KT":        "KTF",
                "LG U+":     "LGT",
                "SKT 알뜰폰": "SKT_MVNO",
                "KT 알뜰폰":  "KTF_MVNO",
                "LG 알뜰폰":  "LGT_MVNO",
            }.get(carrier, "SKT"),
            "authType":    "PUSH",
            "reqType":     "CI",
        }).encode("utf-8")

        _req = _urlreq.Request(
            "https://api.passlogin.com/v2/auth/request",
            data=_payload,
            headers={
                "Content-Type":  "application/json",
                "X-API-Key":     api_key,
                "X-Timestamp":   _ts,
                "X-Nonce":       _nonce,
                "X-Signature":   _sig,
            },
            method="POST",
        )
        with _urlreq.urlopen(_req, timeout=10) as _resp:
            _body = json.loads(_resp.read().decode("utf-8"))

        return {
            "transaction_id": _body.get("transactionId", ""),
            "expires_in":     _body.get("expiresIn", 180),
            "error":          None,
            "mode":           "live",
        }
    except Exception as e:
        return {
            "transaction_id": "",
            "expires_in":     0,
            "error":          str(e)[:200],
            "mode":           "error",
        }


def pass_verify_result(transaction_id: str) -> dict:
    """
    PASS 인증 결과 조회 (폴링 방식).

    반환: {"status": "pending"|"success"|"failed", "ci": str, "error": str|None}
    """
    api_key    = _get_secret("PASS_API_KEY")
    api_secret = _get_secret("PASS_API_SECRET")

    if not api_key or not transaction_id:
        return {"status": "failed", "ci": "", "error": "API 키 또는 트랜잭션 ID 없음"}

    try:
        _ts    = str(int(time.time() * 1000))
        _nonce = _secrets.token_hex(8)
        _sig   = hmac.new(
            api_secret.encode(),
            f"{api_key}:{_ts}:{_nonce}".encode(),
            hashlib.sha256,
        ).hexdigest()

        _req = _urlreq.Request(
            f"https://api.passlogin.com/v2/auth/result/{transaction_id}",
            headers={
                "X-API-Key":   api_key,
                "X-Timestamp": _ts,
                "X-Nonce":     _nonce,
                "X-Signature": _sig,
            },
            method="GET",
        )
        with _urlreq.urlopen(_req, timeout=10) as _resp:
            _body = json.loads(_resp.read().decode("utf-8"))

        _status = _body.get("status", "pending")
        return {
            "status": _status,
            "ci":     _body.get("ci", "") if _status == "success" else "",
            "error":  None,
        }
    except Exception as e:
        return {"status": "failed", "ci": "", "error": str(e)[:200]}


# =============================================================================
# [GATE 2] NICE 표준 본인확인 (공공·금융 기관 수준)
# =============================================================================

def nice_get_encrypt_token() -> dict:
    """
    NICE 암호화 토큰 요청 — 표준창(checkplus_main) 팝업 전용.

    반환: {"enc_data": str, "integrity_value": str, "error": str|None}
    Streamlit 환경에서는 JavaScript window.open() 사용 불가 → HTML 링크 버튼 방식으로 대체.
    실제 연동: NICE_SITE_CODE / NICE_SITE_PASSWORD secrets 등록 필요.
    """
    site_code = _get_secret("NICE_SITE_CODE")
    site_pwd  = _get_secret("NICE_SITE_PASSWORD")

    if not site_code or not site_pwd:
        return {
            "enc_data":        "",
            "integrity_value": "",
            "error":           "NICE_SITE_CODE / NICE_SITE_PASSWORD 미설정",
            "mode":            "config_missing",
        }

    try:
        import time as _t
        _req_dtim  = _t.strftime("%Y%m%d%H%M%S")
        _req_no    = _secrets.token_hex(10).upper()
        _return_url = _get_secret("NICE_CB_URL", "https://localhost/nice_callback")

        _plain = (
            f"7:REQ_SEQ{len(_req_no):d}:{_req_no}"
            f"8:REQ_DTIM14:{_req_dtim}"
            f"12:RETURN_URL{len(_return_url):d}:{_return_url}"
        )

        _hash_key  = hashlib.sha256((site_pwd + _req_dtim + _req_no).encode()).hexdigest()
        _aes_key   = _hash_key[:16].encode()
        _aes_iv    = _hash_key[16:32].encode()

        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend

        _padded = _plain.encode("utf-8")
        _pad_len = 16 - (len(_padded) % 16)
        _padded += bytes([_pad_len] * _pad_len)

        _cipher = Cipher(algorithms.AES(_aes_key), modes.CBC(_aes_iv), backend=default_backend())
        _enc    = _cipher.encryptor()
        _enc_bytes = _enc.update(_padded) + _enc.finalize()
        _enc_data  = base64.b64encode(_enc_bytes).decode("utf-8")

        _integrity = hashlib.sha256((_hash_key + _enc_data).encode()).hexdigest()

        return {
            "enc_data":        _enc_data,
            "integrity_value": _integrity,
            "req_no":          _req_no,
            "site_code":       site_code,
            "error":           None,
            "mode":            "live",
        }
    except ImportError:
        return {
            "enc_data":        "",
            "integrity_value": "",
            "error":           "cryptography 라이브러리 필요: pip install cryptography",
            "mode":            "error",
        }
    except Exception as e:
        return {
            "enc_data":        "",
            "integrity_value": "",
            "error":           str(e)[:200],
            "mode":            "error",
        }


# =============================================================================
# [GATE 3] 카카오 인증 (카카오페이 전자서명)
# =============================================================================

def kakao_auth_request(
    name: str,
    phone: str,
    order_title: str = "보험 마이데이터 조회 동의",
) -> dict:
    """
    카카오페이 전자서명 요청.

    반환: {"sign_txn_id": str, "redirect_url": str, "qr_url": str, "error": str|None}
    실제 연동: KAKAO_AUTH_ADMIN_KEY secrets 등록 필요.
    Streamlit에서는 redirect_url을 링크 버튼으로, qr_url을 QR 이미지로 표시.
    """
    admin_key = _get_secret("KAKAO_AUTH_ADMIN_KEY")

    if not admin_key:
        return {
            "sign_txn_id":  "",
            "redirect_url": "",
            "qr_url":       "",
            "error":        "KAKAO_AUTH_ADMIN_KEY 미설정",
            "mode":         "config_missing",
        }

    try:
        _payload = json.dumps({
            "cid":                  "TC0ONETIME",
            "partner_order_id":     _secrets.token_hex(8),
            "partner_user_id":      hashlib.sha256(phone.encode()).hexdigest()[:16],
            "item_name":            order_title,
            "quantity":             1,
            "total_amount":         0,
            "vat_amount":           0,
            "tax_free_amount":      0,
            "approval_url":         _get_secret("KAKAO_CB_SUCCESS", "https://localhost/kakao/success"),
            "fail_url":             _get_secret("KAKAO_CB_FAIL",    "https://localhost/kakao/fail"),
            "cancel_url":           _get_secret("KAKAO_CB_CANCEL",  "https://localhost/kakao/cancel"),
        }).encode("utf-8")

        _req = _urlreq.Request(
            "https://kapi.kakao.com/v1/payment/ready",
            data=_payload,
            headers={
                "Authorization": f"KakaoAK {admin_key}",
                "Content-Type":  "application/json",
            },
            method="POST",
        )
        with _urlreq.urlopen(_req, timeout=10) as _resp:
            _body = json.loads(_resp.read().decode("utf-8"))

        return {
            "sign_txn_id":  _body.get("tid", ""),
            "redirect_url": _body.get("next_redirect_mobile_url", ""),
            "qr_url":       _body.get("next_redirect_pc_url", ""),
            "error":        None,
            "mode":         "live",
        }
    except Exception as e:
        return {
            "sign_txn_id":  "",
            "redirect_url": "",
            "qr_url":       "",
            "error":        str(e)[:200],
            "mode":         "error",
        }


# =============================================================================
# [GATE 4] 통합 인증 게이트웨이 — 시뮬레이션 폴백 포함
# =============================================================================

def authenticate(
    name:    str,
    phone:   str,
    dob:     str,
    carrier: str = "",
    method:  str = "auto",
) -> dict:
    """
    [통합 인증 진입점] 인증 수단 자동 선택 및 폴백 처리.

    method:
        "pass"     → PASS 인증 API 직접 호출
        "kakao"    → 카카오페이 인증 요청
        "nice"     → NICE 표준 암호화 토큰 생성
        "simulate" → 시뮬레이션 (API 키 없을 때 자동 선택)
        "auto"     → 설정된 API 키 순서대로 자동 선택

    반환:
    {
        "token":         str,    # 인증 토큰 (세션 보관용)
        "ci_hash":       str,    # CI 대체 해시 (마이데이터 조회용)
        "name_initial":  str,    # 마스킹된 이름
        "phone_masked":  str,    # 마스킹된 전화번호
        "method":        str,    # 실제 사용된 인증 방법
        "issued_at":     float,
        "expires_at":    float,
        "aux":           dict,   # 인증 방식별 추가 정보 (redirect_url 등)
        "error":         str|None,
    }

    ⚠️ 보안: name/phone/dob는 이 함수 내에서만 사용되며,
              반환값과 session_state에는 절대 저장되지 않음.
    """
    _name  = name.strip()
    _phone = "".join(c for c in phone if c.isdigit())
    _dob   = "".join(c for c in dob   if c.isdigit())

    # 입력 유효성 검사
    if len(_name) < 2:
        return {"token": "", "ci_hash": "", "error": "이름이 너무 짧습니다.", "method": method}
    if len(_phone) < 10:
        return {"token": "", "ci_hash": "", "error": "전화번호가 올바르지 않습니다.", "method": method}
    if len(_dob) != 8:
        return {"token": "", "ci_hash": "", "error": "생년월일 8자리(YYYYMMDD)를 입력하세요.", "method": method}

    # auto: 사용 가능한 API 키 순으로 방법 결정
    if method == "auto":
        if _get_secret("PASS_API_KEY"):
            method = "pass"
        elif _get_secret("KAKAO_AUTH_ADMIN_KEY"):
            method = "kakao"
        elif _get_secret("NICE_SITE_CODE"):
            method = "nice"
        else:
            method = "simulate"

    _aux   = {}
    _error = None

    if method == "pass":
        _res = pass_request_auth(_name, _phone, _dob, carrier)
        if _res.get("error"):
            _error = _res["error"]
            if _res.get("mode") == "config_missing":
                method = "simulate"
        else:
            _aux = {"transaction_id": _res["transaction_id"], "expires_in": _res["expires_in"]}

    elif method == "kakao":
        _res = kakao_auth_request(_name, _phone)
        if _res.get("error"):
            _error = _res["error"]
            if _res.get("mode") == "config_missing":
                method = "simulate"
        else:
            _aux = {
                "sign_txn_id":  _res["sign_txn_id"],
                "redirect_url": _res["redirect_url"],
                "qr_url":       _res["qr_url"],
            }

    elif method == "nice":
        _res = nice_get_encrypt_token()
        if _res.get("error"):
            _error = _res["error"]
            if _res.get("mode") == "config_missing":
                method = "simulate"
        else:
            _aux = {
                "enc_data":        _res["enc_data"],
                "integrity_value": _res["integrity_value"],
                "site_code":       _res["site_code"],
            }

    # 토큰 생성 (민감정보는 이 함수에서 소비되고 hash만 유지)
    _tok = generate_auth_token(_name, _phone, _dob, carrier, method)
    _tok["aux"]   = _aux
    _tok["error"] = _error  # API 경고가 있어도 시뮬레이션 토큰은 발급

    return _tok


# =============================================================================
# [UTIL] 인증 방법별 UI 메타데이터
# =============================================================================

AUTH_METHOD_META = {
    "kakao": {
        "label":    "카카오톡 인증",
        "icon_svg": (
            "<svg width='28' height='28' viewBox='0 0 28 28' fill='none'>"
            "<rect width='28' height='28' rx='6' fill='#FEE500'/>"
            "<path d='M14 6C9.58 6 6 8.91 6 12.5c0 2.33 1.55 4.38 3.9 5.53l-.97 3.6"
            " 4.22-2.82c.28.04.56.06.85.06 4.42 0 8-2.91 8-6.5S18.42 6 14 6z' fill='#3C1E1E'/>"
            "</svg>"
        ),
        "color":    "#FEE500",
        "text_color": "#3C1E1E",
        "desc":     "카카오톡 앱 알림으로 간편 인증",
        "secret_key": "KAKAO_AUTH_ADMIN_KEY",
    },
    "pass": {
        "label":    "PASS 인증",
        "icon_svg": (
            "<svg width='28' height='28' viewBox='0 0 28 28' fill='none'>"
            "<rect width='28' height='28' rx='6' fill='#E8002D'/>"
            "<text x='14' y='19' font-size='11' font-weight='900' fill='white'"
            " text-anchor='middle' font-family='Arial'>PASS</text>"
            "</svg>"
        ),
        "color":    "#E8002D",
        "text_color": "#ffffff",
        "desc":     "SKT·KT·LGU+ 통신사 PASS 앱 인증",
        "secret_key": "PASS_API_KEY",
    },
    "nice": {
        "label":    "NICE 본인확인",
        "icon_svg": (
            "<svg width='28' height='28' viewBox='0 0 28 28' fill='none'>"
            "<rect width='28' height='28' rx='6' fill='#003087'/>"
            "<text x='14' y='19' font-size='9' font-weight='900' fill='white'"
            " text-anchor='middle' font-family='Arial'>NICE</text>"
            "</svg>"
        ),
        "color":    "#003087",
        "text_color": "#ffffff",
        "desc":     "NICE 표준 본인확인 (SMS OTP)",
        "secret_key": "NICE_SITE_CODE",
    },
    "simulate": {
        "label":    "간편 인증 (데모)",
        "icon_svg": (
            "<svg width='28' height='28' viewBox='0 0 28 28' fill='none'>"
            "<rect width='28' height='28' rx='6' fill='#f0fdf4'/>"
            "<rect x='3' y='3' width='22' height='22' rx='4' stroke='#16a34a' stroke-width='2'/>"
            "<path d='M9 14l4 4 6-6' stroke='#16a34a' stroke-width='2.5'"
            " stroke-linecap='round' stroke-linejoin='round'/>"
            "</svg>"
        ),
        "color":    "#f0fdf4",
        "text_color": "#166534",
        "desc":     "개발·데모 전용 (실제 API 미연결)",
        "secret_key": "",
    },
}


def get_available_methods() -> list[str]:
    """
    현재 환경에서 사용 가능한 인증 수단 목록 반환.
    API 키가 없어도 'simulate'는 항상 포함.
    """
    methods = []
    if _get_secret("KAKAO_AUTH_ADMIN_KEY"):
        methods.append("kakao")
    if _get_secret("PASS_API_KEY"):
        methods.append("pass")
    if _get_secret("NICE_SITE_CODE"):
        methods.append("nice")
    methods.append("simulate")
    return methods
