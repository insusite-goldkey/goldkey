-- ================================================================
-- GoldKey CRM 영구 저장 테이블 마이그레이션
-- Supabase > SQL Editor 에서 아래 전체를 복사하여 실행하세요.
-- ================================================================

CREATE TABLE IF NOT EXISTS public.gk_crm_clients (
    id           BIGSERIAL PRIMARY KEY,
    agent_uid    TEXT        NOT NULL,           -- 설계사 user_id
    client_name  TEXT        NOT NULL,           -- 고객 이름
    profile      JSONB       NOT NULL DEFAULT '{}',  -- 프로필 전체
    analyses     JSONB       NOT NULL DEFAULT '[]',  -- 분석 이력
    registered   BOOLEAN     NOT NULL DEFAULT false, -- 등록고객 여부
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_agent_client UNIQUE (agent_uid, client_name)
);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_crm_updated_at ON public.gk_crm_clients;
CREATE TRIGGER trg_crm_updated_at
    BEFORE UPDATE ON public.gk_crm_clients
    FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();

-- 인덱스 (설계사별 조회 성능)
CREATE INDEX IF NOT EXISTS idx_crm_agent_uid ON public.gk_crm_clients (agent_uid);
CREATE INDEX IF NOT EXISTS idx_crm_updated   ON public.gk_crm_clients (updated_at DESC);

-- Row Level Security (설계사 본인 데이터만 접근)
ALTER TABLE public.gk_crm_clients ENABLE ROW LEVEL SECURITY;

-- service_role 키는 RLS 우회 → 앱에서 service_role 키 사용 시 별도 정책 불필요
-- anon/authenticated 직접 접근 차단 (서버사이드 service_role만 허용)
DROP POLICY IF EXISTS crm_service_only ON public.gk_crm_clients;
CREATE POLICY crm_service_only ON public.gk_crm_clients
    USING (false);   -- anon/authenticated 직접 접근 전면 차단

-- ================================================================
-- 확인 쿼리 (실행 후 테이블 정상 생성 여부 검증)
-- ================================================================
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'gk_crm_clients'
ORDER BY ordinal_position;
