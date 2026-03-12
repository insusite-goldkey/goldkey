import os
import urllib.request, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SUPABASE_URL = 'https://idfzizqidhnpzbqioqqo.supabase.co'
SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

def sql_query(sql):
    body = json.dumps(sql).encode()
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/rpc/exec_sql',
        data=body,
        headers={
            'apikey': SERVICE_KEY,
            'Authorization': f'Bearer {SERVICE_KEY}',
            'Content-Type': 'application/json',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return str(e)

# Supabase에서 pg_tables RLS 상태 조회 (Management API 방식)
# /rest/v1/ 로는 pg_tables 직접 조회 불가 → 대신 information_schema 우회
headers = {
    'apikey': SERVICE_KEY,
    'Authorization': f'Bearer {SERVICE_KEY}',
}

# 1. pending_wisdom 테이블 컬럼 구조 확인
for tname in ['pending_wisdom', 'user_files']:
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/{tname}?select=*&limit=0',
        headers={**headers, 'Prefer': 'count=exact'}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print(f"[{tname}] status={r.status}, Content-Range={r.headers.get('Content-Range','')}")
            # 컬럼 정보
            info_req = urllib.request.Request(
                f'{SUPABASE_URL}/rest/v1/{tname}?limit=1',
                headers=headers
            )
            with urllib.request.urlopen(info_req, timeout=8) as r2:
                data = json.loads(r2.read().decode())
                if data:
                    print(f"  columns: {list(data[0].keys())}")
                else:
                    print(f"  (empty table — columns unknown)")
    except Exception as e:
        print(f"[{tname}] error: {e}")

# 2. anon 키 없이 공개 접근 가능 여부 재확인 (apikey 헤더 완전 제거)
print("\n=== apikey 헤더 완전 제거 테스트 ===")
for tname in ['pending_wisdom', 'user_files']:
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/{tname}?select=*&limit=1'
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print(f"  [OPEN!] {tname}: apikey 없이 접근 가능 — 취약점!")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {tname}: apikey 없으면 차단 ({e.reason})")
    except Exception as e:
        print(f"  [ERR] {tname}: {e}")
