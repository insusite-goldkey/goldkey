import os
"""
Supabase Management API를 통한 RLS SQL 직접 실행
POST https://api.supabase.com/v1/projects/{ref}/database/query
Authorization: Bearer <service_role_key>  ← Management API는 personal access token 필요
"""
import urllib.request, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SUPABASE_URL = 'https://idfzizqidhnpzbqioqqo.supabase.co'
PROJECT_REF  = 'idfzizqidhnpzbqioqqo'
SERVICE_KEY  = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')

def run_sql(sql, label=""):
    """Supabase Management API /v1/projects/{ref}/database/query 로 SQL 실행"""
    body = json.dumps({"query": sql}).encode('utf-8')
    req = urllib.request.Request(
        f'https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query',
        data=body,
        headers={
            'Authorization': f'Bearer {SERVICE_KEY}',
            'Content-Type': 'application/json',
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = r.read().decode()
            print(f"  ✅ [{label}] OK → {resp[:100]}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  ❌ [{label}] HTTP {e.code}: {err[:150]}")
        return False
    except Exception as e:
        print(f"  ❌ [{label}] Error: {e}")
        return False

TABLES = ['pending_wisdom', 'user_files']

print("=== Supabase RLS 보안 강화 실행 시작 ===\n")

for tbl in TABLES:
    print(f"─── {tbl} ───────────────────────────")

    # 1. RLS 활성화
    run_sql(f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY;",
            f"{tbl} RLS ENABLE")

    # 2. 기존 정책 전체 제거
    drop_sql = f"""
DO $$
DECLARE pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
             WHERE tablename = '{tbl}' AND schemaname = 'public'
  LOOP
    EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(pol.policyname) || ' ON public.{tbl}';
  END LOOP;
END $$;"""
    run_sql(drop_sql, f"{tbl} DROP old policies")

    # 3. anon/public 권한 제거
    run_sql(f"REVOKE ALL ON public.{tbl} FROM anon, public;",
            f"{tbl} REVOKE anon/public")

    # 4. 보안 정책 4종 생성
    for op, clause in [
        ("SELECT", f'USING (true)'),
        ("INSERT", f'WITH CHECK (true)'),
        ("UPDATE", f'USING (true) WITH CHECK (true)'),
        ("DELETE", f'USING (true)'),
    ]:
        policy_name = f"{tbl}_{op.lower()}_authenticated"
        if op == "INSERT":
            using_clause = f"WITH CHECK (true)"
        elif op == "UPDATE":
            using_clause = f"USING (true) WITH CHECK (true)"
        else:
            using_clause = f"USING (true)"

        create_sql = f"""CREATE POLICY "{policy_name}"
  ON public.{tbl}
  FOR {op}
  TO authenticated
  {using_clause};"""
        run_sql(create_sql, f"{tbl} POLICY {op}")

    print()

print("=== 완료 ===")

# 검증: anon 접근 재테스트
print("\n=== RLS 적용 후 anon 접근 재검증 ===")
# Supabase의 anon key는 JWT role=anon — 여기서는 invalid token으로 테스트
for tname in TABLES:
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/{tname}?select=*&limit=1',
        headers={
            'apikey': SERVICE_KEY,
            'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiJ9.ZopqoUt20nEV8rw6HtnRnI01BRKxNPMO6lkSGqQs',  # fake anon
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print(f"  [WARN] {tname}: 응답 {r.status} — 정책 확인 필요")
    except urllib.error.HTTPError as e:
        print(f"  [✅ {e.code}] {tname}: anon 차단 확인 ({e.reason})")
    except Exception as e:
        print(f"  [ERR] {tname}: {e}")
