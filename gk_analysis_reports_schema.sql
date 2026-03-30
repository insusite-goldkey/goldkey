-- ════════════════════════════════════════════════════════════════════════════
-- [GP-제14조] 분석 결과 저장 테이블 (0코인 무료 조회 지원)
-- Goldkey AI Masters 2026 - 분석 이력 관리 및 중복 분석 방지
-- ════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 1] 분석 결과 저장 테이블 (analysis_reports)
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.analysis_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    result_data JSONB NOT NULL,
    coins_used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.analysis_reports IS '분석 결과 저장 테이블 (0코인 무료 조회 지원)';
COMMENT ON COLUMN public.analysis_reports.person_id IS '고객 ID';
COMMENT ON COLUMN public.analysis_reports.agent_id IS '설계사 ID';
COMMENT ON COLUMN public.analysis_reports.analysis_type IS '분석 유형 (SCAN, TRINITY, AI_STRATEGY, KAKAO_MESSAGE 등)';
COMMENT ON COLUMN public.analysis_reports.result_data IS '분석 결과 데이터 (JSON)';
COMMENT ON COLUMN public.analysis_reports.coins_used IS '사용된 코인 수량';

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_analysis_reports_person_id 
    ON public.analysis_reports (person_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_reports_agent_id 
    ON public.analysis_reports (agent_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_reports_type 
    ON public.analysis_reports (analysis_type);

-- 복합 인덱스 (0코인 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_analysis_reports_lookup 
    ON public.analysis_reports (person_id, analysis_type, agent_id, created_at DESC);

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 2] RLS (Row Level Security) 정책
-- ──────────────────────────────────────────────────────────────────────────

ALTER TABLE public.analysis_reports ENABLE ROW LEVEL SECURITY;

-- 설계사는 본인이 생성한 분석 결과만 조회 가능
CREATE POLICY "Users can view own analysis reports"
ON public.analysis_reports FOR SELECT
USING (agent_id = auth.uid() OR agent_id = current_setting('request.jwt.claims', true)::json->>'user_id');

-- 설계사는 본인 분석 결과만 삽입 가능
CREATE POLICY "Users can insert own analysis reports"
ON public.analysis_reports FOR INSERT
WITH CHECK (agent_id = auth.uid() OR agent_id = current_setting('request.jwt.claims', true)::json->>'user_id');

-- 설계사는 본인 분석 결과만 업데이트 가능
CREATE POLICY "Users can update own analysis reports"
ON public.analysis_reports FOR UPDATE
USING (agent_id = auth.uid() OR agent_id = current_setting('request.jwt.claims', true)::json->>'user_id');

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 3] 분석 유형 ENUM (선택사항)
-- ──────────────────────────────────────────────────────────────────────────

-- 분석 유형 체크 제약 (데이터 무결성)
ALTER TABLE public.analysis_reports
    ADD CONSTRAINT chk_analysis_type
    CHECK (analysis_type IN (
        'SCAN',                 -- 증권 스캔
        'TABLE_3STEP',          -- 3단 일람표
        'TRINITY',              -- 트리니티 분석
        'AI_TARGETING',         -- AI 타겟 추천
        'EMOTIONAL_PROPOSAL',   -- 감성 제안서
        'KAKAO_MESSAGE',        -- 카카오톡 멘트
        'COMPARISON_STRATEGY',  -- 비교 전략
        'NIBO_ANALYSIS',        -- 내보험다보여 분석
        'MEDICAL_RECORD',       -- 진료기록 분석
        'ACCIDENT_REPORT'       -- 사고 보고서 분석
    ));

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 4] 분석 결과 조회 함수 (0코인 무료 조회)
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.get_latest_analysis(
    p_person_id TEXT,
    p_analysis_type TEXT,
    p_agent_id TEXT DEFAULT NULL
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_result JSONB;
BEGIN
    -- 최신 분석 결과 조회
    SELECT result_data INTO v_result
    FROM public.analysis_reports
    WHERE person_id = p_person_id
      AND analysis_type = p_analysis_type
      AND (p_agent_id IS NULL OR agent_id = p_agent_id)
    ORDER BY created_at DESC
    LIMIT 1;
    
    RETURN v_result;
END;
$$;

COMMENT ON FUNCTION public.get_latest_analysis IS '최신 분석 결과 조회 (0코인 무료 조회)';

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 5] 분석 이력 통계 뷰
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_analysis_stats AS
SELECT
    agent_id,
    analysis_type,
    COUNT(*) AS total_count,
    SUM(coins_used) AS total_coins_used,
    AVG(coins_used) AS avg_coins_per_analysis,
    MIN(created_at) AS first_analysis_date,
    MAX(created_at) AS last_analysis_date
FROM public.analysis_reports
GROUP BY agent_id, analysis_type;

COMMENT ON VIEW public.v_analysis_stats IS '설계사별 분석 이력 통계';

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 6] 테스트 데이터 (개발용)
-- ──────────────────────────────────────────────────────────────────────────

-- 테스트용 분석 결과 삽입 (실제 운영 시 삭제)
/*
INSERT INTO public.analysis_reports (
    person_id,
    agent_id,
    analysis_type,
    result_data,
    coins_used
) VALUES (
    'test_person_001',
    'test_agent_001',
    'SCAN',
    '{"scan_result": "테스트 스캔 결과", "policies": [{"name": "삼성화재 실손보험"}]}'::JSONB,
    1
);

-- 조회 테스트
SELECT public.get_latest_analysis('test_person_001', 'SCAN', 'test_agent_001');
*/
