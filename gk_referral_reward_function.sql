-- ══════════════════════════════════════════════════════════════════════════════
-- Goldkey AI Masters 2026 — 소개자 리워드 지급 함수
-- [GP-REFERRAL] 소개자 검증 및 100코인 리워드 지급
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
-- [함수] grant_referral_reward: 소개자에게 100코인 지급 및 referral_count 증가
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.grant_referral_reward(
    p_referrer_id TEXT,
    p_new_member_id TEXT
)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_current_credits INTEGER;
    v_referral_count INTEGER;
    v_result JSONB;
BEGIN
    -- 소개자의 현재 크레딧 및 소개 횟수 조회
    SELECT current_credits, COALESCE(referral_count, 0)
    INTO v_current_credits, v_referral_count
    FROM public.gk_members
    WHERE user_id = p_referrer_id;
    
    -- 소개자가 존재하지 않으면 에러 반환
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', '소개자를 찾을 수 없습니다'
        );
    END IF;
    
    -- 소개자에게 100코인 지급 + referral_count 증가
    UPDATE public.gk_members
    SET 
        current_credits = current_credits + 100,
        referral_count = COALESCE(referral_count, 0) + 1,
        updated_at = NOW()
    WHERE user_id = p_referrer_id;
    
    -- gk_credit_history에 리워드 지급 기록 추가
    INSERT INTO public.gk_credit_history (
        user_id,
        action_type,
        amount,
        reason,
        description,
        created_at
    ) VALUES (
        p_referrer_id,
        'referral_reward',
        100,
        '신규 회원 소개 리워드',
        '신규 회원 ' || p_new_member_id || ' 소개로 100코인 지급',
        NOW()
    );
    
    -- 성공 결과 반환
    v_result := jsonb_build_object(
        'success', true,
        'message', '소개 리워드 100코인이 지급되었습니다',
        'referrer_id', p_referrer_id,
        'new_credits', v_current_credits + 100,
        'total_referrals', v_referral_count + 1
    );
    
    RETURN v_result;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN jsonb_build_object(
            'success', false,
            'message', '리워드 지급 중 오류 발생: ' || SQLERRM
        );
END;
$$;

-- ──────────────────────────────────────────────────────────────────────────────
-- [권한 설정] service_role에게 함수 실행 권한 부여
-- ──────────────────────────────────────────────────────────────────────────────

GRANT EXECUTE ON FUNCTION public.grant_referral_reward(TEXT, TEXT) TO service_role;

-- ──────────────────────────────────────────────────────────────────────────────
-- [테스트 쿼리] 함수 동작 확인
-- ──────────────────────────────────────────────────────────────────────────────

-- 테스트 예시 (실제 user_id로 교체 필요):
-- SELECT public.grant_referral_reward('referrer_user_id_here', 'new_member_user_id_here');
