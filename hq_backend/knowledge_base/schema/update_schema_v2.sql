-- ══════════════════════════════════════════════════════════════════════════════
-- [Phase 5 고도화] gk_knowledge_base 테이블 스키마 업데이트
-- 파일 메타데이터 컬럼 추가 (중복 감지 및 버전 관리)
-- 실행: Supabase SQL Editor에서 실행
-- 작성일: 2026-03-30
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. 파일 메타데이터 컬럼 추가
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS file_hash TEXT;
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS file_size BIGINT;
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS doc_date DATE;
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS version TEXT;
ALTER TABLE gk_knowledge_base ADD COLUMN IF NOT EXISTS folder_path TEXT;

-- 2. 파일 해시 인덱스 추가 (중복 감지 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_file_hash 
ON gk_knowledge_base (file_hash);

-- 3. 문서 날짜 인덱스 추가 (버전 관리 및 시계열 검색)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_doc_date 
ON gk_knowledge_base (doc_date);

-- 4. 폴더 경로 인덱스 추가 (하위 폴더별 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_folder_path 
ON gk_knowledge_base (folder_path);

-- 5. 스키마 업데이트 확인
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'gk_knowledge_base'
ORDER BY ordinal_position;

-- ══════════════════════════════════════════════════════════════════════════════
-- 실행 결과 확인
-- ══════════════════════════════════════════════════════════════════════════════
-- 다음 컬럼이 추가되어야 함:
-- - file_hash (TEXT)
-- - file_size (BIGINT)
-- - doc_date (DATE)
-- - version (TEXT)
-- - folder_path (TEXT)
-- ══════════════════════════════════════════════════════════════════════════════
