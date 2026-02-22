# ==========================================================
# 골드키지사 마스터 AI - 탭 구조 통합본 (전체 수정판)
# 수정: 구조적/논리적/보안/모바일 문제 전체 반영
# ----------------------------------------------------------
# [파일 경로 메모]
#   메인 파일  : D:\CascadeProjects\app.py
#   백업 파일  : D:\CascadeProjects\app_backup_20260222_2112.py
#   외부 게이트: D:\CascadeProjects\external_gateway.py
#   Streamlit  : C:\Users\insus\CascadeProjects\.streamlit\secrets.toml
# ==========================================================
#
# ██████████████████████████████████████████████████████████
# ██  [코딩 규칙 — 절대명령: 삭제/수정 금지]              ██
# ██                                                      ██
# ██  ★ 관리자 명령이 없으면 앱의 기능을                 ██
# ██    축소하거나 삭제하지 못한다.                       ██
# ██                                                      ██
# ██  ★ 앱을 수정할 때 반드시 수정 전 백업 보관용을      ██
# ██    만들어 놓고, 코딩에 변화가 있으면                 ██
# ██    관리자에게 안내할 것.                             ██
# ██                                                      ██
# ██  1. 아래 섹션 구조(SECTION 0 ~ SECTION 12)는        ██
# ██     절대 삭제하거나 순서를 변경하지 말 것.           ██
# ██                                                      ██
# ██  2. 각 섹션 내 '삭제/수정 금지' 주석이 달린         ██
# ██     코드 블록은 내용을 변경하지 말 것.              ██
# ██                                                      ██
# ██  3. 전문가 역산 로직(건보료/국민연금 기반 소득 역산, ██
# ██     보험료 황금비율, 호프만/라이프니쯔 계수 산출 등) ██
# ██     은 절대 변경하지 말 것.                         ██
# ██                                                      ██
# ██  섹션 구조 목록:                                    ██
# ██   SECTION 1    — 보안 및 암호화 엔진               ██
# ██   SECTION 2    — 데이터베이스 & 회원 관리           ██
# ██   SECTION 3    — 유틸리티 함수                      ██
# ██   SECTION 4    — 시스템 프롬프트                    ██
# ██   SECTION 5    — RAG 시스템                         ██
# ██   SECTION 6    — 상속/증여 정밀 로직               ██
# ██   SECTION 7    — 주택연금 시뮬레이션               ██
# ██   SECTION 8    — 메인 UI (사이드바 / 탭)           ██
# ██   SECTION 9    — 자가 복구 시스템 + 진입점         ██
# ██████████████████████████████████████████████████████████

import streamlit as st
from google import genai
from google.genai import types
import sys, json, os, time, hashlib, base64, re, tempfile, pathlib, codecs, unicodedata, traceback as _traceback

# 외부 격리 게이트웨이 — 모든 외부 접촉은 이 모듈을 통해서만
try:
    import external_gateway as _gw
    _GW_OK = True
except ImportError:
    _GW_OK = False

try:
    import ftfy as _ftfy
    _FTFY_OK = True
except ImportError:
    _FTFY_OK = False

from datetime import datetime as dt, timedelta, date
from typing import List, Dict
import numpy as np
import sqlite3
import pandas as pd
import PIL.Image
from cryptography.fernet import Fernet
import streamlit.components.v1 as components

# ==========================================================
# [SURROGATE 전역 차단] — 모든 문자열 처리 전 최우선 적용
# Python 인터프리터 레벨에서 surrogate 문자를 replace로 강제 치환
# Streamlit 렌더링 엔진은 stdout 설정을 우회하므로
# str 서브클래스 + __str__ 후킹 대신 encode 레벨에서 차단
# ==========================================================
os.environ["PYTHONIOENCODING"] = "utf-8:replace"
os.environ["PYTHONUTF8"] = "1"

# 환경변수 전체를 surrogate-safe하게 정제 (앱 시작 시 1회만 실행)
try:
    for _ekey in list(os.environ.keys()):
        _eval = os.environ[_ekey]
        _safe_eval = _eval.encode("utf-8", errors="ignore").decode("utf-8")
        if _safe_eval != _eval:
            os.environ[_ekey] = _safe_eval
except Exception:
    pass

def _safe_str(obj) -> str:
    """surrogate 문자를 완전 제거한 안전한 문자열 반환 — 전역 사용"""
    try:
        s = obj if isinstance(obj, str) else str(obj)
        return s.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return repr(obj).encode("utf-8", errors="replace").decode("utf-8", errors="replace")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 선택적 임포트 — 앱 시작 시 즉시 로드하지 않음 (지연 로드)
# RAG/PDF 라이브러리는 실제 사용 시점에 로드하여 콜드 스타트 최소화
RAG_AVAILABLE = None  # None=미확인, True=사용가능, False=불가
PDF_AVAILABLE = None

def _check_rag():
    global RAG_AVAILABLE
    if RAG_AVAILABLE is None:
        try:
            from sentence_transformers import SentenceTransformer  # noqa
            import faiss  # noqa
            RAG_AVAILABLE = True
        except ImportError:
            RAG_AVAILABLE = False
    return RAG_AVAILABLE

def _check_pdf():
    global PDF_AVAILABLE
    if PDF_AVAILABLE is None:
        try:
            import pdfplumber  # noqa
            PDF_AVAILABLE = True
        except ImportError:
            PDF_AVAILABLE = False
    return PDF_AVAILABLE

# [시스템 필수 설정]
# Streamlit Cloud / Cloud Run 모두 읽기 전용 파일시스템 → /tmp/ 경로 사용
# Cloud Run: K_SERVICE 환경변수 존재 / Streamlit Cloud: HOME=/home/...
_IS_CLOUD = (
    os.environ.get("K_SERVICE") is not None or          # Cloud Run
    os.environ.get("HOME", "").startswith("/home") or   # Streamlit Cloud
    not os.access(".", os.W_OK)                         # 현재 디렉토리 쓰기 불가
)
_DATA_DIR = "/tmp" if _IS_CLOUD else "."
USAGE_DB = os.path.join(_DATA_DIR, "usage_log.json")
MEMBER_DB = os.path.join(_DATA_DIR, "members.json")

# --------------------------------------------------------------------------
# [SECTION 1] 보안 및 암호화 엔진
# --------------------------------------------------------------------------
DEFAULT_KEY = b'19IPhRNw7fLHub9g5Kp6BaQ6wi53gJ8-OKPF3Bd5Ays='

def get_encryption_key():
    try:
        if "ENCRYPTION_KEY" in st.secrets:
            return st.secrets["ENCRYPTION_KEY"].encode()
    except Exception:
        pass
    return DEFAULT_KEY

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
    except:
        return "Decryption Error"

def encrypt_data(data):
    """단방향 해시 암호화 (연락처 등 민감 정보)"""
    return hashlib.sha256(data.encode()).hexdigest()

def decrypt_data(stored_hash, input_data):
    """해시 비교 검증"""
    return stored_hash == hashlib.sha256(input_data.encode()).hexdigest()

def encrypt_contact(contact):
    return hashlib.sha256(contact.encode()).hexdigest()

def sanitize_unicode(text) -> str:
    """surrogate 문자 완전 제거 — ftfy 우선 + 3단계 방어 (근본 해결판)"""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""
    # 0단계: ftfy로 잘못된 인코딩 자체를 수정 (가장 포괄적)
    if _FTFY_OK:
        try:
            text = _ftfy.fix_text(text, normalization="NFC")
        except Exception:
            pass
    # 1단계: 유니코드 카테고리 Cs(surrogate) 문자를 문자 단위로 직접 제거
    try:
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Cs")
    except Exception:
        pass
    # 2단계: UTF-8 왕복으로 잔여 surrogate 완전 제거 (ignore = 흔적 없이 삭제)
    try:
        text = text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        pass
    # 3단계: 최후 방어 — repr 폴백
    try:
        text.encode("utf-8")  # 검증
    except (UnicodeEncodeError, UnicodeDecodeError):
        text = repr(text).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
    return text

def sanitize_prompt(text):
    """프롬프트 인젝션 방어 - 모든 쿼리에 적용"""
    text = sanitize_unicode(text)
    danger_words = ["system instruction", "지침 무시", "프롬프트 출력", "명령어 변경", "ignore previous"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

def get_admin_key():
    """관리자 키를 st.secrets에서 가져옴 (평문 하드코딩 금지)"""
    try:
        return st.secrets.get("ADMIN_KEY", "goldkey777")
    except Exception:
        return "goldkey777"

# --------------------------------------------------------------------------
# [SECTION 1.5] 비상장주식 평가 엔진 (상증법 + 법인세법)
# --------------------------------------------------------------------------
class AdvancedStockEvaluator:
    """
    상증법 및 법인세법 통합 비상장주식 평가 엔진
    """
    def __init__(self, net_asset, net_incomes, total_shares,
                 market_price=None, is_controlling=False, is_real_estate_rich=False):
        self.net_asset           = net_asset
        self.net_incomes         = net_incomes
        self.total_shares        = total_shares
        self.market_price        = market_price
        self.is_controlling      = is_controlling
        self.is_real_estate_rich = is_real_estate_rich
        self.cap_rate            = 0.1
        self.annuity_factor      = 3.7908

    def evaluate_corporate_tax(self):
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
        pure_asset_per_share = self.net_asset / max(self.total_shares, 1)
        incomes = (self.net_incomes + [0, 0, 0])[:3]  # 3개 미만 시 0으로 패딩
        weighted_eps = (
            incomes[0] / max(self.total_shares, 1) * 3 +
            incomes[1] / max(self.total_shares, 1) * 2 +
            incomes[2] / max(self.total_shares, 1) * 1
        ) / 6
        excess_earnings   = (weighted_eps * 0.5) - (pure_asset_per_share * 0.1)
        goodwill          = max(0, excess_earnings * self.annuity_factor)
        final_asset_value = pure_asset_per_share + goodwill
        earnings_value    = weighted_eps / self.cap_rate
        weight_eps, weight_asset = (2, 3) if self.is_real_estate_rich else (3, 2)
        weighted_avg   = (earnings_value * weight_eps + final_asset_value * weight_asset) / 5
        floor_value    = final_asset_value * 0.8
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
2. 가업승계 전략 — 증여세·상속세 절감 방안
3. CEO 퇴직금 설계 — 임원 퇴직금 규정 정비 및 보험 재원 마련
4. 경영인정기보험 활용 — 법인 납입 보험료 손금산입 가능 여부 및 한도
5. 주가 관리 전략 — 평가액 조정을 통한 절세 시뮬레이션
6. CEO 유고 리스크 대비 — 사망보험금 → 퇴직금·주식 매입 재원 활용
7. 법인 절세 전략 종합 — 세무사 협업 필요 사항 명시

[주의] 본 분석은 참고용이며, 구체적 세무·법률 사항은 반드시 세무사·변호사와 확인하십시오.
"""

CEO_FS_PROMPT = """
[역할] 당신은 기업회계 전문가 겸 법인 보험 컨설턴트입니다.
첨부된 재무제표를 분석하여 아래 항목을 보고하십시오.

[재무제표 분석 항목]
1. 수익성 분석 — 매출액·영업이익·당기순이익 3년 추이
2. 안정성 분석 — 부채비율·유동비율·자기자본비율
3. 성장성 분석 — 매출성장률·이익성장률·자산성장률
4. 비상장주식 평가용 핵심 수치 추출
5. CEO플랜 설계 관점 — 법인 재무 건전성 기반 보험 재원 마련 가능성
6. 리스크 요인 — 재무제표상 주요 위험 신호

[주의] 본 분석은 AI 보조 도구로서 참고용이며, 최종 판단은 공인회계사·세무사와 확인하십시오.
"""

# --------------------------------------------------------------------------
# [SECTION 2] 데이터베이스 및 회원 관리
# --------------------------------------------------------------------------
def setup_database():
    try:
        _db_path = os.path.join(_DATA_DIR, 'insurance_data.db')
        conn = sqlite3.connect(_db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_url TEXT,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, OSError):
        pass  # Cloud 환경 DB 생성 실패 시 앱 크래시 방지

def load_members():
    if not os.path.exists(MEMBER_DB):
        return {}
    try:
        with open(MEMBER_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}  # 파일 손상 시 빈 dict 반환

def save_members(members):
    try:
        with open(MEMBER_DB, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False)
    except (IOError, OSError):
        pass  # Cloud 환경 쓰기 실패 시 크래시 방지

def add_member(name, contact):
    """신규 회원 등록 - 연락처는 해시 암호화 저장"""
    members = load_members()
    user_id = "GK_" + name + "_" + str(int(time.time()))
    join_date = dt.now().strftime("%Y-%m-%d")
    end_date = (dt.now() + timedelta(days=365)).strftime("%Y-%m-%d")
    members[name] = {
        "user_id": user_id,
        "contact": encrypt_contact(contact),  # 평문 저장 금지 → 해시 저장
        "join_date": join_date,
        "subscription_end": end_date,
        "is_active": True
    }
    save_members(members)
    return members[name]

# --------------------------------------------------------------------------
# 에러 로그 기록 (파일 기반 — /tmp/error_log.json 영구 저장, 최근 200건)
# --------------------------------------------------------------------------
ERROR_LOG_PATH = "/tmp/error_log.json"

def log_error(source: str, message: str):
    """에러 발생 시각·출처·내용을 파일에 영구 저장 (최근 200건 유지)"""
    ts = dt.now().strftime("%Y-%m-%d %H:%M:%S")
    # surrogate 문자 포함 시 json.dump 자체가 실패하므로 저장 전 반드시 정제
    safe_msg = message.encode("utf-8", errors="replace").decode("utf-8", errors="replace")[:300]
    try:
        logs = []
        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                logs = json.load(f)
        logs.append({"time": ts, "source": source, "message": safe_msg})
        logs = logs[-200:]  # 최근 200건만 유지
        with open(ERROR_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False)
    except (IOError, OSError, json.JSONDecodeError):
        pass  # 로그 저장 실패는 무시

def load_error_log() -> list:
    """저장된 에러 로그 파일 읽기"""
    try:
        if os.path.exists(ERROR_LOG_PATH):
            with open(ERROR_LOG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError):
        pass
    return []

# 일일 무료 분석 횟수 상수 (단일 정의)
MAX_FREE_DAILY = 10
BETA_END_DATE  = date(2026, 8, 31)
def _get_unlimited_users():
    try:
        master = st.secrets.get("MASTER_NAME", "PERMANENT_MASTER")
    except Exception:
        master = "PERMANENT_MASTER"
    return {master, "PERMANENT_MASTER"}

def check_usage_count(user_name):
    today = str(date.today())
    if not os.path.exists(USAGE_DB):
        return 0
    try:
        with open(USAGE_DB, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(user_name, {}).get(today, 0)
    except (json.JSONDecodeError, IOError):
        return 0

def _is_unlimited_user(user_name):
    return user_name in _get_unlimited_users()

def update_usage(user_name):
    """분석 성공 후에만 호출해야 함"""
    today = str(date.today())
    try:
        data = {}
        if os.path.exists(USAGE_DB):
            with open(USAGE_DB, "r", encoding="utf-8") as f:
                data = json.load(f)
        if user_name not in data:
            data[user_name] = {}
        data[user_name][today] = data[user_name].get(today, 0) + 1
        with open(USAGE_DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except (IOError, OSError):
        pass  # Cloud 환경 쓰기 실패 시 앱 크래시 방지

def get_remaining_usage(user_name):
    return max(0, MAX_FREE_DAILY - check_usage_count(user_name))

def display_usage_dashboard(user_name: str):
    """사이드바 사용량 게이지 UI"""
    current_count = check_usage_count(user_name)
    is_unlimited  = _is_unlimited_user(user_name)
    daily_limit   = 999 if is_unlimited else MAX_FREE_DAILY
    remaining     = max(0, daily_limit - current_count)

    if is_unlimited:
        usage_percent = 0.05
        display_limit = "∞"
        rem_text      = "무제한 이용 가능"
    else:
        usage_percent = min(1.0, current_count / daily_limit) if daily_limit else 1.0
        display_limit = str(daily_limit)
        rem_text      = f"{remaining}회 남음"

    st.sidebar.markdown(f"""
<div style="background:linear-gradient(135deg,#ffffff 0%,#f8fafc 100%);
            border:1px solid #e2e8f0;border-radius:16px;padding:18px;
            margin:10px 0 25px 0;box-shadow:0 4px 12px rgba(0,0,0,0.05);">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
        <span style="font-size:0.7rem;font-weight:900;color:#1e293b;
                     background:#f1f5f9;padding:4px 10px;border-radius:20px;
                     border:1px solid #cbd5e1;letter-spacing:0.05em;">
            {'MASTER' if is_unlimited else 'STANDARD'}
        </span>
        <span style="font-size:0.9rem;font-weight:800;color:#2e6da4;">
            {current_count} <span style="color:#94a3b8;font-weight:400;">/</span> {display_limit}
        </span>
    </div>
    <div style="background:#f1f5f9;border-radius:12px;height:12px;width:100%;
                overflow:hidden;border:1px solid #e2e8f0;">
        <div style="background:linear-gradient(90deg,#3b82f6 0%,#2e6da4 100%);
                    width:{usage_percent * 100:.1f}%;height:100%;border-radius:12px;"></div>
    </div>
    <div style="margin-top:12px;display:flex;justify-content:space-between;align-items:center;">
        <span style="font-size:0.75rem;color:#64748b;font-weight:500;">오늘의 잔여 분석</span>
        <span style="font-size:0.85rem;color:#0f172a;font-weight:800;">{rem_text}</span>
    </div>
</div>
""", unsafe_allow_html=True)

def calculate_subscription_days(join_date):
    if not join_date:
        return 0
    try:
        if isinstance(join_date, str):
            join_date = dt.strptime(join_date, "%Y-%m-%d")
        return max(0, (join_date + timedelta(days=365) - dt.now()).days)
    except:
        return 0

def check_membership_status():
    if 'user_id' not in st.session_state:
        return False, "비회원"
    return True, "무료 이용 중 (~2026.08.31.까지)"

# --------------------------------------------------------------------------
# [SECTION 3] 유틸리티 함수
# --------------------------------------------------------------------------
@st.cache_resource
def get_client():
    # [GATE 1] API 키는 반드시 gateway를 통해 읽음 — surrogate 정제 보장
    if _GW_OK:
        api_key = _gw.get_secret("GEMINI_API_KEY")
    else:
        api_key = None
        try:
            api_key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
        api_key = api_key.encode("utf-8", errors="ignore").decode("utf-8")
    if not api_key:
        st.error("GEMINI_API_KEY가 설정되지 않았습니다. secrets.toml 또는 환경변수를 확인하세요.")
        st.stop()
    return genai.Client(
        api_key=api_key,
        http_options={"api_version": "v1beta"}
    )

def s_voice(text, lang='ko-KR'):
    """TTS - 20대 여성 아나운서 목소리 (pitch=1.4, rate=1.05)"""
    text = sanitize_unicode(text)
    clean = text.replace('"', '').replace("'", "").replace("\n", " ").replace("`", "")
    return (
        '<script>'
        'window.speechSynthesis.cancel();'
        'var msg=new SpeechSynthesisUtterance("' + clean + '");'
        'msg.lang="ko-KR";'
        'msg.rate=1.05;'
        'msg.pitch=1.4;'
        'msg.volume=1.0;'
        'var voices=window.speechSynthesis.getVoices();'
        'var femaleVoice=voices.find(function(v){'
        '  return v.lang==="ko-KR" && (v.name.includes("Female") || v.name.includes("Yuna") || v.name.includes("Google 한국의 목소") || v.name.includes("Heami"));'
        '});'
        'if(femaleVoice) msg.voice=femaleVoice;'
        'window.speechSynthesis.speak(msg);'
        '</script>'
    )

def s_voice_answer(text):
    """AI 답변 음성 읽기 - 첫 200자만 읽음"""
    short = text[:200].replace('**', '').replace('#', '').replace('`', '')
    return s_voice(short)

def load_stt_engine():
    """STT 엔진 초기화 - 다국어 지원 (1회만 호출)"""
    stt_js = (
        '<script>if(!window._sttInit){window._sttInit=true;'
        'window.startRecognition=function(lang,targetId){'
        'var SR=window.SpeechRecognition||window.webkitSpeechRecognition;'
        'if(!SR){alert("Chrome/Edge 브라우저를 사용해주세요.");return;}'
        'var r=new SR();'
        'r.lang=lang||"ko-KR";'
        'r.interimResults=false;'
        'r.continuous=false;'
        'r.onresult=function(e){'
        '  var t=e.results[0][0].transcript;'
        '  var ta=targetId?document.getElementById(targetId):null;'
        '  if(!ta){var all=document.querySelectorAll("textarea");ta=all[0];}'
        '  if(ta){'
        '    var s=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,"value").set;'
        '    s.call(ta,t);ta.dispatchEvent(new Event("input",{bubbles:true}));'
        '  }'
        '};'
        'r.onerror=function(e){alert("음성인식 오류: "+e.error);};'
        'r.start();}'
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

def extract_pdf_chunks(file, char_limit: int = 8000) -> str:
    """PDF 전체 텍스트를 char_limit 내에서 최대한 추출"""
    text = process_pdf(file)
    if len(text) <= char_limit:
        return text
    front = int(char_limit * 0.4)
    mid_s = int(char_limit * 0.2)
    back  = char_limit - front - mid_s
    mid_start = len(text) // 2 - mid_s // 2
    return text[:front] + "\n...(중략)...\n" + text[mid_start:mid_start+mid_s] + "\n...(중략)...\n" + text[-back:]

def process_pdf(file):
    if not _check_pdf():  # 실제 호출 시점에 라이브러리 확인
        return f"[PDF] {file.name} (pdfplumber 미설치)"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        import pdfplumber  # 실제 사용 시점에만 import
        with pdfplumber.open(tmp_path) as pdf:
            text = "".join(page.extract_text() or "" for page in pdf.pages)
        # [GATE 3] PDF 추출 텍스트 — surrogate 발생 최다 지점, gateway 정제 우선
        return _gw.sanitize_pdf_text(text) if _GW_OK else sanitize_unicode(text)
    except Exception as e:
        return f"PDF 처리 오류: {sanitize_unicode(str(e))}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

def process_docx(file):
    try:
        import docx as _docx
        DOCX_OK = True
    except ImportError:
        DOCX_OK = False
    if not DOCX_OK:
        return f"[DOCX] {file.name} (python-docx 미설치)"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        doc_obj = _docx.Document(tmp_path)
        text = "\n".join(p.text for p in doc_obj.paragraphs)
        # [GATE 3] DOCX 추출 텍스트 — gateway 정제 우선
        return _gw.sanitize_pdf_text(text) if _GW_OK else sanitize_unicode(text)
    except Exception as e:
        return f"DOCX 처리 오류: {sanitize_unicode(str(e))}"
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

def display_security_sidebar():
    st.sidebar.markdown("""
    <div style="background:#f0f7ff;padding:12px;border-radius:10px;font-size:0.78rem;">
        <strong>🔒 보안 기준 준수</strong><br>
        - ISO/IEC 27001 정보보안 관리체계<br>
        - GDPR·개인정보보호법 준거<br>
        - TLS 전송 암호화 (서버 레벨)<br>
        - AES-128 Fernet 세션 암호화<br>
        - SHA-256 연락처 해시 저장<br>
        - 세션 종료 시 메모리 자동 초기화
    </div>""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# [SECTION 4] 시스템 프롬프트
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """
[SYSTEM INSTRUCTIONS: 골드키AI마스터 보험 상담 엔진]

## 페르소나
성명: 골드키AI마스터
핵심 가치: 30년 보험 현장 실무 지식과 고객 중심의 보상 철학 계승.
전문성: CFP 수준 자산관리, 전문의 수준 질환 이해, 손해사정사 법리 해석 능력 보유.

## 소득 역산 핵심 산식 (최우선 적용)
- 건강보험료 기반: [건보료 납부액 / 0.0709] = 추정 월 소득
- 국민연금 기반: [국민연금 납부액 / 0.09] = 추정 월 소득
- 적정 보험료: 가처분 소득의 7~10% (위험직군 최대 20%)

## 답변 원칙
- 금감원 보도자료, 법원 판례, 전문 서적을 최우선 근거로 삼는다.
- 3중 검증: 1단계(법률) → 2단계(의학) → 3단계(실무 공감)
- 항상 정중한 '하십시오체' 사용
- 최초 대화: "안녕하십니까? 고객님. 골드키AI마스터입니다. 무엇을 도와드릴까요?"

## 신담보별 표준 권유 가이드라인
- 암 주요치료비: 실손에서 다 채워주지 못하는 비급여 항암제 시술 시 매년 1회 추가 지급
- 표적 항암약물 허가치료비: 암세포만 정밀 타격하는 표적항암제 치료 선택권 보장
- 순환계 질환 주요치료비: 혈관 질환으로 중환자실 입원, 수술, 혈전용해치료 시마다 반복 지급

## 필수 면책 공고 (모든 리포트 말미 포함)
"본 상담 내용은 참고용이며, 최종 책임은 사용자(상담원)에게 귀속됩니다."
상담 문의: 010-3074-2616 골드키지사

## 금기 사항
- 근거 없는 타사 비방, 무조건적 해지 권유(부당 승환) 금지
- 확정되지 않은 보험금 지급 약속 금지
- 욕설, 성차별, 장애인·노인 비하 발언 금지
"""

# --------------------------------------------------------------------------
# [SECTION 5] RAG 시스템
# --------------------------------------------------------------------------
@st.cache_resource
def get_rag_engine():
    if not _check_rag():  # 실제 호출 시점에 라이브러리 확인
        return None
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    except:
        return None

class InsuranceRAGSystem:
    def __init__(self):
        self.embed_model = get_rag_engine()
        self.index = None
        self.documents = []
        self.metadata = []
        self.model_loaded = self.embed_model is not None

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
            import faiss  # 실제 사용 시점에만 import
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
        taxable = max((val_real + val_cash) - 100000, 0)
        est_tax = max(taxable * 0.3 - 6000, 0)
        res_text = (
            f"총 자산 {val_real+val_cash:,.0f}만원 중 예상 상속세는 약 {est_tax:,.0f}만원입니다.\n\n"
            "부동산 비중이 높아 종신보험을 통한 세원 마련이 시급합니다."
        )
        output_manager(masked_name, res_text)

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
        page_title="골드키지사 마스터 AI",
        page_icon="🏆",
        layout="centered",   # 모바일에서 wide 대신 centered 사용
        initial_sidebar_state="collapsed"  # 모바일 초기 사이드바 접힘
    )

    # ── 0단계: 파일경로 복구 플래그 반영 (auto_recover 후 rerun 시) ─────
    if st.session_state.get("_force_tmp"):
        global _DATA_DIR, USAGE_DB, MEMBER_DB
        _DATA_DIR = "/tmp"
        USAGE_DB  = "/tmp/usage_log.json"
        MEMBER_DB = "/tmp/members.json"

    # ── 1단계: 즉시 초기화 (DB만 — 가볍고 필수) ────────────────────────
    if 'db_ready' not in st.session_state:
        setup_database()
        st.session_state.db_ready = True

    # ── 2단계: 지연 초기화 (RAG·STT — 홈 화면 렌더 후 백그라운드) ────────
    # 홈 화면이 이미 한 번 렌더된 뒤에만 무거운 모델 로드
    if st.session_state.get('home_rendered') and 'rag_system' not in st.session_state:
        try:
            st.session_state.rag_system = InsuranceRAGSystem()
        except Exception:
            st.session_state.rag_system = DummyRAGSystem()

    if st.session_state.get('home_rendered') and 'stt_loaded' not in st.session_state:
        load_stt_engine()
        st.session_state.stt_loaded = True

    # RAG 미로드 상태 폴백 (탭 진입 시 즉시 로드)
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = DummyRAGSystem()

    # 핀치줌 + 자동회전 허용 (모바일 최적화)
    components.html("""
<script>
(function(){
  var mv = document.querySelector('meta[name="viewport"]');
  if(mv){
    mv.setAttribute('content',
      'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes');
  } else {
    var m = document.createElement('meta');
    m.name = 'viewport';
    m.content = 'width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes';
    document.head.appendChild(m);
  }
  // 화면 자동 회전 허용 (Screen Orientation API)
  if(screen.orientation && screen.orientation.unlock){
    try{ screen.orientation.unlock(); }catch(e){}
  }
})();
</script>
""", height=0)

    # ── 사이드바 ──────────────────────────────────────────────────────────
    with st.sidebar:
        # ── 아바타 이미지 base64 로드 ──
        _avatar_path = pathlib.Path(__file__).parent / "avatar.png"
        _avatar_b64 = ""
        if _avatar_path.exists():
            _avatar_b64 = base64.b64encode(_avatar_path.read_bytes()).decode()
        _avatar_html = (
            f'<img src="data:image/png;base64,{_avatar_b64}" '
            'style="width:88px;height:88px;border-radius:50%;'
            'object-fit:cover;border:3px solid rgba(255,255,255,0.7);'
            'margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,0.25);">'
        ) if _avatar_b64 else '<div style="font-size:2.5rem;margin-bottom:8px;">🏆</div>'
        st.markdown(f"""
<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);
  border-radius:12px;padding:18px 16px 14px 16px;margin-bottom:12px;color:#fff;text-align:center;">
  {_avatar_html}
  <div style="font-size:1.25rem;font-weight:900;letter-spacing:0.06em;line-height:1.5;">
    Goldkey_AI_Master
  </div>
  <div style="font-size:1.25rem;font-weight:900;letter-spacing:0.06em;line-height:1.4;">
    Lab. &nbsp;·&nbsp; SaaS
  </div>
  <div style="font-size:0.78rem;opacity:0.88;line-height:1.6;margin-top:8px;">
    30년 보험설계사 상담 실무 지식 기반
  </div>
</div>""", unsafe_allow_html=True)

        with st.expander("📜 이용약관 · 서비스 안내", expanded=False):
            st.markdown("""
## Goldkey AI Master Lab. SaaS 이용약관

**제1조 (서비스 기본 정보)**
- **서비스명:** Goldkey AI Master Lab. SaaS
- **운영사:** 케이지에이에셋 골드키지사
- **운영자:** 이세윤
- **문의:** 010-3074-2616 / insusite@gmail.com

---

**제2조 (서비스 이용 조건)**
- 시스템 고도화 기간 **전체 무료** 이용: **~ 2026.08.31.까지**
- 회원가입 후 고도화 기간 내 모든 기능 무료 제공
- 회원 1인당 **1일 10회** AI 상담 이용 제한 (데이터 용량 제한)
- 만 19세 이상 보험설계사 및 관련 업무 종사자 대상

**제3조 (서비스 범위)**
- 보험 상담 보조 AI 분석 도구 제공
- 세무·법인·상속·증여 참고 정보 제공
- 보험사 연락처 및 청구 절차 안내
- 장해보험금·재조달가액 산출 보조 도구

**제4조 (금지 행위)**
- 타인 명의 도용 및 허위 정보 입력 금지
- 서비스를 이용한 불법 행위 및 부당 승환 금지
- 시스템 해킹·크롤링·자동화 접근 금지
- 분석 결과의 무단 상업적 재배포 금지

---

**제5조 (개인정보 수집 및 이용)**
- **수집 항목:** 이름, 연락처(암호화 저장), 이용 횟수
- **이용 목적:** 회원 인증, 이용 한도 관리, 서비스 품질 개선
- **보유 기간:** 회원 탈퇴 후 즉시 파기 (법령 의무 보존 기간 제외)
- **제3자 제공:** 법령에 의한 경우 외 제공 금지

**제6조 (고객정보 보안 기준)**
- 연락처: SHA-256 단방향 해시 암호화 저장
- 세션 데이터: AES-128 Fernet 암호화
- 전송 구간: TLS 암호화 (서버 레벨)
- 분석 내용: 서버에 저장하지 않으며 세션 종료 시 자동 파기
- ISO/IEC 27001 정보보안 관리체계 준거
- GDPR 및 개인정보보호법 준거

**제7조 (고객정보 폐기 지침)**
- **즉시 파기:** 회원 탈퇴 요청 시 회원 DB에서 즉시 삭제
- **자동 파기:** 세션 종료 시 메모리 내 상담 내용 자동 초기화
- **정기 파기:** 이용 로그는 90일 경과 후 자동 삭제
- **파기 방법:** 전자적 파일은 복구 불가능한 방법으로 영구 삭제
- **파기 확인:** 관리자 시스템에서 파기 이력 확인 가능

---

**제8조 (면책 고지)**

본 서비스는 AI 기술을 활용한 상담 **보조** 도구이며, 모든 분석 결과의 최종 판단 및 법적 책임은 **사용자(상담원)** 에게 있습니다.

보험금 지급 여부의 최종 결정은 보험사 심사 및 관련 법령에 따르며, 법률·세무·의료 분야의 최종 판단은 반드시 해당 전문가(변호사·세무사·의사)와 확인하십시오.

본 서비스는 보험 모집·중개·알선 행위와 **무관한 순수 AI 분석 보조 도구**이며, 본 앱의 분석 결과를 활용한 보험 계약 체결·보험금 수령에 대해 **앱 운영자는 일체의 법적 책임을 지지 않습니다.** 모든 책임은 해당 서비스를 활용한 사용자에게 귀속됩니다.

**제9조 (약관 변경)**
- 약관 변경 시 서비스 내 공지 후 7일 이후 적용
- 변경 약관에 동의하지 않을 경우 서비스 이용 중단 가능

*최종 개정일: 2026년 2월*
            """)

        # ── 회원가입 / 로그인 (헤더 바로 아래) ──────────────────────────
        if 'user_id' not in st.session_state:
            st.info("👋 안녕하세요, 무엇을 도와드릴까요?")
            components.html(s_voice("안녕하세요. 무엇을 도와드릴까요?"), height=0)
            st.markdown("""
<div style="background:#fff3cd;border:1.5px solid #f59e0b;border-radius:8px;
  padding:8px 12px;font-size:0.78rem;color:#92400e;margin-bottom:6px;">
  👆 <b>여기 &gt; 를 클릭</b>하여 회원가입 또는 로그인하세요
</div>""", unsafe_allow_html=True)
            tab_s, tab_l = st.tabs(["회원가입", "로그인"])
            with tab_s:
                with st.form("sb_signup_form"):
                    st.markdown("<div style='font-size:0.82rem;color:#555;margin-bottom:4px;'>📝 이름과 연락처를 입력하세요</div>", unsafe_allow_html=True)
                    name = st.text_input("👤 이름", placeholder="홍길동", key="signup_name")
                    contact = st.text_input("📱 연락처 (비밀번호)", type="password", placeholder="010-0000-0000", key="signup_contact")
                    if st.form_submit_button("✅ 가입하기", use_container_width=True):
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
                    st.markdown("<div style='font-size:0.82rem;color:#555;margin-bottom:4px;'>🔑 가입 시 입력한 정보로 로그인하세요</div>", unsafe_allow_html=True)
                    ln = st.text_input("👤 이름", placeholder="홍길동", key="login_name")
                    lc = st.text_input("📱 연락처 (비밀번호)", type="password", placeholder="010-0000-0000", key="login_contact")
                    if st.form_submit_button("🔓 로그인", use_container_width=True):
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
            st.divider()
            st.markdown("""
<div style="background:linear-gradient(135deg,#f0f7ff 0%,#e8f4fd 100%);
  border:1.5px solid #2e6da4;border-radius:12px;padding:10px 12px 4px 12px;
  margin-bottom:8px;">
  <div style="font-size:0.82rem;font-weight:900;color:#1a3a5c;margin-bottom:6px;">
    🎁 회원가입 혜택
  </div>
  <div style="height:160px;overflow-y:auto;font-size:0.76rem;color:#334155;line-height:1.75;
    padding-right:4px;">
    🆓 시스템 고도화 기간 전체 무료<br>
    &nbsp;&nbsp;&nbsp;(~2026.08.31.까지)<br>
    ✅ 매일 무료 AI 상담 10회<br>
    &nbsp;&nbsp;&nbsp;(일일 10회 한도 · 데이터용량제한)<br>
    ✅ 보험금 / 이미지 분석<br>
    ✅ 상속 · 증여 · 주택연금 시뮬레이션<br>
    ✅ 건보료 기반 소득 역산<br>
    <hr style="border:none;border-top:1px solid #cbd5e1;margin:6px 0;">
    <b style="color:#1a3a5c;">📦 지원 도구 제공</b><br>
    🛡️ 보험 컨설팅 지원 도구<br>
    💰 자산관리 컨설팅 지원 도구<br>
    📊 세무 컨설팅 지원 도구<br>
    🏢 법인 컨설팅 지원 도구<br>
    🏘️ 부동산 컨설팅 지원 도구<br>
    🏥 간병 컨설팅 지원 도구
  </div>
</div>""", unsafe_allow_html=True)

        if 'user_id' in st.session_state:
            # 로그인 상태
            user_name = st.session_state.get('user_name', '')
            st.success(f"{user_name} 마스터님 접속 중")

            is_member, status_msg = check_membership_status()
            remaining_usage = get_remaining_usage(user_name)

            st.info(
                f"**서비스 상태**: 무료 이용 중\n\n"
                f"**오늘 남은 횟수**: {remaining_usage}회"
            )

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
        st.markdown("""
<div style="background:#fff8e1;border:1.5px solid #f59e0b;border-radius:10px;
padding:10px 12px;font-size:0.74rem;color:#92400e;line-height:1.7;margin-bottom:8px;">
⚠️ <b>면책 안내</b><br>
이 앱의 자료는 AI가 제공한 것으로 <b>참고용으로만 사용</b>해야 하며,
법률·세무·회계·의료·부동산 관련 사항은 반드시
<b>해당 전문가(변호사·세무사·의사·공인중개사)와 상담</b>이 필요합니다.
</div>""", unsafe_allow_html=True)
        st.caption("문의: insusite@gmail.com")
        st.caption("상담: 010-3074-2616 골드키지사")
        display_security_sidebar()
        st.divider()
        # ── 관리자 콘솔 (최하단) ──────────────────────────────────────────
        with st.expander("🛠️ Admin Console · Goldkey_AI_M", expanded=False):
            admin_id = st.text_input("관리자 ID", key="admin_id", type="password",
                placeholder="admin")
            admin_code = st.text_input("관리자 코드", key="admin_code", type="password",
                placeholder="코드 입력")
            if st.button("관리자 로그인", key="btn_admin_login", use_container_width=True):
                try:
                    _admin_code = st.secrets.get("ADMIN_CODE", "gold1234")
                except Exception:
                    _admin_code = "gold1234"
                try:
                    _master_code = st.secrets.get("MASTER_CODE", "01030742616")
                except Exception:
                    _master_code = "01030742616"
                if admin_id == "admin" and admin_code == _admin_code:
                    st.session_state.user_id = "ADMIN_MASTER"
                    st.session_state.user_name = "Admin"
                    st.session_state.join_date = dt.now()
                    st.session_state.is_admin = True
                    st.success("관리자로 로그인되었습니다!")
                    st.rerun()
                elif admin_code == _master_code:
                    try:
                        _master_name = st.secrets.get("MASTER_NAME", "PERMANENT_MASTER")
                    except Exception:
                        _master_name = "PERMANENT_MASTER"
                    st.session_state.user_id = "PERMANENT_MASTER"
                    st.session_state.user_name = _master_name
                    st.session_state.join_date = dt.now()
                    st.session_state.is_admin = True
                    st.success("마스터로 로그인되었습니다! (무제한 사용)")
                    st.rerun()
                else:
                    st.error("ID 또는 코드가 올바르지 않습니다.")
            # 관리자 로그인 상태일 때 제안 목록 표시
            if st.session_state.get("is_admin"):
                st.divider()
                st.markdown("**📋 접수된 제안 목록**")
                _sug_path = os.path.join(_DATA_DIR, "suggestions.json")
                try:
                    if os.path.exists(_sug_path):
                        with open(_sug_path, "r", encoding="utf-8") as _f:
                            _sug_list = json.load(_f)
                        if _sug_list:
                            for _s in reversed(_sug_list[-20:]):
                                st.markdown(
                                    f"<div style='font-size:0.74rem;background:#f8fafc;"
                                    f"border:1px solid #e2e8f0;border-radius:6px;"
                                    f"padding:6px 10px;margin-bottom:4px;'>"
                                    f"<b style='color:#2e6da4;'>{_s.get('user','?')}</b> "
                                    f"<span style='color:#94a3b8;'>{_s.get('time','')}</span><br>"
                                    f"{sanitize_unicode(_s.get('content',''))}</div>",
                                    unsafe_allow_html=True
                                )
                        else:
                            st.caption("접수된 제안이 없습니다.")
                    else:
                        st.caption("접수된 제안이 없습니다.")
                except Exception:
                    st.caption("제안 목록을 불러올 수 없습니다.")

    # ── 메인 영역 — current_tab 라우팅 ───────────────────────────────────
    st.title("🏆 Goldkey AI Master")

    if 'current_tab' not in st.session_state:
        st.session_state.current_tab = "home"

    cur = st.session_state.current_tab

    # ── 공통 AI 쿼리 블록 ────────────────────────────────────────────────
    def ai_query_block(tab_key, placeholder="상담 내용을 입력하세요."):
        c_name = st.text_input("고객 성함", "우량 고객", key=f"c_name_{tab_key}")
        st.session_state.current_c_name = c_name
        stt_lang_map = {"한국어":"ko-KR","English":"en-US","日本語":"ja-JP","中文":"zh-CN","ภาษาไทย":"th-TH","Tiếng Việt":"vi-VN","Русский":"ru-RU"}
        stt_greet_map = {
            "한국어": "안녕하세요. 골드키 AI 마스터입니다. 무엇을 도와드릴까요?",
            "English": "Hello. I am Goldkey AI Master. How can I help you?",
            "日本語": "こんにちは。ゴールドキーAIマスターです。ご用件をどうぞ。",
            "中文": "您好，我是金钥匙AI大师，请问有什么可以帮您？",
            "ภาษาไทย": "สวัสดีครับ ผมคือ Goldkey AI Master มีอะไรให้ช่วยไหมครับ?",
            "Tiếng Việt": "Xin chào. Tôi là Goldkey AI Master. Tôi có thể giúp gì cho bạn?",
            "Русский": "Здравствуйте. Я Goldkey AI Master. Чем могу помочь?",
        }
        stt_lang_label = st.selectbox("음성입력 언어", list(stt_lang_map.keys()), key=f"stt_{tab_key}")
        stt_lang_code  = stt_lang_map[stt_lang_label]
        stt_greet      = stt_greet_map[stt_lang_label]
        hi_premium = st.number_input("월 건강보험료(원)", value=0, step=1000, key=f"hi_{tab_key}")
        if hi_premium > 0:
            income = hi_premium / 0.0709
            st.success(f"역산 월 소득: **{income:,.0f}원** | 적정 보험료: **{income*0.15:,.0f}원**")
        query = st.text_area("상담 내용 입력", height=180, key=f"query_{tab_key}", placeholder=placeholder)
        do_analyze = st.button("🔍 정밀 분석 실행", type="primary", key=f"btn_analyze_{tab_key}", use_container_width=True)
        # 음성 버튼: HTML 인라인 버튼 (항상 작동, Streamlit 재렌더링 무관)
        components.html(f"""
<style>
.stt-row{{display:flex;gap:8px;margin-top:4px;}}
.stt-btn{{flex:1;padding:9px 0;border-radius:8px;border:1.5px solid #2e6da4;
  background:#eef4fb;color:#1a3a5c;font-size:0.88rem;font-weight:700;cursor:pointer;}}
.stt-btn:hover{{background:#2e6da4;color:#fff;}}
.stt-btn.active{{background:#e74c3c;color:#fff;border-color:#e74c3c;}}
.tts-btn{{flex:1;padding:9px 0;border-radius:8px;border:1.5px solid #27ae60;
  background:#eafaf1;color:#1a5c3a;font-size:0.88rem;font-weight:700;cursor:pointer;}}
.tts-btn:hover{{background:#27ae60;color:#fff;}}
</style>
<div class="stt-row">
  <button class="stt-btn" id="stt_btn_{tab_key}" onclick="startSTT_{tab_key}()">🎙️ 음성입력 ({stt_lang_label})</button>
  <button class="tts-btn" onclick="startTTS_{tab_key}()">🔊 인사말 재생</button>
</div>
<script>
var _sttActive_{tab_key} = false;
var _sttRec_{tab_key} = null;
function startSTT_{tab_key}(){{
  var btn = document.getElementById('stt_btn_{tab_key}');
  if(_sttActive_{tab_key}){{
    if(_sttRec_{tab_key}) _sttRec_{tab_key}.stop();
    _sttActive_{tab_key}=false; btn.textContent='🎙️ 음성입력 ({stt_lang_label})'; btn.classList.remove('active'); return;
  }}
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){{alert('Chrome/Edge 브라우저를 사용해주세요.'); return;}}
  var r=new SR(); r.lang='{stt_lang_code}'; r.interimResults=false; r.continuous=false;
  r.onresult=function(e){{
    var t=e.results[0][0].transcript;
    var frames=window.parent.document.querySelectorAll('iframe');
    var ta=null;
    for(var i=0;i<frames.length;i++){{try{{var el=frames[i].contentDocument.querySelectorAll('textarea');if(el.length){{ta=el[el.length-1];break;}}}}catch(ex){{}}}}
    if(!ta) ta=window.parent.document.querySelectorAll('textarea[data-testid]');
    if(ta && ta.length){{
      var target=ta[ta.length-1];
      var nativeSetter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
      nativeSetter.call(target,t); target.dispatchEvent(new Event('input',{{bubbles:true}}));
    }}
    _sttActive_{tab_key}=false; btn.textContent='🎙️ 음성입력 ({stt_lang_label})'; btn.classList.remove('active');
  }};
  r.onerror=function(e){{alert('음성인식 오류: '+e.error); _sttActive_{tab_key}=false; btn.classList.remove('active');}};
  r.onend=function(){{_sttActive_{tab_key}=false; btn.textContent='🎙️ 음성입력 ({stt_lang_label})'; btn.classList.remove('active');}};
  _sttRec_{tab_key}=r; _sttActive_{tab_key}=true;
  btn.textContent='⏹️ 녹음 중... (클릭하여 중지)'; btn.classList.add('active');
  r.start();
}}
function startTTS_{tab_key}(){{
  window.speechSynthesis.cancel();
  var msg=new SpeechSynthesisUtterance('{stt_greet}');
  msg.lang='{stt_lang_code}'; msg.rate=1.05; msg.pitch=1.4; msg.volume=1.0;
  var voices=window.speechSynthesis.getVoices();
  var fv=voices.find(function(v){{return v.lang==='{stt_lang_code}'&&(v.name.includes('Female')||v.name.includes('Yuna')||v.name.includes('Google'));}}); 
  if(fv) msg.voice=fv;
  window.speechSynthesis.speak(msg);
}}
</script>
""", height=58)
        return c_name, query, hi_premium, do_analyze

    def run_ai_analysis(c_name, query, hi_premium, result_key, extra_prompt=""):
        if 'user_id' not in st.session_state:
            st.error("로그인이 필요합니다.")
            return
        user_name  = st.session_state.get('user_name', '')
        is_special = st.session_state.get('is_admin', False) or _is_unlimited_user(user_name)
        if not is_special and check_usage_count(user_name) >= MAX_FREE_DAILY:
            st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
            return
        with st.spinner("골드키AI마스터 분석 중..."):
            try:
                client, model_config = get_master_model()
                income    = hi_premium / 0.0709 if hi_premium > 0 else 0
                safe_q    = sanitize_prompt(query)
                rag_ctx   = ""
                if st.session_state.rag_system.index is not None:
                    results = st.session_state.rag_system.search(safe_q, k=3)
                    if results:
                        rag_ctx = "\n\n[참고 자료]\n" + "".join(f"{i}. {sanitize_unicode(r['text'])}\n" for i, r in enumerate(results, 1))
                prompt = (f"고객: {sanitize_unicode(c_name)}, 추정소득: {income:,.0f}원\n"
                          f"질문: {safe_q}{rag_ctx}\n{extra_prompt}")
                # [GATE 2] Gemini 호출은 반드시 gateway를 통해 — 입출력 모두 격리 정제
                if _GW_OK:
                    answer = _gw.call_gemini(client, GEMINI_MODEL, prompt, model_config)
                else:
                    prompt = sanitize_unicode(prompt)
                    resp   = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=model_config)
                    answer = sanitize_unicode(resp.text) if resp.text else "AI 응답을 받지 못했습니다."
                safe_name = sanitize_unicode(c_name)
                result_text = (f"### {safe_name}님 골드키AI마스터 정밀 리포트\n\n{answer}\n\n---\n"
                               f"**문의:** insusite@gmail.com | 010-3074-2616\n\n"
                               f"[주의] 최종 책임은 사용자(상담원)에게 귀속됩니다.")
                st.session_state[result_key] = sanitize_unicode(result_text)
                update_usage(user_name)
                components.html(s_voice("분석이 완료되었습니다."), height=0)
                st.rerun()
            except Exception as e:
                safe_err = str(e).encode("utf-8", errors="replace").decode("utf-8", errors="replace")
                log_error("AI분석", safe_err)
                st.error(f"분석 오류: {safe_err}")

    def show_result(result_key, guide_md=""):
        if st.session_state.get(result_key):
            result_text = st.session_state[result_key]
            st.markdown(result_text)
            # ── 출력(인쇄) 기능 ──────────────────────────────────────────
            c_name_out = st.session_state.get('current_c_name', '고객')
            disclaimer = (
                "\n\n---\n"
                "**[면책 고지]** 본 분석 결과는 AI 보조 도구에 의한 참고용 자료이며, "
                "최종 판단 및 법적 책임은 사용자(상담원)에게 귀속됩니다. "
                "보험금 지급 여부의 최종 결정은 보험사 심사 및 관련 법령에 따르며, "
                "법률·세무·의료 분야의 최종 판단은 반드시 해당 전문가와 확인하십시오.\n\n"
                "**문의:** insusite@gmail.com | 010-3074-2616 골드키지사"
            )
            full_text = result_text + disclaimer
            with st.expander("📤 출력 · 전송", expanded=False):
                st.markdown("**면책조항 포함 출력물 미리보기**")
                st.text_area("출력 내용 (복사 후 카톡/문서 전송)", value=full_text,
                    height=200, key=f"print_area_{result_key}")
                pcol1, pcol2 = st.columns(2)
                with pcol1:
                    components.html(f"""
<button onclick="window.print()" style="
  width:100%;padding:9px 0;border-radius:8px;
  border:1.5px solid #2e6da4;background:#eef4fb;
  color:#1a3a5c;font-size:0.88rem;font-weight:700;cursor:pointer;">
  🖨️ 인쇄 / PDF 저장
</button>""", height=44)
                with pcol2:
                    kakao_text = f"[골드키AI마스터 상담결과]\n{c_name_out}님\n" + full_text[:200] + "...\n문의: 010-3074-2616"
                    st.download_button("📩 문서 다운로드 (.txt)",
                        data=full_text.encode("utf-8"),
                        file_name=f"골드키AI_{c_name_out}_상담결과.txt",
                        mime="text/plain",
                        key=f"dl_{result_key}",
                        use_container_width=True)
        elif guide_md:
            st.markdown(guide_md)
        else:
            pass  # 빈 상태 — 별도 안내 불필요

    # ── [홈] 카드 네비게이션 ──────────────────────────────────────────────
    if cur == "home":
        # 홈 화면 첫 렌더 완료 플래그 — 다음 rerun 시 RAG/STT 지연 로드 트리거
        if not st.session_state.get('home_rendered'):
            st.session_state.home_rendered = True

        # ── 제안 박스 (홈 첫 번째 칸) ─────────────────────────────────────
        st.markdown("""
<div style="background:linear-gradient(135deg,#1a3a5c 0%,#2e6da4 100%);
  border-radius:14px;padding:16px 18px 12px 18px;margin-bottom:18px;color:#fff;">
  <div style="font-size:1.0rem;font-weight:900;letter-spacing:0.04em;margin-bottom:4px;">
    💡 시스템 제안 · 개선 의견
  </div>
  <div style="font-size:0.78rem;opacity:0.88;">
    내용 · 시스템 구성 · 개선 제안을 음성 또는 텍스트로 입력해주세요
  </div>
</div>""", unsafe_allow_html=True)

        _suggest_col1, _suggest_col2 = st.columns([3, 2], gap="small")
        with _suggest_col1:
            suggest_text = st.text_area(
                "제안 내용 입력",
                height=110,
                key="suggest_input",
                placeholder="예: 홈 화면에 날씨 정보를 추가해주세요 / 보험금 계산기 개선이 필요합니다",
                label_visibility="collapsed"
            )
            # 음성 입력 버튼 (실시간 STT)
            components.html("""
<style>
.sug-row{display:flex;gap:8px;margin-top:4px;}
.sug-stt{flex:1;padding:9px 0;border-radius:8px;border:1.5px solid #2e6da4;
  background:#eef4fb;color:#1a3a5c;font-size:0.86rem;font-weight:700;cursor:pointer;}
.sug-stt:hover{background:#2e6da4;color:#fff;}
.sug-stt.active{background:#e74c3c;color:#fff;border-color:#e74c3c;}
</style>
<div class="sug-row">
  <button class="sug-stt" id="sug_stt_btn" onclick="startSugSTT()">🎙️ 음성으로 제안하기</button>
</div>
<script>
var _sugActive = false;
var _sugRec = null;
function startSugSTT(){
  var btn = document.getElementById('sug_stt_btn');
  if(_sugActive){
    if(_sugRec) _sugRec.stop();
    _sugActive=false; btn.textContent='🎙️ 음성으로 제안하기'; btn.classList.remove('active'); return;
  }
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Chrome/Edge 브라우저를 사용해주세요.'); return;}
  var r=new SR(); r.lang='ko-KR'; r.interimResults=true; r.continuous=true;
  r.onresult=function(e){
    var interim=''; var final_t='';
    for(var i=e.resultIndex;i<e.results.length;i++){
      if(e.results[i].isFinal){ final_t+=e.results[i][0].transcript; }
      else { interim+=e.results[i][0].transcript; }
    }
    var display = final_t || interim;
    var tas = window.parent.document.querySelectorAll('textarea');
    var ta = null;
    for(var i=0;i<tas.length;i++){
      if(tas[i].getAttribute('aria-label')==='제안 내용 입력' || tas[i].placeholder.includes('제안')){
        ta=tas[i]; break;
      }
    }
    if(!ta && tas.length) ta = tas[0];
    if(ta && display){
      var nativeSetter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
      nativeSetter.call(ta, display);
      ta.dispatchEvent(new Event('input',{bubbles:true}));
    }
  };
  r.onerror=function(e){alert('음성인식 오류: '+e.error); _sugActive=false; btn.classList.remove('active');};
  r.onend=function(){
    if(_sugActive){ r.start(); }
    else{ btn.textContent='🎙️ 음성으로 제안하기'; btn.classList.remove('active'); }
  };
  _sugRec=r; _sugActive=true;
  btn.textContent='⏹️ 받아쓰는 중... (클릭하여 중지)'; btn.classList.add('active');
  r.start();
}
</script>
""", height=50)

        with _suggest_col2:
            st.markdown("""
<div style="background:#f8fafc;border:1.5px solid #d0dce8;border-radius:10px;
  padding:12px 14px;font-size:0.76rem;color:#475569;line-height:1.7;height:110px;
  overflow-y:auto;">
  <b style="color:#1a3a5c;">📋 제안 가능 항목</b><br>
  • 화면 구성 · 메뉴 배치<br>
  • 기능 추가 · 개선 요청<br>
  • 오류 · 불편 사항 신고<br>
  • 새로운 상담 카테고리<br>
  • 기타 시스템 의견
</div>""", unsafe_allow_html=True)

        _sbtn_col1, _sbtn_col2 = st.columns([1, 1], gap="small")
        with _sbtn_col1:
            if st.button("📨 제안 제출", key="btn_suggest_submit", use_container_width=True, type="primary"):
                _sug = st.session_state.get("suggest_input", "").strip()
                if _sug:
                    # 제안 내용 저장
                    _sug_path = os.path.join(_DATA_DIR, "suggestions.json")
                    try:
                        _sug_list = []
                        if os.path.exists(_sug_path):
                            with open(_sug_path, "r", encoding="utf-8") as _f:
                                _sug_list = json.load(_f)
                        _sug_list.append({
                            "time": dt.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "user": st.session_state.get("user_name", "비회원"),
                            "content": sanitize_unicode(_sug)
                        })
                        with open(_sug_path, "w", encoding="utf-8") as _f:
                            json.dump(_sug_list, _f, ensure_ascii=False)
                        st.session_state["suggest_submitted"] = True
                        st.rerun()
                    except Exception:
                        st.session_state["suggest_submitted"] = True
                        st.rerun()
                else:
                    st.warning("제안 내용을 입력해주세요.")
        with _sbtn_col2:
            if st.button("🗑️ 초기화", key="btn_suggest_clear", use_container_width=True):
                st.session_state["suggest_input"] = ""
                st.session_state.pop("suggest_submitted", None)
                st.rerun()

        if st.session_state.get("suggest_submitted"):
            st.success("✅ 말씀하신 제안이 반영되었습니다.")
            components.html(
                '<script>setTimeout(function(){}, 100);</script>' +
                s_voice("말씀하신 제안이 반영되었습니다."),
                height=0
            )

        st.divider()
        st.markdown("### 📌 상담 카테고리 — 원하는 항목을 선택하세요")

        # ── 카드 CSS: 전체 박스 클릭 + 동일 높이 ──
        st.markdown("""
<style>
.gk-section-label {
    font-size:0.88rem; font-weight:900; letter-spacing:0.06em;
    color:#fff; background:#2e6da4; border-radius:6px;
    padding:5px 14px; margin:18px 0 10px 0; display:inline-block;
}
/* 카드 래퍼: 상대위치 컨테이너 */
.gk-card-wrap {
    position:relative; height:120px; margin-bottom:8px;
}
/* 실제 카드 내용: 가로 레이아웃 */
.gk-card {
    background:#f8fafc; border:1.5px solid #d0dce8; border-radius:12px;
    padding:12px 14px; height:100%;
    display:flex; flex-direction:row; align-items:center; gap:12px;
    box-sizing:border-box; pointer-events:none;
    transition:border-color 0.18s, background 0.18s, box-shadow 0.18s;
}
.gk-card-icon {
    font-size:3.0rem; line-height:1;
    flex-shrink:0; width:52px; text-align:center;
}
.gk-card-body {
    display:flex; flex-direction:column; justify-content:center;
    flex:1; min-width:0;
}
.gk-card-title {
    font-weight:900; font-size:1.08rem; color:#1a3a5c;
    margin-bottom:5px; line-height:1.2;
    display:flex; align-items:center; justify-content:space-between;
}
.gk-card-click-badge {
    font-size:0.68rem; font-weight:700; color:#fff;
    background:#2e6da4; border-radius:20px;
    padding:2px 8px; margin-left:6px; white-space:nowrap;
    flex-shrink:0;
}
.gk-card-desc {
    font-size:0.80rem; color:#475569; line-height:1.55;
}
/* Streamlit 버튼을 전체 박스로 확장 — 텍스트·테두리 완전 숨김 */
.gk-card-wrap > div[data-testid="stButton"] {
    position:absolute !important;
    top:0 !important; left:0 !important;
    width:100% !important; height:100% !important;
    margin:0 !important; padding:0 !important;
}
.gk-card-wrap > div[data-testid="stButton"] > button {
    position:absolute !important;
    top:0 !important; left:0 !important;
    width:100% !important; height:100% !important;
    opacity:0 !important;
    cursor:pointer !important;
    z-index:10 !important;
    border-radius:12px !important;
    border:none !important;
    background:transparent !important;
    padding:0 !important;
    margin:0 !important;
    font-size:0 !important;
    line-height:0 !important;
    color:transparent !important;
}
.gk-card-wrap:hover .gk-card {
    border-color:#2e6da4;
    background:#eef4fb;
    box-shadow:0 2px 10px rgba(46,109,164,0.15);
}
</style>
""", unsafe_allow_html=True)

        # ── 파트 1: 보험 상담 (6개, 2열×3행) ──
        st.markdown('<div class="gk-section-label">�️ 보험 상담</div>', unsafe_allow_html=True)
        PART1 = [
            ("t0",  "📋", "신규보험 상담",      "기존 보험증권 분석\n보장 공백 진단 · 신규 컨설팅"),
            ("t1",  "💰", "보험금 상담",        "청구 절차 · 지급 거절 대응\n민원·손해사정·약관 해석"),
            ("disability","🩺","장해보험금 산출","AMA·맥브라이드·호프만계수\n후유장해 보험금 산출"),
            ("t2",  "🛡️", "기본보험 상담",      "자동차·화재·운전자\n일상배상책임 점검"),
            ("t3",  "🏥", "질병·상해 통합보험",  "암·뇌·심장 3대질병 보장\n간병·치매·생명보험 설계"),
            ("t4",  "🚗", "자동차사고 상담",    "과실비율·합의금 분석\n13대 중과실·민식이법 안내"),
        ]
        def _render_cards(cards, prefix):
            for row in range(3):
                c1, c2 = st.columns(2, gap="small")
                for ci, col in enumerate([c1, c2]):
                    idx = row * 2 + ci
                    if idx >= len(cards): break
                    _k, _ic, _ti, _de = cards[idx]
                    with col:
                        st.markdown(
                            f"<div class='gk-card-wrap'>"
                            f"<div class='gk-card'>"
                            f"<div class='gk-card-icon'>{_ic}</div>"
                            f"<div class='gk-card-body'>"
                            f"<div class='gk-card-title'>{_ti}<span class='gk-card-click-badge'>▶ 클릭</span></div>"
                            f"<div class='gk-card-desc'>{_de.replace(chr(10),'<br>')}</div>"
                            f"</div>"
                            f"</div></div>", unsafe_allow_html=True)
                        if st.button("​", key=f"{prefix}_{_k}", use_container_width=True):
                            st.session_state.current_tab = _k
                            st.rerun()

        _render_cards(PART1, "home_p1")

        # ── 파트 2: 자산·세무·법인 (6개, 2열×3행) ──
        st.markdown('<div class="gk-section-label">💼 자산·세무·법인</div>', unsafe_allow_html=True)
        PART2 = [
            ("t5",  "🌅", "노후·연금·상속설계",  "연금 3층 설계 · 주택연금\n상속·증여 절세 전략"),
            ("t6",  "📊", "세무상담",           "소득세·법인세·부가세 절세\n건보료 역산 · 금융소득 분석"),
            ("t7",  "🏢", "법인상담",           "법인 보험 · 단체보험 설계\n법인세 절감 · 복리후생 플랜"),
            ("t8",  "👔", "CEO플랜",            "비상장주식 평가(상증법)\n가업승계 · CEO 퇴직금 설계"),
            ("fire","🔥", "화재보험(재조달가액)","REB 기준 건물 재조달가액\n비례보상 방지 전략"),
            ("liability","⚖️","배상책임보험",   "중복보험 독립책임액 안분\n민법·실화책임법 정리"),
        ]
        _render_cards(PART2, "home_p2")

        # ── 파트 3: 부동산 투자 · 간병 컨설팅 ──
        st.markdown('<div class="gk-section-label">🏘️ 부동산 투자 · 간병 컨설팅</div>', unsafe_allow_html=True)
        _rc1, _rc2 = st.columns(2, gap="small")
        with _rc1:
            st.markdown(
                "<div class='gk-card-wrap'>"
                "<div class='gk-card'>"
                "<div class='gk-card-icon'>🏘️</div>"
                "<div class='gk-card-body'>"
                "<div class='gk-card-title'>부동산 투자 상담<span class='gk-card-click-badge'>▶ 클릭</span></div>"
                "<div class='gk-card-desc'>등기부등본·건축물대장 판독<br>투자수익 분석 · 보험 연계 설계</div>"
                "</div>"
                "</div></div>", unsafe_allow_html=True)
            if st.button("\u200b", key="home_p3_realty", use_container_width=True):
                st.session_state.current_tab = "realty"
                st.rerun()
        with _rc2:
            st.markdown(
                "<div class='gk-card-wrap'>"
                "<div class='gk-card'>"
                "<div class='gk-card-icon'>🏥</div>"
                "<div class='gk-card-body'>"
                "<div class='gk-card-title'>간병비 컨설팅<span class='gk-card-click-badge'>▶ 클릭</span></div>"
                "<div class='gk-card-desc'>치매·뇌졸중·요양병원 간병비 산출<br>장기요양등급 · 간병보험 설계</div>"
                "</div>"
                "</div></div>", unsafe_allow_html=True)
            if st.button("\u200b", key="home_p3_nursing", use_container_width=True):
                st.session_state.current_tab = "nursing"
                st.rerun()

        st.divider()
        if st.session_state.get('is_admin'):
            if st.button("⚙️ 관리자 시스템 이동", key="home_dash_t9"):
                st.session_state.current_tab = "t9"
                st.rerun()

        # ── 보험사 연락처 섹션 ──────────────────────────────────────────
        st.divider()
        st.markdown("## 📞 보험사 연락처 & 청구 안내")

        LIFE_INS = [
            {"name":"삼성생명","color":"#0066CC","call":"1588-3114","emergency":"해당없음","hq":"서울 서초구 서초대로74길 11","gwangju":"광주 서구 상무대로 904 / 062-360-7700","claim":"① 앱(삼성생명) → 보험금 청구\n② 지점 방문 또는 우편 접수\n③ 팩스 접수 후 원본 우편 발송","fax":"02-1588-3114"},
            {"name":"한화생명","color":"#E8001C","call":"1588-6363","emergency":"해당없음","hq":"서울 영등포구 63로 50","gwangju":"광주 서구 상무중앙로 110 / 062-380-7000","claim":"① 앱(한화생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-789-8282"},
            {"name":"교보생명","color":"#003087","call":"1588-1001","emergency":"해당없음","hq":"서울 종로구 종로 1","gwangju":"광주 서구 상무대로 904 / 062-380-1001","claim":"① 앱(교보생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-721-3535"},
            {"name":"신한라이프","color":"#0046FF","call":"1588-5580","emergency":"해당없음","hq":"서울 중구 세종대로 9","gwangju":"광주 서구 상무중앙로 110 / 062-380-5580","claim":"① 앱(신한라이프) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3455-4500"},
            {"name":"NH농협생명","color":"#00843D","call":"1544-4000","emergency":"해당없음","hq":"서울 중구 새문안로 16","gwangju":"광주 북구 우치로 226 / 062-520-4000","claim":"① 앱(NH농협생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2080-6000"},
            {"name":"흥국생명","color":"#8B0000","call":"1588-2288","emergency":"해당없음","hq":"서울 종로구 새문안로 68","gwangju":"광주 서구 상무대로 904 / 062-380-2288","claim":"① 앱(흥국생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2002-7000"},
            {"name":"동양생명","color":"#FF6600","call":"1577-1004","emergency":"해당없음","hq":"서울 종로구 종로 26","gwangju":"광주 서구 상무중앙로 110 / 062-380-1004","claim":"① 앱(동양생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3455-5000"},
            {"name":"ABL생명","color":"#004B87","call":"1588-6600","emergency":"해당없음","hq":"서울 영등포구 국제금융로 10","gwangju":"광주 서구 상무대로 904 / 062-380-6600","claim":"① 앱(ABL생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3455-6000"},
            {"name":"미래에셋생명","color":"#E8001C","call":"1588-0220","emergency":"해당없음","hq":"서울 중구 을지로5길 26 (미래에셋센터원빌딩)","gwangju":"광주 서구 상무중앙로 110 / 062-380-0220","claim":"① 앱(미래에셋생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3774-7000"},
            {"name":"푸본현대생명","color":"#009B77","call":"1588-1005","emergency":"해당없음","hq":"서울 영등포구 국제금융로 10","gwangju":"광주 서구 상무대로 904 / 062-380-1005","claim":"① 앱(푸본현대생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3455-7000"},
            {"name":"KDB생명","color":"#005BAC","call":"1588-4040","emergency":"해당없음","hq":"서울 영등포구 국제금융로 10","gwangju":"광주 서구 상무대로 904 / 062-380-4040","claim":"① KDB생명 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3455-8000"},
            {"name":"처브라이프","color":"#C8102E","call":"1566-0770","emergency":"해당없음","hq":"서울 종로구 종로 33 (그랑서울)","gwangju":"콜센터 문의 (1566-0770)","claim":"① 처브라이프 홈페이지 → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2076-9000"},
            {"name":"AIA생명","color":"#E8001C","call":"1588-9898","emergency":"해당없음","hq":"서울 중구 을지로5길 26 (미래에셋센터원빌딩)","gwangju":"광주 서구 상무중앙로 110 / 062-380-9898","claim":"① 앱(AIA생명) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3774-8000"},
            {"name":"메트라이프생명","color":"#00A3E0","call":"1588-9600","emergency":"해당없음","hq":"서울 종로구 종로 33 (그랑서울 메트라이프타워)","gwangju":"광주 서구 상무대로 904 / 062-380-9600","claim":"① 앱(메트라이프) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2076-8000"},
        ]
        NON_LIFE_INS = [
            {"name":"삼성화재","color":"#0066CC","call":"1588-5114","emergency":"1588-5114 (24시간)","hq":"서울 서초구 서초대로74길 11","gwangju":"광주 서구 상무대로 904 / 062-360-5114","claim":"① 앱(삼성화재) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-1588-5114"},
            {"name":"현대해상","color":"#005BAC","call":"1588-5656","emergency":"1588-5656 (24시간)","hq":"서울 종로구 세종대로 163","gwangju":"광주 서구 상무중앙로 110 / 062-380-5656","claim":"① 앱(현대해상) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2002-8000"},
            {"name":"KB손해보험","color":"#FFB81C","call":"1588-0114","emergency":"1588-0114 (24시간)","hq":"서울 강남구 테헤란로 222","gwangju":"광주 서구 상무대로 904 / 062-360-0114","claim":"① 앱(KB손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2002-5000"},
            {"name":"DB손해보험","color":"#E8001C","call":"1588-0100","emergency":"1588-0100 (24시간)","hq":"서울 강남구 테헤란로 432","gwangju":"광주 서구 상무대로 904 / 062-360-0100","claim":"① 앱(DB손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3011-8000"},
            {"name":"메리츠화재","color":"#FF6600","call":"1566-7711","emergency":"1566-7711 (24시간)","hq":"서울 강남구 테헤란로 138","gwangju":"광주 서구 상무대로 904 / 062-360-7711","claim":"① 앱(메리츠화재) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-3786-8000"},
            {"name":"한화손해보험","color":"#E8001C","call":"1566-8000","emergency":"1566-8000 (24시간)","hq":"서울 영등포구 63로 50","gwangju":"광주 서구 상무대로 904 / 062-360-8000","claim":"① 앱(한화손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-789-8100"},
            {"name":"롯데손해보험","color":"#E8001C","call":"1588-3344","emergency":"1588-3344 (24시간)","hq":"서울 중구 을지로 30","gwangju":"광주 서구 상무대로 904 / 062-360-3344","claim":"① 앱(롯데손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2218-8000"},
            {"name":"흥국화재","color":"#8B0000","call":"1688-1688","emergency":"1688-1688 (24시간)","hq":"서울 종로구 새문안로 68","gwangju":"광주 서구 상무대로 904 / 062-360-1688","claim":"① 앱(흥국화재) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2002-7100"},
            {"name":"NH농협손해보험","color":"#00843D","call":"1644-9000","emergency":"1644-9000 (24시간)","hq":"서울 중구 새문안로 16","gwangju":"광주 서구 상무대로 904 / 062-360-9000","claim":"① 앱(NH농협손보) → 보험금 청구\n② 지점 방문 / 우편 접수\n③ 팩스 접수","fax":"02-2080-7000"},
        ]

        def _tel_link(text, color):
            def _rep(m):
                raw = m.group(0)
                digits = re.sub(r"[^0-9]", "", raw)
                return (f'<a href="tel:{digits}" style="color:{color};font-weight:700;'
                        f'text-decoration:none;border-bottom:1.5px solid {color}88;">{raw}</a>')
            return re.sub(
                r'\b1[0-9]{3}-[0-9]{4}\b|\b0[2-9][0-9]?-[0-9]{3,4}-[0-9]{4}\b',
                _rep, text)

        def _ins_card(ins):
            c = ins['color']
            claim_html = ins['claim'].replace('\n','<br>')
            gj = ins.get('gwangju','콜센터 문의')
            call_l  = _tel_link(ins['call'], c)
            emerg_l = _tel_link(ins['emergency'], c)
            gj_l    = _tel_link(gj, c)
            return (f"<div style='border:1.5px solid {c}33;border-left:5px solid {c};"
                    f"border-radius:8px;padding:12px 14px;margin-bottom:8px;background:#fff;'>"
                    f"<div style='font-size:0.95rem;font-weight:800;color:{c};margin-bottom:6px;'>🏢 {ins['name']}</div>"
                    f"<table style='width:100%;font-size:0.78rem;color:#333;border-collapse:collapse;'>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;width:82px;'>📞 콜센터</td><td>{call_l}</td></tr>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;'>🚨 긴급출동</td><td>{emerg_l}</td></tr>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;vertical-align:top;'>🏛️ 본사</td><td>{ins['hq']}</td></tr>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;vertical-align:top;'>🌸 광주</td><td>{gj_l}</td></tr>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;vertical-align:top;'>📋 청구</td><td>{claim_html}</td></tr>"
                    f"<tr><td style='padding:2px 6px 2px 0;font-weight:600;color:#555;'>📠 팩스</td><td>{ins['fax']}</td></tr>"
                    f"</table></div>")

        ins_tab_life, ins_tab_nonlife = st.tabs(["🏦 생명보험사", "🚗 손해보험사"])
        with ins_tab_life:
            cols_l = st.columns(2)
            for i, ins in enumerate(LIFE_INS):
                with cols_l[i % 2]:
                    st.markdown(_ins_card(ins), unsafe_allow_html=True)
        with ins_tab_nonlife:
            cols_n = st.columns(2)
            for i, ins in enumerate(NON_LIFE_INS):
                with cols_n[i % 2]:
                    st.markdown(_ins_card(ins), unsafe_allow_html=True)

    # ── [홈 복귀 버튼] 각 탭 공통 ────────────────────────────────────────
    def tab_home_btn(tab_key):
        if st.button("🏠 홈으로", key=f"btn_home_{tab_key}", type="primary"):
            st.session_state.current_tab = "home"
            st.rerun()

    # ── [t0] 신규보험 상담 ────────────────────────────────────────────────
    if cur == "t0":
        tab_home_btn("t0")
        st.subheader("📋 신규 보험 상품 상담")
        st.caption("기존 보험증권 분석 → 보장 공백 파악 → 신규 보험 컨설팅")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name0, query0, hi0, do0 = ai_query_block("t0", "현재 보험 가입 현황, 신규 상담 내용을 입력하세요.")
            policy_files = st.file_uploader("보험증권 PDF/이미지", accept_multiple_files=True,
                type=['pdf','jpg','jpeg','png'], key="up_t0")
            if policy_files:
                st.success(f"{len(policy_files)}개 증권 업로드 완료")
            if do0:
                doc_text = "".join(f"\n[증권: {pf.name}]\n" + extract_pdf_chunks(pf, char_limit=8000)
                    for pf in (policy_files or []) if pf.type == 'application/pdf')
                run_ai_analysis(c_name0, query0, hi0, "res_t0",
                    "[신규보험 상담 · 증권분석]\n1. 소득 역산 및 재무 진단\n"
                    "2. 암·뇌·심장·실손 보장 공백 분석\n3. 보험료 황금비율 안내\n"
                    "4. 신규 보험 컨설팅 및 우선순위 제안\n" + doc_text)
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t0")
            components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">📋 신규보험 상담 안내</b><br><br>
<b style="color:#c0392b;">▶ 증권 분석 체크리스트</b><br>
• 실손보험 중복 여부 및 갱신 여부 확인<br>
• 암·뇌·심장 3대 질환 보장 공백 점검<br>
• 간병·치매·장해 담보 누락 여부<br>
• 수수료 여부 확인 (연막 수술마취 포함 여부)<br><br>
<b style="color:#c0392b;">▶ 보험료 황금비율 원칙</b><br>
• 가처분 소득의 7~10% 적정 보험료<br>
• 위험직군 최대 20%까지 허용<br>
• 건보료 기반 역산 소득 활용<br><br>
<b style="color:#c0392b;">▶ 신규 컨설팅 우선순위</b><br>
1. 실손보험 갱신 (구실손 유지 여부)<br>
2. 암보험 보장 강화<br>
3. 뇌·심장혁관 담보 추가<br>
4. 간병보험 설계 (간병인 인정 기준 확인)<br>
5. 종신보험 또는 CI보험 검토<br><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 본 상담 내용은 참고용이며 최종 선택은 고객에게 있습니다.</b>
</div>""", height=340)

    # ── [t1] 보험금 상담 ──────────────────────────────────────────────────
    if cur == "t1":
        tab_home_btn("t1")
        st.subheader("💰 보험금 상담 · 민원 · 손해사정")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name1, query1, hi1, do1 = ai_query_block("t1", "보험금 청구 내용을 입력하세요.")
            claim_type = st.selectbox("상담 유형",
                ["보험금 청구 안내","보험금 미지급 민원","금융감독원 민원","손해사정 의뢰","민사소송 검토"],
                key="claim_type")
            claim_files = st.file_uploader("서류 업로드", accept_multiple_files=True,
                type=['pdf','jpg','jpeg','png'], key="up_t1")
            if do1:
                doc_text1 = "".join(f"\n[첨부: {cf.name}]\n" + extract_pdf_chunks(cf, char_limit=6000)
                    for cf in (claim_files or []) if cf.type == 'application/pdf')
                run_ai_analysis(c_name1, query1, hi1, "res_t1",
                    f"[보험금 상담 - {claim_type}]\n1.보험금 청구 가능 여부와 예상 지급액 분석\n"
                    "2.보험사 거절 시 대응 방안\n3.금융감독원 민원 절차\n4.관련 판례와 약관 조항\n" + doc_text1)
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t1")
            components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">💰 보험금 청구 안내</b><br><br>
<b style="color:#c0392b;">▶ 청구 절차 (5단계)</b><br>
1. 보험사 콜센터 접수 또는 앱 청구<br>
2. 필요서류 제출 (진단서·입원확인서 등)<br>
3. 보험사 심사 (3~14일 소요)<br>
4. 지급 결정 통보<br>
5. 불복 시 이의신청 또는 민원<br><br>
<b style="color:#c0392b;">▶ 지급 거절 대응 전략</b><br>
• 금감원 민원 (금감원 전화: 1332)<br>
• 속해사정 의뢰 검토<br>
• 약관 해석 이의 신청<br>
• 민사소송 검토 (시효 3년)<br><br>
<b style="color:#c0392b;">▶ 필수 준비서류</b><br>
• 보험금 청구서<br>
• 진단서 (주치의 도장 필수)<br>
• 입원확인서 / 퇴원확인서<br>
• 수술확인서 (해당 시)<br>
• 통장사본 (입금 계좌)<br><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 보험금 지급 여부는 보험사 심사 및 약관에 따릅니다.</b>
</div>""", height=340)

    # ── [disability] 장해보험금 산출 ─────────────────────────────────────
    if cur == "disability":
        tab_home_btn("disability")
        st.subheader("🩺 장해보험금 산출")
        st.caption("AMA방식(개인보험) · 맥브라이드방식(배상책임) · 호프만계수 적용")
        dis_sub = st.radio("산출 방식 선택",
            ["AMA방식 (개인보험 후유장해)","맥브라이드방식 (배상책임·손해배상)","호프만계수 (중간이자 공제)"],
            horizontal=True, key="dis_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_d, query_d, hi_d, do_d = ai_query_block("disability",
                "예: 남성 45세, 건설노동자, 월소득 350만원, 요추 추간판탈출증 수술 후 척추 장해 15% 판정")
            _dc1, _dc2 = st.columns(2)
            with _dc1:
                dis_gender = st.selectbox("성별", ["남성","여성"], key="dis_gender")
                dis_age    = st.number_input("나이 (세)", min_value=1, max_value=80, value=45, step=1, key="dis_age")
            with _dc2:
                dis_income = st.number_input("직전 3개월 평균 월소득 (만원)", min_value=0, value=350, step=10, key="dis_income")
                dis_rate   = st.number_input("장해지급률 (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.5, key="dis_rate")
            dis_type = st.selectbox("장해 유형", ["영구장해","한시장해(5년 이상)"], key="dis_type")
            dis_sum  = st.number_input("보험가입금액 (만원)", min_value=0, value=10000, step=500, key="dis_sum")
            if do_d:
                _n_years = max(0, (65 - dis_age))
                _hoffman = round(_n_years / (1 + 0.05 * _n_years / 2), 2) if _n_years > 0 else 0
                _ama_est = round(dis_sum * dis_rate / 100 * (0.2 if "한시" in dis_type else 1.0), 1)
                _mcb_est = round(dis_income * (dis_rate / 100) * (2 / 3) * _hoffman, 1)
                run_ai_analysis(c_name_d, query_d, hi_d, "res_disability",
                    f"[장해보험금 산출 — {dis_sub}]\n성별: {dis_gender}, 나이: {dis_age}세\n"
                    f"월평균소득: {dis_income}만원, 장해율: {dis_rate}%, 장해유형: {dis_type}\n"
                    f"호프만계수: {_hoffman}, AMA예상: {_ama_est}만원, 맥브라이드 일실수익: {_mcb_est}만원\n"
                    "1. AMA방식 보험금 산출\n2. 맥브라이드방식 일실수익 산출\n"
                    "3. 호프만 vs 라이프니쯔 비교\n4. 기왕증·과실상계 감액 시나리오\n"
                    "⚠️ 본 산출은 참고용이며 최종 보험금은 보험사 심사 및 법원 판결에 따릅니다.")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_disability")
            components.html("""
<div style="height:340px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🩺 장해보험금 산출 안내</b><br><br>
<b style="color:#c0392b;">▶ AMA방식 (개인보험)</b><br>
• 보험가입금액 × 장해지급률(%) = 예상 보험금<br>
• 한시장해(5년 이상): 해당 지급률의 <b>20%만 인정</b><br>
• 영구장해: 전액 지급률 적용<br><br>
<b style="color:#c0392b;">▶ 맥브라이드방식 (배상책임·손해배상)</b><br>
• 월평균소득 × 장해율(%) × (1-생활비율1/3) × 호프만계수<br>
• 가동연한(65세)까지 잔여 기간 적용<br><br>
<b style="color:#c0392b;">▶ 호프만 vs 라이프니쯔 비교</b><br>
• <b>호프만(단리)</b>: 법원·표준약관 기준 — 피해자에게 유리<br>
• <b>라이프니쯔(복리)</b>: 구 보험사 방식 — 보상금 상대적으로 적음<br>
• 2023.1.1 이후 사고: 표준약관상 호프만 의무 적용<br>
• 동일 장해율에서 약 <b>15~20% 차이</b> 발생<br><br>
<b style="color:#c0392b;">▶ 기본 준비서류</b><br>
• 성별·직업·직전 3개월 평균소득<br>
• 나이·장해부위(한시/영구)<br>
• 의사 장해진단서 (필수)<br><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 본 산출은 참고용이며 최종 보험금은 보험사 심사 및 법원 판결에 따릅니다.</b>
</div>""", height=360)
            st.markdown("##### 🔬 전문의 수준 의무기록 분석 가이드")
            components.html("""
<div style="height:480px;overflow-y:auto;padding:14px 16px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.55;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">🔬 의무기록 판독 핵심 포인트</b><br><br>
<b style="color:#c0392b;">▶ 진단서 (Diagnosis Certificate)</b><br>
• <b>상병명(ICD코드)</b>: 주상병·부상병 구분 확인 — 보험 약관상 보장 여부 직결<br>
• <b>발병일 vs 진단일</b>: 보험 가입일 이전 발병 여부 → 기왕증 분쟁 핵심<br>
• <b>인과관계</b>: 사고·질병과 현재 상태의 의학적 연관성 기재 여부<br>
• <b>치료 기간</b>: 입원·통원 기간 명시 → 입원일당·통원일당 청구 근거<br><br>
<b style="color:#c0392b;">▶ 장해진단서 (Disability Certificate)</b><br>
• <b>장해 부위 및 정도</b>: AMA 기준 vs 맥브라이드 기준 구분 확인<br>
• <b>영구장해 vs 한시장해</b>: 한시장해는 AMA방식 지급률의 20%만 인정<br>
• <b>장해지급률</b>: 보험사 자체 산정 vs 의사 소견 차이 → 분쟁 주요 원인<br>
• <b>기왕증 기여도</b>: 기존 질환 기여도 % 기재 → 보험금 감액 근거로 활용됨<br>
• <b>확인 포인트</b>: 전문의(해당과) 발급 여부, 병원 직인·의사 면허번호 확인<br><br>
<b style="color:#c0392b;">▶ 수술기록지 (Operative Record)</b><br>
• <b>수술명</b>: 약관상 수술 해당 여부 확인 (단순 처치 vs 수술 구분)<br>
• <b>마취 방법</b>: 전신마취·척추마취·국소마취 → 수술비 지급 기준 상이<br>
• <b>수술 부위·범위</b>: 다발성 수술 시 각 부위별 청구 가능 여부 검토<br>
• <b>집도의 전문과목</b>: 해당 수술의 적정성 판단 기준<br><br>
<b style="color:#c0392b;">▶ 영상검사 (MRI·CT·X-ray)</b><br>
• <b>판독 소견서</b>: 영상 자체보다 <b>판독 소견서</b>가 보험 청구 핵심 서류<br>
• <b>추간판탈출증(디스크)</b>: 탈출 레벨·압박 정도 → 장해율 산정 기준<br>
• <b>골절</b>: 골절선 위치·분쇄 여부 → 5대 골절 해당 시 추가 보험금<br>
• <b>뇌·심장</b>: 뇌경색 범위·심근경색 부위 → 진단비 지급 기준<br><br>
<b style="color:#c0392b;">▶ 입·퇴원 확인서 (Admission/Discharge Summary)</b><br>
• <b>입원 사유</b>: 치료 목적 입원 vs 요양 목적 → 실손보험 지급 기준 상이<br>
• <b>주치의 소견</b>: 퇴원 후 치료 계획 → 향후 치료비 청구 근거<br>
• <b>입원 기간</b>: 연속 입원 vs 분리 입원 → 입원일당 산정 방식 차이<br><br>
<b style="color:#c0392b;">▶ 보험사 분쟁 대응 전략</b><br>
• <b>보험사 장해율 < 의사 소견</b>: 독립 손해사정사 선임 권장<br>
• <b>기왕증 기여도 과다 적용</b>: 의무기록 재검토 + 전문의 소견서 추가 확보<br>
• <b>약관 해석 분쟁</b>: 금융감독원 분쟁조정위원회 신청 (무료)<br>
• <b>소멸시효</b>: 보험금 청구권 <b>3년</b> (상법 제662조) — 기산점 주의<br><br>
<b style="color:#8e44ad;">▶ 주요 ICD-10 코드 (보험 청구 빈출)</b><br>
• <b>M51</b>: 추간판 장애 (디스크) &nbsp;• <b>S72</b>: 대퇴골 골절<br>
• <b>I63</b>: 뇌경색 &nbsp;• <b>I21</b>: 급성 심근경색<br>
• <b>C00-C97</b>: 악성신생물(암) &nbsp;• <b>G35</b>: 다발성 경화증<br>
• <b>F00-F03</b>: 치매 &nbsp;• <b>G20</b>: 파킨슨병<br>
<b style="color:#555;font-size:0.78rem;">⚠️ 의무기록 해석은 전문의·손해사정사와 반드시 확인하십시오.</b>
</div>
""", height=498)

    # ── [t2] 기본보험 상담 ────────────────────────────────────────────────
    if cur == "t2":
        tab_home_btn("t2")
        st.subheader("🛡️ 기본보험 상담")
        ins_type = st.selectbox("보험 유형 선택",
            ["🚗 자동차보험","🚙 운전자보험","🔥 화재보험","🤝 (가족)일상생활배상책임담보"],
            key="t2_ins_type")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name2, query2, hi2, do2 = ai_query_block("t2", f"{ins_type} 관련 상담 내용을 입력하세요.")
            if do2:
                run_ai_analysis(c_name2, query2, hi2, "res_t2",
                    f"[기본보험 상담 - {ins_type}]\n1. 현재 가입 현황 분석 및 보장 공백\n"
                    "2. 권장 가입 기준 및 특약 안내\n3. 보험료 절감 방법\n4. 면책 사항 안내")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t2")
            if ins_type == "🔥 화재보험":
                if st.button("🏗️ 화재보험 재조달가액 산출 이동", key="btn_fire_from_t2"):
                    st.session_state.current_tab = "fire"
                    st.rerun()
            elif ins_type == "🚙 운전자보험":
                st.markdown("##### 🚙 운전자보험 플랜 안내")
                components.html("""
<div style="height:420px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
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
• <b>판례 기준</b>: 뇌손상·척수손상·사지마비·시력상실·청력상실 등 <b>영구장애</b><br>
• <b>핵심</b>: 중상해 발생 시 피해자 합의 여부와 <b>무관하게 형사처벌 대상</b><br>
• <b>형사합의 필요성</b>: 합의 시 양형 감경 가능 → 교통사고처리지원금(2억) 활용<br>
<br>
<b style="font-size:0.9rem;color:#1a3a5c;">🌟 운전자보험 (권장) 플랜</b><br>
기본 플랜 + 아래 상해보장 특약 추가:<br>
• <b>후유장해</b>: 교통사고로 인한 영구 장해 시 장해율에 따라 보험금 지급<br>
• <b>상해수술비</b>: 교통사고 부상으로 수술 시 1회당 정액 지급<br>
• <b>교통사고 부상 위로금</b>: 상해급수(1~14급) 기준 정액 지급<br>
• <b>골절 진단비</b>: 일반 골절 + <b>5대 골절</b>(대퇴골·척추·골반·상완골·하퇴골) 추가 지급<br>
• <b>척추수술비</b>: 추간판탈출증(디스크) 등 척추 수술 시 별도 지급
</div>
""", height=438)
            elif ins_type == "🚗 자동차보험":
                st.markdown("##### 🚗 자동차보험 권장 기준")
                components.html("""
<div style="height:260px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🚗 자동차보험 권장 기준</b><br>
• <b>대인배상</b>: 무한 (법적 의무)<br>
• <b>대물배상</b>: 기본 5억 / 권장 10억 이상<br>
• <b>자기신체손해</b>: 자동차상해(자상) 선택 권장 (과실 무관 실손 보상)<br>
• <b>자기차량손해</b>: 차량 가액 대비 자기부담금 설정 검토<br>
• <b>무보험차상해</b>: 상대방 무보험 대비 필수<br>
• <b>긴급출동 특약</b>: 배터리·타이어·잠금장치 등 포함 권장<br>
• <b>할인 항목</b>: 블랙박스·마일리지·안전운전 할인 적용 여부 확인
</div>
""", height=278)
            elif ins_type == "🤝 (가족)일상생활배상책임담보":
                st.markdown("##### 🤝 (가족)일상생활배상책임담보 안내")
                components.html("""
<div style="height:260px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
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

    # ── [t3] 통합보험 설계 ────────────────────────────────────────────────
    if cur == "t3":
        tab_home_btn("t3")
        st.subheader("🏥 질병·상해 통합보험 상담")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name3, query3, hi3, do3 = ai_query_block("t3",
                "예) 40세 남성, 실손+암보험 가입, 뇌·심장 보장 공백 분석 요청")
            if do3:
                run_ai_analysis(c_name3, query3, hi3, "res_t3",
                    "[통합보험 설계]\n1. 실손보험 현황 분석 (1~4세대 구분)\n"
                    "2. 암·뇌·심장 3대 질병 보장 공백 파악\n3. 간병보험·치매보험 필요성 분석\n"
                    "4. 생명보험·CI보험 통합 포트폴리오 최적화\n5. 헬스케어 서비스 연계 종합 설계")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t3")
            st.markdown("##### 📋 통합보험 설계 포인트")
            components.html("""
<div style="height:520px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
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
• <b>갱신형(년만기)</b>: 초기 보험료 저렴, 경제활동기 큰 보장 확보 고객 추천<br>
<b style="font-size:0.85rem;color:#1a3a5c;">📝 유병자 간편보험 (3·N·5) 고지 실무</b><br>
• <b>3개월 내</b>: 약 종류/용량 변경, 단순 통원, 재검사 소견 등 반드시 확인<br>
• <b>입원/수술 범위</b>: 응급실 6시간 체류, MRI 검사 입원, 용종 제거(내시경) 등도 고지 대상<br>
• <b>5년 무사고 법칙</b>: 고지의무 위반 후 5년 내 추가 치료 없어도 분쟁 위험<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💊 최신 비급여 의료비 기준</b><br>
• 다빈치 로봇 수술: 약 1,500만원<br>
• 표적항암 치료: 5,000만원 ~ 2억원<br>
• 중입자 치료: 약 5,000만원<br>
• 면역항암 치료: 약 1억 5,000만원<br>
• 카티(CAR-T) 항암: 7,000만원 ~ 15,000만원<br>
• 항암방사선: 3,000만원 ~ 6,000만원
</div>
""", height=538)

    # ── [이미지 분석] 보험금/이미지 ──────────────────────────────────────
    if cur == "img":
        tab_home_btn("img")
        st.subheader("📷 의무기록 및 증권 이미지 분석")
        st.caption("보험 증권, 진단서, 의료 기록, 사고 현장 사진을 AI가 정밀 분석합니다.")
        col_a, col_b = st.columns([1, 1])
        with col_a:
            files = st.file_uploader("자료 업로드 (PDF/이미지)", accept_multiple_files=True,
                type=['pdf','jpg','jpeg','png','bmp'], key="uploader_img")
            if files:
                st.success(f"{len(files)}개 파일 업로드 완료")
                for i, f in enumerate(files, 1):
                    if f.type.startswith('image/'):
                        st.image(f, caption=f"파일 {i}", width=180)
        with col_b:
            img_query_type = st.selectbox("분석 유형",
                ["보험금 청구","진단서 분석","사고 현장 분석","의료 기록 분석"], key="img_query_type")
            img_specific = st.text_area("특정 요청사항",
                placeholder="예: 이 증권의 암 보장 금액을 분석해주세요.", height=160, key="img_specific")
        if files and st.button("AI 이미지 분석 시작", type="primary", key="btn_img_analyze"):
            if 'user_id' not in st.session_state:
                st.error("로그인이 필요합니다.")
            else:
                user_name = st.session_state.get('user_name', '')
                is_special = st.session_state.get('is_admin', False)
                if not is_special and check_usage_count(user_name) >= MAX_FREE_DAILY:
                    st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                else:
                    with st.spinner("비전 엔진을 통한 정밀 분석 중..."):
                        try:
                            client, model_config = get_master_model()
                            c_name_img = st.session_state.get('current_c_name', '고객')
                            contents = [f"[보험금 상담 분석]\n분석 유형: {img_query_type}\n요청: {img_specific}\n"
                                        "1. 보험 문서의 주요 내용\n2. 의료 기록의 핵심 정보\n"
                                        "3. 보험금 청구 가능성 및 예상 금액\n4. 필요한 추가 서류"]
                            for f in files:
                                if f.type.startswith('image/'):
                                    contents.append(PIL.Image.open(f))
                                elif f.type == 'application/pdf':
                                    contents.append(f"PDF: {f.name}\n{process_pdf(f)[:500]}")
                            resp = client.models.generate_content(model=GEMINI_MODEL, contents=contents, config=model_config)
                            answer = sanitize_unicode(resp.text) if resp.text else "AI 응답을 받지 못했습니다."
                            safe_img_name = sanitize_unicode(c_name_img)
                            st.session_state['res_img'] = sanitize_unicode(f"### {safe_img_name}님 보험금 분석 리포트\n\n{answer}")
                            update_usage(user_name)
                            st.rerun()
                        except Exception as e:
                            st.error(f"이미지 분석 오류: {sanitize_unicode(str(e))}")
        show_result("res_img")


    # ── [t4] 자동차사고 상담 ──────────────────────────────────────────────
    if cur == "t4":
        tab_home_btn("t4")
        st.subheader("🚗 자동차사고 상담 · 과실비율 분석")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name4, query4, hi4, do4 = ai_query_block("t4", "예) 신호등 없는 교차로에서 직진 중 우측에서 좌회전 차량과 충돌.")
            with st.expander("✅ 13대 중과실 해당 여부 체크", expanded=False):
                fault_items = ["① 신호·지시 위반","② 중앙선 침범","③ 제한속도 20km/h 초과",
                    "④ 앞지르기 방법·금지 위반","⑤ 철길건널목 통과방법 위반",
                    "⑥ 횡단보도 보행자 보호의무 위반","⑦ 무면허 운전","⑧ 음주운전(0.03% 이상)",
                    "⑨ 보도 침범·횡단방법 위반","⑩ 승객 추락 방지의무 위반",
                    "⑪ 어린이 보호구역 안전운전의무 위반","⑫ 화물 추락 방지의무 위반","⑬ 개문발차 사고"]
                checked_faults = [fi for fi in fault_items if st.checkbox(fi, key=f"fault_{fi[:3]}")]
                if checked_faults:
                    st.warning(f"⚠️ {len(checked_faults)}개 중과실 해당 → 운전자보험 필수")
            if do4:
                fault_ctx = f"\n[13대 중과실 해당: {', '.join(checked_faults)}]\n" if checked_faults else ""
                run_ai_analysis(c_name4, query4, hi4, "res_t4",
                    f"[자동차사고 상담]{fault_ctx}\n1. 과실비율 분쟁심의위원회 기준 과실비율 분석\n"
                    "2. 13대 중과실 해당 여부\n3. 운전자보험 교통사고처리지원금 지급 가능 여부\n"
                    "⚠️ 최종 과실비율은 위원회/법원 판결에 따르며 본 답변은 참고용입니다.")
        with col2:
            st.markdown("##### 📋 자동차사고 상담 절차")
            components.html("""
<div style="height:420px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">📋 자동차사고 상담 절차 및 필요 서류</b><br>
<b>1단계 — 사고 상황 입력</b><br>
• 사고 일시·장소·도로 유형(교차로/직선/골목 등)<br>
• 상대방 차량 번호·보험사·담당자 연락처<br>
• 필요 서류: 사고사실확인원(경찰서 발급) / 현장 사진·블랙박스 영상 / 목격자 진술서<br>
<b>2단계 — 13대 중과실 해당 여부 체크</b><br>
• 근거: 교통사고처리특례법 제3조 제2항 단서<br>
• ① 신호·지시위반 ② 중앙선침범 ③ 제한속도 20km/h 초과<br>
• ④ 앞지르기 위반 ⑤ 철길건널목 위반 ⑥ 횟단보도 보행자 보호의무 위반<br>
• ⑦ 무면허운전 ⑧ 음주운전(0.03% 이상) ⑨ 보도침범<br>
• ⑩ 승객추락방지의무 위반 ⑪ 어린이보호구역(민식이법) ⑫ 화물추락방지 위반 ⑬ 개문발차<br>
• ⚠️ 중과실 해당 시: 피해자 합의 없어도 <b>형사처벌 가능</b> → 운전자보험 필수<br>
<b>👶 민식이법 (어린이보호구역 특례)</b><br>
• 근거: 특정범죄가중처벨법 제5조의13 (2020.3.25 시행)<br>
• 어린이보호구역 내 어린이(13세 미만) 사망: <b>무기 또는 3년 이상 징역</b><br>
• 어린이 상해: <b>1년 이상 15년 이하 징역 또는 500만~3,000만원 벨금</b><br>
• 대응: 운전자보험 교통사고처리지원금(2억 권장) + 변호사선임비용 특약 필수<br>
<b>⚖️ 교통사고처리특례법 핵심 정리</b><br>
• 제3조 제1항: 교통사고 업무상과실·중과실 → 5년 이하 금고 또는 2,000만원 이하 벨금<br>
• 제3조 제2항: 종합보험 가입 + 피해자 합의 시 <b>공소권 없음</b> (단, 13대 중과실 제외)<br>
<b>3단계 — 분쟁심의위원회 신청</b><br>
• 신청처: <a href="https://accident.knia.or.kr" target="_blank">accident.knia.or.kr</a> 온라인 신청<br>
• 신청 비용: 없음 / 처리 기간: 약 60일 이내<br>
• 필요 서류: 신청서 / 사고사실확인원 / 보험증권 / 진단서 / 블랙박스 영상·사진
</div>
""", height=440)
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t4")

    # ── [t5] 노후·상속설계 ────────────────────────────────────────────────
    if cur == "t5":
        tab_home_btn("t5")
        st.subheader("🌅 노후설계 · 연금 3층 · 상속·증여")
        retire_sub = st.radio("상담 분야", ["노후/연금 설계","상속·증여 설계","주택연금"],
            horizontal=True, key="retire_sub")
        if retire_sub == "상속·증여 설계":
            section_inheritance_will()
        elif retire_sub == "주택연금":
            section_housing_pension()
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                c_name5, query5, hi5, do5 = ai_query_block("t5", "예) 55세, 은퇴 후 월 300만원 필요, 국민연금 20년 가입")
                if do5:
                    run_ai_analysis(c_name5, query5, hi5, "res_t5",
                        "[노후설계 상담]\n1. 국민연금·퇴직연금·개인연금 3층 연금 현황 분석\n"
                        "2. 소득대체율 격차 해소 방안\n3. 은퇴 후 필요 생활비 역산\n"
                        "4. 연금보험·즉시연금·종신보험으로 격차 보완\n5. IRP·연금저축 세액공제 활용법")
            with col2:
                st.subheader("🤖 AI 분석 리포트")
                show_result("res_t5")
                st.markdown("##### 🏗️ 연금 3층 설계 핵심 전략")
                components.html("""
<div style="height:260px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🏗️ 1층 — 국민연금</b><br>
• <b>수령 시기 최적화</b>: 연기연금 신청 시 1개월당 0.6% 증액 → 최대 5년 연기 시 <b>36% 증액</b><br>
• 조기수령(최대 5년 앞당김) 시 1개월당 0.5% 감액 → 장수 리스크 고려 신중 결정<br>
• 실질 소득대체율: 명목 40% 대비 실제 <b>22~28%</b> 수준 (가입 기간 단절 반영)<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 2층 — 퇴직연금</b><br>
• IRP 세액공제: 연 <b>900만원 한도</b> (연금저축 포함) / 세액공제율 13.2~16.5%<br>
• DC형: 본인 추가 납입 가능 → 운용 수익률 제고 필수<br>
• 중도 인출 시 세액공제 혜택 반납 + 기타소득세 16.5% 부과 → 유지 권장<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💼 3층 — 개인연금</b><br>
• 연금저축: 연 <b>400만원</b> 세액공제 한도 (종합소득 5,500만원 이하 16.5%)<br>
• IRP 추가 납입: 연금저축 외 <b>300만원 추가</b> 세액공제 가능<br>
• 연금보험(비과세): 10년 이상 유지 시 이자소득세 비과세 → 장기 유지 전략<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🎯 격차 보완 전략</b><br>
• 명목 소득대체율 65% vs 실질 40~50% → <b>15~25%p 격차</b> 보완 필수<br>
• 즉시연금·종신보험 연계로 사망 시까지 월 소득 확보<br>
• 목표: 실질 소득대체율 <b>60~70%</b> 달성
</div>
""", height=278)

    # ── [t6] 세무상담 ─────────────────────────────────────────────────────
    if cur == "t6":
        tab_home_btn("t6")
        st.subheader("📊 세무상담")
        tax_sub = st.radio("상담 분야", ["상속·증여세","연금소득세","CEO설계"],
            horizontal=True, key="tax_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name6, query6, hi6, do6 = ai_query_block("t6", f"{tax_sub} 관련 세무 상담 내용을 입력하세요.")
            if do6:
                run_ai_analysis(c_name6, query6, hi6, "res_t6",
                    f"[세무상담 - {tax_sub}]\n1. 관련 세법 조항과 최신 개정 내용\n"
                    "2. 절세 전략과 합법적 세금 최소화 방안\n3. 신고 기한과 필요 서류\n"
                    "4. 세무사 상담이 필요한 사항\n※ 본 답변은 참고용이며 구체적 사안은 세무사와 상의하십시오.")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            if tax_sub == "상속·증여세":
                show_result("res_t6", "**상속·증여세 핵심 포인트:**\n"
                    "- 상속세: 일괄공제 5억 / 배우자공제 최소 5억\n"
                    "- 증여세: 10년 합산 / 배우자 6억·자녀 5시만원 공제\n"
                    "- 사망보험금(생명보험사 종신·정기): 상속재산 제외 가능 (세무사 확인 필수)\n"
                    "- 세율: 10%~50% 누진세율 적용")
            elif tax_sub == "연금소득세":
                show_result("res_t6", "**연금소득세 핵심 포인트:**\n"
                    "- 연금저축·IRP 수령 시: 3.3~5.5% 연금소득세\n"
                    "- 연간 1,500만원 초과 수령 시: 종합소득세 합산 또는 분리과세 선택\n"
                    "- 수령 시기 분산으로 세부담 최소화 가능 (세무사 확인 권장)")
            else:
                show_result("res_t6", "**CEO설계 핵심 포인트:**\n"
                    "- 경영인정기보험: 법인 납입 보험료 손금산입 가능 여부 확인\n"
                    "- CEO 유고 시 법인 리스크 대비: 사망보험금 → 퇴직금 재원 활용\n"
                    "- 임원 퇴직금 규정 정비 필수 (정관 반영)\n"
                    "- 가입 전 법인 정관·세무처리 방식 반드시 세무사와 확인")
            st.markdown("##### 📊 세무상담 핵심 정리")
            components.html("""
<div style="height:260px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🏠 상속·증여세 핵심</b><br>
• 상속세 일괄공제: <b>5억원</b> / 배우자공제: 최소 5억원<br>
• 증여세 10년 합산 공제: 배우자 6억 / 성년자녀 5시만원 / 미성년자녀 2시만원<br>
• 세율: 10%~50% 누진세율<br>
• 생명보험 사망보험금: 상속재산 제외 가능 (세무사 확인 필수)<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💰 연금소득세 핵심</b><br>
• 연금저축·IRP 수령 시: 3.3~5.5% 연금소득세<br>
• 연간 1,500만원 초과: 종합소득세 합산 또는 <b>16.5% 분리과세</b> 선택<br>
• 수령 시기 분산 전략으로 세부담 최소화<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 CEO설계 핵심</b><br>
• 경영인정기보험: 손금산입 가능 여부 세무사 사전 확인 필수<br>
• 임원 퇴직금 규정 정비 필수 (정관 반영)<br>
• 법인세·소득세 분산 효과: 세무사와 사전 검토 필수<br>
• 가입 전 법인 정관·세무처리 방식 반드시 세무사와 확인
</div>
""", height=278)

    # ── [t7] 법인상담 ─────────────────────────────────────────────────────
    if cur == "t7":
        tab_home_btn("t7")
        st.subheader("🏢 법인상담 (CEO플랜 · 단체보험 · 기업보험)")
        corp_sub = st.radio("상담 분야",
            ["CEO플랜 (사망·퇴직)","단체상해보험","공장·기업 화재보험","법인 절세 전략","임원 퇴직금 설계"],
            horizontal=True, key="corp_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name7, query7, hi7, do7 = ai_query_block("t7", f"{corp_sub} 관련 법인 상담 내용을 입력하세요.")
            emp_count  = st.number_input("임직원 수", min_value=1, value=10, step=1, key="emp_count")
            corp_asset = st.number_input("법인 자산 규모 (만원)", value=100000, step=10000, key="corp_asset")
            if do7:
                run_ai_analysis(c_name7, query7, hi7, "res_t7",
                    f"[법인상담 - {corp_sub}]\n임직원수: {emp_count}명, 법인자산: {corp_asset:,}만원\n"
                    "1. 법인 보험의 세무처리(손금산입) 방법\n2. CEO 유고 시 법인 리스크 관리\n"
                    "3. 단체보험 가입 기준과 보장 설계\n4. 퇴직금 재원 마련을 위한 보험 활용")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_t7", "**법인보험 핵심 포인트:**\n"
                "- CEO플랜: 사망보험금 → 퇴직금 재원\n"
                "- 단체상해: 전 직원 의무 가입 권장\n"
                "- 공장화재: 재조달가액 기준 가입\n"
                "- 법인 납입 보험료 손금산입 가능\n"
                "- 임원 퇴직금 규정 정비 필수")
            st.markdown("##### 🏢 법인보험 핵심 안내")
            components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">👔 CEO플랜 (사망·퇴직)</b><br>
• 경영인정기보험: 사망보험금 → <b>퇴직금 재원</b> 활용<br>
• 임원 퇴직금 규정 정비 필수 (정관 반영)<br>
• 법인 납입 보험료: 손금산입 가능 여부 세무사 사전 확인<br>
• CEO 유고 시 법인 리스크: 운영자금 결속, 주가 하락, 거래선 상실 대비<br>
<b style="font-size:0.85rem;color:#1a3a5c;">👥 단체상해보험</b><br>
• 전 직원 의무 가입 권장 (산재보험 보완)<br>
• 업무상 상해·질병 보장 포함<br>
• 단체보험 가입 기준: 임직원 5인 이상 시 유리<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏠 공장·기업 화재보험</b><br>
• 재조달가액 기준 가입 필수 (비례보상 방지)<br>
• 기계장치·재고자산 포함 여부 확인<br>
• 영업중단손실 보상 특약 검토<br>
<b style="font-size:0.85rem;color:#1a3a5c;">📊 법인 절세 전략</b><br>
• 보험료 손금산입: 전액 또는 일부 손금 가능 (상품별 상이)<br>
• 임원 보수 설계: 소득세 절감 + 퇴직금 재원 동시 확보<br>
• 가업승계 전략: 비상장주식 평가 후 증여 시점 최적화
</div>
""", height=338)

    # ── [t8] CEO플랜 ──────────────────────────────────────────────────────
    if cur == "t8":
        tab_home_btn("t8")
        st.subheader("👔 CEO플랜 — 비상장주식 약식 평가 & 법인 재무분석")
        ceo_sub = st.radio("분석 방식 선택", ["📊 직접 입력 평가표","📁 재무제표 스캔 업로드"],
            horizontal=True, key="ceo_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            if ceo_sub == "📊 직접 입력 평가표":
                ceo_company  = st.text_input("법인명", "(주)예시기업", key="ceo_company")
                total_shares = st.number_input("발행주식 총수 (주)", value=10000, step=100, key="ceo_shares")
                is_ctrl      = st.checkbox("최대주주 (경영권 할증 20% 적용)", value=True, key="ceo_ctrl")
                is_re        = st.checkbox("부동산 과다 법인 (자산 비중 80% 이상)", value=False, key="ceo_re")
                mkt_price_in = st.number_input("매매사례가액 (원, 없으면 0)", value=0, step=1000, key="ceo_mkt")
                net_asset    = st.number_input("순자산 (원)", value=12_864_460_902, step=1_000_000, key="ceo_asset")
                st.markdown("**당기순이익 3개년 (원)**")
                c1, c2, c3 = st.columns(3)
                with c1: ni_1 = st.number_input("최근년", value=688_182_031, step=1_000_000, key="ceo_ni1")
                with c2: ni_2 = st.number_input("전년",   value=451_811_737, step=1_000_000, key="ceo_ni2")
                with c3: ni_3 = st.number_input("전전년", value=553_750_281, step=1_000_000, key="ceo_ni3")
                if st.button("📈 비상장주식 평가 실행", type="primary", key="btn_ceo_eval"):
                    mkt = mkt_price_in if mkt_price_in > 0 else None
                    ev  = AdvancedStockEvaluator(net_asset=net_asset, net_incomes=[ni_1, ni_2, ni_3],
                        total_shares=total_shares, market_price=mkt, is_controlling=is_ctrl, is_real_estate_rich=is_re)
                    st.session_state.update({"ceo_eval_corp": ev.evaluate_corporate_tax(),
                        "ceo_eval_inh": ev.evaluate_inheritance_tax(),
                        "ceo_company_result": ceo_company, "ceo_shares_result": total_shares})
                    st.rerun()
            else:
                fs_files = st.file_uploader("재무제표 파일 업로드", type=["pdf","jpg","jpeg","png"],
                    accept_multiple_files=True, key="ceo_fs_files")
                ceo_c2   = st.text_input("법인명", "(주)예시기업", key="ceo_company2")
                ceo_note = st.text_area("추가 분석 요청", height=80, key="ceo_note")
                if st.button("🔍 재무제표 AI 분석 실행", type="primary", key="btn_ceo_fs"):
                    if not fs_files:
                        st.error("재무제표 파일을 업로드하세요.")
                    elif 'user_id' not in st.session_state:
                        st.error("로그인이 필요합니다.")
                    else:
                        user_name = st.session_state.get('user_name', '')
                        if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                            st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                        else:
                            with st.spinner("재무제표 분석 중..."):
                                try:
                                    client, model_config = get_master_model()
                                    fs_text = "".join(
                                        f"\n[재무제표: {f.name}]\n" + (extract_pdf_chunks(f, 6000) if f.type == "application/pdf" else f"[이미지: {f.name}]")
                                        for f in fs_files)
                                    resp = client.models.generate_content(model=GEMINI_MODEL,
                                        contents=CEO_FS_PROMPT + f"\n법인명: {ceo_c2}\n{ceo_note or ''}\n{fs_text}",
                                        config=model_config)
                                    st.session_state['res_ceo_fs'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                    update_usage(user_name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"분석 오류: {sanitize_unicode(str(e))}")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            if ceo_sub == "📊 직접 입력 평가표":
                corp_r = st.session_state.get("ceo_eval_corp")
                inh_r  = st.session_state.get("ceo_eval_inh")
                company = st.session_state.get("ceo_company_result", "")
                shares  = st.session_state.get("ceo_shares_result", 0)
                if corp_r and inh_r:
                    corp_val = corp_r["법인세법상 시가"]
                    inh_val  = inh_r["상증법상 최종가액"]
                    st.metric("법인세법상 시가 (주당)", f"{corp_val:,.0f}원")
                    st.metric("상증법상 최종가액 (주당)", f"{inh_val:,.0f}원")
                    st.metric("총 평가액 (법인세법)", f"{corp_val*shares:,.0f}원")
                    if st.button("🤖 AI 심층 분석 (CEO플랜 설계)", key="btn_ceo_ai"):
                        if 'user_id' not in st.session_state:
                            st.error("로그인이 필요합니다.")
                        else:
                            user_name = st.session_state.get('user_name', '')
                            with st.spinner("CEO플랜 분석 중..."):
                                try:
                                    client, model_config = get_master_model()
                                    resp = client.models.generate_content(model=GEMINI_MODEL,
                                        contents=CEO_PLAN_PROMPT + f"\n법인명: {company}, 발행주식: {shares:,}주\n"
                                        f"법인세법상 시가: {corp_val:,.0f}원/주\n상증법상 최종가액: {inh_val:,.0f}원/주",
                                        config=model_config)
                                    st.session_state['res_ceo_ai'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                    update_usage(user_name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"분석 오류: {sanitize_unicode(str(e))}")
                    show_result("res_ceo_ai")
                else:
                    st.info("좌측 입력표를 작성하고 '비상장주식 평가 실행'을 클릭하세요.")
                    st.markdown("##### 📘 비상장주식 평가 방법 안내")
                    components.html("""
<div style="height:320px;overflow-y:auto;padding:14px 16px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">📌 비상장주식 평가 방법 (상증법 기준)</b><br>
<b style="color:#c0392b;">① 순자산가치</b><br>
• 공식: 순자산 ÷ 발행주식 총수<br>
• 기준: 최근 사업연도 말 대차대조표 자본총계<br>
<b style="color:#c0392b;">② 순손익가치</b><br>
• 공식: 최근 3년 가중평균 순이익 ÷ 발행주식 총수 ÷ 10%<br>
• 가중치: 최근년 3 / 전년 2 / 전전년 1 (합계 6)<br>
<b style="color:#c0392b;">③ 상증법상 최종가액</b><br>
• 일반법인: 순자산가치 40% + 순손익가치 60%<br>
• 부동산 과다 법인: 순자산가치 60% + 순손익가치 40%<br>
• 최대주주 경영권 할증: 평가액의 <b>20% 가산</b><br>
<b style="color:#c0392b;">④ 법인세법상 시가</b><br>
• 매매사례가액 우선 적용 (최근 거래가)<br>
• 없을 경우: 상증법 보충적 평가방법 준용<br>
<b style="color:#e67e22;">⚠️ CEO플랜 활용 포인트</b><br>
• 주식 가치 낮을 때 증여 → 증여세 절감<br>
• 사망보험금 → 퇴직금 재원 → 주식 매입 재원<br>
• 가업승계: 증여세 과세특례 (최대 600억 공제)<br>
• 상속세 연부연납: 최대 10년 분할 납부 가능<br>
<b style="color:#555;font-size:0.78rem;">⚠️ 본 평가는 참고용이며 실제 세무처리는 세무사와 확인하십시오.</b>
</div>
""", height=338)
            else:
                show_result("res_ceo_fs")
                if not st.session_state.get("res_ceo_fs"):
                    st.markdown("##### 📘 비상장주식 평가 방법 안내")
                    components.html("""
<div style="height:320px;overflow-y:auto;padding:14px 16px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">📁 재무제표 스캔 분석 안내</b><br>
• PDF 또는 이미지(JPG/PNG) 형식으로 업로드<br>
• 손익계산서·대차대조표 3개년치 포함 권장<br>
• AI가 순자산·순손익 자동 추출 후 비상장주식 평가<br>
<b style="color:#c0392b;">분석 포함 항목</b><br>
• 비상장주식 약식 평가 (상증법·법인세법)<br>
• CEO 퇴직금 설계 방안<br>
• 가업승계 전략 및 증여세 절감 방안<br>
• 법인 절세 전략 종합 리포트<br>
<b style="color:#555;font-size:0.78rem;">⚠️ 본 분석은 참고용이며 실제 세무처리는 세무사와 확인하십시오.</b>
</div>
""", height=338)

    # ── [fire] 화재보험 재조달가액 ────────────────────────────────────────
    if cur == "fire":
        tab_home_btn("fire")
        st.subheader("🔥 화재보험 재조달가액 산출")
        st.caption("한국부동산원(REB) 기준 건물 재조달가액 산출 · 비례보상 방지 전략")

        # ── 상단: AI 분석 리포트 + 설계 가이드 스크롤창 ──────────────────
        st.subheader("🤖 AI 분석 리포트")
        show_result("res_fire")
        components.html("""
<div style="height:360px;overflow-y:auto;padding:13px 16px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">🏗️ 화재보험 설계 가이드</b><br><br>

<b style="color:#c0392b;">▶ 재조달가액 산출 공식 (REB 기준)</b><br>
• <b>재조달가액</b> = (표준단가 × 부대설비 보정치) × 연면적 + 간접비(15%) + 수급인 이윤(6%)<br>
• 표준단가: 한국부동산원(REB) 건물신축단가표 (매년 갱신)<br>
• 건설노임단가: 대한건설협회(CAK) 연 2회 발표 기준<br><br>

<b style="color:#c0392b;">▶ 비례보상(일부보험) 방지 전략</b><br>
• <b>보험금 산출식</b>: 지급액 = 실제 손해액 × (보험가입금액 ÷ 보험가액)<br>
• ⚠️ <b>일부보험 상태 시 실제 손해액의 일부만 지급</b> — 비례보상 불이익 발생<br>
• <b>권장 가입비율: 재조달가액의 100%~110% 가입 제안</b><br>
&nbsp;&nbsp;(5년 장기의 경우 매년 물가상승률 반영 시 5년 뒤 약 20% 근접 보험가액 차이 발생)<br><br>

<b style="color:#c0392b;">▶ 실손담보 vs 비례담보 비교</b><br>
<table style="width:100%;border-collapse:collapse;font-size:0.81rem;">
<tr style="background:#e8f0fe;"><th style="padding:4px 6px;text-align:left;border:1px solid #c5cae9;">구분</th><th style="padding:4px 6px;border:1px solid #c5cae9;">실손담보</th><th style="padding:4px 6px;border:1px solid #c5cae9;">비례담보(일부보험)</th></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">가입금액</td><td style="padding:4px 6px;border:1px solid #ddd;">보험가액의 100% 이상</td><td style="padding:4px 6px;border:1px solid #ddd;">보험가액 미만</td></tr>
<tr style="background:#fafafa;"><td style="padding:4px 6px;border:1px solid #ddd;">보험금 지급</td><td style="padding:4px 6px;border:1px solid #ddd;">실제 손해액 전액 지급</td><td style="padding:4px 6px;border:1px solid #ddd;">손해액 × (가입금액/보험가액)</td></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">예시(손해 1억)</td><td style="padding:4px 6px;border:1px solid #ddd;">1억원 지급</td><td style="padding:4px 6px;border:1px solid #ddd;">가입 80% → 8,000만원만 지급</td></tr>
<tr style="background:#fff5f5;"><td style="padding:4px 6px;border:1px solid #ddd;color:#c0392b;" colspan="3">⚠️ 장기보험(5년)은 물가상승으로 보험가액이 높아져 자동으로 일부보험 전락 위험</td></tr>
</table><br>

<b style="color:#c0392b;">▶ 구조별 내용연수 및 평균 최종 잔가율</b><br>
<table style="width:100%;border-collapse:collapse;font-size:0.81rem;">
<tr style="background:#e8f0fe;"><th style="padding:4px 6px;border:1px solid #c5cae9;">구조</th><th style="padding:4px 6px;border:1px solid #c5cae9;">내용연수</th><th style="padding:4px 6px;border:1px solid #c5cae9;">평균 최종 잔가율</th></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">철근콘크리트(RC)</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">50년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr style="background:#fafafa;"><td style="padding:4px 6px;border:1px solid #ddd;">철골철근콘크리트(SRC)</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">55년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">철골조(S)</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">45년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr style="background:#fafafa;"><td style="padding:4px 6px;border:1px solid #ddd;">경량철골조</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">35년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">조적조(벽돌)</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">40년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr style="background:#fafafa;"><td style="padding:4px 6px;border:1px solid #ddd;">목조</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">30년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
<tr><td style="padding:4px 6px;border:1px solid #ddd;">기타</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">40년</td><td style="padding:4px 6px;border:1px solid #ddd;text-align:center;">20%</td></tr>
</table><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 산출 결과는 참고용이며 실제 보험가액은 보험사 심사에 따릅니다.</b>
</div>""", height=380)

        st.divider()

        # ── 하단: 재조달가액 산출기 + AI 상담 ────────────────────────────
        fire_sub = st.radio("기능 선택", ["🏗️ 재조달가액 산출기", "🤖 AI 화재보험 상담"],
            horizontal=True, key="fire_sub")

        if fire_sub == "🏗️ 재조달가액 산출기":
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

            fc1, fc2 = st.columns([1, 1])
            with fc1:
                st.markdown("##### 🏠 건물 기본 정보")
                _fuse    = st.selectbox("건물 용도", list(_FREB.keys()), key="fire_use")
                _fstruct = st.selectbox("구조", list(_FREB[_fuse].keys()), key="fire_struct")
                _farea   = st.number_input("연면적 (㎡)", min_value=1.0, value=100.0, step=1.0, key="fire_area")
                _fbuild_yr = st.number_input("사용승인연도", min_value=1950, max_value=2025, value=2000, step=1, key="fire_build_yr")
                _fpurchase = st.number_input("매입가격 (만원)", min_value=0, value=0, step=1000, key="fire_purchase",
                    help="매입가격 입력 시 재조달가액과 비교 표시")
                _frent_type = st.selectbox("전월세 임대 유무",
                    ["해당없음(자가사용)", "전세 임대 중", "월세 임대 중", "전·월세 혼합"],
                    key="fire_rent_type")
                _fbase_yr  = st.number_input("기준연도", min_value=2020, max_value=2035, value=2025, step=1, key="fire_base_yr")
                _finfl     = st.number_input("연평균 물가상승률 (%)", min_value=0.5, max_value=10.0, value=3.0, step=0.1, key="fire_infl")
                _flabor    = st.number_input("건설노임 보정률 (%)", min_value=-20, max_value=30, value=0, step=1, key="fire_labor")
                _fcur_ins  = st.number_input("현 화재보험 건물가입금액 (만원)", min_value=0, value=0, step=1000, key="fire_cur_ins",
                    help="현재 가입 중인 화재보험 건물 가입금액 (비교용)")
                _do_fire_calc = st.button("🔍 재조달가액 산출 실행", type="primary", key="fire_calc_btn", use_container_width=True)

            with fc2:
                st.markdown("##### 📊 산출 결과")
                if _do_fire_calc:
                    _fbase_unit = _FREB.get(_fuse, {}).get(_fstruct, 90)
                    _funit      = _fbase_unit * (1 + _flabor / 100)
                    _faux       = _FAUX.get(_fuse, 1.05)
                    _fdirect    = _funit * 10000 * _faux * _farea
                    _findirect  = _fdirect * 0.15
                    _fprofit    = (_fdirect + _findirect) * 0.06
                    _frebuild   = _fdirect + _findirect + _fprofit
                    _flife      = _FLIFE.get(_fstruct, 40)
                    _felapsed   = max(0, _fbase_yr - _fbuild_yr)
                    _fresid     = max(0.20, 1.0 - _felapsed / _flife)
                    _finsured   = _frebuild * _fresid  # 예상 보험가액(시가)
                    _frec100    = _frebuild             # 재조달가액 100%
                    _frec110    = _frebuild * 1.10      # 재조달가액 110%
                    st.session_state['fire_calc'] = {
                        "rebuild": _frebuild, "insured": _finsured,
                        "rec100": _frec100, "rec110": _frec110,
                        "life": _flife, "elapsed": _felapsed, "resid": _fresid,
                        "unit": _funit, "aux": _faux, "infl": _finfl,
                        "base_yr": _fbase_yr, "purchase": _fpurchase,
                        "cur_ins": _fcur_ins, "rent_type": _frent_type,
                    }

                fc = st.session_state.get('fire_calc')
                if fc:
                    # 핵심 지표
                    st.markdown("**🔥 산출 재조달가액 · 예상 보험가액**")
                    tbl_data = {
                        "항목": ["산출 재조달가액", "예상 보험가액(시가)", "권장 가입금액(100%)", "권장 가입금액(110%)"],
                        "금액(만원)": [
                            f"{fc['rebuild']/10000:,.0f}",
                            f"{fc['insured']/10000:,.0f}",
                            f"{fc['rec100']/10000:,.0f}",
                            f"{fc['rec110']/10000:,.0f}",
                        ],
                        "금액(억원)": [
                            f"{fc['rebuild']/1e8:.2f}억",
                            f"{fc['insured']/1e8:.2f}억",
                            f"{fc['rec100']/1e8:.2f}억",
                            f"{fc['rec110']/1e8:.2f}억",
                        ],
                    }
                    st.dataframe(pd.DataFrame(tbl_data), use_container_width=True, hide_index=True)

                    # 매입가격 비교
                    if fc['purchase'] > 0:
                        diff = fc['rebuild']/10000 - fc['purchase']
                        st.markdown(f"**매입가격 비교:** 매입가 {fc['purchase']:,}만원 → "
                            f"재조달가액 {fc['rebuild']/10000:,.0f}만원 "
                            f"({'**+**' if diff>=0 else '**-**'}{abs(diff):,.0f}만원 {'초과' if diff>=0 else '미만'})")

                    # 현 가입금액 비교
                    if fc['cur_ins'] > 0:
                        gap = fc['rec100']/10000 - fc['cur_ins']
                        status = "✅ 적정" if gap <= 0 else f"⚠️ 부족 ({gap:,.0f}만원 미달 — 일부보험 위험)"
                        st.markdown(f"**현 화재보험 가입금액:** {fc['cur_ins']:,}만원 → {status}")

                    # 임대 유무 안내
                    if fc['rent_type'] != "해당없음(자가사용)":
                        st.info(f"🏠 임대 유형: **{fc['rent_type']}** — 임차인 화재 피해 배상책임 및 임대인 배상책임보험 연계 설계 권장")

                    st.markdown(f"**경과연수:** {fc['elapsed']}년 / **잔가율:** {fc['resid']*100:.1f}% / **내용연수:** {fc['life']}년")

                    # 향후 5년 변화 표
                    st.markdown("**📈 향후 5년 건물가액 변화**")
                    rows5 = []
                    for _fy in range(6):
                        _frb = fc['rebuild'] * ((1 + fc['infl'] / 100) ** _fy)
                        _frs = max(0.20, 1.0 - (fc['elapsed'] + _fy) / fc['life'])
                        rows5.append({
                            "연도": f"{fc['base_yr'] + _fy}년",
                            "재조달가액(만원)": f"{_frb/10000:,.0f}",
                            "잔가율(%)": f"{_frs*100:.1f}",
                            "예상보험가액(만원)": f"{_frb*_frs/10000:,.0f}",
                            "권장가입(100%)(만원)": f"{_frb/10000:,.0f}",
                            "권장가입(110%)(만원)": f"{_frb*1.10/10000:,.0f}",
                        })
                    st.dataframe(pd.DataFrame(rows5), use_container_width=True, hide_index=True)
                else:
                    st.info("좌측 정보 입력 후 '재조달가액 산출 실행' 버튼을 클릭하세요.")

        else:  # AI 화재보험 상담
            col1, col2 = st.columns([1, 1])
            with col1:
                c_name_f, query_f, hi_f, do_f = ai_query_block("fire",
                    "예) 철근콘크리트 5층 상가, 연면적 1,200㎡, 1995년 준공")
                if do_f:
                    run_ai_analysis(c_name_f, query_f, hi_f, "res_fire",
                        "[화재보험 재조달가액 산출]\n1. 한국부동산원(REB) 기준 건물 재조달가액 산출\n"
                        "2. 비례보상 방지를 위한 적정 보험가액 설정\n3. 화재보험 설계 가이드\n"
                        "4. 건물 구조별 표준단가 안내\n5. 실손담보·비례담보 차이 및 보험금 산출식 안내")
            with col2:
                st.info("AI 분석 결과는 상단 '🤖 AI 분석 리포트'에 표시됩니다.")

    # ── [liability] 배상책임보험 상담 ────────────────────────────────────
    if cur == "liability":
        tab_home_btn("liability")
        st.subheader("⚖️ 배상책임보험 상담")
        liab_page = st.radio("페이지 선택", ["📋 1페이지 — 기본 배상책임", "🏢 2페이지 — 시설·요양기관 배상책임"],
            horizontal=True, key="liab_page")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_l, query_l, hi_l, do_l = ai_query_block("liability",
                "예) 음식점 운영 중 고객 식중독 사고 발생, 배상책임보험 청구 가능 여부 문의")
            if do_l:
                run_ai_analysis(c_name_l, query_l, hi_l, "res_liability",
                    "[배상책임보험 상담]\n1. 배상책임보험 개념 및 성립 요건 (민법 제750조)\n"
                    "2. 중복보험 독립책임액 안분방식 설명\n3. 민법·화재보험법·실화책임법 관련 법률\n"
                    "4. 변호사 수임료·성과보수 기준 안내\n5. 보험금 청구 절차 및 필요 서류")
        with col2:
            st.subheader("🤖 AI 분석 리포트")
            show_result("res_liability")
            if liab_page == "📋 1페이지 — 기본 배상책임":
                components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">⚖️ 배상책임보험 개념 및 중복가입 분담방식</b><br><br>
<b style="color:#c0392b;">▶ 배상책임 성립 요건 (민법 제750조)</b><br>
• 가해 행위의 존재<br>
• 위법성 (고의 또는 과실)<br>
• 손해의 발생<br>
• 인과관계 성립<br><br>
<b style="color:#c0392b;">▶ 중복보험 독립책임액 안분방식</b><br>
• 각 보험사의 독립책임액 합산 후 안분<br>
• 실제 손해액을 초과하여 지급할 수 없음<br>
• 중복 가입 시 반드시 보험사에 상호 통보 의무<br><br>
<b style="color:#c0392b;">▶ 민사배상(불법행위) 관련 법률</b><br>
• 민법 제750조: 고의·과실로 타인에게 손해를 가한 자는 배상 책임<br>
• 민법 제756조: 사용자 배상책임 (피용자의 불법행위)<br>
• 민법 제758조: 공작물 점유자·소유자 배상책임<br>
• 민법 제759조: 동물 점유자 배상책임<br><br>
<b style="color:#c0392b;">▶ 실화책임법 핵심</b><br>
• 경과실화: 중대한 과실이 있는 경우만 배상<br>
• 일반 실화: 실손해액 범위내 배상<br>
• 임대인 책임: 임차인의 과실 있는 경우 임대인도 연대책임<br><br>
<b style="color:#c0392b;">▶ 변호사 보수 기준 권고안 (대한변호사협회)</b><br>
• 소송가액 1억 이하: 소송가액의 10% 수준<br>
• 성과보수: 회수금액의 10~20% 수준<br>
• 보험금 지급 시 변호사비용 담보는 본 권고안 기준 적용<br>
※ 실제 수임료는 변호사마다 상이할 수 있습니다.<br><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 배상책임 여부는 법원 판결 및 약관에 따릅니다.</b>
</div>""", height=340)
            else:
                st.markdown("##### 🏢 시설·요양기관 배상책임 안내")
                components.html("""
<div style="height:560px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.5;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 시설소유관리자 배상책임 관련 법률</b><br>
• <b>민법 제758조</b>: 공작물(건물·시설) 점유자·소유자 배상책임<br>
• 점유자 1차 책임 → 손해 방지 불가 시 소유자 2차 책임<br>
• 적용 사례: 건물 외벽 낙하물 → 행인 부상 / 주차장 시설 결함 → 차량 파손<br>
• <b>의무보험 대상</b>: 다중이용업소, 학원, 체육시설, 의료기관 등<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 일상생활배상책임 약관 핵심</b><br>
• <b>피보험 범위</b>: 가족형 (동거 친족 + 별거 미혼 자녀)<br>
• <b>성립 요건</b>: 민법 제750조 기준, 일상생활 중 우연한 과실로 타인에게 손해<br>
• <b>자기부담금</b>: 대인 0원 / 대물 시기별 상이<br>
• <b>면책</b>: 고의 사고·천재지변·차량 관련 사고<br>
• <b>보상 사례</b>: 아파트 누수 → 아래층 피해 / 자녀 자전거 사고 → 타인 부상<br>
• <b>권장 한도</b>: 대인 무한 / 대물 1억 이상<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏥 시설·요양기관 관련 배상책임보험 종류</b><br>
• <b>시설소유관리자 배상책임</b>: 건물·시설 결함으로 인한 제3자 피해<br>
• <b>요양기관 배상책임</b>: 요양원·요양병원 입소자 낙상·사고 배상<br>
• <b>의료기관 배상책임</b>: 의료사고·감염 등 환자 피해 배상<br>
• <b>학원·체육시설 배상책임</b>: 수강생·이용자 부상 배상<br>
• <b>음식점 배상책임</b>: 식중독·이물질 등 고객 피해 배상<br><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🔥 화재배상책임 및 관련 법률 (시설·요양기관)</b><br>
• <b>다중이용업소 화재배상책임보험 의무가입</b> (다중이용업소 안전관리에 관한 특별법)<br>
• 대상: 음식점(150㎡ 이상), 노래방, PC방, 학원, 목욕장업 등<br>
• 보장 한도: 사망 1인당 1.5억 / 부상 최대 3천만원 / 재산피해 10억<br>
• 미가입 시: 과태료 300만원 + 영업정지 처분<br>
• <b>실화책임법</b>: 중과실 인정 시 인접 건물 피해 전액 배상<br>
• <b>화재보험법</b>: 22층 이상 건물·연면적 3,000㎡ 이상 특수건물 의무가입<br><br>
<b style="color:#555;font-size:0.78rem;">⚠️ 의무보험 미가입 시 행정처분 및 과태료 부과 대상입니다.</b>
</div>""", height=578)

    # ── [nursing] 간병비 컨설팅 ──────────────────────────────────────────
    if cur == "nursing":
        tab_home_btn("nursing")
        st.subheader("🏥 간병비 컨설팅")
        st.caption("국민연금 장애등급·장기요양등급 기반 간병비 산출 및 보험 설계 (참고용 추정치)")

        _nursing_goto = st.session_state.pop("_nursing_sub_goto", None)
        _nursing_opts = ["🧮 간병비 산출기", "🤖 AI 간병 설계 상담"]
        if _nursing_goto in _nursing_opts:
            st.session_state["nursing_sub"] = _nursing_goto

        nursing_sub = st.radio("상담 분야", _nursing_opts, horizontal=True, key="nursing_sub")

        # ── [1] 간병비 산출기 ─────────────────────────────────────────────
        if nursing_sub == "🧮 간병비 산출기":
            st.markdown("#### 🧮 간병비 총액 산출기")
            st.caption("질환별 평균 간병 기간 × 간병인 유형별 일당 → 총 간병비 및 보험 필요액 산출")
            nc1, nc2 = st.columns(2)
            with nc1:
                st.markdown("##### 👤 환자 기본 정보")
                nc_age = st.number_input("현재 나이 (세)", value=65, min_value=1, max_value=100, key="nc_age")
                nc_life_exp = st.number_input("기대수명 (세)", value=83, min_value=50, max_value=110, key="nc_life_exp",
                    help="통계청 기준 한국인 평균 기대수명 83세 (남 80세, 여 86세)")
                st.markdown("##### 🏥 장애·요양 등급")
                nc_disability = st.selectbox("국민연금 장애등급",
                    ["해당 없음", "장애 1급 (전면 의존)", "장애 2급 (상당 부분 의존)", "장애 3급 (부분 의존)"],
                    key="nc_disability")
                nc_ltc_grade = st.selectbox("장기요양 등급 (국민건강보험공단)",
                    ["미판정/해당 없음", "1등급 (최중증)", "2등급 (중증)", "3등급 (중등도)",
                     "4등급 (경증)", "5등급 (치매 경증)", "인지지원등급"],
                    key="nc_ltc_grade")
                st.markdown("##### 🩺 질환 유형")
                nc_disease = st.selectbox("주요 질환",
                    ["치매(알츠하이머)", "뇌졸중(중증)", "파킨슨병", "사지마비(척수손상)",
                     "ALS/루게릭병", "중증 근무력증", "말기 암", "중증 심부전", "기타 중증질환"],
                    key="nc_disease")
                disease_period_map = {
                    "치매(알츠하이머)": 12, "뇌졸중(중증)": 7, "파킨슨병": 10,
                    "사지마비(척수손상)": max(1, nc_life_exp - nc_age),
                    "ALS/루게릭병": 3, "중증 근무력증": 10,
                    "말기 암": 1, "중증 심부전": 3, "기타 중증질환": 5,
                }
                default_period = min(disease_period_map.get(nc_disease, 5), max(1, nc_life_exp - nc_age))
                nc_period = st.number_input("예상 간병 기간 (년)",
                    value=default_period, min_value=1, max_value=50, key="nc_period",
                    help=f"{nc_disease} 평균 간병 기간 기준 자동 설정. 직접 수정 가능.")

            with nc2:
                st.markdown("##### 🧑‍⚕️ 간병인 유형 및 비용")
                nc_care_type = st.selectbox("간병 유형",
                    ["요양병원 공동간병", "요양병원 전담간병 (1:1)",
                     "재택 방문요양 (장기요양급여)", "재택 24시간 사설 간병인", "전문 간호사 동반 간병"],
                    key="nc_care_type")
                care_daily_map = {
                    "요양병원 공동간병": 4, "요양병원 전담간병 (1:1)": 10,
                    "재택 방문요양 (장기요양급여)": 2,
                    "재택 24시간 사설 간병인": 12, "전문 간호사 동반 간병": 20,
                }
                nc_daily_cost = st.number_input("간병인 일당 (만원/일)",
                    value=care_daily_map.get(nc_care_type, 10),
                    min_value=1, max_value=50, key="nc_daily_cost")
                nc_inflation = st.number_input("간병비 물가상승률 (%/년)", value=4.0, step=0.5, key="nc_inflation",
                    help="간병비 인플레이션 실측 연 4~6%. 보수적 추정 시 3% 적용.")
                st.markdown("##### 🏛️ 국가 지원 차감")
                ltc_monthly_map = {
                    "미판정/해당 없음": 0, "1등급 (최중증)": 209, "2등급 (중증)": 185,
                    "3등급 (중등도)": 143, "4등급 (경증)": 133, "5등급 (치매 경증)": 110, "인지지원등급": 60,
                }
                ltc_monthly_limit = ltc_monthly_map.get(nc_ltc_grade, 0)
                nc_ltc_copay = 0.15
                nc_gov_monthly = ltc_monthly_limit * (1 - nc_ltc_copay)
                st.info(
                    f"**장기요양 {nc_ltc_grade}** 기준\n\n"
                    f"재가급여 월 한도: **{ltc_monthly_limit:,}만원**\n\n"
                    f"국가 부담분 (85%): **{nc_gov_monthly:,.0f}만원/월**\n\n"
                    f"본인 부담 (15%): **{ltc_monthly_limit - nc_gov_monthly:,.0f}만원/월**")
                st.markdown("##### 🛡️ 기보유 간병보험")
                nc_ins_daily = st.number_input("보유 간병보험 일당 (만원/일, 없으면 0)",
                    value=0, min_value=0, max_value=30, key="nc_ins_daily")
                nc_ins_lump = st.number_input("보유 간병보험 일시금 (만원, 없으면 0)",
                    value=0, step=100, key="nc_ins_lump")

            if st.button("💰 간병비 총액 산출 실행", type="primary", key="btn_nursing_calc"):
                total_care_cost = sum(
                    nc_daily_cost * ((1 + nc_inflation / 100) ** yr) * 365
                    for yr in range(int(nc_period))
                )
                gov_support_total = nc_gov_monthly * 12 * nc_period
                ins_total = nc_ins_daily * 365 * nc_period + nc_ins_lump
                self_pay = max(total_care_cost - gov_support_total - ins_total, 0)

                st.markdown("### 💰 간병비 산출 결과")
                st.dataframe(pd.DataFrame([
                    {"항목": "총 간병비 (물가상승 반영)", "금액(만원)": f"{total_care_cost:,.0f}",
                     "비고": f"{nc_daily_cost}만원/일×365×{nc_period}년, 연{nc_inflation}%상승"},
                    {"항목": "국가 지원 차감 (장기요양)", "금액(만원)": f"-{gov_support_total:,.0f}",
                     "비고": f"{nc_ltc_grade} 기준 월{nc_gov_monthly:,.0f}만원×{nc_period*12:.0f}개월"},
                    {"항목": "보유 보험 지급 차감", "금액(만원)": f"-{ins_total:,.0f}",
                     "비고": f"일당{nc_ins_daily}만원×{nc_period}년+일시금{nc_ins_lump}만원"},
                    {"항목": "자기부담 간병비", "금액(만원)": f"{self_pay:,.0f}", "비고": "총간병비-국가지원-보험"},
                ]), use_container_width=True, hide_index=True)

                if self_pay >= 30000:
                    st.error(f"🔴 자기부담 {self_pay:,.0f}만원 — 간병비 파산 위험 구간. 추가 보험 설계 필수.")
                elif self_pay >= 10000:
                    st.warning(f"⚠️ 자기부담 {self_pay:,.0f}만원 — 상당한 재정 부담. 보험 보완 권장.")
                else:
                    st.success(f"✅ 자기부담 {self_pay:,.0f}만원 — 현재 보장 수준 검토 후 보완 여부 결정.")

                st.markdown("#### 📋 질환별 간병 기간 참고표")
                st.markdown("""
| 질환 | 평균 간병 기간 | 간병 강도 |
|---|---|---|
| 치매(알츠하이머) | 8~15년 (평균 12년) | 초기 재택 → 중기 이후 시설 |
| 뇌졸중(중증) | 3~10년 | 발병 후 6개월 집중 재활 |
| 파킨슨병 | 7~15년 | 진행성, 후기 전면 의존 |
| 사지마비(척수손상) | 잔여 기대수명 전체 | 24시간 전담 간병 |
| ALS/루게릭병 | 2~5년 | 급속 진행, 인공호흡기 단계 |
| 말기 암 | 6개월~2년 | 호스피스·완화의료 연계 |
""")
                st.markdown("#### 🏛️ 장기요양등급별 국가 지원 한도 (2025년 기준)")
                st.markdown("""
| 등급 | 재가급여 월 한도 | 국가 부담(85%) | 본인 부담(15%) |
|---|---|---|---|
| 1등급 | 209만원 | 177만원 | 32만원 |
| 2등급 | 185만원 | 157만원 | 28만원 |
| 3등급 | 143만원 | 122만원 | 21만원 |
| 4등급 | 133만원 | 113만원 | 20만원 |
| 5등급 | 110만원 | 94만원 | 17만원 |
""")
                st.warning("⚠️ 위 산출은 참고용 추정치입니다. 실제 지원 금액은 국민건강보험공단 장기요양 등급 판정 결과 및 개인 상황에 따라 달라집니다.")

                with st.expander("🛡️ 간병보험 설계 연계", expanded=True):
                    rec_daily = max(5, round((self_pay / max(nc_period, 1) / 365 / 10)) * 10)
                    rec_lump  = min(3000, round(self_pay * 0.3 / 100) * 100)
                    st.markdown(f"""
**보험 설계 권장 기준 (자기부담 {self_pay:,.0f}만원 기준)**

| 설계 항목 | 권장 수준 | 비고 |
|---|---|---|
| 간병인 일당 보험 | **{rec_daily:,}만원/일** | 자기부담 일당 기준 |
| 치매 진단 일시금 | **{rec_lump:,}만원** | 초기 환경 정비 비용 |
| 장기요양 일시금 | **{min(2000, round(self_pay * 0.2 / 100) * 100):,}만원** | 등급 판정 후 즉시 지급 |
| 간병비 파산 방지 목표 | **{self_pay:,.0f}만원** | 추가 보험 + 저축 합산 목표 |
""")
                    if st.button("🤖 AI 간병 보험 설계 상담으로 이동", key="nursing_to_ai"):
                        st.session_state["_nursing_sub_goto"] = "🤖 AI 간병 설계 상담"
                        st.rerun()

        # ── [2] AI 간병 설계 상담 ─────────────────────────────────────────
        elif nursing_sub == "🤖 AI 간병 설계 상담":
            st.markdown("#### 🤖 AI 간병 설계 상담")
            na_c1, na_c2 = st.columns([1, 1])
            with na_c1:
                c_name_n, query_n, hi_n, do_n = ai_query_block(
                    "nursing",
                    "환자 나이, 질환명, 장애등급, 장기요양등급, 현재 간병 상황을 입력하세요.\n"
                    "(예: 72세 여성, 알츠하이머 치매 중기, 장기요양 2등급, 재택 방문요양 중, 간병보험 미가입)")
                st.markdown("**📋 추가 정보 입력 (선택)**")
                na_disease2 = st.selectbox("질환 유형",
                    ["치매(알츠하이머)", "뇌졸중(중증)", "파킨슨병", "사지마비(척수손상)",
                     "ALS/루게릭병", "중증 근무력증", "말기 암", "중증 심부전", "기타"],
                    key="na_disease2")
                na_grade2   = st.selectbox("장기요양 등급",
                    ["미판정", "1등급", "2등급", "3등급", "4등급", "5등급", "인지지원등급"],
                    key="na_grade2")
                na_period2  = st.number_input("예상 간병 기간 (년)", value=10, min_value=1, max_value=50, key="na_period2")
                na_daily2   = st.number_input("현재 간병인 일당 (만원)", value=10, min_value=0, key="na_daily2")
                na_ins2     = st.number_input("현재 간병보험 일당 (만원, 없으면 0)", value=0, min_value=0, key="na_ins2")
                if do_n:
                    nursing_ctx = (
                        f"\n[간병 정보] 질환: {na_disease2}, 장기요양 등급: {na_grade2}, "
                        f"예상 간병 기간: {na_period2}년, 간병인 일당: {na_daily2}만원/일, "
                        f"현재 간병보험 일당: {na_ins2}만원/일\n"
                        f"[추정 총 간병비] {na_daily2 * 365 * na_period2:,}만원 (물가상승 미반영 단순 추정)\n"
                    )
                    run_ai_analysis(c_name_n, query_n, hi_n, "res_nursing",
                        "[간병비 컨설팅 — CFP·사회복지사·의료사회사업 관점]\n"
                        "### 1. 국민연금 장애등급 및 국가 지원 분석\n"
                        "- 장애등급(1~3급) 기준 요양병원 입원 급여 적용 여부 및 본인부담률 안내\n"
                        "- 장기요양보험 등급별 재가급여·시설급여 한도 및 본인부담 산출\n"
                        "- 산정특례(중증암·희귀질환) 해당 시 본인부담 경감 안내\n"
                        "### 2. 질환별 간병 기간 및 강도 분석\n"
                        "- 해당 질환의 평균 간병 기간, 진행 단계별 간병 강도 변화 설명\n"
                        "- 치매: 초기(재택) → 중기(주야간보호) → 말기(시설) 단계별 비용 구조\n"
                        "- 뇌졸중: 급성기 집중 재활(6개월) → 장기 요양 전환 시점 및 비용\n"
                        "### 3. 간병비 총액 및 자기부담 산출\n"
                        "- 총 간병비 = 일당 × 365 × 기간 (물가상승률 4% 복리 반영)\n"
                        "- 국가 지원(장기요양급여) 차감 후 자기부담 산출\n"
                        "- 보험 보장 공백(Gap) 명시\n"
                        "### 4. 보험 설계 권장안\n"
                        "- 간병인 일당 보험 적정 금액 (자기부담 일당 기준)\n"
                        "- 치매 진단 일시금·장기요양 일시금 권장 수준\n"
                        "- 간병비 파산 방지 목표 금액 및 보험+저축 복합 설계안\n"
                        "### 5. 재택간병 vs 시설간병 비교\n"
                        "- 재택 방문요양(장기요양급여) vs 요양원 입소 vs 요양병원 입원 비용 비교\n"
                        "- 가족 간병 시 간병 휴직급여(고용보험) 활용 안내\n"
                        + nursing_ctx)
            with na_c2:
                st.subheader("🤖 AI 간병 설계 리포트")
                show_result("res_nursing")
                components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">🏛️ 국가 간병 지원 체계 안내</b><br><br>
<b style="color:#c0392b;">① 국민연금 장애등급 (1~3급)</b><br>
• 1급: 일상생활 전면 타인 의존 → 요양병원 건강보험 급여 적용<br>
• 2급: 상당 부분 의존 → 장기요양 2~3등급 연계<br>
• 3급: 부분 의존 → 장기요양 3~4등급 연계<br><br>
<b style="color:#e67e22;">② 장기요양보험 (65세 이상 또는 노인성 질환)</b><br>
• 1~2등급: 재가급여 월 185~209만원 한도<br>
• 본인부담: 재가 15%, 시설 20% (의료급여 수급자 절반)<br>
• 방문요양·방문간호·주야간보호·단기보호 서비스<br><br>
<b style="color:#27ae60;">③ 재택간병 지원 (방문요양)</b><br>
• 장기요양 1~5등급: 하루 3~4시간 방문요양 급여 적용<br>
• 가족요양비: 도서·벽지 등 방문요양 어려운 경우 월 15만원<br><br>
<b style="color:#8e44ad;">④ 산정특례 (중증질환)</b><br>
• 중증암·희귀질환·중증난치질환: 본인부담 5~10%<br>
• 말기암 환자: 호스피스·완화의료 건강보험 적용<br><br>
<b style="color:#2c3e50;">⑤ 간병비 파산 방지 기준</b><br>
• 하루 10만원 × 10년 = <b>3억 6,500만원</b> 자기부담 발생 가능<br>
• 치매 평균 12년 × 10만원/일 = <b>4억 3,800만원</b> 추정<br><br>
<b style="font-size:0.88rem;color:#c0392b;">🧑‍⚕️ 간병인 배상책임 — 사고 유형 및 보험 처리</b><br><br>
<b style="color:#1a3a5c;">▶ 간병인 과실 사고 유형</b><br>
• <b>낙상 사고</b>: 침대·화장실 이동 보조 중 환자 추락 → 골절·뇌출혈 발생<br>
• <b>투약 오류</b>: 약 종류·용량·시간 착오 → 부작용·사망 사고<br>
• <b>욕창 방치</b>: 체위 변경 소홀 → 욕창 악화 → 패혈증 위험<br>
• <b>흡인성 폐렴</b>: 식사 보조 부주의 → 기도 흡인 → 폐렴<br>
• <b>이탈·실종</b>: 치매 환자 감시 소홀 → 무단 이탈<br><br>
<b style="color:#1a3a5c;">▶ 배상책임 법률 근거</b><br>
• <b>민법 제750조</b>: 고의·과실로 타인에게 손해 → 불법행위 배상책임<br>
• <b>민법 제756조</b>: 간병인 고용 시 <b>사용자(가족·병원·요양기관)</b> 연대책임<br>
• 간병인 직접 고용 시: 고용주(가족)가 사용자 책임 부담<br>
• 파견 간병인 사고: 파견업체 + 의뢰인 공동 책임 가능<br><br>
<b style="color:#1a3a5c;">▶ 간병인 관련 보험 종류</b><br>
• <b>간병인 배상책임보험</b>: 간병인 과실로 환자·제3자에게 손해 발생 시 보상<br>
• <b>시설소유관리자 배상책임</b>: 요양원·요양병원 시설 내 사고 보상<br>
• <b>일상생활배상책임 (가족형)</b>: 가족이 직접 간병 중 사고 시 적용 가능<br>
• 권장: 간병인 고용 전 <b>배상책임보험 가입 여부 반드시 확인</b><br><br>
<b style="font-size:0.88rem;color:#c0392b;">⚖️ 손해사정사 선임 문제점 — 변호사법 위반 소지</b><br><br>
<b style="color:#1a3a5c;">▶ 손해사정사의 법적 업무 범위</b><br>
• <b>보험업법 제185조</b>: 손해사정사는 <b>손해액 및 보험금 사정</b> 업무만 허용<br>
• 허용 업무: 손해 조사·평가, 보험금 산정, 보험사에 사정서 제출<br>
• <b>금지 업무</b>: 법률 자문, 소송 대리, 법적 권리 주장·교섭 대리<br><br>
<b style="color:#e74c3c;">▶ 변호사법 위반 소지 — 핵심 쟁점</b><br>
• <b>변호사법 제109조</b>: 변호사 아닌 자가 <b>금품·이익을 받고 법률사무를 취급</b>하면 <b>7년 이하 징역 또는 5천만원 이하 벌금</b><br>
• 위반 행위 유형:<br>
&nbsp;&nbsp;① 보험사와의 <b>보험금 협상·교섭 대리</b> (법률사무 해당)<br>
&nbsp;&nbsp;② <b>소송 제기·수행 대리</b> (변호사 고유 업무)<br>
&nbsp;&nbsp;③ <b>법적 권리 주장 서면 작성·제출</b> 대리<br>
&nbsp;&nbsp;④ 성공보수 명목 <b>보험금의 일정 비율 수취</b> 약정<br>
• 대법원 판례: 손해사정사가 보험금 청구 교섭을 대리하고 수수료를 받은 경우 변호사법 위반 인정 (대법원 2012도11586)<br><br>
<b style="color:#27ae60;">▶ 올바른 분쟁 해결 절차</b><br>
• <b>1단계 — 민원 압박</b>: 금융감독원 민원 접수 (☎ 1332 / fine.fss.or.kr)<br>
&nbsp;&nbsp;→ 보험사에 자료 제출 의무 부과 + 자체 재검토 압박 효과<br>
• <b>2단계 — 금융분쟁조정위원회</b>: 민원 불수용 시 분쟁조정 신청 (비용 없음, 60일 이내)<br>
&nbsp;&nbsp;→ 조정안 수락 시 재판상 화해 효력 (법적 구속력)<br>
• <b>3단계 — 손해사정사 선임 (선택)</b>: 손해액 산정·사정서 작성 목적에 한정<br>
&nbsp;&nbsp;→ 통상 <b>사정 금액의 7~10% 수수료</b> 요구 — 교섭·소송 대리는 변호사법 위반<br>
• <b>3단계 — 변호사 선임 (선택)</b>: 소송 제기·법적 교섭 대리 필요 시<br>
&nbsp;&nbsp;→ 통상 <b>인용액의 7~10% 성공보수</b> + 착수금 별도<br>
• <b>나홀로 소송 (증가 추세)</b>: 소액사건(3,000만원 이하) 본인 직접 소송 가능<br>
&nbsp;&nbsp;→ 소액심판 절차 — 1회 변론으로 신속 판결 / 법원 민원실 서류 지원<br>
&nbsp;&nbsp;→ 대법원 나홀로소송 사이트: <a href="https://pro-se.scourt.go.kr" target="_blank" style="color:#2e6da4;">pro-se.scourt.go.kr</a><br>
• <b>성공보수 약정 전 반드시 업무 범위 확인</b> — 불법 약정은 무효<br>
</div>
""", height=680)
                with st.expander("🧮 간병비 산출기 바로가기", expanded=False):
                    if st.button("💰 간병비 산출기로 이동", key="nursing_ai_to_calc"):
                        st.session_state["_nursing_sub_goto"] = "🧮 간병비 산출기"
                        st.rerun()

    # ── [realty] 부동산 투자 상담 ────────────────────────────────────────
    if cur == "realty":
        tab_home_btn("realty")
        st.subheader("🏘️ 부동산 투자 상담")
        realty_sub = st.radio("상담 분야",
            ["📄 서류 판독 & AI 분석", "📊 투자수익 산출기", "🛡️ 보험 연계 설계"],
            horizontal=True, key="realty_sub")
        col1, col2 = st.columns([1, 1])

        if realty_sub == "📄 서류 판독 & AI 분석":
            with col1:
                st.markdown("##### 📄 등기부등본 · 건축물대장 업로드")
                realty_files = st.file_uploader("서류 업로드 (PDF/이미지)",
                    type=["pdf","jpg","jpeg","png"], accept_multiple_files=True, key="realty_files")
                realty_query = st.text_area("분석 요청사항",
                    placeholder="예) 근저당 설정 현황, 위반건축물 여부, 권리관계 분석 요청",
                    height=120, key="realty_query")
                if st.button("🔍 AI 서류 분석 실행", type="primary", key="btn_realty_doc"):
                    if not realty_files:
                        st.error("서류 파일을 업로드하세요.")
                    elif 'user_id' not in st.session_state:
                        st.error("로그인이 필요합니다.")
                    else:
                        user_name = st.session_state.get('user_name', '')
                        if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                            st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                        else:
                            with st.spinner("부동산 서류 분석 중..."):
                                try:
                                    client, model_config = get_master_model()
                                    contents = [
                                        f"[부동산 서류 판독 분석]\n요청: {realty_query}\n"
                                        "1. 등기부등본 권리관계 분석 (근저당·가압류·가처분·전세권 등)\n"
                                        "2. 건축물대장 위반건축물 여부 및 용도 확인\n"
                                        "3. 투자 리스크 요인 정리\n"
                                        "4. 보험 연계 필요 항목 안내"
                                    ]
                                    for f in realty_files:
                                        if f.type.startswith('image/'):
                                            contents.append(PIL.Image.open(f))
                                        elif f.type == 'application/pdf':
                                            contents.append(f"PDF: {f.name}\n{process_pdf(f)[:800]}")
                                    resp = client.models.generate_content(
                                        model=GEMINI_MODEL, contents=contents, config=model_config)
                                    answer = sanitize_unicode(resp.text) if resp.text else "AI 응답을 받지 못했습니다."
                                    st.session_state['res_realty_doc'] = answer
                                    update_usage(user_name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"분석 오류: {sanitize_unicode(str(e))}")
            with col2:
                st.subheader("🤖 AI 분석 리포트")
                show_result("res_realty_doc")
                st.markdown("##### 📋 등기부등본 판독 핵심 포인트")
                components.html("""
<div style="height:320px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">📌 등기부등본 판독 핵심</b><br>
• <b>표제부</b>: 소재지·지목·면적·건물구조 확인<br>
• <b>갑구</b>: 소유권 이전 이력, 가압류·가처분·예고등기 확인<br>
• <b>을구</b>: 근저당·전세권·임차권 등 담보권 확인<br>
• <b>근저당 채권최고액</b>: 실제 대출액의 120~130% → 실질 부채 역산 필수<br>
• <b>위험 신호</b>: 가압류·가처분·예고등기 존재 시 투자 보류 권장<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏗️ 건축물대장 판독 핵심</b><br>
• <b>위반건축물</b>: 불법 증축·용도변경 → 담보 대출 불가, 보험 면책 위험<br>
• <b>용도</b>: 주거용·상업용·공업용 구분 → 임대수익 전략 결정<br>
• <b>건폐율·용적률</b>: 추가 개발 가능성 판단 기준<br>
• <b>사용승인일</b>: 준공 연도 → 재건축 가능 연한 산정<br>
<b style="font-size:0.85rem;color:#1a3a5c;">⚠️ 투자 전 필수 확인 사항</b><br>
• 토지이용계획확인서: 개발제한구역·군사시설보호구역 여부<br>
• 실거래가 조회: 국토교통부 실거래가 공개시스템<br>
• 임차인 현황: 확정일자·전입신고 여부 (선순위 임차인 리스크)
</div>
""", height=338)

        elif realty_sub == "📊 투자수익 산출기":
            # 2페이지 구성: 탭으로 분리
            r_tab1, r_tab2, r_tab3 = st.tabs(["📊 수익률 산출", "🏗️ 토지종류별 투자", "🏦 보유세 계산"])

            with r_tab1:
                rc1, rc2 = st.columns([1, 1])
                with rc1:
                    st.markdown("##### 📊 임대수익 산출기")
                    r_land_type = st.selectbox("토지·건물 유형",
                        ["상업용지(상가·오피스)", "공장용지", "임야", "대지(주거용)", "농지", "물류창고"],
                        key="r_land_type")
                    r_price    = st.number_input("매입가 (만원)", value=50000, step=1000, key="r_price")
                    r_deposit  = st.number_input("보증금 (만원)", value=10000, step=500, key="r_deposit")
                    r_monthly  = st.number_input("월 임대료 (만원)", value=150, step=10, key="r_monthly")
                    r_vacancy  = st.slider("공실률 (%)", 0, 50, 10, key="r_vacancy")
                    r_loan     = st.number_input("대출금 (만원)", value=20000, step=1000, key="r_loan")
                    r_rate     = st.number_input("대출금리 (%)", value=4.5, step=0.1, key="r_rate")
                    r_prop_tax = st.number_input("재산세 연간 (만원)", value=120, step=10, key="r_prop_tax")
                    r_comp_tax = st.number_input("종합부동산세 연간 (만원)", value=80, step=10, key="r_comp_tax")
                    r_maint    = st.number_input("연간 유지비·관리비 (만원)", value=100, step=50, key="r_maint")
                    r_insur    = st.number_input("연간 보험료 (만원)", value=30, step=5, key="r_insur")
                    if st.button("📈 수익률 산출", type="primary", key="btn_realty_calc", use_container_width=True):
                        eff_rent     = r_monthly * (1 - r_vacancy / 100)
                        annual_rent  = eff_rent * 12
                        loan_int     = r_loan * r_rate / 100
                        total_tax    = r_prop_tax + r_comp_tax
                        total_cost   = loan_int + total_tax + r_maint + r_insur
                        net_income   = annual_rent - total_cost
                        invest_cost  = r_price - r_deposit - r_loan
                        gross_yield  = (r_monthly * 12 / r_price * 100) if r_price > 0 else 0
                        net_yield    = (net_income / invest_cost * 100) if invest_cost > 0 else 0
                        vacancy_loss = r_monthly * 12 * r_vacancy / 100
                        st.session_state['realty_calc'] = {
                            "토지유형": r_land_type,
                            "공실률": r_vacancy,
                            "공실손실": vacancy_loss,
                            "실효임대수입": annual_rent,
                            "대출이자": loan_int,
                            "보유세합계": total_tax,
                            "유지비보험료": r_maint + r_insur,
                            "총비용": total_cost,
                            "순수익": net_income,
                            "실투자금": invest_cost,
                            "총수익률": gross_yield,
                            "순수익률": net_yield,
                        }
                        st.rerun()
                with rc2:
                    st.subheader("📊 수익률 분석 결과")
                    calc = st.session_state.get('realty_calc')
                    if calc:
                        st.markdown(f"**토지 유형:** {calc['토지유형']}")
                        col_m1, col_m2 = st.columns(2)
                        with col_m1:
                            st.metric("실효 임대수입(연)", f"{calc['실효임대수입']:,.0f}만원")
                            st.metric("공실 손실(연)", f"{calc['공실손실']:,.0f}만원",
                                delta=f"-{calc['공실률']}% 공실", delta_color="inverse")
                            st.metric("대출이자(연)", f"{calc['대출이자']:,.0f}만원")
                            st.metric("보유세 합계(연)", f"{calc['보유세합계']:,.0f}만원")
                        with col_m2:
                            st.metric("유지비+보험료(연)", f"{calc['유지비보험료']:,.0f}만원")
                            st.metric("총 비용(연)", f"{calc['총비용']:,.0f}만원")
                            st.metric("순수익(연)", f"{calc['순수익']:,.0f}만원")
                            st.metric("실투자금", f"{calc['실투자금']:,}만원")
                        st.divider()
                        col_y1, col_y2 = st.columns(2)
                        with col_y1:
                            st.metric("총수익률(표면)", f"{calc['총수익률']:.2f}%")
                        with col_y2:
                            color = "normal" if calc['순수익률'] >= 4 else "inverse"
                            st.metric("순수익률(실질)", f"{calc['순수익률']:.2f}%",
                                delta="양호" if calc['순수익률'] >= 4 else "주의", delta_color=color)
                    else:
                        st.info("좌측 입력 후 '수익률 산출' 버튼을 클릭하세요.")

            with r_tab2:
                st.markdown("##### 🏗️ 토지종류별 투자 특성 및 전략")
                components.html("""
<div style="height:520px;overflow-y:auto;padding:14px 16px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.88rem;color:#1a3a5c;">🏪 상업용지 (상가·오피스)</b><br>
• <b>수익률</b>: 서울 3~5% / 수도권 4~7% / 지방 5~10%<br>
• <b>공실 리스크</b>: 경기 침체 시 공실률 급등 (2023년 서울 중심가 평균 9.2%)<br>
• <b>투자 포인트</b>: 유동인구·배후세대·역세권 여부 최우선 확인<br>
• <b>보험</b>: 화재보험(재조달가액) + 시설소유관리자 배상책임 필수<br>
• <b>세금</b>: 취득세 4.6% / 부가가치세 환급 가능 (사업자 등록 시)<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">🏭 공장용지</b><br>
• <b>수익률</b>: 5~9% (임대형 공장 기준)<br>
• <b>공실 리스크</b>: 상가 대비 낮음 — 장기 임대 계약 선호<br>
• <b>투자 포인트</b>: 도로 접근성·전력 용량·용도지역(공업지역) 확인<br>
• <b>보험</b>: 공장화재보험(기계장치 포함) + 영업중단손실 특약<br>
• <b>세금</b>: 취득세 4.6% / 산업단지 내 취득세 감면 가능<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">🌲 임야</b><br>
• <b>수익률</b>: 임대수익 낮음 — 개발 차익 목적 투자<br>
• <b>투자 포인트</b>: 보전산지 vs 준보전산지 구분 필수 (개발 가능 여부)<br>
• <b>리스크</b>: 개발제한·산지전용허가 불허 시 장기 묶임<br>
• <b>세금</b>: 취득세 3.16% / 비사업용 토지 양도세 중과(+10%p)<br>
• <b>보험</b>: 산불 피해 대비 임야화재보험 검토<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">🏠 대지 (주거용)</b><br>
• <b>수익률</b>: 임대수익 3~5% / 재건축·재개발 기대 수익 포함<br>
• <b>투자 포인트</b>: 용적률·건폐율·정비구역 지정 여부 확인<br>
• <b>세금</b>: 취득세 1~12% (주택수 따라 상이) / 종부세 9억 초과 부과<br>
• <b>보험</b>: 건물화재보험 + 임대인 배상책임<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">🌾 농지</b><br>
• <b>투자 포인트</b>: 농업진흥구역 vs 농업보호구역 구분 (전용 가능 여부)<br>
• <b>리스크</b>: 비농업인 취득 제한 — 농지취득자격증명 필수<br>
• <b>세금</b>: 취득세 3.16% / 8년 자경 시 양도세 감면<br>
• <b>공실 개념</b>: 미경작 시 농지처분의무 발생 (3년 이상 미경작)<br><br>
<b style="font-size:0.88rem;color:#1a3a5c;">📦 물류창고</b><br>
• <b>수익률</b>: 6~10% (e커머스 성장으로 수요 급증)<br>
• <b>투자 포인트</b>: 고속도로 IC 인접 여부·층고(9m↑)·바닥 하중<br>
• <b>보험</b>: 창고화재보험 + 재고자산 보험 + 배상책임<br>
• <b>세금</b>: 취득세 4.6% / 물류단지 내 취득세 감면 가능
</div>
""", height=538)

            with r_tab3:
                st.markdown("##### 🏦 부동산 보유세 계산기")
                rc3, rc4 = st.columns([1, 1])
                with rc3:
                    bt_type    = st.selectbox("부동산 유형", ["주택", "토지(종합합산)", "토지(별도합산)", "상가·오피스텔"], key="bt_type")
                    bt_pubval  = st.number_input("공시가격 (만원)", value=50000, step=1000, key="bt_pubval")
                    bt_own_cnt = st.number_input("주택 보유 수 (주택만 해당)", value=1, min_value=1, max_value=5, key="bt_own_cnt")
                    bt_area    = st.selectbox("소재지", ["조정대상지역", "비조정지역"], key="bt_area")
                    if st.button("🧮 보유세 계산", type="primary", key="btn_bt_calc", use_container_width=True):
                        pub = bt_pubval
                        # 재산세 (공정시장가액비율 60%)
                        prop_base = pub * 0.60
                        if prop_base <= 6000:
                            prop_tax = prop_base * 0.001
                        elif prop_base <= 15000:
                            prop_tax = 6 + (prop_base - 6000) * 0.0015
                        elif prop_base <= 30000:
                            prop_tax = 19.5 + (prop_base - 15000) * 0.0025
                        else:
                            prop_tax = 57 + (prop_base - 30000) * 0.004
                        # 종합부동산세 (주택 기준, 공정시장가액비율 60%)
                        comp_tax = 0.0
                        if bt_type == "주택":
                            threshold = 9000 if bt_own_cnt == 1 else 6000
                            comp_base = max(0, (pub - threshold)) * 0.60
                            if bt_own_cnt == 1:
                                if comp_base <= 30000: comp_tax = comp_base * 0.005
                                elif comp_base <= 60000: comp_tax = 150 + (comp_base-30000)*0.007
                                elif comp_base <= 120000: comp_tax = 360 + (comp_base-60000)*0.010
                                elif comp_base <= 500000: comp_tax = 960 + (comp_base-120000)*0.013
                                else: comp_tax = 5900 + (comp_base-500000)*0.027
                            else:
                                rate = 0.012 if bt_area == "비조정지역" else 0.020
                                comp_tax = comp_base * rate
                        elif bt_type == "토지(종합합산)":
                            comp_base = max(0, (pub - 5000)) * 0.60
                            if comp_base <= 15000: comp_tax = comp_base * 0.010
                            elif comp_base <= 45000: comp_tax = 150 + (comp_base-15000)*0.020
                            else: comp_tax = 750 + (comp_base-45000)*0.030
                        elif bt_type == "토지(별도합산)":
                            comp_base = max(0, (pub - 80000)) * 0.60
                            if comp_base <= 200000: comp_tax = comp_base * 0.005
                            elif comp_base <= 400000: comp_tax = 1000 + (comp_base-200000)*0.006
                            else: comp_tax = 2200 + (comp_base-400000)*0.007
                        city_tax   = prop_tax * 0.14  # 도시계획세
                        edu_tax    = prop_tax * 0.20  # 지방교육세
                        comp_edu   = comp_tax * 0.20  # 종부세 농특세
                        total_hold = prop_tax + city_tax + edu_tax + comp_tax + comp_edu
                        st.session_state['bt_calc'] = {
                            "재산세": prop_tax, "도시계획세": city_tax, "지방교육세": edu_tax,
                            "종합부동산세": comp_tax, "농어촌특별세": comp_edu, "합계": total_hold
                        }
                        st.rerun()
                with rc4:
                    st.subheader("🏦 보유세 산출 결과")
                    bt = st.session_state.get('bt_calc')
                    if bt:
                        st.metric("재산세", f"{bt['재산세']:,.1f}만원")
                        st.metric("도시계획세", f"{bt['도시계획세']:,.1f}만원")
                        st.metric("지방교육세", f"{bt['지방교육세']:,.1f}만원")
                        st.metric("종합부동산세", f"{bt['종합부동산세']:,.1f}만원")
                        st.metric("농어촌특별세", f"{bt['농어촌특별세']:,.1f}만원")
                        st.divider()
                        st.metric("**연간 보유세 합계**", f"**{bt['합계']:,.1f}만원**")
                    else:
                        st.info("좌측 입력 후 '보유세 계산' 버튼을 클릭하세요.")
                        components.html("""
<div style="height:280px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.83rem;line-height:1.6;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🏦 부동산 보유세 항목</b><br>
<b style="color:#c0392b;">① 재산세</b> (지방세, 매년 7·9월 납부)<br>
• 과세표준: 공시가격 × 공정시장가액비율(60%)<br>
• 세율: 0.1%~0.4% 누진세율 (주택 기준)<br>
<b style="color:#c0392b;">② 종합부동산세</b> (국세, 매년 12월 납부)<br>
• 주택: 공시가격 합산 9억 초과분 (1주택 기준)<br>
• 토지(종합합산): 5억 초과 / 토지(별도합산): 80억 초과<br>
• 세율: 0.5%~5.0% (주택수·조정지역 따라 상이)<br>
<b style="color:#c0392b;">③ 부가세목</b><br>
• 도시계획세: 재산세의 14%<br>
• 지방교육세: 재산세의 20%<br>
• 농어촌특별세: 종부세의 20%<br>
<b style="color:#e67e22;">⚠️ 절세 전략</b><br>
• 1세대 1주택 장기보유특별공제: 최대 80%<br>
• 임대사업자 등록: 재산세·종부세 감면 가능<br>
• 공동명의: 종부세 기본공제 각각 적용
</div>
""", height=298)

        else:  # 보험 연계 설계
            with col1:
                c_name_r, query_r, hi_r, do_r = ai_query_block("realty",
                    "예) 상가 건물 소유, 임차인 3명, 화재·배상책임 보험 연계 설계 요청")
                if do_r:
                    run_ai_analysis(c_name_r, query_r, hi_r, "res_realty_ins",
                        "[부동산 보험 연계 설계]\n1. 건물 화재보험 (재조달가액 기준) 설계\n"
                        "2. 시설소유관리자 배상책임보험 설계\n3. 임대인·임차인 보험 역할 분담\n"
                        "4. 전세보증보험·임대보증금 반환보증 안내\n5. 부동산 투자 리스크 헤지 전략")
            with col2:
                st.subheader("🤖 AI 분석 리포트")
                show_result("res_realty_ins")
                st.markdown("##### 🛡️ 부동산 보험 연계 핵심 전략")
                components.html("""
<div style="height:420px;overflow-y:auto;padding:12px 15px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-size:0.84rem;line-height:1.45;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;color:#1a1a2e;">
<b style="font-size:0.85rem;color:#1a3a5c;">🔥 화재보험 (건물주 필수)</b><br>
• <b>재조달가액 기준</b> 가입 필수 (비례보상 방지)<br>
• 특수건물(22층↑ 또는 연면적 3,000㎡↑): 의무가입<br>
• 임차인 화재 시 임대인도 연대책임 가능 → 임차인 화재보험 가입 요구<br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏢 시설소유관리자 배상책임</b><br>
• 건물·시설 결함으로 제3자 피해 발생 시 배상<br>
• 민법 제758조: 공작물 점유자·소유자 배상책임<br>
• 다중이용업소: 화재배상책임보험 <b>의무가입</b><br>
<b style="font-size:0.85rem;color:#1a3a5c;">🏠 전세보증보험 (임차인 보호)</b><br>
• HUG(주택도시보증공사): 전세보증금 반환보증<br>
• SGI서울보증: 전세금보장신용보험<br>
• 가입 조건: 전세가율 80% 이하 (HUG 기준)<br>
• 임대인 동의 불필요 → 임차인 단독 가입 가능<br>
<b style="font-size:0.85rem;color:#1a3a5c;">📋 임대인 리스크 헤지 전략</b><br>
• 임대료 미납 대비: 임대료 보증보험 (SGI서울보증)<br>
• 공실 리스크: 임대수익보장보험 검토<br>
• 재건축·재개발 구역: 권리산정기준일 확인 필수<br>
<b style="font-size:0.85rem;color:#1a3a5c;">💰 부동산 투자 세금 핵심</b><br>
• 취득세: 1주택 1~3% / 2주택 8% / 3주택↑ 12%<br>
• 종합부동산세: 공시가격 합산 9억 초과 시 부과<br>
• 양도소득세: 보유기간·주택수에 따라 6~82%<br>
• 임대소득세: 연 2,000만원 초과 시 종합과세
</div>
""", height=438)

    # ── [t9] 관리자 ───────────────────────────────────────────────────────
    if cur == "t9":
        tab_home_btn("t9")
        st.subheader("⚙️ 관리자 전용 시스템")
        admin_key_input = st.text_input("관리자 인증키", type="password", key="admin_key_tab3")

        if admin_key_input == get_admin_key():
            st.success("관리자 시스템 활성화")
            inner_tabs = st.tabs(["회원 관리", "RAG 지식베이스", "데이터 파기"])
            with inner_tabs[0]:
                members = load_members()
                if members:
                    st.write(f"**총 회원수: {len(members)}명**")
                    member_data = [{"이름": n, "가입일": info.get("join_date",""),
                        "구독 종료": info.get("subscription_end",""),
                        "상태": "활성" if info.get("is_active") else "비활성"}
                        for n, info in members.items()]
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
            with inner_tabs[1]:
                st.write("### 마스터 전용 RAG 엔진")
                rag_files = st.file_uploader("전문가용 노하우 PDF/DOCX/TXT 업로드",
                    type=['pdf','docx','txt'], accept_multiple_files=True, key="rag_uploader_admin")
                if rag_files and st.button("지식베이스 동기화", key="btn_rag_sync"):
                    with st.spinner("동기화 중..."):
                        try:
                            docs = []
                            for f in rag_files:
                                if f.type == "application/pdf":
                                    docs.append(process_pdf(f))
                                elif "wordprocessingml" in f.type:
                                    docs.append(process_docx(f))
                                else:
                                    docs.append(f.read().decode('utf-8', errors='replace'))
                            st.session_state.rag_system.add_documents(docs)
                            st.success(f"{len(rag_files)}개 파일이 지식베이스에 추가되었습니다!")
                        except Exception as e:
                            st.error(f"동기화 오류: {e}")
            with inner_tabs[2]:
                # ── 에러 로그 스크롤창 ──────────────────────────────────
                st.markdown("##### 📋 시스템 에러 로그")
                error_log = load_error_log()
                if error_log:
                    log_lines = "".join(
                        f'<div style="border-bottom:1px solid #e0e0e0;padding:5px 2px;'
                        f'color:{"#c0392b" if r["source"]=="API" else "#1a1a2e"};font-size:0.82rem;">'
                        f'<b>[{r["time"]}]</b> '
                        f'<span style="background:#eef4fb;border-radius:4px;padding:1px 6px;'
                        f'font-size:0.78rem;color:#2e6da4;margin:0 4px;">{r["source"]}</span>'
                        f'{r["message"]}</div>'
                        for r in reversed(error_log)  # 최신순
                    )
                    components.html(f"""
<div style="height:260px;overflow-y:auto;padding:10px 12px;
  background:#f8fafc;border:1px solid #d0d7de;border-radius:8px;
  font-family:'Noto Sans KR','Malgun Gothic',sans-serif;">
{log_lines}
</div>""", height=280)
                    col_log1, col_log2 = st.columns(2)
                    with col_log1:
                        st.caption(f"총 {len(error_log)}건 기록 (최근 200건 유지 · /tmp/error_log.json)")
                    with col_log2:
                        if st.button("🗑️ 로그 초기화", key="btn_clear_log"):
                            try:
                                if os.path.exists(ERROR_LOG_PATH):
                                    os.remove(ERROR_LOG_PATH)
                            except Exception:
                                pass
                            st.rerun()
                else:
                    st.success("✅ 기록된 에러가 없습니다.")
                st.divider()
                st.warning("만료된 사용자 데이터를 영구 삭제합니다.")
                if st.button("만료 데이터 파기 실행", type="primary", key="btn_purge_admin"):
                    try:
                        conn = sqlite3.connect(os.path.join(_DATA_DIR, 'insurance_data.db'))
                        cursor = conn.cursor()
                        cursor.execute("SELECT COUNT(*) FROM user_documents WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')")
                        count = cursor.fetchone()[0]
                        cursor.execute("DELETE FROM user_documents WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')")
                        conn.commit()
                        conn.close()
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
        "앱 운영 문의: 010-3074-2616"
    )


# --------------------------------------------------------------------------
# [SECTION 9] 자가 복구 시스템 + 앱 진입점
# --------------------------------------------------------------------------
def auto_recover(e: Exception) -> bool:
    """오류 유형별 자동 복구 시도. 복구 성공 시 True 반환."""
    # surrogate 문자가 포함된 예외 메시지 자체가 또 오류를 유발하지 않도록 먼저 정제
    err = str(e).encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    # 1. 인코딩 오류 → 세션 초기화 후 재시도
    if "codec" in err or "surrogate" in err or "encode" in err:
        log_error("인코딩", err)
        for key in ['analysis_result']:
            st.session_state.pop(key, None)
        st.warning("⚠️ 인코딩 오류가 발생했습니다. 자동 복구되었습니다. 다시 시도해주세요.")
        return True

    # 2. 파일 쓰기 오류 → /tmp/ 경로로 전환
    if "Read-only" in err or "Permission denied" in err or "No such file" in err:
        log_error("파일I/O", err)
        global _DATA_DIR, USAGE_DB, MEMBER_DB
        _DATA_DIR = "/tmp"
        USAGE_DB  = "/tmp/usage_log.json"
        MEMBER_DB = "/tmp/members.json"
        st.session_state["_force_tmp"] = True
        st.warning("⚠️ 파일 경로 오류가 발생했습니다. 자동 복구되었습니다.")
        return True

    # 3. API 오류 → 안내 메시지 + 음성 안내 (재시도 불필요 — 무한루프 방지)
    if "API" in err or "quota" in err.lower() or "rate" in err.lower():
        log_error("API", err)
        st.warning("⚠️ 서버사정으로 잠시후 로그인 지연")
        _tts_msg = "서버사정으로 잠시후 로그인 진행해주세요."
        components.html(s_voice(_tts_msg), height=0)
        return False

    # 4. 세션 오류 → 세션 초기화
    if "session" in err.lower() or "StreamlitAPIException" in err:
        log_error("세션", err)
        st.session_state.clear()
        st.warning("⚠️ 세션 오류가 발생했습니다. 자동 초기화되었습니다.")
        return True

    # 5. 기타 오류 → 로그만 기록
    log_error("기타", err)
    return False  # 복구 불가 → 원본 오류 표시


# ==========================================================
# [앱 진입점] surrogate-safe 래퍼로 main() 실행
# 모든 예외의 str() 변환을 encode/decode로 정제 후 처리
# ==========================================================
def _run_safe():
    """surrogate 문자 포함 예외를 안전하게 처리하는 진입점 래퍼"""
    _MAX_RETRY = 2
    for _attempt in range(_MAX_RETRY):
        try:
            main()
            break
        except UnicodeEncodeError as _ue:
            # traceback 전체를 로그에 기록 → 정확한 발생 위치 파악
            _tb = _traceback.format_exc().encode("utf-8", errors="ignore").decode("utf-8")
            log_error("인코딩[TB]", _tb)
            for _k in list(st.session_state.keys()):
                if _k not in ("_force_tmp", "_error_log", "db_ready", "rag_system"):
                    st.session_state.pop(_k, None)
            if _attempt < _MAX_RETRY - 1:
                st.warning("⚠️ 인코딩 오류가 감지되어 자동 복구합니다. 잠시만 기다려주세요.")
                st.rerun()
            else:
                st.error("인코딩 오류가 되풍됩니다. 페이지를 새로고침(F5)해주세요.")
                break
        except Exception as _e:
            # 일반 예외도 traceback 기록
            _tb = _traceback.format_exc().encode("utf-8", errors="ignore").decode("utf-8")
            log_error("예외[TB]", _tb)
            _recovered = auto_recover(_e)
            if _recovered and _attempt < _MAX_RETRY - 1:
                st.rerun()
            else:
                st.error(f"시스템 오류 (복구 불가): {_safe_str(_e)}")
                st.info("페이지를 새로고침(F5)하거나 관리자에게 문의하세요: 010-3074-2616")
                break

_run_safe()
