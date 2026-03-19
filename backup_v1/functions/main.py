"""
functions/main.py — Goldkey AI Masters 2026
GCP Cloud Functions: verifyOTP (TOTP RFC 6238)

배포 명령:
  gcloud functions deploy verifyOTP \
    --project goldkey-ai-2026 \
    --runtime python312 \
    --trigger-http \
    --allow-unauthenticated \
    --region asia-northeast3 \
    --entry-point verify_otp \
    --set-env-vars GCP_PROJECT=goldkey-ai-2026

Firestore 경로: users/{userId}/secrets → { totp_secret: "BASE32..." }
"""
from __future__ import annotations

import hashlib
import base64
import functions_framework
import pyotp
from flask import Request, jsonify
from google.cloud import firestore

# ── 상수 ────────────────────────────────────────────────────────────────────
GCP_PROJECT    = "goldkey-ai-2026"
APP_SALT       = "GK-AI-2026-TOTP-SALT"
VALID_WINDOW   = 1       # ±30초 (총 3개 토큰 허용)
MAX_ATTEMPTS   = 5

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=GCP_PROJECT)
    return _db


def _derive_secret(person_id: str) -> str:
    """DB에 secret 없을 때 person_id 기반 결정론적 파생 (fallback)"""
    raw = hashlib.sha256(f"{APP_SALT}:{person_id}".encode()).digest()
    return base64.b32encode(raw[:20]).decode()


def _get_secret(person_id: str) -> str:
    """Firestore users/{person_id}/secrets 에서 totp_secret 조회. 없으면 파생값."""
    try:
        db   = _get_db()
        doc  = db.collection("users").document(person_id).collection("secrets").document("totp").get()
        if doc.exists:
            data = doc.to_dict() or {}
            return data.get("totp_secret") or _derive_secret(person_id)
    except Exception:
        pass
    return _derive_secret(person_id)


@functions_framework.http
def verify_otp(request: Request):
    """
    POST /verifyOTP
    Body: { "person_id": "uuid", "token": "123456" }
    Response: { "valid": true/false, "message": "..." }
    """
    # CORS 프리플라이트
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin":  "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
        }
        return ("", 204, headers)

    cors_headers = {"Access-Control-Allow-Origin": "*"}

    if request.method != "POST":
        return jsonify({"valid": False, "message": "POST only"}), 405, cors_headers

    body = request.get_json(silent=True) or {}
    person_id = (body.get("person_id") or "").strip()
    token     = (body.get("token")     or "").strip()

    if not person_id or not token:
        return jsonify({"valid": False, "message": "person_id와 token 필수"}), 400, cors_headers

    if len(token) != 6 or not token.isdigit():
        return jsonify({"valid": False, "message": "token은 6자리 숫자"}), 400, cors_headers

    # 시도 횟수 제한 (Firestore 카운터)
    db = _get_db()
    attempt_ref = db.collection("otp_attempts").document(person_id)
    attempt_doc = attempt_ref.get()
    attempts    = (attempt_doc.to_dict() or {}).get("count", 0) if attempt_doc.exists else 0

    if attempts >= MAX_ATTEMPTS:
        return jsonify({
            "valid":   False,
            "message": f"시도 횟수({MAX_ATTEMPTS}회) 초과. 관리자에게 문의하세요.",
        }), 429, cors_headers

    # TOTP 검증
    secret = _get_secret(person_id)
    totp   = pyotp.TOTP(secret)
    valid  = totp.verify(token, valid_window=VALID_WINDOW)

    if valid:
        # 성공 시 카운터 초기화
        attempt_ref.set({"count": 0})
        return jsonify({"valid": True,  "message": "인증 성공"}), 200, cors_headers
    else:
        # 실패 시 카운터 증가
        attempt_ref.set({"count": attempts + 1})
        left = MAX_ATTEMPTS - attempts - 1
        return jsonify({
            "valid":   False,
            "message": f"코드 불일치. 남은 시도: {left}회",
        }), 401, cors_headers
