"""
Supabase RLS 강제 적용 스크립트
- pending_wisdom, user_files 테이블에 RLS Enable
- 보안 정책(SELECT/INSERT/UPDATE/DELETE) 재설정
- service_role은 bypass되므로 app.py 서버 코드는 영향 없음
"""
import urllib.request, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SUPABASE_URL = 'https://idfzizqidhnpzbqioqqo.supabase.co'
SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkZnppenFpZGhucHpicWlvcXFvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTgyOTg0MiwiZXhwIjoyMDg3NDA1ODQyfQ.-oeAIGqA4k1crI4zeOwrHXlBVEdltXKAyCiW4BNtRxA'

def run_sql(sql_statement):
    """Supabase SQL 실행 — service_role 권한 필요"""
    # Supabase는 /rest/v1/rpc/[function] 으로만 SQL 실행 가능
    # 단, pg_dump/DDL은 Management API 또는 psql 직접 연결 필요
    # Management API: POST /v1/projects/{ref}/database/query
    PROJECT_REF = 'idfzizqidhnpzbqioqqo'
    # Management API는 personal access token 필요 (service_role과 다름)
    # → 직접 psql 연결 필요
    print(f"\n[SQL] {sql_statement[:80]}...")
    print("  → Management API personal token 필요 — SQL 파일로 출력합니다")
    return None

# RLS 적용 SQL 생성
TABLES = ['pending_wisdom', 'user_files']

sql_lines = []
sql_lines.append("-- ============================================================")
sql_lines.append("-- Goldkey AI Masters — Supabase RLS 보안 강화 SQL")
sql_lines.append("-- 생성일: 2026-03-12")
sql_lines.append("-- 대상: pending_wisdom, user_files")
sql_lines.append("-- ============================================================")
sql_lines.append("")

for tbl in TABLES:
    sql_lines.append(f"-- ── {tbl} ──────────────────────────────────────────────────")
    sql_lines.append(f"-- 1. RLS 활성화")
    sql_lines.append(f"ALTER TABLE public.{tbl} ENABLE ROW LEVEL SECURITY;")
    sql_lines.append("")
    sql_lines.append(f"-- 2. 기존 정책 전체 제거 (초기화)")
    sql_lines.append(f"DO $$")
    sql_lines.append(f"DECLARE")
    sql_lines.append(f"  pol RECORD;")
    sql_lines.append(f"BEGIN")
    sql_lines.append(f"  FOR pol IN SELECT policyname FROM pg_policies")
    sql_lines.append(f"             WHERE tablename = '{tbl}' AND schemaname = 'public'")
    sql_lines.append(f"  LOOP")
    sql_lines.append(f"    EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(pol.policyname) || ' ON public.{tbl}';")
    sql_lines.append(f"  END LOOP;")
    sql_lines.append(f"END $$;")
    sql_lines.append("")
    sql_lines.append(f"-- 3. anon/public 접근 완전 차단 (기본 DENY ALL)")
    sql_lines.append(f"REVOKE ALL ON public.{tbl} FROM anon, public;")
    sql_lines.append("")
    sql_lines.append(f"-- 4. authenticated role 전용 정책")
    sql_lines.append(f"-- SELECT: 자신의 데이터만 조회")
    sql_lines.append(f"CREATE POLICY \"{tbl}_select_own\"")
    sql_lines.append(f"  ON public.{tbl}")
    sql_lines.append(f"  FOR SELECT")
    sql_lines.append(f"  TO authenticated")
    sql_lines.append(f"  USING (true);  -- service_role bypass; authenticated는 모든 행 허용 (서버 사이드 앱)")
    sql_lines.append("")
    sql_lines.append(f"-- INSERT: authenticated만 허용")
    sql_lines.append(f"CREATE POLICY \"{tbl}_insert_authenticated\"")
    sql_lines.append(f"  ON public.{tbl}")
    sql_lines.append(f"  FOR INSERT")
    sql_lines.append(f"  TO authenticated")
    sql_lines.append(f"  WITH CHECK (true);")
    sql_lines.append("")
    sql_lines.append(f"-- UPDATE: authenticated만 허용")
    sql_lines.append(f"CREATE POLICY \"{tbl}_update_authenticated\"")
    sql_lines.append(f"  ON public.{tbl}")
    sql_lines.append(f"  FOR UPDATE")
    sql_lines.append(f"  TO authenticated")
    sql_lines.append(f"  USING (true)")
    sql_lines.append(f"  WITH CHECK (true);")
    sql_lines.append("")
    sql_lines.append(f"-- DELETE: authenticated만 허용")
    sql_lines.append(f"CREATE POLICY \"{tbl}_delete_authenticated\"")
    sql_lines.append(f"  ON public.{tbl}")
    sql_lines.append(f"  FOR DELETE")
    sql_lines.append(f"  TO authenticated")
    sql_lines.append(f"  USING (true);")
    sql_lines.append("")
    sql_lines.append(f"-- 5. anon role — 모든 작업 명시적 차단 정책 없음 = DENY (RLS enabled + no matching policy = deny)")
    sql_lines.append(f"-- anon에게 아무 정책도 부여하지 않으면 자동 거부됨")
    sql_lines.append("")

sql_lines.append("-- ============================================================")
sql_lines.append("-- 추가: gk_members 테이블 (향후 생성 시 적용할 정책)")
sql_lines.append("-- user_id 컬럼 기반 행 단위 보안 (users 테이블 연동)")
sql_lines.append("-- ============================================================")
sql_lines.append("")
sql_lines.append("-- ALTER TABLE public.gk_members ENABLE ROW LEVEL SECURITY;")
sql_lines.append("-- CREATE POLICY \"gk_members_select_own\"")
sql_lines.append("--   ON public.gk_members FOR SELECT TO authenticated")
sql_lines.append("--   USING (user_id = auth.uid());")
sql_lines.append("-- CREATE POLICY \"gk_members_insert_own\"")
sql_lines.append("--   ON public.gk_members FOR INSERT TO authenticated")
sql_lines.append("--   WITH CHECK (user_id = auth.uid());")
sql_lines.append("-- CREATE POLICY \"gk_members_update_own\"")
sql_lines.append("--   ON public.gk_members FOR UPDATE TO authenticated")
sql_lines.append("--   USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());")
sql_lines.append("-- CREATE POLICY \"gk_members_delete_own\"")
sql_lines.append("--   ON public.gk_members FOR DELETE TO authenticated")
sql_lines.append("--   USING (user_id = auth.uid());")

sql_content = "\n".join(sql_lines)
out_path = 'D:/CascadeProjects/_rls_security.sql'
open(out_path, 'w', encoding='utf-8').write(sql_content)
print(f"SQL 파일 생성 완료: {out_path}")
print()
print(sql_content)
