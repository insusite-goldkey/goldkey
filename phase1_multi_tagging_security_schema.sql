-- ============================================================
-- [GP-PHASE1] 다중 관계망 태깅 및 철통 보안 구축
-- 작성일: 2026-03-28
-- 목적: 8가지 관계 태그 + 보험계약 이력 + 이중화 백업
-- ============================================================

-- ══════════════════════════════════════════════════════════════════════════════
-- §1. gk_people_backup — 이중화 백업 테이블 (정보보호법 준수)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_people_backup (
    backup_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL,                      -- 원본 gk_people.id
    name            TEXT NOT NULL,                       -- Fernet 암호화 필수
    birth_date      TEXT,                                -- YYYYMMDD
    gender          TEXT,
    contact         TEXT,                                -- Fernet 암호화 필수
    address         TEXT,                                -- Fernet 암호화 필수
    job             TEXT,
    injury_level    INT,
    is_real_client  BOOLEAN DEFAULT FALSE,
    agent_id        TEXT,
    memo            TEXT,
    status          TEXT,
    is_favorite     BOOLEAN,
    -- 1차 라인: 연간 계약 관리
    auto_renewal_month INT,
    fire_renewal_month INT,
    last_auto_carrier  TEXT,
    -- 2차 라인: 핵심 케어
    management_tier    INT,
    wedding_anniversary TEXT,
    driving_status     TEXT,
    risk_note          TEXT,
    -- 3차 라인: 인맥 & 생활
    lead_source        TEXT,
    referrer_id        TEXT,
    referrer_relation  TEXT,
    community_tags     TEXT[],
    prospecting_stage  TEXT,
    -- 백업 메타데이터
    is_deleted      BOOLEAN DEFAULT FALSE,
    original_created_at TIMESTAMPTZ,                    -- 원본 생성일
    original_updated_at TIMESTAMPTZ,                    -- 원본 수정일
    backup_created_at   TIMESTAMPTZ DEFAULT NOW(),      -- 백업 생성일
    backup_reason       TEXT DEFAULT 'auto_mirror'      -- 'auto_mirror' | 'manual_backup'
);

CREATE INDEX IF NOT EXISTS idx_gk_people_backup_person_id ON gk_people_backup(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_people_backup_agent_id  ON gk_people_backup(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_people_backup_created   ON gk_people_backup(backup_created_at DESC);

COMMENT ON TABLE gk_people_backup IS '[GP-SEC] 고객 정보 이중화 백업 테이블 — 물리적 데이터 손실 방지';


-- ══════════════════════════════════════════════════════════════════════════════
-- §2. gk_relationship_tags — 8가지 다중 관계망 태깅 시스템
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_relationship_tags (
    tag_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL,                      -- 태그 대상 고객 (gk_people.id FK)
    agent_id        TEXT NOT NULL,                      -- 담당 설계사
    tag_type        TEXT NOT NULL CHECK (tag_type IN (
                        '상담자',      -- (1) 상담 진행 중인 고객
                        '계약자',      -- (2) 보험 계약자
                        '피보험자',    -- (3) 보험 피보험자
                        '가족',        -- (4) 가족 관계
                        '소개자',      -- (5) 고객 소개자
                        '동일법인',    -- (6) 같은 법인 소속
                        '동일단체',    -- (7) 같은 단체 소속
                        '친인척'       -- (8) 친인척 관계
                    )),
    related_person_id UUID,                             -- 관계 대상 (상대방 person_id, NULL 가능)
    memo            TEXT,                                -- 관계 상세 메모
    is_active       BOOLEAN DEFAULT TRUE,                -- 활성 태그 여부
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_relationship_tag UNIQUE (person_id, tag_type, related_person_id)
);

CREATE INDEX IF NOT EXISTS idx_gk_rel_tags_person_id ON gk_relationship_tags(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_rel_tags_agent_id  ON gk_relationship_tags(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_rel_tags_type      ON gk_relationship_tags(tag_type);
CREATE INDEX IF NOT EXISTS idx_gk_rel_tags_related   ON gk_relationship_tags(related_person_id);

COMMENT ON TABLE gk_relationship_tags IS '[GP-PHASE1] 8가지 다중 관계망 태깅 시스템';


-- ══════════════════════════════════════════════════════════════════════════════
-- §3. gk_insurance_contracts_detail — 보험계약 상세 이력 (자사 + 타부점 + 해지)
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_insurance_contracts_detail (
    contract_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL,                      -- 고객 (gk_people.id FK)
    agent_id        TEXT NOT NULL,                      -- 담당 설계사
    contract_status TEXT NOT NULL CHECK (contract_status IN (
                        '자사계약',    -- 본인이 관리하는 계약
                        '타부점계약',  -- 다른 부점/타사 계약
                        '해지계약'     -- 해지된 계약
                    )),
    -- 보험 기본 정보
    insurance_company TEXT,                             -- 보험회사
    product_name      TEXT,                             -- 보험상품명
    contract_date     TEXT,                             -- 계약년월 (YYYYMM)
    contractor_name   TEXT,                             -- 계약자명 (Fernet 암호화 권장)
    insured_name      TEXT,                             -- 피보험자명 (Fernet 암호화 권장)
    monthly_premium   NUMERIC(15, 2),                   -- 월납입보험료
    key_point         TEXT,                             -- 비고 (주요 핵심 포인트)
    -- 해지 정보
    termination_date  TEXT,                             -- 해지일 (YYYYMMDD)
    termination_reason TEXT,                            -- 해지 사유
    -- 메타데이터
    is_deleted      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_ins_detail_person_id ON gk_insurance_contracts_detail(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_ins_detail_agent_id  ON gk_insurance_contracts_detail(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_ins_detail_status    ON gk_insurance_contracts_detail(contract_status);
CREATE INDEX IF NOT EXISTS idx_gk_ins_detail_company   ON gk_insurance_contracts_detail(insurance_company);

COMMENT ON TABLE gk_insurance_contracts_detail IS '[GP-PHASE1] 보험계약 상세 이력 — 자사/타부점/해지 분류';


-- ══════════════════════════════════════════════════════════════════════════════
-- §4. gk_consultation_schedule — 상담 일정 및 내용 태깅
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_consultation_schedule (
    consultation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL,                      -- 고객 (gk_people.id FK)
    agent_id        TEXT NOT NULL,                      -- 담당 설계사
    schedule_date   TEXT,                                -- 상담 예정일 (YYYYMMDD)
    schedule_time   TEXT,                                -- 상담 시간 (HHMM)
    consultation_type TEXT CHECK (consultation_type IN (
                        '초회상담',
                        '보장분석',
                        '증권점검',
                        '계약체결',
                        '사후관리',
                        '기타'
                    )),
    consultation_content TEXT,                          -- 상담 내용 요약
    consultation_result  TEXT,                          -- 상담 결과 (계약 성사 여부 등)
    next_action          TEXT,                          -- 다음 액션 아이템
    is_completed    BOOLEAN DEFAULT FALSE,               -- 상담 완료 여부
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_consult_person_id ON gk_consultation_schedule(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_consult_agent_id  ON gk_consultation_schedule(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_consult_date      ON gk_consultation_schedule(schedule_date);
CREATE INDEX IF NOT EXISTS idx_gk_consult_completed ON gk_consultation_schedule(is_completed);

COMMENT ON TABLE gk_consultation_schedule IS '[GP-PHASE1] 상담 일정 및 내용 태깅';


-- ══════════════════════════════════════════════════════════════════════════════
-- §5. 자동 이중화 트리거 — gk_people INSERT/UPDATE 시 gk_people_backup 자동 미러링
-- ══════════════════════════════════════════════════════════════════════════════
CREATE OR REPLACE FUNCTION public.gk_people_auto_backup()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
BEGIN
    -- INSERT 또는 UPDATE 시 백업 테이블에 자동 저장
    INSERT INTO public.gk_people_backup (
        person_id, name, birth_date, gender, contact, address, job, injury_level,
        is_real_client, agent_id, memo, status, is_favorite,
        auto_renewal_month, fire_renewal_month, last_auto_carrier,
        management_tier, wedding_anniversary, driving_status, risk_note,
        lead_source, referrer_id, referrer_relation, community_tags, prospecting_stage,
        is_deleted, original_created_at, original_updated_at, backup_reason
    ) VALUES (
        NEW.person_id, NEW.name, NEW.birth_date, NEW.gender, NEW.contact, NEW.address, NEW.job, NEW.injury_level,
        NEW.is_real_client, NEW.agent_id, NEW.memo, NEW.status, NEW.is_favorite,
        NEW.auto_renewal_month, NEW.fire_renewal_month, NEW.last_auto_carrier,
        NEW.management_tier, NEW.wedding_anniversary, NEW.driving_status, NEW.risk_note,
        NEW.lead_source, NEW.referrer_id, NEW.referrer_relation, NEW.community_tags, NEW.prospecting_stage,
        NEW.is_deleted, NEW.created_at, NEW.updated_at, 'auto_mirror'
    );
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_gk_people_auto_backup ON gk_people;
CREATE TRIGGER trg_gk_people_auto_backup
    AFTER INSERT OR UPDATE ON gk_people
    FOR EACH ROW EXECUTE FUNCTION gk_people_auto_backup();

COMMENT ON FUNCTION gk_people_auto_backup IS '[GP-SEC] gk_people 자동 이중화 백업 트리거';


-- ══════════════════════════════════════════════════════════════════════════════
-- §6. updated_at 자동 갱신 트리거 (신규 테이블용)
-- ══════════════════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS trg_gk_rel_tags_updated_at ON gk_relationship_tags;
CREATE TRIGGER trg_gk_rel_tags_updated_at
    BEFORE UPDATE ON gk_relationship_tags
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

DROP TRIGGER IF EXISTS trg_gk_ins_detail_updated_at ON gk_insurance_contracts_detail;
CREATE TRIGGER trg_gk_ins_detail_updated_at
    BEFORE UPDATE ON gk_insurance_contracts_detail
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

DROP TRIGGER IF EXISTS trg_gk_consult_updated_at ON gk_consultation_schedule;
CREATE TRIGGER trg_gk_consult_updated_at
    BEFORE UPDATE ON gk_consultation_schedule
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();


-- ══════════════════════════════════════════════════════════════════════════════
-- §7. RLS (Row Level Security) 설정 — agent_id 기준 데이터 격리
-- ══════════════════════════════════════════════════════════════════════════════
ALTER TABLE gk_people_backup              ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_relationship_tags          ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_insurance_contracts_detail ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_consultation_schedule      ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 모든 행 접근 허용 (앱 서버용)
DROP POLICY IF EXISTS "service_role_all_people_backup" ON public.gk_people_backup;
DROP POLICY IF EXISTS "service_role_all_rel_tags"      ON public.gk_relationship_tags;
DROP POLICY IF EXISTS "service_role_all_ins_detail"    ON public.gk_insurance_contracts_detail;
DROP POLICY IF EXISTS "service_role_all_consult"       ON public.gk_consultation_schedule;

CREATE POLICY "service_role_all_people_backup"
    ON public.gk_people_backup FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_rel_tags"
    ON public.gk_relationship_tags FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_ins_detail"
    ON public.gk_insurance_contracts_detail FOR ALL TO service_role USING (true) WITH CHECK (true);
CREATE POLICY "service_role_all_consult"
    ON public.gk_consultation_schedule FOR ALL TO service_role USING (true) WITH CHECK (true);


-- ══════════════════════════════════════════════════════════════════════════════
-- §8. 완료 확인 쿼리
-- ══════════════════════════════════════════════════════════════════════════════
-- 실행 후 아래 쿼리로 테이블 생성 확인
-- SELECT tablename FROM pg_tables WHERE schemaname = 'public' 
--   AND tablename IN ('gk_people_backup', 'gk_relationship_tags', 
--                     'gk_insurance_contracts_detail', 'gk_consultation_schedule');
