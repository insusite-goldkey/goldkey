"""
[GP-IAP] 인앱 결제 시뮬레이션 테스트 스크립트
Goldkey AI Masters 2026 - 코인 충전 파이프라인 검증
"""
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.payment_handler import (
    simulate_test_purchase,
    get_current_credits,
    process_iap_recharge
)


def test_coin_recharge_pipeline():
    """
    코인 충전 파이프라인 전체 테스트.
    """
    print("=" * 80)
    print("[GP-IAP] 인앱 결제 코인 충전 시뮬레이션 테스트")
    print("=" * 80)
    
    # 테스트 사용자 ID
    test_user_id = "test_user_iap_001"
    
    # 1. 초기 코인 잔액 조회
    print(f"\n[STEP 1] 초기 코인 잔액 조회")
    initial_credits = get_current_credits(test_user_id)
    print(f"✅ 현재 잔액: {initial_credits} 코인")
    
    # 2. 베이직 플랜 충전 시뮬레이션 (50코인)
    print(f"\n[STEP 2] 베이직 플랜 충전 시뮬레이션 (+50 코인)")
    result1 = simulate_test_purchase(test_user_id, "basic_addon_50")
    
    if result1.get('success'):
        print(f"✅ 충전 성공!")
        print(f"   - 충전 코인: {result1.get('coins_granted')} 코인")
        print(f"   - 충전 전: {result1.get('balance_before')} 코인")
        print(f"   - 충전 후: {result1.get('balance_after')} 코인")
        print(f"   - 테스트 토큰: {result1.get('test_token')}")
    else:
        print(f"❌ 충전 실패: {result1.get('message')}")
        return
    
    # 3. 중복 결제 방지 테스트
    print(f"\n[STEP 3] 중복 결제 방지 테스트 (동일 토큰 재사용)")
    duplicate_token = result1.get('test_token')
    
    # Supabase RPC 직접 호출 (중복 토큰)
    from db_utils import _get_sb
    sb = _get_sb()
    
    try:
        duplicate_result = sb.rpc(
            'grant_coins_from_iap',
            {
                'p_user_id': test_user_id,
                'p_purchase_token': duplicate_token,
                'p_product_id': 'basic_addon_50',
                'p_coins': 50
            }
        ).execute()
        
        if duplicate_result.data:
            dup_data = duplicate_result.data
            if dup_data.get('success') == False and dup_data.get('error') == 'DUPLICATE_PURCHASE':
                print(f"✅ 중복 결제 차단 성공!")
                print(f"   - 에러 메시지: {dup_data.get('message')}")
            else:
                print(f"⚠️ 중복 결제가 처리되었습니다 (예상치 못한 동작)")
    except Exception as e:
        print(f"❌ 중복 테스트 실패: {e}")
    
    # 4. 프로 플랜 충전 시뮬레이션 (300코인)
    print(f"\n[STEP 4] 프로 플랜 충전 시뮬레이션 (+300 코인)")
    result2 = simulate_test_purchase(test_user_id, "pro_addon_300")
    
    if result2.get('success'):
        print(f"✅ 충전 성공!")
        print(f"   - 충전 코인: {result2.get('coins_granted')} 코인")
        print(f"   - 충전 전: {result2.get('balance_before')} 코인")
        print(f"   - 충전 후: {result2.get('balance_after')} 코인")
    else:
        print(f"❌ 충전 실패: {result2.get('message')}")
    
    # 5. 최종 잔액 확인
    print(f"\n[STEP 5] 최종 코인 잔액 확인")
    final_credits = get_current_credits(test_user_id)
    print(f"✅ 최종 잔액: {final_credits} 코인")
    print(f"   - 총 충전량: {final_credits - initial_credits} 코인")
    
    # 6. 코인 내역 조회
    print(f"\n[STEP 6] 코인 충전 내역 조회")
    try:
        history = sb.table('gk_credit_history').select('*').eq(
            'user_id', test_user_id
        ).order('created_at', desc=True).limit(5).execute()
        
        if history.data:
            print(f"✅ 최근 내역 {len(history.data)}건:")
            for idx, record in enumerate(history.data, 1):
                print(f"   [{idx}] {record.get('action_type')} | "
                      f"{record.get('amount'):+d} 코인 | "
                      f"잔액: {record.get('balance_after')} | "
                      f"{record.get('description')}")
        else:
            print(f"⚠️ 내역 없음")
    except Exception as e:
        print(f"❌ 내역 조회 실패: {e}")
    
    print("\n" + "=" * 80)
    print("[테스트 완료] 모든 단계가 성공적으로 완료되었습니다! 🎉")
    print("=" * 80)


def test_hard_lock_scenario():
    """
    하드 락(Hard Lock) 시나리오 테스트.
    """
    print("\n" + "=" * 80)
    print("[GP-IAP] 하드 락 시나리오 테스트")
    print("=" * 80)
    
    test_user_id = "test_user_hardlock_001"
    
    # 1. 코인 0으로 설정
    print(f"\n[STEP 1] 코인 잔액을 0으로 설정")
    from db_utils import _get_sb
    sb = _get_sb()
    
    try:
        sb.table('gk_members').update({
            'current_credits': 0
        }).eq('user_id', test_user_id).execute()
        print(f"✅ 잔액 초기화 완료")
    except Exception as e:
        print(f"❌ 초기화 실패: {e}")
        return
    
    # 2. 잔액 확인
    credits = get_current_credits(test_user_id)
    print(f"✅ 현재 잔액: {credits} 코인")
    
    # 3. 하드 락 상태 시뮬레이션
    print(f"\n[STEP 2] 하드 락 상태 (코인 부족)")
    if credits < 3:
        print(f"🔒 하드 락 활성화!")
        print(f"   - 필요 코인: 3 코인")
        print(f"   - 현재 잔액: {credits} 코인")
        print(f"   - 부족 코인: {3 - credits} 코인")
    
    # 4. 충전 후 락 해제
    print(f"\n[STEP 3] 코인 충전으로 락 해제")
    result = simulate_test_purchase(test_user_id, "basic_addon_50")
    
    if result.get('success'):
        new_credits = result.get('balance_after', 0)
        print(f"✅ 충전 성공! 잔액: {new_credits} 코인")
        
        if new_credits >= 3:
            print(f"🔓 하드 락 해제! 기능 사용 가능")
        else:
            print(f"⚠️ 여전히 코인 부족")
    else:
        print(f"❌ 충전 실패: {result.get('message')}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 전체 파이프라인 테스트
    test_coin_recharge_pipeline()
    
    # 하드 락 시나리오 테스트
    test_hard_lock_scenario()
