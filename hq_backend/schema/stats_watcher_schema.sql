-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-STEP14] 실시간 통계 감시 및 자동 업데이트 엔진 - Supabase 테이블 스키마
-- ══════════════════════════════════════════════════════════════════════════════

-- [1] gk_pending_updates: 승인 대기 중인 통계 업데이트
CREATE TABLE IF NOT EXISTS gk_pending_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_name TEXT NOT NULL,                    -- 변경 대상 필드명 (예: "암 발생률 (전체)")
    current_value TEXT NOT NULL,                 -- 현재 값
    new_value TEXT NOT NULL,                     -- 신규 값
    diff_percent DECIMAL(10, 2) NOT NULL,        -- 변화율 (%)
    change_type TEXT NOT NULL,                   -- 변화 유형 (increase, decrease)
    significance TEXT NOT NULL,                  -- 중요도 (high, medium, low)
    source TEXT NOT NULL,                        -- 데이터 출처 (KOSIS, HIRA 등)
    status TEXT NOT NULL DEFAULT 'pending',      -- 상태 (pending, approved, rejected)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at TIMESTAMPTZ,
    approved_by TEXT,                            -- 승인자 agent_id
    agent_id TEXT NOT NULL,                      -- 생성자 agent_id
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT valid_change_type CHECK (change_type IN ('increase', 'decrease')),
    CONSTRAINT valid_significance CHECK (significance IN ('high', 'medium', 'low'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_pending_updates_status ON gk_pending_updates(status);
CREATE INDEX IF NOT EXISTS idx_pending_updates_created_at ON gk_pending_updates(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pending_updates_agent_id ON gk_pending_updates(agent_id);


-- [2] gk_current_stats: 현재 저장된 통계 (비교 기준)
CREATE TABLE IF NOT EXISTS gk_current_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    data_type TEXT NOT NULL UNIQUE,              -- 통계 유형 (cancer_incidence_rate, cancer_treatment_cost 등)
    male_rate DECIMAL(10, 2),                    -- 남성 암 발생률 (%)
    female_rate DECIMAL(10, 2),                  -- 여성 암 발생률 (%)
    total_rate DECIMAL(10, 2),                   -- 전체 암 발생률 (%)
    average_cost BIGINT,                         -- 평균 치료비 (원)
    ngs_test_cost BIGINT,                        -- NGS 검사비 (원)
    targeted_therapy_yearly BIGINT,              -- 표적항암 연간 비용 (원)
    immunotherapy_yearly BIGINT,                 -- 면역항암 연간 비용 (원)
    average_non_covered BIGINT,                  -- 평균 비급여 비용 (원)
    source TEXT NOT NULL,                        -- 데이터 출처
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reference_year TEXT,                         -- 기준 연도 (예: "2021")
    
    CONSTRAINT valid_data_type CHECK (data_type IN ('cancer_incidence_rate', 'cancer_treatment_cost', 'non_covered_costs'))
);

-- 초기 데이터 삽입 (현재 앱에서 사용 중인 통계)
INSERT INTO gk_current_stats (
    data_type, male_rate, female_rate, total_rate, 
    source, reference_year
) VALUES (
    'cancer_incidence_rate', 39.1, 36.0, 38.1,
    'KOSIS', '2021'
) ON CONFLICT (data_type) DO NOTHING;

INSERT INTO gk_current_stats (
    data_type, average_cost, ngs_test_cost, 
    targeted_therapy_yearly, immunotherapy_yearly,
    source
) VALUES (
    'cancer_treatment_cost', 38000000, 1500000,
    50000000, 100000000,
    'HIRA'
) ON CONFLICT (data_type) DO NOTHING;


-- [3] gk_audit_log: 통계 업데이트 감사 로그
CREATE TABLE IF NOT EXISTS gk_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    action TEXT NOT NULL,                        -- 작업 유형 (global_stats_patch, manual_update 등)
    agent_id TEXT NOT NULL,                      -- 실행자 agent_id
    affected_tables TEXT[] NOT NULL,             -- 영향받은 테이블 목록
    updated_count INTEGER NOT NULL DEFAULT 0,    -- 업데이트된 레코드 수
    pending_update_ids UUID[],                   -- 관련 pending_updates ID 목록
    details JSONB,                               -- 상세 정보 (JSON)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_action CHECK (action IN ('global_stats_patch', 'manual_update', 'auto_sync', 'rollback'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON gk_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_agent_id ON gk_audit_log(agent_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON gk_audit_log(action);


-- [4] RPC 함수: 통계 값 일괄 교체
CREATE OR REPLACE FUNCTION replace_stat_value(
    old_value TEXT,
    new_value TEXT,
    field_name TEXT
) RETURNS TEXT AS $$
BEGIN
    -- 텍스트 내의 통계 값을 교체하는 로직
    -- 예: "38.1%" → "39.2%"
    -- 실제 구현 시 정규식 기반 교체 로직 추가 필요
    RETURN REPLACE(old_value, old_value, new_value);
END;
$$ LANGUAGE plpgsql;


-- [5] RPC 함수: 승인 대기 중인 업데이트 조회
CREATE OR REPLACE FUNCTION get_pending_updates_summary()
RETURNS TABLE (
    total_count BIGINT,
    high_significance_count BIGINT,
    medium_significance_count BIGINT,
    low_significance_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_count,
        COUNT(*) FILTER (WHERE significance = 'high') AS high_significance_count,
        COUNT(*) FILTER (WHERE significance = 'medium') AS medium_significance_count,
        COUNT(*) FILTER (WHERE significance = 'low') AS low_significance_count
    FROM gk_pending_updates
    WHERE status = 'pending';
END;
$$ LANGUAGE plpgsql;


-- [6] RPC 함수: 통계 업데이트 히스토리 조회
CREATE OR REPLACE FUNCTION get_stats_update_history(
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    action TEXT,
    agent_id TEXT,
    updated_count INTEGER,
    created_at TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        al.id,
        al.action,
        al.agent_id,
        al.updated_count,
        al.created_at
    FROM gk_audit_log al
    WHERE al.action = 'global_stats_patch'
    ORDER BY al.created_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- [7] 트리거: pending_updates 승인 시 current_stats 자동 업데이트
CREATE OR REPLACE FUNCTION update_current_stats_on_approval()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND OLD.status = 'pending' THEN
        -- 암 발생률 업데이트
        IF NEW.field_name LIKE '%암 발생률%' THEN
            UPDATE gk_current_stats
            SET 
                total_rate = CASE 
                    WHEN NEW.field_name = '암 발생률 (전체)' THEN NEW.new_value::DECIMAL
                    ELSE total_rate
                END,
                male_rate = CASE 
                    WHEN NEW.field_name = '암 발생률 (남성)' THEN NEW.new_value::DECIMAL
                    ELSE male_rate
                END,
                female_rate = CASE 
                    WHEN NEW.field_name = '암 발생률 (여성)' THEN NEW.new_value::DECIMAL
                    ELSE female_rate
                END,
                updated_at = NOW()
            WHERE data_type = 'cancer_incidence_rate';
        END IF;
        
        -- 치료비 업데이트
        IF NEW.field_name LIKE '%치료비%' THEN
            UPDATE gk_current_stats
            SET 
                average_cost = CASE 
                    WHEN NEW.field_name = '암 평균 치료비' THEN NEW.new_value::BIGINT
                    ELSE average_cost
                END,
                updated_at = NOW()
            WHERE data_type = 'cancer_treatment_cost';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_current_stats
AFTER UPDATE ON gk_pending_updates
FOR EACH ROW
EXECUTE FUNCTION update_current_stats_on_approval();


-- [8] Row Level Security (RLS) 설정
ALTER TABLE gk_pending_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_current_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE gk_audit_log ENABLE ROW LEVEL SECURITY;

-- 관리자만 pending_updates 조회/수정 가능
CREATE POLICY pending_updates_admin_policy ON gk_pending_updates
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin' OR agent_id = auth.jwt() ->> 'sub');

-- 모든 사용자가 current_stats 조회 가능 (읽기 전용)
CREATE POLICY current_stats_read_policy ON gk_current_stats
    FOR SELECT
    USING (true);

-- 관리자만 current_stats 수정 가능
CREATE POLICY current_stats_admin_policy ON gk_current_stats
    FOR ALL
    USING (auth.jwt() ->> 'role' = 'admin');

-- 관리자만 audit_log 조회 가능
CREATE POLICY audit_log_admin_policy ON gk_audit_log
    FOR SELECT
    USING (auth.jwt() ->> 'role' = 'admin' OR agent_id = auth.jwt() ->> 'sub');


-- [9] 주석 및 설명
COMMENT ON TABLE gk_pending_updates IS '[GP-STEP14] 승인 대기 중인 통계 업데이트 - AI가 감지한 통계 변동 사항을 관리자 승인 전까지 임시 저장';
COMMENT ON TABLE gk_current_stats IS '[GP-STEP14] 현재 저장된 통계 - 외부 API와 비교하기 위한 기준 통계';
COMMENT ON TABLE gk_audit_log IS '[GP-STEP14] 통계 업데이트 감사 로그 - 언제, 누가, 무엇을 변경했는지 추적';

COMMENT ON COLUMN gk_pending_updates.field_name IS '변경 대상 필드명 (예: "암 발생률 (전체)", "암 평균 치료비")';
COMMENT ON COLUMN gk_pending_updates.diff_percent IS '변화율 (%) - 유의미한 변화 판단 기준';
COMMENT ON COLUMN gk_pending_updates.significance IS '중요도 (high: 1% 이상, medium: 0.5~1%, low: 0.5% 미만)';
COMMENT ON COLUMN gk_pending_updates.status IS '상태 (pending: 승인 대기, approved: 승인 완료, rejected: 거부)';

COMMENT ON COLUMN gk_current_stats.data_type IS '통계 유형 (cancer_incidence_rate, cancer_treatment_cost, non_covered_costs)';
COMMENT ON COLUMN gk_current_stats.reference_year IS '기준 연도 (예: "2021" - 2021년 국가암등록통계)';

COMMENT ON COLUMN gk_audit_log.action IS '작업 유형 (global_stats_patch: 전역 업데이트, manual_update: 수동 업데이트, auto_sync: 자동 동기화, rollback: 롤백)';
COMMENT ON COLUMN gk_audit_log.affected_tables IS '영향받은 테이블 목록 (예: ["gk_knowledge_base", "gk_war_room_scripts"])';
