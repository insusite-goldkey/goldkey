-- ============================================================
-- 골드키 CRM 데이터 요새 스키마 (GP 제정)
-- 설계 원칙: 인물 1회 등록 / 증권-인물 N:M / Soft Delete
-- Supabase SQL Editor에서 순서대로 실행하세요.
-- ============================================================

-- ──────────────────────────────────────────────────────────
-- 1. [people] 모든 인적 자원의 본부
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_people (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    birth_date      TEXT,                       -- YYYYMMDD 형식
    gender          TEXT CHECK (gender IN ('남', '여', '기타')),
    contact         TEXT,                       -- 암호화 저장 권장
    is_real_client  BOOLEAN NOT NULL DEFAULT FALSE,
    agent_id        TEXT,                       -- 담당 FC (gk_members.user_id)
    memo            TEXT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_people_name       ON gk_people(name);
CREATE INDEX IF NOT EXISTS idx_gk_people_agent_id   ON gk_people(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_people_is_deleted ON gk_people(is_deleted);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION public.gk_set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$;

DROP TRIGGER IF EXISTS trg_gk_people_updated_at ON gk_people;
CREATE TRIGGER trg_gk_people_updated_at
    BEFORE UPDATE ON gk_people
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();


-- ──────────────────────────────────────────────────────────
-- 2. [relationships] 인맥 및 가족 지도
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_relationships (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_person_id  UUID NOT NULL REFERENCES gk_people(id) ON DELETE RESTRICT,
    to_person_id    UUID NOT NULL REFERENCES gk_people(id) ON DELETE RESTRICT,
    relation_type   TEXT NOT NULL
                    CHECK (relation_type IN (
                        '배우자','자녀','부모','형제','소개자','법인직원','기타'
                    )),
    agent_id        TEXT,
    memo            TEXT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gk_relationship UNIQUE (from_person_id, to_person_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_gk_rel_from ON gk_relationships(from_person_id);
CREATE INDEX IF NOT EXISTS idx_gk_rel_to   ON gk_relationships(to_person_id);


-- ──────────────────────────────────────────────────────────
-- 3. [policies] 보험 증권의 몸체
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_policies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_number       TEXT,                   -- 증권번호
    insurance_company   TEXT,                   -- 보험사명
    product_name        TEXT,                   -- 상품명
    product_type        TEXT,                   -- 생명/손해/실손/연금 등
    contract_date       TEXT,                   -- YYYYMMDD
    expiry_date         TEXT,                   -- 만기일 YYYYMMDD
    premium             NUMERIC(15, 2),         -- 월 보험료
    payment_period      TEXT,                   -- 납입기간 (예: 20년납)
    coverage_period     TEXT,                   -- 보장기간 (예: 100세)
    raw_text            TEXT,                   -- OCR/크롤링 원문 전체
    source              TEXT DEFAULT 'manual'  -- 'manual','ocr','crawl'
                        CHECK (source IN ('manual','ocr','crawl')),
    agent_id            TEXT,
    is_deleted          BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_policies_policy_number ON gk_policies(policy_number);
CREATE INDEX IF NOT EXISTS idx_gk_policies_agent_id      ON gk_policies(agent_id);

DROP TRIGGER IF EXISTS trg_gk_policies_updated_at ON gk_policies;
CREATE TRIGGER trg_gk_policies_updated_at
    BEFORE UPDATE ON gk_policies
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();


-- ──────────────────────────────────────────────────────────
-- 4. [policy_roles] 증권-인물 N:M 연결 핵심 테이블
--    피보험자 수 제한 없음 — role 별 복수 연결 가능
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_policy_roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id   UUID NOT NULL REFERENCES gk_policies(id) ON DELETE RESTRICT,
    person_id   UUID NOT NULL REFERENCES gk_people(id)   ON DELETE RESTRICT,
    role        TEXT NOT NULL
                CHECK (role IN ('계약자','피보험자','수익자')),
    agent_id    TEXT,
    memo        TEXT,
    is_deleted  BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_gk_policy_role UNIQUE (policy_id, person_id, role)
);

CREATE INDEX IF NOT EXISTS idx_gk_pr_policy_id ON gk_policy_roles(policy_id);
CREATE INDEX IF NOT EXISTS idx_gk_pr_person_id ON gk_policy_roles(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_pr_role      ON gk_policy_roles(role);


-- ──────────────────────────────────────────────────────────
-- 5. [policy_coverages] 보장 항목 상세 (스캔/OCR 결과 저장)
-- ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gk_policy_coverages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id       UUID NOT NULL REFERENCES gk_policies(id) ON DELETE RESTRICT,
    coverage_name   TEXT NOT NULL,              -- 담보명
    coverage_amount NUMERIC(20, 0),             -- 보장금액 (원)
    deductible      NUMERIC(20, 0),             -- 자기부담금
    coverage_period TEXT,                       -- 보장기간
    is_active       BOOLEAN DEFAULT TRUE,
    agent_id        TEXT,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_cov_policy_id ON gk_policy_coverages(policy_id);


-- ──────────────────────────────────────────────────────────
-- 6. RLS(Row Level Security) — agent_id 기준 데이터 격리
--    (서비스 롤 키 사용 시 bypass 가능)
-- ──────────────────────────────────────────────────────────
ALTER TABLE gk_people           ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_relationships    ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_policies         ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_policy_roles     ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_policy_coverages ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 모든 행 접근 허용 (앱 서버용) — PG15 호환 재생성 패턴
DROP POLICY IF EXISTS "service_role_all_people"   ON public.gk_people;
DROP POLICY IF EXISTS "service_role_all_rel"       ON public.gk_relationships;
DROP POLICY IF EXISTS "service_role_all_policies"  ON public.gk_policies;
DROP POLICY IF EXISTS "service_role_all_pr"        ON public.gk_policy_roles;
DROP POLICY IF EXISTS "service_role_all_cov"       ON public.gk_policy_coverages;

CREATE POLICY "service_role_all_people"
    ON public.gk_people FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_rel"
    ON public.gk_relationships FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_policies"
    ON public.gk_policies FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_pr"
    ON public.gk_policy_roles FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_cov"
    ON public.gk_policy_coverages FOR ALL TO service_role USING (true) WITH CHECK (true);
