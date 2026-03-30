"""
[GP-IAP] Google Play Billing 결제 검증 및 코인 충전 핸들러
Goldkey AI Masters 2026 - 인앱 결제 실시간 검증 시스템
"""
import os
import json
from typing import Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from db_utils import _get_sb


# ──────────────────────────────────────────────────────────────────────────
# [§1] Google Play Developer API 설정
# ──────────────────────────────────────────────────────────────────────────

def _get_google_play_service():
    """
    Google Play Developer API 서비스 객체 생성.
    
    Returns:
        Google API 서비스 객체 또는 None
    """
    try:
        # 서비스 계정 JSON 키 파일 경로
        credentials_path = os.getenv("GOOGLE_PLAY_CREDENTIALS_PATH")
        if not credentials_path or not os.path.exists(credentials_path):
            print("[IAP] Google Play 서비스 계정 키 파일을 찾을 수 없습니다.")
            return None
        
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/androidpublisher']
        )
        
        service = build('androidpublisher', 'v3', credentials=credentials)
        return service
    except Exception as e:
        print(f"[IAP] Google Play API 초기화 실패: {e}")
        return None


# ──────────────────────────────────────────────────────────────────────────
# [§2] 결제 영수증 검증
# ──────────────────────────────────────────────────────────────────────────

def verify_google_play_purchase(
    package_name: str,
    product_id: str,
    purchase_token: str
) -> Dict:
    """
    Google Play 인앱 결제 영수증 검증.
    
    Args:
        package_name: 앱 패키지명 (예: com.goldkey.ai.masters)
        product_id: 상품 ID (예: basic_monthly)
        purchase_token: 구매 토큰
    
    Returns:
        검증 결과 딕셔너리
        {
            'valid': bool,
            'purchase_state': int,  # 0: 구매됨, 1: 취소됨
            'consumption_state': int,  # 0: 미소비, 1: 소비됨
            'error': str (optional)
        }
    """
    try:
        service = _get_google_play_service()
        if not service:
            return {'valid': False, 'error': 'SERVICE_UNAVAILABLE'}
        
        # Google Play Developer API 호출
        result = service.purchases().products().get(
            packageName=package_name,
            productId=product_id,
            token=purchase_token
        ).execute()
        
        # 결제 상태 확인
        purchase_state = result.get('purchaseState', 1)
        consumption_state = result.get('consumptionState', 1)
        
        return {
            'valid': purchase_state == 0,  # 0 = 구매됨
            'purchase_state': purchase_state,
            'consumption_state': consumption_state,
            'order_id': result.get('orderId'),
            'purchase_time': result.get('purchaseTimeMillis'),
        }
    
    except Exception as e:
        print(f"[IAP] 영수증 검증 실패: {e}")
        return {'valid': False, 'error': str(e)}


# ──────────────────────────────────────────────────────────────────────────
# [§3] 코인 충전 처리
# ──────────────────────────────────────────────────────────────────────────

def process_iap_recharge(
    user_id: str,
    purchase_token: str,
    product_id: str,
    package_name: str = "com.goldkey.ai.masters"
) -> Dict:
    """
    인앱 결제 검증 후 코인 충전 처리.
    
    Args:
        user_id: 회원 ID
        purchase_token: 구매 토큰
        product_id: 상품 ID
        package_name: 앱 패키지명
    
    Returns:
        처리 결과 딕셔너리
        {
            'success': bool,
            'coins_granted': int,
            'balance_after': int,
            'message': str,
            'error': str (optional)
        }
    """
    # 1. 상품별 코인 매핑
    PRODUCT_COINS = {
        'basic_monthly': 50,
        'pro_monthly': 300,
        'basic_addon_50': 50,
        'pro_addon_300': 300,
    }
    
    coins = PRODUCT_COINS.get(product_id, 0)
    if coins == 0:
        return {
            'success': False,
            'error': 'INVALID_PRODUCT',
            'message': f'알 수 없는 상품 ID: {product_id}'
        }
    
    # 2. Google Play 영수증 검증
    verification = verify_google_play_purchase(
        package_name=package_name,
        product_id=product_id,
        purchase_token=purchase_token
    )
    
    if not verification.get('valid'):
        return {
            'success': False,
            'error': 'INVALID_RECEIPT',
            'message': '결제 영수증이 유효하지 않습니다.',
            'details': verification.get('error')
        }
    
    # 3. Supabase 함수 호출 (원자적 트랜잭션)
    sb = _get_sb()
    if not sb:
        return {
            'success': False,
            'error': 'DB_UNAVAILABLE',
            'message': '데이터베이스 연결 실패'
        }
    
    try:
        result = sb.rpc(
            'grant_coins_from_iap',
            {
                'p_user_id': user_id,
                'p_purchase_token': purchase_token,
                'p_product_id': product_id,
                'p_coins': coins
            }
        ).execute()
        
        if result.data:
            return result.data
        else:
            return {
                'success': False,
                'error': 'RPC_FAILED',
                'message': '코인 충전 처리 실패'
            }
    
    except Exception as e:
        print(f"[IAP] 코인 충전 RPC 실패: {e}")
        return {
            'success': False,
            'error': 'EXCEPTION',
            'message': str(e)
        }


# ──────────────────────────────────────────────────────────────────────────
# [§4] 테스트 모드 (개발용)
# ──────────────────────────────────────────────────────────────────────────

def simulate_test_purchase(
    user_id: str,
    product_id: str = 'basic_monthly'
) -> Dict:
    """
    테스트용 가상 결제 시뮬레이션.
    
    실제 Google Play API를 호출하지 않고,
    가상의 purchase_token으로 코인 충전을 시뮬레이션.
    
    Args:
        user_id: 회원 ID
        product_id: 상품 ID
    
    Returns:
        처리 결과 딕셔너리
    """
    import uuid
    
    # 가상 토큰 생성
    test_token = f"TEST_TOKEN_{uuid.uuid4().hex[:16]}"
    
    # 상품별 코인 매핑
    PRODUCT_COINS = {
        'basic_monthly': 50,
        'pro_monthly': 300,
        'basic_addon_50': 50,
        'pro_addon_300': 300,
    }
    
    coins = PRODUCT_COINS.get(product_id, 0)
    if coins == 0:
        return {
            'success': False,
            'error': 'INVALID_PRODUCT',
            'message': f'알 수 없는 상품 ID: {product_id}'
        }
    
    # Supabase 함수 직접 호출 (영수증 검증 건너뜀)
    sb = _get_sb()
    if not sb:
        return {
            'success': False,
            'error': 'DB_UNAVAILABLE',
            'message': '데이터베이스 연결 실패'
        }
    
    try:
        result = sb.rpc(
            'grant_coins_from_iap',
            {
                'p_user_id': user_id,
                'p_purchase_token': test_token,
                'p_product_id': product_id,
                'p_coins': coins
            }
        ).execute()
        
        if result.data:
            response = result.data
            response['test_mode'] = True
            response['test_token'] = test_token
            return response
        else:
            return {
                'success': False,
                'error': 'RPC_FAILED',
                'message': '코인 충전 처리 실패'
            }
    
    except Exception as e:
        print(f"[IAP] 테스트 충전 실패: {e}")
        return {
            'success': False,
            'error': 'EXCEPTION',
            'message': str(e)
        }


# ──────────────────────────────────────────────────────────────────────────
# [§5] 코인 잔액 조회
# ──────────────────────────────────────────────────────────────────────────

def get_current_credits(user_id: str) -> int:
    """
    현재 코인 잔액 조회.
    
    Args:
        user_id: 회원 ID
    
    Returns:
        코인 잔액 (조회 실패 시 0)
    """
    sb = _get_sb()
    if not sb:
        return 0
    
    try:
        result = sb.table('gk_members').select('current_credits').eq('user_id', user_id).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('current_credits', 0)
        return 0
    except Exception as e:
        print(f"[IAP] 코인 잔액 조회 실패: {e}")
        return 0
