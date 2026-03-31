-- ══════════════════════════════════════════════════════════════════════════════
-- RAG Knowledge Base Version Control (버전 관리)
-- 구버전 카탈로그 데이터 격리 및 Hot-Swap 로직
-- 
-- 작성일: 2026-03-31
-- 목적: 과거 자료가 섞여서 오답이 나가는 것을 방지
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. is_active 컬럼 추가 (기본값: true)
ALTER TABLE gk_knowledge_base 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- 2. version_date 컬럼 추가 (버전 관리용)
ALTER TABLE gk_knowledge_base 
ADD COLUMN IF NOT EXISTS version_date DATE DEFAULT CURRENT_DATE;

-- 3. archived_at 컬럼 추가 (아카이브 시점 기록)
ALTER TABLE gk_knowledge_base 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ;

-- 4. is_active 인덱스 생성 (검색 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_base_is_active 
ON gk_knowledge_base(is_active);

-- 5. company + reference_date + is_active 복합 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_base_company_date_active 
ON gk_knowledge_base(company, reference_date, is_active);

-- 6. version_date 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_base_version_date 
ON gk_knowledge_base(version_date);

-- 7. 기존 데이터 is_active=true 설정 (마이그레이션)
UPDATE gk_knowledge_base 
SET is_active = true 
WHERE is_active IS NULL;

-- 8. search_knowledge_base 함수 업데이트 (is_active 필터 추가)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    filter_company text DEFAULT NULL,
    filter_reference_date text DEFAULT NULL
)
RETURNS TABLE (
    id bigint,
    document_name text,
    document_category text,
    chunk_index int,
    content text,
    content_length int,
    company text,
    reference_date text,
    version_date date,
    is_active boolean,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        gk.id,
        gk.document_name,
        gk.document_category,
        gk.chunk_index,
        gk.content,
        gk.content_length,
        gk.company,
        gk.reference_date,
        gk.version_date,
        gk.is_active,
        1 - (gk.embedding <=> query_embedding) AS similarity
    FROM gk_knowledge_base gk
    WHERE 
        gk.is_active = true  -- 활성 데이터만 검색 (Hot-Swap 핵심)
        AND (filter_company IS NULL OR gk.company = filter_company)
        AND (filter_reference_date IS NULL OR gk.reference_date = filter_reference_date)
    ORDER BY gk.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 9. 구버전 아카이브 함수 생성
CREATE OR REPLACE FUNCTION archive_old_versions(
    target_company text,
    target_reference_date text
)
RETURNS TABLE (
    archived_count int,
    archived_documents text[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_archived_count int;
    v_archived_documents text[];
BEGIN
    -- 동일 보험사의 이전 버전 데이터를 is_active=false로 변경
    WITH archived AS (
        UPDATE gk_knowledge_base
        SET 
            is_active = false,
            archived_at = NOW()
        WHERE 
            company = target_company
            AND reference_date < target_reference_date
            AND is_active = true
        RETURNING document_name
    )
    SELECT 
        COUNT(*)::int,
        ARRAY_AGG(DISTINCT document_name)
    INTO v_archived_count, v_archived_documents
    FROM archived;
    
    RETURN QUERY SELECT v_archived_count, v_archived_documents;
END;
$$;

-- 10. 버전 통계 조회 함수
CREATE OR REPLACE FUNCTION get_version_statistics()
RETURNS TABLE (
    company text,
    reference_date text,
    is_active boolean,
    document_count bigint,
    chunk_count bigint,
    latest_version_date date
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        gk.company,
        gk.reference_date,
        gk.is_active,
        COUNT(DISTINCT gk.document_name) AS document_count,
        COUNT(*) AS chunk_count,
        MAX(gk.version_date) AS latest_version_date
    FROM gk_knowledge_base gk
    GROUP BY gk.company, gk.reference_date, gk.is_active
    ORDER BY gk.company, gk.reference_date DESC, gk.is_active DESC;
END;
$$;

-- 11. 활성 버전 조회 함수
CREATE OR REPLACE FUNCTION get_active_versions()
RETURNS TABLE (
    company text,
    reference_date text,
    document_count bigint,
    chunk_count bigint,
    version_date date
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        gk.company,
        gk.reference_date,
        COUNT(DISTINCT gk.document_name) AS document_count,
        COUNT(*) AS chunk_count,
        MAX(gk.version_date) AS version_date
    FROM gk_knowledge_base gk
    WHERE gk.is_active = true
    GROUP BY gk.company, gk.reference_date
    ORDER BY gk.company, gk.reference_date DESC;
END;
$$;

-- 12. 주석 추가
COMMENT ON COLUMN gk_knowledge_base.is_active IS '활성 상태 (true: 검색 대상, false: 아카이브)';
COMMENT ON COLUMN gk_knowledge_base.version_date IS '버전 날짜 (업로드 날짜)';
COMMENT ON COLUMN gk_knowledge_base.archived_at IS '아카이브 시점';
COMMENT ON FUNCTION search_knowledge_base IS 'RAG 벡터 검색 (is_active=true만 검색)';
COMMENT ON FUNCTION archive_old_versions IS '구버전 데이터 아카이브 (Hot-Swap)';
COMMENT ON FUNCTION get_version_statistics IS '버전별 통계 조회';
COMMENT ON FUNCTION get_active_versions IS '활성 버전 목록 조회';

-- ══════════════════════════════════════════════════════════════════════════════
-- 마이그레이션 완료
-- ══════════════════════════════════════════════════════════════════════════════
