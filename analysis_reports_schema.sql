-- ============================================================
-- analysis_reports — 트리니티 엔진 분석 결과 공유 테이블
-- Goldkey AI Masters 2026 | HQ × CRM 공통 중앙 DB
-- ============================================================
-- ⚠️  GP-SEC §1: 연락처 원문 저장 금지 — contact_hash(SHA-256)만 저장
-- ============================================================

CREATE TABLE IF NOT EXISTS analysis_reports (
    id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_hash     TEXT        NOT NULL,              -- SHA-256(11자리숫자) [GP-SEC §1]
    agent_id         TEXT        NOT NULL DEFAULT '',   -- 담당 설계사 user_id
    person_id        TEXT        DEFAULT '',            -- gk_people.person_id (cross-ref용)
    analyzed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    estimated_income NUMERIC     DEFAULT 0,             -- 추정 월소득(원) — 건보료×30 역산
    kb7_score        INTEGER     DEFAULT 0,             -- KB 7대 분류 종합점수 (0-100)
    analysis_data    JSONB,                             -- 트리니티 분석 상세 결과 (run_trinity_analysis 반환값)
    report_text      TEXT        DEFAULT '',            -- 렌더링된 리포트 원문 (카카오 전송용)
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

-- contact_hash + agent_id 복합 UNIQUE — 동일 고객/설계사 조합 Upsert
CREATE UNIQUE INDEX IF NOT EXISTS idx_analysis_reports_contact_agent
    ON analysis_reports (contact_hash, agent_id);

-- person_id 조회용 (HQ 도킹 시 person_id → 분석 결과 Pull)
CREATE INDEX IF NOT EXISTS idx_analysis_reports_person_id
    ON analysis_reports (person_id)
    WHERE person_id IS NOT NULL AND person_id <> '';

-- agent_id 조회용 (설계사별 전체 분석 현황)
CREATE INDEX IF NOT EXISTS idx_analysis_reports_agent_id
    ON analysis_reports (agent_id);

-- analyzed_at 최신순 조회용
CREATE INDEX IF NOT EXISTS idx_analysis_reports_analyzed_at
    ON analysis_reports (analyzed_at DESC);

-- RLS (Row Level Security) — 설계사 본인 데이터만 접근
ALTER TABLE analysis_reports ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 전체 접근 허용 (백엔드 API 호출용)
CREATE POLICY "service_role_all" ON analysis_reports
    FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 일반 authenticated 사용자: agent_id = auth.uid() 본인 행만
CREATE POLICY "agent_own_data" ON analysis_reports
    FOR ALL TO authenticated
    USING (agent_id = auth.uid()::text)
    WITH CHECK (agent_id = auth.uid()::text);

-- updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_analysis_reports_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_analysis_reports_updated_at ON analysis_reports;
CREATE TRIGGER trg_analysis_reports_updated_at
    BEFORE UPDATE ON analysis_reports
    FOR EACH ROW EXECUTE FUNCTION update_analysis_reports_updated_at();
