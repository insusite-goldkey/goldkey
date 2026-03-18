-- ============================================================
-- Supabase Security Advisor 보안 취약점 수정 스크립트
-- 프로젝트: goldkey (idfzizqidhnpzbqioqqo)
-- 작성일: 2026-03-18  |  Security Advisor 5개 오류 해결
-- ============================================================
-- ▶ Supabase SQL Editor에서 전체 복사 후 [Run] 실행
-- ============================================================


-- ──────────────────────────────────────────────────────────
-- STEP 1. gk_set_updated_at 함수 — search_path 고정
--   오류 유형: function_search_path_mutable
--   원인: 함수 내 search_path 미설정 → SQL injection 위험
-- ──────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.gk_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;


-- ──────────────────────────────────────────────────────────
-- STEP 2. RLS 강제 활성화
--   오류 유형: rls_disabled_in_public (5개 테이블 전체)
--   이미 활성화된 경우에도 무해하게 재실행됨
-- ──────────────────────────────────────────────────────────
ALTER TABLE public.gk_people           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_relationships    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policies         ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policy_roles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policy_coverages ENABLE ROW LEVEL SECURITY;


-- ──────────────────────────────────────────────────────────
-- STEP 3. 기존 정책 삭제 후 재생성 (PG15 호환 방식)
--   원인: CREATE POLICY IF NOT EXISTS 는 PG17 전용 문법.
--         PG15 Supabase 환경에서 정책이 실제로 생성되지 않았음.
--   해결: DROP IF EXISTS → CREATE 순서로 안전하게 재생성
-- ──────────────────────────────────────────────────────────

-- [gk_people]
DROP POLICY IF EXISTS "service_role_all_people" ON public.gk_people;
CREATE POLICY "service_role_all_people"
    ON public.gk_people
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- [gk_relationships]
DROP POLICY IF EXISTS "service_role_all_rel" ON public.gk_relationships;
CREATE POLICY "service_role_all_rel"
    ON public.gk_relationships
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- [gk_policies]
DROP POLICY IF EXISTS "service_role_all_policies" ON public.gk_policies;
CREATE POLICY "service_role_all_policies"
    ON public.gk_policies
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- [gk_policy_roles]
DROP POLICY IF EXISTS "service_role_all_pr" ON public.gk_policy_roles;
CREATE POLICY "service_role_all_pr"
    ON public.gk_policy_roles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- [gk_policy_coverages]
DROP POLICY IF EXISTS "service_role_all_cov" ON public.gk_policy_coverages;
CREATE POLICY "service_role_all_cov"
    ON public.gk_policy_coverages
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- ──────────────────────────────────────────────────────────
-- STEP 4. 결과 검증 쿼리 (실행 후 아래로 확인)
-- ──────────────────────────────────────────────────────────
SELECT
    schemaname,
    tablename,
    rowsecurity AS rls_enabled,
    (SELECT COUNT(*) FROM pg_policies p
     WHERE p.schemaname = c.schemaname
       AND p.tablename  = c.tablename) AS policy_count
FROM pg_tables c
WHERE schemaname = 'public'
  AND tablename LIKE 'gk_%'
ORDER BY tablename;
-- 기대값: rls_enabled = true, policy_count >= 1 (5개 테이블 모두)

SELECT routine_name, security_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'gk_set_updated_at';
-- 기대값: security_type = INVOKER
