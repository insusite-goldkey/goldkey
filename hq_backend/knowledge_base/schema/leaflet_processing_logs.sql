-- ══════════════════════════════════════════════════════════════════════════════
-- 리플릿 처리 로그 테이블
-- 매월 신규 리플릿 처리 이력 기록
-- 
-- 작성일: 2026-03-31
-- 목적: 리플릿 자동 처리 작업 완료 보고서 기록
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. leaflet_processing_logs 테이블 생성
CREATE TABLE IF NOT EXISTS leaflet_processing_logs (
    id BIGSERIAL PRIMARY KEY,
    company TEXT NOT NULL,
    year INT NOT NULL,
    month INT NOT NULL,
    file_path TEXT,
    file_hash TEXT,
    points_extracted INT DEFAULT 0,
    status TEXT CHECK (status IN ('success', 'failed', 'duplicate')),
    error_message TEXT,
    processed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_leaflet_processing_logs_company ON leaflet_processing_logs(company);
CREATE INDEX IF NOT EXISTS idx_leaflet_processing_logs_status ON leaflet_processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_leaflet_processing_logs_date ON leaflet_processing_logs(year, month);
CREATE INDEX IF NOT EXISTS idx_leaflet_processing_logs_processed_at ON leaflet_processing_logs(processed_at DESC);

-- 3. 주석 추가
COMMENT ON TABLE leaflet_processing_logs IS '리플릿 처리 로그 테이블';
COMMENT ON COLUMN leaflet_processing_logs.company IS '보험사명';
COMMENT ON COLUMN leaflet_processing_logs.year IS '적용 연도';
COMMENT ON COLUMN leaflet_processing_logs.month IS '적용 월';
COMMENT ON COLUMN leaflet_processing_logs.file_hash IS 'SHA-256 해시';
COMMENT ON COLUMN leaflet_processing_logs.points_extracted IS '추출된 마케팅 포인트 수';
COMMENT ON COLUMN leaflet_processing_logs.status IS '처리 상태 (success/failed/duplicate)';

-- ══════════════════════════════════════════════════════════════════════════════
-- 마이그레이션 완료
-- ══════════════════════════════════════════════════════════════════════════════
