"""
Supabase usage_log 테이블 생성 스크립트
실행: python create_usage_log_table.py
"""
import os, sys, re

# ── secrets.toml에서 Supabase 접속 정보 읽기 (정규식 파싱) ──────────────
def _load_secrets():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
    if not os.path.exists(toml_path):
        print(f"[ERROR] secrets.toml not found: {toml_path}")
        return None, None
    try:
        with open(toml_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] secrets.toml 읽기 실패: {e}")
        return None, None
    # key = "value" 또는 key = 'value' 패턴 추출
    def _get(keys):
        for k in keys:
            m = re.search(rf'^\s*{re.escape(k)}\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
            if m:
                return m.group(1).strip()
        return ""
    url = _get(["SUPABASE_URL", "url"]) or os.environ.get("SUPABASE_URL", "")
    key = _get(["SUPABASE_SERVICE_ROLE_KEY", "service_role_key"]) or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    return url.strip(), key.strip()

url, key = _load_secrets()
if not url or not key:
    print("[ERROR] SUPABASE_URL 또는 SUPABASE_SERVICE_ROLE_KEY를 찾을 수 없습니다.")
    sys.exit(1)

import urllib.request, urllib.error, json as _json

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ── 1단계: 테이블 존재 여부 확인 (GET /rest/v1/usage_log?limit=1) ─────────
print(f"Supabase URL: {url[:40]}...")
print("usage_log 테이블 존재 여부 확인 중...")

check_url = f"{url}/rest/v1/usage_log?select=user_name&limit=1"
req = urllib.request.Request(check_url, headers=headers, method="GET")
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = _json.loads(resp.read())
        print(f"[OK] usage_log 테이블이 이미 존재합니다. 행 수: {len(data)}")
        sys.exit(0)
except urllib.error.HTTPError as e:
    body = e.read().decode("utf-8", errors="replace")
    if e.code == 404 or "does not exist" in body or "42P01" in body or "relation" in body.lower():
        print("[INFO] 테이블 없음 → 생성 시도...")
    else:
        print(f"[WARN] 조회 응답 {e.code}: {body[:200]}")
        print("생성 시도를 계속합니다...")
except Exception as e:
    print(f"[WARN] 연결 오류: {e}")
    print("생성 시도를 계속합니다...")

# ── 2단계: Supabase Management API로 SQL 실행 ────────────────────────────
# POST https://<project>.supabase.co/rest/v1/rpc/<func> 방식은 함수 필요
# 대신 Supabase Management REST API 사용
SQL = (
    "CREATE TABLE IF NOT EXISTS usage_log ("
    "user_name TEXT NOT NULL, "
    "log_date TEXT NOT NULL, "
    "count INTEGER DEFAULT 0, "
    "PRIMARY KEY (user_name, log_date)"
    ");"
)

# project ref 추출
ref = url.replace("https://", "").split(".")[0]
mgmt_url = f"https://api.supabase.com/v1/projects/{ref}/database/query"
mgmt_headers = {
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
}
body = _json.dumps({"query": SQL}).encode("utf-8")
req2 = urllib.request.Request(mgmt_url, data=body, headers=mgmt_headers, method="POST")
try:
    with urllib.request.urlopen(req2, timeout=15) as resp:
        result = resp.read().decode("utf-8", errors="replace")
        print(f"[OK] usage_log 테이블 생성 완료!\n응답: {result[:200]}")
        sys.exit(0)
except urllib.error.HTTPError as e:
    body_r = e.read().decode("utf-8", errors="replace")
    print(f"[WARN] Management API 응답 {e.code}: {body_r[:300]}")
except Exception as e:
    print(f"[WARN] Management API 실패: {e}")

# ── 3단계: 모두 실패 시 수동 안내 ────────────────────────────────────────
print("\n" + "="*60)
print("자동 생성 실패. 아래 방법 중 하나로 수동 실행하세요:")
print("="*60)
print("\n[방법 1] Supabase Dashboard → SQL Editor")
print(f"URL: https://supabase.com/dashboard/project/{ref}/sql/new")
print("\n실행할 SQL:")
print("-"*40)
print(SQL)
print("-"*40)
