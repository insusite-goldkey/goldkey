-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-PHASE2] 트리니티 & KB 분석 결과 영구 저장 스키마
-- 작성일: 2026-03-28
-- 목적: 세션 휘발 방지 — 분석 결과를 DB에 영구 저장하여 HQ에서 조회 가능
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
-- [1] gk_trinity_analysis — 트리니티 분석 결과 저장
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.gk_trinity_analysis (
    -- 기본 키
    analysis_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 고객 식별
    person_id           TEXT NOT NULL,                    -- gk_people.person_id 참조
    agent_id            TEXT NOT NULL,                    -- 담당 설계사
    
    -- 분석 메타데이터
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_version    TEXT DEFAULT 'v1.0',              -- 분석 엔진 버전
    
    -- 건보료 역산 결과
    nhis_premium        NUMERIC(12,2),                    -- 입력된 월 건강보험료
    gross_monthly       NUMERIC(12,2),                    -- 역산된 명목 월소득
    gross_annual        NUMERIC(12,2),                    -- 역산된 명목 연봉
    net_annual          NUMERIC(12,2),                    -- 가처분 연소득
    monthly_required    NUMERIC(12,2),                    -- 필요 월소득 (M_req)
    deduction_rate      NUMERIC(5,4),                     -- 합산 공제율
    
    -- 분석 결과 (JSON)
    analysis_data       JSONB NOT NULL,                   -- 전체 분석 결과 (담보별 Gap 등)
    income_breakdown    JSONB,                            -- 소득 공제 상세 (세금, 4대보험)
    coverage_needs      JSONB,                            -- 보장 자산 필요 자금
    kb7_metadata        JSONB,                            -- KB 7대 분류 메타데이터 (있는 경우)
    
    -- 리포트 텍스트
    report_summary      TEXT,                             -- 분석 요약 텍스트
    ai_closing_comment  TEXT,                             -- AI 마무리 멘트
    
    -- 추가 메타
    employment_type     TEXT,                             -- 직장/지역 구분
    ltc_included        BOOLEAN DEFAULT FALSE,            -- 장기요양 포함 여부
    
    -- 타임스탬프
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 인덱스용 복합 키
    CONSTRAINT uq_trinity_person_agent UNIQUE (person_id, agent_id, analyzed_at)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_trinity_person_id ON public.gk_trinity_analysis(person_id);
CREATE INDEX IF NOT EXISTS idx_trinity_agent_id ON public.gk_trinity_analysis(agent_id);
CREATE INDEX IF NOT EXISTS idx_trinity_analyzed_at ON public.gk_trinity_analysis(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_trinity_person_agent ON public.gk_trinity_analysis(person_id, agent_id);

-- 코멘트
COMMENT ON TABLE public.gk_trinity_analysis IS '[GP-PHASE2] 트리니티 분석 결과 영구 저장 — 건보료 역산 × 8단계 세율 × KB 표준 교차 분석';
COMMENT ON COLUMN public.gk_trinity_analysis.analysis_data IS '전체 분석 결과 JSON (담보별 현재가입/표준KB/적정역산/부족분/충족여부)';
COMMENT ON COLUMN public.gk_trinity_analysis.monthly_required IS '가처분 연소득 / 12 (순 필요 월소득, M_req)';


-- ──────────────────────────────────────────────────────────────────────────────
-- [2] gk_kb_analysis — KB 7대 스탠다드 분석 결과 저장
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.gk_kb_analysis (
    -- 기본 키
    analysis_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 고객 식별
    person_id           TEXT NOT NULL,                    -- gk_people.person_id 참조
    agent_id            TEXT NOT NULL,                    -- 담당 설계사
    
    -- 분석 메타데이터
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_version    TEXT DEFAULT 'v1.0',              -- 분석 엔진 버전
    
    -- 고객 정보
    customer_age        INTEGER,                          -- 분석 시점 나이
    customer_gender     TEXT,                             -- 성별 (M/F/전체)
    
    -- KB 7대 분류 점수
    kb_total_score      NUMERIC(5,2),                     -- 총점 (0-100)
    kb_grade            TEXT,                             -- 등급 (S/A/B/C/D/F)
    
    -- 분석 결과 (JSON)
    analysis_data       JSONB NOT NULL,                   -- 전체 분석 결과 (7대 분류별 상세)
    category_scores     JSONB,                            -- 카테고리별 점수 배열
    gap_analysis        JSONB,                            -- 보장 공백 분석
    kosis_weights       JSONB,                            -- KOSIS 가중치 적용 결과
    
    -- 리포트 텍스트
    report_summary      TEXT,                             -- 분석 요약 텍스트
    ai_summary          TEXT,                             -- AI 요약 멘트
    recommendations     TEXT,                             -- 개선 권장사항
    
    -- 원본 데이터
    raw_coverages       JSONB,                            -- 입력된 원본 담보 데이터
    
    -- 타임스탬프
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 인덱스용 복합 키
    CONSTRAINT uq_kb_person_agent UNIQUE (person_id, agent_id, analyzed_at)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_kb_person_id ON public.gk_kb_analysis(person_id);
CREATE INDEX IF NOT EXISTS idx_kb_agent_id ON public.gk_kb_analysis(agent_id);
CREATE INDEX IF NOT EXISTS idx_kb_analyzed_at ON public.gk_kb_analysis(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_kb_person_agent ON public.gk_kb_analysis(person_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_kb_grade ON public.gk_kb_analysis(kb_grade);
CREATE INDEX IF NOT EXISTS idx_kb_score ON public.gk_kb_analysis(kb_total_score DESC);

-- 코멘트
COMMENT ON TABLE public.gk_kb_analysis IS '[GP-PHASE2] KB 7대 스탠다드 분석 결과 영구 저장 — KOSIS 데이터 요새 교차 분석';
COMMENT ON COLUMN public.gk_kb_analysis.analysis_data IS 'KB 7대 분류별 상세 분석 결과 JSON (질병사망/3대진단/수술입원/실손/운전자/치아치매/연금저축)';
COMMENT ON COLUMN public.gk_kb_analysis.kb_grade IS 'KB 종합 등급 (S: 90+, A: 80+, B: 70+, C: 60+, D: 50+, F: 50 미만)';


-- ──────────────────────────────────────────────────────────────────────────────
-- [3] gk_integrated_analysis — 통합 분석 결과 (트리니티 + KB + NIBO)
-- ──────────────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.gk_integrated_analysis (
    -- 기본 키
    analysis_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 고객 식별
    person_id           TEXT NOT NULL,                    -- gk_people.person_id 참조
    agent_id            TEXT NOT NULL,                    -- 담당 설계사
    
    -- 분석 메타데이터
    analyzed_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_type       TEXT NOT NULL,                    -- 'full' | 'trinity_only' | 'kb_only'
    
    -- 연결된 개별 분석 ID
    trinity_analysis_id UUID REFERENCES public.gk_trinity_analysis(analysis_id),
    kb_analysis_id      UUID REFERENCES public.gk_kb_analysis(analysis_id),
    
    -- 통합 결과
    integrated_score    NUMERIC(5,2),                     -- 통합 점수
    integrated_grade    TEXT,                             -- 통합 등급
    
    -- 통합 리포트
    integrated_report   JSONB,                            -- 통합 분석 리포트 전체
    bridge_packet       JSONB,                            -- N-SECTION 브릿지 패킷
    
    -- NIBO 연동
    nibo_status         TEXT,                             -- 'pending' | 'done' | 'failed'
    nibo_data           JSONB,                            -- 내보험다보여 크롤링 결과
    
    -- 타임스탬프
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 인덱스용 복합 키
    CONSTRAINT uq_integrated_person_agent UNIQUE (person_id, agent_id, analyzed_at)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_integrated_person_id ON public.gk_integrated_analysis(person_id);
CREATE INDEX IF NOT EXISTS idx_integrated_agent_id ON public.gk_integrated_analysis(agent_id);
CREATE INDEX IF NOT EXISTS idx_integrated_analyzed_at ON public.gk_integrated_analysis(analyzed_at DESC);
CREATE INDEX IF NOT EXISTS idx_integrated_trinity_id ON public.gk_integrated_analysis(trinity_analysis_id);
CREATE INDEX IF NOT EXISTS idx_integrated_kb_id ON public.gk_integrated_analysis(kb_analysis_id);

-- 코멘트
COMMENT ON TABLE public.gk_integrated_analysis IS '[GP-PHASE2] 통합 분석 결과 — 트리니티 + KB + NIBO 전체 패키지';
COMMENT ON COLUMN public.gk_integrated_analysis.bridge_packet IS 'N-SECTION 브릿지 패킷 (CRM → HQ 컨텍스트 전달용)';


-- ──────────────────────────────────────────────────────────────────────────────
-- [4] RLS (Row Level Security) 정책
-- ──────────────────────────────────────────────────────────────────────────────

-- RLS 활성화
ALTER TABLE public.gk_trinity_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_kb_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.gk_integrated_analysis ENABLE ROW LEVEL SECURITY;

-- service_role 전용 정책 (앱 서버만 접근 가능) - 멱등성 보장
DROP POLICY IF EXISTS "gk_trinity_analysis_service_role_policy" ON public.gk_trinity_analysis;
CREATE POLICY "gk_trinity_analysis_service_role_policy"
    ON public.gk_trinity_analysis
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "gk_kb_analysis_service_role_policy" ON public.gk_kb_analysis;
CREATE POLICY "gk_kb_analysis_service_role_policy"
    ON public.gk_kb_analysis
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

DROP POLICY IF EXISTS "gk_integrated_analysis_service_role_policy" ON public.gk_integrated_analysis;
CREATE POLICY "gk_integrated_analysis_service_role_policy"
    ON public.gk_integrated_analysis
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);


-- ──────────────────────────────────────────────────────────────────────────────
-- [5] 자동 updated_at 갱신 트리거
-- ──────────────────────────────────────────────────────────────────────────────

-- 트리거 함수 (공통)
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 트리거 적용 (멱등성 보장)
DROP TRIGGER IF EXISTS trg_trinity_updated_at ON public.gk_trinity_analysis;
CREATE TRIGGER trg_trinity_updated_at
    BEFORE UPDATE ON public.gk_trinity_analysis
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS trg_kb_updated_at ON public.gk_kb_analysis;
CREATE TRIGGER trg_kb_updated_at
    BEFORE UPDATE ON public.gk_kb_analysis
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS trg_integrated_updated_at ON public.gk_integrated_analysis;
CREATE TRIGGER trg_integrated_updated_at
    BEFORE UPDATE ON public.gk_integrated_analysis
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


-- ──────────────────────────────────────────────────────────────────────────────
-- [6] 완료 확인 쿼리
-- ──────────────────────────────────────────────────────────────────────────────

-- 테이블 생성 확인
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('gk_trinity_analysis', 'gk_kb_analysis', 'gk_integrated_analysis');

-- 트리거 확인
SELECT tgname FROM pg_trigger 
WHERE tgname IN ('trg_trinity_updated_at', 'trg_kb_updated_at', 'trg_integrated_updated_at');

-- RLS 정책 확인
SELECT tablename, policyname FROM pg_policies 
WHERE schemaname = 'public' 
  AND tablename IN ('gk_trinity_analysis', 'gk_kb_analysis', 'gk_integrated_analysis');
