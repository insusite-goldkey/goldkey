-- ============================================================
-- gk_rewards 테이블 생성 — Step 9 리워드 시스템
-- [GP-STEP9] Goldkey AI Masters 2026
-- ============================================================

CREATE TABLE IF NOT EXISTS gk_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reward_id TEXT NOT NULL UNIQUE DEFAULT gen_random_uuid()::TEXT,
    person_id TEXT NOT NULL REFERENCES gk_people(person_id) ON DELETE RESTRICT,
    agent_id TEXT NOT NULL,
    reward_type TEXT NOT NULL CHECK (reward_type IN ('point', 'gift', 'discount')),
    reward_amount INTEGER NOT NULL DEFAULT 0,
    reason TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'redeemed', 'expired')),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    redeemed_at TIMESTAMPTZ
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_gk_rewards_person_id ON gk_rewards(person_id);
CREATE INDEX IF NOT EXISTS idx_gk_rewards_agent_id ON gk_rewards(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_rewards_reward_id ON gk_rewards(reward_id);
CREATE INDEX IF NOT EXISTS idx_gk_rewards_status ON gk_rewards(status);

-- updated_at 자동 갱신 트리거
DROP TRIGGER IF EXISTS trg_gk_rewards_updated_at ON gk_rewards;
CREATE TRIGGER trg_gk_rewards_updated_at
    BEFORE UPDATE ON gk_rewards
    FOR EACH ROW EXECUTE FUNCTION gk_set_updated_at();

-- 주석 추가
COMMENT ON TABLE gk_rewards IS '리워드 시스템 테이블 (Step 9) - 소개 보상 및 포인트 관리';
COMMENT ON COLUMN gk_rewards.reward_type IS '리워드 유형 (point: 포인트, gift: 기프티콘, discount: 할인)';
COMMENT ON COLUMN gk_rewards.reward_amount IS '리워드 금액/포인트';
COMMENT ON COLUMN gk_rewards.status IS '리워드 상태 (pending: 대기, approved: 승인, redeemed: 사용, expired: 만료)';
COMMENT ON COLUMN gk_rewards.reason IS '리워드 사유 (예: 신규 고객 소개, 계약 체결 등)';
