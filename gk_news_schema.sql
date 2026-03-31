-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-ZERO-TRUST] 뉴스 데이터 테이블 스키마
-- Zero-Trust 파이프라인으로 검증된 뉴스 데이터 저장
-- ══════════════════════════════════════════════════════════════════════════════

-- ── gk_news 테이블 생성 ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.gk_news (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_id          TEXT NOT NULL,                    -- 등록한 설계사 ID
    company           TEXT NOT NULL,                    -- 보험사/기업명
    profit            TEXT,                             -- 순이익 (예: 12조원)
    revenue           TEXT,                             -- 매출액 (예: 50조원)
    change_rate       TEXT,                             -- 증감률 (예: 15%)
    trend             TEXT NOT NULL,                    -- 상승/하락/유지
    summary           TEXT NOT NULL,                    -- 3줄 요약
    publish_date      DATE,                             -- 발행일
    source_url        TEXT,                             -- 원본 URL
    created_at        TIMESTAMPTZ DEFAULT NOW(),        -- 등록일시
    updated_at        TIMESTAMPTZ DEFAULT NOW()         -- 수정일시
);

-- ── 인덱스 생성 ──────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_gk_news_agent_id ON public.gk_news(agent_id);
CREATE INDEX IF NOT EXISTS idx_gk_news_company ON public.gk_news(company);
CREATE INDEX IF NOT EXISTS idx_gk_news_publish_date ON public.gk_news(publish_date DESC);
CREATE INDEX IF NOT EXISTS idx_gk_news_created_at ON public.gk_news(created_at DESC);

-- ── RLS (Row Level Security) 활성화 ──────────────────────────────────────
ALTER TABLE public.gk_news ENABLE ROW LEVEL SECURITY;

-- ── RLS 정책: 자신이 등록한 뉴스만 조회 ──────────────────────────────────
DROP POLICY IF EXISTS "gk_news_select_own" ON public.gk_news;
CREATE POLICY "gk_news_select_own" ON public.gk_news
    FOR SELECT
    USING (agent_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- ── RLS 정책: 자신만 뉴스 등록 가능 ───────────────────────────────────────
DROP POLICY IF EXISTS "gk_news_insert_own" ON public.gk_news;
CREATE POLICY "gk_news_insert_own" ON public.gk_news
    FOR INSERT
    WITH CHECK (agent_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- ── RLS 정책: 자신이 등록한 뉴스만 수정 ──────────────────────────────────
DROP POLICY IF EXISTS "gk_news_update_own" ON public.gk_news;
CREATE POLICY "gk_news_update_own" ON public.gk_news
    FOR UPDATE
    USING (agent_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- ── RLS 정책: 자신이 등록한 뉴스만 삭제 ──────────────────────────────────
DROP POLICY IF EXISTS "gk_news_delete_own" ON public.gk_news;
CREATE POLICY "gk_news_delete_own" ON public.gk_news
    FOR DELETE
    USING (agent_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- ── updated_at 자동 업데이트 트리거 ───────────────────────────────────────
CREATE OR REPLACE FUNCTION update_gk_news_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_gk_news_updated_at ON public.gk_news;
CREATE TRIGGER trigger_gk_news_updated_at
    BEFORE UPDATE ON public.gk_news
    FOR EACH ROW
    EXECUTE FUNCTION update_gk_news_updated_at();

-- ── 코멘트 추가 ──────────────────────────────────────────────────────────
COMMENT ON TABLE public.gk_news IS '[GP-ZERO-TRUST] Zero-Trust 파이프라인으로 검증된 뉴스 데이터';
COMMENT ON COLUMN public.gk_news.agent_id IS '등록한 설계사 ID (RLS 기준)';
COMMENT ON COLUMN public.gk_news.company IS '보험사/기업명 (AI 환각 방지 검증 완료)';
COMMENT ON COLUMN public.gk_news.profit IS '순이익 (예: 12조원, 3000억원)';
COMMENT ON COLUMN public.gk_news.revenue IS '매출액 (예: 50조원)';
COMMENT ON COLUMN public.gk_news.change_rate IS '증감률 (예: 15%, -3.5%)';
COMMENT ON COLUMN public.gk_news.trend IS '실적 추세 (상승/하락/유지)';
COMMENT ON COLUMN public.gk_news.summary IS '3줄 요약 (팩트 100% 유지)';
COMMENT ON COLUMN public.gk_news.publish_date IS '뉴스 발행일';
COMMENT ON COLUMN public.gk_news.source_url IS '원본 뉴스 URL';
