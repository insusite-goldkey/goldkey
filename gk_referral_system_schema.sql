-- ══════════════════════════════════════════════════════════════════════════════
-- Goldkey AI Masters 2026 — 추천인 마케팅 시스템 DB 스키마
-- 목적: 바이럴 마케팅 및 사용자 락인(Lock-in)
-- ══════════════════════════════════════════════════════════════════════════════

-- ──────────────────────────────────────────────────────────────────────────────
-- [1] gk_members 테이블에 referrer_id 컬럼 추가
-- ──────────────────────────────────────────────────────────────────────────────

-- referrer_id: 소개자의 user_id 또는 추천 코드
ALTER TABLE gk_members 
ADD COLUMN IF NOT EXISTS referrer_id TEXT;

-- 인덱스 추가 (추천인 조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_gk_members_referrer_id 
ON gk_members(referrer_id);

-- 코멘트 추가
COMMENT ON COLUMN gk_members.referrer_id IS '소개자 ID 또는 추천 코드 (바이럴 마케팅)';

-- ──────────────────────────────────────────────────────────────────────────────
-- [2] gk_members 테이블에 monthly_renewal_date 컬럼 추가
-- ──────────────────────────────────────────────────────────────────────────────

-- monthly_renewal_date: 다음 구독 갱신일 (코인으로 연장 가능)
ALTER TABLE gk_members 
ADD COLUMN IF NOT EXISTS monthly_renewal_date TIMESTAMPTZ;

-- 기본값 설정 (기존 회원은 현재 날짜 + 30일)
UPDATE gk_members 
SET monthly_renewal_date = NOW() + INTERVAL '30 days'
WHERE monthly_renewal_date IS NULL;

-- 코멘트 추가
COMMENT ON COLUMN gk_members.monthly_renewal_date IS '다음 구독 갱신일 (코인으로 연장 가능)';

-- ──────────────────────────────────────────────────────────────────────────────
-- [3] gk_credit_history 테이블 action_type 열거형 확장
-- ──────────────────────────────────────────────────────────────────────────────

-- 기존 transaction_type에 새로운 타입 추가
-- REFERRAL_REWARD: 추천인 보상 (+100코인)
-- SUBSCRIPTION_EXTENSION: 코인으로 구독 연장 (-120코인)

-- 참고: gk_credit_history 테이블의 transaction_type은 이미 TEXT 타입이므로
-- 새로운 값을 바로 사용할 수 있음 (열거형 확장 불필요)

-- ──────────────────────────────────────────────────────────────────────────────
-- [4] 추천인 보상 지급 함수 (7일 후 자동 지급)
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION grant_referral_reward(
    p_referrer_id TEXT,
    p_new_member_id TEXT,
    p_new_member_name TEXT
) RETURNS JSONB AS $$
DECLARE
    v_reward_coins INTEGER := 100;
    v_current_credits INTEGER;
    v_new_balance INTEGER;
    v_result JSONB;
BEGIN
    -- 소개자가 존재하는지 확인
    IF NOT EXISTS (SELECT 1 FROM gk_members WHERE id = p_referrer_id) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Referrer not found'
        );
    END IF;
    
    -- 이미 보상을 받았는지 확인 (중복 지급 방지)
    IF EXISTS (
        SELECT 1 FROM gk_credit_history 
        WHERE user_id = p_referrer_id 
        AND transaction_type = 'REFERRAL_REWARD'
        AND reason LIKE '%' || p_new_member_id || '%'
    ) THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Reward already granted'
        );
    END IF;
    
    -- 소개자의 현재 코인 조회
    SELECT current_credits INTO v_current_credits
    FROM gk_members
    WHERE id = p_referrer_id;
    
    -- 새로운 잔액 계산
    v_new_balance := COALESCE(v_current_credits, 0) + v_reward_coins;
    
    -- 소개자 코인 증가
    UPDATE gk_members
    SET current_credits = v_new_balance,
        updated_at = NOW()
    WHERE id = p_referrer_id;
    
    -- 크레딧 히스토리 기록
    INSERT INTO gk_credit_history (
        user_id,
        action_type,
        amount,
        before_balance,
        after_balance,
        reason,
        created_at
    ) VALUES (
        p_referrer_id,
        'REFERRAL_REWARD',
        v_reward_coins,
        v_current_credits,
        v_new_balance,
        '추천인 보상: ' || p_new_member_name || ' 님 가입 (ID: ' || p_new_member_id || ')',
        NOW()
    );
    
    -- 결과 반환
    v_result := jsonb_build_object(
        'success', true,
        'referrer_id', p_referrer_id,
        'reward_coins', v_reward_coins,
        'new_balance', v_new_balance,
        'new_member_id', p_new_member_id,
        'new_member_name', p_new_member_name
    );
    
    RETURN v_result;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 함수 코멘트
COMMENT ON FUNCTION grant_referral_reward IS '추천인 보상 지급 함수 (+100코인)';

-- ──────────────────────────────────────────────────────────────────────────────
-- [5] 코인으로 구독 연장 함수
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION extend_subscription_with_coins(
    p_user_id TEXT,
    p_plan_type TEXT DEFAULT 'basic'
) RETURNS JSONB AS $$
DECLARE
    v_required_coins INTEGER;
    v_current_credits INTEGER;
    v_new_balance INTEGER;
    v_current_renewal_date TIMESTAMPTZ;
    v_new_renewal_date TIMESTAMPTZ;
    v_result JSONB;
BEGIN
    -- 플랜별 필요 코인 설정
    v_required_coins := CASE 
        WHEN p_plan_type = 'basic' THEN 120
        WHEN p_plan_type = 'pro' THEN 360
        ELSE 120
    END;
    
    -- 사용자의 현재 코인 조회
    SELECT current_credits, monthly_renewal_date
    INTO v_current_credits, v_current_renewal_date
    FROM gk_members
    WHERE id = p_user_id;
    
    -- 사용자 존재 확인
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'User not found'
        );
    END IF;
    
    -- 코인 부족 확인
    IF COALESCE(v_current_credits, 0) < v_required_coins THEN
        RETURN jsonb_build_object(
            'success', false,
            'error', 'Insufficient credits',
            'required', v_required_coins,
            'current', COALESCE(v_current_credits, 0)
        );
    END IF;
    
    -- 새로운 잔액 계산
    v_new_balance := v_current_credits - v_required_coins;
    
    -- 새로운 갱신일 계산 (현재 갱신일 + 30일, 없으면 오늘 + 30일)
    IF v_current_renewal_date IS NULL THEN
        v_new_renewal_date := NOW() + INTERVAL '30 days';
    ELSE
        v_new_renewal_date := v_current_renewal_date + INTERVAL '30 days';
    END IF;
    
    -- 코인 차감 및 갱신일 연장
    UPDATE gk_members
    SET current_credits = v_new_balance,
        monthly_renewal_date = v_new_renewal_date,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    -- 크레딧 히스토리 기록
    INSERT INTO gk_credit_history (
        user_id,
        action_type,
        amount,
        before_balance,
        after_balance,
        reason,
        created_at
    ) VALUES (
        p_user_id,
        'SUBSCRIPTION_EXTENSION',
        -v_required_coins,
        v_current_credits,
        v_new_balance,
        '코인으로 구독 연장 (' || UPPER(p_plan_type) || ' 플랜 1개월)',
        NOW()
    );
    
    -- 결과 반환
    v_result := jsonb_build_object(
        'success', true,
        'user_id', p_user_id,
        'plan_type', p_plan_type,
        'coins_deducted', v_required_coins,
        'new_balance', v_new_balance,
        'new_renewal_date', v_new_renewal_date,
        'extended_days', 30
    );
    
    RETURN v_result;
    
EXCEPTION WHEN OTHERS THEN
    RETURN jsonb_build_object(
        'success', false,
        'error', SQLERRM
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 함수 코멘트
COMMENT ON FUNCTION extend_subscription_with_coins IS '코인으로 구독 기간 연장 함수 (베이직: 120코인, 프로: 360코인)';

-- ──────────────────────────────────────────────────────────────────────────────
-- [6] 추천인 리워드 현황 조회 뷰
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW v_referral_rewards AS
SELECT 
    ch.user_id AS referrer_id,
    ch.created_at AS reward_date,
    ch.amount AS reward_coins,
    ch.after_balance,
    ch.reason,
    -- 가입한 친구 이름 추출 (reason에서 파싱)
    SUBSTRING(ch.reason FROM '추천인 보상: (.*?) 님') AS referred_member_name,
    -- 가입한 친구 ID 추출
    SUBSTRING(ch.reason FROM 'ID: ([^)]+)') AS referred_member_id
FROM gk_credit_history ch
WHERE ch.action_type = 'REFERRAL_REWARD'
ORDER BY ch.created_at DESC;

-- 뷰 코멘트
COMMENT ON VIEW v_referral_rewards IS '추천인 리워드 현황 조회 뷰 (마이페이지 표시용)';

-- ──────────────────────────────────────────────────────────────────────────────
-- [7] 추천인 통계 함수
-- ──────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION get_referral_stats(p_user_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_total_referrals INTEGER;
    v_total_rewards INTEGER;
    v_result JSONB;
BEGIN
    -- 총 추천 인원 수
    SELECT COUNT(*) INTO v_total_referrals
    FROM gk_members
    WHERE referrer_id = p_user_id;
    
    -- 총 받은 보상 코인
    SELECT COALESCE(SUM(amount), 0) INTO v_total_rewards
    FROM gk_credit_history
    WHERE user_id = p_user_id
    AND action_type = 'REFERRAL_REWARD';
    
    v_result := jsonb_build_object(
        'user_id', p_user_id,
        'total_referrals', v_total_referrals,
        'total_rewards', v_total_rewards,
        'average_reward', CASE 
            WHEN v_total_referrals > 0 THEN v_total_rewards / v_total_referrals 
            ELSE 0 
        END
    );
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 함수 코멘트
COMMENT ON FUNCTION get_referral_stats IS '추천인 통계 조회 함수';

-- ──────────────────────────────────────────────────────────────────────────────
-- [8] RLS (Row Level Security) 정책
-- ──────────────────────────────────────────────────────────────────────────────

-- gk_credit_history 테이블에 RLS 정책 추가 (본인 내역만 조회)
ALTER TABLE gk_credit_history ENABLE ROW LEVEL SECURITY;

-- 기존 정책 삭제 (있을 경우)
DROP POLICY IF EXISTS credit_history_select_policy ON gk_credit_history;

-- 본인 내역만 조회 가능
CREATE POLICY credit_history_select_policy ON gk_credit_history
    FOR SELECT
    USING (user_id = current_setting('app.current_user_id', true));

-- ──────────────────────────────────────────────────────────────────────────────
-- [9] 테스트 데이터 삽입 (개발 환경용)
-- ──────────────────────────────────────────────────────────────────────────────

-- 주석 처리: 프로덕션 환경에서는 실행하지 않음
/*
-- 테스트 사용자 1 (추천인)
INSERT INTO gk_members (id, name, contact_hash, current_credits, subscription_plan, referrer_id)
VALUES ('test_referrer_001', '김추천', 'hash_001', 50, 'basic', NULL)
ON CONFLICT (id) DO NOTHING;

-- 테스트 사용자 2 (피추천인)
INSERT INTO gk_members (id, name, contact_hash, current_credits, subscription_plan, referrer_id)
VALUES ('test_referred_001', '이신규', 'hash_002', 50, 'basic', 'test_referrer_001')
ON CONFLICT (id) DO NOTHING;

-- 추천인 보상 지급 테스트
SELECT grant_referral_reward('test_referrer_001', 'test_referred_001', '이신규');

-- 결과 확인
SELECT * FROM gk_members WHERE id = 'test_referrer_001';
SELECT * FROM gk_credit_history WHERE user_id = 'test_referrer_001';
SELECT * FROM v_referral_rewards WHERE referrer_id = 'test_referrer_001';
*/

-- ══════════════════════════════════════════════════════════════════════════════
-- 스키마 업데이트 완료
-- ══════════════════════════════════════════════════════════════════════════════
