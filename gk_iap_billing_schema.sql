-- ════════════════════════════════════════════════════════════════════════════
-- [GP-IAP] Google Play Billing 인앱 결제 검증 및 코인 충전 시스템
-- Goldkey AI Masters 2026 - 실시간 결제 검증 및 중복 방지
-- ════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 1] 결제 중복 방지 테이블 (gk_purchases)
-- ──────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.gk_purchases (
    purchase_token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    status TEXT DEFAULT 'COMPLETED',
    coins_granted INTEGER NOT NULL DEFAULT 0,
    platform TEXT DEFAULT 'google_play',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.gk_purchases IS 'Google Play 인앱 결제 영수증 중복 지급 방지 테이블';
COMMENT ON COLUMN public.gk_purchases.purchase_token IS 'Google Play 영수증 토큰 (중복 방지 PK)';
COMMENT ON COLUMN public.gk_purchases.user_id IS '결제한 회원 ID';
COMMENT ON COLUMN public.gk_purchases.product_id IS '구매한 상품 ID (예: basic_monthly, pro_monthly)';
COMMENT ON COLUMN public.gk_purchases.coins_granted IS '지급된 코인 수량';
COMMENT ON COLUMN public.gk_purchases.platform IS '결제 플랫폼 (google_play, apple_store)';

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gk_purchases_user_id 
    ON public.gk_purchases (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gk_purchases_product_id 
    ON public.gk_purchases (product_id);

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 2] 코인 충전 내역 테이블 (gk_credit_history) 확장
-- 참고: gk_members_credit_system.sql에서 이미 생성된 테이블에 컬럼 추가
-- ──────────────────────────────────────────────────────────────────────────

-- description 컬럼 추가 (기존 reason 컬럼과 별도)
ALTER TABLE public.gk_credit_history
    ADD COLUMN IF NOT EXISTS description TEXT;

-- purchase_token 컬럼 추가 (IAP 결제 영수증 연결용)
ALTER TABLE public.gk_credit_history
    ADD COLUMN IF NOT EXISTS purchase_token TEXT;

COMMENT ON COLUMN public.gk_credit_history.description IS '거래 상세 설명 (선택사항)';
COMMENT ON COLUMN public.gk_credit_history.purchase_token IS 'IAP 결제 시 영수증 토큰 (외래키)';

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_gk_credit_history_user_id 
    ON public.gk_credit_history (user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_gk_credit_history_action_type 
    ON public.gk_credit_history (action_type);

-- 외래키 제약 (선택사항) - 멱등성 보장
ALTER TABLE public.gk_credit_history
    DROP CONSTRAINT IF EXISTS fk_credit_history_purchase;

ALTER TABLE public.gk_credit_history
    ADD CONSTRAINT fk_credit_history_purchase
    FOREIGN KEY (purchase_token)
    REFERENCES public.gk_purchases(purchase_token)
    ON DELETE SET NULL;

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 3] 코인 충전 함수 (원자적 트랜잭션)
-- ──────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.grant_coins_from_iap(
    p_user_id TEXT,
    p_purchase_token TEXT,
    p_product_id TEXT,
    p_coins INTEGER
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_credits INTEGER;
    v_new_credits INTEGER;
    v_already_processed BOOLEAN;
BEGIN
    -- 1. 중복 결제 확인
    SELECT EXISTS(
        SELECT 1 FROM public.gk_purchases 
        WHERE purchase_token = p_purchase_token
    ) INTO v_already_processed;

    IF v_already_processed THEN
        RETURN json_build_object(
            'success', false,
            'error', 'DUPLICATE_PURCHASE',
            'message', '이미 처리된 결제입니다.'
        );
    END IF;

    -- 2. 현재 코인 조회
    SELECT current_credits INTO v_current_credits
    FROM public.gk_members
    WHERE user_id = p_user_id;

    IF v_current_credits IS NULL THEN
        RETURN json_build_object(
            'success', false,
            'error', 'USER_NOT_FOUND',
            'message', '사용자를 찾을 수 없습니다.'
        );
    END IF;

    -- 3. 코인 충전
    v_new_credits := v_current_credits + p_coins;

    UPDATE public.gk_members
    SET current_credits = v_new_credits,
        updated_at = NOW()
    WHERE user_id = p_user_id;

    -- 4. 결제 기록 저장
    INSERT INTO public.gk_purchases (
        purchase_token,
        user_id,
        product_id,
        coins_granted,
        status,
        created_at
    ) VALUES (
        p_purchase_token,
        p_user_id,
        p_product_id,
        p_coins,
        'COMPLETED',
        NOW()
    );

    -- 5. 코인 내역 기록
    INSERT INTO public.gk_credit_history (
        user_id,
        action_type,
        amount,
        before_balance,
        after_balance,
        reason,
        purchase_token,
        created_at
    ) VALUES (
        p_user_id,
        'IAP_RECHARGE',
        p_coins,
        v_current_credits,
        v_new_credits,
        format('인앱 결제 충전: %s', p_product_id),
        p_purchase_token,
        NOW()
    );

    -- 6. 성공 응답
    RETURN json_build_object(
        'success', true,
        'coins_granted', p_coins,
        'balance_before', v_current_credits,
        'balance_after', v_new_credits,
        'message', format('%s 코인이 충전되었습니다!', p_coins)
    );

EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', false,
            'error', 'INTERNAL_ERROR',
            'message', SQLERRM
        );
END;
$$;

COMMENT ON FUNCTION public.grant_coins_from_iap IS '인앱 결제 검증 후 코인 충전 (중복 방지 포함)';

-- ──────────────────────────────────────────────────────────────────────────
-- [STEP 4] 테스트 데이터 (개발용)
-- ──────────────────────────────────────────────────────────────────────────

-- 테스트용 결제 시뮬레이션 (실제 운영 시 삭제)
/*
SELECT public.grant_coins_from_iap(
    'test_user_001',
    'TEST_TOKEN_' || gen_random_uuid()::TEXT,
    'basic_monthly',
    50
);
*/
