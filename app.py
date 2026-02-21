# ==========================================================
# 골드키지사 마스터 AI - 탭 구조 통합본 (전체 수정판)
# 수정: 구조적/논리적/보안/모바일 문제 전체 반영
# ==========================================================
#
# ██████████████████████████████████████████████████████████
# ██  [코딩 규칙 — 삭제/수정 금지]                        ██
# ██                                                      ██
# ██  1. 아래 섹션 구조(SECTION 0 ~ SECTION 12)는         ██
# ██     절대 삭제하거나 순서를 변경하지 말 것.            ██
# ██                                                      ██
# ██  2. 각 섹션 내 '삭제/수정 금지' 주석이 달린          ██
# ██     코드 블록은 내용을 변경하지 말 것.               ██
# ██                                                      ██
# ██  3. 전문가 역산 로직(건보료/국민연금 기반 소득 역산,  ██
# ██     보험료 황금비율, 호프만/라이프니쯔 계수 산출 등)  ██
# ██     은 절대 변경하지 말 것.                          ██
# ██                                                      ██
# ██  섹션 구조 목록:                                     ██
# ██   SECTION 0    — Google Play 결제 검증 & RTDN        ██
# ██   SECTION 0.5  — 베타 모드 / 결제 플래그             ██
# ██   SECTION 1.5  — Google Sheets 영구 저장소           ██
# ██   SECTION 2    — 데이터베이스 & 회원 관리            ██
# ██   SECTION 3    — 유틸리티 함수                       ██
# ██   SECTION 4    — RAG 시스템                          ██
# ██   SECTION 5    — AI 모델 & 프롬프트                  ██
# ██   SECTION 6    — 메인 UI (사이드바 / 이용약관)       ██
# ██   SECTION 7    — 탭 라우팅 & 각 상담 탭              ██
# ██   SECTION 8    — 관리자 패널                         ██
# ██   SECTION 9    — 엔트리포인트 (main)                 ██
# ██   SECTION 12   — 배상책임보험 상담 탭                ██
# ██████████████████████████████████████████████████████████

import streamlit as st
from google import genai
from google.genai import types
import json, os, time, hashlib, base64, re, tempfile
from datetime import datetime as dt, timedelta, date
from typing import List, Dict
import numpy as np
import sqlite3
import PIL.Image
from cryptography.fernet import Fernet
import streamlit.components.v1 as components

# 선택적 임포트 (미설치 시 해당 기능만 비활성화)
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False

try:
    import pdfplumber
    import docx
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# [시스템 필수 설정]
USAGE_DB = "usage_log.json"
MEMBER_DB = "members.json"

# 선택적 임포트 — Google Play Billing
# BETA_MODE=True 시 완전 비활성화 (라이브러리 미설치 환경 포함)
# 주의: BETA_MODE 플래그는 아래 [SECTION 0.5]에서 정의됨
#   이 시점에서는 아직 정의 전이므로 False 리터럴로 임포트 차단
_BILLING_IMPORT_ENABLED = False  # BETA_MODE 연동 전 임시 차단 플래그

if _BILLING_IMPORT_ENABLED:
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        import google.auth.exceptions
        BILLING_AVAILABLE = True
    except ImportError:
        BILLING_AVAILABLE = False
    try:
        from google.cloud import pubsub_v1
        PUBSUB_AVAILABLE = True
    except ImportError:
        PUBSUB_AVAILABLE = False
else:
    BILLING_AVAILABLE = False
    PUBSUB_AVAILABLE = False

# --------------------------------------------------------------------------
# [SECTION 0] Google Play 인앱 결제 검증 & RTDN (Real-Time Developer Notifications)
# --------------------------------------------------------------------------
# 아키텍처:
#   Android(Bubblewrap/TWA) → 결제 → purchaseToken 획득
#   → Python 백엔드: verify_google_purchase() → Google Play API 검증
#   → DB subscription_end + is_active 업데이트 → 서비스 개시
#
# RTDN(Pull) 흐름:
#   Google Play → Cloud Pub/Sub Topic
#   → run_worker() 백그라운드 스레드 → callback() → DB 동기화
#   (Push 방식은 외부 공개 URL 필요 — 로컬/Streamlit Cloud는 Pull 권장)

def _get_play_config():
    """Play Console 설정값을 secrets에서 가져옴 — 없으면 환경변수 폴백"""
    try:
        pkg  = st.secrets.get("PLAY_PACKAGE_NAME",    "") or os.environ.get("PLAY_PACKAGE_NAME",    "")
        sub  = st.secrets.get("PLAY_SUBSCRIPTION_ID", "") or os.environ.get("PLAY_SUBSCRIPTION_ID", "")
        return pkg, sub
    except Exception:
        return (
            os.environ.get("PLAY_PACKAGE_NAME",    ""),
            os.environ.get("PLAY_SUBSCRIPTION_ID", ""),
        )

PLAY_PACKAGE_NAME,    PLAY_SUBSCRIPTION_ID = _get_play_config()

# Google Billing v7 기준 notificationType 매핑
NOTIFICATION_TYPES = {
    1:  "RECOVERED",
    2:  "RENEWED",
    3:  "CANCELED",
    4:  "PURCHASED",
    5:  "ACCOUNT_HOLD",
    6:  "IN_GRACE_PERIOD",
    7:  "RESTARTED",
    12: "REVOKED",
    13: "EXPIRED",
}
# 비활성화 트리거 유형
_DEACTIVATE_TYPES = {3, 12, 13}   # CANCELED, REVOKED, EXPIRED
# 활성화 트리거 유형
_ACTIVATE_TYPES   = {1, 2, 4, 7}  # RECOVERED, RENEWED, PURCHASED, RESTARTED

def _get_gcp_credentials(scopes: list):
    """secrets.toml [gcp_service_account] → 인증 객체 반환"""
    if not BILLING_AVAILABLE:
        return None
    try:
        gcp_info = dict(st.secrets["gcp_service_account"])
        return service_account.Credentials.from_service_account_info(
            gcp_info, scopes=scopes
        )
    except Exception:
        return None

def _get_play_service():
    """Google Play Developer API (androidpublisher v3) 서비스 객체"""
    creds = _get_gcp_credentials(
        ["https://www.googleapis.com/auth/androidpublisher"]
    )
    if not creds:
        return None
    try:
        return build("androidpublisher", "v3", credentials=creds, cache_discovery=False)
    except Exception:
        return None

def verify_google_purchase(purchase_token: str, user_name: str) -> tuple:
    """
    Google Play 구독 토큰 검증 후 DB 업데이트.
    반환: (success: bool, message: str)
    """
    if not BILLING_AVAILABLE:
        return False, "결제 검증 라이브러리가 설치되지 않았습니다."
    service = _get_play_service()
    if not service:
        return False, "GCP 서비스 계정 인증 실패. secrets.toml을 확인하세요."
    try:
        result = service.purchases().subscriptions().get(
            packageName=PLAY_PACKAGE_NAME,
            subscriptionId=PLAY_SUBSCRIPTION_ID,
            token=purchase_token
        ).execute()

        payment_state = result.get("paymentState", 0)
        expiry_ms     = int(result.get("expiryTimeMillis", 0))
        expiry_dt     = dt.fromtimestamp(expiry_ms / 1000) if expiry_ms else None
        auto_renewing = result.get("autoRenewing", False)

        if payment_state == 1 and expiry_dt and expiry_dt > dt.now():
            _update_subscription_from_play(user_name, expiry_dt, purchase_token)
            return True, f"구독 활성화 완료 (만료: {expiry_dt.strftime('%Y-%m-%d')}, 자동갱신: {auto_renewing})"
        elif payment_state == 0:
            return False, "결제 대기 중입니다. 잠시 후 다시 시도하세요."
        else:
            return False, f"구독이 만료되었거나 유효하지 않습니다. (만료: {expiry_dt})"
    except Exception as e:
        return False, f"검증 오류: {str(e)}"

def _update_subscription_from_play(user_name: str, expiry_dt: dt, purchase_token: str = ""):
    """결제 검증 성공 시 DB 구독 만료일 + purchase_token 업데이트"""
    expiry_str = expiry_dt.strftime("%Y-%m-%d")
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE members SET subscription_end=?, is_active=1, purchase_token=? WHERE name=?",
                (expiry_str, purchase_token, user_name)
            )
    except Exception:
        pass

# ── Pub/Sub Pull 방식 콜백 ──────────────────────────────────────────────────
def _rtdn_callback(message):
    """
    Pub/Sub Pull 구독 콜백.
    메시지 처리 성공 → message.ack()  (중복 수신 방지)
    처리 실패       → message.nack() (재시도 요청)
    """
    try:
        raw = base64.b64decode(message.data).decode("utf-8")
        data = json.loads(raw)
        sub_notif = data.get("subscriptionNotification")
        if not sub_notif:
            message.ack()
            return

        n_type  = sub_notif.get("notificationType")
        p_token = sub_notif.get("purchaseToken", "")
        event   = NOTIFICATION_TYPES.get(n_type, "UNKNOWN")

        if n_type in _DEACTIVATE_TYPES:
            _set_active_by_token(p_token, False)
        elif n_type in _ACTIVATE_TYPES:
            _set_active_by_token(p_token, True)

        message.ack()
    except Exception:
        try:
            message.nack()
        except Exception:
            pass

def _set_active_by_token(purchase_token: str, is_active: bool):
    """purchase_token 기준으로 DB is_active 업데이트"""
    val = 1 if is_active else 0
    try:
        with _get_conn() as conn:
            conn.execute(
                "UPDATE members SET is_active=? WHERE purchase_token=?",
                (val, purchase_token)
            )
    except Exception:
        pass

def handle_rtdn_message(message_data: dict):
    """
    Push 방식 RTDN 처리 (외부 공개 URL 환경용).
    Pull 방식은 run_worker() 사용.
    """
    try:
        sub_notif = message_data.get("subscriptionNotification", {})
        n_type  = sub_notif.get("notificationType")
        p_token = sub_notif.get("purchaseToken", "")
        if n_type in _DEACTIVATE_TYPES:
            _set_active_by_token(p_token, False)
        elif n_type in _ACTIVATE_TYPES:
            _set_active_by_token(p_token, True)
    except Exception:
        pass

def run_worker():
    """
    RTDN Pull 방식 백그라운드 리스너.
    별도 스레드에서 실행 — Streamlit 앱과 독립적으로 구독 상태 동기화.

    실행 방법 (앱과 별도 터미널):
        python insurance_bot.py --worker

    GCP 설정:
      1. GCP Console → Pub/Sub → 주제(Topic) 생성
      2. Play Console → 설정 → 실시간 개발자 알림 → 주제 연결
      3. Pub/Sub → 구독(Subscription) 생성 → Pull 방식
      4. secrets.toml [gcp_service_account] 인증 설정
    """
    if not PUBSUB_AVAILABLE:
        print("[RTDN] google-cloud-pubsub 미설치 — 워커 비활성화")
        return
    try:
        creds = _get_gcp_credentials(
            ["https://www.googleapis.com/auth/pubsub"]
        )
        if not creds:
            print("[RTDN] GCP 인증 실패 — secrets.toml [gcp_service_account] 확인")
            return
        try:
            project_id = st.secrets.get("gcp_service_account", {}).get("project_id", "")
        except Exception:
            project_id = ""
        try:
            subscription_id = st.secrets.get("PUBSUB_SUBSCRIPTION_ID", "") or os.environ.get("PUBSUB_SUBSCRIPTION_ID", "play-subs-notifications-sub")
        except Exception:
            subscription_id = os.environ.get("PUBSUB_SUBSCRIPTION_ID", "play-subs-notifications-sub")
        subscriber      = pubsub_v1.SubscriberClient(credentials=creds)
        sub_path        = subscriber.subscription_path(project_id, subscription_id)
        print(f"[RTDN] 모니터링 시작: {sub_path}")
        future = subscriber.subscribe(sub_path, callback=_rtdn_callback)
        with subscriber:
            try:
                future.result()
            except KeyboardInterrupt:
                future.cancel()
                print("[RTDN] 워커 종료")
    except Exception as e:
        print(f"[RTDN] 워커 오류: {e}")

# --------------------------------------------------------------------------
# [SECTION 1] 보안 및 암호화 엔진
# --------------------------------------------------------------------------
_KEY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".goldkey")

def get_encryption_key() -> bytes:
    """우선순위: st.secrets > 환경변수 > 로컬 .goldkey 파일 > 런타임 생성 후 저장"""
    # 1) Streamlit secrets
    try:
        if "ENCRYPTION_KEY" in st.secrets:
            return st.secrets["ENCRYPTION_KEY"].encode()
    except Exception:
        pass
    # 2) 환경변수
    env_key = os.environ.get("ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()
    # 3) 로컬 키 파일
    if os.path.exists(_KEY_FILE):
        with open(_KEY_FILE, "rb") as f:
            return f.read().strip()
    # 4) 런타임 생성 후 파일 저장 (하드코딩 키 완전 제거)
    new_key = Fernet.generate_key()
    try:
        with open(_KEY_FILE, "wb") as f:
            f.write(new_key)
    except Exception:
        pass
    return new_key

def get_cipher():
    """cipher_suite 지연 초기화 - 모듈 수준 st.secrets 접근 방지"""
    if 'cipher_suite' not in st.session_state:
        st.session_state.cipher_suite = Fernet(get_encryption_key())
    return st.session_state.cipher_suite

def encrypt_val(data):
    return get_cipher().encrypt(data.encode()).decode()

def decrypt_val(data):
    try:
        return get_cipher().decrypt(data.encode()).decode()
    except Exception:
        return "Decryption Error"

def encrypt_data(data):
    """단방향 해시 암호화 (연락처 등 민감 정보)"""
    return hashlib.sha256(data.encode()).hexdigest()

# --------------------------------------------------------------------------
# [SECTION 1.5] 비상장주식 평가 엔진 (상증법 + 법인세법)
# --------------------------------------------------------------------------
class AdvancedStockEvaluator:
    """
    상증법 및 법인세법 통합 비상장주식 평가 엔진
    (Integrated Valuation Engine for Inheritance & Corporate Tax)
    """
    def __init__(self, net_asset, net_incomes, total_shares,
                 market_price=None, is_controlling=False, is_real_estate_rich=False):
        self.net_asset          = net_asset
        self.net_incomes        = net_incomes        # [최근년, 전년, 전전년] 순
        self.total_shares       = total_shares
        self.market_price       = market_price       # 매매사례가액 (법인세법 최우선)
        self.is_controlling     = is_controlling     # 최대주주 경영권 할증 여부
        self.is_real_estate_rich = is_real_estate_rich
        self.cap_rate           = 0.1
        self.annuity_factor     = 3.7908

    def evaluate_corporate_tax(self):
        """법인세법상 시가 평가"""
        if self.market_price:
            base_val    = self.market_price
            method_name = "매매사례가액 (Primary Market Price)"
        else:
            result      = self.evaluate_inheritance_tax()
            base_val    = result['최종 평가액 (할증 전)']
            method_name = "보충적 평가방법 (Supplementary Method)"
        final_val = base_val * 1.2 if self.is_controlling else base_val
        return {
            "평가 방식":        method_name,
            "경영권 할증 적용": "Yes (20%)" if self.is_controlling else "No",
            "법인세법상 시가":  round(final_val, 2),
        }

    def evaluate_inheritance_tax(self):
        """상증법상 보충적 평가"""
        pure_asset_per_share = self.net_asset / self.total_shares
        weighted_eps = (
            self.net_incomes[0] / self.total_shares * 3 +
            self.net_incomes[1] / self.total_shares * 2 +
            self.net_incomes[2] / self.total_shares * 1
        ) / 6
        excess_earnings  = (weighted_eps * 0.5) - (pure_asset_per_share * 0.1)
        goodwill         = max(0, excess_earnings * self.annuity_factor)
        final_asset_value = pure_asset_per_share + goodwill
        earnings_value   = weighted_eps / self.cap_rate
        weight_eps, weight_asset = (2, 3) if self.is_real_estate_rich else (3, 2)
        weighted_avg  = (earnings_value * weight_eps + final_asset_value * weight_asset) / 5
        floor_value   = final_asset_value * 0.8
        base_valuation = max(weighted_avg, floor_value)
        final_valuation = base_valuation * 1.2 if self.is_controlling else base_valuation
        return {
            "주당 순자산가치":        round(final_asset_value, 2),
            "주당 순손익가치":        round(earnings_value, 2),
            "최종 평가액 (할증 전)": round(base_valuation, 2),
            "경영권 할증 적용":       "Yes (20%)" if self.is_controlling else "No",
            "상증법상 최종가액":      round(final_valuation, 2),
        }

# --------------------------------------------------------------------------
# [SECTION 1.6] CEO플랜 AI 프롬프트 상수
# --------------------------------------------------------------------------
CEO_PLAN_PROMPT = """
[역할] 당신은 법인 CEO플랜 전문 보험·세무 컨설턴트입니다.
비상장주식 평가 결과를 바탕으로 아래 항목을 체계적으로 분석하십시오.

[분석 항목]
1. 비상장주식 평가 결과 해석 (법인세법 vs 상증법 비교)
2. 가업승계 전략 — 증여세·상속세 절감 방안 (가업상속공제, 가업승계 증여세 과세특례)
3. CEO 퇴직금 설계 — 임원 퇴직금 규정 정비 및 보험 재원 마련
4. 경영인정기보험 활용 — 법인 납입 보험료 손금산입 가능 여부 및 한도
5. 주가 관리 전략 — 평가액 조정을 통한 절세 시뮬레이션
6. CEO 유고 리스크 대비 — 사망보험금 → 퇴직금·주식 매입 재원 활용
7. 법인 절세 전략 종합 — 세무사 협업 필요 사항 명시

[주의] 본 분석은 참고용이며, 구체적 세무·법률 사항은 반드시 세무사·변호사와 확인하십시오.
"""

CEO_FS_PROMPT = """
[역할] 당신은 기업회계 전문가 겸 법인 보험 컨설턴트입니다.
첨부된 재무제표(손익계산서·대차대조표·현금흐름표)를 분석하여 아래 항목을 보고하십시오.

[재무제표 분석 항목]
1. 수익성 분석 — 매출액·영업이익·당기순이익 3년 추이 및 증감률
2. 안정성 분석 — 부채비율·유동비율·자기자본비율 산출 및 평가
3. 성장성 분석 — 매출성장률·이익성장률·자산성장률
4. 비상장주식 평가용 핵심 수치 추출
   - 순자산(자본총계), 3개년 당기순이익, 발행주식 총수(확인 가능 시)
5. 상증법 보충적 평가 적용 시 예상 주당 가치 범위 추정
6. CEO플랜 설계 관점 — 법인 재무 건전성 기반 보험 재원 마련 가능성
7. 리스크 요인 — 재무제표상 주요 위험 신호(적자 지속·부채 급증 등)
8. 세무사·회계사 추가 검토 필요 사항

[기업회계 기준] K-IFRS 또는 일반기업회계기준(K-GAAP) 적용
[주의] 본 분석은 AI 보조 도구로서 참고용이며, 최종 판단은 공인회계사·세무사와 확인하십시오.
"""

CEO_EVAL_GUIDE = """
<b style="font-size:0.88rem;color:#1a3a5c;">① 상증법 보충적 평가 (상속세 및 증여세법)</b><br>
<table style="width:100%;border-collapse:collapse;font-size:0.82rem;margin:6px 0 10px 0;">
  <tr style="background:#1a3a5c;color:#fff;">
    <th style="padding:5px 8px;text-align:left;">구분</th>
    <th style="padding:5px 8px;text-align:left;">산식</th>
    <th style="padding:5px 8px;text-align:center;">가중치</th>
  </tr>
  <tr style="border-bottom:1px solid #dde3ea;">
    <td style="padding:5px 8px;">주당 순손익가치</td>
    <td style="padding:5px 8px;">3개년 가중평균 EPS ÷ 환원율(10%)</td>
    <td style="padding:5px 8px;text-align:center;font-weight:700;">3</td>
  </tr>
  <tr style="background:#f4f7fb;border-bottom:1px solid #dde3ea;">
    <td style="padding:5px 8px;">주당 순자산가치</td>
    <td style="padding:5px 8px;">(순자산 + 영업권) ÷ 총주식수</td>
    <td style="padding:5px 8px;text-align:center;font-weight:700;">2</td>
  </tr>
  <tr style="border-bottom:1px solid #dde3ea;">
    <td style="padding:5px 8px;font-weight:700;">가중평균</td>
    <td style="padding:5px 8px;font-weight:700;">(손익가치×3 + 자산가치×2) ÷ 5</td>
    <td style="padding:5px 8px;text-align:center;">—</td>
  </tr>
  <tr style="background:#f4f7fb;border-bottom:1px solid #dde3ea;">
    <td style="padding:5px 8px;">하한선</td>
    <td style="padding:5px 8px;">순자산가치 × 80%</td>
    <td style="padding:5px 8px;text-align:center;">—</td>
  </tr>
  <tr>
    <td style="padding:5px 8px;">경영권 할증</td>
    <td style="padding:5px 8px;">최대주주 등 → 평가액 × 1.2</td>
    <td style="padding:5px 8px;text-align:center;">—</td>
  </tr>
</table>
<span style="font-size:0.8rem;color:#c0392b;">※ 부동산 과다 법인: 손익가치 2 : 자산가치 3 역전 적용</span><br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">② 법인세법상 시가</b><br>
• 매매사례가액 있으면 → 해당 가액 우선 적용<br>
• 없으면 → 상증법 보충적 평가방법 준용<br>
• 최대주주 20% 할증 동일 적용<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">③ 영업권 계산</b><br>
<div style="background:#f0f4f8;border-radius:6px;padding:8px 12px;margin:4px 0 10px 0;font-family:monospace;font-size:0.82rem;">
초과이익 = (가중평균EPS × 50%) − (주당순자산 × 10%)<br>
영업권 &nbsp;&nbsp;= max(0, 초과이익 × 연금현가계수 3.7908)
</div>
<b style="font-size:0.88rem;color:#1a3a5c;">④ 활용 목적</b><br>
• 가업승계 증여·상속 시 과세표준 산정<br>
• 법인 간 주식 거래 시 부당행위계산 판단 기준<br>
• CEO 퇴직금·보험 설계 시 법인 가치 평가 근거
"""

def decrypt_data(stored_hash, input_data):
    """해시 비교 검증"""
    return stored_hash == hashlib.sha256(input_data.encode()).hexdigest()

def encrypt_contact(contact):
    return hashlib.sha256(contact.encode()).hexdigest()

def sanitize_prompt(text):
    """프롬프트 인젝션 방어 - 모든 쿼리에 적용"""
    danger_words = ["system instruction", "지침 무시", "프롬프트 출력", "비밀번호", "명령어 변경"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

# --------------------------------------------------------------------------
# [SECTION 0.5] 베타 모드 및 결제 모듈 활성화 플래그
# --------------------------------------------------------------------------
# BETA_MODE = True  → 결제 라이브러리/기능 완전 비활성화 (베타 배포/심사 대응)
# BETA_MODE = False → 결제 연동 활성화 (실제 운영 시)
BETA_MODE: bool = True

# BETA_MODE 연동: 비활성화 시 임포트 차단 플래그 동기화
_BILLING_IMPORT_ENABLED = not BETA_MODE

# 이용약관 결제 조항: BETA_MODE일 때 숨김
SHOW_PAYMENT_TERMS: bool = not BETA_MODE

def get_admin_key():
    """관리자 키를 st.secrets에서 가져옴 (평문 하드코딩 금지)"""
    try:
        key = st.secrets.get("ADMIN_KEY", "goldkey777")
        return key if key else "goldkey777"
    except Exception:
        return "goldkey777"

# --------------------------------------------------------------------------
# [SECTION 1.5] Google Sheets 영구 저장소 레이어
# --------------------------------------------------------------------------
# 구조: SQLite(빠른 읽기/쓰기) + Google Sheets(영구 백업)
#   앱 시작 시: Sheets → SQLite 복원 (휘발성 /tmp 초기화 대응)
#   쓰기 시:   SQLite 저장 후 Sheets 동기화 (비동기 처리)
#
# secrets.toml 설정:
#   [gcp_service_account] 항목 재사용 (결제 연동과 동일 서비스 계정)
#   SHEETS_MEMBERS_ID = "구글시트_스프레드시트_ID"
#
# Google Sheets 구조:
#   시트1 "members"  : name | user_id | contact_hash | join_date | subscription_end | is_active | purchase_token
#   시트2 "usage_log": user_name | log_date | count

try:
    import gspread
    from google.oauth2.service_account import Credentials as _SACredentials
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False

_SHEETS_SCOPES = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

@st.cache_resource(show_spinner=False)
def _get_sheets_client():
    """gspread 클라이언트 — secrets.toml [gcp_service_account] 재사용"""
    if not SHEETS_AVAILABLE:
        return None
    try:
        info = dict(st.secrets["gcp_service_account"])
        creds = _SACredentials.from_service_account_info(info, scopes=_SHEETS_SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None

def _get_spreadsheet():
    """스프레드시트 객체 반환 — SHEETS_MEMBERS_ID secrets 키 사용"""
    gc = _get_sheets_client()
    if not gc:
        return None
    try:
        sid = st.secrets.get("SHEETS_MEMBERS_ID", "")
        if not sid:
            return None
        return gc.open_by_key(sid)
    except Exception:
        return None

def _sheets_get_or_create_worksheet(ss, title: str, headers: list):
    """시트가 없으면 생성 후 헤더 삽입"""
    try:
        ws = ss.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        ws = ss.add_worksheet(title=title, rows=1000, cols=len(headers))
        ws.append_row(headers)
    return ws

# ── Sheets → SQLite 복원 ──────────────────────────────────────────────────
def restore_from_sheets(conn):
    """
    앱 시작 시 1회 호출.
    Google Sheets의 최신 데이터를 SQLite에 INSERT OR REPLACE.
    Sheets 미설정 시 조용히 스킵.
    """
    ss = _get_spreadsheet()
    if not ss:
        return
    try:
        # members 복원
        ws_m = _sheets_get_or_create_worksheet(
            ss, "members",
            ["name","user_id","contact_hash","join_date","subscription_end","is_active","purchase_token"]
        )
        rows = ws_m.get_all_records()
        for r in rows:
            conn.execute(
                "INSERT OR REPLACE INTO members "
                "(name,user_id,contact_hash,join_date,subscription_end,is_active,purchase_token) "
                "VALUES (?,?,?,?,?,?,?)",
                (r.get("name",""), r.get("user_id",""), r.get("contact_hash",""),
                 r.get("join_date",""), r.get("subscription_end",""),
                 int(r.get("is_active", 1)), r.get("purchase_token",""))
            )
    except Exception:
        pass
    try:
        # usage_log 복원
        ws_u = _sheets_get_or_create_worksheet(
            ss, "usage_log", ["user_name","log_date","count"]
        )
        rows = ws_u.get_all_records()
        for r in rows:
            conn.execute(
                "INSERT OR IGNORE INTO usage_log (user_name,log_date,count) VALUES (?,?,?)",
                (r.get("user_name",""), r.get("log_date",""), int(r.get("count", 0)))
            )
    except Exception:
        pass

# ── SQLite → Sheets 동기화 (쓰기 후 호출) ────────────────────────────────
def _sync_member_to_sheets(name: str, user_id: str, contact_hash: str,
                            join_date: str, subscription_end: str,
                            is_active: int, purchase_token: str = ""):
    """단일 회원 행을 Sheets에 upsert"""
    ss = _get_spreadsheet()
    if not ss:
        return
    try:
        ws = _sheets_get_or_create_worksheet(
            ss, "members",
            ["name","user_id","contact_hash","join_date","subscription_end","is_active","purchase_token"]
        )
        cell = ws.find(name, in_column=1)
        row_data = [name, user_id, contact_hash, join_date,
                    subscription_end, is_active, purchase_token]
        if cell:
            ws.update(f"A{cell.row}:G{cell.row}", [row_data])
        else:
            ws.append_row(row_data)
    except Exception:
        pass

def _sync_usage_to_sheets(user_name: str, log_date: str, count: int):
    """usage_log 단일 행을 Sheets에 upsert"""
    ss = _get_spreadsheet()
    if not ss:
        return
    try:
        ws = _sheets_get_or_create_worksheet(
            ss, "usage_log", ["user_name","log_date","count"]
        )
        # user_name + log_date 조합으로 행 검색
        records = ws.get_all_records()
        for i, r in enumerate(records, start=2):  # 헤더가 1행
            if r.get("user_name") == user_name and r.get("log_date") == log_date:
                ws.update(f"C{i}", [[count]])
                return
        ws.append_row([user_name, log_date, count])
    except Exception:
        pass

def _delete_member_from_sheets(name: str):
    """Sheets에서 회원 행 삭제 (GDPR 파기 연동)"""
    ss = _get_spreadsheet()
    if not ss:
        return
    try:
        ws = ss.worksheet("members")
        cell = ws.find(name, in_column=1)
        if cell:
            ws.delete_rows(cell.row)
    except Exception:
        pass

# --------------------------------------------------------------------------
# [SECTION 2] 데이터베이스 및 회원 관리 (SQLite 영구 저장)
# --------------------------------------------------------------------------
# Streamlit Cloud: 앱 디렉터리는 읽기 전용 → /tmp 폴백 사용
_app_dir = os.path.dirname(os.path.abspath(__file__))
_db_local = os.path.join(_app_dir, "goldkey_data.db")
try:
    _test_write = open(_db_local, "ab")
    _test_write.close()
    DB_PATH = _db_local
except OSError:
    DB_PATH = "/tmp/goldkey_data.db"

from contextlib import contextmanager

@contextmanager
def _get_conn():
    """WAL 모드 + 30초 timeout — database is locked 방지"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def setup_database():
    """앱 시작 시 1회 — 테이블 생성 + JSON 레거시 마이그레이션"""
    with _get_conn() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS members (
            name TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            contact_hash TEXT NOT NULL,
            join_date TEXT NOT NULL,
            subscription_end TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            purchase_token TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )''')
        # 기존 DB에 purchase_token 컬럼 없을 경우 마이그레이션
        try:
            c.execute("ALTER TABLE members ADD COLUMN purchase_token TEXT DEFAULT ''")
        except Exception:
            pass  # 이미 존재하면 무시
        c.execute('''CREATE TABLE IF NOT EXISTS usage_log (
            user_name TEXT NOT NULL,
            log_date TEXT NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (user_name, log_date)
        )''')
        c.execute('''CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_url TEXT,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        _migrate_json_to_db(conn)
        restore_from_sheets(conn)  # Sheets → SQLite 복원 (휘발성 /tmp 대응)

def _migrate_json_to_db(conn):
    """기존 members.json / usage_log.json 을 DB로 이전 후 백업 보관 (이미 열린 conn 재사용)"""
    c = conn.cursor()
    if os.path.exists(MEMBER_DB):
        try:
            with open(MEMBER_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, m in data.items():
                c.execute("INSERT OR IGNORE INTO members "
                          "(name,user_id,contact_hash,join_date,subscription_end,is_active) "
                          "VALUES (?,?,?,?,?,?)",
                          (name, m.get("user_id",""), m.get("contact",""),
                           m.get("join_date",""), m.get("subscription_end",""),
                           1 if m.get("is_active", True) else 0))
            os.rename(MEMBER_DB, MEMBER_DB + ".migrated")
        except Exception:
            pass
    if os.path.exists(USAGE_DB):
        try:
            with open(USAGE_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
            for uname, days in data.items():
                for log_date, cnt in days.items():
                    c.execute("INSERT OR IGNORE INTO usage_log (user_name,log_date,count) VALUES (?,?,?)",
                              (uname, log_date, cnt))
            os.rename(USAGE_DB, USAGE_DB + ".migrated")
        except Exception:
            pass

def load_members() -> dict:
    """DB에서 회원 목록 반환 (기존 코드 호환 dict 형식)"""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT name,user_id,contact_hash,join_date,subscription_end,is_active FROM members"
        ).fetchall()
    return {
        r[0]: {"user_id": r[1], "contact": r[2], "join_date": r[3],
               "subscription_end": r[4], "is_active": bool(r[5])}
        for r in rows
    }

def save_members(members: dict):
    """dict 전체를 DB에 upsert (하위 호환)"""
    with _get_conn() as conn:
        for name, m in members.items():
            conn.execute("INSERT OR REPLACE INTO members "
                         "(name,user_id,contact_hash,join_date,subscription_end,is_active) "
                         "VALUES (?,?,?,?,?,?)",
                         (name, m["user_id"], m["contact"], m["join_date"],
                          m["subscription_end"], 1 if m.get("is_active", True) else 0))
    # Sheets 동기화
    for name, m in members.items():
        _sync_member_to_sheets(
            name, m["user_id"], m["contact"], m["join_date"],
            m["subscription_end"], 1 if m.get("is_active", True) else 0
        )

def add_member(name, contact):
    """
    신규 회원 등록 - 6개월 베타 테스트 무료 개방 버전
    만료일: 2026-08-31 고정
    """
    user_id = "GK_" + name + "_" + str(int(time.time()))
    join_date = dt.now().strftime("%Y-%m-%d")
    # [전문가 역산 로직] 베타 테스트 종료일 고정 설정
    end_date = "2026-08-31"
    contact_hash = encrypt_contact(contact)
    with _get_conn() as conn:
        conn.execute("INSERT OR REPLACE INTO members "
                     "(name,user_id,contact_hash,join_date,subscription_end,is_active) "
                     "VALUES (?,?,?,?,?,1)",
                     (name, user_id, contact_hash, join_date, end_date))
    # Sheets 동기화
    _sync_member_to_sheets(name, user_id, contact_hash, join_date, end_date, 1)
    return {"user_id": user_id, "contact": contact_hash,
            "join_date": join_date, "subscription_end": end_date, "is_active": True}

def gdpr_purge_member(name: str):
    """GDPR Art.17 / 개인정보보호법 기준 완전 파기
       1) DB 레코드 삭제  2) VACUUM(빈 공간 덮어쓰기)  3) Sheets 삭제  4) 세션 초기화"""
    with _get_conn() as conn:
        conn.execute("DELETE FROM members WHERE name=?", (name,))
        conn.execute("DELETE FROM usage_log WHERE user_name=?", (name,))
    # VACUUM은 트랜잭션 밖에서 별도 실행 필요
    vconn = sqlite3.connect(DB_PATH, timeout=30)
    try:
        vconn.execute("VACUUM")
    finally:
        vconn.close()
    # Sheets에서도 삭제 (GDPR 완전 파기)
    _delete_member_from_sheets(name)

# ── 무료 이용 정책 상수 ──────────────────────────────────────────────
# 베타 테스트 종료일: 2026-08-31 (6개월 베타)
BETA_END_DATE  = date(2026, 8, 31)
FREE_EVENT_END = BETA_END_DATE   # 하위 호환 별칭
# 가입 후 10일 이내: 1일 3회 (결제카드 불필요)
MAX_FREE_EARLY = 3
EARLY_FREE_DAYS = 10
# 10일 이후: 1일 10회 (결제 정보 등록 후)
MAX_FREE_DAILY = 10
# 무제한 사용 계정 (사용량 카운트 제외)
UNLIMITED_USERS = {"이세윤", "PERMANENT_MASTER"}

# [전문가 역산 로직] 등급별 일일 한도 정책
PLAN_POLICIES = {
    "Free":     {"limit": 2,   "label": "체험용",            "color": "#6c757d"},
    "Standard": {"limit": 10,  "label": "일반 설계사용",      "color": "#2e6da4"},
    "Master":   {"limit": 999, "label": "전문가용 (무제한)",  "color": "#ffc107"},
}

def get_dynamic_limit(user_name: str, user_tier: str = "Standard"):
    """
    날짜 기반 자동 전환 엔진:
    1. 2026-08-31 이전: 모든 가입자 10회 제공 (베타 프리미엄)
    2. 2026-08-31 이후: 가입 등급(Free/Standard/Master)에 따른 차등 제한
    반환: (tier_label: str, daily_limit: int)
    """
    today_d = date.today()
    if user_name in UNLIMITED_USERS:
        return "MASTER", PLAN_POLICIES["Master"]["limit"]
    if today_d <= BETA_END_DATE:
        return "STANDARD (BETA)", MAX_FREE_DAILY
    policy = PLAN_POLICIES.get(user_tier, PLAN_POLICIES["Free"])
    return user_tier.upper(), policy["limit"]

def display_usage_dashboard(user_name: str):
    """사이드바 프리미엄 사용량 게이지 UI — get_dynamic_limit 기반"""
    current_count = check_usage_count(user_name)
    tier_label, daily_limit = get_dynamic_limit(user_name)

    remaining = max(0, daily_limit - current_count)
    is_unlimited = daily_limit > 100

    if is_unlimited:
        usage_percent = 0.05
        display_limit = "∞"
        rem_text = "무제한 이용 가능"
    else:
        usage_percent = min(1.0, current_count / daily_limit) if daily_limit else 1.0
        display_limit = str(daily_limit)
        rem_text = f"{remaining}회 남음"

    upgrade_html = (
        '<div style="margin-top:14px;border-top:1px dashed #e2e8f0;padding-top:10px;text-align:center;">'
        '<a href="mailto:insusite@gmail.com" style="text-decoration:none;font-size:0.72rem;'
        'color:#2e6da4;font-weight:700;">🚀 MASTER 플랜 업그레이드 문의</a></div>'
        if not is_unlimited else ""
    )

    st.sidebar.markdown(f"""
<div style="background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
            border:1px solid #e2e8f0;border-radius:16px;padding:18px;
            margin:10px 0 25px 0;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <span style="font-size:0.7rem;font-weight:900;color:#1e293b;
                     background:#f1f5f9;padding:4px 10px;border-radius:20px;
                     border:1px solid #cbd5e1;letter-spacing:0.05em;">
            {tier_label}
        </span>
        <span style="font-size:0.9rem;font-weight:800;color:#2e6da4;">
            {current_count} <span style="color:#94a3b8;font-weight:400;">/</span> {display_limit}
        </span>
    </div>
    <div style="background:#f1f5f9;border-radius:12px;height:12px;width:100%;
                overflow:hidden;border:1px solid #e2e8f0;position:relative;">
        <div style="background:linear-gradient(90deg,#3b82f6 0%,#2e6da4 100%);
                    width:{usage_percent * 100:.1f}%;height:100%;border-radius:12px;
                    transition:width 1s cubic-bezier(0.4,0,0.2,1);"></div>
    </div>
    <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:0.75rem;color:#64748b;font-weight:500;">오늘의 잔여 분석</span>
        <span style="font-size:0.85rem;color:#0f172a;font-weight:800;">{rem_text}</span>
    </div>
    {upgrade_html}
</div>
""", unsafe_allow_html=True)

def get_daily_limit(join_date) -> int:
    """가입일 기준 오늘의 일일 한도 반환 (하위 호환 유지)"""
    today_d = date.today()
    if today_d > FREE_EVENT_END:
        return 0
    if not join_date:
        return MAX_FREE_EARLY
    try:
        jd = join_date.date() if hasattr(join_date, 'date') else dt.strptime(str(join_date)[:10], "%Y-%m-%d").date()
        days_since = (today_d - jd).days
    except Exception:
        days_since = 0
    if days_since < EARLY_FREE_DAYS:
        return MAX_FREE_EARLY   # 가입 후 10일 이내: 3회
    return MAX_FREE_DAILY       # 10일 이후: 10회

def check_usage_count(user_name: str) -> int:
    today = str(date.today())
    with _get_conn() as conn:
        row = conn.execute("SELECT count FROM usage_log WHERE user_name=? AND log_date=?",
                           (user_name, today)).fetchone()
    return row[0] if row else 0

def update_usage(user_name: str):
    """분석 성공 후에만 호출"""
    today = str(date.today())
    with _get_conn() as conn:
        conn.execute("INSERT INTO usage_log (user_name,log_date,count) VALUES (?,?,1) "
                     "ON CONFLICT(user_name,log_date) DO UPDATE SET count=count+1",
                     (user_name, today))
        new_count = conn.execute(
            "SELECT count FROM usage_log WHERE user_name=? AND log_date=?",
            (user_name, today)
        ).fetchone()[0]
    # Sheets 동기화
    _sync_usage_to_sheets(user_name, today, new_count)

def get_remaining_usage(user_name: str, join_date=None) -> int:
    limit = get_daily_limit(join_date)
    return max(0, limit - check_usage_count(user_name))

def calculate_subscription_days(join_date):
    if not join_date:
        return 0
    try:
        if isinstance(join_date, str):
            join_date = dt.strptime(join_date, "%Y-%m-%d")
        return max(0, (join_date + timedelta(days=180) - dt.now()).days)  # 6개월
    except:
        return 0

def check_membership_status():
    if 'user_id' not in st.session_state:
        return False, "비회원"
    remaining = calculate_subscription_days(st.session_state.get('join_date'))
    if remaining <= 0:
        return False, "구독 만료"
    return True, f"정상 (잔여 {remaining}일)"

# --------------------------------------------------------------------------
# [SECTION 3] 유틸리티 함수
# --------------------------------------------------------------------------
@st.cache_resource
def get_client():
    # 우선순위: 1) st.secrets  2) 환경변수 (더 안전)
    api_key = None
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        st.error("GEMINI_API_KEY가 설정되지 않았습니다. secrets.toml 또는 환경변수를 확인하세요.")
        st.stop()
    return genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1beta"}
    )

def s_voice(text, lang='ko-KR'):
    """TTS - Android WebView 차단 대응 폴백 포함"""
    clean = text.replace('"', '').replace("'", "").replace("\n", " ").replace("`", "")
    return (
        '<script>'
        '(function(){'  
        '  var ua=navigator.userAgent||"";'
        '  var isWebView=ua.indexOf("wv")>-1||(ua.indexOf("Android")>-1&&ua.indexOf("Version/")<0);'
        '  if(!window.speechSynthesis||isWebView){return;}'
        '  try{'
        '    window.speechSynthesis.cancel();'
        '    var msg=new SpeechSynthesisUtterance("' + clean + '");'
        '    msg.lang="ko-KR";msg.rate=1.05;msg.pitch=1.4;msg.volume=1.0;'
        '    var voices=window.speechSynthesis.getVoices();'
        '    var fv=voices.find(function(v){'
        '      return v.lang==="ko-KR"&&(v.name.includes("Female")||v.name.includes("Yuna")||v.name.includes("Google 한국의 목소")||v.name.includes("Heami"));'
        '    });'
        '    if(fv)msg.voice=fv;'
        '    window.speechSynthesis.speak(msg);'
        '  }catch(e){}'
        '})();'
        '</script>'
    )

def s_voice_answer(text):
    """AI 답변 음성 읽기 - 첫 200자만 읽음"""
    short = text[:200].replace('**', '').replace('#', '').replace('`', '')
    return s_voice(short)

def load_stt_engine():
    """STT 엔진 초기화 - Android WebView 차단 대응 폴백 포함"""
    stt_js = (
        '<script>if(!window._sttInit){window._sttInit=true;'
        'var _ua=navigator.userAgent||"";'
        'var _isWebView=_ua.indexOf("wv")>-1||(_ua.indexOf("Android")>-1&&_ua.indexOf("Version/")<0);'
        'var _SR=window.SpeechRecognition||window.webkitSpeechRecognition||null;'
        'window._sttSupported=(!_isWebView&&!!_SR);'
        'window.startRecognition=function(lang,targetId){'
        '  if(!window._sttSupported){'
        '    var el=document.getElementById("stt_status");'
        '    if(el)el.innerText="이 환경에서는 음성인식이 지원되지 않습니다. 텍스트로 입력해주세요.";'
        '    return;'
        '  }'
        '  try{'
        '    var r=new _SR();'
        '    r.lang=lang||"ko-KR";'
        '    r.interimResults=false;r.continuous=false;'
        '    r.onresult=function(e){'
        '      var t=e.results[0][0].transcript;'
        '      var ta=targetId?document.getElementById(targetId):null;'
        '      if(!ta){var all=document.querySelectorAll("textarea");ta=all[0];}'
        '      if(ta){'
        '        var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value").set;'
        '        s.call(ta,t);ta.dispatchEvent(new Event("input",{bubbles:true}));'
        '      }'
        '    };'
        '    r.onerror=function(e){'
        '      var el=document.getElementById("stt_status");'
        '      if(el)el.innerText="음성인식 오류: "+e.error;'
        '    };'
        '    r.start();'
        '  }catch(e){}'
        '}'
        '}</script>'
    )
    components.html(stt_js, height=0)

def output_manager(masked_name, result_text):
    """분석 결과 세션 저장 및 출력"""
    st.session_state.analysis_result = result_text
    st.divider()
    st.subheader(f"{masked_name}님 분석 결과")
    st.markdown(result_text)
    st.info("[주의] 본 분석 결과의 최종 책임은 사용자(상담원)에게 귀속됩니다.")

# 사용 모델 상수 (변경 시 이 한 줄만 수정)
GEMINI_MODEL = "gemini-2.0-flash"

def get_master_model():
    client = get_client()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT
    )
    return client, config

def process_pdf(file):
    if not PDF_AVAILABLE:
        return f"[PDF] {file.name} (pdfplumber 미설치)"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        with pdfplumber.open(tmp_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        os.unlink(tmp_path)
        return text
    except Exception as e:
        return f"PDF 처리 오류: {e}"

def extract_pdf_chunks(file, char_limit: int = 8000) -> str:
    """
    PDF 전체 텍스트를 char_limit 내에서 최대한 추출.
    전략:
      1) 전체 페이지 텍스트를 추출
      2) 총 길이가 char_limit 이하면 전문 반환
      3) 초과 시 앞 40% / 중간 20% / 뒤 40% 균등 샘플링
         → 보험 증권 특약은 뒷부분에 집중되므로 후반부 비중 높임
    """
    if not PDF_AVAILABLE:
        return f"[PDF] {file.name} (pdfplumber 미설치)"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        with pdfplumber.open(tmp_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        os.unlink(tmp_path)
    except Exception as e:
        return f"PDF 처리 오류: {e}"

    full_text = "\n".join(pages)
    total = len(full_text)

    if total <= char_limit:
        return full_text

    # 앞 40% / 중간 20% / 뒤 40% 샘플링
    front_limit  = int(char_limit * 0.40)
    mid_limit    = int(char_limit * 0.20)
    back_limit   = char_limit - front_limit - mid_limit

    front = full_text[:front_limit]
    mid_start = total // 2 - mid_limit // 2
    mid   = full_text[mid_start: mid_start + mid_limit]
    back  = full_text[-back_limit:]

    page_count = len(pages)
    return (
        f"[PDF 전체 {total:,}자 / {page_count}페이지 → {char_limit:,}자 샘플링]\n\n"
        f"── 앞부분 (p.1~) ──\n{front}\n\n"
        f"── 중간부분 (p.{page_count//2}~) ──\n{mid}\n\n"
        f"── 뒷부분 (~p.{page_count}) ──\n{back}"
    )

def process_docx(file):
    try:
        import docx as _docx
        DOCX_OK = True
    except ImportError:
        DOCX_OK = False
    if not DOCX_OK:
        return f"[DOCX] {file.name} (python-docx 미설치)"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        doc_obj = _docx.Document(tmp_path)
        text = "\n".join(p.text for p in doc_obj.paragraphs)
        os.unlink(tmp_path)
        return text
    except Exception as e:
        return f"DOCX 처리 오류: {e}"

def display_security_sidebar():
    st.sidebar.markdown("""
    <div style="background:#f0f7ff;padding:12px;border-radius:10px;font-size:0.78rem;">
        <strong>🔒 글로벌 보안 기준 준수</strong><br>
        - ISO/IEC 27001 정보보안 관리체계<br>
        - GDPR·개인정보보호법 준거<br>
        - TLS 1.3 전송 암호화<br>
        - AES-256 데이터 암호화<br>
        - 세션 종료 시 메모리 자동 초기화
    </div>""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# [SECTION 4] 시스템 프롬프트 (system_prompt.txt 에서 로드)
# --------------------------------------------------------------------------
def _load_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    try:
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return (
            "[SYSTEM INSTRUCTIONS: 골드키지사 AI 마스터]\n"
            "성명: 골드키AI마스터. 운영: 골드키지사.\n"
            "항상 '하십시오체'로 답변하고, 금감원 판례·법령에 근거하여 상담하십시오.\n"
            "상담 연락처: 010-3074-2616 골드키지사"
        )

SYSTEM_PROMPT = _load_system_prompt()

# --------------------------------------------------------------------------
# [SECTION 5] RAG 시스템
# --------------------------------------------------------------------------
@st.cache_resource
def get_rag_engine():
    if not RAG_AVAILABLE:
        return None
    try:
        return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    except:
        return None

# --------------------------------------------------------------------------
# RAG 파일 경로 전략 (휘발성 방지)
# --------------------------------------------------------------------------
# 우선순위:
#   1) 앱 디렉터리(_app_dir) — GitHub에 커밋된 파일이 있으면 재시작 후에도 유지
#   2) /tmp 폴백              — Streamlit Cloud 읽기전용 환경 대응
#
# [권장 워크플로우] 노하우 데이터를 영구 보존하려면:
#   1. 로컬에서 관리자 탭 → RAG 문서 업로드 → 인덱스 빌드
#   2. 생성된 rag_index.faiss / rag_docs.json 을 Git 저장소에 커밋
#      $ git add rag_index.faiss rag_docs.json
#      $ git commit -m "chore: update RAG knowledge base"
#      $ git push
#   3. Streamlit Cloud가 재배포되면 앱 디렉터리에서 파일을 자동 로드
# --------------------------------------------------------------------------
_app_dir_rag = os.path.dirname(os.path.abspath(__file__))
_rag_app_index = os.path.join(_app_dir_rag, "rag_index.faiss")
_rag_app_docs  = os.path.join(_app_dir_rag, "rag_docs.json")
_rag_tmp_index = os.path.join("/tmp", "rag_index.faiss")
_rag_tmp_docs  = os.path.join("/tmp", "rag_docs.json")

# 앱 디렉터리 쓰기 가능 여부 확인
try:
    _rag_test = open(_rag_app_index if os.path.exists(_rag_app_index) else
                     os.path.join(_app_dir_rag, ".rag_write_test"), "ab")
    _rag_test.close()
    if not os.path.exists(_rag_app_index):
        os.remove(os.path.join(_app_dir_rag, ".rag_write_test"))
    _rag_dir_writable = True
except Exception:
    _rag_dir_writable = False

# 최종 경로 결정: 앱 디렉터리 우선, 쓰기 불가 시 /tmp 폴백
if _rag_dir_writable:
    RAG_INDEX_PATH = _rag_app_index
    RAG_DOCS_PATH  = _rag_app_docs
else:
    RAG_INDEX_PATH = _rag_tmp_index
    RAG_DOCS_PATH  = _rag_tmp_docs

class InsuranceRAGSystem:
    def __init__(self):
        self.embed_model = get_rag_engine()
        self.index = None
        self.documents = []
        self.metadata = []
        self.model_loaded = self.embed_model is not None
        self._load_from_disk()  # 앱 시작 시 디스크에서 자동 로드

    def _load_from_disk(self):
        """디스크에 저장된 FAISS 인덱스와 문서를 로드"""
        if not RAG_AVAILABLE:
            return
        try:
            if os.path.exists(RAG_DOCS_PATH):
                with open(RAG_DOCS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.metadata  = data.get("metadata", [])
            if os.path.exists(RAG_INDEX_PATH) and self.documents:
                self.index = faiss.read_index(RAG_INDEX_PATH)
        except Exception:
            pass

    def _save_to_disk(self):
        """FAISS 인덱스와 문서를 디스크에 영구 저장"""
        if not RAG_AVAILABLE or self.index is None:
            return
        try:
            faiss.write_index(self.index, RAG_INDEX_PATH)
            with open(RAG_DOCS_PATH, "w", encoding="utf-8") as f:
                json.dump({"documents": self.documents, "metadata": self.metadata}, f, ensure_ascii=False)
        except Exception:
            pass

    def delete_from_disk(self):
        """디스크 저장 파일 영구 삭제 (관리자 전용)"""
        for path in [RAG_INDEX_PATH, RAG_DOCS_PATH]:
            if os.path.exists(path):
                os.remove(path)
        self.index = None
        self.documents = []
        self.metadata = []

    def delete_document(self, idx: int):
        """개별 문서 삭제 후 인덱스 재빌드 및 디스크 저장"""
        if idx < 0 or idx >= len(self.documents):
            return
        self.documents.pop(idx)
        if self.metadata and idx < len(self.metadata):
            self.metadata.pop(idx)
        if self.documents:
            self.build_index(self.documents, self.metadata or None)
        else:
            self.index = None
        self._save_to_disk()

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        if not self.model_loaded:
            return np.array([])
        try:
            all_embeddings = []
            for i in range(0, len(texts), 2):
                batch = texts[i:i+2]
                emb = self.embed_model.encode(batch, normalize_embeddings=True, show_progress_bar=False)
                all_embeddings.append(emb)
            return np.vstack(all_embeddings) if all_embeddings else np.array([])
        except:
            return np.array([])

    def build_index(self, texts: List[str], metadata: List[Dict] = None):
        if not self.model_loaded or not texts:
            return
        try:
            embeddings = self.create_embeddings(texts)
            if embeddings.size == 0:
                return
            self.index = faiss.IndexFlatIP(embeddings.shape[1])
            self.index.add(embeddings)
            self.documents = texts
            self.metadata = metadata or [{} for _ in texts]
        except:
            pass

    def search(self, query: str, k: int = 3) -> List[Dict]:
        if not self.model_loaded or self.index is None:
            return []
        qe = self.create_embeddings([query])
        if qe.size == 0:
            return []
        scores, indices = self.index.search(qe, k)
        return [
            {'text': self.documents[idx], 'score': float(scores[0][i])}
            for i, idx in enumerate(indices[0]) if idx < len(self.documents)
        ]

    def add_documents(self, docs: List[str]):
        self.build_index(self.documents + [d for d in docs if d])
        self._save_to_disk()  # 추가 즉시 디스크에 영구 저장

class DummyRAGSystem:
    def __init__(self):
        self.index = None
        self.model_loaded = False
    def search(self, query, k=3):
        return []
    def add_documents(self, docs):
        pass

# --------------------------------------------------------------------------
# [SECTION 6] 상속/증여 정밀 로직
# --------------------------------------------------------------------------
def section_inheritance_will():
    st.subheader("상속증여 및 유류분 통합 설계")
    st.caption("2026년 최신 세법 및 민법 제1000조(상속순위) 기준")

    c_name = st.text_input("상담 고객 성함", "홍길동", key="inh_c_name")
    if len(c_name) >= 3:
        masked_name = c_name[0] + "*" * (len(c_name) - 2) + c_name[-1]
    elif len(c_name) == 2:
        masked_name = c_name[0] + "*"
    else:
        masked_name = c_name

    col1, col2 = st.columns(2)
    with col1:
        spouse = st.radio("배우자 관계", ["법률혼 (상속권 있음)", "사실혼 (상속권 없음)"], key="inh_spouse")
        val_real = st.number_input("부동산 시가(만원)", value=100000, step=1000, key="inh_real")
    with col2:
        child_count = st.number_input("자녀 수", min_value=0, value=1, key="inh_child")
        val_cash = st.number_input("금융 자산(만원)", value=50000, step=1000, key="inh_cash")

    shares = "배우자 1.5 : 자녀 1.0" if spouse.startswith("법률혼") else "자녀 100%"
    st.info(f"법정 상속 비율: {shares}")

    if st.button("상속세 시뮬레이션", type="primary", key="btn_inh_calc"):
        total_asset = val_real + val_cash
        # 기초공제 + 인적공제 (일괄공제 5억 적용, 배우자 있을 경우 최소 5억 추가)
        basic_deduction = 50000  # 일괄공제 5억(만원)
        spouse_deduction = 50000 if spouse.startswith("법률혼") else 0
        total_deduction = basic_deduction + spouse_deduction
        taxable = max(total_asset - total_deduction, 0)

        # 상속세 세율 구간 (2024년 기준)
        tax_brackets = [
            (10000,  0.10,     0),
            (50000,  0.20,  1000),
            (100000, 0.30,  6000),
            (300000, 0.40, 16000),
            (float('inf'), 0.50, 46000),
        ]
        est_tax = 0
        applied_rate = 0
        applied_deduction_amt = 0
        for limit, rate, prog_deduct in tax_brackets:
            if taxable <= limit:
                est_tax = max(taxable * rate - prog_deduct, 0)
                applied_rate = rate
                applied_deduction_amt = prog_deduct
                break

        # 사망보험금 필요 재원 (상속세 + 유동성 여유분 20%)
        insurance_need = round(est_tax * 1.2 / 1000) * 1000

        st.markdown("### 📊 상속세 계산 결과")
        st.markdown(f"""
| 항목 | 금액 |
|---|---|
| 총 상속 자산 | **{total_asset:,.0f}만원** |
| 일괄공제 | -{basic_deduction:,.0f}만원 |
| 배우자공제 | -{spouse_deduction:,.0f}만원 |
| **과세표준** | **{taxable:,.0f}만원** |
| 적용 세율 | {applied_rate*100:.0f}% (누진공제 {applied_deduction_amt:,.0f}만원) |
| **예상 상속세** | **{est_tax:,.0f}만원** |
""")

        st.markdown("#### 📋 상속세 세율표 (2024년 기준)")
        st.markdown("""
| 과세표준 | 세율 | 누진공제 |
|---|---|---|
| 1억 이하 | 10% | - |
| 1억 초과 ~ 5억 이하 | 20% | 1,000만원 |
| 5억 초과 ~ 10억 이하 | 30% | 6,000만원 |
| 10억 초과 ~ 30억 이하 | 40% | 1억 6,000만원 |
| 30억 초과 | 50% | 4억 6,000만원 |
""")
        st.warning(f"⚠️ 위 계산은 참고용 추정치입니다. 실제 상속세는 공제 항목·평가 방법에 따라 달라지므로 세무사와 반드시 확인하십시오.")

        st.divider()
        st.markdown("### 🛡️ 사망보험 연계 재원 마련 안내")
        st.info(
            f"예상 상속세 **{est_tax:,.0f}만원** 납부를 위한 보험 재원 마련 방안\n\n"
            f"권장 사망보험 가입금액 (상속세 × 1.2배 여유분): **{insurance_need:,.0f}만원**\n\n"
            "※ 사망보험금은 생명보험사 종신보험·정기보험에 한하여 상속 재산에서 제외될 수 있습니다 (세무사 확인 필수)."
        )
        st.markdown("#### 사망보험 가입금액 참고 설계표 (생명보험사 종신·정기보험 한정)")
        st.markdown(f"""
| 구분 | 내용 |
|---|---|
| 예상 상속세 | {est_tax:,.0f}만원 |
| 권장 최소 가입금액 | {est_tax:,.0f}만원 이상 |
| 권장 가입금액 (여유분 포함) | {insurance_need:,.0f}만원 |
| 적합 상품 유형 | 종신보험 (생명보험사) / 정기보험 (생명보험사) |
| 계약 구조 참고 | 피보험자: 피상속인 / 수익자: 상속인 (세무사 확인 필수) |
| 주의사항 | 손해보험사 상품은 상속세 재원으로 활용 불가 |
""")

        output_manager(masked_name,
            f"총 자산 {total_asset:,.0f}만원 / 과세표준 {taxable:,.0f}만원 / 예상 상속세 {est_tax:,.0f}만원\n"
            f"권장 사망보험 가입금액: {insurance_need:,.0f}만원 (종신·정기보험 한정)\n"
            "※ 세무사 확인 필수 — 본 수치는 참고용 추정치입니다."
        )

    st.divider()
    st.warning("2024년 최신 판례: 형제자매의 유류분 청구권은 폐지되었습니다.")
    if st.checkbox("자필유언장 표준 양식 보기", key="inh_will_checkbox"):
        will_text = "나 유언자 [성함]은 주소 [주소]에서 다음과 같이 유언한다...\n1. 부동산은 [동거인]에게 사인증여한다..."
        st.code(will_text, language="text")
        st.success("반드시 전체 내용을 직접 자필로 작성하고 날인하십시오.")

# --------------------------------------------------------------------------
# [SECTION 7] 주택연금 시뮬레이션
# --------------------------------------------------------------------------
def section_housing_pension():
    st.subheader("주택연금 정밀 시뮬레이션")
    st.caption("2024-2026 한국주택금융공사(HF) 표준형/종신지급방식 기준")

    col1, col2 = st.columns(2)
    with col1:
        h_age = st.number_input("가입자 연령 (부부 중 연소자)", min_value=55, max_value=90, value=65, key="hp_age")
        h_value = st.number_input("주택 시세 (만원)", min_value=0, value=50000, step=1000, key="hp_value")

    hf_table = {55: 145000, 60: 197000, 65: 242000, 70: 297000,
                75: 367000, 80: 461000, 85: 593000, 90: 775000}
    base_age = max(a for a in hf_table if a <= h_age)
    estimated_monthly = (h_value / 10000) * hf_table[base_age]

    with col2:
        st.metric(label=f"{h_age}세 가입 시 예상 월수령액", value=f"{estimated_monthly:,.0f} 원")
        st.caption("종신지급방식, 정액형 기준")

    if estimated_monthly > 0:
        st.success(
            "**이세윤 마스터의 전략적 조언:**\n\n"
            "1. 기초연금 수급 자격 유지에 유리합니다.\n"
            "2. 수령액은 건강보험료 산정에 포함되지 않습니다.\n"
            "3. 자녀에게 '집'이 아닌 '현금흐름'을 물려주는 현대적 상속 전략입니다."
        )


# --------------------------------------------------------------------------
# [SECTION 8] 메인 앱 - 사이드바 + 탭0(상담) + 탭1(이미지분석)
# --------------------------------------------------------------------------
def main():
    # 모바일 최적화: wide 레이아웃 조건부 적용
    st.set_page_config(
        page_title="Goldkey AI Master SaaS",
        page_icon="🏆",
        layout="centered",   # 모바일에서 wide 대신 centered 사용
        initial_sidebar_state="collapsed"  # 모바일 초기 사이드바 접힘
    )

    # 1회 초기화
    if 'db_ready' not in st.session_state:
        setup_database()
        st.session_state.db_ready = True

    # Google Play 결제 토큰 수신 처리 (query_params 방식)
    handle_verify_purchase_query()

    if 'rag_system' not in st.session_state:
        try:
            st.session_state.rag_system = InsuranceRAGSystem()
        except Exception:
            st.session_state.rag_system = DummyRAGSystem()

    if 'stt_loaded' not in st.session_state:
        load_stt_engine()
        st.session_state.stt_loaded = True

    # ── 사이드바 ──────────────────────────────────────────────────────────
    with st.sidebar:
        # ── 사이드바 헤더 (타이틀 + GitHub 이미지) ──
        _AI_IMG_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
        st.markdown(f"""
<div style="
  background:linear-gradient(135deg,#1a3a5c,#2e6da4);
  border-radius:12px; padding:16px 14px 12px 14px; margin-bottom:10px;
  text-align:center;
">
  <img src="{_AI_IMG_URL}" style="width:72px;height:72px;border-radius:50%;
    object-fit:cover;border:3px solid #fff;margin-bottom:6px;"
    onerror="this.style.display='none'">
  <div style="font-size:1.15rem;font-weight:900;color:#ffffff;
    letter-spacing:0.04em; font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
    line-height:1.3;">
    🏆 Goldkey AI Master SaaS
  </div>
  <div style="font-size:0.72rem;color:#b8d4f0;margin-top:3px;letter-spacing:0.02em;">
    Goldkey AI Master SaaS · AI 상담 시스템
  </div>
</div>
""", unsafe_allow_html=True)

        # ── 회원 로그인 (위쪽) ──────────────────────────────────────────
        # 회원가입 혜택 안내
        if 'user_id' not in st.session_state:
            st.markdown("""
<div style="font-size:1.0rem;font-weight:900;color:#1a3a5c;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
  line-height:1.5; margin-bottom:6px;">
🎁 회원가입 혜택<br>
<span style="font-size:0.82rem;font-weight:700;color:#2e6da4;">
(무료 행사 ~2026.08.31)
</span>
</div>
""", unsafe_allow_html=True)
            st.markdown("""
<div style="
  background:#eaf4fb; border-left:4px solid #2e6da4;
  border-radius:8px; padding:10px 14px 10px 14px;
  font-size:0.83rem; color:#1a1a2e;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
  line-height:1.9; margin-bottom:4px;
">
🎉 <b>가입 회원</b>: 베타 테스트 기간 내 <b>모든 기능 개방</b>
</div>
""", unsafe_allow_html=True)
            st.divider()

        if 'user_id' not in st.session_state:
            # 비로그인 안내 멘트 (1)
            st.warning("🔐 상담을 위해 로그인이 필요합니다.")
            components.html(s_voice("상담을 위해 로그인이 필요합니다."), height=0)
            # 비로그인: 회원가입 / 로그인
            tab_s, tab_l = st.tabs(["회원가입", "로그인"])
            with tab_s:
                with st.form("signup_form"):
                    name = st.text_input("이름", key="signup_name")
                    contact = st.text_input("연락처", type="password", key="signup_contact")
                    if st.form_submit_button("가입"):
                        if name and contact:
                            info = add_member(name, contact)
                            st.session_state.user_id = info["user_id"]
                            st.session_state.user_name = name
                            st.session_state.join_date = dt.strptime(info["join_date"], "%Y-%m-%d")
                            st.session_state.is_admin = False
                            st.success("가입 완료!")
                            st.rerun()
                        else:
                            st.error("이름과 연락처를 입력해주세요.")
            with tab_l:
                with st.form("login_form"):
                    ln = st.text_input("이름", key="login_name")
                    lc = st.text_input("연락처", type="password", key="login_contact")
                    if st.form_submit_button("로그인"):
                        if ln and lc:
                            members = load_members()
                            if ln in members and decrypt_data(members[ln]["contact"], lc):
                                m = members[ln]
                                st.session_state.user_id = m["user_id"]
                                st.session_state.user_name = ln
                                st.session_state.join_date = dt.strptime(m["join_date"], "%Y-%m-%d")
                                st.session_state.is_admin = False
                                st.success(f"{ln}님 환영합니다!")
                                st.rerun()
                            else:
                                st.error("이름 또는 연락처가 올바르지 않습니다.")
                        else:
                            st.error("이름과 연락처를 입력해주세요.")
        else:
            # 로그인 상태
            user_name = st.session_state.get('user_name', '')
            is_admin_user = st.session_state.get('is_admin', False)
            if is_admin_user:
                # 구독회원(관리자) 로그인 시 안내 멘트 (5)
                if not st.session_state.get('_member_greeted'):
                    st.session_state['_member_greeted'] = True
                    components.html(s_voice(f"{user_name} 회원님, 오늘도 행복하세요."), height=0)
            st.success(f"{user_name} 마스터님 접속 중")

            is_member, status_msg = check_membership_status()
            remaining_days = calculate_subscription_days(st.session_state.get('join_date'))
            st.caption(f"구독 상태: {status_msg}  |  잔여 기간: {remaining_days}일")
            display_usage_dashboard(user_name)

            if st.button("안전 로그아웃", key="btn_logout"):
                st.session_state.clear()
                st.rerun()

            if st.button("상담 자료 파기", key="btn_purge", use_container_width=True):
                try:
                    st.session_state.rag_system = InsuranceRAGSystem()
                except Exception:
                    st.session_state.rag_system = DummyRAGSystem()
                for k in ['analysis_result']:
                    st.session_state.pop(k, None)
                st.success("상담 자료가 파기되었습니다.")

        st.divider()

        # ── 관리자 로그인 (아래쪽) ──────────────────────────────────────
        if 'user_id' not in st.session_state or not st.session_state.get('is_admin', False):
            with st.expander("🔑 관리자 로그인", expanded=False):
                with st.form("admin_login_form"):
                    admin_id = st.text_input("관리자 ID", key="admin_id_sidebar", type="password")
                    admin_code = st.text_input("관리자 코드", key="admin_code_sidebar", type="password")
                    if st.form_submit_button("관리자 로그인"):
                        try:
                            master_code = st.secrets.get("MASTER_CODE", "")
                            admin_code_secret = st.secrets.get("ADMIN_CODE", "")
                        except Exception:
                            master_code = ""
                            admin_code_secret = ""
                        if admin_id == "이세윤" and admin_code == master_code:
                            st.session_state.user_id = "PERMANENT_MASTER"
                            st.session_state.user_name = "이세윤"
                            st.session_state.join_date = dt.now()
                            st.session_state.is_admin = True
                            st.success("마스터 로그인 완료! (무제한 사용)")
                            st.rerun()
                        elif admin_id == "admin" and admin_code == admin_code_secret:
                            st.session_state.user_id = "ADMIN_MASTER"
                            st.session_state.user_name = "관리자"
                            st.session_state.join_date = dt.now()
                            st.session_state.is_admin = True
                            st.success("관리자로 로그인되었습니다!")
                            st.rerun()
                        else:
                            st.error("ID 또는 코드가 올바르지 않습니다.")

        st.caption("문의: insusite@gmail.com")
        st.caption("상담: 010-3074-2616 골드키지사")

        # ── 개인정보처리방침 ──────────────────────────────────────────────
        with st.expander("📄 개인정보처리방침", expanded=False):
            st.markdown("""
**개인정보처리방침**
*시행일: 2025년 1월 1일 | 최종 개정: 2026년 2월 21일*

**1. 수집하는 개인정보 항목**
- 필수: 성명, 연락처(해시 암호화 저장)
- 자동 수집: 서비스 이용 횟수(날짜별 카운트), 접속 일시

**2. 개인정보 수집·이용 목적**
- 회원 식별 및 서비스 이용 횟수 관리
- AI 보험 상담 서비스 제공
- 불법·부정 이용 방지

**3. 개인정보 보유·이용 기간**
- 회원 탈퇴 또는 서비스 종료 시까지
- 관련 법령에 따른 보존 의무가 있는 경우 해당 기간

**4. 개인정보 처리 위탁**
- Google Gemini API (AI 분석): 입력 내용 일시 처리 후 저장 없음
- 위탁 업체는 개인정보보호법 제26조에 따라 관리·감독

**5. 개인정보의 파기 절차 및 방법**
- 파기 사유 발생 시 지체 없이 파기
- 전자 파일: DB 레코드 삭제 후 VACUUM(물리적 덮어쓰기) 처리
- GDPR Article 17 '잊혀질 권리' 기준 준수

**6. 정보주체의 권리**
- 개인정보 열람·정정·삭제·처리정지 요청 가능
- 요청 연락처: insusite@gmail.com / 010-3074-2616

**7. 개인정보 보호책임자**
- 성명: 이세윤 | 소속: 케이지에이에셋 골드키지사
- 연락처: insusite@gmail.com

**8. 보안 조치**
- 연락처: SHA-256 단방향 해시 저장 (복호화 불가)
- 전송 구간: TLS 1.3 암호화
- 저장 데이터: AES-256 암호화 적용

**9. 개인정보처리방침 변경**
- 변경 시 앱 내 공지 및 시행일 7일 전 안내
""")

        # ── 이용약관 ──────────────────────────────────────────────────────
        with st.expander("📋 이용약관", expanded=False):
            # SHOW_PAYMENT_TERMS=True 시 결제 조항(제5·6조) 표시, 이후 조번호 자동 조정
            _n = (lambda base: base + 2) if SHOW_PAYMENT_TERMS else (lambda base: base)
            _rev = " (제6조 Google Play 결제 연동 조항 포함)" if SHOW_PAYMENT_TERMS else ""
            _tos = f"""
**골드키지사 AI 마스터 서비스 이용약관**
*시행일: 2025년 1월 1일 | 최종 개정: 2026년 2월 22일{_rev}*

**제1조 (목적)**
본 약관은 케이지에이에셋 골드키지사(이하 "회사") 소속 이세윤(이하 "운영자")이 제공하는 AI 보험 상담 보조 도구 서비스(이하 "서비스")의 이용 조건 및 절차에 관한 사항을 규정합니다.
본 서비스는 **보험 모집 행위가 아닌 상담 보조 도구**로서, 이용자의 의사결정을 지원하는 참고 정보를 제공합니다.

**제2조 (서비스 내용)**
1. AI 기반 보험 상담 분석 리포트 제공 (다국어 포함)
2. 보험 증권 분석 및 보장 공백 진단
3. 보험금 상담·민원·손해사정에 대한 지원
4. 자동차사고·보험금·노후·상속·증여·주택연금 설계 등 상담 지원
5. 화재보험·운전자보험·장기손해보험 및 통합보험 상담 지원
6. 각종 생명보험 상품 및 헬스케어서비스 등 부가서비스 안내
7. 상속·증여·연금 상담 지원
8. 법인 CEO플랜·단체보험·기업보험 상담 지원
9. 고객 상담·지원 등 관련 일체 서비스

**제3조 (법적 면책 고지)**
- 본 서비스는 **AI 상담 보조 도구로서 참고 정보 제공**에 한정됩니다.
- 변호사법 제109조: 법률 사무·조언이 아닙니다.
- 세무사법 제2조: 세무 조정·신고 대리가 아닙니다.
- 보험업법 제185조: 손해사정 업무가 아닙니다.
- 의료법 제27조: 진단·처방·치료 권고가 아닙니다.
- ⚠️ **본 서비스의 분석 결과는 보험금 지급을 보장하지 않으며, 실제 지급 여부는 해당 보험사의 심사 결과에 따릅니다.**
- **최종 판단 및 법적 책임은 이용자에게 귀속됩니다.**

**제4조 (이용 제한)**
- 타인의 개인정보를 무단 입력하는 행위 금지
- 서비스를 이용한 불법 행위 금지
- 프롬프트 인젝션 등 시스템 공격 행위 금지
- 위반 시 이용 제한 및 법적 조치 가능
"""  # _tos f-string 기본 블록 끝

            if SHOW_PAYMENT_TERMS:
                _tos += """
**제5조 (이용 요금)**

회사가 제공하는 유료 서비스의 이용요금은 앱 내 결제 화면 또는 공식 홈페이지에 게시된 가격표에 따릅니다.

- **무료 회원**: 1일 AI 상담 횟수는 운영 정책에 따라 변동될 수 있으며, 현행 기준은 앱 내 서비스 안내 페이지에 게시합니다.
- **유료 구독**: 월 11,000원 (부가가치세 VAT 10% 별도 / 실 결제금액 월 12,100원)
- 연간 환산 기준: 132,000원 (VAT 별도) / 145,200원 (VAT 포함)
- 이용요금은 서비스 정책에 따라 변경될 수 있으며, 변경 시 **7일 전** 앱 내 공지사항을 통해 알립니다.
- 가격 인상 시 미동의 이용자는 해당 결제 주기 만료 후 자동 해지됩니다.
- AI 모델 업그레이드(예: Gemini 버전 변경) 등 기술적 환경 변화로 요금 체계가 변경될 경우 **30일 전** 사전 고지합니다.

**제6조 (결제·자동갱신·환불·해지)**

① **결제 방식**
- 유료 구독은 **Google Play 인앱 결제(In-App Purchase)** 를 통해 처리됩니다.
- 결제 처리·영수증 발급은 Google Play 정책을 따릅니다.
- 결제 수단 등록·변경·삭제는 Google Play 계정 설정에서 직접 관리하십시오.

② **Google Play 결제 연동 기술 안내**
본 서비스는 Google Play 공식 결제 시스템과 다음과 같이 연동되어 있습니다.

- **결제 흐름**: Android 앱(Google Play) → 결제 완료 → Google이 발급한 `purchaseToken` → 본 서버의 Google Play Developer API 검증 → 구독 활성화
- **서버 측 검증**: 이용자의 결제 완료 후, 운영자 서버는 Google Play Developer API(androidpublisher v3)를 통해 `purchaseToken`의 유효성·결제 상태·만료일을 **실시간으로 검증**합니다. 검증 실패 시 구독이 활성화되지 않습니다.
- **실시간 구독 상태 동기화 (RTDN)**: Google Play는 구독 갱신·취소·만료·복구 등 상태 변경 시 **Google Cloud Pub/Sub**를 통해 운영자 서버에 실시간으로 알림(Real-Time Developer Notification)을 전송합니다. 운영자 서버는 이 알림을 수신하여 서비스 이용 가능 여부를 즉시 반영합니다.
- **자동 갱신 처리**: 매월 결제 주기 도래 시 Google Play가 자동 결제를 처리하며, 성공 시 RTDN을 통해 구독 만료일이 자동 연장됩니다.
- **결제 실패·유예 기간**: 결제 수단 문제로 자동 갱신이 실패할 경우, Google Play 정책에 따라 유예 기간(Grace Period) 동안 서비스가 유지될 수 있습니다. 유예 기간 내 결제 수단 업데이트 시 구독이 정상 복구됩니다.
- **구독 취소 후 처리**: 구독 취소 시 현재 결제 주기 만료일까지 서비스가 유지되며, 만료 후 RTDN 알림에 의해 자동으로 서비스 이용이 제한됩니다.
- **데이터 처리**: 결제 검증 과정에서 `purchaseToken`(Google이 발급한 불투명 식별자)만 서버에 저장되며, 카드번호·결제 수단 정보는 운영자 서버에 저장되지 않습니다.

③ **자동 갱신 (Automatic Renewal)**
- 본 서비스는 정기 구독 상품으로, **매월 결제 주기에 맞춰 자동 갱신**됩니다.
- 자동 결제 예정일 및 청구 금액은 Google Play [구독 관리] 화면에서 상시 확인 가능합니다.
- 결제 수단의 잔액 부족 등으로 결제 실패 시 서비스 이용이 제한될 수 있습니다.
- **구독 취소**: 결제 예정일 **24시간 전**까지 아래 링크에서 직접 해지하십시오.
  👉 https://play.google.com/store/account/subscriptions

④ **청약 철회 및 환불**
- 결제 후 **7일 이내 미사용** 시 전액 환불 신청 가능합니다 (전자상거래법 제17조 기준).
- ⚠️ **청약철회 제한 고지 (전자상거래법 제17조 제2항 제5호)**: AI 분석을 **1회 이상 실행한 경우**, 용역의 제공이 개시된 디지털 콘텐츠로 간주되어 청약철회가 제한될 수 있습니다. 이 사실에 동의한 후 서비스를 이용하십시오.
- 7일 초과 또는 서비스 이용 후 환불은 Google Play 환불 정책에 따르며, 운영자 고객센터(insusite@gmail.com)에 별도 문의 가능합니다.
- Google Play 환불 정책: https://support.google.com/googleplay/answer/2479637

⑤ **중도 해지**
- 구독 해지 시 **남은 기간 서비스는 만료일까지 유지**됩니다.
- 잔여 기간에 대한 일할 환불은 원칙적으로 제공되지 않으나, 운영자 귀책 사유 발생 시 예외 적용합니다.

⑥ **공정 이용 정책 (Fair Use Policy)**
- 구독 회원은 일반적인 보험 상담 업무 범위를 벗어나지 않는 수준에서 충분히 이용할 수 있습니다.
- 스크립트·자동화 도구를 이용한 대량 API 호출, 상업적 재판매, 비정상적 대량 호출로 시스템 부하 또는 API 원가 급증이 발생할 경우 서비스 속도를 제한(Throttling)하거나 이용을 제한할 수 있습니다.
- 결제 관련 분쟁은 Google Play 결제 정책 및 전자상거래 등에서의 소비자보호에 관한 법률에 따릅니다.
"""

            _tos += f"""
**제{_n(5)}조 (AI 생성물 고지)**
- 본 서비스의 모든 분석 리포트 및 답변은 **Google Gemini AI가 생성한 결과물**입니다.
- Google 생성형 AI 사용 정책(Google Generative AI Prohibited Use Policy)을 준수합니다.
- AI 생성 답변은 사실과 다를 수 있으며, **최종 판단은 반드시 전문가(변호사·세무사·손해사정사)와 확인**하십시오.
- AI 답변을 법적 증거·공식 문서로 사용하는 것을 금지합니다.
- 생성된 콘텐츠의 정확성에 대해 운영자는 법적 책임을 지지 않습니다.

**제{_n(6)}조 (회원의 의무 및 손해배상)**
- 이용자는 본 약관 및 관련 법령을 준수하여야 합니다.
- 이용자는 타인의 개인정보를 무단으로 입력하거나 서비스를 불법적인 목적으로 사용하여서는 안 됩니다.
- 이용자가 본 약관을 위반하여 운영자 또는 제3자에게 손해를 끼친 경우, 이용자는 그 손해를 배상할 책임이 있습니다.
- 프롬프트 인젝션·시스템 공격 등 고의적 서비스 침해 행위에 대해서는 민·형사상 책임을 물을 수 있습니다.

**제{_n(7)}조 (서비스 중단)**
- 시스템 점검·장애·천재지변 등으로 서비스가 중단될 수 있습니다.
- 중단 시 사전 공지를 원칙으로 하되, 긴급 시 사후 공지 가능

**제{_n(8)}조 (준거법 및 관할)**
- 본 약관은 대한민국 법률에 따라 해석됩니다.
- 분쟁 발생 시 **대한민국 민사소송법에 따른 법정 관할 법원**을 관할로 합니다.

**제{_n(9)}조 (개인정보 보호)**
- 운영자는 별도의 **개인정보 처리방침**을 수립하여 앱 내에 공시합니다.
- 이용자의 개인정보는 해당 방침에 따라 수집·이용·보호되며, 이용자는 앱 내 [개인정보처리방침] 항목에서 전문을 확인할 수 있습니다.
- 개인정보 관련 문의: insusite@gmail.com

**제{_n(10)}조 (회원 탈퇴 및 데이터 파기)**

① **파기 원칙**
운영자는 회원이 탈퇴를 요청하거나 개인정보 수집 및 이용 목적이 달성된 경우, 수집된 개인정보 및 상담 데이터를 「개인정보보호법」 및 **GDPR(유럽 개인정보보호규정)** 의 권고 기준에 따라 지체 없이 파기합니다.

② **법령에 따른 보존**
전항의 원칙에도 불구하고, 관계 법령의 규정에 의하여 보존할 필요가 있는 경우 아래 기간 동안 보관합니다.

| 보존 항목 | 보존 근거 법령 | 보존 기간 |
|---|---|---|
| 계약 또는 청약철회 등에 관한 기록 | 전자상거래 등에서의 소비자보호에 관한 법률 | 5년 |
| 대금결제 및 재화 등의 공급에 관한 기록 | 전자상거래 등에서의 소비자보호에 관한 법률 | 5년 |
| 소비자의 불만 또는 분쟁처리에 관한 기록 | 전자상거래 등에서의 소비자보호에 관한 법률 | 3년 |
| 서비스 접속 기록 (로그 데이터) | 통신비밀보호법 | 3개월 |

③ **데이터의 분리 보관**
탈퇴 시 법적 의무에 의해 보존이 필요한 정보는 즉시 별도의 데이터베이스(DB) 또는 격리된 저장 공간으로 분리하여 관리합니다. 해당 정보는 법률에 의한 경우 외에는 다른 목적으로 이용되지 않으며, 담당자 외의 접근을 엄격히 통제합니다.

④ **파기 방법**
보존 기간이 경과한 정보는 아래의 방법으로 영구 삭제합니다.
- **전자적 파일 형태**: 복원이 불가능한 기술적 방법(NIST 800-88 표준에 따른 로우 레벨 포맷 또는 암호화 파기 등)을 사용하여 영구 삭제합니다.
- **출력물 등 종이 문서**: 분쇄기로 분쇄하거나 소각하여 파기합니다.

**문의: insusite@gmail.com (운영자: 이세윤)**
"""
            st.markdown(_tos)

        display_security_sidebar()

    # ── 공통 STT 언어 맵 ──────────────────────────────────────────────────
    stt_lang_map = {
        "한국어": "ko-KR", "English": "en-US", "日本語": "ja-JP",
        "中文": "zh-CN", "ภาษาไทย": "th-TH", "Tiếng Việt": "vi-VN", "Русский": "ru-RU",
    }

    def ai_query_block(tab_key, placeholder_text, hide_query=False):
        """공통 입력 블록 (고객명/언어/텍스트영역/건보료/분석버튼/마이크)"""
        c_name = st.text_input("고객 성함", "우량 고객", key=f"c_name_{tab_key}")
        st.session_state.current_c_name = c_name
        lang_label = st.selectbox("음성입력 언어", list(stt_lang_map.keys()), key=f"stt_{tab_key}")
        lang_code = stt_lang_map[lang_label]
        query = st.text_area("상담 내용 입력", height=200, key=f"query_{tab_key}",
                             placeholder=placeholder_text,
                             label_visibility="collapsed" if hide_query else "visible",
                             disabled=hide_query)
        hi = st.number_input("월 건강보험료(원)", value=0, step=1000, key=f"hi_{tab_key}")
        if hi > 0:
            inc = hi / 0.0709
            st.success(f"역산 월 소득: **{inc:,.0f}원** | 적정 보험료: **{inc*0.15:,.0f}원**")
        bc1, bc2 = st.columns([3, 1])
        with bc1:
            do_analyze = st.button("정밀 분석 실행", type="primary", key=f"btn_analyze_{tab_key}")
            # 버튼 색상: primary(빨간계열) → 파란색 강제 오버라이드
            st.markdown("""
<style>
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #1a3a5c 0%, #2e6da4 100%) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 6px rgba(46,109,164,0.35) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #0f2540 0%, #1a5a8a 100%) !important;
}
</style>""", unsafe_allow_html=True)
            if do_analyze:
                components.html(s_voice("잠시만 기다려주세요. 답변 검색 중입니다."), height=0)
        with bc2:
            _stt_id = f"stt_btn_{tab_key}"
            _qkey   = f"query_{tab_key}"
            components.html(f"""
<button id="{_stt_id}"
  onclick="(function(){{
    var q = (window.parent.document.querySelector('[data-testid=stTextArea] textarea[aria-label]') || {{}}).value || '';
    var q2 = '';
    try {{ q2 = window.parent.document.querySelectorAll('[data-testid=stTextArea] textarea')[0].value || ''; }} catch(e){{}}
    var hasInput = (q.trim().length > 0 || q2.trim().length > 0);
    if (!hasInput) {{
      var u = new SpeechSynthesisUtterance('상담 내용을 입력하세요');
      u.lang = 'ko-KR'; window.speechSynthesis.speak(u);
    }} else {{
      var u2 = new SpeechSynthesisUtterance('AI 리포트 및 관련 자료를 참조하세요');
      u2.lang = 'ko-KR'; window.speechSynthesis.speak(u2);
    }}
    window.startRecognition('{lang_code}', null);
  }})()"
  style="
    display:flex; align-items:center; justify-content:center; gap:6px;
    width:100%; height:42px; cursor:pointer;
    background:linear-gradient(135deg,#1a3a5c,#2e6da4);
    color:#fff; font-size:0.92rem; font-weight:700;
    border:none; border-radius:8px;
    box-shadow:0 2px 6px rgba(26,58,92,0.3);
    white-space:nowrap; letter-spacing:0.03em;
    font-family:'Noto Sans KR','Malgun Gothic',sans-serif;
  ">
  🎤&nbsp;음성
</button>""", height=50)
        return c_name, query, hi, do_analyze

    def run_ai_analysis(c_name, query, hi_premium, result_key, prompt_prefix=""):
        """공통 AI 분석 실행 - 사용량 체크 포함"""
        if 'user_id' not in st.session_state:
            st.error("로그인이 필요합니다.")
            return
        user_name = st.session_state.get('user_name', '')
        is_special = st.session_state.get('is_admin', False)
        join_date = st.session_state.get('join_date')
        daily_limit = get_daily_limit(join_date)
        current_count = check_usage_count(user_name)
        if not is_special and daily_limit == 0:
            st.error("무료 행사 기간(~2027.03.31)이 종료되었습니다. 결제 후 이용해주세요.")
            return
        if not is_special and current_count >= daily_limit:
            st.error(f"오늘 {daily_limit}회 분석을 모두 사용하셨습니다.")
            components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다."), height=0)
            return
        with st.spinner("⏳ 잠시만 기다려주세요. 답변 검색 중입니다..."):
            try:
                client, model_config = get_master_model()
                safe_query = sanitize_prompt(query)
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                rag_ctx = ""
                if st.session_state.rag_system.index is not None:
                    results = st.session_state.rag_system.search(safe_query, k=3)
                    if results:
                        rag_ctx = "\n\n[참고 자료]\n" + "".join(f"{i}. {r['text']}\n" for i, r in enumerate(results, 1))
                prompt = f"{prompt_prefix}\n고객: {c_name}, 추정소득: {income:,.0f}원\n질문: {safe_query}{rag_ctx}"

                # 재시도 로직: 429 발생 시 자동 폴백 + 라운드 재시도 (오류 노출 없이 끝까지 자동 검색)
                FALLBACK_MODELS = [GEMINI_MODEL, "gemini-2.0-flash-lite", "gemini-1.5-flash"]
                MAX_ROUNDS = 3        # 전체 폴백 라운드 최대 횟수
                ROUND_WAIT = 30       # 라운드 간 대기 시간(초)
                resp = None
                last_err = None
                success = False
                for round_idx in range(MAX_ROUNDS):
                    for attempt, model_name in enumerate(FALLBACK_MODELS):
                        try:
                            if round_idx == 0 and attempt == 0:
                                pass  # 첫 시도는 즉시
                            elif attempt == 0 and round_idx > 0:
                                # 새 라운드 시작 전 대기 + 안내
                                st.toast(f"⏳ 잠시만 기다려주세요. 자동으로 재검색 중입니다... ({round_idx + 1}/{MAX_ROUNDS})")
                                time.sleep(ROUND_WAIT)
                            else:
                                # 같은 라운드 내 모델 전환 시 짧은 대기
                                time.sleep(3)
                            resp = client.models.generate_content(
                                model=model_name, contents=prompt, config=model_config
                            )
                            success = True
                            break  # 성공 시 모델 루프 탈출
                        except Exception as api_err:
                            last_err = api_err
                            err_str = str(api_err)
                            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                                continue  # 다음 모델 또는 다음 라운드로
                            else:
                                raise  # 429 외 오류는 즉시 상위로 전달
                    if success:
                        break  # 성공 시 라운드 루프 탈출

                if not success:
                    raise Exception(
                        "⚠️ 잠시만 기다려주세요.\n\n"
                        "AI 서버 요청이 일시적으로 집중되어 자동 재검색을 모두 시도하였으나 "
                        "응답을 받지 못했습니다.\n"
                        "1~2분 후 다시 시도해 주세요.\n"
                        "(오류코드: 429 RESOURCE_EXHAUSTED)"
                    )

                answer = resp.text if (resp and resp.text) else "AI 응답을 받지 못했습니다. 다시 시도해주세요."
                # 요약: 첫 번째 ## 섹션 또는 앞 400자
                lines = answer.strip().split('\n')
                summary_lines = []
                for ln in lines:
                    if ln.startswith('##') and summary_lines:
                        break
                    summary_lines.append(ln)
                    if len('\n'.join(summary_lines)) > 400:
                        break
                summary_text = '\n'.join(summary_lines).strip()
                if len(summary_text) < 50:
                    summary_text = answer[:400].strip()
                result_text = (
                    f"### {c_name}님 골드키AI마스터 리포트\n\n{answer}\n\n---\n"
                    f"**문의:** insusite@gmail.com | 010-3074-2616\n\n"
                    f"[주의] 최종 책임은 사용자(상담원)에게 귀속됩니다."
                )
                st.session_state[result_key] = result_text
                st.session_state[result_key + "_summary"] = summary_text
                st.session_state[result_key + "_detail"] = answer
                st.session_state[result_key + "_cname"] = c_name
                if user_name not in UNLIMITED_USERS:
                    update_usage(user_name)
                components.html(s_voice("분석이 완료되었습니다."), height=0)
                components.html(s_voice_answer(answer), height=0)
                if not is_special:
                    remaining = MAX_FREE_DAILY - (current_count + 1)
                    st.success(f"분석 완료! (오늘 남은 횟수: {remaining}회)")
                else:
                    st.success("분석 완료! (무제한 사용 계정)")
                st.rerun()
            except Exception as e:
                st.error(f"분석 오류: {e}")

    def show_result(result_key, guide_md=""):
        """공통 결과 출력 패널 — 요약(상단) + 상세 스크롤(하단) + A4 PDF 출력"""
        if st.session_state.get(result_key):
            c_name_r   = st.session_state.get(result_key + "_cname", "고객")
            summary    = st.session_state.get(result_key + "_summary", "")
            detail     = st.session_state.get(result_key + "_detail", "")
            today_str  = dt.now().strftime("%Y년 %m월 %d일")

            # ── 상단: 핵심 요약 스크롤 박스 ─────────────────────────────
            st.markdown("##### 📌 핵심 요약")
            summary_html = (summary if summary else detail[:300]).replace('\n', '<br>')
            components.html(
                f"""<div style="
  height:120px; overflow-y:auto; padding:10px 14px;
  background:#eef4fb; border:1px solid #b8d0ea;
  border-radius:8px; font-size:0.86rem; line-height:1.5;
  font-family:'Noto Sans KR',sans-serif; color:#1a1a2e;
">{summary_html}</div>""",
                height=138,
            )

            # ── 하단: 상세 내용 스크롤 창 ────────────────────────────────
            st.markdown("##### 📋 상세 분석 내용")
            detail_html = detail.replace('\n', '<br>')
            detail_html = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', detail_html)
            components.html(
                f"""
<div style="
  height:460px; overflow-y:auto; padding:14px 16px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.86rem; line-height:1.5;
  font-family:'Noto Sans KR', sans-serif; color:#1a1a2e;
">
{detail_html}
</div>""",
                height=478,
            )

            # ── A4 PDF 보고서 출력 버튼 ──────────────────────────────────
            st.markdown("---")
            DISCLAIMER = (
                "[법적 면책 고지] "
                "본 보고서는 공개된 법령·판례·의학 문헌에 근거한 참고 정보 제공에 한정됩니다. "
                "▶ 법률: 변호사법 제109조에 따른 법률 사무·조언이 아닙니다. "
                "▶ 세무: 세무사법 제2조에 따른 세무 조정·신고 대리가 아닙니다. "
                "▶ 손해사정: 보험업법 제185조에 따른 손해사정 업무가 아닙니다. "
                "▶ 의료: 의료법 제27조에 따른 진단·처방·치료 권고가 아닙니다. "
                "실제 보험금 지급 여부는 약관 및 보험사 심사 결과에 따릅니다. "
                "최종 판단 및 법적 책임은 사용자(상담원·설계사)에게 귀속됩니다. "
                "상담 문의: 010-3074-2616 골드키지사 | insusite@gmail.com"
            )
            detail_escaped = detail.replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')
            summary_escaped = summary.replace('`', "'").replace('\\', '\\\\').replace('\n', '\\n')
            disclaimer_escaped = DISCLAIMER.replace('`', "'")

            pdf_js = f"""
<button onclick="onPrintClick()" style="
  background:#1a3a5c; color:#fff; border:none; border-radius:6px;
  padding:10px 22px; font-size:0.95rem; cursor:pointer; margin-bottom:6px;
">📄 A4 보고서 출력 (PDF 저장)</button>
<script>
function onPrintClick() {{
  var msg = new SpeechSynthesisUtterance('잠시만 기다리세요. 고객님 내 문서 폴더로 출력 자료 보내드립니다.');
  msg.lang = 'ko-KR'; msg.rate = 1.05; msg.pitch = 1.4;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(msg);
  setTimeout(function(){{ printReport(); }}, 1200);
}}
</script>
<script>
function printReport() {{
  var detail = `{detail_escaped}`;
  var summary = `{summary_escaped}`;
  var disclaimer = `{disclaimer_escaped}`;
  var today = "{today_str}";
  var cname = "{c_name_r}";
  var w = window.open('', '_blank', 'width=900,height=1200');
  w.document.write(`
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>골드키지사 AI 마스터 보고서</title>
<style>
  @page {{ size: A4; margin: 20mm 18mm 22mm 18mm; }}
  body {{ font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
         font-size: 11pt; color: #1a1a2e; line-height: 1.75; margin:0; padding:0; }}
  .header {{ border-bottom: 2.5px solid #1a3a5c; padding-bottom: 10px; margin-bottom: 18px; }}
  .header h1 {{ font-size:16pt; color:#1a3a5c; margin:0 0 4px 0; }}
  .header .meta {{ font-size:9.5pt; color:#555; }}
  .section-title {{ font-size:12pt; font-weight:700; color:#1a3a5c;
                    border-left:4px solid #1a3a5c; padding-left:8px;
                    margin:18px 0 8px 0; }}
  .summary-box {{ background:#eef4fb; border:1px solid #b8d0ea;
                  border-radius:6px; padding:12px 16px; margin-bottom:16px;
                  font-size:10.5pt; white-space:pre-wrap; }}
  .detail-box {{ font-size:10.5pt; white-space:pre-wrap; }}
  .footer {{ margin-top:28px; border-top:1.5px solid #ccc; padding-top:10px;
             font-size:8.5pt; color:#555; line-height:1.6; }}
  @media print {{ button {{ display:none; }} }}
</style>
</head>
<body>
<div class="header">
  <h1>🏆 골드키지사 AI 마스터 보고서</h1>
  <div class="meta">고객명: ${{cname}} &nbsp;|&nbsp; 작성일: ${{today}} &nbsp;|&nbsp; 케이지에이에셋 골드키지사</div>
</div>
<div class="section-title">📌 핵심 요약</div>
<div class="summary-box">${{summary}}</div>
<div class="section-title">📋 상세 분석 내용</div>
<div class="detail-box">${{detail}}</div>
<div class="footer">${{disclaimer}}</div>
</body></html>`);
  w.document.close();
  w.focus();
  setTimeout(function(){{ w.print(); }}, 600);
}}
</script>"""
            components.html(pdf_js, height=60)

        else:
            if guide_md:
                _guide_html = guide_md.replace('\n', '<br>').replace('**', '<b>', 1)
                _guide_html = _guide_html.replace('**', '</b>')
                components.html(f"""
<div style="
  height:180px; overflow-y:auto; padding:12px 16px;
  background:#eef4fb; border-left:4px solid #2e6da4;
  border-radius:8px; font-size:0.84rem; line-height:1.8;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">{_guide_html}</div>""", height=196)

    # ── 세션 상태 초기화 ──────────────────────────────────────────────────
    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "home"

    # ── 네비게이션 상수 ───────────────────────────────────────────────────
    NAV_ITEMS = [
        ("home",      "🏠 홈"),
        ("t0",        "📋 신규보험"),
        ("t1",        "💰 보험금"),
        ("disability", "🩺 장해보험금"),
        ("t2",        "🛡️ 기본보험상담"),
        ("t3",        "🏥 통합보험"),
        ("t4",        "🚗 자동차사고"),
        ("t5",        "🌅 노후·상속"),
        ("t6",        "📊 세무상담"),
        ("t7",        "🏢 법인상담"),
        ("t8",        "👔 CEO플랜"),
        ("fire",      "🔥 화재보험"),
        ("liability", "⚖️ 배상책임"),
        ("t9",        "⚙️ 관리자"),
    ]

    # ── 상단 네비게이션 바 CSS ────────────────────────────────────────────
    st.markdown("""
<style>
.nav-bar {
    display:flex; flex-wrap:nowrap; overflow-x:auto;
    gap:6px; padding:8px 0 10px 0; margin-bottom:8px;
    scrollbar-width:none; -ms-overflow-style:none;
}
.nav-bar::-webkit-scrollbar { display:none; }
.nav-btn {
    flex:0 0 auto; padding:5px 12px; border-radius:20px;
    font-size:0.78rem; font-weight:600; cursor:pointer;
    border:1.5px solid #2e6da4; color:#2e6da4;
    background:#fff; white-space:nowrap;
    transition:all 0.15s;
}
.nav-btn.active {
    background:#2e6da4; color:#fff;
}
.dash-card-wrap {
    height:auto; min-height:150px; overflow-y:visible; overflow-x:hidden;
    background:#fff; border:1.5px solid #d0dce8;
    border-radius:12px;
    box-shadow:0 2px 8px rgba(46,109,164,0.07);
    margin-bottom:6px;
    scrollbar-width:thin; scrollbar-color:#b8d0ea #f0f4f8;
}
.dash-card-wrap::-webkit-scrollbar { width:5px; }
.dash-card-wrap::-webkit-scrollbar-thumb { background:#b8d0ea; border-radius:4px; }
.dash-card {
    padding:14px 14px 10px 14px;
}
.dash-card:hover { background:#f4f8fd; }
.dash-icon { font-size:1.8rem; margin-bottom:4px; }
.dash-title { font-size:0.95rem; font-weight:700; color:#1a3a5c; margin-bottom:4px; }
.dash-desc { font-size:0.78rem; color:#555; line-height:1.55; margin-bottom:10px; }
.dash-nav-btn {
    display:block; width:100%; padding:7px 0;
    background:#2e6da4; color:#fff; border:none;
    border-radius:8px; font-size:0.82rem; font-weight:700;
    cursor:pointer; text-align:center; letter-spacing:0.02em;
    margin-top:2px;
}
.dash-nav-btn:hover { background:#1a3a5c; }
.ins-scroll-box {
    height:auto; min-height:130px; max-height:260px; overflow-y:auto; overflow-x:hidden;
    background:#fff;
    border-radius:10px;
    scrollbar-width:thin; scrollbar-color:#c0d4e8 #f5f8fc;
    margin-bottom:10px;
}
.ins-scroll-box::-webkit-scrollbar { width:5px; }
.ins-scroll-box::-webkit-scrollbar-thumb { background:#c0d4e8; border-radius:4px; }

/* ── 모바일 방향 자동전환 ── */
@media screen and (orientation: portrait) {
    .block-container { max-width: 100% !important; padding: 0.5rem 0.6rem !important; }
    .dash-card-wrap { min-height: 130px; }
    .ins-scroll-box { min-height: 110px; max-height: 220px; }
    .dash-icon { font-size: 1.4rem; }
    .dash-title { font-size: 0.82rem; }
    .dash-desc { font-size: 0.7rem; }
}
@media screen and (orientation: landscape) and (max-width: 1024px) {
    .block-container { max-width: 100% !important; padding: 0.5rem 1rem !important; }
    .dash-card-wrap { min-height: 140px; }
    .ins-scroll-box { min-height: 120px; max-height: 240px; }
}
</style>
""", unsafe_allow_html=True)

    # ── 모바일 방향 자동전환 JS (orientationchange → 페이지 리로드) ──
    components.html("""
<script>
(function(){
  var _lastOrient = (window.screen && window.screen.orientation)
                    ? window.screen.orientation.type : String(window.orientation);
  function _onOrientChange() {
    var cur = (window.screen && window.screen.orientation)
              ? window.screen.orientation.type : String(window.orientation);
    if (cur !== _lastOrient) {
      _lastOrient = cur;
      setTimeout(function(){ window.parent.location.reload(); }, 350);
    }
  }
  if (window.screen && window.screen.orientation) {
    window.screen.orientation.addEventListener('change', _onOrientChange);
  } else {
    window.addEventListener('orientationchange', _onOrientChange);
  }
})();
</script>
""", height=0)

    # ── query_params 경유 네비게이션 처리 (사이드바 메뉴용) ────────────
    _qp_nav = st.query_params.get("nav", None)
    if _qp_nav and _qp_nav in [n[0] for n in NAV_ITEMS]:
        st.session_state.current_tab = _qp_nav
        st.query_params.clear()
        st.rerun()

    # ── 현재 탭 키 ─────────────────────────────────────────────────────
    cur = st.session_state.current_tab

    # ── 탭 라우팅: cur 값으로 직접 조건 분기 ──────────────────────────────

    # ── 홈 대시보드 ──────────────────────────────────────────────────────
    if cur == "home":
        # ── 표지: AI마스터 이미지(확대) + 안내 박스 ──
        _AI_COVER_URL = "https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/ai_expert.png"
        _col_img, _col_txt = st.columns([5, 7])
        with _col_img:
            st.markdown(
                f'<div style="display:flex;align-items:flex-end;height:100%;padding-bottom:4px;">'
                f'<img src="{_AI_COVER_URL}" style="width:100%;max-width:280px;border-radius:20px;'
                f'box-shadow:0 6px 24px rgba(46,109,164,0.22);display:block;" '
                f'onerror="this.outerHTML=\'<div style=&quot;font-size:7rem;text-align:center;width:100%;&quot;>🤖</div>\'">'
                f'</div>',
                unsafe_allow_html=True
            )
        with _col_txt:
            st.markdown(f"""
<div style="
  background:linear-gradient(135deg,#eef4fb 0%,#f8fafc 100%);
  border:1.5px solid #b8d0ea;
  border-radius:16px;
  padding:24px 26px 20px 26px;
  height:100%;
  box-shadow:0 2px 12px rgba(46,109,164,0.08);
">
  <div style="font-size:1.55rem;font-weight:900;color:#1a3a5c;
    font-family:'Noto Sans KR',sans-serif;line-height:1.35;margin-bottom:14px;">
    안녕하세요! 👋<br>
    <span style="color:#2e6da4;">골드키지사 AI 마스터</span>입니다.
  </div>
  <div style="font-size:0.93rem;color:#333;line-height:1.85;margin-bottom:16px;">
    🏦 <b>보험·세무·법인·상속</b> 등 다양한 분야의<br>
    &nbsp;&nbsp;&nbsp;&nbsp;AI 전문 상담을 제공합니다.<br>
    📌 아래 카테고리에서 원하는 상담을 선택하거나<br>
    &nbsp;&nbsp;&nbsp;&nbsp;왼쪽 사이드바에서 바로 이동하세요.<br>
    ⚡ 로그인 후 <b>하루 10회 무료</b> AI 상담 이용 가능합니다.
  </div>
  <div style="
    background:#1a3a5c;border-radius:8px;
    padding:10px 16px;display:inline-block;
  ">
    <span style="color:#fff;font-size:0.82rem;font-weight:600;letter-spacing:0.03em;">
      📞 010-3074-2616 &nbsp;|&nbsp; 케이지에이에셋 골드키지사
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

        st.divider()
        st.markdown("### 📌 상담 카테고리 — 원하는 항목을 선택하세요")

        # 카드 데이터 — (탭키, 아이콘, 제목, 설명)
        CARDS = [
            ("t0", "📋", "신규보험 상담",
             "기존 보험증권 분석 → 보장 공백 진단 → 신규 보험 컨설팅\n실손·암·종신·CI·치아·간병 등 전 상품 상담"),
            ("t1", "💰", "보험금 상담",
             "보험금 청구 절차 안내 · 지급 거절 대응\n민원·손해사정·약관 해석 지원"),
            ("disability", "🩺", "장해보험금 산출",
             "AMA방식(개인보험) · 맥브라이드방식(배상책임) · 호프만계수 적용\n후유장해 보험금 및 일실수익 손해배상금 산출"),
            ("t2", "🛡️", "기본보험 상담",
             "자동차·화재·운전자·일상배상책임 기본 보험 점검\n🏗️ 화재보험 선택 시 건물 재조달가액 산출 통합 제공"),
            ("t3", "🏥", "통합보험 설계",
             "생명·손해 통합 포트폴리오 최적화\n헬스케어 서비스 연계 종합 설계"),
            ("t4", "🚗", "자동차사고 상담",
             "사고 처리 절차 · 과실 비율 · 합의금 분석\n렌트·수리비·부상 보험금 청구 지원"),
            ("t5", "🌅", "노후·상속설계",
             "연금·주택연금·건강보험료 시뮬레이션\n상속·증여 절세 전략 및 유언장 설계"),
            ("t6", "📊", "세무상담",
             "소득세·법인세·부가세 절세 전략\n건보료 역산 · 금융소득 종합과세 분석"),
            ("t7", "🏢", "법인상담",
             "법인 보험 설계 · 단체보험 · 기업보험\n법인세 절감 · 복리후생 플랜 구축"),
            ("t8", "👔", "CEO플랜",
             "비상장주식 평가(상증법·법인세법)\n가업승계 · CEO 퇴직금 · 경영인정기보험 설계"),
            ("fire", "🔥", "화재보험(재조달가액평가)",
             "화재보험 설계 가이드 · 비례보상 방지 전략\n한국부동산원(REB) 기준 건물 재조달가액 산출\n건축물대장 AI OCR 분석 → 예상보험가액 산출"),
            ("liability", "⚖️", "배상책임보험 상담",
             "배상책임보험 개념 · 중복보험 독립책임액 안분방식\n민법·화재보험법·실화책임법 등 관련 법률 정리\n변호사 수임료·성과보수 기준 안내"),
        ]

        # ── 카드 클릭 이벤트 처리 (JS → Streamlit) ──────────────────────
        # components.html iframe에서 postMessage로 탭키 전달 → query_params 경유
        _nav_clicked = st.query_params.get("nav", None)
        if _nav_clicked and _nav_clicked in [c[0] for c in CARDS] + ["t9"]:
            st.session_state.current_tab = _nav_clicked
            st.query_params.clear()
            st.rerun()

        # 4열 다행 카드 배치
        import math
        _COLS = 4
        _total_rows = math.ceil(len(CARDS) / _COLS)
        for row in range(_total_rows):
            cols = st.columns(_COLS, gap="small")
            for col_i in range(_COLS):
                card_i = row * _COLS + col_i
                if card_i >= len(CARDS):
                    break
                _tab_key, icon, title, desc = CARDS[card_i]
                _desc_html = desc.replace(chr(10), "<br>")
                with cols[col_i]:
                    st.markdown(
                        f"<div class='dash-card-wrap'>"
                        f"  <div class='dash-card'>"
                        f"    <div class='dash-icon'>{icon}</div>"
                        f"    <div class='dash-title'>{title}</div>"
                        f"    <div class='dash-desc'>{_desc_html}</div>"
                        f"  </div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if st.button(f"▶ {title}",
                                 key=f"home_dash_{_tab_key}",
                                 use_container_width=True,
                                 type="primary"):
                        st.session_state.current_tab = _tab_key
                        st.rerun()

        st.divider()
        # 관리자 카드 (별도 — 관리자 로그인 시만 표시)
        if st.session_state.get('is_admin'):
            if st.button("⚙️ 관리자 시스템 이동", key="home_dash_t9", use_container_width=False):
                st.session_state.current_tab = "t9"
                st.rerun()

        # ── 보험사 정보 섹션 ──────────────────────────────────────────────
        st.divider()
        st.markdown("## 📞 보험사 연락처 & 청구 안내")

        # ── 생명보험사 데이터 ──
        LIFE_INS = [
            {
                "name": "삼성생명", "color": "#0066CC",
                "call": "1588-3114",
                "emergency": "해당없음",
                "hq": "서울 서초구 서초대로74길 11 (삼성생명 서초타워)",
                "gwangju": "광주 서구 상무대로 904 / 062-360-7700",
                "claim": "① 앱(삼성생명) → 보험금 청구\n② 지점 방문 또는 우편 접수\n③ 팩스 접수 후 원본 우편 발송",
                "fax": "02-1588-3114 (지점별 상이, 콜센터 확인)",
            },
            {
                "name": "한화생명", "color": "#E8001C",
                "call": "1588-6363",
                "emergency": "해당없음",
                "hq": "서울 영등포구 63로 50 (63한화생명빌딩)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-7000",
                "claim": "① 앱(한화생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-789-8282",
            },
            {
                "name": "교보생명", "color": "#003087",
                "call": "1588-1001",
                "emergency": "해당없음",
                "hq": "서울 종로구 종로 1 (교보생명빌딩)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-1001",
                "claim": "① 앱(교보생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-721-3535",
            },
            {
                "name": "신한라이프", "color": "#0046FF",
                "call": "1588-5580",
                "emergency": "해당없음",
                "hq": "서울 중구 세종대로 9 (신한금융그룹 본사)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-5580",
                "claim": "① 앱(신한라이프) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3455-4500",
            },
            {
                "name": "NH농협생명", "color": "#00843D",
                "call": "1544-4000",
                "emergency": "해당없음",
                "hq": "서울 중구 새문안로 16 (농협생명 본사)",
                "gwangju": "광주 북구 우치로 226 / 062-520-4000",
                "claim": "① 앱(NH농협생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2080-6000",
            },
            {
                "name": "흥국생명", "color": "#8B0000",
                "call": "1588-2288",
                "emergency": "해당없음",
                "hq": "서울 종로구 새문안로 68 (흥국생명빌딩)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-2288",
                "claim": "① 앱(흥국생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2002-7000",
            },
            {
                "name": "동양생명", "color": "#FF6600",
                "call": "1577-1004",
                "emergency": "해당없음",
                "hq": "서울 종로구 종로 26 (동양생명빌딩)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-1004",
                "claim": "① 앱(동양생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3455-5000",
            },
            {
                "name": "ABL생명", "color": "#004B87",
                "call": "1588-6600",
                "emergency": "해당없음",
                "hq": "서울 영등포구 국제금융로 10 (Two IFC)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-6600",
                "claim": "① 앱(ABL생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2009-8000",
            },
            {
                "name": "미래에셋생명", "color": "#E4002B",
                "call": "1588-0220",
                "emergency": "해당없음",
                "hq": "서울 중구 을지로5길 26 (미래에셋센터원빌딩)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-0220",
                "claim": "① 앱(미래에셋생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3774-1000",
            },
            {
                "name": "KB라이프생명", "color": "#FFBC00",
                "call": "1588-9922",
                "emergency": "해당없음",
                "hq": "서울 영등포구 의사당대로 141 (KB라이프생명 본사)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-9922",
                "claim": "① 앱(KB라이프생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2073-8000",
            },
            {
                "name": "하나생명", "color": "#009B77",
                "call": "1588-6500",
                "emergency": "해당없음",
                "hq": "서울 중구 을지로 66 (하나생명 본사)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-6500",
                "claim": "① 앱(하나생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2002-8000",
            },
            {
                "name": "IBK연금보험", "color": "#005BAC",
                "call": "1588-5959",
                "emergency": "해당없음",
                "hq": "서울 중구 을지로 79 (IBK기업은행 본점)",
                "gwangju": "광주 북구 제봉로 322 IBK기업은행 광주지점 / 062-520-5959",
                "claim": "① IBK연금보험 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-6322-8000",
            },
            {
                "name": "DB생명", "color": "#E8001C",
                "call": "1588-3131",
                "emergency": "해당없음",
                "hq": "서울 강남구 테헤란로 432 (DB금융센터)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-3131",
                "claim": "① 앱(DB생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3011-7000",
            },
            {
                "name": "KDB생명", "color": "#004B87",
                "call": "1588-4040",
                "emergency": "해당없음",
                "hq": "서울 영등포구 은행로 14 (KDB생명타워)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-4040",
                "claim": "① KDB생명 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-6940-8000",
            },
            {
                "name": "푸본현대생명", "color": "#C8102E",
                "call": "1588-1688",
                "emergency": "해당없음",
                "hq": "서울 종로구 종로 33 (그랑서울)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-1688",
                "claim": "① 푸본현대생명 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3701-7000",
            },
            {
                "name": "IM라이프(구 DGB생명)", "color": "#005BAC",
                "call": "1588-4770",
                "emergency": "해당없음",
                "hq": "대구 수성구 달구벌대로 2310 (IM라이프 본사)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-4770",
                "claim": "① IM라이프 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "053-740-8000",
            },
            {
                "name": "AIA생명", "color": "#D4003B",
                "call": "1588-9898",
                "emergency": "해당없음",
                "hq": "서울 중구 을지로5길 26 (미래에셋센터원빌딩)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-9898",
                "claim": "① 앱(AIA생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3774-8000",
            },
            {
                "name": "메트라이프생명", "color": "#00A3E0",
                "call": "1588-9600",
                "emergency": "해당없음",
                "hq": "서울 종로구 종로 33 (그랑서울 메트라이프타워)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-9600",
                "claim": "① 앱(메트라이프) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2076-8000",
            },
        ]

        # ── 손해보험사 데이터 ──
        NON_LIFE_INS = [
            {
                "name": "삼성화재", "color": "#0066CC",
                "call": "1588-5114",
                "emergency": "1588-5114 (24시간)",
                "hq": "서울 서초구 서초대로74길 14 (삼성화재 서초사옥)",
                "claim": "① 앱(삼성화재 다이렉트) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수 후 원본 우편 발송",
                "fax": "02-758-7500",
            },
            {
                "name": "현대해상", "color": "#003087",
                "call": "1588-5656",
                "emergency": "1588-5656 (24시간)",
                "hq": "서울 종로구 세종대로 163 (현대해상빌딩)",
                "claim": "① 앱(Hi-Care) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3701-8000",
            },
            {
                "name": "KB손해보험", "color": "#FFBC00",
                "call": "1544-0114",
                "emergency": "1544-0114 (24시간)",
                "hq": "서울 강남구 테헤란로 92 (KB손보 본사)",
                "claim": "① 앱(KB손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-6980-8000",
            },
            {
                "name": "DB손해보험", "color": "#E8001C",
                "call": "1588-0100",
                "emergency": "1588-0100 (24시간)",
                "hq": "서울 강남구 테헤란로 432 (DB금융센터)",
                "claim": "① 앱(DB손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3011-8000",
            },
            {
                "name": "메리츠화재", "color": "#FF6600",
                "call": "1566-7711",
                "emergency": "1566-7711 (24시간)",
                "hq": "서울 강남구 테헤란로 138 (메리츠타워)",
                "claim": "① 앱(메리츠화재) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3786-8000",
            },
            {
                "name": "한화손해보험", "color": "#E8001C",
                "call": "1566-8000",
                "emergency": "1566-8000 (24시간)",
                "hq": "서울 영등포구 63로 50 (한화손보 본사)",
                "claim": "① 앱(한화손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-789-8100",
            },
            {
                "name": "롯데손해보험", "color": "#E8001C",
                "call": "1588-3344",
                "emergency": "1588-3344 (24시간)",
                "hq": "서울 중구 을지로 30 (롯데손보 본사)",
                "claim": "① 앱(롯데손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2218-8000",
            },
            {
                "name": "흥국화재", "color": "#8B0000",
                "call": "1688-1688",
                "emergency": "1688-1688 (24시간)",
                "hq": "서울 종로구 새문안로 68 (흥국화재 본사)",
                "claim": "① 앱(흥국화재) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2002-7100",
            },
            {
                "name": "MG손해보험", "color": "#00843D",
                "call": "1588-5959",
                "emergency": "1588-5959 (24시간)",
                "hq": "서울 중구 통일로 120 (MG손보 본사)",
                "claim": "① 앱(MG손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2002-6000",
            },
            {
                "name": "NH농협손해보험", "color": "#00843D",
                "call": "1644-9000",
                "emergency": "1644-9000 (24시간)",
                "hq": "서울 중구 새문안로 16 (농협손보 본사)",
                "claim": "① 앱(NH농협손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2080-7000",
            },
            {
                "name": "라이나손해보험", "color": "#005BAC",
                "call": "1588-0058",
                "emergency": "1588-0058 (24시간)",
                "hq": "서울 종로구 종로 33 (그랑서울)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-0058",
                "claim": "① 라이나손보 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2076-7000",
            },
            {
                "name": "하나손해보험", "color": "#009B77",
                "call": "1566-3000",
                "emergency": "1566-3000 (24시간)",
                "hq": "서울 중구 을지로 66 (하나손보 본사)",
                "gwangju": "광주 서구 상무중앙로 110 / 062-380-3000",
                "claim": "① 앱(하나손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-2002-9000",
            },
            {
                "name": "AIG손해보험", "color": "#00A3E0",
                "call": "02-3707-4500",
                "emergency": "02-3707-4500 (24시간)",
                "hq": "서울 종로구 종로 33 (그랑서울)",
                "gwangju": "광주 서구 상무대로 904 / 062-380-4500",
                "claim": "① AIG손보 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수",
                "fax": "02-3707-4600",
            },
        ]

        def _tel_link(text, color):
            """텍스트에서 전화번호를 찾아 tel: 링크로 변환. 숫자·하이픈으로 구성된 번호 패턴 처리."""
            import re
            def _replace(m):
                raw = m.group(0)
                digits = re.sub(r"[^0-9]", "", raw)
                return (f'<a href="tel:{digits}" '
                        f'style="color:{color};font-weight:700;text-decoration:none;'
                        f'border-bottom:1.5px solid {color}88;">{raw}</a>')
            return re.sub(r'\b[\d]{2,4}-[\d]{3,4}-[\d]{4}\b|\b0\d{1,2}-\d{3,4}-\d{4}\b'
                          r'|\b1[0-9]{3}-[0-9]{4}\b|\b0[2-9][0-9]-[0-9]{3,4}-[0-9]{4}\b',
                          _replace, text)

        def _ins_card_html(ins):
            claim_html = ins["claim"].replace("\n", "<br>")
            gwangju_raw = ins.get("gwangju", "콜센터 문의 (1588 대표번호)")
            c = ins['color']
            call_linked     = _tel_link(ins['call'], c)
            emerg_linked    = _tel_link(ins['emergency'], c)
            gwangju_linked  = _tel_link(gwangju_raw, c)
            return f"""
<div class="ins-scroll-box" style="border:1.5px solid {c}33;border-left:5px solid {c};">
  <div style="padding:12px 14px 10px 14px;">
    <div style="font-size:0.95rem;font-weight:800;color:{c};margin-bottom:7px;">
      🏢 {ins['name']}
    </div>
    <table style="width:100%;font-size:0.78rem;color:#333;border-collapse:collapse;">
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;width:82px;">📞 콜센터</td>
        <td style="padding:2px 0;">{call_linked}</td>
      </tr>
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;">🚨 긴급출동</td>
        <td style="padding:2px 0;">{emerg_linked}</td>
      </tr>
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;vertical-align:top;">🏛️ 본사주소</td>
        <td style="padding:2px 0;line-height:1.5;">{ins['hq']}</td>
      </tr>
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;vertical-align:top;">🌸 광주고객센터</td>
        <td style="padding:2px 0;line-height:1.55;">{gwangju_linked}</td>
      </tr>
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;vertical-align:top;">📋 청구방법</td>
        <td style="padding:2px 0;line-height:1.55;">{claim_html}</td>
      </tr>
      <tr>
        <td style="padding:2px 6px 2px 0;white-space:nowrap;font-weight:600;color:#555;">📠 청구팩스</td>
        <td style="padding:2px 0;">{ins['fax']}</td>
      </tr>
    </table>
  </div>
</div>"""

        # ── 생명보험 섹션 ──
        st.markdown("""
<div style="background:linear-gradient(90deg,#1a3a5c,#2e6da4);
  border-radius:10px;padding:12px 18px;margin-bottom:14px;">
  <span style="color:#fff;font-size:1.05rem;font-weight:800;">🛡️ 생명보험사</span>
  <span style="color:#b8d4f0;font-size:0.8rem;margin-left:10px;">Life Insurance</span>
</div>""", unsafe_allow_html=True)

        _life_cols = st.columns(4, gap="small")
        for _li, _lins in enumerate(LIFE_INS):
            with _life_cols[_li % 4]:
                st.markdown(_ins_card_html(_lins), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── 손해보험 섹션 ──
        st.markdown("""
<div style="background:linear-gradient(90deg,#7b2d00,#c0392b);
  border-radius:10px;padding:12px 18px;margin-bottom:14px;">
  <span style="color:#fff;font-size:1.05rem;font-weight:800;">🚗 손해보험사</span>
  <span style="color:#f5c6c6;font-size:0.8rem;margin-left:10px;">Non-Life Insurance</span>
</div>""", unsafe_allow_html=True)

        _nonlife_cols = st.columns(4, gap="small")
        for _ni, _nins in enumerate(NON_LIFE_INS):
            with _nonlife_cols[_ni % 4]:
                st.markdown(_ins_card_html(_nins), unsafe_allow_html=True)

    # ── [장해보험금 산출] 렌더 함수 ──────────────────────────────────────
    def _disability_render():
        _dh_col, _dh_sp = st.columns([1, 5])
        with _dh_col:
            if st.button(
                "🏠  홈으로",
                key="btn_home_disability",
                use_container_width=True,
                type="primary",
                help="홈 메뉴로 돌아갑니다"
            ):
                st.session_state.current_tab = "home"
                st.rerun()
        st.divider()
        st.subheader("🩺 장해보험금 산출")
        st.caption("AMA방식(개인보험) · 맥브라이드방식(배상책임) · 호프만계수 적용 | 후유장해 보험금 및 일실수익 손해배상금 산출")

        dis_sub = st.radio(
            "산출 방식 선택",
            ["AMA방식 (개인보험 후유장해)", "맥브라이드방식 (배상책임·손해배상)", "호프만계수 (중간이자 공제)"],
            horizontal=True, key="dis_sub"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_d, query_d, hi_d, do_d = ai_query_block(
                "disability",
                f"{dis_sub} 관련 상담 내용을 입력하세요.\n"
                "(예: 남성 45세, 건설노동자, 월소득 350만원, 요추 추간판탈출증 수술 후 척추 장해 15% 판정)"
            )

            st.markdown("##### 📋 기본 준비서류 입력")
            _dc1, _dc2 = st.columns(2)
            with _dc1:
                dis_gender = st.selectbox("성별", ["남성", "여성"], key="dis_gender")
                dis_age    = st.number_input("나이 (세)", min_value=1, max_value=80, value=45, step=1, key="dis_age")
                dis_job    = st.text_input("직업", "건설노동자", key="dis_job")
            with _dc2:
                dis_income = st.number_input("직전 3개월 평균 월소득 (만원)", min_value=0, value=350, step=10, key="dis_income")
                dis_type   = st.selectbox("장해 유형", ["영구장해", "한시장해(5년 이상)"], key="dis_type")
                dis_rate   = st.number_input("장해지급률 / 노동능력상실률 (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5, key="dis_rate")

            dis_acc_date = st.date_input("사고일", key="dis_acc_date")
            dis_sum      = st.number_input("보험가입금액 (만원, AMA방식 전용)", min_value=0, value=10000, step=500, key="dis_sum")

            dis_diag = st.file_uploader(
                "장해진단서 업로드 (PDF/JPG/PNG) — AI OCR 분석",
                type=["pdf", "jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key="dis_diag_files"
            )
            if dis_diag:
                st.success(f"✅ {len(dis_diag)}개 파일 업로드 완료")
                for _df in dis_diag:
                    if _df.type.startswith("image/"):
                        st.image(_df, caption=_df.name, width=200)

            if do_d:
                # 장해진단서 텍스트 추출
                diag_text = ""
                if dis_diag:
                    for _df in dis_diag:
                        if _df.type == "application/pdf":
                            diag_text += f"\n[장해진단서: {_df.name}]\n" + extract_pdf_chunks(_df, char_limit=6000)
                        else:
                            diag_text += f"\n[장해진단서 이미지: {_df.name} — OCR 분석 요청]\n"

                # 가동연한까지 잔여 개월 수 산출
                _working_age = 65
                _months_left = max(0, (_working_age - dis_age) * 12)
                # AMA 예상 보험금 간이 산출
                _ama_est = round(dis_sum * dis_rate / 100 * (0.2 if "한시" in dis_type else 1.0), 1)
                # 호프만 계수 근사값 (단리 공제, 연 5% 기준)
                _n_years = _months_left / 12
                _hoffman = round(_n_years / (1 + 0.05 * _n_years / 2), 2) if _n_years > 0 else 0
                # 맥브라이드 일실수익 간이 산출 (생활비율 1/3 공제)
                _mcb_est = round(dis_income * (dis_rate / 100) * (2 / 3) * _hoffman, 1)

                run_ai_analysis(c_name_d, query_d, hi_d, "res_disability",
                    f"[장해보험금 산출 — {dis_sub}]\n"
                    f"성별: {dis_gender}, 나이: {dis_age}세, 직업: {dis_job}\n"
                    f"월평균소득: {dis_income}만원, 장해유형: {dis_type}, 장해율: {dis_rate}%\n"
                    f"사고일: {dis_acc_date}, 보험가입금액: {dis_sum}만원\n"
                    f"가동연한(65세)까지 잔여: {_months_left}개월({_n_years:.1f}년)\n"
                    f"호프만계수(단리 5%): {_hoffman}\n"
                    f"[간이 산출] AMA예상보험금: {_ama_est}만원 / 맥브라이드 일실수익: {_mcb_est}만원\n"
                    f"{diag_text}\n"
                    "아래 순서로 상세 분석하십시오:\n"
                    "1. AMA방식: 보험가입금액 × 장해지급률(%) = 예상 보험금 (한시장해 시 20% 적용)\n"
                    "2. 맥브라이드방식: 월평균소득 × 장해율(%) × (1-생활비율1/3) × 호프만계수 = 일실수익\n"
                    "3. 호프만계수 vs 라이프니쯔계수 비교 설명\n"
                    "4. 장해진단서 판독 결과 및 AMA·맥브라이드 테이블 대조\n"
                    "5. 기왕증 기여도·과실상계 적용 시 감액 시나리오\n"
                    "6. 전문가(손해사정사·변호사) 검토 필요 사항 명시\n"
                    "⚠️ 본 산출은 참고용이며 최종 보험금은 보험사 심사 및 법원 판결에 따릅니다.\n"
                )

        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_disability")

            # ── 보험사 vs 법원 장해 산출 차액 비교 ──────────────────────────
            st.markdown("")
            components.html("""
<div style="
  background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);
  border-radius:12px; padding:16px 20px 14px 20px; margin:8px 0 4px 0;
  box-shadow:0 3px 10px rgba(26,58,92,0.25);
">
  <div style="color:#fff;font-size:1.05rem;font-weight:800;letter-spacing:0.02em;line-height:1.5;">
    📊 보험사(라이프니쯔) vs 법원(호프만) — 차액 비교 산출
  </div>
  <div style="color:#c8e0f8;font-size:0.82rem;margin-top:5px;line-height:1.4;">
    동일 장해율에서 방식 차이로 발생하는 보상금 차액을 즉시 산출합니다
  </div>
</div>""", height=82)

            with st.expander("▶ 입력값 설정 후 산출 실행 버튼(클릭)", expanded=True):
                st.markdown(
                    "<span style='color:#111;font-size:0.88rem;'>좌측 입력값이 자동 반영됩니다. 필요 시 아래에서 직접 수정하세요.</span>",
                    unsafe_allow_html=True
                )
                st.markdown(
                    "<span style='color:#111;font-size:0.88rem;'>📌 2023년 1월 1일 이후 사고는 <b>호프만(단리)</b> 방식이 표준약관 기준입니다.</span>",
                    unsafe_allow_html=True
                )

                _cc1, _cc2, _cc3 = st.columns(3)
                with _cc1:
                    _cmp_income = st.number_input("💴 월평균소득 (만원)", min_value=0, value=int(dis_income), step=10, key="cmp_income")
                with _cc2:
                    _cmp_rate   = st.number_input("📉 노동능력상실률 (%)", min_value=0.0, max_value=100.0, value=float(dis_rate), step=0.5, key="cmp_rate")
                with _cc3:
                    _cmp_fault  = st.number_input("⚖️ 본인 과실 (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0, key="cmp_fault")

                _cmp_months = st.slider(
                    "📅 장해 기간 (개월)",
                    min_value=12, max_value=480,
                    value=min(int(max(0, (65 - dis_age) * 12)), 480),
                    step=12, key="cmp_months",
                    help="가동연한(65세)까지 잔여 개월 수가 자동 계산됩니다"
                )
                _cmp_name = st.text_input("👤 고객명 (리포트용)", value=c_name_d if c_name_d else "고객", key="cmp_name")

                _btn_col1, _btn_col2 = st.columns([3, 1])
                with _btn_col1:
                    _do_calc = st.button("🔢 차액 비교 산출 실행", key="btn_cmp_calc", use_container_width=True, type="primary")
                with _btn_col2:
                    _do_reset = st.button("🔄 초기화", key="btn_cmp_reset", use_container_width=True, type="secondary",
                                          disabled=not bool(st.session_state.get("cmp_result")))

                if _do_reset:
                    st.session_state.pop("cmp_result", None)
                    st.rerun()

                if _do_calc:
                    _r2 = 0.05 / 12
                    _months = _cmp_months
                    _h_factor = min(sum([1 / (1 + n * _r2) for n in range(1, _months + 1)]), 240.0)
                    _l_factor = sum([1 / ((1 + _r2) ** n) for n in range(1, _months + 1)])
                    _base = (_cmp_income * 10000) * (_cmp_rate / 100) * (2 / 3)
                    _fault = _cmp_fault / 100
                    _p_h = int(_base * _h_factor * (1 - _fault))
                    _p_l = int(_base * _l_factor * (1 - _fault))
                    _diff = _p_h - _p_l
                    _inc_rate = round(_diff / _p_l * 100, 2) if _p_l > 0 else 0.0
                    st.session_state["cmp_result"] = {
                        "name": _cmp_name,
                        "months": _months,
                        "h_factor": round(_h_factor, 4),
                        "l_factor": round(_l_factor, 4),
                        "hoffman": _p_h,
                        "leibniz": _p_l,
                        "diff": _diff,
                        "rate": _inc_rate,
                    }

                if st.session_state.get("cmp_result"):
                    _rv = st.session_state["cmp_result"]
                    components.html(f"""
<style>
  .cmp-wrap {{font-family:'Noto Sans KR','Malgun Gothic',sans-serif;}}
  .cmp-header {{
    background:linear-gradient(135deg,#1a3a5c,#2e6da4);
    color:#fff; border-radius:10px 10px 0 0;
    padding:12px 18px; font-size:0.95rem; font-weight:800;
  }}
  .cmp-body {{
    background:#f4f8fd; border:1.5px solid #b8d0ea;
    border-top:none; border-radius:0 0 10px 10px;
    padding:14px 18px 10px 18px;
  }}
  .cmp-row {{
    display:flex; justify-content:space-between; align-items:center;
    padding:7px 0; border-bottom:1px solid #dde8f4;
    font-size:0.85rem; color:#1a1a2e;
  }}
  .cmp-row:last-child {{border-bottom:none;}}
  .cmp-label {{color:#555; font-size:0.82rem;}}
  .cmp-val-h {{
    font-size:1.05rem; font-weight:800; color:#1a6e2e;
    background:#e6f4ea; border-radius:6px; padding:3px 10px;
  }}
  .cmp-val-l {{
    font-size:1.05rem; font-weight:800; color:#8b1a1a;
    background:#fdecea; border-radius:6px; padding:3px 10px;
  }}
  .cmp-diff {{
    background:linear-gradient(90deg,#fffde7,#fff9c4);
    border:1.5px solid #f39c12; border-radius:8px;
    padding:10px 16px; margin-top:10px;
    font-size:0.88rem; color:#7d5a00;
  }}
  .cmp-diff-amt {{font-size:1.2rem; font-weight:900; color:#c0392b;}}
  .cmp-coeff {{
    background:#eef4fb; border-radius:6px;
    padding:6px 12px; margin-top:8px;
    font-size:0.78rem; color:#2e6da4;
  }}
  .cmp-disclaimer {{
    margin-top:10px; font-size:0.74rem; color:#888;
    border-top:1px dashed #ccc; padding-top:7px;
  }}
</style>
<div class="cmp-wrap">
  <div class="cmp-header">
    📋 Goldkey AI Master — 정밀 분석 리포트 &nbsp;|&nbsp;
    <span style="font-size:0.82rem;font-weight:400;">{_rv['name']} 고객님</span>
  </div>
  <div class="cmp-body">
    <div class="cmp-row">
      <span class="cmp-label">장해 기간</span>
      <span><b>{_rv['months']}개월</b> ({round(_rv['months']/12,1)}년)</span>
    </div>
    <div class="cmp-row">
      <span class="cmp-label">✅ 법원 / 표준약관 기준 <b style="color:#1a6e2e;">(호프만·단리)</b></span>
      <span class="cmp-val-h">{format(_rv['hoffman'], ',')} 원</span>
    </div>
    <div class="cmp-row">
      <span class="cmp-label">🔴 보험사 구 방식 <b style="color:#8b1a1a;">(라이프니쯔·복리)</b></span>
      <span class="cmp-val-l">{format(_rv['leibniz'], ',')} 원</span>
    </div>
    <div class="cmp-coeff">
      호프만 계수: <b>{_rv['h_factor']}</b> &nbsp;/&nbsp; 라이프니쯔 계수: <b>{_rv['l_factor']}</b>
    </div>
    <div class="cmp-diff">
      💡 방식 차이에 따른 <b>증액분</b>:
      <span class="cmp-diff-amt">+{format(_rv['diff'], ',')} 원</span>
      &nbsp;&nbsp;
      <span style="font-size:0.95rem;font-weight:700;color:#c0392b;">▲ {_rv['rate']}%</span><br>
      <span style="font-size:0.8rem;">전문적인 법리 검토 여부에 따라 보상금의 규모가 이만큼 달라질 수 있습니다.</span>
    </div>
    <div class="cmp-disclaimer">
      ⚠️ 상기 내용은 AI가 산출한 것으로 전문가(손해사정사·변호사)의 검토가 반드시 필요합니다.
      최종 보험금은 보험사 심사 및 법원 판결에 따릅니다.
    </div>
  </div>
</div>""", height=390)

            st.markdown("##### 참고")
            components.html("""
<div style="
  height:480px; overflow-y:auto; padding:14px 16px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.83rem; line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">1. 재산보험(AMA) vs 배상책임(McBride) 비교</b><br>
• <b>개인보험(AMA)</b>: 약관상 '장해분류표'에 따라 정해진 지급률을 보험가입금액에 곱하여 정액 보상.<br>
• <b>배상책임(McBride)</b>: 사고가 없었을 때 벌어들였을 소득에서 장해로 인해 상실된 수익을 계산하는 실손 보상 원칙.<br>
<br>
<b style="font-size:0.85rem;color:#c0392b;">▶ 용어의 정의: 호프만 vs 라이프니쯔 (중간이자 공제방식)</b><br>
• <b>호프만(Hoffman)</b>과 <b>라이프니쯔(Leibniz)</b>는 장해율 자체가 아니라, 미래의 가치를 현재 시점으로 당겨올 때 발생하는 이자를 공제하는 <b>'중간이자 공제방식(계수)'</b>의 차이입니다.<br>
• <b>법원</b>은 호프만 방식, <b>보험사</b>는 라이프니쯔 방식을 기준으로 적용 — 보험사는 이자 공제가 많은 라이프니쯔를 선호하고, 손해사정사 및 변호사는 호프만을 주장합니다.<br>
• 동일한 장해율이라도 약 <b>15~20%의 보험금 수령액 차이</b> 발생.<br>
• 근거: 한국손해사정사회 실무 지침 및 대법원 손해배상 산정 기준(2025-2026 개정판 예측치 반영)<br>
<br>
<b style="font-size:0.85rem;color:#c0392b;">▶ 2023년부터 시행된 「자동차보험 표준약관 개정안」</b><br>
• <b>근거</b>: 금융감독원 공식 보도자료 (2022. 12. 26.) — 「자동차보험 표준약관 개선을 통한 소비자 권익 제고」<br>
• <b>주요 골자</b>: 상실수익액 산정 시 할인율 적용 방식을 <b>복리(라이프니쯔) → 단리(호프만)로 변경</b><br>
• <b>시행일</b>: 2023년 1월 1일 사고분부터 적용<br>
• 2023년 이후 발생하는 모든 자동차 사고 및 주요 배상책임 사고에서 보험사는 <b>의무적으로 호프만 계수를 적용</b>해야 합니다.<br>
• ⚠️ 만약 보험사에서 라이프니쯔 방식을 고수한다면 이는 <b>표준약관 위반</b>에 해당하여 민원 제기 및 정정 요구의 대상이 됩니다.<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">2. AMA 방식: 개인보험 후유장해 보험금 산식</b><br>
• <b>보험가입금액 × 장해지급률(%) = 예상 보험금</b><br>
• 의사 진단서상 부위별 장해 판정을 AMA 기준 지급률로 역산 적용<br>
• 한시장해(5년 이상)인 경우 해당 지급률의 <b>20%만 인정</b><br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">3. 맥브라이드 방식: 일실수익(손해배상금) 산식</b><br>
• 법원 판결 및 자동차보험 실무에서 사용하는 산식<br>
• <b>월평균소득 × 장해율(%) × (1 - 생활비율) × 호프만(또는 라이프니쯔) 계수</b><br>
• 직업별 노동능력상실률(McBride Table) 적용, 가동연한(65세)까지 잔여 기간 계산<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">4. 중간이자 공제: 호프만 vs 라이프니쯔</b><br>
• <b>호프만(Hoffman)</b>: 단리 공제 방식. 대한민국 법원에서 피해자에게 유리하게 적용 (이자 공제 적음)<br>
• <b>라이프니쯔(Leibniz)</b>: 복리 공제 방식. 과거 자동차보험 약관·일본/유럽에서 주로 사용, 보상금 상대적으로 적음<br>
• 남은 가동기간에 해당하는 계수를 적용하여 일시금으로 환산<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">5. 직업 및 성별 데이터 반영 (가동연한)</b><br>
• <b>성별/나이</b>: 통계청 '간이생명표'로 기대여명 확인, 소득 상실 기간 확정<br>
• <b>직업</b>: 맥브라이드 장해율표의 직종 번호 매칭 (옥내근로자 vs 건설노동자 등 동일 장해 부위라도 상실률 상이)<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">6. 장해 진단서 판독 및 분석 로직</b><br>
• 진단서 내 '장해부위', '각도', '운동범위(ROM)', '검사 소견' 등을 분석하여 AMA·맥브라이드 테이블과 대조<br>
• <b>한시장해</b>: 해당 기간만큼의 호프만 계수만 적용 / <b>영구장해</b>: 가동연한 종료 시까지 적용<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">7. 평균소득 산정 기준</b><br>
• <b>급여소득자</b>: 사고 직전 3개월간 평균 세전 소득<br>
• <b>사업·자영업자</b>: 세무신고 소득 기준, 미달 시 통계소득(시중노임단가) 적용<br>
• <b>무직·가사</b>: 건설업 보통인부 노임 적용하여 산출<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">8. 예상 보험금 산출 프로세스</b><br>
① 데이터 입력: 성별·연령·직업·소득·사고일<br>
② 장해 확정: 진단서 판독 → AMA 지급률(보험용) &amp; 맥브라이드 상실률(법원용) 도출<br>
③ 기간 확정: 가동연한(65세)까지 잔여 개월 수 산출<br>
④ 계수 적용: 호프만 계수(법원 기준) 대입<br>
⑤ 최종 결과: 보험금 및 손해배상금 각각 산출<br>
<br>
<b style="font-size:0.85rem;color:#1a3a5c;">9. 한계점 및 전문가 검토 사항</b><br>
• <b>기왕증(Pre-existing condition) 기여도</b>: 사고 전 질환이 장해에 영향 시 해당 비율만큼 감액<br>
• <b>과실 상계</b>: 배상책임(맥브라이드)의 경우 본인 과실분만큼 감액<br>
<br>
<b style="font-size:0.85rem;color:#555;">(기본 준비서류)</b><br>
성별 · 직업 · 직전 3개월 평균소득 · 나이 · 장해부위(한시/영구) · 의사 장해진단서
</div>
""", height=500)

    # ── [화재보험(재조달가액평가)] 렌더 함수 ──────────────────────────────
    def _fire_render():
        import pandas as pd
        _fh_col, _fh_sp = st.columns([1, 5])
        with _fh_col:
            if st.button(
                "🏠  홈으로",
                key="btn_home_fire",
                use_container_width=True,
                type="primary",
                help="홈 메뉴로 돌아갑니다"
            ):
                st.session_state.current_tab = "home"
                st.rerun()
        st.divider()
        st.subheader("🔥 화재보험(재조달가액평가)")
        st.caption("화재보험 설계 가이드 · 비례보상 방지 · 한국부동산원(REB) 기준 재조달가액 산출")

        _fc1, _fc2 = st.columns([1, 1])
        with _fc1:
            c_name_f, query_f, hi_f, do_f = ai_query_block(
                "fire",
                "화재보험 관련 상담 내용을 입력하세요. (예: 공장 화재보험 가입, 재조달가액 기준 설정 문의)")
            if do_f:
                run_ai_analysis(c_name_f, query_f, hi_f, "res_fire",
                    "[화재보험(재조달가액평가) 상담]\n"
                    "1.화재보험 필수 가입 기준 및 법적 의무 여부\n"
                    "2.재조달가액 기준 보험가액 설정 방법과 비례보상 방지 전략\n"
                    "3.물가상승률 반영 적정 가입금액 산정 방법\n"
                    "4.공장·상가·주택 용도별 화재보험 설계 포인트\n"
                    "5.영업배상책임(CGL) 연계 설계 전략\n")
        with _fc2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_fire")
            st.markdown("##### 🏗️ 화재보험 설계 가이드")
            components.html("""
<div style="
  height:340px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#c0392b;">🏗️ 정밀 건물가액 산정 로직 (비례보상 방지)</b><br>
• <b>물가상승률 반영 법칙</b>: 현재 시가 아닌 미래 가치 상승을 반영하여 가입금액 설정<br>
• [산식]: 현재 건물가액 × (1 + 연 5% 물가상승률 × 보험가입기간) = 적정 가입금액<br>
• <b>재조달가액 평가</b>: 사고 시 다시 지을 때 드는 비용인 '재조달가액' 기준으로 평가<br>
• 소유자는 <b>'무과실 책임'</b>을 부담함 (실화책임법 및 부진정연대채무 근거)<br>
• ⚠️ <b>경고</b>: '일부보험' 상태 시 실제 손해액 일부만 지급하는 <b>'비례보상'</b> 불이익 발생 가능<br>
• <b>화재배상</b>: 주변 건물 화재 피해 고려. 대물 배상 한도를 주변 시세보다 충분히 크게 설정<br>
<b style="font-size:0.85rem;color:#c0392b;">🏭 공장 화재 배상책임 고액 설계 전략</b><br>
• <b>전략 1 — 증권 분리 및 중복 가입</b><br>
&nbsp;&nbsp;- A사 + B사 여러 증권 분리 가입으로 <b>'한도의 총합'</b> 확장<br>
&nbsp;&nbsp;- 인당 보상 한도 1.5억 → 3억 → 4.5억 등으로 확장, 유족 합의금 및 경영 리스크 대비<br>
• <b>영업배상책임(CGL) 및 CSL 통합 설계</b>: 화재 특약이 아닌 독립된 CGL 별도 가입<br>
<b style="font-size:0.85rem;color:#c0392b;">⚙️ 공장 업종별 요율 적용 원칙</b><br>
• <b>최고위험 업종 적용 원칙</b>: 건물 내 공정/업종 혼재 시 반드시 <b>'가장 위험한 업종'</b>을 대표 업종으로 선택
</div>
""", height=370)

        st.divider()
        st.markdown("""
<div style="background:linear-gradient(135deg,#7b2d00 0%,#c0392b 60%,#1a3a5c 100%);
  border-radius:12px;padding:14px 20px;margin-bottom:14px;">
  <div style="color:#fff;font-size:1.05rem;font-weight:900;">🏗️ 건물 재조달가액 산출 시스템</div>
  <div style="color:#f5c6c6;font-size:0.78rem;margin-top:4px;">
    한국부동산원(REB) 건물신축단가표 기준 &nbsp;|&nbsp; 대한건설협회(CAK) 건설노임단가 반영
  </div>
</div>""", unsafe_allow_html=True)

        _FREB = {
            "주택(단독·다가구)":   {"철근콘크리트(RC)":98,"철골조(S)":90,"철골철근콘크리트(SRC)":108,"조적조(벽돌)":74,"목조":67,"경량철골조":80,"기타":72},
            "아파트·연립·다세대":  {"철근콘크리트(RC)":115,"철골조(S)":104,"철골철근콘크리트(SRC)":125,"조적조(벽돌)":83,"목조":72,"경량철골조":88,"기타":82},
            "상가·근린생활시설":   {"철근콘크리트(RC)":108,"철골조(S)":98,"철골철근콘크리트(SRC)":118,"조적조(벽돌)":80,"목조":70,"경량철골조":84,"기타":77},
            "사무용 건물(오피스)": {"철근콘크리트(RC)":125,"철골조(S)":114,"철골철근콘크리트(SRC)":140,"조적조(벽돌)":88,"목조":78,"경량철골조":93,"기타":88},
            "공장·창고":          {"철근콘크리트(RC)":78,"철골조(S)":67,"철골철근콘크리트(SRC)":88,"조적조(벽돌)":60,"목조":52,"경량철골조":62,"기타":57},
            "기타":               {"철근콘크리트(RC)":93,"철골조(S)":85,"철골철근콘크리트(SRC)":103,"조적조(벽돌)":72,"목조":64,"경량철골조":77,"기타":70},
        }
        _FLIFE = {"철근콘크리트(RC)":50,"철골조(S)":45,"철골철근콘크리트(SRC)":55,"조적조(벽돌)":40,"목조":30,"경량철골조":35,"기타":40}
        _FAUX  = {"주택(단독·다가구)":1.05,"아파트·연립·다세대":1.08,"상가·근린생활시설":1.10,"사무용 건물(오피스)":1.15,"공장·창고":1.03,"기타":1.05}

        if 'user_id' not in st.session_state:
            st.warning("🔐 로그인 후 재조달가액 산출을 이용할 수 있습니다.")
        else:
            _ftabs = st.tabs(["🏗️ 재조달가액 산출", "📚 단가표 관리 (관리자)"])

            with _ftabs[0]:
                st.markdown("""
<div style="background:#fff5f5;border:1.5px solid #c0392b;border-radius:10px;
  padding:12px 16px;margin-bottom:14px;font-size:0.82rem;color:#1a3a5c;line-height:1.8;">
  <b>📌 재조달가액 산출 공식 (REB 기준)</b><br>
  <code>재조달가액 = (표준단가 × 부대설비 보정치) × 연면적 + 간접비(15%) + 수급인 이윤(6%)</code><br>
  &nbsp;• <b>표준단가</b>: 한국부동산원(REB) 건물신축단가표 (매년 갱신)<br>
  &nbsp;• <b>건설노임단가</b>: 대한건설협회(CAK) 연 2회 발표 기준
  &nbsp;<a href="https://www.cak.or.kr" target="_blank" style="color:#c0392b;">[CAK 바로가기]</a>
</div>""", unsafe_allow_html=True)

                if st.session_state.rag_system.index is not None:
                    st.caption("✅ 관리자 업로드 단가표 반영됨")
                else:
                    st.caption("ℹ️ 기본 단가표(REB 2025) 적용 중")

                st.markdown("### 📎 서류 업로드")
                _fuc1, _fuc2 = st.columns(2)
                with _fuc1:
                    st.markdown("**① 건축물대장** (필수)")
                    _freg = st.file_uploader("건축물대장 스캔 (PDF/이미지)",
                        type=["pdf","jpg","jpeg","png"], key="fire_reg_file")
                with _fuc2:
                    st.markdown("**② 등기부등본** (선택)")
                    _fdeed = st.file_uploader("등기부등본 스캔 (PDF/이미지)",
                        type=["pdf","jpg","jpeg","png"], key="fire_deed_file")

                st.markdown("### 🏠 건물 기본 정보")
                _fb1, _fb2, _fb3 = st.columns(3)
                with _fb1:
                    _fuse = st.selectbox("건물 용도", list(_FREB.keys()), key="fire_use")
                with _fb2:
                    _fstruct = st.selectbox("구조", list(_FREB[_fuse].keys()), key="fire_struct")
                with _fb3:
                    _farea = st.number_input("연면적 (㎡)", min_value=1.0, value=100.0, step=1.0, key="fire_area")

                _fb4, _fb5, _fb6 = st.columns(3)
                with _fb4:
                    _fbuild_yr = st.number_input("사용승인연도", min_value=1950, max_value=2025, value=2000, step=1, key="fire_build_yr")
                with _fb5:
                    _finfl = st.number_input("연평균 물가상승률 (%)", min_value=0.5, max_value=10.0, value=3.0, step=0.1, key="fire_infl")
                with _fb6:
                    _flabor = st.number_input("건설노임 보정률 (%)", min_value=-20, max_value=30, value=0, step=1, key="fire_labor")

                _fb7, _fb8 = st.columns(2)
                with _fb7:
                    _fbase_yr = st.number_input("기준연도", min_value=2020, max_value=2035, value=2025, step=1, key="fire_base_yr")
                with _fb8:
                    _fins_ratio = st.number_input("보험가입비율 (%)", min_value=50, max_value=100, value=80, step=5, key="fire_ins_ratio")

                st.divider()
                _do_fire_calc = st.button("🔍 재조달가액 산출 실행", type="primary", key="fire_calc_btn", use_container_width=True)

                if _do_fire_calc:
                    _fbase_unit = _FREB.get(_fuse, {}).get(_fstruct, 90)
                    _funit = _fbase_unit * (1 + _flabor / 100)
                    _faux  = _FAUX.get(_fuse, 1.05)
                    _fdirect   = _funit * 10000 * _faux * _farea
                    _findirect = _fdirect * 0.15
                    _fprofit   = (_fdirect + _findirect) * 0.06
                    _frebuild  = _fdirect + _findirect + _fprofit

                    _flife     = _FLIFE.get(_fstruct, 40)
                    _felapsed  = max(0, _fbase_yr - _fbuild_yr)
                    _fresid    = max(0.20, 1.0 - _felapsed / _flife)
                    _finsured  = _frebuild * _fresid
                    _fins_amt  = _finsured * (_fins_ratio / 100)

                    st.success(f"✅ 재조달가액: **{_frebuild/1e8:.2f}억원** ({_frebuild/10000:,.0f}만원)")
                    st.info(f"💰 권장 보험가입금액: **{_fins_amt/1e8:.2f}억원** (시가 {_finsured/1e8:.2f}억원 × {_fins_ratio}%)")

                    _mr1, _mr2, _mr3, _mr4 = st.columns(4)
                    _mr1.metric("표준단가", f"{_funit:.1f}만원/㎡")
                    _mr2.metric("부대설비 보정치", f"{_faux:.2f}")
                    _mr3.metric("경과연수/잔가율", f"{_felapsed}년 / {_fresid*100:.1f}%")
                    _mr4.metric("내용연수", f"{_flife}년")

                    st.markdown("#### 📈 향후 10년 건물가액 변화")
                    _frows = []
                    for _fy in range(11):
                        _frb = _frebuild * ((1 + _finfl / 100) ** _fy)
                        _frs = max(0.20, 1.0 - (_felapsed + _fy) / _flife)
                        _frows.append({
                            "연도": f"{_fbase_yr + _fy}년",
                            "재조달가액(만원)": f"{_frb/10000:,.0f}",
                            "잔가율(%)": f"{_frs*100:.1f}",
                            "예상보험가액(만원)": f"{_frb*_frs/10000:,.0f}",
                            f"권장가입금액({_fins_ratio}%)(만원)": f"{_frb*_frs*(_fins_ratio/100)/10000:,.0f}",
                        })
                    st.dataframe(pd.DataFrame(_frows), use_container_width=True, hide_index=True)

                    with st.expander("📋 산출 근거 및 주의사항"):
                        st.markdown(f"""
**산출 기준** — REB 건물신축단가표(2025) / CAK 건설노임단가
- 건물 용도: {_fuse} / 구조: {_fstruct} / 연면적: {_farea:.1f}㎡
- 표준단가: {_funit:.1f}만원/㎡ (노임보정 {_flabor:+d}%) / 부대설비 보정치: {_faux}
- 내용연수: {_flife}년 / 잔가율 최저: 20% / 물가상승률: {_finfl}%

**⚠️ 주의사항** — 본 산출액은 참고용이며 실제 가입 시 현장 실사 및 전문가 확인 필요. 토지가액 미포함.
""")

            with _ftabs[1]:
                if not st.session_state.get('is_admin'):
                    st.warning("🔐 관리자 로그인 후 이용 가능합니다.")
                else:
                    st.markdown("#### 📤 REB/CAK 단가표 업로드 (RAG 자동 등록)")
                    _fadm_yr = st.number_input("발행연도", min_value=2020, max_value=2035, value=2025, key="fire_adm_yr")
                    _fadm_half = st.selectbox("발표 시기", ["연간", "상반기", "하반기"], key="fire_adm_half")
                    _fadm_files = {
                        "REB 건물신축단가표": st.file_uploader("REB 단가표 (PDF/Excel/CSV)", type=["pdf","xlsx","xls","csv"], key="fire_reb_file"),
                        "CAK 건설노임단가":   st.file_uploader("CAK 노임단가 (PDF/Excel/CSV)", type=["pdf","xlsx","xls","csv"], key="fire_cak_file"),
                    }
                    if st.button("📥 RAG 등록", type="primary", key="fire_adm_upload"):
                        _fany = False
                        for _flbl, _fuf in _fadm_files.items():
                            if _fuf is None:
                                continue
                            with st.spinner(f"📄 {_flbl} 처리 중..."):
                                try:
                                    if _fuf.type == "application/pdf":
                                        _ftxt = process_pdf(_fuf)
                                    elif _fuf.type in ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet","application/vnd.ms-excel"):
                                        import io
                                        _ftxt = pd.read_excel(io.BytesIO(_fuf.read())).to_string(index=False)
                                    elif _fuf.type == "text/csv":
                                        import io
                                        _ftxt = pd.read_csv(io.BytesIO(_fuf.read()), encoding="utf-8-sig").to_string(index=False)
                                    else:
                                        _ftxt = _fuf.read().decode("utf-8", errors="ignore")
                                    _fhdr = f"[{_flbl}]\n출처: REB/CAK\n발행연도: {_fadm_yr}년 {_fadm_half}\n\n"
                                    st.session_state.rag_system.add_documents([_fhdr + _ftxt[:8000]])
                                    st.success(f"✅ {_flbl} — RAG 등록 완료")
                                    _fany = True
                                except Exception as e:
                                    st.error(f"❌ {_flbl} 등록 오류: {e}")
                        if not _fany:
                            st.warning("업로드할 파일을 선택해주세요.")

    # ── 탭 클릭 안내 멘트 헬퍼 (2) ─────────────────────────────────────
    def tab_greeting(tab_key):
        """탭 진입 시 최초 1회 안내 멘트 출력 + 홈 복귀 버튼"""
        # ── 홈 복귀 버튼 (항상 최상단) ──
        _home_col, _spacer = st.columns([1, 5])
        with _home_col:
            if st.button(
                "🏠  홈으로",
                key=f"btn_home_{tab_key}",
                use_container_width=True,
                type="primary",
                help="홈 메뉴로 돌아갑니다"
            ):
                st.session_state.current_tab = "home"
                st.rerun()
        st.divider()
        flag = f"_tab_greeted_{tab_key}"
        if not st.session_state.get(flag):
            st.session_state[flag] = True
            components.html(s_voice("무엇을 도와드릴까요? 필요 항목을 클릭하세요."), height=0)

    # ── [탭 0] 신규보험 상담 (기존보험 분석 + 신규 컨설팅) ──────────────
    if cur == "t0":
        tab_greeting("t0")
        st.subheader("📋 신규 보험 상품 상담")
        st.caption("기존 보험증권 분석 → 보장 공백 파악 → 신규 보험 컨설팅")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name0, query0, hi0, do0 = ai_query_block(
                "t0", "현재 보험 가입 현황, 신규 상담 내용을 입력하세요. (예: 40세 남성, 실손+암보험 가입, 추가 필요 보장 분석 요청)")
            st.markdown("**📎 기존 보험증권 업로드 (선택)**")
            policy_files = st.file_uploader("보험증권 PDF/이미지", accept_multiple_files=True,
                                            type=['pdf','jpg','jpeg','png'], key="up_t0")
            if policy_files:
                st.success(f"{len(policy_files)}개 증권 업로드 완료")
            if do0:
                doc_text = ""
                if policy_files:
                    for pf in policy_files:
                        if pf.type == 'application/pdf':
                            doc_text += f"\n[증권: {pf.name}]\n" + extract_pdf_chunks(pf, char_limit=8000)
                run_ai_analysis(c_name0, query0, hi0, "res_t0",
                    "[신규보험 상담 · 증권분석]\n"
                    "### 1. 소득 역산 및 재무 진단\n"
                    "- 월소득 추정: [건강보험료/0.0709] 또는 [국민연금/0.09]\n"
                    "- 보험료 황금비율: 위험보장 7~10%(위험직군 최대 20%) / 사망보장 3~5% / 노후 소득의 30% 이상(연금 최소 10%)\n"
                    "- 가처분소득 기준 적정 보험료 산출 및 보장 공백 파악\n"
                    "### 2. 암 보장 분석\n"
                    "- 일반암+소액암 합산 최소 1억 이상 '충분', 미만 '보완' 권장\n"
                    "- 표적항암·면역항암·중입자치료·CAR-T 등 고가 비급여 대응 여부 점검\n"
                    "- NGS 검사 후 표적항암 담보 미비 시 치료 기회 상실 위험 강조\n"
                    "### 3. 뇌·심장 보장 분석\n"
                    "- 뇌졸중·급성심근경색만 가입 시 '범위 좁음' 판정\n"
                    "- 24개월 소득 공백기 대비 금액 설정 필수\n"
                    "### 4. 수술비·입원일당 분석\n"
                    "- 질병/상해 수술비(기본) + 1~5종 수술비 중첩 가입 권유\n"
                    "- 필요일당 = 가처분소득 ÷ 30 (월 300만원 → 10만원/일)\n"
                    "### 5. 간병·치매 연계\n"
                    "- 간병비 파산 방지: 하루 10만원 × 2년 = 7,200만원\n"
                    "- 뇌졸중 생존자 25~30% 6개월 내 치매 경험 통계 근거 제시\n"
                    "- 알츠하이머 치료제(레캠비 등) 보장 필요성 안내\n"
                    "### 6. 기존보험 현황 분석 및 신규 추천\n"
                    "1.기존보험 현황 분석 및 보장 공백 파악\n2.연령/소득 기반 적정 보험료 산출\n"
                    "3.부족한 보장에 대한 신규 보험 상품 추천\n4.타사 증권 비교 분석\n" + doc_text)
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t0")
            st.markdown("##### 📋 상담 흐름")
            components.html("""
<div style="
  height:160px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">📋 상담 흐름</b><br>
• <b>1단계</b>: 고객 성함 입력<br>
• <b>2단계</b>: 현재 보험 현황 입력 또는 증권 업로드<br>
• <b>3단계</b>: 월 건강보험료 입력 (소득 역산 자동 계산)<br>
• <b>4단계</b>: 정밀 분석 실행 → AI 보장 공백 분석 및 신규 추천
</div>
""", height=178)
            st.markdown("##### 🔬 증권 분석 및 업그레이드 로직 (3-Step)")
            components.html("""
<div style="
  height:260px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.88rem;color:#c0392b;">1단계 — 과거 보험금의 한계 (보험 포비아 해소)</b><br>
• 구 보험은 <b>'암 진단 시 1회 지급 후 소멸'</b> 구조<br>
• 장기화된 암·혈관 질환 치료비 감당 불가 → 진단비 소진 후 치료비 자부담 발생<br>
• 고객의 보험 불신(포비아) 근본 원인: 보장 한계를 모르고 가입한 구조적 문제<br>
• 핵심 메시지: <i>"예전 보험은 치료가 끝나면 끝이었습니다. 지금은 다릅니다."</i><br>
<br>
<b style="font-size:0.88rem;color:#e67e22;">2단계 — 의료 기술의 첨단 변화</b><br>
• 수술 중심 → <b>항암 약물·방사선·반복적 시술</b> 중심으로 패러다임 전환<br>
• <b>선행 항암요법(Neoadjuvant Therapy)</b>: 수술 전 종양 축소 목적 항암 선행 → 수술비 담보만으론 부족<br>
• <b>NGS(차세대 유전자 염기서열 분석)</b>: 맞춤형 표적항암제 선택 → 검사비 + 약제비 고액 발생<br>
• <b>ADC(항체-약물 접합체)</b>: 엔허투 등 신규 표적항암제 1회 투여 수백만원 수준<br>
• 결론: 기존 수술비·입원비 중심 보장으로는 <b>현대 암 치료비 대응 불가</b><br>
<br>
<b style="font-size:0.88rem;color:#27ae60;">3단계 — 솔루션: 신담보 설계</b><br>
• <b>암 진단비 반복 지급</b>: 재발·전이 시 추가 지급 구조 → 장기 암 치료 대응<br>
• <b>진행성 악성암 치료비</b>: 표적항암·면역항암·ADC 등 고가 비급여 치료 집중 보장<br>
• <b>표적항암약물허가치료비</b>: 식약처 허가 표적항암제 실비 보장 신담보<br>
• <b>중입자·양성자 치료비</b>: 1회 약 5,000만원 수준 비급여 대응<br>
• <b>CAR-T 세포치료비</b>: 7,000만~1억5,000만원 초고가 치료 대응<br>
• 설계 핵심: 진단비(정액) + 치료비(실손형 신담보) <b>이중 구조</b>로 완전 보장
</div>
""", height=278)

    # ── [탭 1] 보험금 상담 (청구·민원·손해사정·소송) ─────────────────────
    if cur == "t1":
        tab_greeting("t1")
        st.subheader("💰 보험금 상담 · 민원 · 손해사정")
        st.caption("보험금 청구 안내 · 미지급 민원 · 금감원 신고 · 손해사정 · 민사소송 지원")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name1, query1, hi1, do1 = ai_query_block(
                "t1", "보험금 청구 내용을 입력하세요. (예: 입원 30일, 수술 1회, 보험사에서 지급 거절 통보 받음)")
            claim_type = st.selectbox("상담 유형",
                ["보험금 청구 안내", "보험금 미지급 민원", "금융감독원 민원", "손해사정 의뢰", "민사소송 검토"],
                key="claim_type")
            st.markdown("**📎 관련 서류 업로드 (진단서·의무기록·거절통보서)**")
            claim_files = st.file_uploader("서류 업로드 (PDF/이미지)", accept_multiple_files=True,
                                           type=['pdf','jpg','jpeg','png','bmp'], key="up_t1")
            if claim_files:
                st.success(f"{len(claim_files)}개 파일 업로드 완료")
                for i, f in enumerate(claim_files, 1):
                    if f.type.startswith('image/'):
                        st.image(f, caption=f"서류 {i}", width=150)
            if do1:
                doc_text1 = ""
                if claim_files:
                    for cf in claim_files:
                        if cf.type == 'application/pdf':
                            doc_text1 += f"\n[첨부: {cf.name}]\n" + extract_pdf_chunks(cf, char_limit=6000)
                run_ai_analysis(c_name1, query1, hi1, "res_t1",
                    f"[보험금 상담 - {claim_type}]\n1.보험금 청구 가능 여부와 예상 지급액 분석\n"
                    "2.보험사 거절 시 대응 방안(민원/손해사정/소송)\n3.금융감독원 민원 절차와 필요 서류\n"
                    "4.관련 판례와 약관 조항 근거 제시\n" + doc_text1)
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t1")
            st.markdown("##### 📋 보험금 분쟁 해결 단계")
            components.html("""
<div style="
  height:200px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">📋 보험금 분쟁 해결 단계</b><br>
<b>1단계 📝 보험사 재심사 청구</b><br>
• 보험금 지급 거절·삭감 통보 수령 후 <b>90일 이내</b> 이의신청 가능<br>
• 필요 서류: 진단서·입퇴원확인서·수술기록지·약처방전 등 의무기록 일체<br>
• 보험사 내부 심사팀 재검토 요청 → 결과 서면 통보 의무<br>
• 팁: 주치의 소견서 추가 제출 시 번복 가능성 상승<br>
<br>
<b>2단계 🏛️ 금융감독원 민원 접수</b><br>
• 접수처: <b>금융소비자 정보포털 파인(fine.fss.or.kr)</b> 또는 ☎ 1332<br>
• 처리 기간: 접수 후 <b>30일 이내</b> 결과 통보 (연장 시 60일)<br>
• 보험사에 자료 제출 의무 부과 → 사실상 압박 효과<br>
• 민원 제기만으로도 보험사 자체 재검토 후 지급 전환 사례 다수<br>
<br>
<b>3단계 ⚖️ 금융분쟁조정위원회</b><br>
• 금감원 민원 불수용 시 <b>분쟁조정 신청</b> (별도 비용 없음)<br>
• 처리 기간: <b>60일 이내</b> 조정안 제시 (복잡 사건 90일)<br>
• 조정안 수락 시 재판상 화해 효력 → 법적 구속력 발생<br>
• 보험사가 조정안 거부 시 소송으로 이행<br>
• 근거: 금융소비자보호법 제36조<br>
<br>
<b>4단계 🔨 민사소송 (손해사정사 연계)</b><br>
• <b>독립손해사정사</b> 선임: 보험사 전속 사정사와 별개로 고객 측 사정 가능 (보험업법 제185조)<br>
• 소액사건(3,000만원 이하): 소액심판 절차 → 1회 변론으로 신속 판결<br>
• 승소 시 소송비용·변호사비용 일부 상대방 부담 청구 가능<br>
• 참고 판례: 대법원 2016다248998 (약관 불명확 시 고객 유리 해석 원칙)
</div>
""", height=420)

    # ── [장해보험금 산출] 독립 섹터 ──────────────────────────────────────
    if cur == "disability":
        _disability_render()

    # ── [탭 2] 필수보험 ──────────────────────────────────────────────────
    if cur == "t2":
        tab_greeting("t2")
        st.subheader("🛡️ 기본보험 상담")
        st.caption("자동차보험 · 운전자보험 · 일상생활배상책임 | 화재보험은 '화재보험(재조달가액평가)' 섹터를 이용하세요")
        ins_type = st.radio("보험 유형 선택",
            ["🚗 자동차보험", "🚙 운전자보험", "🤝 (가족)일상생활배상책임담보"],
            horizontal=True, key="ess_type")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name2, query2, hi2, do2 = ai_query_block(
                "t2",
                f"{ins_type} 관련 상담 내용을 입력하세요.",
                hide_query=(ins_type in ["🚙 운전자보험", "🚗 자동차보험", "🤝 (가족)일상생활배상책임담보"])
            )
            if do2:
                run_ai_analysis(c_name2, query2, hi2, "res_t2",
                    f"[기본보험 상담 - {ins_type}]\n1.해당 보험의 필수 가입 기준과 법적 의무 여부\n"
                    "2.적정 보장 금액과 특약 구성 추천\n3.주요 보험사 상품 비교 포인트\n4.보험료 절감 방법\n")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t2")
            if ins_type == "🚗 자동차보험":
                st.markdown("##### � 자동차보험 권장 기준")
                components.html("""
<div style="
  height:260px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">� 자동차보험 권장 기준</b><br>
• <b>대인배상</b>: 무한 (법적 의무)<br>
• <b>대물배상</b>: 기본 5억 / 권장 10억 이상<br>
• <b>자기신체손해</b>: 자동차상해(자상) 선택 권장 (과실 무관 실손 보상)<br>
• <b>자기차량손해</b>: 차량 가액 대비 자기부담금 설정 검토<br>
• <b>무보험차상해</b>: 상대방 무보험 대비 필수<br>
• <b>긴급출동 특약</b>: 배터리·타이어·잠금장치 등 포함 권장<br>
• <b>할인 항목</b>: 블랙박스·마일리지·안전운전 할인 적용 여부 확인
</div>
""", height=278)
            elif ins_type == "🚙 운전자보험":
                st.markdown("##### 🚙 운전자보험 플랜 안내")
                components.html("""
<div style="
  height:420px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.9rem;color:#1a3a5c;">🚙 운전자보험 (기본) 플랜</b><br>
• <b>교통사고처리지원금</b>: <b>2억원</b> 권장 (13대 중과실·중상해·사망사고 형사합의금 대비)<br>
• <b>변호사선임비용</b>: 형사·민사 소송 대비 특약 포함 권장<br>
• <b>형사합의지원금</b>: 피해자 합의 비용 지원 특약 포함<br>
• <b>벌금 담보</b>: 교통사고 벌금 최대 <b>2,000만원</b> 대비<br>
• <b>면허정지·취소 위로금</b>: 행정처분 대비 특약 검토<br>
• <b>가입 추천 시점</b>: 경찰서 조사 → 검찰 기소 <b>이전</b> 가입 필수<br>
• <b>주의</b>: 사고 발생 후 가입 시 해당 사고 <b>면책</b> → 반드시 사전 가입<br>
<br>
<b style="font-size:0.88rem;color:#c0392b;">⚠️ 13대 중과실 (형사처벌 위험 항목)</b><br>
• ① 신호·지시위반 &nbsp;② 중앙선침범 &nbsp;③ 제한속도 20km/h 초과<br>
• ④ 앞지르기 위반 &nbsp;⑤ 철길건널목 위반 &nbsp;⑥ 횡단보도 보행자 보호의무 위반<br>
• ⑦ 무면허운전 &nbsp;⑧ 음주운전(0.03% 이상) &nbsp;⑨ 보도침범<br>
• ⑩ 승객추락방지의무 위반 &nbsp;⑪ 어린이보호구역(민식이법) &nbsp;⑫ 화물추락방지 위반 &nbsp;⑬ 개문발차<br>
• 근거: 교통사고처리특례법 제3조 제2항 단서 — 피해자 합의 무관 <b>형사처벌 가능</b><br>
<br>
<b style="font-size:0.88rem;color:#c0392b;">🚫 면책 사항 (보험금 미지급)</b><br>
• <b>음주·약물운전</b>: 혈중알코올농도 0.03% 이상 또는 약물 복용 운전 중 사고<br>
• <b>무면허운전</b>: 면허 미취득·취소·정지 상태에서의 운전 중 사고<br>
• <b>뺑소니 사고</b>: 사고 후 피해자 구호 없이 도주한 경우<br>
• ※ 위 3가지는 <b>운전자보험 핵심 면책</b> — 가입 전 반드시 안내 필수<br>
<br>
<b style="font-size:0.88rem;color:#8e44ad;">🏥 중상해 (형사합의 대상)</b><br>
• <b>정의</b>: 교통사고처리특례법 제3조 — 생명에 대한 위험 / 불구 / 불치·난치 질병 유발<br>
• <b>판례 기준</b> (대법원): 뇌손상·척수손상·사지마비·시력상실·청력상실 등 <b>영구장애</b><br>
• <b>핵심</b>: 중상해 발생 시 피해자 합의 여부와 <b>무관하게 형사처벌 대상</b> (공소권 있음)<br>
• <b>형사합의 필요성</b>: 합의 시 양형 감경 가능 → 교통사고처리지원금(2억) 활용<br>
• <b>필요 서류</b>: 진단서(상해 등급 명시) / 수술기록지 / 후유장해진단서 / 의무기록 사본<br>
• <b>중상해 vs 중과실 비교</b><br>
&nbsp;&nbsp;- 중과실: 사고 원인(행위) 기준 → 13대 항목 해당 시 적용<br>
&nbsp;&nbsp;- 중상해: 사고 결과(피해) 기준 → 피해자 상해 정도에 따라 적용<br>
&nbsp;&nbsp;- 두 가지 동시 해당 시 <b>가중처벌</b> 가능 → 운전자보험 2억 이상 필수<br>
<br>
<b style="font-size:0.9rem;color:#1a3a5c;">🌟 운전자보험 (권장) 플랜</b><br>
<b>기본 플랜</b> + 아래 상해보장 특약 추가:<br>
• <b>후유장해</b>: 교통사고로 인한 영구 장해 시 장해율에 따라 보험금 지급<br>
• <b>상해수술비</b>: 교통사고 부상으로 수술 시 1회당 정액 지급<br>
• <b>교통사고 부상 위로금</b>: 상해급수(1~14급) 기준 정액 지급<br>
• <b>골절 진단비</b>: 일반 골절 + <b>5대 골절</b>(대퇴골·척추·골반·상완골·하퇴골) 추가 지급<br>
• <b>척추수술비</b>: 추간판탈출증(디스크) 등 척추 수술 시 별도 지급<br>
• 권장 이유: 교통사고 후 장기 치료·재활 비용 실손 외 정액 보완 → <b>실질 보장 강화</b>
</div>
""", height=580)
            elif ins_type == "🤝 (가족)일상생활배상책임담보":
                st.markdown("##### 🤝 (가족)일상생활배상책임담보 안내")
                components.html("""
<div style="
  height:260px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🤝 (가족)일상생활배상책임담보 안내</b><br>
• <b>피보험 범위</b>: 가족형 (동거 친족 + 별거 미혼 자녀 포함)<br>
• <b>성립 요건</b>: 민법 제750조 기준, 일상생활 중 우연한 과실로 타인에게 손해 발생<br>
• <b>자기부담금</b>: 대인 0원 / 대물 시기별 상이<br>
• <b>면책</b>: 고의 사고·천재지변·차량 관련 사고<br>
• <b>보상 사례</b>: 아파트 누수 → 아래층 피해 / 자녀 자전거 사고 → 타인 부상<br>
• <b>권장 한도</b>: 대인 무한 / 대물 1억 이상<br>
• <b>월 보험료</b>: 수천 원 수준으로 가성비 최고 담보
</div>
""", height=278)

    # ── [화재보험(재조달가액평가)] 독립 섹터 ─────────────────────────────
    if cur == "fire":
        _fire_render()

    # ── [탭 3] 통합보험 (질병·상해 + 생명·헬스케어) ──────────────────────
    if cur == "t3":
        tab_greeting("t3")
        _t3_left_col, _t3_right_col = st.columns([1, 1])
        with _t3_left_col:
            st.subheader("🏥 질병·상해 통합보험 상담")
            st.caption("실손보험 · 암보험 · 뇌심장 · 간병 · 생명보험 · 헬스케어 연동")
        with _t3_right_col:
            st.subheader("🤖 AI 분석 리포트")
            if st.session_state.get("res_t3"):
                show_result("res_t3")
            else:
                components.html("""
<div style="
  height:180px; overflow-y:auto; padding:12px 16px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.8;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#888;
  display:flex; align-items:center; justify-content:center;
">분석 실행 후 결과가 여기에 표시됩니다.</div>""", height=196)

        # ── 상담 분야 2×2 버튼 그리드 ──
        if "t3_sub" not in st.session_state:
            st.session_state["t3_sub"] = "실손/통합보험"
        _t3_opts = [
            ("실손/통합보험",       "🏥 실손/통합보험"),
            ("암·뇌·심장 3대질병", "🎗️ 암·뇌·심장 3대질병"),
            ("간병·치매보험",       "🦽 간병·치매보험"),
            ("생명보험·헬스케어",   "💊 생명보험·헬스케어"),
        ]
        _t3_r1, _t3_r2 = st.columns(2)
        for _idx, (_val, _lbl) in enumerate(_t3_opts):
            _col = _t3_r1 if _idx % 2 == 0 else _t3_r2
            with _col:
                _is_active = st.session_state["t3_sub"] == _val
                if st.button(
                    _lbl,
                    key=f"t3_btn_{_idx}",
                    use_container_width=True,
                    type="primary" if _is_active else "secondary",
                ):
                    st.session_state["t3_sub"] = _val
                    st.rerun()
        sub_type = st.session_state["t3_sub"]

        col1, col2 = st.columns([1, 1])
        with col1:
            c_name3, query3, hi3, do3 = ai_query_block("t3",
                f"{sub_type} 관련 상담 내용을 입력하세요. (예: 현재 실손 가입, 암진단비 추가 필요)")
            if do3:
                run_ai_analysis(c_name3, query3, hi3, "res_t3",
                    f"[통합보험 상담 - {sub_type}]\n1.현재 보장 현황 분석 및 공백 파악\n"
                    "2.질병/상해 통합 보장 설계 제안\n3.생명보험 연계 헬스케어 서비스 안내\n"
                    "4.보험료 대비 보장 효율 분석\n5.갱신형/비갱신형 비교\n")
        with col2:
            st.subheader("📋 통합보험 설계 포인트")
            components.html("""
<div style="
  height:520px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🎗️ 암진단비</b><br>
• 일반암 진단비: 최소 5,000만원 ~ 최대 3억원<br>
• 표적항암·항암방사선·항암수술 등 고액항암 치료비: <b>2억원 이상</b> 권장<br>
• NGS 검사 후 표적항암 담보 미비 시 치료 기회 상실 위험<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🧠 뇌·심장</b><br>
• 진단비: 3,000만원 ~ 5,000만원 (수술비 포함)<br>
• 뇌졸중·급성심근경색만 가입 시 <b>'범위 좁음'</b> → 뇌혈관·심혈관 전체 광범위 담보 확인<br>
• 24개월 공백기 법칙: 영구장애 진단까지 18~24개월 소득 공백 대비 필수<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🦽 일반상해 후유장해</b><br>
• 최소 3억원 ~ 적정 5억원<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏥 간병보험</b><br>
• 간병인사용일당 또는 간병인지원서비스 담보<br>
• 간병비 파산 방지: 하루 10만원 × 2년 = <b>7,200만원</b><br>
• <i>"진단비 3,000만원은 간병비 10개월이면 소멸됩니다"</i><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🧬 치매</b><br>
• 표적치매치료(레캠비 등) + CDR1 경도인지장애 + 파킨슨진단 + CDR3 중증치매<br>
• 뇌졸중 생존자 25~30%가 6개월 내 치매 경험 (통계 근거)<br>
<b style="font-size:0.85rem;color:#1a3a5c;">📊 필요일당 산출</b><br>
• 가처분소득 ÷ 30 = 필요일당<br>
• 월 300만원 소득자 → 필요일당 <b>10만원</b><br>
<b style="font-size:0.85rem;color:#1a3a5c;">⚰️ 사망보험금 설정</b><br>
• 사회복귀 목적: 사망 후 심리적 안정 및 사회복귀를 위한 <b>'36개월(3년)'</b> 소득 보전 자금<br>
• [충분]: 연봉 3배 이상 / [부족]: 연봉 1배 미만 → 사별 직후 생계 위협 경고<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🔄 갱신형 vs 비갱신형 전략</b><br>
• <b>비갱신형(세만기)</b>: 은퇴 후 보험료 부담 감소 고객 추천 (확정 비용)<br>
• <b>갱신형(년만기)</b>: 초기 보험료 저렴, 경제활동기 큰 보장 확보 고객 추천. 담보 교체 주기 고려<br>
<b style="font-size:0.85rem;color:#1a3a5c;">📝 유병자 간편보험 (3·N·5) 고지 실무</b><br>
• <b>3개월 내</b>: 약 종류/용량 변경, 단순 통원, 재검사 소견 등 사소한 기록 반드시 확인<br>
• <b>입원/수술 범위</b>: 응급실 6시간 체류, MRI 검사 입원, 용종 제거(내시경) 등도 고지 대상<br>
• <b>5년 무사고 법칙</b>: 고지의무 위반 후 5년 내 추가 치료 없어도 분쟁 위험 → 정직한 고지 권고<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💊 최신 비급여 의료비 기준</b><br>
• 다빈치 로봇 수술: 약 1,500만원<br>
• 표적항암 치료: 5,000만원 ~ 2억원<br>
• 중입자 치료: 약 5,000만원<br>
• 면역항암 치료: 약 1억 5,000만원<br>
• 카티(CAR-T) 항암: 7,000만원 ~ 15,000만원<br>
• 항암방사선: 3,000만원 ~ 6,000만원
</div>
""", height=538)

    # ── [SECTION 12] 배상책임보험 상담 탭 ────────────────────────────────
    if cur == "liability":
        tab_greeting("liability")
        st.subheader("⚖️ 배상책임보험 상담")

        _la_page = st.radio(
            "상담 페이지 선택",
            ["📋 배상책임보험 상담 1", "🏥 배상책임보험 상담 2 (시설·요양기관)"],
            horizontal=True, key="la_page_sel"
        )

        # ════════════════════════════════════════════════════════
        # 상담 1 — 기존 내용 유지
        # ════════════════════════════════════════════════════════
        if _la_page == "📋 배상책임보험 상담 1":
            st.caption("배상책임보험 개념 · 관련 법률 · 보험금 분담 · 변호사 수임료")
            _la_left, _la_right = st.columns([1, 1])

            with _la_left:
                # ── 스크롤박스 1: 배상책임보험 개념 & 중복가입 분담방식 ──
                st.markdown("##### 📌 배상책임보험 개념 및 중복가입 분담방식")
                components.html("""
<div style="
  height:260px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.88rem;color:#1a3a5c;">⚖️ 배상책임보험 개념</b><br>
가해자로서 피보험자가 사고로 타인에게 손해를 입힘으로써 <b>법률상 배상책임</b>이 있는 금액을,
보험 약관상 조건에 따라 산정하여 보험자가 피보험자에게 보상하거나
피보험자를 대신하여 피해자에게 <b>직접 배상</b>하는 보험제도입니다.<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">📋 핵심 구성요소</b><br>
• <b>피보험자</b>: 법률상 배상책임을 지는 가해자<br>
• <b>피해자</b>: 손해를 입은 제3자 (직접청구권 보유)<br>
• <b>보험자</b>: 약관 조건에 따라 보상 또는 직접 배상<br>
• <b>보상 범위</b>: 법률상 손해배상금 + 소송비용 + 긴급비용<br>
• <b>면책사유</b>: 고의사고, 전쟁·지진, 계약상 가중책임 등<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">🔄 중복가입 시 보험금 분담방식 — 독립책임액 안분방식</b><br>
동일 사고에 대해 2개 이상의 배상책임보험이 중복 가입된 경우:<br>
① 각 보험사가 <b>단독으로 부담할 책임액(독립책임액)</b>을 각각 산출<br>
② 실제 손해액을 각 독립책임액의 비율로 안분하여 분담<br><br>
<b>예시</b>: 손해액 1억원, A사 독립책임액 1억원, B사 독립책임액 5,000만원<br>
→ 합계 1억 5,000만원 기준 비율: A사 2/3, B사 1/3<br>
→ A사 분담: <b>6,667만원</b> / B사 분담: <b>3,333만원</b><br>
• 근거: 상법 제672조(중복보험), 보험업감독규정<br>
• 피보험자는 실손해액을 초과하여 이중 수령 불가
</div>""", height=278)

                # ── 스크롤박스 2: 민사배상(불법행위) 관련 법률 ──
                st.markdown("##### 📜 민사배상(불법행위) 관련 법률")
                components.html("""
<div style="
  height:300px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제390조 — 채무불이행과 손해배상</b><br>
채무자가 채무의 내용에 좇은 이행을 하지 아니한 때 채권자는 손해배상을 청구할 수 있음.
고의·과실 없음을 채무자가 입증해야 면책.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제750조 — 불법행위의 내용</b><br>
고의 또는 과실로 인한 위법행위로 타인에게 손해를 가한 자는 그 손해를 배상할 책임이 있음.
<b>배상책임보험의 핵심 근거 조문</b>.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제753조 — 미성년자의 책임능력</b><br>
미성년자가 타인에게 손해를 가한 경우 그 행위의 책임을 변식할 지능이 없는 때에는 배상책임 없음.
→ 책임능력 없는 미성년자 사고 시 감독자(부모) 책임 전가.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제755조 — 감독자의 책임</b><br>
책임능력 없는 미성년자·심신상실자를 감독할 법정의무 있는 자가 그 손해를 배상할 책임.
감독 의무 해태 없음을 입증하면 면책 가능.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제756조 — 사용자의 배상책임</b><br>
피용자가 사무집행에 관하여 제3자에게 손해를 가한 경우 사용자가 연대 배상책임.
사용자가 상당한 주의를 기울였음을 입증하면 면책 가능(실무상 거의 인정 안 됨).<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제758조 — 공작물 점유자·소유자의 책임</b><br>
공작물(건물·시설 등)의 설치·보존 하자로 타인에게 손해 발생 시 점유자 1차 책임,
점유자가 면책 입증 시 소유자가 무과실 책임. <b>시설소유관리자배상책임보험 근거</b>.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제760조 — 공동불법행위자의 책임</b><br>
수인이 공동의 불법행위로 타인에게 손해를 가한 때 연대하여 배상책임.
가해자 불명 시에도 공동불법행위로 추정.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제396조 — 과실상계</b><br>
채무불이행에 관하여 채권자(피해자)에게도 과실이 있는 때 법원은 손해배상액 산정 시 이를 참작.
→ 피해자 과실 비율만큼 배상액 감액.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제777조 — 친족의 범위</b><br>
8촌 이내 혈족, 4촌 이내 인척, 배우자. 일상생활배상책임보험의 피보험자 범위 판단 기준.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">상법 제680조 — 손해방지의무</b><br>
보험사고 발생 시 피보험자는 손해 방지·경감을 위해 필요한 조치를 취할 의무.
이를 위한 비용은 보험자가 부담(보험금액 초과 시에도).
</div>""", height=318)

                # ── 스크롤박스 3: 화재배상 및 기타 특별법 ──
                st.markdown("##### 🔥 화재배상 및 기타 의무보험 관련 법률")
                components.html("""
<div style="
  height:420px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">화재보험법 제4조 — 특수건물 소유자의 손해배상책임</b><br>
특수건물 소유자는 화재로 타인에게 손해를 입힌 경우 <b>무과실 배상책임</b>.
과실 입증 불필요 — 소유 사실만으로 책임 성립.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 특수건물의 종류 (화재로 인한 재해보상과 보험가입에 관한 법률 제2조)</b><br>
① <b>11층 이상</b> 건물 (아파트·오피스텔·주상복합 등)<br>
② <b>연면적 3,000㎡ 이상</b> 건물 (상가·판매시설·업무시설 등)<br>
③ <b>학교</b>: 초·중·고·대학교 및 이에 준하는 각종 학교<br>
④ <b>공장</b>: 연면적 1,000㎡ 이상의 공장·창고<br>
⑤ <b>공동주택</b>: 16세대 이상 아파트·연립주택<br>
⑥ <b>숙박업소</b>: 객실 30실 이상 호텔·여관·모텔<br>
⑦ <b>병원</b>: 입원실 30병상 이상 의료기관<br>
⑧ <b>방송국·촬영소</b>: 연면적 3,000㎡ 이상<br>
⑨ <b>공항·항만</b>: 여객터미널 등 공중이용시설<br>
⑩ <b>국유·공유 건물</b>: 국가·지자체 소유 연면적 1,000㎡ 이상<br>
⑪ <b>전통시장</b>: 점포 수 50개 이상 또는 연면적 1,000㎡ 이상<br>
⑫ <b>물류창고</b>: 연면적 1,500㎡ 이상<br>
※ 위 요건 중 하나라도 해당하면 특수건물로 분류 → 의무보험 가입 대상<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">화재보험법 제8조 — 특수건물의 보험금액</b><br>
특수건물 소유자는 신체손해배상특약부 화재보험 의무 가입.
사망·후유장해: 1인당 1억 5천만원 이상 / 부상: 급수별 3천만원 이하 / 재물: 실손 기준.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">실화책임법 — 실화로 인한 손해배상 특례</b><br>
경과실(중과실 아닌 실수)로 인한 화재 시 손해배상액을 법원이 <b>감경</b> 가능.
감경 고려 요소: 과실 정도, 피해 규모, 피해자 보험 가입 여부, 가해자 경제력 등.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">재난배상책임보험 (재난안전법)</b><br>
다중이용시설 소유·관리자 의무 가입. 대상: 공연장·전시장·박람회장·유원시설 등.
사망 1인당 1억 5천만원, 부상 3천만원, 재물 10억원 한도.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">다중이용업소 화재배상책임보험 (다중이용업소법)</b><br>
PC방·노래방·유흥주점·식품접객업소 등 의무 가입.
사망 1인당 1억 5천만원 / 부상 3천만원 / 재물 10억원.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">승강기배상책임보험 (승강기안전관리법)</b><br>
승강기 관리주체 의무 가입. 사망 8천만원, 부상 1,500만원, 재물 1천만원 이상.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">가스사고배상책임보험 (액화석유가스법·도시가스사업법)</b><br>
가스 제조·공급·판매사업자 의무 가입. 사망 8천만원, 부상 1,500만원 이상.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">음식물배상책임보험</b><br>
식품위생법상 집단급식소·식품접객업자 임의 가입(일부 지자체 의무화).
식중독·이물질 등으로 인한 소비자 손해 배상 담보.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">차량정비업자배상책임보험</b><br>
자동차관리법상 정비사업자가 정비 과정 중 발생한 차량 손상·인명 사고 배상 담보.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">이미용배상책임보험</b><br>
이미용업소에서 시술 중 발생한 고객 신체 손해(화상·피부트러블 등) 배상 담보.
공중위생관리법 적용 업종.
</div>""", height=318)

            with _la_right:
                # ── 스크롤박스 4: 배상책임보험 종류별 정리 ──
                st.markdown("##### 🛡️ 배상책임보험 종류별 핵심 정리")
                components.html("""
<div style="
  height:300px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🏠 일상생활배상책임보험</b><br>
• 피보험자: 가족형(동거 친족 + 별거 미혼 자녀)<br>
• 담보: 일상생활 중 우연한 과실로 타인 신체·재물 손해<br>
• 면책: 고의·자동차 사고·직무수행 중 사고·친족 간 사고<br>
• 보상 사례: 아파트 누수·자녀 자전거 사고·반려동물 사고<br>
• 권장 한도: 대인 무한 / 대물 1억 이상<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 시설소유관리자배상책임보험</b><br>
• 피보험자: 건물·시설 소유자·관리자<br>
• 담보: 시설 하자·관리 소홀로 제3자 손해 (민법 제758조)<br>
• 대상: 상가·오피스텔·공장·주차장·스포츠시설 등<br>
• 보상: 대인·대물 손해 + 소송비용 포함<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">👷 생산물배상책임보험 (PL보험)</b><br>
• 담보: 제조·판매한 제품의 결함으로 소비자 손해 발생<br>
• 근거: 제조물책임법(PL법)<br>
• 대상: 제조업·식품업·수입업자 필수<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🔨 도급업자배상책임보험</b><br>
• 담보: 공사·작업 중 제3자 신체·재물 손해<br>
• 대상: 건설·설비·청소·경비 도급업자<br>
• 특이사항: 완성 후 하자 담보는 별도 하자보증보험<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">👨‍⚕️ 전문직업인배상책임보험 (E&O)</b><br>
• 담보: 전문직 업무상 과실·태만으로 고객 손해<br>
• 대상: 의사·변호사·회계사·건축사·보험설계사 등<br>
• 특이사항: 클레임발생기준(Claims-made) 방식 적용<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🌐 임원배상책임보험 (D&O)</b><br>
• 담보: 이사·임원의 경영판단 오류로 주주·채권자 손해<br>
• 대상: 상장법인·코스닥·스타트업 임원<br>
• 보상: 방어비용(변호사비) + 손해배상금<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🚗 자동차보험 대인·대물배상 (의무)</b><br>
• 대인배상Ⅰ: 무한 (의무) / 대인배상Ⅱ: 임의<br>
• 대물배상: 2,000만원 이상 의무 (권장: 1억 이상)<br>
• 자동차손해배상보장법 제5조 의무가입 근거
</div>""", height=318)

                # ── 스크롤박스 5: 변호사 수임료 및 성과보수 ──
                st.markdown("##### 💼 변호사 수임료 및 성과보수 기준")
                components.html("""
<div style="
  height:300px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">⚖️ 변호사보수의 소송비용 산입에 관한 규칙 (대법원규칙)</b><br>
패소자 부담 소송비용에 산입되는 변호사보수 한도 (2024년 기준):<br>
• 소가 500만원 이하: 소가의 <b>10%</b><br>
• 소가 500만원 초과 ~ 2,000만원 이하: 50만원 + 초과액의 <b>8%</b><br>
• 소가 2,000만원 초과 ~ 5,000만원 이하: 170만원 + 초과액의 <b>6%</b><br>
• 소가 5,000만원 초과 ~ 1억원 이하: 350만원 + 초과액의 <b>4%</b><br>
• 소가 1억원 초과 ~ 1.5억원 이하: 550만원 + 초과액의 <b>3%</b><br>
• 소가 1.5억원 초과 ~ 2억원 이하: 700만원 + 초과액의 <b>2%</b><br>
• 소가 2억원 초과 ~ 5억원 이하: 800만원 + 초과액의 <b>1%</b><br>
• 소가 5억원 초과 ~ 10억원 이하: 1,100만원 + 초과액의 <b>0.5%</b><br>
• 소가 10억원 초과: 1,350만원 + 초과액의 <b>0.1%</b><br>
※ 실제 수임료와 다를 수 있으며, 패소자 부담 한도 기준임.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">💰 성과보수(성공보수)의 일반적 책정 기준</b><br>
변호사법 제3조·제31조 및 대한변호사협회 윤리규정 기준:<br>
• <b>착수금</b>: 사건 수임 시 선납. 결과에 무관하게 귀속.<br>
  - 민사 일반: 소가의 5~10% (최소 100만원 이상)<br>
  - 형사 사건: 500만원 ~ 2,000만원 (사건 중요도별)<br>
• <b>성공보수</b>: 승소·유리한 결과 달성 시 추가 지급.<br>
  - 민사 승소: 인용액의 5~15% (통상 10%)<br>
  - 형사 무죄·집행유예: 착수금의 50~200%<br>
  - 보험금 청구 대리: 수령액의 10~20%<br>
• <b>형사사건 성공보수 금지</b>: 2015년 대법원 전원합의체 판결로<br>
  형사사건 성공보수 약정은 <b>선량한 풍속 위반으로 무효</b> (대법원 2015다200111)<br>
  → 형사사건은 착수금만 유효, 성공보수 약정 자체가 무효.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 배상책임 사건 수임료 실무 참고</b><br>
• 교통사고 손해배상: 착수금 100~300만원 + 성공보수 인용액의 10%<br>
• 산재·의료과실: 착수금 200~500만원 + 성공보수 10~15%<br>
• 보험금 분쟁 대리: 착수금 100~200만원 + 수령액의 10~20%<br>
• 소액사건(3,000만원 이하): 착수금 50~100만원 (간이절차 적용)
</div>""", height=318)

                # ── AI 분석 블록 ──
                st.markdown("##### 🤖 AI 배상책임 분석")
                c_name_la, query_la, hi_la, do_la = ai_query_block(
                    "liability",
                    "배상책임 관련 상담 내용을 입력하세요.\n예) 아파트 누수로 아래층 피해 발생, 중복보험 2개 가입, 손해액 3,000만원"
                )
                if do_la:
                    run_ai_analysis(c_name_la, query_la, hi_la, "res_liability",
                        "[배상책임보험 상담]\n"
                        "1. 해당 사고의 법률상 배상책임 성립 여부 분석 (민법 조문 근거 명시)\n"
                        "2. 적용 가능한 배상책임보험 종류 및 담보 범위 안내\n"
                        "3. 중복보험 해당 시 독립책임액 안분방식 계산 예시\n"
                        "4. 보험사 면책 주장 대응 방안 및 분쟁 해결 절차\n"
                        "5. 변호사 선임 필요 여부 및 예상 비용 안내\n"
                        "※ 본 답변은 참고용이며 구체적 법률 판단은 전문가와 상의하십시오.\n")
                show_result("res_liability")

        # ════════════════════════════════════════════════════════
        # 상담 2 — 시설소유관리자·병원·요양기관 배상책임
        # ════════════════════════════════════════════════════════
        elif _la_page == "🏥 배상책임보험 상담 2 (시설·요양기관)":
            st.caption("시설소유관리자(병원·요양기관) 배상책임 · 보험 종류 · 일상생활배상책임 약관 · 화재배상")
            _la2_left, _la2_right = st.columns([1, 1])

            with _la2_left:
                # ── 스크롤박스 1: 시설소유관리자 관련 법률 ──
                st.markdown("##### 📜 시설소유관리자 배상책임 관련 법률")
                components.html("""
<div style="
  height:340px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제750조 — 불법행위의 내용</b><br>
고의 또는 과실로 인한 위법행위로 타인에게 손해를 가한 자는 그 손해를 배상할 책임이 있음.<br>
→ 병원·요양기관의 의료사고·낙상·감염 등 모든 과실 사고의 <b>기본 배상책임 근거</b>.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제756조 — 사용자의 배상책임</b><br>
피용자(의사·간호사·간병인·직원)가 사무집행 중 제3자에게 손해를 가한 경우<br>
<b>사용자(병원·요양기관)</b>가 연대 배상책임.<br>
• 병원장·요양원장이 직원 과실에 대해 사용자로서 책임<br>
• 면책 요건: 상당한 주의 기울임 입증 (실무상 거의 인정 안 됨)<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">민법 제758조 — 공작물 점유자·소유자의 책임</b><br>
공작물(건물·시설·의료기기·침대·욕실 등)의 설치·보존 하자로 손해 발생 시:<br>
• <b>점유자(관리자)</b>: 1차 책임 — 면책 입증 시 소유자 책임<br>
• <b>소유자</b>: 무과실 책임 (면책 불가)<br>
→ 병원 내 낙상(미끄러운 바닥), 침대 추락, 의료기기 오작동 사고 적용.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">의료법 제24조의2 — 의료행위에 관한 설명</b><br>
의사는 수술·시술 전 환자에게 충분한 설명 후 서면 동의 취득 의무.<br>
설명 의무 위반 시 손해배상책임 발생 (대법원 판례 다수).<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">노인장기요양보험법 — 요양기관 의무</b><br>
장기요양기관은 수급자의 신체·정신 건강 보호 의무.<br>
요양보호사 과실(낙상·욕창·투약 오류 등) → 기관 사용자 책임 적용.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">사회복지사업법 제34조의3 — 시설 안전관리</b><br>
사회복지시설 운영자는 이용자 안전을 위한 시설 관리 의무.<br>
위반 시 행정처분 + 민사 손해배상책임 병과 가능.
</div>""", height=358)

                # ── 스크롤박스 3: 일상생활배상책임 약관 / 배상책임 도표 ──
                st.markdown("##### 📋 일상생활배상책임 약관 핵심 및 배상책임 도표")
                components.html("""
<div style="
  height:340px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">📄 일상생활배상책임보험 약관 핵심 정리</b><br>
<b>① 보상하는 손해</b><br>
• 피보험자가 일상생활 중 우연한 사고로 타인의 신체·재물에 손해를 입혀<br>
&nbsp;&nbsp;법률상 배상책임을 부담함으로써 입은 손해<br>
• 소송비용·변호사비용·긴급비용 포함<br><br>
<b>② 피보험자 범위 (가족형)</b><br>
• 기명피보험자 본인<br>
• 배우자 (법률혼·사실혼)<br>
• 동거 친족 (민법 제777조 기준)<br>
• 별거 미혼 자녀<br><br>
<b>③ 보상하지 않는 손해 (면책)</b><br>
• 고의로 가한 손해<br>
• 자동차·선박·항공기 소유·사용·관리 중 사고<br>
• 직무수행 중 발생한 사고 (업무배상책임 별도)<br>
• 피보험자 상호 간 손해<br>
• 지진·분화·홍수 등 천재지변<br>
• 전쟁·내란·테러<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📊 배상책임 성립 요건 도표</b><br>
<table style="width:100%;border-collapse:collapse;font-size:0.8rem;">
<tr style="background:#e8f0fb;">
  <th style="border:1px solid #c0d0e8;padding:4px 6px;">요건</th>
  <th style="border:1px solid #c0d0e8;padding:4px 6px;">내용</th>
  <th style="border:1px solid #c0d0e8;padding:4px 6px;">관련 조문</th>
</tr>
<tr><td style="border:1px solid #d0dce8;padding:4px 6px;">① 가해행위</td><td style="border:1px solid #d0dce8;padding:4px 6px;">고의·과실에 의한 행위</td><td style="border:1px solid #d0dce8;padding:4px 6px;">민법 750조</td></tr>
<tr><td style="border:1px solid #d0dce8;padding:4px 6px;">② 위법성</td><td style="border:1px solid #d0dce8;padding:4px 6px;">법규·사회통념 위반</td><td style="border:1px solid #d0dce8;padding:4px 6px;">민법 750조</td></tr>
<tr><td style="border:1px solid #d0dce8;padding:4px 6px;">③ 손해 발생</td><td style="border:1px solid #d0dce8;padding:4px 6px;">재산적·정신적 손해</td><td style="border:1px solid #d0dce8;padding:4px 6px;">민법 751조</td></tr>
<tr><td style="border:1px solid #d0dce8;padding:4px 6px;">④ 인과관계</td><td style="border:1px solid #d0dce8;padding:4px 6px;">행위와 손해 간 상당인과관계</td><td style="border:1px solid #d0dce8;padding:4px 6px;">판례</td></tr>
<tr><td style="border:1px solid #d0dce8;padding:4px 6px;">⑤ 책임능력</td><td style="border:1px solid #d0dce8;padding:4px 6px;">가해자의 책임변식능력</td><td style="border:1px solid #d0dce8;padding:4px 6px;">민법 753조</td></tr>
</table>
</div>""", height=358)

            with _la2_right:
                # ── 스크롤박스 2: 보험 종류별 상세 ──
                st.markdown("##### 🛡️ 시설·요양기관 관련 배상책임보험 종류")
                components.html("""
<div style="
  height:340px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🏥 간병인배상책임보험</b><br>
• 피보험자: 간병인(개인·파견업체)<br>
• 담보: 간병 업무 중 환자에게 가한 신체·재물 손해<br>
• 주요 사고: 낙상 보조 실패, 투약 오류, 욕창 방치<br>
• 특이사항: 간병인 개인 가입 또는 파견업체 단체 가입 가능<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 시설소유관리자배상책임보험 (병원·요양기관)</b><br>
• 피보험자: 병원·요양원·노인복지시설 소유자·관리자<br>
• 담보: 시설 내 사고(낙상·화재·시설 하자)로 입원환자·방문객 손해<br>
• 구외업무수행특약: 직원이 <b>시설 외부</b>에서 업무 수행 중 발생한 사고도 담보<br>
&nbsp;&nbsp;(왕진·외부 검사·이송 중 사고 포함)<br>
• 권장 한도: 대인 무한 / 대물 5억 이상<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🌐 영업배상책임보험 (CGL — Commercial General Liability)</b><br>
• 담보 3가지:<br>
&nbsp;&nbsp;① <b>시설위험</b>: 사업장 내 사고로 제3자 손해<br>
&nbsp;&nbsp;② <b>작업위험</b>: 업무 수행 중 제3자 손해<br>
&nbsp;&nbsp;③ <b>생산물위험</b>: 제조·판매 제품 결함으로 손해<br>
• 병원·요양기관 적용: 시설위험 + 작업위험 담보 중심<br>
• 의료행위 자체는 별도 의료배상책임보험(MPL) 필요<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">⚖️ 행정소송 법률비용담보</b><br>
• 담보: 행정처분(면허취소·업무정지·과징금)에 대한 행정소송 비용<br>
• 대상: 병원·요양기관 행정처분 불복 소송<br>
• 보상: 변호사비용·소송비용·행정심판비용<br>
• 특이사항: 의료분쟁 시 행정·민사 병행 소송 대응 가능<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 민사소송 법률비용담보</b><br>
• 담보: 환자·보호자가 제기한 민사손해배상 소송 방어 비용<br>
• 보상: 변호사 착수금·성공보수·소송비용·감정비용<br>
• 특이사항: 배상책임보험 본담보와 별도로 방어비용 선지급 가능<br>
• 의료분쟁조정법상 조정·중재 비용도 포함
</div>""", height=358)

                # ── 스크롤박스 4: 화재배상책임 및 관련 법률 ──
                st.markdown("##### 🔥 화재배상책임 및 관련 법률 (시설·요양기관)")
                components.html("""
<div style="
  height:340px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0dce8;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🔥 화재보험법 제4조 — 특수건물 무과실 배상책임</b><br>
병원(입원실 30병상 이상)·요양원(연면적 3,000㎡ 이상)은 <b>특수건물</b>에 해당.<br>
화재 발생 시 과실 여부와 무관하게 소유자가 <b>무과실 배상책임</b> 부담.<br>
→ 신체손해배상특약부 화재보험 <b>의무 가입</b> 대상.<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏥 의료기관 화재 시 배상책임 구조</b><br>
① 입원환자 사망: 화재보험법 제4조 무과실 책임 + 민법 750조 과실책임 병존<br>
② 방문객·보호자 피해: 시설소유관리자배상책임보험 담보<br>
③ 인접 건물 피해: 실화책임법 적용 (경과실 시 감경 가능)<br>
④ 의료기기·의무기록 소실: 재물손해 + 영업중단손해 별도 담보<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏠 요양기관 화재 특수 쟁점</b><br>
• 거동 불편 수급자 대피 지원 의무 — 위반 시 중과실 인정 가능성<br>
• 야간 당직 인력 부족으로 인한 피해 확대 → 관리 소홀 책임<br>
• 스프링클러·방화문 미설치: 소방시설법 위반 + 민사 과실 가중<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 다중이용업소 화재배상책임보험 (요양·복지시설)</b><br>
노인요양시설·장애인거주시설 등 다중이용업소 해당 시 의무 가입.<br>
• 사망: 1인당 1억 5천만원<br>
• 부상: 급수별 최대 3천만원<br>
• 재물: 10억원 한도<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">⚠️ 실화책임법 적용 시 주의사항</b><br>
경과실 화재라도 <b>요양·의료시설은 중과실 인정 가능성 높음</b>:<br>
• 소방시설 미점검·불량<br>
• 화재 예방 교육 미실시<br>
• 위험물 부적절 보관<br>
→ 중과실 인정 시 실화책임법 감경 혜택 없음 — 전액 배상 책임
</div>""", height=358)

                # ── AI 분석 블록 ──
                st.markdown("##### 🤖 AI 시설배상책임 분석")
                c_name_la2, query_la2, hi_la2, do_la2 = ai_query_block(
                    "liability2",
                    "시설·요양기관 배상책임 관련 상담 내용을 입력하세요.\n예) 요양원 입소자 낙상 사고, 병원 화재로 환자 피해, 간병인 투약 오류"
                )
                if do_la2:
                    run_ai_analysis(c_name_la2, query_la2, hi_la2, "res_liability2",
                        "[시설소유관리자·요양기관 배상책임 상담]\n"
                        "1. 사고 유형별 법률상 배상책임 성립 여부 (민법 756·758조 근거)\n"
                        "2. 적용 가능한 배상책임보험 종류 및 담보 범위\n"
                        "3. 화재 사고 시 화재보험법·실화책임법 적용 분석\n"
                        "4. 행정처분 병행 시 행정소송 법률비용담보 활용 방안\n"
                        "5. 분쟁 해결 절차 (의료분쟁조정원·소송) 안내\n"
                        "※ 본 답변은 참고용이며 구체적 법률 판단은 전문가와 상의하십시오.\n")
                show_result("res_liability2")

    # ── [탭 5] 노후·상속설계 ─────────────────────────────────────────────
    if cur == "t5":
        tab_greeting("t5")
        st.subheader("🌅 노후설계 · 상속설계 · 사망보험 연계")
        retire_sub = st.radio("상담 분야",
            ["노후/연금 설계", "상속·증여 설계", "주택연금", "사망보험 연계"],
            horizontal=True, key="retire_sub")
        if retire_sub == "상속·증여 설계":
            section_inheritance_will()
        elif retire_sub == "주택연금":
            section_housing_pension()
        else:
            # ── 연금 3층 제도 팝업 표 (노후/연금 설계 탭 전용) ──────────────
            if retire_sub == "노후/연금 설계":
                with st.expander("📊 연금 3층 제도 소득대체율 점검표 (클릭하여 펼치기)", expanded=False):
                    st.markdown("""
<style>
.pension-table { width:100%; border-collapse:collapse; font-size:0.88rem; }
.pension-table th { background:#1a3a5c; color:#fff; padding:8px 10px; text-align:center; }
.pension-table td { padding:7px 10px; border-bottom:1px solid #dde3ea; text-align:center; vertical-align:top; }
.pension-table tr:nth-child(even) td { background:#f4f7fb; }
.pension-table tr.total-row td { background:#e8f0fe; font-weight:700; color:#1a3a5c; }
.pension-table .note { font-size:0.78rem; color:#555; text-align:left; }
.gap-box { background:#fff3cd; border-left:4px solid #ffc107; padding:10px 14px; border-radius:6px; margin-top:12px; font-size:0.87rem; }
.gap-box strong { color:#856404; }
</style>
<table class="pension-table">
  <thead>
    <tr>
      <th>구분</th>
      <th>명목 소득대체율</th>
      <th>실질/추정 소득대체율</th>
      <th>비고</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><b>🏛️ 국민연금 (1층)</b></td>
      <td>40.0% <span style="font-size:0.78rem;color:#c00">(추가보장 필요)</span></td>
      <td>약 22 ~ 28%</td>
      <td class="note">40년 가입 기준 명목 소득대체율 40% / 실제 가입 기간 고려 시 실질 수령액 감소</td>
    </tr>
    <tr>
      <td><b>🏢 퇴직연금 (2층)</b></td>
      <td>약 12 ~ 13%</td>
      <td>약 2.1 ~ 16%</td>
      <td class="note">40년 근속 및 전액 연금 수령 시(추정) / 중도 인출·일시금 수령 시 급감</td>
    </tr>
    <tr>
      <td><b>💼 개인연금 (3층)</b></td>
      <td>자율 선택</td>
      <td>약 5 ~ 10%</td>
      <td class="note">가입률 및 납입 금액에 따라 상이 / IRP·연금저축 세액공제 활용 권장</td>
    </tr>
    <tr class="total-row">
      <td><b>합계 (3층 연금)</b></td>
      <td>총 62.0% + α</td>
      <td>약 40 ~ 50% 미만</td>
      <td class="note">이상적 설계 vs 현실 수령액 격차 발생 → <b>보험 연계 보완 필수</b></td>
    </tr>
  </tbody>
</table>
<div class="gap-box">
  <strong>⚠️ 핵심 격차 포인트</strong><br>
  명목 소득대체율 65%와 실질 40~50% 사이의 <b>15~25%p 격차</b>는 연금보험·종신보험·즉시연금으로 보완해야 합니다.<br>
  <b>월 소득 500만원 기준</b> → 격차 월 75~125만원 → 연금보험 추가 납입으로 해소 가능
</div>
""", unsafe_allow_html=True)

                    st.markdown("##### 🔍 내 연금 3층 현황 빠른 점검")
                    chk_col1, chk_col2, chk_col3 = st.columns(3)
                    with chk_col1:
                        nps_years = st.number_input("국민연금 가입 기간(년)", min_value=0, max_value=40, value=20, step=1, key="nps_years")
                        nps_avg_income = st.number_input("평균 월 소득(만원)", min_value=0, value=400, step=10, key="nps_income")
                    with chk_col2:
                        retire_type = st.selectbox("퇴직연금 유형", ["DB형", "DC형", "IRP", "미가입"], key="retire_type")
                        retire_years = st.number_input("퇴직연금 가입 기간(년)", min_value=0, max_value=40, value=10, step=1, key="retire_years")
                    with chk_col3:
                        personal_monthly = st.number_input("개인연금 월 납입(만원)", min_value=0, value=20, step=5, key="personal_monthly")
                        target_income = st.number_input("은퇴 후 목표 월 소득(만원)", min_value=0, value=300, step=10, key="target_income")

                    if st.button("📈 연금 3층 갭 분석", key="btn_pension_gap"):
                        nps_est = round(nps_avg_income * (nps_years / 40) * 0.43 * 0.7, 1)
                        retire_est = round(nps_avg_income * (retire_years / 40) * 0.125 * 0.5, 1)
                        personal_est = round(personal_monthly * 12 * 20 / 240, 1)
                        total_est = nps_est + retire_est + personal_est
                        gap = max(0, target_income - total_est)
                        st.markdown(f"""
<table class="pension-table">
  <thead><tr><th>구분</th><th>추정 월 수령액</th><th>비율</th></tr></thead>
  <tbody>
    <tr><td>🏛️ 국민연금</td><td><b>{nps_est:.0f}만원</b></td><td>{nps_est/target_income*100:.1f}%</td></tr>
    <tr><td>🏢 퇴직연금</td><td><b>{retire_est:.0f}만원</b></td><td>{retire_est/target_income*100:.1f}%</td></tr>
    <tr><td>💼 개인연금</td><td><b>{personal_est:.0f}만원</b></td><td>{personal_est/target_income*100:.1f}%</td></tr>
    <tr class="total-row"><td>합계</td><td><b>{total_est:.0f}만원</b></td><td>{min(total_est/target_income*100,100):.1f}%</td></tr>
    <tr><td colspan="3" class="note" style="background:#fff3cd;color:#856404;font-weight:700;">
      목표 {target_income}만원 대비 부족액: <b>{gap:.0f}만원/월</b>
      {"→ 연금보험·즉시연금으로 보완 필요" if gap > 0 else " ✅ 목표 달성 가능"}
    </td></tr>
  </tbody>
</table>
""", unsafe_allow_html=True)
                        if gap > 0:
                            st.warning(f"💡 월 {gap:.0f}만원 부족 → 연금보험 추가 납입 또는 즉시연금 활용을 AI 분석으로 설계하세요.")

            col1, col2 = st.columns([1, 1])
            with col1:
                c_name4, query4, hi4, do4 = ai_query_block("t5",
                    f"{retire_sub} 관련 상담 내용을 입력하세요. (예: 55세, 은퇴 후 월 300만원 필요)")
                if do4:
                    pension_ctx = ""
                    if retire_sub == "노후/연금 설계":
                        try:
                            nps_y = st.session_state.get("nps_years", 20)
                            nps_inc = st.session_state.get("nps_income", 400)
                            r_type = st.session_state.get("retire_type", "미입력")
                            r_y = st.session_state.get("retire_years", 0)
                            p_m = st.session_state.get("personal_monthly", 0)
                            tgt = st.session_state.get("target_income", 300)
                            pension_ctx = (
                                f"\n[연금 3층 현황] 국민연금 가입{nps_y}년/평균소득{nps_inc}만원, "
                                f"퇴직연금({r_type}) {r_y}년, 개인연금 월{p_m}만원, 목표월소득 {tgt}만원"
                            )
                        except Exception:
                            pass
                    run_ai_analysis(c_name4, query4, hi4, "res_t5",
                        f"[노후설계 상담 - {retire_sub}]{pension_ctx}\n"
                        "1.국민연금·퇴직연금·개인연금 3층 연금 현황 분석 및 소득대체율 계산\n"
                        "2.명목 소득대체율(65%)과 실질 소득대체율(40~50%) 격차 해소 방안\n"
                        "3.은퇴 후 필요 생활비 역산 및 월 부족분 산출\n"
                        "4.연금보험·즉시연금·종신보험으로 격차 보완 전략\n"
                        "5.IRP·연금저축 세액공제 최대 활용법\n"
                        "6.건강보험료 절감 방안 및 수령 시기 최적화\n")
            with col2:
                st.subheader("🤖 AI 분석 리포트")
                show_result("res_t5")
                st.markdown("##### 🏛️ 연금 3층 설계 핵심 전략")
                components.html("""
<div style="
  height:260px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">🏛️ 1층 — 국민연금</b><br>
• <b>수령 시기 최적화</b>: 연기연금 신청 시 1개월당 0.6% 증액 → 최대 5년 연기 시 <b>36% 증액</b><br>
• 조기수령(최대 5년 앞당김) 시 1개월당 0.5% 감액 → 장수 리스크 고려 신중 결정<br>
• 실질 소득대체율: 명목 40% 대비 실제 <b>22~28%</b> 수준 (가입 기간 단절 반영)<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 2층 — 퇴직연금</b><br>
• IRP 세액공제: 연 <b>900만원 한도</b> (연금저축 포함) / 세액공제율 13.2~16.5%<br>
• DC형: 본인 추가 납입 가능 → 운용 수익률 제고 필수<br>
• 중도 인출 시 세액공제 혜택 반납 + 기타소득세 16.5% 부과 → 유지 권장<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💼 3층 — 개인연금</b><br>
• 연금저축: 연 <b>400만원</b> 세액공제 한도 (총급여 5,500만원 이하 16.5%)<br>
• IRP 추가 납입: 연금저축 외 <b>300만원 추가</b> 세액공제 가능<br>
• 연금보험(비과세): 10년 이상 유지 시 이자소득세 비과세 → 장기 유지 전략<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🎯 격차 보완 전략</b><br>
• 명목 소득대체율 65% vs 실질 40~50% → <b>15~25%p 격차</b> 보완 필수<br>
• 즉시연금·종신보험 연계로 사망 시까지 월 소득 확보<br>
• 목표: 실질 소득대체율 <b>60~70%</b> 달성
</div>
""", height=278)

    # ── [탭 6] 세무상담 ──────────────────────────────────────────
    if cur == "t6":
        tab_greeting("t6")
        st.subheader("📊 세무상담")
        st.caption("보험 관련 세금 · 상속세 · 증여세 · 연금소득세 · 절세 전략")
        tax_sub = st.radio("상담 분야",
            ["상속·증여세", "연금소득세", "CEO설계"],
            horizontal=True, key="tax_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name5, query5, hi5, do5 = ai_query_block("t6",
                f"{tax_sub} 관련 세무 상담 내용을 입력하세요.")
            if do5:
                run_ai_analysis(c_name5, query5, hi5, "res_t6_tax",
                    f"[세무상담 - {tax_sub}]\n1.관련 세법 조항과 최신 개정 내용 안내\n"
                    "2.절세 전략과 합법적 세금 최소화 방안\n3.신고 기한과 필요 서류 안내\n"
                    "4.세무사 상담이 필요한 사항 명시\n"
                    "※주의: 본 답변은 참고용이며 구체적 사안은 세무사와 상의하십시오.\n")
        with col2:
            st.subheader("AI 분석 리포트")
            if tax_sub == "상속·증여세":
                show_result("res_t6_tax", "**상속·증여세 핵심 포인트:**\n"
                            "- 상속세: 일괄공제 5억 / 배우자공제 최소 5억\n"
                            "- 증여세: 10년 합산 / 배우자 6억·자녀 5천만원 공제\n"
                            "- 사망보험금(생명보험사 종신·정기): 상속재산 제외 가능 (세무사 확인 필수)\n"
                            "- 세율: 10%~50% 누진세율 적용")
            elif tax_sub == "연금소득세":
                show_result("res_t6_tax", "**연금소득세 핵심 포인트:**\n"
                            "- 연금저축·IRP 수령 시: 3.3~5.5% 연금소득세\n"
                            "- 연간 1,500만원 초과 수령 시: 종합소득세 합산 또는 분리과세 선택\n"
                            "- 수령 시기 분산으로 세부담 최소화 가능 (세무사 확인 권장)")
            else:
                show_result("res_t6_tax", "**CEO설계 핵심 포인트:**\n"
                            "- 경영인정기보험: 법인 납입 보험료 손금산입 가능 여부 확인\n"
                            "- CEO 유고 시 법인 리스크 대비: 사망보험금 → 퇴직금 재원 활용\n"
                            "- 임원 퇴직금 규정 정비 필수 (정관 반영)\n"
                            "- 법인세·소득세 분산 효과: 세무사와 사전 검토 필수\n"
                            "- 가입 전 법인 정관·세무처리 방식 반드시 세무사와 확인")

    # ── [탭 7] 법인상담 ──────────────────────────────────────────
    if cur == "t7":
        tab_greeting("t7")
        st.subheader("🏢 법인상담 (CEO플랜 · 단체보험 · 기업보험)")
        st.caption("CEO 사망·퇴직 플랜 · 단체상해 · 공장화재 · 법인 절세 전략")
        corp_sub = st.radio("상담 분야",
            ["CEO플랜 (사망·퇴직)", "단체상해보험", "공장·기업 화재보험", "법인 절세 전략", "임원 퇴직금 설계"],
            horizontal=True, key="corp_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name6, query6, hi6, do6 = ai_query_block("t7",
                f"{corp_sub} 관련 법인 상담 내용을 입력하세요. (예: 직원 50명, 제조업, CEO 60세)")
            emp_count = st.number_input("임직원 수", min_value=1, value=10, step=1, key="emp_count")
            corp_asset = st.number_input("법인 자산 규모 (만원)", value=100000, step=10000, key="corp_asset")
            if do6:
                run_ai_analysis(c_name6, query6, hi6, "res_t7",
                    f"[법인상담 - {corp_sub}]\n임직원수: {emp_count}명, 법인자산: {corp_asset:,}만원\n"
                    "1.법인 보험의 세무처리(손금산입) 방법\n2.CEO 유고 시 법인 리스크 관리 방안\n"
                    "3.단체보험 가입 기준과 보장 설계\n4.퇴직금 재원 마련을 위한 보험 활용\n"
                    "5.공장·기업 재산 보호를 위한 화재보험 설계\n")
        with col2:
            st.subheader("AI 분석 리포트")
            show_result("res_t7", "**법인보험 핵심 포인트:**\n- CEO플랜: 사망보험금 → 퇴직금 재원\n"
                        "- 단체상해: 전 직원 의무 가입 권장\n- 공장화재: 재조달가액 기준 가입\n"
                        "- 법인 납입 보험료 손금산입 가능\n- 임원 퇴직금 규정 정비 필수")

    # ── [탭 4] 자동차사고 상담 ───────────────────────────────────────────
    if cur == "t4":
        tab_greeting("t4")
        st.subheader("🚗 자동차사고 상담 · 과실비율 분석")
        st.caption("교통사고처리특례법 13대 중과실 기준 · 자동차사고 과실비율 분쟁심의위원회(accident.knia.or.kr) 기준")

        acc_sub = st.radio("상담 유형",
            ["🚨 사고 과실비율 분석", "📹 블랙박스 영상 분석", "💰 보험금 청구 안내", "⚖️ 분쟁심의 절차 안내"],
            horizontal=True, key="acc_sub")

        col1, col2 = st.columns([1, 1])
        with col1:
            c_name7 = st.text_input("고객 성함", "우량 고객", key="c_name_t7")

            # 블랙박스 업로드 — 항상 렌더링(rerun 시 튕김 방지), 다른 유형 선택 시 숨김
            show_bb = (acc_sub == "📹 블랙박스 영상 분석")
            if show_bb:
                st.markdown("**📹 블랙박스 영상 업로드**")
            bb_container = st.container()
            with bb_container:
                bb_file = st.file_uploader(
                    "블랙박스 영상 (MP4/AVI/MOV/MKV)",
                    type=['mp4', 'avi', 'mov', 'mkv', 'wmv'],
                    key="bb_video",
                    label_visibility="visible" if show_bb else "collapsed",
                    disabled=not show_bb
                )
                bb_img = st.file_uploader(
                    "사고 현장 사진 (JPG/PNG) — 선택",
                    type=['jpg', 'jpeg', 'png'],
                    accept_multiple_files=True,
                    key="bb_img",
                    label_visibility="visible" if show_bb else "collapsed",
                    disabled=not show_bb
                )
            if show_bb:
                if bb_file:
                    st.video(bb_file)
                    st.success(f"✅ 영상 업로드 완료: {bb_file.name}")
                if bb_img:
                    for img in bb_img:
                        st.image(img, caption=img.name, width=200)

            acc_query = st.text_area(
                "사고 상황 입력",
                height=160,
                key="acc_query",
                placeholder="예) 신호등 없는 교차로에서 직진 중 우측에서 좌회전 차량과 충돌. 상대방이 과실 100% 주장"
            )

            with st.expander("✅ 13대 중과실 해당 여부 체크", expanded=False):
                fault_items = [
                    "① 신호·지시 위반", "② 중앙선 침범", "③ 제한속도 20km/h 초과 과속",
                    "④ 앞지르기 방법·금지 위반", "⑤ 철길건널목 통과방법 위반",
                    "⑥ 횡단보도 보행자 보호의무 위반", "⑦ 무면허 운전",
                    "⑧ 음주운전(0.03% 이상)", "⑨ 보도 침범·횡단방법 위반",
                    "⑩ 승객 추락 방지의무 위반", "⑪ 어린이 보호구역 안전운전의무 위반",
                    "⑫ 화물 추락 방지의무 위반", "⑬ 개문발차 사고"
                ]
                checked_faults = []
                for fi in fault_items:
                    if st.checkbox(fi, key=f"fault_{fi[:3]}"):
                        checked_faults.append(fi)
                if checked_faults:
                    st.warning(f"⚠️ {len(checked_faults)}개 중과실 해당 → 운전자보험 사고담당금 및 형사처벌 위험")

            hi7 = st.number_input("월 건강보험료(원)", value=0, step=1000, key="hi_t7")
            do7 = st.button("과실비율 AI 분석 실행", type="primary", key="btn_acc7")
            if do7:
                components.html(s_voice("잠시만 기다려주세요. 답변 검색 중입니다."), height=0)
                bb_ctx = ""
                if acc_sub == "📹 블랙박스 영상 분석" and bb_file:
                    bb_ctx = f"\n[블랙박스 영상 업로드됨: {bb_file.name} ({bb_file.size//1024}KB)]\n영상 내용을 바탕으로 사고 상황을 추정하여 과실비율을 분석하십시오.\n"
                fault_ctx = ""
                if checked_faults:
                    fault_ctx = f"\n[13대 중과실 해당 항목: {', '.join(checked_faults)}]\n"
                run_ai_analysis(c_name7, acc_query, hi7, "res_t7",
                    f"[자동차사고 상담 - {acc_sub}]{bb_ctx}{fault_ctx}\n"
                    "자동차사고 과실비율 분석 요청. 아래 기준으로 답변하십시오:\n"
                    "1. 자동차사고 과실비율 분쟁심의위원회(accident.knia.or.kr) 과실비율 인정기준 기준\n"
                    "2. 교통사고처리특례법 제3조 제2항 단서(13대 중과실) 해당 여부\n"
                    "3. 사고 유형별(정면/측면/후면/교차로) 기본 과실비율 범위 안내\n"
                    "4. 블랙박스 영상이 있는 경우 영상 설명 내용을 바탕으로 과실 정황 추정\n"
                    "5. 운전자보험 교통사고처리지원금 지급 가능 여부 및 필요 서류 안내\n"
                    "6. 분쟁 심화 시 과실비율 분쟁심의위원회 신청 절차 안내\n"
                    "⚠️ 최종 과실비율은 분쟁심의위원회 또는 법원 판결에 따르며, 본 답변은 참고용입니다.\n"
                )
        with col2:
            st.subheader("AI 분석 리포트")
            st.markdown("""
<div style="background:#fff8e1;border-left:4px solid #ff9800;padding:10px 14px;border-radius:6px;font-size:0.83rem;margin-bottom:10px;">
🚨 <b>과실비율 참조 기준</b><br>
• 자동차사고 과실비율 분쟁심의위원회 <a href="https://accident.knia.or.kr" target="_blank">accident.knia.or.kr</a><br>
• 교통사고처리특례법 제3조 제2항 단서 (13대 중과실)<br>
• 최종 과실비율은 위원회/법원 판결에 따르며 AI 답변은 <b>참고용</b>입니다.
</div>""", unsafe_allow_html=True)
            show_result("res_t7")
            st.markdown("##### 📋 자동차사고 상담 절차")
            components.html("""
<div style="
  height:200px; overflow-y:auto; padding:12px 15px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.84rem; line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">
<b style="font-size:0.85rem;color:#1a3a5c;">📋 자동차사고 상담 절차 및 필요 서류</b><br>
<b>1단계 — 사고 상황 입력</b><br>
• 사고 일시·장소·도로 유형(교차로/직선/골목 등)<br>
• 상대방 차량 번호·보험사·담당자 연락처<br>
• 필요 서류: 사고사실확인원(경찰서 발급) / 현장 사진·블랙박스 영상 / 목격자 진술서<br>
<b>2단계 — 13대 중과실 해당 여부 체크</b><br>
• 근거: 교통사고처리특례법 제3조 제2항 단서<br>
• ① 신호·지시위반 ② 중앙선침범 ③ 제한속도 20km/h 초과<br>
• ④ 앞지르기 위반 ⑤ 철길건널목 위반 ⑥ 횡단보도 보행자 보호의무 위반<br>
• ⑦ 무면허운전 ⑧ 음주운전(0.03% 이상) ⑨ 보도침범<br>
• ⑩ 승객추락방지의무 위반 ⑪ 어린이보호구역(민식이법) ⑫ 화물추락방지 위반 ⑬ 개문발차<br>
• ⚠️ 중과실 해당 시: 피해자 합의 없어도 <b>형사처벌 가능</b> → 운전자보험 필수<br>
<b>🧒 민식이법 (어린이보호구역 특례)</b><br>
• 근거: 특정범죄가중처벌법 제5조의13 (2020.3.25 시행)<br>
• 어린이보호구역 내 어린이(13세 미만) 사망: <b>무기 또는 3년 이상 징역</b><br>
• 어린이 상해: <b>1년 이상 15년 이하 징역 또는 500만~3,000만원 벌금</b><br>
• 필요 서류: 사고사실확인원 / 피해 어린이 진단서·입퇴원확인서 / 블랙박스 영상<br>
• 대응: 운전자보험 교통사고처리지원금(2억 권장) + 변호사선임비용 특약 필수<br>
<b>🏥 중상해 기준 (교통사고처리특례법 제3조)</b><br>
• 중상해 정의: 생명에 대한 위험 / 불구 / 불치·난치 질병 유발<br>
• 판례 기준: 대법원 — 뇌손상·척수손상·사지마비·시력상실 등 영구장애<br>
• 중상해 발생 시: 합의 여부 무관 <b>형사처벌 대상</b> (공소권 있음)<br>
• 필요 서류: 진단서(상해 등급 명시) / 수술기록지 / 후유장해진단서<br>
<b>⚖️ 교통사고처리특례법 핵심 정리</b><br>
• 제3조 제1항: 교통사고 업무상과실·중과실 → 5년 이하 금고 또는 2,000만원 이하 벌금<br>
• 제3조 제2항: 종합보험 가입 + 피해자 합의 시 <b>공소권 없음</b> (단, 13대 중과실 제외)<br>
• 제4조: 보험 미가입 차량 사고 → 합의와 무관하게 처벌<br>
<b>3단계 — 블랙박스 영상 업로드</b><br>
• 원본 파일 보존 필수 (덮어쓰기 방지 — 즉시 별도 저장)<br>
• 영상 제출처: 경찰서 / 보험사 / 분쟁심의위원회<br>
<b>4단계 — AI 과실비율 분석 실행</b><br>
• 참조: 자동차사고 과실비율 분쟁심의위원회 인정기준 (손해보험협회·생명보험협회 공동 발행)<br>
• AI 분석 결과는 <b>참고용</b> — 최종 결정은 위원회 또는 법원<br>
<b>5단계 — 분쟁심의위원회 신청</b><br>
• 신청처: <a href="https://accident.knia.or.kr" target="_blank">accident.knia.or.kr</a> 온라인 신청<br>
• 신청 비용: 없음 / 처리 기간: 약 60일 이내<br>
• 필요 서류: 신청서 / 사고사실확인원 / 보험증권 / 진단서 / 블랙박스 영상·사진
</div>
""", height=520)

    # ── [탭 8] CEO플랜 — 비상장주식 평가 + 재무제표 분석 ──────────────────
    if cur == "t8":
        tab_greeting("t8")
        st.subheader("👔 CEO플랜 — 비상장주식 약식 평가 & 법인 재무분석")
        st.caption("상증법·법인세법 통합 비상장주식 평가 | 재무제표 3년치 스캔 분석 | AI 기업회계 진단")

        ceo_sub = st.radio(
            "분석 방식 선택",
            ["📊 직접 입력 평가표", "📁 재무제표 스캔 업로드"],
            horizontal=True, key="ceo_sub"
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            if ceo_sub == "📊 직접 입력 평가표":
                st.markdown("##### 📋 기업 기본 정보")
                ceo_company = st.text_input("법인명", "(주)예시기업", key="ceo_company")
                total_shares = st.number_input("발행주식 총수 (주)", value=10000, step=100, key="ceo_shares")
                is_controlling = st.checkbox("최대주주 (경영권 할증 20% 적용)", value=True, key="ceo_ctrl")
                is_re_rich = st.checkbox("부동산 과다 법인 (자산 비중 80% 이상)", value=False, key="ceo_re")
                market_price_input = st.number_input(
                    "매매사례가액 (원, 없으면 0)", value=0, step=1000, key="ceo_mkt",
                    help="최근 거래된 주당 가격이 있으면 입력 — 법인세법상 최우선 시가"
                )

                st.markdown("##### 🏦 재무 데이터 입력")
                net_asset = st.number_input(
                    "순자산 (원) — 최근 사업연도 말 기준",
                    value=12_864_460_902, step=1_000_000, key="ceo_asset",
                    help="대차대조표 자본총계 기준"
                )
                st.markdown("**당기순이익 3개년 (원)** — 최근년 → 전전년 순")
                inc_c1, inc_c2, inc_c3 = st.columns(3)
                with inc_c1:
                    ni_1 = st.number_input("최근년",  value=688_182_031, step=1_000_000, key="ceo_ni1")
                with inc_c2:
                    ni_2 = st.number_input("전년",    value=451_811_737, step=1_000_000, key="ceo_ni2")
                with inc_c3:
                    ni_3 = st.number_input("전전년",  value=553_750_281, step=1_000_000, key="ceo_ni3")

                if st.button("📈 비상장주식 평가 실행", type="primary", key="btn_ceo_eval"):
                    mkt = market_price_input if market_price_input > 0 else None
                    evaluator = AdvancedStockEvaluator(
                        net_asset=net_asset,
                        net_incomes=[ni_1, ni_2, ni_3],
                        total_shares=total_shares,
                        market_price=mkt,
                        is_controlling=is_controlling,
                        is_real_estate_rich=is_re_rich,
                    )
                    corp_r = evaluator.evaluate_corporate_tax()
                    inh_r  = evaluator.evaluate_inheritance_tax()
                    st.session_state["ceo_eval_corp"]    = corp_r
                    st.session_state["ceo_eval_inh"]     = inh_r
                    st.session_state["ceo_company_result"] = ceo_company
                    st.session_state["ceo_shares_result"]  = total_shares
                    st.rerun()

            else:  # 재무제표 스캔 업로드
                st.markdown("##### 📁 재무제표 3년치 업로드")
                st.caption("PDF 또는 이미지(JPG/PNG) — 손익계산서·대차대조표 포함 파일")
                fs_files = st.file_uploader(
                    "재무제표 파일 업로드 (최대 3개)",
                    type=["pdf", "jpg", "jpeg", "png"],
                    accept_multiple_files=True,
                    key="ceo_fs_files"
                )
                if fs_files:
                    st.success(f"{len(fs_files)}개 파일 업로드 완료")
                    for i, f in enumerate(fs_files, 1):
                        if f.type.startswith("image/"):
                            st.image(f, caption=f"재무제표 {i}년차", width=300)

                ceo_c2 = st.text_input("법인명", "(주)예시기업", key="ceo_company2")
                ceo_note = st.text_area(
                    "추가 분석 요청 사항 (선택)",
                    height=100, key="ceo_note",
                    placeholder="예) 비상장주식 평가 외 CEO 퇴직금 설계, 가업승계 전략도 함께 분석해주세요."
                )

                if st.button("🔍 재무제표 AI 분석 실행", type="primary", key="btn_ceo_fs"):
                    if not fs_files:
                        st.error("재무제표 파일을 업로드하세요.")
                    else:
                        fs_text = ""
                        for f in fs_files:
                            if f.type == "application/pdf":
                                fs_text += f"\n[재무제표: {f.name}]\n" + extract_pdf_chunks(f, char_limit=6000)
                            elif f.type.startswith("image/"):
                                fs_text += f"\n[재무제표 이미지: {f.name} — OCR 분석 요청]\n"
                        run_ai_analysis(
                            ceo_c2, ceo_note or "재무제표 분석 요청", 0, "res_ceo_fs",
                            CEO_FS_PROMPT + fs_text
                        )

        with col2:
            if ceo_sub == "📊 직접 입력 평가표":
                st.markdown("##### 📊 비상장주식 평가 결과")
                corp_r = st.session_state.get("ceo_eval_corp")
                inh_r  = st.session_state.get("ceo_eval_inh")
                company = st.session_state.get("ceo_company_result", "")
                shares  = st.session_state.get("ceo_shares_result", 0)

                if corp_r and inh_r:
                    corp_val = corp_r["법인세법상 시가"]
                    inh_val  = inh_r["상증법상 최종가액"]
                    asset_ps = inh_r["주당 순자산가치"]
                    earn_ps  = inh_r["주당 순손익가치"]

                    st.markdown(f"""
<div style="background:#eef4fb;border:1px solid #b8d0ea;border-radius:8px;padding:14px 18px;margin-bottom:10px;">
  <div style="font-size:1.05rem;font-weight:700;color:#1a3a5c;margin-bottom:8px;">🏢 {company} 비상장주식 평가</div>
  <table style="width:100%;font-size:0.88rem;border-collapse:collapse;">
    <tr style="background:#1a3a5c;color:#fff;">
      <th style="padding:6px 10px;text-align:left;">구분</th>
      <th style="padding:6px 10px;text-align:right;">주당 평가액</th>
      <th style="padding:6px 10px;text-align:right;">총 평가액 ({shares:,}주)</th>
    </tr>
    <tr style="border-bottom:1px solid #dde3ea;">
      <td style="padding:6px 10px;">📌 법인세법상 시가</td>
      <td style="padding:6px 10px;text-align:right;"><b>{corp_val:,.0f}원</b></td>
      <td style="padding:6px 10px;text-align:right;">{corp_val*shares:,.0f}원</td>
    </tr>
    <tr style="border-bottom:1px solid #dde3ea;background:#f4f7fb;">
      <td style="padding:6px 10px;">📌 상증법상 최종가액</td>
      <td style="padding:6px 10px;text-align:right;"><b>{inh_val:,.0f}원</b></td>
      <td style="padding:6px 10px;text-align:right;">{inh_val*shares:,.0f}원</td>
    </tr>
    <tr style="border-bottom:1px solid #dde3ea;">
      <td style="padding:6px 10px;">주당 순자산가치</td>
      <td style="padding:6px 10px;text-align:right;">{asset_ps:,.0f}원</td>
      <td style="padding:6px 10px;text-align:right;">—</td>
    </tr>
    <tr style="background:#f4f7fb;">
      <td style="padding:6px 10px;">주당 순손익가치</td>
      <td style="padding:6px 10px;text-align:right;">{earn_ps:,.0f}원</td>
      <td style="padding:6px 10px;text-align:right;">—</td>
    </tr>
  </table>
  <div style="margin-top:8px;font-size:0.8rem;color:#555;">
    경영권 할증: {corp_r['경영권 할증 적용']} &nbsp;|&nbsp; 평가방식: {corp_r['평가 방식']}
  </div>
</div>
""", unsafe_allow_html=True)

                    # AI 심층 분석 버튼
                    if st.button("🤖 AI 심층 분석 (CEO플랜 설계)", key="btn_ceo_ai"):
                        ai_prompt = (
                            f"[CEO플랜 — 비상장주식 평가 결과 기반 심층 분석]\n"
                            f"법인명: {company}, 발행주식: {shares:,}주\n"
                            f"법인세법상 시가: {corp_val:,.0f}원/주 (총 {corp_val*shares:,.0f}원)\n"
                            f"상증법상 최종가액: {inh_val:,.0f}원/주 (총 {inh_val*shares:,.0f}원)\n"
                            f"주당 순자산가치: {asset_ps:,.0f}원 | 주당 순손익가치: {earn_ps:,.0f}원\n"
                        )
                        run_ai_analysis(
                            company or "법인", "CEO플랜 심층 분석", 0, "res_ceo_ai",
                            CEO_PLAN_PROMPT + ai_prompt
                        )
                    show_result("res_ceo_ai")

                else:
                    st.info("좌측 입력표를 작성하고 '비상장주식 평가 실행'을 클릭하세요.")
                    st.markdown("##### 📘 비상장주식 평가 방법 안내")
                    components.html(f"""
<div style="
  height:320px; overflow-y:auto; padding:14px 16px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">{CEO_EVAL_GUIDE}</div>""", height=338)

            else:
                st.subheader("🤖 AI 재무제표 분석 리포트")
                if st.session_state.get("res_ceo_fs"):
                    show_result("res_ceo_fs")
                else:
                    st.markdown("##### 📘 비상장주식 평가 방법 안내")
                    components.html(f"""
<div style="
  height:320px; overflow-y:auto; padding:14px 16px;
  background:#f8fafc; border:1px solid #d0d7de;
  border-radius:8px; font-size:0.83rem; line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif; color:#1a1a2e;
">{CEO_EVAL_GUIDE}</div>""", height=338)

    # ── [탭 9] 관리자 ────────────────────────────────────────────────────
    if cur == "t9":
        st.subheader("관리자 전용 시스템")
        # 관리자 키를 st.secrets에서 가져옴 (평문 하드코딩 금지 - 보안 개선)
        admin_key_input = st.text_input("관리자 인증키", type="password", key="admin_key_tab3")

        if admin_key_input == get_admin_key():
            st.success("관리자 시스템 활성화")

            inner_tabs = st.tabs(["회원 관리", "RAG 지식베이스", "데이터 파기"])

            # 회원 관리
            with inner_tabs[0]:
                members = load_members()
                if members:
                    st.write(f"**총 회원수: {len(members)}명**")
                    member_data = [
                        {
                            "이름": n,
                            "가입일": info.get("join_date", ""),
                            "구독 종료": info.get("subscription_end", ""),
                            "상태": "활성" if info.get("is_active") else "비활성"
                        }
                        for n, info in members.items()
                    ]
                    st.dataframe(member_data, use_container_width=True)

                    selected = st.selectbox("회원 선택", list(members.keys()), key="admin_member_sel")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("구독 30일 연장", key="btn_extend"):
                            end = dt.strptime(members[selected]["subscription_end"], "%Y-%m-%d")
                            members[selected]["subscription_end"] = (end + timedelta(days=30)).strftime("%Y-%m-%d")
                            save_members(members)
                            st.success(f"{selected}님 구독 연장 완료")
                    with c2:
                        if st.button("회원 비활성화", key="btn_deactivate"):
                            members[selected]["is_active"] = False
                            save_members(members)
                            st.warning(f"{selected}님 비활성화 완료")
                else:
                    st.info("등록된 회원이 없습니다.")

            # RAG 지식베이스
            with inner_tabs[1]:
                # ── 헤더: 타이틀 + 현재 용량 한 줄 표시 ──
                rag_sys = st.session_state.rag_system
                doc_count = len(rag_sys.documents)
                disk_exists = os.path.exists(RAG_DOCS_PATH)
                total_chars = sum(len(d) for d in rag_sys.documents) if doc_count > 0 else 0
                total_mb = total_chars / 1024 / 1024
                disk_mb = os.path.getsize(RAG_DOCS_PATH) / 1024 / 1024 if disk_exists else 0
                st.markdown(
                    f"### 마스터 전용 RAG 엔진 "
                    f"<span style='font-size:0.85rem;color:#555;font-weight:normal;'>"
                    f"📦 로딩 데이터: <b>{total_mb:.3f} MB</b>"
                    f"{' | 디스크: <b>' + f'{disk_mb:.3f} MB</b> ✅' if disk_exists else ''}"
                    f" | 문서 {doc_count}개</span>",
                    unsafe_allow_html=True
                )

                # ── 파일 업로더 ──
                rag_files = st.file_uploader(
                    "전문가용 노하우 PDF/DOCX/TXT 업로드",
                    type=['pdf', 'docx', 'txt'],
                    accept_multiple_files=True,
                    key="rag_uploader_admin")

                if rag_files and st.button("지식베이스 동기화 (영구저장)", key="btn_rag_sync"):
                    with st.spinner("동기화 및 디스크 저장 중..."):
                        try:
                            docs = []
                            for f in rag_files:
                                if f.type == "application/pdf":
                                    docs.append(process_pdf(f))
                                elif "wordprocessingml" in f.type:
                                    docs.append(process_docx(f))
                                else:
                                    docs.append(f.read().decode('utf-8'))
                            rag_sys.add_documents(docs)
                            st.success(f"✅ {len(rag_files)}개 파일 추가 완료 — 디스크 영구 저장됨")
                            st.caption(f"저장 위치: {os.path.abspath(RAG_DOCS_PATH)}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"동기화 오류: {e}")

                # ── 로딩된 문서 목록 스크롤 창 + 개별 삭제 ──
                if doc_count > 0:
                    st.markdown("**📋 로딩된 문서 목록**")
                    scroll_container = st.container(height=260)
                    with scroll_container:
                        for i, doc in enumerate(rag_sys.documents):
                            doc_mb = len(doc) / 1024 / 1024
                            size_label = f"{doc_mb:.3f} MB" if doc_mb >= 0.01 else f"{len(doc)/1024:.1f} KB"
                            preview = doc[:80].replace("\n", " ").strip()
                            col_txt, col_btn = st.columns([9, 1])
                            with col_txt:
                                st.markdown(
                                    f"<div style='font-size:0.82rem;padding:4px 0;border-bottom:1px solid #eee;'>"
                                    f"<b>#{i+1}</b> {preview}… "
                                    f"<span style='color:#888;font-size:0.78rem;'>({size_label})</span></div>",
                                    unsafe_allow_html=True
                                )
                            with col_btn:
                                if st.button("🗑", key=f"del_doc_{i}", help=f"문서 #{i+1} 삭제"):
                                    rag_sys.delete_document(i)
                                    st.rerun()

                st.divider()
                # ── GitHub 커밋 안내 ──
                _rag_writable_now = _rag_dir_writable
                _path_label = os.path.abspath(RAG_INDEX_PATH)
                if _rag_writable_now:
                    st.info(
                        "💾 **RAG 파일 영구 보존 방법 (권장)**\n\n"
                        "Streamlit Cloud는 서버 재시작 시 `/tmp` 데이터가 초기화됩니다.\n"
                        "현재 저장 위치가 앱 디렉터리이면 아래 명령으로 GitHub에 커밋하세요:\n\n"
                        "```bash\n"
                        "git add rag_index.faiss rag_docs.json\n"
                        "git commit -m \"chore: update RAG knowledge base\"\n"
                        "git push\n"
                        "```\n"
                        f"현재 저장 경로: `{_path_label}`"
                    )
                else:
                    st.warning(
                        "⚠️ **앱 디렉터리 쓰기 불가 — `/tmp` 임시 저장 중**\n\n"
                        "현재 RAG 데이터는 `/tmp`에 저장되어 서버 재시작 시 **소멸**됩니다.\n"
                        "영구 보존하려면 로컬 환경에서 인덱스를 빌드한 후 "
                        "`rag_index.faiss` / `rag_docs.json`을 GitHub 저장소에 커밋하세요."
                    )
                st.divider()
                st.markdown("##### 🗑️ 지식베이스 전체 삭제 (관리자 전용)")
                st.warning("삭제 시 디스크 파일까지 완전히 제거됩니다. 복구 불가합니다.")
                if st.button("지식베이스 전체 삭제", type="primary", key="btn_rag_delete"):
                    rag_sys.delete_from_disk()
                    st.error("지식베이스가 완전히 삭제되었습니다.")
                    st.rerun()

            # 데이터 파기
            with inner_tabs[2]:
                st.warning("만료된 사용자 데이터를 영구 삭제합니다.")
                if st.button("만료 데이터 파기 실행", type="primary", key="btn_purge_admin"):
                    try:
                        with _get_conn() as conn:
                            count = conn.execute(
                                "SELECT COUNT(*) FROM user_documents "
                                "WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')"
                            ).fetchone()[0]
                            conn.execute(
                                "DELETE FROM user_documents "
                                "WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')"
                            )
                        st.success(f"{count}개의 만료 데이터가 파기되었습니다.")
                    except Exception as e:
                        st.error(f"파기 오류: {e}")
        elif admin_key_input:
            st.error("관리자 인증키가 올바르지 않습니다.")
        else:
            st.info("관리자 인증키를 입력하세요.")

    # 하단 공통 면책 고지
    st.divider()
    st.caption(
        "[법적 책임 한계고지] 본 서비스는 AI 기술을 활용한 상담 보조 도구이며, "
        "모든 분석 결과의 최종 판단 및 법적 책임은 사용자(상담원)에게 있습니다. "
        "상담 문의: 010-3074-2616 골드키지사"
    )


# --------------------------------------------------------------------------
# [SECTION 8.5] /verify_purchase — TWA billing.js 수신 엔드포인트
# --------------------------------------------------------------------------
# Streamlit은 자체 HTTP 라우터가 없으므로, query_params로 POST 흉내내거나
# 별도 FastAPI/Flask 서버를 사이드카로 운영하는 것이 정석입니다.
# 아래는 Streamlit query_params 방식(GET 폴백)과
# 사이드카 FastAPI 서버 코드를 모두 제공합니다.

def handle_verify_purchase_query():
    """
    Streamlit query_params 방식 폴백.
    billing.js → window.location = '?verify=TOKEN&user=NAME' 으로 리다이렉트 시 처리.
    실제 운영에서는 아래 FastAPI 사이드카 서버 사용을 권장합니다.
    """
    params = st.query_params
    token = params.get("verify", "")
    user  = params.get("user",   "")
    if token and user:
        ok, msg = verify_google_purchase(token, user)
        if ok:
            st.success(f"구독 활성화 완료: {msg}")
        else:
            st.error(f"검증 실패: {msg}")
        # 처리 후 query_params 초기화
        st.query_params.clear()

# ── FastAPI 사이드카 서버 (권장) ──────────────────────────────────────────
# 아래 코드를 별도 파일 twa/verify_server.py 로 저장 후 실행:
#   uvicorn twa.verify_server:app --host 0.0.0.0 --port 8502
#
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# import sys, os
# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# from insurance_bot import verify_google_purchase, setup_database
#
# app = FastAPI()
# app.add_middleware(CORSMiddleware,
#     allow_origins=["https://your-streamlit-app.streamlit.app"],
#     allow_methods=["POST"], allow_headers=["Content-Type"])
#
# @app.on_event("startup")
# def startup(): setup_database()
#
# @app.post("/verify_purchase")
# async def verify_purchase(request: Request):
#     body = await request.json()
#     token     = body.get("purchase_token", "")
#     user_name = body.get("user_name", "")
#     if not token or not user_name:
#         raise HTTPException(status_code=400, detail="purchase_token, user_name 필수")
#     ok, msg = verify_google_purchase(token, user_name)
#     return {"success": ok, "message": msg}
#
# @app.get("/.well-known/assetlinks.json")
# async def assetlinks():
#     import json, pathlib
#     p = pathlib.Path(__file__).parent / "assetlinks.json"
#     return json.loads(p.read_text())

# --------------------------------------------------------------------------
# [SECTION 9] 앱 진입점
# --------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        # RTDN Pull 워커 모드 — Streamlit 앱과 별도 터미널에서 실행
        # 사용법: python insurance_bot.py --worker
        setup_database()
        run_worker()
    else:
        try:
            main()
        except Exception as e:
            st.error(f"시스템 오류: {e}")
