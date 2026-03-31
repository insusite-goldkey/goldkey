-- ══════════════════════════════════════════════════════════════════════════════
-- 문서 해시 테이블 (중복 방지)
-- SHA-256 해시를 사용한 중복 문서 감지
-- 
-- 작성일: 2026-03-31
-- 목적: 동일한 리플릿이 중복 임베딩되지 않도록 방지
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. document_hashes 테이블 생성
CREATE TABLE IF NOT EXISTS document_hashes (
    id BIGSERIAL PRIMARY KEY,
    file_hash TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_path TEXT,
    company TEXT,
    reference_date TEXT,
    registered_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_document_hashes_file_hash ON document_hashes(file_hash);
CREATE INDEX IF NOT EXISTS idx_document_hashes_company ON document_hashes(company);
CREATE INDEX IF NOT EXISTS idx_document_hashes_reference_date ON document_hashes(reference_date);

-- 3. 주석 추가
COMMENT ON TABLE document_hashes IS '문서 해시 테이블 (중복 방지)';
COMMENT ON COLUMN document_hashes.file_hash IS 'SHA-256 해시 (64자 hex)';
COMMENT ON COLUMN document_hashes.file_name IS '파일명';
COMMENT ON COLUMN document_hashes.company IS '보험사명';
COMMENT ON COLUMN document_hashes.reference_date IS '기준연월 (YYYY-MM)';

-- ══════════════════════════════════════════════════════════════════════════════
-- 마이그레이션 완료
-- ══════════════════════════════════════════════════════════════════════════════
