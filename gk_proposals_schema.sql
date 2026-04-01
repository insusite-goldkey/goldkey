-- ============================================================
-- gk_proposals 테이블 생성 — Step 8 AI 제안서 저장
-- [GP-STEP8] Goldkey AI Masters 2026
-- ============================================================

CREATE TABLE IF NOT EXISTS gk_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id TEXT NOT NULL UNIQUE,
    person_id TEXT NOT NULL REFERENCES gk_people(person_id) ON DELETE RESTRICT,
    agent_id TEXT NOT NULL,
    proposal_data JSONB NOT NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_gk_proposals_person_id ON gk_proposals(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_agent_id ON gk_proposals(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_proposals_proposal_id ON gk_proposals(proposal_id);

-- updated_at 자동 갱신 트리거
DROP TRIGGER IF EXISTS trg_gk_proposals_updated_at ON gk_proposals;
CREATE TRIGGER trg_gk_proposals_updated_at
    BEFORE UPDATE ON gk_proposals
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

-- 주석 추가
COMMENT ON TABLE gk_proposals IS 'AI 제안서 저장 테이블 (Step 8) - 감성 세일즈 전략 및 맞춤형 제안서';
COMMENT ON COLUMN gk_proposals.proposal_id IS '제안서 고유 ID (PROP_xxxxxxxx_YYYYMMDDHHmmss)';
COMMENT ON COLUMN gk_proposals.proposal_data IS 'AI 제안서 전체 데이터 (JSON) - 페르소나, 보장 공백 분석, 감성 스크립트, 3가지 플랜 포함';
