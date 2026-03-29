-- ════════════════════════════════════════════════════════════════════════════
-- [GP-BILLING] gk_members 크레딧 기반 과금 시스템 마이그레이션
-- 런칭 타임라인 기반 베타 ➡️ 무료체험 ➡️ 유료화 전환 체계
-- Supabase SQL Editor에서 실행 (기존 데이터 유지, 무중단)
-- ════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 1] 신규 컬럼 추가 및 타입 강제 변경
-- ──────────────────────────────────────────────────────────────────────────

ALTER TABLE public.gk_members
  ADD COLUMN IF NOT EXISTS plan_type              TEXT DEFAULT 'BASIC'
                                                   CHECK (plan_type IN ('BASIC', 'PRO')),
  ADD COLUMN IF NOT EXISTS status                 TEXT DEFAULT 'BETA'
                                                   CHECK (status IN ('BETA', 'TRIAL', 'PAID', 'EXPIRED')),
  ADD COLUMN IF NOT EXISTS current_credits        INTEGER DEFAULT 100,
  ADD COLUMN IF NOT EXISTS join_date              DATE DEFAULT CURRENT_DATE,
  ADD COLUMN IF NOT EXISTS monthly_renewal_date   DATE,
  ADD COLUMN IF NOT EXISTS trial_end_date         DATE;

-- 만약 join_date가 기존에 TEXT였다면 DATE로 타입 변경 (강제 형변환)
DO $$ BEGIN
  ALTER TABLE public.gk_members ALTER COLUMN join_date TYPE DATE USING join_date::DATE;
EXCEPTION WHEN OTHERS THEN 
  RAISE NOTICE 'join_date 타입 변경 스킵 또는 이미 DATE임';
END $$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 1.5] 외래 키 참조를 위한 UNIQUE 제약 조건 추가 (필수)
-- ──────────────────────────────────────────────────────────────────────────

DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'gk_members_user_id_unique') THEN
    ALTER TABLE public.gk_members ADD CONSTRAINT gk_members_user_id_unique UNIQUE (user_id);
  END IF;
END $$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 2] 기존 회원 데이터 초기화 (베타 사용자로 전환)
-- ──────────────────────────────────────────────────────────────────────────

-- 기존 회원들은 모두 베타 사용자로 간주 (2026년 8월 31일 이전 가입)
UPDATE public.gk_members
SET 
    plan_type = 'BASIC',
    status = 'BETA',
    current_credits = 100,
    join_date = COALESCE(join_date::DATE, CURRENT_DATE),
    monthly_renewal_date = (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month')::DATE
WHERE status IS NULL OR status = '';

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 3] 인덱스 생성 (크레딧 조회 최적화)
-- ──────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_gk_members_status
  ON public.gk_members(status) WHERE status IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_gk_members_join_date
  ON public.gk_members(join_date) WHERE join_date IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_gk_members_trial_end
  ON public.gk_members(trial_end_date) WHERE trial_end_date IS NOT NULL;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 4] 크레딧 히스토리 테이블 생성 (감사 추적용)
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.gk_credit_history (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL REFERENCES gk_members(user_id) ON DELETE CASCADE,
    action_type     TEXT NOT NULL CHECK (action_type IN ('DEDUCT', 'REFUND', 'RENEW', 'ADMIN_ADD', 'ADMIN_SUBTRACT')),
    amount          INTEGER NOT NULL,
    before_balance  INTEGER NOT NULL,
    after_balance   INTEGER NOT NULL,
    reason          TEXT,
    admin_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_gk_credit_history_user
  ON public.gk_credit_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gk_credit_history_action
  ON public.gk_credit_history(action_type, created_at DESC);

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 5] RLS 정책 (크레딧 조작 방지)
-- ──────────────────────────────────────────────────────────────────────────

ALTER TABLE gk_credit_history ENABLE ROW LEVEL SECURITY;

-- 서비스 롤은 모든 행 접근 허용 (앱 서버용)
DROP POLICY IF EXISTS "service_role_all_credit_history" ON public.gk_credit_history;
CREATE POLICY "service_role_all_credit_history"
    ON public.gk_credit_history FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- 일반 사용자는 자신의 히스토리만 읽기 가능
DROP POLICY IF EXISTS "users_read_own_credit_history" ON public.gk_credit_history;
CREATE POLICY "users_read_own_credit_history"
    ON public.gk_credit_history FOR SELECT
    USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 6] 헬퍼 함수: 크레딧 차감 및 히스토리 기록
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.deduct_user_credits(
    p_user_id TEXT,
    p_amount INTEGER,
    p_reason TEXT DEFAULT 'AI 기능 사용'
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_current_credits INTEGER;
    v_new_credits INTEGER;
    v_status TEXT;
BEGIN
    -- 사용자 정보 조회
    SELECT current_credits, status INTO v_current_credits, v_status
    FROM gk_members
    WHERE user_id = p_user_id;
    
    -- 사용자 없음
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', false,
            'message', '사용자를 찾을 수 없습니다.',
            'remaining', 0
        );
    END IF;
    
    -- TRIAL 상태는 크레딧 무제한
    IF v_status = 'TRIAL' THEN
        RETURN json_build_object(
            'success', true,
            'message', '무료체험 중 (크레딧 무제한)',
            'remaining', 999
        );
    END IF;
    
    -- EXPIRED 상태는 차단
    IF v_status = 'EXPIRED' THEN
        RETURN json_build_object(
            'success', false,
            'message', '무료체험 종료. 결제가 필요합니다.',
            'remaining', 0
        );
    END IF;
    
    -- 크레딧 부족 체크
    IF v_current_credits < p_amount THEN
        RETURN json_build_object(
            'success', false,
            'message', '이번 달 잔여 코인이 부족합니다. 다음 달 갱신을 기다리시거나 관리자에게 충전을 문의하세요.',
            'remaining', v_current_credits
        );
    END IF;
    
    -- 크레딧 차감
    v_new_credits := v_current_credits - p_amount;
    
    UPDATE gk_members
    SET current_credits = v_new_credits
    WHERE user_id = p_user_id;
    
    -- 히스토리 기록
    INSERT INTO gk_credit_history (user_id, action_type, amount, before_balance, after_balance, reason)
    VALUES (p_user_id, 'DEDUCT', p_amount, v_current_credits, v_new_credits, p_reason);
    
    RETURN json_build_object(
        'success', true,
        'message', '크레딧 차감 완료',
        'remaining', v_new_credits
    );
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 7] 헬퍼 함수: 월간 크레딧 갱신
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.renew_monthly_credits(
    p_user_id TEXT
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_status TEXT;
    v_plan_type TEXT;
    v_monthly_renewal_date DATE;
    v_new_credits INTEGER;
    v_old_credits INTEGER;
BEGIN
    -- 사용자 정보 조회
    SELECT status, plan_type, monthly_renewal_date, current_credits
    INTO v_status, v_plan_type, v_monthly_renewal_date, v_old_credits
    FROM gk_members
    WHERE user_id = p_user_id;
    
    -- 사용자 없음
    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '사용자를 찾을 수 없습니다.');
    END IF;
    
    -- TRIAL/EXPIRED는 갱신 대상 아님
    IF v_status IN ('TRIAL', 'EXPIRED') THEN
        RETURN json_build_object('success', false, 'message', '갱신 대상이 아닙니다.');
    END IF;
    
    -- 갱신일이 없으면 오늘로 설정 (최초 1회)
    IF v_monthly_renewal_date IS NULL THEN
        UPDATE gk_members
        SET monthly_renewal_date = CURRENT_DATE + INTERVAL '1 month'
        WHERE user_id = p_user_id;
        
        RETURN json_build_object('success', true, 'message', '갱신일 설정 완료');
    END IF;
    
    -- 갱신일 도달 체크
    IF CURRENT_DATE < v_monthly_renewal_date THEN
        RETURN json_build_object('success', false, 'message', '아직 갱신일이 아닙니다.');
    END IF;
    
    -- 플랜별 크레딧 지급량
    IF v_status = 'BETA' THEN
        v_new_credits := 100;
    ELSIF v_status = 'PAID' AND v_plan_type = 'PRO' THEN
        v_new_credits := 200;
    ELSIF v_status = 'PAID' AND v_plan_type = 'BASIC' THEN
        v_new_credits := 50;
    ELSE
        v_new_credits := 100;
    END IF;
    
    -- 크레딧 갱신
    UPDATE gk_members
    SET 
        current_credits = v_new_credits,
        monthly_renewal_date = v_monthly_renewal_date + INTERVAL '1 month'
    WHERE user_id = p_user_id;
    
    -- 히스토리 기록
    INSERT INTO gk_credit_history (user_id, action_type, amount, before_balance, after_balance, reason)
    VALUES (p_user_id, 'RENEW', v_new_credits, v_old_credits, v_new_credits, '월간 크레딧 갱신');
    
    RETURN json_build_object(
        'success', true,
        'message', '크레딧 갱신 완료',
        'new_credits', v_new_credits
    );
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 8] 헬퍼 함수: 트라이얼 만료 체크
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.check_trial_expiry(
    p_user_id TEXT
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    v_status TEXT;
    v_trial_end_date DATE;
BEGIN
    -- 사용자 정보 조회
    SELECT status, trial_end_date INTO v_status, v_trial_end_date
    FROM gk_members
    WHERE user_id = p_user_id;
    
    -- 사용자 없음
    IF NOT FOUND THEN
        RETURN json_build_object('success', false, 'message', '사용자를 찾을 수 없습니다.');
    END IF;
    
    -- TRIAL 상태가 아니면 체크 불필요
    IF v_status != 'TRIAL' THEN
        RETURN json_build_object('success', false, 'message', 'TRIAL 상태가 아닙니다.');
    END IF;
    
    -- 만료일 도달 체크
    IF CURRENT_DATE >= v_trial_end_date THEN
        UPDATE gk_members
        SET status = 'EXPIRED'
        WHERE user_id = p_user_id;
        
        RETURN json_build_object(
            'success', true,
            'message', '무료체험 종료 → EXPIRED 전환',
            'expired', true
        );
    END IF;
    
    RETURN json_build_object(
        'success', true,
        'message', '무료체험 진행 중',
        'expired', false,
        'days_left', v_trial_end_date - CURRENT_DATE
    );
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 9] 코멘트 추가
-- ──────────────────────────────────────────────────────────────────────────

COMMENT ON COLUMN gk_members.plan_type IS '플랜 유형 (BASIC/PRO)';
COMMENT ON COLUMN gk_members.status IS '회원 상태 (BETA/TRIAL/PAID/EXPIRED)';
COMMENT ON COLUMN gk_members.current_credits IS '잔여 크레딧 (코인)';
COMMENT ON COLUMN gk_members.join_date IS '가입일 (타임라인 판단 기준)';
COMMENT ON COLUMN gk_members.monthly_renewal_date IS '매월 크레딧 갱신일 (BETA/PAID 전용)';
COMMENT ON COLUMN gk_members.trial_end_date IS '무료체험 종료일 (TRIAL 전용)';

COMMENT ON TABLE gk_credit_history IS '[GP-BILLING] 크레딧 히스토리 테이블 (감사 추적용)';
COMMENT ON FUNCTION deduct_user_credits IS '[GP-BILLING] 크레딧 차감 및 히스토리 기록';
COMMENT ON FUNCTION renew_monthly_credits IS '[GP-BILLING] 월간 크레딧 갱신';
COMMENT ON FUNCTION check_trial_expiry IS '[GP-BILLING] 트라이얼 만료 체크 및 EXPIRED 전환';

-- ════════════════════════════════════════════════════════════════════════════
-- 설치 완료 메시지
-- ════════════════════════════════════════════════════════════════════════════

DO $$
BEGIN
    RAISE NOTICE '✅ [GP-BILLING] 크레딧 시스템 마이그레이션 완료';
    RAISE NOTICE '   - gk_members 테이블 확장 완료';
    RAISE NOTICE '   - gk_credit_history 테이블 생성 완료';
    RAISE NOTICE '   - 헬퍼 함수 3개 생성 완료';
    RAISE NOTICE '   - 기존 회원 BETA 전환 완료';
END $$;
