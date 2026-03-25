"""HEAD API 공통 보안 의존성.

- Bearer 인증(HMAC 서명 토큰) 검증
- request.state.user_id 주입
- 테넌트 강제(Body user_id 신뢰 금지)
"""
from __future__ import annotations

import hmac
import os
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)
_MAX_TOKEN_AGE_SEC = 300


@dataclass
class AuthContext:
    user_id: str
    token_ts: int


def _secret() -> str:
    return os.environ.get("ENCRYPTION_KEY", "gk_token_secret_2026")


def _verify_signed_bearer(token: str) -> AuthContext:
    # format: <user_id>.<ts>.<sig32>
    try:
        uid, ts_s, sig = token.split(".", 2)
        ts = int(ts_s)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_format")
    if not uid or len(sig) < 16:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_payload")
    now = int(time.time())
    if abs(now - ts) > _MAX_TOKEN_AGE_SEC:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_expired")
    expected = hmac.new(_secret().encode(), f"{uid}.{ts}".encode(), "sha256").hexdigest()[:32]
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token_signature_mismatch")
    return AuthContext(user_id=uid, token_ts=ts)


def get_auth_context(
    request: Request,
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> AuthContext:
    if cred is None or (cred.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing_bearer_token")
    ctx = _verify_signed_bearer(cred.credentials or "")
    request.state.user_id = ctx.user_id
    return ctx
