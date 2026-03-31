-- =============================================================================
-- [GP-PENSION-MONITORING] 연금 분석 모니터링 테이블 스키마
-- 목적: 사용자 행동 추적, A/B 테스트, 전환율 분석
-- =============================================================================

-- ══════════════════════════════════════════════════════════════════════════════
-- [1] pension_analysis_logs — 연금 분석 실행 로그
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pension_analysis_logs (
    -- 기본 식별자
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 사용자 정보
    agent_id TEXT NOT NULL,                    -- 설계사 ID
    customer_name TEXT,                        -- 고객명 (선택)
    customer_id TEXT,                          -- 고객 ID (선택, 암호화된 cid)
    
    -- 입력 파라미터
    age INT NOT NULL,                          -- 현재 나이
    retirement_age INT NOT NULL,               -- 은퇴 나이
    life_expectancy INT NOT NULL,              -- 기대 수명
    region_type TEXT NOT NULL,                 -- 지역 (광역/중소/농어촌)
    household_type TEXT NOT NULL,              -- 가구 (단독/부부)
    monthly_contribution BIGINT NOT NULL,      -- 월 납입액 (원)
    annual_return_rate NUMERIC(5,2) NOT NULL,  -- 연 수익률 (%)
    monthly_salary BIGINT,                     -- 월 급여 (원)
    
    -- 4층 보장 입력
    national_pension_amt BIGINT DEFAULT 0,     -- 국민연금 (원/월)
    retirement_pension_amt BIGINT DEFAULT 0,   -- 퇴직연금 (원/월)
    housing_pension_amt BIGINT DEFAULT 0,      -- 주택연금 (원/월)
    annual_income BIGINT,                      -- 연 총급여 (만원)
    
    -- 분석 옵션
    inflation_scenario TEXT NOT NULL,          -- 물가상승률 (보수적/중립/공격적)
    use_trinity_mode BOOLEAN DEFAULT FALSE,    -- 트리니티 4% 모드
    
    -- 분석 결과
    accumulated_amount BIGINT,                 -- 적립 총액 (원)
    monthly_pension_standard BIGINT,           -- 월 수령액 표준 (원)
    monthly_pension_trinity BIGINT,            -- 월 수령액 트리니티 (원)
    gap_amount BIGINT,                         -- 부족 금액 (원/월)
    gap_percentage NUMERIC(5,2),               -- 부족 비율 (%)
    total_replacement_rate NUMERIC(5,2),       -- 총 소득대체율 (%)
    annual_tax_benefit BIGINT,                 -- 연간 세액공제 (원)
    total_tax_benefit BIGINT,                  -- 총 세액공제 (원)
    
    -- 메타데이터
    session_id TEXT,                           -- 세션 ID
    device_type TEXT,                          -- 디바이스 (desktop/tablet/mobile)
    analysis_duration_ms INT,                  -- 분석 소요 시간 (밀리초)
    
    -- 인덱스
    CONSTRAINT pension_logs_agent_idx CHECK (agent_id IS NOT NULL)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_pension_logs_agent ON pension_analysis_logs(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pension_logs_customer ON pension_analysis_logs(customer_id) WHERE customer_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pension_logs_scenario ON pension_analysis_logs(inflation_scenario, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pension_logs_created ON pension_analysis_logs(created_at DESC);

-- RLS 정책
ALTER TABLE pension_analysis_logs ENABLE ROW LEVEL SECURITY;

-- 설계사는 자신의 로그만 조회 가능
CREATE POLICY pension_logs_select_own ON pension_analysis_logs
    FOR SELECT
    USING (agent_id = current_setting('app.current_user_id', TRUE));

-- 설계사는 자신의 로그만 삽입 가능
CREATE POLICY pension_logs_insert_own ON pension_analysis_logs
    FOR INSERT
    WITH CHECK (agent_id = current_setting('app.current_user_id', TRUE));

-- 주석
COMMENT ON TABLE pension_analysis_logs IS '연금 분석 실행 로그 - 사용자 행동 추적 및 A/B 테스트용';
COMMENT ON COLUMN pension_analysis_logs.inflation_scenario IS '물가상승률 시나리오: 보수적(3%), 중립(4%), 공격적(5%)';
COMMENT ON COLUMN pension_analysis_logs.gap_percentage IS '부족 비율 (%) - A/B 테스트 핵심 지표';


-- ══════════════════════════════════════════════════════════════════════════════
-- [2] pension_conversion_tracking — 전환율 추적 테이블
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pension_conversion_tracking (
    -- 기본 식별자
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 연결 정보
    analysis_log_id UUID REFERENCES pension_analysis_logs(id) ON DELETE CASCADE,
    agent_id TEXT NOT NULL,
    customer_id TEXT,
    
    -- 전환 단계
    stage TEXT NOT NULL,                       -- 단계: view/interest/consult/contract
    stage_timestamp TIMESTAMPTZ DEFAULT NOW(), -- 단계 도달 시각
    
    -- 전환 결과
    is_converted BOOLEAN DEFAULT FALSE,        -- 계약 전환 여부
    contract_amount BIGINT,                    -- 계약 금액 (원/월)
    contract_product TEXT,                     -- 계약 상품명
    contract_date DATE,                        -- 계약 체결일
    
    -- A/B 테스트 그룹
    test_group TEXT,                           -- A/B 테스트 그룹 (A/B/C)
    inflation_scenario_shown TEXT,             -- 보여준 물가 시나리오
    gap_amount_shown BIGINT,                   -- 보여준 부족 금액
    
    -- 메타데이터
    notes TEXT,                                -- 상담 메모
    
    -- 제약조건
    CONSTRAINT valid_stage CHECK (stage IN ('view', 'interest', 'consult', 'contract'))
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_conversion_agent ON pension_conversion_tracking(agent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversion_stage ON pension_conversion_tracking(stage, is_converted);
CREATE INDEX IF NOT EXISTS idx_conversion_test_group ON pension_conversion_tracking(test_group, is_converted);

-- RLS 정책
ALTER TABLE pension_conversion_tracking ENABLE ROW LEVEL SECURITY;

CREATE POLICY conversion_select_own ON pension_conversion_tracking
    FOR SELECT
    USING (agent_id = current_setting('app.current_user_id', TRUE));

CREATE POLICY conversion_insert_own ON pension_conversion_tracking
    FOR INSERT
    WITH CHECK (agent_id = current_setting('app.current_user_id', TRUE));

CREATE POLICY conversion_update_own ON pension_conversion_tracking
    FOR UPDATE
    USING (agent_id = current_setting('app.current_user_id', TRUE));

-- 주석
COMMENT ON TABLE pension_conversion_tracking IS '연금 상담 전환율 추적 - A/B 테스트 핵심 테이블';
COMMENT ON COLUMN pension_conversion_tracking.stage IS 'view(조회) → interest(관심) → consult(상담) → contract(계약)';
COMMENT ON COLUMN pension_conversion_tracking.test_group IS 'A/B/C 테스트 그룹 - 물가 시나리오별 전환율 비교';


-- ══════════════════════════════════════════════════════════════════════════════
-- [3] pension_dashboard_usage — 대시보드 사용 통계
-- ══════════════════════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS pension_dashboard_usage (
    -- 기본 식별자
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 사용자 정보
    agent_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    
    -- 사용 통계
    page_view_count INT DEFAULT 1,             -- 페이지 조회 수
    analysis_run_count INT DEFAULT 0,          -- 분석 실행 횟수
    avg_time_on_page_sec INT,                  -- 평균 체류 시간 (초)
    
    -- 입력 필드 상호작용
    input_changes_count INT DEFAULT 0,         -- 입력 필드 변경 횟수
    scenario_changes_count INT DEFAULT 0,      -- 시나리오 변경 횟수
    
    -- 디바이스 정보
    device_type TEXT,                          -- desktop/tablet/mobile
    browser TEXT,                              -- 브라우저 정보
    screen_width INT,                          -- 화면 너비 (px)
    screen_height INT,                         -- 화면 높이 (px)
    
    -- 날짜 정보 (집계용)
    usage_date DATE DEFAULT CURRENT_DATE,
    
    -- 제약조건
    UNIQUE(agent_id, session_id, usage_date)
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_dashboard_usage_agent ON pension_dashboard_usage(agent_id, usage_date DESC);
CREATE INDEX IF NOT EXISTS idx_dashboard_usage_date ON pension_dashboard_usage(usage_date DESC);

-- RLS 정책
ALTER TABLE pension_dashboard_usage ENABLE ROW LEVEL SECURITY;

CREATE POLICY dashboard_usage_select_own ON pension_dashboard_usage
    FOR SELECT
    USING (agent_id = current_setting('app.current_user_id', TRUE));

CREATE POLICY dashboard_usage_insert_own ON pension_dashboard_usage
    FOR INSERT
    WITH CHECK (agent_id = current_setting('app.current_user_id', TRUE));

CREATE POLICY dashboard_usage_update_own ON pension_dashboard_usage
    FOR UPDATE
    USING (agent_id = current_setting('app.current_user_id', TRUE));

-- 주석
COMMENT ON TABLE pension_dashboard_usage IS '연금 대시보드 사용 통계 - 일별 집계';


-- ══════════════════════════════════════════════════════════════════════════════
-- [4] 집계 뷰 (Aggregation Views)
-- ══════════════════════════════════════════════════════════════════════════════

-- 4-1. 일별 분석 실행 통계
CREATE OR REPLACE VIEW v_pension_daily_stats AS
SELECT
    DATE(created_at) AS analysis_date,
    COUNT(*) AS total_analyses,
    COUNT(DISTINCT agent_id) AS unique_agents,
    COUNT(DISTINCT customer_id) AS unique_customers,
    AVG(gap_percentage) AS avg_gap_percentage,
    AVG(total_replacement_rate) AS avg_replacement_rate,
    COUNT(*) FILTER (WHERE inflation_scenario = '보수적') AS scenario_conservative,
    COUNT(*) FILTER (WHERE inflation_scenario = '중립') AS scenario_neutral,
    COUNT(*) FILTER (WHERE inflation_scenario = '공격적') AS scenario_aggressive,
    COUNT(*) FILTER (WHERE use_trinity_mode = TRUE) AS trinity_mode_count
FROM pension_analysis_logs
GROUP BY DATE(created_at)
ORDER BY analysis_date DESC;

COMMENT ON VIEW v_pension_daily_stats IS '연금 분석 일별 통계 - 대시보드용';


-- 4-2. A/B 테스트 전환율 분석
CREATE OR REPLACE VIEW v_pension_ab_test_results AS
SELECT
    test_group,
    inflation_scenario_shown,
    COUNT(*) AS total_views,
    COUNT(*) FILTER (WHERE stage = 'interest') AS interest_count,
    COUNT(*) FILTER (WHERE stage = 'consult') AS consult_count,
    COUNT(*) FILTER (WHERE is_converted = TRUE) AS conversion_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE is_converted = TRUE) / NULLIF(COUNT(*), 0),
        2
    ) AS conversion_rate_pct,
    AVG(gap_amount_shown) AS avg_gap_shown,
    SUM(contract_amount) AS total_contract_amount
FROM pension_conversion_tracking
GROUP BY test_group, inflation_scenario_shown
ORDER BY conversion_rate_pct DESC;

COMMENT ON VIEW v_pension_ab_test_results IS 'A/B 테스트 전환율 분석 - 시나리오별 비교';


-- 4-3. 설계사별 성과 분석
CREATE OR REPLACE VIEW v_pension_agent_performance AS
SELECT
    agent_id,
    COUNT(DISTINCT DATE(created_at)) AS active_days,
    COUNT(*) AS total_analyses,
    COUNT(DISTINCT customer_id) AS unique_customers,
    AVG(gap_percentage) AS avg_gap_shown,
    COUNT(*) FILTER (WHERE inflation_scenario = '공격적') AS aggressive_scenario_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE inflation_scenario = '공격적') / NULLIF(COUNT(*), 0),
        2
    ) AS aggressive_scenario_rate_pct
FROM pension_analysis_logs
GROUP BY agent_id
ORDER BY total_analyses DESC;

COMMENT ON VIEW v_pension_agent_performance IS '설계사별 연금 분석 성과 - 활동 통계';


-- ══════════════════════════════════════════════════════════════════════════════
-- [5] 샘플 데이터 (테스트용)
-- ══════════════════════════════════════════════════════════════════════════════

-- 샘플 분석 로그 (테스트용 - 실제 운영에서는 삭제)
-- INSERT INTO pension_analysis_logs (
--     agent_id, customer_name, age, retirement_age, life_expectancy,
--     region_type, household_type, monthly_contribution, annual_return_rate,
--     national_pension_amt, retirement_pension_amt, housing_pension_amt,
--     inflation_scenario, gap_amount, gap_percentage
-- ) VALUES
-- ('agent_001', '김철수', 40, 65, 85, '광역', '부부', 300000, 4.5,
--  1720000, 640000, 540000, '공격적', 6550000, 62.4),
-- ('agent_001', '이영희', 35, 60, 85, '중소', '단독', 500000, 5.0,
--  1500000, 500000, 0, '중립', 3200000, 45.2),
-- ('agent_002', '박민수', 45, 65, 85, '광역', '부부', 400000, 4.0,
--  1800000, 700000, 600000, '공격적', 5800000, 58.1);


-- ══════════════════════════════════════════════════════════════════════════════
-- [6] 유틸리티 함수
-- ══════════════════════════════════════════════════════════════════════════════

-- 6-1. 전환율 계산 함수
CREATE OR REPLACE FUNCTION calculate_conversion_rate(
    p_test_group TEXT DEFAULT NULL,
    p_start_date DATE DEFAULT CURRENT_DATE - INTERVAL '30 days',
    p_end_date DATE DEFAULT CURRENT_DATE
)
RETURNS TABLE (
    test_group TEXT,
    total_views BIGINT,
    conversions BIGINT,
    conversion_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COALESCE(pct.test_group, 'ALL') AS test_group,
        COUNT(*) AS total_views,
        COUNT(*) FILTER (WHERE pct.is_converted = TRUE) AS conversions,
        ROUND(
            100.0 * COUNT(*) FILTER (WHERE pct.is_converted = TRUE) / NULLIF(COUNT(*), 0),
            2
        ) AS conversion_rate
    FROM pension_conversion_tracking pct
    WHERE pct.created_at BETWEEN p_start_date AND p_end_date
        AND (p_test_group IS NULL OR pct.test_group = p_test_group)
    GROUP BY ROLLUP(pct.test_group);
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION calculate_conversion_rate IS '전환율 계산 함수 - A/B 테스트 그룹별';


-- ══════════════════════════════════════════════════════════════════════════════
-- [7] 완료 메시지
-- ══════════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
    RAISE NOTICE '✅ [GP-PENSION-MONITORING] 연금 분석 모니터링 스키마 생성 완료';
    RAISE NOTICE '   - pension_analysis_logs: 분석 실행 로그';
    RAISE NOTICE '   - pension_conversion_tracking: 전환율 추적';
    RAISE NOTICE '   - pension_dashboard_usage: 대시보드 사용 통계';
    RAISE NOTICE '   - 3개 집계 뷰 생성 완료';
    RAISE NOTICE '   - RLS 정책 적용 완료';
END $$;
