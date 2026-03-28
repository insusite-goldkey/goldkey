-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-PHASE4] 좀비 테이블 심폐소생술 - DDL 스키마
-- 4개 테이블: gk_customer_docs, gk_agent_profiles, gk_home_notes, gk_home_ins
-- ══════════════════════════════════════════════════════════════════════════════

-- ══════════════════════════════════════════════════════════════════════════════
-- §1. gk_customer_docs — 고객 문서 메타데이터
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_customer_docs (
    doc_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       TEXT NOT NULL,
    agent_id        TEXT NOT NULL,
    doc_type        TEXT NOT NULL,              -- 'contract', 'claim', 'medical', 'id_card', 'other'
    doc_name        TEXT,
    file_path       TEXT,                       -- GCS 경로
    file_size       BIGINT,
    mime_type       TEXT,
    uploaded_at     TIMESTAMPTZ DEFAULT NOW(),
    tags            TEXT[],
    notes           TEXT,
    is_deleted      BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_customer_docs_person ON gk_customer_docs(person_id);
CREATE INDEX IF NOT EXISTS idx_customer_docs_agent ON gk_customer_docs(agent_id);
CREATE INDEX IF NOT EXISTS idx_customer_docs_type ON gk_customer_docs(doc_type);

ALTER TABLE gk_customer_docs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_customer_docs" ON gk_customer_docs;
CREATE POLICY "service_role_all_customer_docs"
    ON gk_customer_docs FOR ALL TO service_role
    USING (true) WITH CHECK (true);

COMMENT ON TABLE gk_customer_docs IS '[GP-PHASE4] 고객 문서 메타데이터 — 증권·청구서·의무기록 등';


-- ══════════════════════════════════════════════════════════════════════════════
-- §2. gk_agent_profiles — 설계사 프로필 확장 정보
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_agent_profiles (
    profile_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        TEXT NOT NULL UNIQUE,
    display_name    TEXT,
    company         TEXT,
    department      TEXT,
    position        TEXT,
    license_number  TEXT,
    office_phone    TEXT,
    office_address  TEXT,
    profile_photo   TEXT,                       -- GCS 경로
    bio             TEXT,
    specialties     TEXT[],
    certifications  TEXT[],
    social_links    JSONB,                      -- {"linkedin": "...", "instagram": "..."}
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agent_profiles_agent ON gk_agent_profiles(agent_id);

ALTER TABLE gk_agent_profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_agent_profiles" ON gk_agent_profiles;
CREATE POLICY "service_role_all_agent_profiles"
    ON gk_agent_profiles FOR ALL TO service_role
    USING (true) WITH CHECK (true);

COMMENT ON TABLE gk_agent_profiles IS '[GP-PHASE4] 설계사 프로필 확장 정보 — 명함·자격증·SNS 등';


-- ══════════════════════════════════════════════════════════════════════════════
-- §3. gk_home_notes — 홈 화면 메모/노트
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_home_notes (
    note_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        TEXT NOT NULL,
    note_type       TEXT DEFAULT 'general',     -- 'general', 'reminder', 'goal', 'idea'
    title           TEXT,
    content         TEXT,
    priority        TEXT DEFAULT 'normal',      -- 'low', 'normal', 'high', 'urgent'
    color           TEXT DEFAULT '#fef3c7',     -- 파스텔 색상 코드
    is_pinned       BOOLEAN DEFAULT false,
    is_archived     BOOLEAN DEFAULT false,
    due_date        DATE,
    tags            TEXT[],
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_home_notes_agent ON gk_home_notes(agent_id);
CREATE INDEX IF NOT EXISTS idx_home_notes_type ON gk_home_notes(note_type);
CREATE INDEX IF NOT EXISTS idx_home_notes_pinned ON gk_home_notes(is_pinned);

ALTER TABLE gk_home_notes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_home_notes" ON gk_home_notes;
CREATE POLICY "service_role_all_home_notes"
    ON gk_home_notes FOR ALL TO service_role
    USING (true) WITH CHECK (true);

COMMENT ON TABLE gk_home_notes IS '[GP-PHASE4] 홈 화면 메모/노트 — 리마인더·목표·아이디어 등';


-- ══════════════════════════════════════════════════════════════════════════════
-- §4. gk_home_ins — 홈 화면 인사이트/통계 스냅샷
-- ══════════════════════════════════════════════════════════════════════════════
CREATE TABLE IF NOT EXISTS gk_home_ins (
    insight_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id        TEXT NOT NULL,
    insight_type    TEXT NOT NULL,              -- 'daily_summary', 'weekly_goal', 'monthly_stats', 'alert'
    title           TEXT,
    summary         TEXT,
    data_snapshot   JSONB,                      -- {"contracts": 5, "revenue": 1000000, ...}
    metric_value    NUMERIC,
    metric_unit     TEXT,
    trend           TEXT,                       -- 'up', 'down', 'stable'
    is_read         BOOLEAN DEFAULT false,
    valid_until     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_home_ins_agent ON gk_home_ins(agent_id);
CREATE INDEX IF NOT EXISTS idx_home_ins_type ON gk_home_ins(insight_type);
CREATE INDEX IF NOT EXISTS idx_home_ins_read ON gk_home_ins(is_read);

ALTER TABLE gk_home_ins ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "service_role_all_home_ins" ON gk_home_ins;
CREATE POLICY "service_role_all_home_ins"
    ON gk_home_ins FOR ALL TO service_role
    USING (true) WITH CHECK (true);

COMMENT ON TABLE gk_home_ins IS '[GP-PHASE4] 홈 화면 인사이트/통계 스냅샷 — 일일요약·주간목표·월간통계 등';


-- ══════════════════════════════════════════════════════════════════════════════
-- 트리거 설정 (updated_at 자동 갱신)
-- ══════════════════════════════════════════════════════════════════════════════
DROP TRIGGER IF EXISTS trg_customer_docs_updated_at ON gk_customer_docs;
CREATE TRIGGER trg_customer_docs_updated_at
    BEFORE UPDATE ON gk_customer_docs
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

DROP TRIGGER IF EXISTS trg_agent_profiles_updated_at ON gk_agent_profiles;
CREATE TRIGGER trg_agent_profiles_updated_at
    BEFORE UPDATE ON gk_agent_profiles
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

DROP TRIGGER IF EXISTS trg_home_notes_updated_at ON gk_home_notes;
CREATE TRIGGER trg_home_notes_updated_at
    BEFORE UPDATE ON gk_home_notes
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

DROP TRIGGER IF EXISTS trg_home_ins_updated_at ON gk_home_ins;
CREATE TRIGGER trg_home_ins_updated_at
    BEFORE UPDATE ON gk_home_ins
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();


-- ══════════════════════════════════════════════════════════════════════════════
-- 검증 쿼리
-- ══════════════════════════════════════════════════════════════════════════════
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('gk_customer_docs', 'gk_agent_profiles', 'gk_home_notes', 'gk_home_ins')
ORDER BY tablename;
-- 기대값: 4개 테이블 모두 rowsecurity = true
