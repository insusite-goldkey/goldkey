-- ============================================================
-- gk_policies 테이블 확장 — Step 11 계약 생애주기 관리
-- [GP-STEP11] Goldkey AI Masters 2026
-- ============================================================

-- status 컬럼 추가 (계약 상태)
ALTER TABLE gk_policies 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '정상' 
CHECK (status IN ('정상', '실효', '해지', '철회', '갱신'));

-- policy_category 컬럼 추가 (보험 유형)
ALTER TABLE gk_policies 
ADD COLUMN IF NOT EXISTS policy_category TEXT DEFAULT '장기' 
CHECK (policy_category IN ('장기', '자동차', '연간소멸식', '특종'));

-- 인덱스 추가 (상태 및 카테고리 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_status ON gk_policies(status);
CREATE INDEX IF NOT EXISTS idx_gk_policies_category ON gk_policies(policy_category);
CREATE INDEX IF NOT EXISTS idx_gk_policies_status_category ON gk_policies(status, policy_category);

-- 만기일 인덱스 추가 (만기 알림 스케줄 생성 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_expiry_date ON gk_policies(expiry_date);

-- 주석 추가
COMMENT ON COLUMN gk_policies.status IS '계약 상태 (정상: 활성, 실효: 보험료 미납, 해지: 계약 종료, 철회: 청약 철회, 갱신: 갱신 완료)';
COMMENT ON COLUMN gk_policies.policy_category IS '보험 유형 (장기: 종신/건강, 자동차: 자동차보험, 연간소멸식: 1년 만기, 특종: 화재/배상책임 등)';

-- ============================================================
-- gk_insurance_contracts 테이블 확장 (기존 테이블이 있는 경우)
-- ============================================================

-- status 컬럼 추가 (계약 상태)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'gk_insurance_contracts') THEN
        ALTER TABLE gk_insurance_contracts 
        ADD COLUMN IF NOT EXISTS status TEXT DEFAULT '정상' 
        CHECK (status IN ('정상', '실효', '해지', '철회', '갱신'));
        
        -- policy_category 컬럼 추가 (보험 유형)
        ALTER TABLE gk_insurance_contracts 
        ADD COLUMN IF NOT EXISTS policy_category TEXT DEFAULT '장기' 
        CHECK (policy_category IN ('장기', '자동차', '연간소멸식', '특종'));
        
        -- 인덱스 추가
        CREATE INDEX IF NOT EXISTS idx_gk_insurance_contracts_status ON gk_insurance_contracts(status);
        CREATE INDEX IF NOT EXISTS idx_gk_insurance_contracts_category ON gk_insurance_contracts(policy_category);
        
        -- 주석 추가
        COMMENT ON COLUMN gk_insurance_contracts.status IS '계약 상태 (정상: 활성, 실효: 보험료 미납, 해지: 계약 종료, 철회: 청약 철회, 갱신: 갱신 완료)';
        COMMENT ON COLUMN gk_insurance_contracts.policy_category IS '보험 유형 (장기: 종신/건강, 자동차: 자동차보험, 연간소멸식: 1년 만기, 특종: 화재/배상책임 등)';
    END IF;
END $$;

-- ============================================================
-- 기존 데이터 마이그레이션 (기본값 설정)
-- ============================================================

-- gk_policies 기존 데이터에 기본값 설정
UPDATE gk_policies 
SET status = '정상' 
WHERE status IS NULL;

UPDATE gk_policies 
SET policy_category = '장기' 
WHERE policy_category IS NULL;

-- gk_insurance_contracts 기존 데이터에 기본값 설정 (테이블이 있는 경우)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'gk_insurance_contracts') THEN
        UPDATE gk_insurance_contracts 
        SET status = '정상' 
        WHERE status IS NULL;
        
        UPDATE gk_insurance_contracts 
        SET policy_category = '장기' 
        WHERE policy_category IS NULL;
    END IF;
END $$;

-- ============================================================
-- 계약 상태 변경 이력 테이블 (선택 사항)
-- ============================================================

CREATE TABLE IF NOT EXISTS gk_policy_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT,
    changed_by TEXT,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_gk_policy_status_history_policy_id ON gk_policy_status_history(policy_id);
CREATE INDEX IF NOT EXISTS idx_gk_policy_status_history_agent_id ON gk_policy_status_history(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_policy_status_history_changed_at ON gk_policy_status_history(changed_at);

-- 주석 추가
COMMENT ON TABLE gk_policy_status_history IS '계약 상태 변경 이력 테이블 (Step 11) - 해지/실효/갱신 등 상태 변경 추적';
COMMENT ON COLUMN gk_policy_status_history.old_status IS '변경 전 상태';
COMMENT ON COLUMN gk_policy_status_history.new_status IS '변경 후 상태';
COMMENT ON COLUMN gk_policy_status_history.reason IS '변경 사유';
COMMENT ON COLUMN gk_policy_status_history.changed_by IS '변경자 (agent_id 또는 시스템)';
