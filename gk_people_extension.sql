-- ============================================================
-- gk_people 테이블 확장 — Step 5 인텔리전스 CRM 지원
-- [GP-STEP5] Goldkey AI Masters 2026
-- ============================================================

-- 직업(job) 컬럼 추가
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS job TEXT;

-- 관심사(interests) 컬럼 추가 (JSON 또는 쉼표 구분 텍스트)
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS interests TEXT;

-- 현재 세일즈 단계(current_stage) 컬럼 추가 (1~12)
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS current_stage INTEGER DEFAULT 1 
    CHECK (current_stage BETWEEN 1 AND 12);

-- 마지막 접촉일(last_contact) 컬럼 추가 (YYYY-MM-DD)
ALTER TABLE gk_people ADD COLUMN IF NOT EXISTS last_contact TEXT;

-- 인덱스 추가 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_gk_people_job ON gk_people(job);
CREATE INDEX IF NOT EXISTS idx_gk_people_current_stage ON gk_people(current_stage);
CREATE INDEX IF NOT EXISTS idx_gk_people_last_contact ON gk_people(last_contact);

-- 주석 추가
COMMENT ON COLUMN gk_people.job IS '고객 직업 (예: 의사, 변호사, 자영업 등)';
COMMENT ON COLUMN gk_people.interests IS '고객 관심사 (예: 골프, 등산, 재테크 등)';
COMMENT ON COLUMN gk_people.current_stage IS '현재 세일즈 프로세스 단계 (1~12)';
COMMENT ON COLUMN gk_people.last_contact IS '마지막 접촉일 (YYYY-MM-DD)';
