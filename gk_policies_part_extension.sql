-- ============================================================
-- gk_policies 테이블 확장 — Step 7 보험 3버킷 시스템 지원
-- [GP-STEP7] Goldkey AI Masters 2026
-- ============================================================

-- part 컬럼 추가 (A: Direct, B: External, C: Legacy)
ALTER TABLE gk_policies ADD COLUMN IF NOT EXISTS part TEXT DEFAULT 'A'
    CHECK (part IN ('A', 'B', 'C'));

-- 인덱스 추가 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_gk_policies_part ON gk_policies(part);

-- 주석 추가
COMMENT ON COLUMN gk_policies.part IS '보험 버킷 구분 (A: Direct 직접관리, B: External 타사, C: Legacy 해지/승환)';

-- 기존 데이터 마이그레이션 (모두 A로 초기화)
UPDATE gk_policies
SET part = 'A'
WHERE part IS NULL;
