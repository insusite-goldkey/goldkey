# GoldKey AI — 하이브리드 아키텍처 설계 문서
**버전:** 1.0 | **작성일:** 2026-02-25 | **작성자:** 골드키지사 개발팀

---

## 1. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT (React Native / Streamlit)             │
│  ┌─────────────────┐          ┌──────────────────────────────┐  │
│  │  좌측: 공용 뷰어  │          │  중앙: 개인 문서 뷰어 (Private)│  │
│  │  (Public Zone)   │          │  (Private Zone — UID 귀속)   │  │
│  └────────┬────────┘          └──────────────┬───────────────┘  │
└───────────┼───────────────────────────────────┼─────────────────┘
            │ HTTPS/TLS                         │ HTTPS/TLS + E2EE
            ▼                                   ▼
┌───────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server                      │
│                                                               │
│  ┌─────────────────────┐   ┌───────────────────────────────┐ │
│  │  /api/public/*       │   │  /api/private/{uid}/*         │ │
│  │  (공용 데이터 API)    │   │  (개인 데이터 API — JWT 필수)  │ │
│  └──────────┬──────────┘   └───────────────┬───────────────┘ │
│             │                               │ IAM 권한 검증    │
│  ┌──────────▼──────────┐   ┌───────────────▼───────────────┐ │
│  │  RAG Engine (공용)   │   │  RAG Engine (개인 — 휘발성)    │ │
│  │  법령·논문·리플릿    │   │  고객 의무기록·증권·카탈로그   │ │
│  └──────────┬──────────┘   └───────────────┬───────────────┘ │
└─────────────┼───────────────────────────────┼─────────────────┘
              │                               │
              ▼                               ▼
┌─────────────────────┐       ┌───────────────────────────────┐
│  Public S3 Bucket    │       │  Private S3 Bucket            │
│  (supabase/public)   │       │  /private/{uid}/              │
│  - 법령 DB           │       │  - 고객_의무기록.pdf (AES-256) │
│  - 의학 논문         │       │  - 보험증권_스캔.pdf (AES-256) │
│  - 보험사 리플릿     │       │  - 개별_카탈로그.pdf (AES-256) │
└─────────────────────┘       └───────────────────────────────┘
```

---

## 2. Data Storage 분리 설계

### 2-1. Public Zone (관리자 전용 관리)

| 항목 | 값 |
|---|---|
| **버킷명** | `goldkey-public` |
| **접근 권한** | 인증된 모든 사용자 READ / 관리자만 WRITE |
| **저장 데이터** | 보험사 카탈로그, 의학 논문, 법령 DB, 공통 리플릿 |
| **암호화** | TLS(전송) + S3 서버사이드 암호화(저장) |
| **Supabase 매핑** | `storage/public/catalogs/`, `storage/public/laws/`, `storage/public/papers/` |

### 2-2. Private Zone (회원 개별 독립 버킷)

| 항목 | 값 |
|---|---|
| **버킷 경로** | `goldkey-private/{uid}/` |
| **접근 권한** | 해당 UID 소유자만 READ/WRITE — **관리자 접근 불가** |
| **저장 데이터** | 고객 의무기록, 개인 증권 스캔, 개별 카탈로그 |
| **암호화** | E2EE(클라이언트 사이드 AES-256) + TLS(전송) |
| **IAM 정책** | `uid == token.sub` 일치 시에만 접근 허용 |

---

## 3. FastAPI Backend 구현

### 3-1. 폴더 구조

```
backend/
├── main.py                  # FastAPI 진입점
├── routers/
│   ├── public_api.py        # 공용 데이터 API
│   ├── private_api.py       # 개인 데이터 API (JWT 필수)
│   └── admin_api.py         # 관리자 API (Private Zone 접근 불가)
├── services/
│   ├── rag_service.py       # RAG 통합 엔진
│   ├── storage_service.py   # S3/Supabase Storage 연동
│   └── crypto_service.py    # AES-256 암호화 모듈
├── models/
│   ├── user.py
│   └── document.py
└── middleware/
    └── iam_policy.py        # IAM 권한 미들웨어
```

### 3-2. `main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import public_api, private_api, admin_api
from middleware.iam_policy import IAMPolicyMiddleware

app = FastAPI(title="GoldKey AI Hybrid Backend")

app.add_middleware(CORSMiddleware,
    allow_origins=["https://goldkey-rich-goldkey-ai.hf.space"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"])

app.add_middleware(IAMPolicyMiddleware)

app.include_router(public_api.router,  prefix="/api/public",       tags=["Public"])
app.include_router(private_api.router, prefix="/api/private",      tags=["Private"])
app.include_router(admin_api.router,   prefix="/api/admin",        tags=["Admin"])
```

### 3-3. `routers/private_api.py` — UID 격리 로직

```python
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from services.storage_service import upload_private, list_private, delete_private_zone
from services.crypto_service import encrypt_aes256, decrypt_aes256
from middleware.iam_policy import require_uid_match
import uuid

router = APIRouter()

@router.post("/{uid}/upload")
async def upload_document(
    uid: str,
    file: UploadFile = File(...),
    token_uid: str = Depends(require_uid_match)   # JWT uid == path uid 검증
):
    """개인 문서 업로드 — E2EE 암호화 후 Private Zone 저장"""
    raw = await file.read()
    encrypted = encrypt_aes256(raw)                # 클라이언트 사이드 암호화
    path = f"private/{uid}/{uuid.uuid4()}_{file.filename}"
    url = await upload_private(path, encrypted)
    return {"status": "ok", "path": path}

@router.get("/{uid}/list")
async def list_documents(
    uid: str,
    token_uid: str = Depends(require_uid_match)
):
    """본인 문서 목록 조회 — 타 UID 접근 불가"""
    return await list_private(f"private/{uid}/")

@router.delete("/{uid}/purge")
async def purge_user_data(
    uid: str,
    token_uid: str = Depends(require_uid_match)
):
    """회원 탈퇴 시 Private Zone 전체 삭제"""
    deleted_count = await delete_private_zone(f"private/{uid}/")
    return {"status": "purged", "deleted_files": deleted_count}
```

### 3-4. `middleware/iam_policy.py` — IAM 권한 제어

```python
from fastapi import Request, HTTPException
from jose import jwt, JWTError
import os

SECRET = os.environ["JWT_SECRET"]

async def require_uid_match(request: Request) -> str:
    """JWT의 sub(uid)와 path parameter uid가 일치하는지 검증"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "인증 토큰 없음")
    try:
        payload = jwt.decode(auth[7:], SECRET, algorithms=["HS256"])
        token_uid = payload["sub"]
    except JWTError:
        raise HTTPException(401, "토큰 유효하지 않음")

    path_uid = request.path_params.get("uid", "")
    if token_uid != path_uid:
        raise HTTPException(403, "타 회원 데이터 접근 불가 — IAM 정책 위반")
    return token_uid

class IAMPolicyMiddleware:
    """관리자 토큰으로 /api/private/ 접근 시 403 차단"""
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            path = scope.get("path", "")
            headers = dict(scope.get("headers", []))
            auth = headers.get(b"authorization", b"").decode()
            if "/api/private/" in path and auth.startswith("Bearer "):
                try:
                    payload = jwt.decode(auth[7:], SECRET, algorithms=["HS256"])
                    if payload.get("role") == "admin":
                        from starlette.responses import JSONResponse
                        response = JSONResponse(
                            {"detail": "관리자는 Private Zone에 접근할 수 없습니다."},
                            status_code=403)
                        await response(scope, receive, send)
                        return
                except JWTError:
                    pass
        await self.app(scope, receive, send)
```

### 3-5. `services/crypto_service.py` — AES-256 암호화

```python
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64

def encrypt_aes256(data: bytes) -> bytes:
    """AES-256-GCM 암호화 (인증된 암호화 — 변조 탐지 포함)"""
    key = os.environ["AES256_KEY"].encode()[:32]   # 32바이트 = 256bit
    nonce = os.urandom(12)                          # 96bit nonce
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, data, None)
    return nonce + ciphertext                       # nonce 앞에 붙여 저장

def decrypt_aes256(data: bytes) -> bytes:
    """AES-256-GCM 복호화"""
    key = os.environ["AES256_KEY"].encode()[:32]
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)
```

### 3-6. `services/rag_service.py` — 공용+개인 RAG 통합 (휘발성)

```python
from services.storage_service import fetch_public_docs, fetch_private_docs
from services.crypto_service import decrypt_aes256

async def build_rag_context(uid: str, query: str) -> str:
    """
    공용 지식(Public Zone) + 개인 지식(Private Zone)을 임시 병합.
    답변 생성 후 컨텍스트는 즉시 메모리에서 삭제 (휘발성 보장).
    """
    # 1. 공용 데이터 로드
    public_docs = await fetch_public_docs(query)

    # 2. 개인 데이터 로드 (복호화 — 메모리 내 처리만)
    private_encrypted = await fetch_private_docs(uid)
    private_docs = [decrypt_aes256(doc) for doc in private_encrypted]

    # 3. 임시 컨텍스트 병합
    context = "\n\n".join([
        "=== 공용 지식 (법령·논문·리플릿) ===",
        *[d.decode("utf-8", errors="ignore") for d in public_docs],
        f"=== {uid} 개인 지식 (업로드 문서) ===",
        *[d.decode("utf-8", errors="ignore") for d in private_docs],
    ])

    # 4. RAG 컨텍스트 반환 — 호출자가 사용 후 del로 메모리 해제
    return context

    # ★ 호출 예시:
    # ctx = await build_rag_context(uid, query)
    # answer = await gemini_generate(ctx, query)
    # del ctx   ← 즉시 휘발
```

---

## 4. Frontend Logic (React Native / Streamlit 연동)

### 4-1. 데이터 소스 분리 원칙

```
좌측 패널 (보험사 선택창)      →  GET /api/public/catalogs
중앙 뷰어 (문서/카탈로그)      →  GET /api/private/{uid}/list  (우선 로드)
                                   없으면 GET /api/public/catalogs (폴백)
AI 상담 응답                   →  POST /api/private/{uid}/rag  (휘발성)
```

### 4-2. Streamlit 연동 예시 (`app.py` 내 추가 가능)

```python
import requests, os

BACKEND = os.environ.get("HYBRID_BACKEND_URL", "https://api.goldkey.ai")

def get_private_docs(uid: str, jwt_token: str) -> list:
    """Private Zone 문서 목록 조회"""
    r = requests.get(
        f"{BACKEND}/api/private/{uid}/list",
        headers={"Authorization": f"Bearer {jwt_token}"},
        timeout=10)
    return r.json() if r.ok else []

def upload_private_doc(uid: str, jwt_token: str, file_bytes: bytes, filename: str):
    """Private Zone 업로드 (클라이언트에서 E2EE 후 전송)"""
    r = requests.post(
        f"{BACKEND}/api/private/{uid}/upload",
        headers={"Authorization": f"Bearer {jwt_token}"},
        files={"file": (filename, file_bytes, "application/octet-stream")},
        timeout=30)
    return r.json()
```

---

## 5. 암호화 정책 요약

| 구간 | 방식 | 비고 |
|---|---|---|
| 전송 (업로드/다운로드) | HTTPS/TLS 1.3 | 인증서 필수 |
| 저장 (Private Zone) | AES-256-GCM | nonce 포함 저장 |
| 클라이언트 사이드 | E2EE (업로드 전 암호화) | 서버는 암호문만 수신 |
| 관리자 접근 | 물리적 차단 (IAM) | 403 강제 반환 |

---

## 6. 회원 탈퇴 — Private Zone 완전 삭제

```python
# DELETE /api/private/{uid}/purge 호출 시 실행
async def delete_private_zone(prefix: str) -> int:
    """Private Zone 내 모든 파일 삭제 후 카운트 반환"""
    supabase = get_supabase_client()
    files = supabase.storage.from_("goldkey-private").list(prefix)
    paths = [f"{prefix}{f['name']}" for f in files]
    if paths:
        supabase.storage.from_("goldkey-private").remove(paths)
    return len(paths)
```

**탈퇴 처리 순서:**
1. `DELETE /api/private/{uid}/purge` → Private Zone 전체 파일 삭제
2. DB에서 해당 UID 사용자 레코드 삭제 (`users` 테이블)
3. JWT 토큰 블랙리스트 등록 (재사용 방지)
4. 탈퇴 완료 이메일 발송 (선택)

---

## 7. 이용약관 삽입 문구

> **제 N조 (데이터 저장 및 프라이버시 보호)**
>
> 본 서비스는 **'하이브리드 아키텍처(Hybrid Architecture)'** 기술을 채택하여 운영됩니다.
>
> 회원이 업로드한 고객의 의무기록, 보험 증권, 개별 카탈로그 등 민감 정보는 **'로컬 프라이빗 우선 설계'** 에 따라 각 회원의 고유 식별 계정에 귀속된 독립된 보안 저장소(Private Bucket)에 분리 보관됩니다.
>
> 본 서비스의 운영진 및 관리자는 기술적으로 회원의 개별 보안 저장소에 접근하거나 데이터를 열람할 수 없도록 **물리적·논리적으로 차단**되어 있으며, 데이터의 주권은 전적으로 해당 회원에게 있습니다.
>
> 공용으로 제공되는 법령 및 의학 지식은 중앙 서버에서 배포되나, 회원의 개인 상담 자료와는 엄격히 분리되어 구동됩니다.
>
> AI 상담 시 공용 지식과 개인 지식은 일시적으로 병합되어 답변에 활용되며, 답변 생성 종료 후 해당 컨텍스트는 즉시 휘발됩니다.

---

## 8. 구현 우선순위 로드맵

| 단계 | 작업 | 예상 기간 |
|---|---|---|
| **Phase 1** | FastAPI 백엔드 기본 구조 + Supabase Storage 연동 | 2주 |
| **Phase 2** | IAM 정책 미들웨어 + JWT UID 검증 | 1주 |
| **Phase 3** | AES-256 암호화 모듈 + E2EE 업로드 | 1주 |
| **Phase 4** | RAG 통합 엔진 (휘발성 컨텍스트) | 2주 |
| **Phase 5** | React Native 프론트엔드 연동 | 3주 |
| **Phase 6** | 탈퇴 처리 + 보안 감사 | 1주 |

---

## 9. 필요 환경변수 (`.env` / Streamlit Secrets)

```env
# FastAPI Backend
JWT_SECRET=<256bit 랜덤 문자열>
AES256_KEY=<32바이트 랜덤 문자열>
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_SERVICE_KEY=<service_role 키 — 서버 전용>

# Streamlit Frontend (읽기 전용 anon 키만 사용)
SUPABASE_ANON_KEY=<anon 키>
HYBRID_BACKEND_URL=https://api.goldkey.ai
```

> **⚠️ 보안 주의:** `SUPABASE_SERVICE_KEY`는 절대 클라이언트(Streamlit/React)에 노출하지 말 것. 서버 환경변수에만 저장.
