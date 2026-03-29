-- ════════════════════════════════════════════════════════════════════════════
-- [STEP 4.5] gk_policies 테이블 status 컬럼 추가
-- 계약 해지/유지 상태 관리용
-- Supabase SQL Editor에서 실행 (선택 사항)
-- ════════════════════════════════════════════════════════════════════════════

-- status 컬럼 추가 (기본값: active)
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';

-- status 인덱스 추가 (해지 계약 조회 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_status
  ON public.gk_policies(status) WHERE status IS NOT NULL;

-- status 값 제약 조건 (선택 사항)
-- ALTER TABLE public.gk_policies
--   ADD CONSTRAINT chk_gk_policies_status 
--   CHECK (status IN ('active', 'cancelled', 'terminated'));
