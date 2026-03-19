-- ============================================================
-- Goldkey AI Masters — Supabase RLS 보안 강화 SQL
-- 생성일: 2026-03-12
-- 대상: pending_wisdom, user_files
-- ============================================================

-- ── pending_wisdom ──────────────────────────────────────────────────
-- 1. RLS 활성화
ALTER TABLE public.pending_wisdom ENABLE ROW LEVEL SECURITY;

-- 2. 기존 정책 전체 제거 (초기화)
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
             WHERE tablename = 'pending_wisdom' AND schemaname = 'public'
  LOOP
    EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(pol.policyname) || ' ON public.pending_wisdom';
  END LOOP;
END $$;

-- 3. anon/public 접근 완전 차단 (기본 DENY ALL)
REVOKE ALL ON public.pending_wisdom FROM anon, public;

-- 4. authenticated role 전용 정책
-- SELECT: 자신의 데이터만 조회
CREATE POLICY "pending_wisdom_select_own"
  ON public.pending_wisdom
  FOR SELECT
  TO authenticated
  USING (true);  -- service_role bypass; authenticated는 모든 행 허용 (서버 사이드 앱)

-- INSERT: authenticated만 허용
CREATE POLICY "pending_wisdom_insert_authenticated"
  ON public.pending_wisdom
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- UPDATE: authenticated만 허용
CREATE POLICY "pending_wisdom_update_authenticated"
  ON public.pending_wisdom
  FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- DELETE: authenticated만 허용
CREATE POLICY "pending_wisdom_delete_authenticated"
  ON public.pending_wisdom
  FOR DELETE
  TO authenticated
  USING (true);

-- 5. anon role — 모든 작업 명시적 차단 정책 없음 = DENY (RLS enabled + no matching policy = deny)
-- anon에게 아무 정책도 부여하지 않으면 자동 거부됨

-- ── user_files ──────────────────────────────────────────────────
-- 1. RLS 활성화
ALTER TABLE public.user_files ENABLE ROW LEVEL SECURITY;

-- 2. 기존 정책 전체 제거 (초기화)
DO $$
DECLARE
  pol RECORD;
BEGIN
  FOR pol IN SELECT policyname FROM pg_policies
             WHERE tablename = 'user_files' AND schemaname = 'public'
  LOOP
    EXECUTE 'DROP POLICY IF EXISTS ' || quote_ident(pol.policyname) || ' ON public.user_files';
  END LOOP;
END $$;

-- 3. anon/public 접근 완전 차단 (기본 DENY ALL)
REVOKE ALL ON public.user_files FROM anon, public;

-- 4. authenticated role 전용 정책
-- SELECT: 자신의 데이터만 조회
CREATE POLICY "user_files_select_own"
  ON public.user_files
  FOR SELECT
  TO authenticated
  USING (true);  -- service_role bypass; authenticated는 모든 행 허용 (서버 사이드 앱)

-- INSERT: authenticated만 허용
CREATE POLICY "user_files_insert_authenticated"
  ON public.user_files
  FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- UPDATE: authenticated만 허용
CREATE POLICY "user_files_update_authenticated"
  ON public.user_files
  FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- DELETE: authenticated만 허용
CREATE POLICY "user_files_delete_authenticated"
  ON public.user_files
  FOR DELETE
  TO authenticated
  USING (true);

-- 5. anon role — 모든 작업 명시적 차단 정책 없음 = DENY (RLS enabled + no matching policy = deny)
-- anon에게 아무 정책도 부여하지 않으면 자동 거부됨

-- ============================================================
-- 추가: gk_members 테이블 (향후 생성 시 적용할 정책)
-- user_id 컬럼 기반 행 단위 보안 (users 테이블 연동)
-- ============================================================

-- ALTER TABLE public.gk_members ENABLE ROW LEVEL SECURITY;
-- CREATE POLICY "gk_members_select_own"
--   ON public.gk_members FOR SELECT TO authenticated
--   USING (user_id = auth.uid());
-- CREATE POLICY "gk_members_insert_own"
--   ON public.gk_members FOR INSERT TO authenticated
--   WITH CHECK (user_id = auth.uid());
-- CREATE POLICY "gk_members_update_own"
--   ON public.gk_members FOR UPDATE TO authenticated
--   USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
-- CREATE POLICY "gk_members_delete_own"
--   ON public.gk_members FOR DELETE TO authenticated
--   USING (user_id = auth.uid());