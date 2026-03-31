-- ══════════════════════════════════════════════════════════════════════════════
-- agent_work_state 테이블 스키마
-- 목적: Cross-Device Sync - 기기 간 작업 상태 동기화
-- 작성일: 2026-03-31
-- ══════════════════════════════════════════════════════════════════════════════

-- 테이블 생성
CREATE TABLE IF NOT EXISTS agent_work_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    state_type TEXT NOT NULL,
    state_data JSONB NOT NULL,
    device_id TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, state_type)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_agent_work_state_user_id 
    ON agent_work_state(user_id);

CREATE INDEX IF NOT EXISTS idx_agent_work_state_state_type 
    ON agent_work_state(state_type);

CREATE INDEX IF NOT EXISTS idx_agent_work_state_updated_at 
    ON agent_work_state(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_agent_work_state_device_id 
    ON agent_work_state(device_id);

-- 복합 인덱스
CREATE INDEX IF NOT EXISTS idx_agent_work_state_user_state 
    ON agent_work_state(user_id, state_type);

-- 코멘트 추가
COMMENT ON TABLE agent_work_state IS 'Cross-Device Sync: 설계사 작업 상태 동기화 테이블';
COMMENT ON COLUMN agent_work_state.id IS '고유 ID';
COMMENT ON COLUMN agent_work_state.user_id IS '사용자(설계사) ID';
COMMENT ON COLUMN agent_work_state.state_type IS '상태 유형 (draft_report, analysis_in_progress, customer_form 등)';
COMMENT ON COLUMN agent_work_state.state_data IS '상태 데이터 (JSON)';
COMMENT ON COLUMN agent_work_state.device_id IS '기기 ID (UUID)';
COMMENT ON COLUMN agent_work_state.updated_at IS '최종 업데이트 시각';
COMMENT ON COLUMN agent_work_state.created_at IS '생성 시각';

-- RLS (Row Level Security) 활성화
ALTER TABLE agent_work_state ENABLE ROW LEVEL SECURITY;

-- RLS 정책: 사용자는 자신의 작업 상태만 조회 가능
CREATE POLICY "Users can view their own work state"
    ON agent_work_state FOR SELECT
    USING (auth.uid()::text = user_id);

-- RLS 정책: 사용자는 자신의 작업 상태만 삽입 가능
CREATE POLICY "Users can insert their own work state"
    ON agent_work_state FOR INSERT
    WITH CHECK (auth.uid()::text = user_id);

-- RLS 정책: 사용자는 자신의 작업 상태만 업데이트 가능
CREATE POLICY "Users can update their own work state"
    ON agent_work_state FOR UPDATE
    USING (auth.uid()::text = user_id);

-- RLS 정책: 사용자는 자신의 작업 상태만 삭제 가능
CREATE POLICY "Users can delete their own work state"
    ON agent_work_state FOR DELETE
    USING (auth.uid()::text = user_id);

-- 트리거: updated_at 자동 업데이트
CREATE OR REPLACE FUNCTION update_agent_work_state_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_agent_work_state_updated_at
    BEFORE UPDATE ON agent_work_state
    FOR EACH ROW
    EXECUTE FUNCTION update_agent_work_state_updated_at();

-- ══════════════════════════════════════════════════════════════════════════════
-- 샘플 데이터 (테스트용)
-- ══════════════════════════════════════════════════════════════════════════════

-- Draft Report 샘플
INSERT INTO agent_work_state (user_id, state_type, state_data, device_id)
VALUES (
    'test_agent_001',
    'draft_report',
    '{
        "customer_id": "cust_001",
        "report_data": {
            "customer_name": "김철수",
            "total_risk": 450000000,
            "inheritance_tax": 300000000,
            "sections": ["Executive Summary", "Risk Assessment", "Strategic Recommendation"]
        },
        "saved_at": "2026-03-31T14:00:00Z"
    }'::jsonb,
    'device_12345'
)
ON CONFLICT (user_id, state_type) DO UPDATE
SET state_data = EXCLUDED.state_data,
    device_id = EXCLUDED.device_id,
    updated_at = NOW();

-- Analysis In Progress 샘플
INSERT INTO agent_work_state (user_id, state_type, state_data, device_id)
VALUES (
    'test_agent_001',
    'analysis_in_progress',
    '{
        "customer_id": "cust_001",
        "analysis_data": {
            "customer_name": "김철수",
            "current_step": "리스크 계산 중",
            "progress": 65,
            "ocr_result": {
                "insurance_company": "삼성생명",
                "coverage_amount": 50000000
            }
        },
        "saved_at": "2026-03-31T14:05:00Z"
    }'::jsonb,
    'device_12345'
)
ON CONFLICT (user_id, state_type) DO UPDATE
SET state_data = EXCLUDED.state_data,
    device_id = EXCLUDED.device_id,
    updated_at = NOW();

-- Customer Form 샘플
INSERT INTO agent_work_state (user_id, state_type, state_data, device_id)
VALUES (
    'test_agent_001',
    'customer_form',
    '{
        "name": "김철수",
        "age": 52,
        "industry": "제조업",
        "phone": "010-1234-5678",
        "address": "서울특별시 강남구",
        "saved_at": "2026-03-31T14:10:00Z"
    }'::jsonb,
    'device_12345'
)
ON CONFLICT (user_id, state_type) DO UPDATE
SET state_data = EXCLUDED.state_data,
    device_id = EXCLUDED.device_id,
    updated_at = NOW();

-- ══════════════════════════════════════════════════════════════════════════════
-- 유용한 쿼리
-- ══════════════════════════════════════════════════════════════════════════════

-- 특정 사용자의 모든 작업 상태 조회
-- SELECT * FROM agent_work_state WHERE user_id = 'test_agent_001' ORDER BY updated_at DESC;

-- 특정 사용자의 특정 상태 유형 조회
-- SELECT * FROM agent_work_state WHERE user_id = 'test_agent_001' AND state_type = 'draft_report';

-- 최근 업데이트된 작업 상태 조회 (모든 사용자)
-- SELECT user_id, state_type, updated_at FROM agent_work_state ORDER BY updated_at DESC LIMIT 10;

-- 특정 기기에서 작업한 상태 조회
-- SELECT * FROM agent_work_state WHERE device_id = 'device_12345';

-- 오래된 작업 상태 삭제 (30일 이상)
-- DELETE FROM agent_work_state WHERE updated_at < NOW() - INTERVAL '30 days';

-- ══════════════════════════════════════════════════════════════════════════════
-- 마이그레이션 롤백 (필요 시)
-- ══════════════════════════════════════════════════════════════════════════════

-- DROP TRIGGER IF EXISTS trigger_update_agent_work_state_updated_at ON agent_work_state;
-- DROP FUNCTION IF EXISTS update_agent_work_state_updated_at();
-- DROP TABLE IF EXISTS agent_work_state CASCADE;
