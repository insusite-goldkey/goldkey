-- ================================================================
-- GoldKey CRM 영구 저장 테이블 마이그레이션
-- Supabase > SQL Editor 에서 아래 전체를 복사하여 실행하세요.
-- (CREATE TABLE IF NOT EXISTS — 중복 실행 안전)
-- ================================================================

-- ================================================================
-- §1 gk_crm_clients — 레거시 CRM 클라이언트 캐시 (gk_people 보조)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_crm_clients (
    id           BIGSERIAL PRIMARY KEY,
    agent_uid    TEXT        NOT NULL,
    client_name  TEXT        NOT NULL,
    profile      JSONB       NOT NULL DEFAULT '{}',
    analyses     JSONB       NOT NULL DEFAULT '[]',
    registered   BOOLEAN     NOT NULL DEFAULT false,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_agent_client UNIQUE (agent_uid, client_name)
);

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

CREATE INDEX IF NOT EXISTS idx_crm_agent_uid ON public.gk_crm_clients (agent_uid);
CREATE INDEX IF NOT EXISTS idx_crm_updated   ON public.gk_crm_clients (updated_at DESC);

ALTER TABLE public.gk_crm_clients ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS crm_service_only ON public.gk_crm_clients;
CREATE POLICY crm_service_only ON public.gk_crm_clients USING (false);

-- ================================================================
-- §15 gk_unified_reports — Cloud Run 통합 AI 보고서 캐시
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_unified_reports (
    id          BIGSERIAL   PRIMARY KEY,
    person_id   TEXT        NOT NULL,
    agent_id    TEXT        NOT NULL,
    sections    JSONB       NOT NULL DEFAULT '{}',
    version     INTEGER     NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_id     TEXT,
    CONSTRAINT uq_unified_report UNIQUE (agent_id, person_id)
);
CREATE INDEX IF NOT EXISTS idx_unirep_agent  ON public.gk_unified_reports (agent_id);
CREATE INDEX IF NOT EXISTS idx_unirep_person ON public.gk_unified_reports (person_id);
ALTER TABLE public.gk_unified_reports ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS unirep_service_only ON public.gk_unified_reports;
CREATE POLICY unirep_service_only ON public.gk_unified_reports USING (false);

-- ================================================================
-- §15b gk_handoff_sessions — QR/링크 고객 인증 세션
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_handoff_sessions (
    session_id              TEXT        PRIMARY KEY,
    user_id                 TEXT        NOT NULL,
    person_id               TEXT        NOT NULL,
    channel                 TEXT        NOT NULL DEFAULT 'qr',
    status                  TEXT        NOT NULL DEFAULT 'pending',
    consent_info_lookup     BOOLEAN     NOT NULL DEFAULT false,
    consent_kakao_report    BOOLEAN     NOT NULL DEFAULT false,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_handoff_user   ON public.gk_handoff_sessions (user_id);
CREATE INDEX IF NOT EXISTS idx_handoff_person ON public.gk_handoff_sessions (person_id);
ALTER TABLE public.gk_handoff_sessions ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS handoff_service_only ON public.gk_handoff_sessions;
CREATE POLICY handoff_service_only ON public.gk_handoff_sessions USING (false);

-- ================================================================
-- §15c gk_consents — 고객 동의 영구 원장
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_consents (
    id                      BIGSERIAL   PRIMARY KEY,
    user_id                 TEXT        NOT NULL,
    person_id               TEXT        NOT NULL,
    consent_info_lookup     BOOLEAN     NOT NULL DEFAULT false,
    consent_kakao_report    BOOLEAN     NOT NULL DEFAULT false,
    source_session_id       TEXT        DEFAULT '',
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_consent UNIQUE (user_id, person_id)
);
CREATE INDEX IF NOT EXISTS idx_consent_user   ON public.gk_consents (user_id);
CREATE INDEX IF NOT EXISTS idx_consent_person ON public.gk_consents (person_id);
ALTER TABLE public.gk_consents ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS consent_service_only ON public.gk_consents;
CREATE POLICY consent_service_only ON public.gk_consents USING (false);

-- ================================================================
-- §17 gk_consultation_contexts — CRM → HQ 컨텍스트 이전 (Context Transfer)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_consultation_contexts (
    context_id   TEXT        PRIMARY KEY,
    person_id    TEXT        NOT NULL,
    agent_id     TEXT        NOT NULL,
    context_data TEXT        NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at   TIMESTAMPTZ NOT NULL DEFAULT (now() + INTERVAL '24 hours')
);
CREATE INDEX IF NOT EXISTS idx_ctx_agent   ON public.gk_consultation_contexts (agent_id);
CREATE INDEX IF NOT EXISTS idx_ctx_person  ON public.gk_consultation_contexts (person_id);
CREATE INDEX IF NOT EXISTS idx_ctx_expires ON public.gk_consultation_contexts (expires_at);
ALTER TABLE public.gk_consultation_contexts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ctx_service_only ON public.gk_consultation_contexts;
CREATE POLICY ctx_service_only ON public.gk_consultation_contexts USING (false);

-- 만료 컨텍스트 자동 삭제 (pg_cron 활성화 환경에서만)
-- SELECT cron.schedule('0 * * * *', $$DELETE FROM gk_consultation_contexts WHERE expires_at < now()$$);

-- ================================================================
-- §18 gk_people.last_device_id 컬럼 추가 (멀티디바이스 머지)
-- ================================================================
ALTER TABLE public.gk_people ADD COLUMN IF NOT EXISTS last_device_id TEXT DEFAULT '';

-- ================================================================
-- §19 gk_insurance_contracts — 보험 가입 관리 3파트 파이프라인
--   part: 'A'(설계사 취급계약) | 'B'(타부점 계약) | 'C'(해지/승환)
-- ================================================================
CREATE TABLE IF NOT EXISTS public.gk_insurance_contracts (
    id               TEXT        PRIMARY KEY,
    agent_id         TEXT        NOT NULL,
    person_id        TEXT        NOT NULL,
    part             TEXT        NOT NULL DEFAULT 'A'
                                 CHECK (part IN ('A','B','C')),
    policyholder     TEXT        NOT NULL DEFAULT '',
    insured          TEXT        NOT NULL DEFAULT '',
    insurer          TEXT        NOT NULL DEFAULT '',
    product_name     TEXT        NOT NULL DEFAULT '',
    policy_no        TEXT        NOT NULL DEFAULT '',
    contract_ym      TEXT        NOT NULL DEFAULT '',
    expiry_ym        TEXT        NOT NULL DEFAULT '',
    monthly_premium  TEXT        NOT NULL DEFAULT '',
    memo             TEXT        NOT NULL DEFAULT '',
    terminated_at    TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ic_agent  ON public.gk_insurance_contracts (agent_id);
CREATE INDEX IF NOT EXISTS idx_ic_person ON public.gk_insurance_contracts (person_id);
CREATE INDEX IF NOT EXISTS idx_ic_part   ON public.gk_insurance_contracts (agent_id, person_id, part);
ALTER TABLE public.gk_insurance_contracts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ic_service_only ON public.gk_insurance_contracts;
CREATE POLICY ic_service_only ON public.gk_insurance_contracts USING (false);

-- ================================================================
-- 확인 쿼리 (실행 후 테이블 정상 생성 여부 검증)
-- ================================================================
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN (
    'gk_crm_clients', 'gk_unified_reports',
    'gk_handoff_sessions', 'gk_consents',
    'gk_consultation_contexts', 'gk_people', 'gk_insurance_contracts'
)
ORDER BY table_name, ordinal_position;