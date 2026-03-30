-- ════════════════════════════════════════════════════════════════════════════
-- [GP-EXPIRY] 보험 만기 자동 관리 시스템 스키마 확장
-- Goldkey AI Masters 2026 - 단기/갱신형 보험 만기 추적 자동화
-- ════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 0] gk_schedules 테이블 필수 컬럼 확인 및 추가
-- ──────────────────────────────────────────────────────────────────────────

-- gk_schedules 테이블에 필수 컬럼이 없을 경우 추가
ALTER TABLE public.gk_schedules
  ADD COLUMN IF NOT EXISTS agent_id TEXT,
  ADD COLUMN IF NOT EXISTS person_id TEXT,
  ADD COLUMN IF NOT EXISTS policy_id TEXT,
  ADD COLUMN IF NOT EXISTS customer_name TEXT,
  ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general',
  ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 1] gk_policies 테이블 확장 - 보험 세부 유형 및 기간 정보
-- ──────────────────────────────────────────────────────────────────────────

-- agent_id: 담당 설계사 ID (기존 테이블에 없을 경우 추가)
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS agent_id TEXT;

-- sub_type: 자동차, 화재, 공장화재, 영업배상, 일반손해 등 세부 분류
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS sub_type TEXT;

-- start_date: 보험 개시일 (YYYYMMDD 형식)
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS start_date TEXT;

-- is_deleted: 소프트 삭제 플래그 (기존 테이블에 없을 경우 추가)
ALTER TABLE public.gk_policies
  ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 기존 contract_date를 start_date로 복사 (최초 1회 마이그레이션)
UPDATE public.gk_policies
SET start_date = contract_date
WHERE start_date IS NULL AND contract_date IS NOT NULL;

-- expiry_date 인덱스 추가 (만기일 기준 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_expiry_date
  ON public.gk_policies (expiry_date, agent_id);

-- sub_type 인덱스 추가 (보험 유형별 검색 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_sub_type
  ON public.gk_policies (sub_type, agent_id);

-- is_deleted 인덱스 추가 (삭제되지 않은 데이터 필터링 최적화)
CREATE INDEX IF NOT EXISTS idx_gk_policies_is_deleted
  ON public.gk_policies (is_deleted, agent_id)
  WHERE is_deleted = FALSE;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 2] 보험 만기 태그 매핑 함수
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.get_expiry_tag(p_sub_type TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  RETURN CASE
    WHEN p_sub_type ILIKE '%자동차%' THEN '#자동차보험만기'
    WHEN p_sub_type ILIKE '%화재%' AND p_sub_type ILIKE '%공장%' THEN '#공장화재만기'
    WHEN p_sub_type ILIKE '%화재%' THEN '#화재보험만기'
    WHEN p_sub_type ILIKE '%배상%' THEN '#영업배상만기'
    WHEN p_sub_type ILIKE '%특종%' THEN '#특종보험만기'
    ELSE '#보험만기'
  END;
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 3] 보험 만기 자동 일정 생성 함수
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.create_expiry_schedule(
  p_policy_id UUID,
  p_agent_id TEXT,
  p_person_id TEXT,
  p_customer_name TEXT,
  p_sub_type TEXT,
  p_expiry_date TEXT,
  p_product_name TEXT
)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_tag TEXT;
  v_title TEXT;
  v_memo TEXT;
  v_schedule_id UUID;
BEGIN
  -- 만기일이 없으면 종료
  IF p_expiry_date IS NULL OR p_expiry_date = '' THEN
    RETURN;
  END IF;

  -- 태그 생성
  v_tag := get_expiry_tag(p_sub_type);
  
  -- 일정 제목 생성
  IF p_customer_name IS NOT NULL AND p_customer_name != '' THEN
    v_title := format('[만기관리] 🔔 %s 고객님 %s 만기 안내', p_customer_name, COALESCE(p_sub_type, '보험'));
  ELSE
    v_title := format('[만기관리] 🔔 %s 만기 안내', COALESCE(p_sub_type, '보험'));
  END IF;

  -- 메모 생성
  v_memo := format('상품명: %s | 만기일: %s | 재가입 상담 필요 | %s',
    COALESCE(p_product_name, '미등록'),
    p_expiry_date,
    v_tag
  );

  -- 일정 ID 생성
  v_schedule_id := gen_random_uuid();

  -- gk_schedules 테이블에 만기일 일정 등록
  INSERT INTO public.gk_schedules (
    id,
    agent_id,
    person_id,
    policy_id,
    title,
    date,
    start_time,
    memo,
    category,
    tags,
    customer_name,
    is_deleted,
    created_at,
    updated_at
  ) VALUES (
    v_schedule_id,
    p_agent_id,
    p_person_id,
    p_policy_id::TEXT,
    v_title,
    p_expiry_date,
    '09:00',
    v_memo,
    'expiry',
    ARRAY[v_tag],
    p_customer_name,
    FALSE,
    NOW(),
    NOW()
  )
  ON CONFLICT DO NOTHING;

END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 4] 기존 보험 데이터에 대한 만기 일정 자동 생성 (최초 1회 실행)
-- ──────────────────────────────────────────────────────────────────────────

-- 주의: 기존 데이터에 잘못된 날짜 형식이 있을 수 있어 주석 처리
-- 신규 데이터는 STEP 5의 트리거로 자동 처리됩니다.
-- 기존 데이터를 마이그레이션하려면 수동으로 expiry_date를 YYYYMMDD 형식으로 정리한 후
-- 아래 주석을 해제하고 실행하세요.

/*
DO $$
DECLARE
  r RECORD;
  v_person_id TEXT;
  v_customer_name TEXT;
BEGIN
  FOR r IN 
    SELECT 
      p.id AS policy_id,
      p.agent_id,
      p.sub_type,
      p.expiry_date,
      p.product_name
    FROM public.gk_policies p
    WHERE p.expiry_date IS NOT NULL
      AND p.expiry_date != ''
      AND LENGTH(p.expiry_date) = 8  -- YYYYMMDD 형식 (8자리) 검증
      AND p.expiry_date ~ '^\d{8}$'  -- 숫자 8자리 정규식 검증
      AND p.is_deleted = FALSE
      AND NOT EXISTS (
        SELECT 1 FROM public.gk_schedules s
        WHERE s.policy_id = p.id::TEXT
          AND s.category = 'expiry'
          AND s.is_deleted = FALSE
      )
  LOOP
    -- 계약자 정보 조회 (gk_policy_roles 조인)
    SELECT pr.person_id, pp.name
    INTO v_person_id, v_customer_name
    FROM public.gk_policy_roles pr
    JOIN public.gk_people pp ON pr.person_id = pp.id::TEXT
    WHERE pr.policy_id = r.policy_id
      AND pr.role = '계약자'
      AND pr.is_deleted = FALSE
    LIMIT 1;

    -- 계약자 정보가 있으면 일정 생성
    IF v_person_id IS NOT NULL THEN
      PERFORM create_expiry_schedule(
        r.policy_id,
        r.agent_id,
        v_person_id,
        v_customer_name,
        r.sub_type,
        r.expiry_date,
        r.product_name
      );
    END IF;
  END LOOP;
END $$;
*/

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 5] 트리거: 신규 보험 계약 입력 시 자동 만기 일정 생성
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.trg_auto_create_expiry_schedule()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_person_id TEXT;
  v_customer_name TEXT;
BEGIN
  -- 만기일이 없으면 종료
  IF NEW.expiry_date IS NULL OR NEW.expiry_date = '' THEN
    RETURN NEW;
  END IF;

  -- 계약자 정보 조회
  SELECT pr.person_id, pp.name
  INTO v_person_id, v_customer_name
  FROM public.gk_policy_roles pr
  JOIN public.gk_people pp ON pr.person_id = pp.id::TEXT
  WHERE pr.policy_id = NEW.id
    AND pr.role = '계약자'
    AND pr.is_deleted = FALSE
  LIMIT 1;

  -- 계약자 정보가 있으면 일정 생성
  IF v_person_id IS NOT NULL THEN
    PERFORM create_expiry_schedule(
      NEW.id,
      NEW.agent_id,
      v_person_id,
      v_customer_name,
      NEW.sub_type,
      NEW.expiry_date,
      NEW.product_name
    );
  END IF;

  RETURN NEW;
END;
$$;

-- 트리거 등록 (INSERT 시에만 실행)
DROP TRIGGER IF EXISTS trg_gk_policies_expiry_schedule ON public.gk_policies;
CREATE TRIGGER trg_gk_policies_expiry_schedule
  AFTER INSERT ON public.gk_policies
  FOR EACH ROW
  EXECUTE FUNCTION trg_auto_create_expiry_schedule();

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 6] 만기 알림 대상자 조회 뷰 (D-28일, D-14일)
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW public.v_expiry_alerts AS
SELECT
  s.id,
  s.agent_id,
  s.person_id,
  s.policy_id,
  s.customer_name,
  s.title,
  s.date AS expiry_date,
  s.tags,
  s.memo,
  p.sub_type,
  p.product_name,
  p.insurance_company,
  -- D-Day 계산
  (s.date::DATE - CURRENT_DATE) AS days_until_expiry,
  -- 알림 우선순위 (D-28 = 1, D-14 = 2)
  CASE
    WHEN (s.date::DATE - CURRENT_DATE) BETWEEN 26 AND 30 THEN 1
    WHEN (s.date::DATE - CURRENT_DATE) BETWEEN 12 AND 16 THEN 2
    ELSE 0
  END AS alert_priority
FROM public.gk_schedules s
LEFT JOIN public.gk_policies p ON s.policy_id::UUID = p.id
WHERE s.category = 'expiry'
  AND s.is_deleted = FALSE
  AND s.date IS NOT NULL
  AND (s.date::DATE - CURRENT_DATE) BETWEEN 0 AND 30  -- 만기일 30일 전부터 표시
ORDER BY s.date ASC;

COMMENT ON VIEW public.v_expiry_alerts IS '보험 만기 알림 대상자 조회 뷰 (D-28일, D-14일 우선 표시)';
