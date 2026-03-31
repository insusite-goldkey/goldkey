-- ══════════════════════════════════════════════════════════════════════════════
-- 보험 마케팅 포인트 테이블
-- LLM이 추출한 이달의 핵심 판매포인트 저장
-- 
-- 작성일: 2026-03-31
-- 목적: 매월 신규 리플릿에서 핵심 판매포인트 자동 추출 및 저장
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. insurance_marketing_points 테이블 생성
CREATE TABLE IF NOT EXISTS insurance_marketing_points (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    company_type TEXT NOT NULL CHECK (company_type IN ('손해보험', '생명보험')),
    marketing_point TEXT NOT NULL,
    reference_year INT NOT NULL,
    reference_month INT NOT NULL,
    priority INT DEFAULT 0,
    extracted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_insurance_marketing_points_company ON insurance_marketing_points(company);
CREATE INDEX IF NOT EXISTS idx_insurance_marketing_points_company_type ON insurance_marketing_points(company_type);
CREATE INDEX IF NOT EXISTS idx_insurance_marketing_points_reference ON insurance_marketing_points(reference_year, reference_month);
CREATE INDEX IF NOT EXISTS idx_insurance_marketing_points_priority ON insurance_marketing_points(priority DESC);

-- 3. 복합 인덱스 (조회 최적화)
CREATE INDEX IF NOT EXISTS idx_insurance_marketing_points_type_priority 
    ON insurance_marketing_points(company_type, priority DESC, reference_year DESC, reference_month DESC);

-- 4. 주석 추가
COMMENT ON TABLE insurance_marketing_points IS '보험 마케팅 포인트 테이블';
COMMENT ON COLUMN insurance_marketing_points.company IS '보험사명';
COMMENT ON COLUMN insurance_marketing_points.company_type IS '보험사 구분 (손해보험/생명보험)';
COMMENT ON COLUMN insurance_marketing_points.marketing_point IS '핵심 판매포인트';
COMMENT ON COLUMN insurance_marketing_points.reference_year IS '적용 연도';
COMMENT ON COLUMN insurance_marketing_points.reference_month IS '적용 월';
COMMENT ON COLUMN insurance_marketing_points.priority IS '우선순위 (높을수록 상단 노출)';

-- 5. 이달의 마케팅 포인트 조회 함수
CREATE OR REPLACE FUNCTION get_monthly_marketing_points(
    target_year INT DEFAULT NULL,
    target_month INT DEFAULT NULL,
    limit_count INT DEFAULT 10
)
RETURNS TABLE (
    company TEXT,
    company_type TEXT,
    marketing_point TEXT,
    priority INT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_year INT;
    v_month INT;
BEGIN
    -- 기본값: 현재 년월
    v_year := COALESCE(target_year, EXTRACT(YEAR FROM CURRENT_DATE)::INT);
    v_month := COALESCE(target_month, EXTRACT(MONTH FROM CURRENT_DATE)::INT);
    
    RETURN QUERY
    SELECT
        imp.company,
        imp.company_type,
        imp.marketing_point,
        imp.priority
    FROM insurance_marketing_points imp
    WHERE 
        imp.reference_year = v_year
        AND imp.reference_month = v_month
    ORDER BY 
        CASE imp.company_type 
            WHEN '손해보험' THEN 1 
            WHEN '생명보험' THEN 2 
            ELSE 3 
        END,
        imp.priority DESC,
        imp.company
    LIMIT limit_count;
END;
$$;

COMMENT ON FUNCTION get_monthly_marketing_points IS '이달의 마케팅 포인트 조회 (손해보험 우선, 우선순위 순)';

-- ══════════════════════════════════════════════════════════════════════════════
-- 마이그레이션 완료
-- ══════════════════════════════════════════════════════════════════════════════
