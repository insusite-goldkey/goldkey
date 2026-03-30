-- ══════════════════════════════════════════════════════════════════════════════
-- [GP-SUBSCRIPTION] gk_members 테이블 다운그레이드 예약 컬럼 추가
-- 2026-03-30 신규 생성 - 유연한 다운그레이드 시스템
-- ══════════════════════════════════════════════════════════════════════════════

-- [§1] next_plan_type 컬럼 추가
ALTER TABLE gk_members
ADD COLUMN IF NOT EXISTS next_plan_type TEXT DEFAULT NULL;

-- [§2] 컬럼 설명
COMMENT ON COLUMN gk_members.next_plan_type IS 
'다음 결제일부터 적용될 플랜 타입 (예약 다운그레이드용). NULL=변경 없음, BASIC=베이직 전환 예약, PRO=프로 전환 예약';

-- [§3] 인덱스 추가 (월간 갱신 엔진 성능 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_members_next_plan_type 
ON gk_members(next_plan_type) 
WHERE next_plan_type IS NOT NULL;

-- [§4] 기존 데이터 마이그레이션 (필요 시)
-- 기존 사용자는 next_plan_type = NULL 유지 (변경 없음)

-- [§5] 사용 예시
/*
-- 프로 → 베이직 다운그레이드 예약
UPDATE gk_members 
SET next_plan_type = 'BASIC' 
WHERE user_id = 'user123' AND subscription_status = 'active';

-- 예약 취소
UPDATE gk_members 
SET next_plan_type = NULL 
WHERE user_id = 'user123';

-- 월간 갱신 시 적용
UPDATE gk_members 
SET 
    plan_type = next_plan_type,
    next_plan_type = NULL,
    subscription_status = 'active',
    subscription_expires_at = NOW() + INTERVAL '30 days'
WHERE next_plan_type IS NOT NULL 
  AND subscription_expires_at <= NOW();
*/
