-- ════════════════════════════════════════════════════════════════════════════
-- gk_schedules 스마트 캘린더 엔진 스키마 마이그레이션
-- [GP-CALENDAR] Goldkey AI Masters 2026
-- Supabase SQL Editor에서 실행 (기존 데이터 유지, 무중단)
-- ════════════════════════════════════════════════════════════════════════════

-- 기존 테이블에 신규 컬럼 추가 (IF NOT EXISTS — 중복 실행 안전)
ALTER TABLE public.gk_schedules
  ADD COLUMN IF NOT EXISTS end_time      TEXT,
  ADD COLUMN IF NOT EXISTS end_date      TEXT,
  ADD COLUMN IF NOT EXISTS customer_name TEXT,
  ADD COLUMN IF NOT EXISTS body          TEXT,
  ADD COLUMN IF NOT EXISTS policy_id     TEXT;

-- 해시태그 전용 TEXT ARRAY 컬럼 (검색 성능용)
ALTER TABLE public.gk_schedules
  ADD COLUMN IF NOT EXISTS tags          TEXT[] DEFAULT '{}';

-- GIN 인덱스 — tags 배열 고속 검색
CREATE INDEX IF NOT EXISTS idx_gk_schedules_tags
  ON public.gk_schedules USING GIN (tags);

-- 기존 memo 컬럼에서 해시태그 마이그레이션 (최초 1회 실행)
-- (정규표현식으로 #\w+ 추출 → tags 배열에 적재)
UPDATE public.gk_schedules
SET tags = ARRAY(
  SELECT DISTINCT m[1]
  FROM regexp_matches(COALESCE(memo, ''), '#\w+', 'g') AS m
)
WHERE tags = '{}' OR tags IS NULL;

-- customer_name: gk_people 조인 fallback 채우기
UPDATE public.gk_schedules s
SET customer_name = p.name
FROM public.gk_people p
WHERE s.person_id = p.person_id
  AND (s.customer_name IS NULL OR s.customer_name = '');

-- 날짜+설계사 복합 인덱스 (월간 뷰 쿼리 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_schedules_agent_date
  ON public.gk_schedules (agent_id, date, is_deleted);

-- [STEP 4.5] 계약-일정 연결 인덱스 (중도 해지 시 미래 일정 삭제 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_schedules_policy_id
  ON public.gk_schedules (policy_id, date) WHERE policy_id IS NOT NULL;

-- ── RLS (Row Level Security) ────────────────────────────────────────────────
-- 기존 RLS가 없을 경우에만 활성화
ALTER TABLE public.gk_schedules ENABLE ROW LEVEL SECURITY;

-- 설계사 본인 데이터만 접근 허용
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename='gk_schedules' AND policyname='agent_own_schedules'
  ) THEN
    CREATE POLICY agent_own_schedules ON public.gk_schedules
      USING (agent_id = auth.uid()::text);
  END IF;
END$$;
