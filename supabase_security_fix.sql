-- ============================================================
-- Goldkey AI Masters 2026 — 완전한 테넌트 데이터 격리(RLS) 스크립트
-- 프로젝트: goldkey (idfzizqidhnpzbqioqqo)
-- 버전: v2.0 | 2026-03-20 | 전체 gk_* 테이블 격리 강화
-- ============================================================
-- ▶ Supabase SQL Editor에서 전체 복사 후 [Run] 실행
-- ============================================================
--
-- [아키텍처 원칙]
-- 앱(HQ/CRM)은 SUPABASE_SERVICE_ROLE_KEY 로 접근 → RLS 바이패스 (정상)
-- 앱 레이어에서 agent_id 필터를 직접 강제 (db_utils.py 참조)
-- RLS 정책 = 2차 방어선:
--   ① Supabase Dashboard 직접 쿼리 차단
--   ② 외부 anon/authenticated 키 접근 차단
--   ③ 향후 JWT 인증 방식 도입 시 즉시 활성화 가능한 기반 제공
-- ============================================================


-- ──────────────────────────────────────────────────────────
-- STEP 1. gk_set_updated_at 함수 — search_path 고정
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
-- STEP 2. 전체 gk_* 업무 테이블 RLS 활성화
-- ──────────────────────────────────────────────────────────
ALTER TABLE public.gk_people              ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_relationships       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policies            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policy_roles        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_policy_coverages    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_schedules           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_members             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_crawl_status        ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_consulting_logs     ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_customer_docs       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_ai_briefs           ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_feedback_log        ENABLE ROW LEVEL SECURITY;
-- 디바이스·방문자 기록 (user_name/fp_id 기반)
ALTER TABLE public.gk_device_history      ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_guest_visits        ENABLE ROW LEVEL SECURITY;
-- RAG 지식베이스 (공용 — 별도 정책 부여)
ALTER TABLE public.gk_policy_terms_qa     ENABLE ROW LEVEL SECURITY;


-- ──────────────────────────────────────────────────────────
-- STEP 3. service_role 전용 전체 접근 정책
--   앱 서버(service_role_key)만 모든 데이터에 접근 가능.
--   authenticated/anon 은 아래 정책이 없으므로 기본 DENY.
-- ──────────────────────────────────────────────────────────

-- [gk_people] 고객 마스터
DROP POLICY IF EXISTS "service_role_all_people" ON public.gk_people;
CREATE POLICY "service_role_all_people"
    ON public.gk_people FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_relationships] 관계망
DROP POLICY IF EXISTS "service_role_all_rel" ON public.gk_relationships;
CREATE POLICY "service_role_all_rel"
    ON public.gk_relationships FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_policies] 보험증권
DROP POLICY IF EXISTS "service_role_all_policies" ON public.gk_policies;
CREATE POLICY "service_role_all_policies"
    ON public.gk_policies FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_policy_roles] 증권-인물 역할
DROP POLICY IF EXISTS "service_role_all_pr" ON public.gk_policy_roles;
CREATE POLICY "service_role_all_pr"
    ON public.gk_policy_roles FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_policy_coverages] 담보 상세
DROP POLICY IF EXISTS "service_role_all_cov" ON public.gk_policy_coverages;
CREATE POLICY "service_role_all_cov"
    ON public.gk_policy_coverages FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_schedules] 일정
DROP POLICY IF EXISTS "service_role_all_schedules" ON public.gk_schedules;
CREATE POLICY "service_role_all_schedules"
    ON public.gk_schedules FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_members] 설계사 회원
DROP POLICY IF EXISTS "service_role_all_members" ON public.gk_members;
CREATE POLICY "service_role_all_members"
    ON public.gk_members FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_crawl_status] 크롤링 상태 파이프라인
DROP POLICY IF EXISTS "service_role_all_crawl" ON public.gk_crawl_status;
CREATE POLICY "service_role_all_crawl"
    ON public.gk_crawl_status FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_consulting_logs] 상담일지
DROP POLICY IF EXISTS "service_role_all_logs" ON public.gk_consulting_logs;
CREATE POLICY "service_role_all_logs"
    ON public.gk_consulting_logs FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_customer_docs] 고객 문서 메타
DROP POLICY IF EXISTS "service_role_all_docs" ON public.gk_customer_docs;
CREATE POLICY "service_role_all_docs"
    ON public.gk_customer_docs FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_ai_briefs] AI 브리핑 저장
DROP POLICY IF EXISTS "service_role_all_briefs" ON public.gk_ai_briefs;
CREATE POLICY "service_role_all_briefs"
    ON public.gk_ai_briefs FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [ai_feedback_log] 컴플라이언스 피드백
DROP POLICY IF EXISTS "service_role_all_fb" ON public.ai_feedback_log;
CREATE POLICY "service_role_all_fb"
    ON public.ai_feedback_log FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_device_history] 디바이스 이력
DROP POLICY IF EXISTS "service_role_all_dev" ON public.gk_device_history;
CREATE POLICY "service_role_all_dev"
    ON public.gk_device_history FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- [gk_guest_visits] 게스트 방문 기록
DROP POLICY IF EXISTS "service_role_all_guest" ON public.gk_guest_visits;
CREATE POLICY "service_role_all_guest"
    ON public.gk_guest_visits FOR ALL TO service_role
    USING (true) WITH CHECK (true);


-- ──────────────────────────────────────────────────────────
-- STEP 4. RAG 지식베이스 — authenticated 읽기 허용
--   gk_policy_terms_qa 는 약관 청크(공용 지식). 쓰기는 service_role만.
-- ──────────────────────────────────────────────────────────
DROP POLICY IF EXISTS "service_role_all_rag" ON public.gk_policy_terms_qa;
CREATE POLICY "service_role_all_rag"
    ON public.gk_policy_terms_qa FOR ALL TO service_role
    USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "authenticated_read_rag" ON public.gk_policy_terms_qa;
CREATE POLICY "authenticated_read_rag"
    ON public.gk_policy_terms_qa FOR SELECT TO authenticated
    USING (true);


-- ──────────────────────────────────────────────────────────
-- STEP 5. 추가 보안 — 설계사 본인 행만 접근 가능 정책
--   향후 Supabase Auth(JWT) 도입 시 활성화용 준비 정책.
--   현재는 service_role 정책이 우선 적용됨.
--   활성화 방법: anon/authenticated 키로 접근하는 클라이언트가 생기면
--               아래 COMMENTED 섹션의 주석을 제거하고 재실행.
-- ──────────────────────────────────────────────────────────
-- [미래 활성화 예시 — 현재 비활성]
-- CREATE POLICY "tenant_isolation_people"
--     ON public.gk_people FOR ALL TO authenticated
--     USING (agent_id = current_setting('app.current_agent_id', true))
--     WITH CHECK (agent_id = current_setting('app.current_agent_id', true));
--
-- CREATE POLICY "tenant_isolation_schedules"
--     ON public.gk_schedules FOR ALL TO authenticated
--     USING (agent_id = current_setting('app.current_agent_id', true))
--     WITH CHECK (agent_id = current_setting('app.current_agent_id', true));


-- ──────────────────────────────────────────────────────────
-- STEP 6. 결과 검증 쿼리
-- ──────────────────────────────────────────────────────────
SELECT
    t.tablename,
    t.rowsecurity                          AS rls_on,
    COUNT(p.policyname)                    AS policy_count,
    STRING_AGG(p.policyname, ', ')         AS policies
FROM pg_tables t
LEFT JOIN pg_policies p
    ON  p.schemaname = t.schemaname
    AND p.tablename  = t.tablename
WHERE t.schemaname = 'public'
  AND t.tablename  LIKE 'gk_%'
   OR t.tablename  = 'ai_feedback_log'
GROUP BY t.tablename, t.rowsecurity
ORDER BY t.tablename;
-- 기대값: rls_on = true, policy_count >= 1 (전 테이블)

SELECT routine_name, security_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'gk_set_updated_at';
-- 기대값: security_type = INVOKER
