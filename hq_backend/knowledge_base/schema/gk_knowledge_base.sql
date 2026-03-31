-- ══════════════════════════════════════════════════════════════════════════════
-- [Phase 5] RAG 전문 지식 벡터 DB 스키마
-- Supabase pgvector 확장 기능 활용
-- 작성일: 2026-03-30
-- 목적: 법률, 세무, 인수심사(Underwriting) 해설 텍스트 검색
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. pgvector 확장 활성화 (Supabase 대시보드에서 실행 또는 SQL Editor)
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 지식베이스 테이블 생성
CREATE TABLE IF NOT EXISTS gk_knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 문서 메타데이터
    document_name TEXT NOT NULL,                    -- 원본 문서명 (예: "법인_상담_자료.pdf")
    document_category TEXT NOT NULL,                -- 카테고리 (예: "법인컨설팅", "화재보험", "배상책임")
    chunk_index INTEGER NOT NULL,                   -- 청크 순서 (0부터 시작)
    
    -- 텍스트 컨텐츠
    content TEXT NOT NULL,                          -- 실제 텍스트 청크 (1000~2000자)
    content_length INTEGER NOT NULL,                -- 텍스트 길이
    
    -- 벡터 임베딩 (OpenAI text-embedding-3-small: 1536 차원)
    embedding vector(1536) NOT NULL,                -- pgvector 타입
    
    -- 메타데이터
    source_page INTEGER,                            -- 원본 PDF 페이지 번호
    keywords TEXT[],                                -- 키워드 배열 (검색 보조)
    
    -- [Phase 5 고도화] 파일 메타데이터 (중복 감지 및 버전 관리)
    file_hash TEXT,                                 -- 파일 SHA-256 해시 (중복 감지)
    file_size BIGINT,                               -- 파일 크기 (바이트)
    doc_date DATE,                                  -- 문서 날짜 (파일명 또는 수정일 기준)
    version TEXT,                                   -- 문서 버전 (파일명에서 추출)
    
    -- 시스템 필드
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 인덱스 최적화를 위한 제약
    CONSTRAINT unique_document_chunk UNIQUE (document_name, chunk_index)
);

-- 3. 벡터 유사도 검색 인덱스 (IVFFlat 알고리즘)
-- lists 파라미터: 데이터 포인트를 그룹화할 클러스터 수
-- 일반적으로 rows / 1000 권장 (최소 10, 최대 10000)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_embedding 
ON gk_knowledge_base 
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. 카테고리 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_category 
ON gk_knowledge_base (document_category);

-- 5. 문서명 검색 인덱스
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_document 
ON gk_knowledge_base (document_name);

-- 6. 전체 텍스트 검색 인덱스 (키워드 보조 검색)
-- 참고: Supabase는 기본적으로 'english' 설정만 지원
-- 한국어 전체 텍스트 검색이 필요한 경우 keywords 배열 컬럼 활용
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_content_gin 
ON gk_knowledge_base 
USING gin(to_tsvector('english', content));

-- 7. 파일 해시 인덱스 (중복 감지 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_file_hash 
ON gk_knowledge_base (file_hash);

-- 8. 문서 날짜 인덱스 (버전 관리 및 시계열 검색)
CREATE INDEX IF NOT EXISTS idx_gk_knowledge_doc_date 
ON gk_knowledge_base (doc_date);

-- 7. updated_at 자동 갱신 트리거
CREATE OR REPLACE FUNCTION update_gk_knowledge_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_gk_knowledge_updated_at
BEFORE UPDATE ON gk_knowledge_base
FOR EACH ROW
EXECUTE FUNCTION update_gk_knowledge_updated_at();

-- 10. RLS (Row Level Security) 정책 (선택적)
-- 모든 인증된 사용자가 읽기 가능, 관리자만 쓰기 가능
ALTER TABLE gk_knowledge_base ENABLE ROW LEVEL SECURITY;

CREATE POLICY "지식베이스 읽기 허용"
ON gk_knowledge_base
FOR SELECT
TO authenticated
USING (true);

CREATE POLICY "지식베이스 쓰기 제한"
ON gk_knowledge_base
FOR INSERT
TO authenticated
WITH CHECK (
    -- 관리자 role 체크 (실제 구현 시 수정 필요)
    auth.jwt() ->> 'role' = 'admin'
);

-- 11. 유사도 검색 함수 (헬퍼 함수)
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding vector(1536),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5,
    filter_category text DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_name text,
    document_category text,
    content text,
    source_page integer,
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
        gk.content,
        gk.source_page,
        1 - (gk.embedding <=> query_embedding) AS similarity
    FROM gk_knowledge_base gk
    WHERE 
        (filter_category IS NULL OR gk.document_category = filter_category)
        AND (1 - (gk.embedding <=> query_embedding)) > match_threshold
    ORDER BY gk.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 12. 통계 뷰 (모니터링용)
CREATE OR REPLACE VIEW gk_knowledge_stats AS
SELECT
    document_category,
    COUNT(*) AS chunk_count,
    COUNT(DISTINCT document_name) AS document_count,
    AVG(content_length) AS avg_chunk_length,
    MIN(created_at) AS first_ingested,
    MAX(updated_at) AS last_updated
FROM gk_knowledge_base
GROUP BY document_category;

-- 13. 샘플 데이터 삽입 (테스트용)
-- 실제 임베딩은 rag_ingestion.py에서 생성
INSERT INTO gk_knowledge_base (
    document_name,
    document_category,
    chunk_index,
    content,
    content_length,
    embedding,
    source_page,
    keywords
) VALUES (
    'test_document.pdf',
    '테스트',
    0,
    '이것은 테스트 문서입니다. pgvector 확장이 정상 작동하는지 확인합니다.',
    50,
    array_fill(0, ARRAY[1536])::vector,  -- 더미 임베딩 (모두 0)
    1,
    ARRAY['테스트', 'pgvector', '확인']
) ON CONFLICT (document_name, chunk_index) DO NOTHING;

-- 14. 권한 부여 (Supabase 서비스 role)
GRANT SELECT ON gk_knowledge_base TO anon, authenticated;
GRANT INSERT, UPDATE, DELETE ON gk_knowledge_base TO service_role;
GRANT EXECUTE ON FUNCTION search_knowledge_base TO authenticated;

-- ══════════════════════════════════════════════════════════════════════════════
-- 사용 예시
-- ══════════════════════════════════════════════════════════════════════════════

-- 1. 벡터 유사도 검색 (Python에서 생성한 임베딩 사용)
/*
SELECT * FROM search_knowledge_base(
    '[0.1, 0.2, ..., 0.5]'::vector(1536),  -- 쿼리 임베딩
    0.7,                                    -- 유사도 임계값
    5,                                      -- 상위 5개
    '법인컨설팅'                            -- 카테고리 필터
);
*/

-- 2. 카테고리별 통계 조회
-- SELECT * FROM gk_knowledge_stats;

-- 3. 특정 문서의 모든 청크 조회
-- SELECT * FROM gk_knowledge_base WHERE document_name = '법인_상담_자료.pdf' ORDER BY chunk_index;

-- 4. 키워드 기반 전체 텍스트 검색 (벡터 검색 보조)
-- 참고: 한국어 검색은 keywords 배열 컬럼 사용 권장
-- SELECT * FROM gk_knowledge_base WHERE to_tsvector('english', content) @@ to_tsquery('english', 'insurance & fire');
-- 또는 키워드 배열 검색: SELECT * FROM gk_knowledge_base WHERE '화재보험' = ANY(keywords);
