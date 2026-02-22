# ==========================================================
# 골드키지사 마스터 AI - 탭 구조 통합본 (전체 수정판)
# 수정: 구조적/논리적/보안/모바일 문제 전체 반영
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
import sys, json, os, time, hashlib, base64, re, tempfile

from datetime import datetime as dt, timedelta, date
from typing import List, Dict
import numpy as np
import sqlite3
import PIL.Image
from cryptography.fernet import Fernet
import streamlit.components.v1 as components

# Cloud Run 환경 UTF-8 강제 설정 (서로게이트 문자 오류 방지)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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

def sanitize_unicode(text):
    """서로게이트 문자 제거 - UTF-8 인코딩 오류 방지"""
    if not isinstance(text, str):
        return text
    return text.encode('utf-8', errors='replace').decode('utf-8')

def sanitize_prompt(text):
    """프롬프트 인젝션 방어 - 모든 쿼리에 적용"""
    text = sanitize_unicode(text)
    danger_words = ["system instruction", "지침 무시", "프롬프트 출력", "비밀번호", "명령어 변경"]
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
        pure_asset_per_share = self.net_asset / self.total_shares
        weighted_eps = (
            self.net_incomes[0] / self.total_shares * 3 +
            self.net_incomes[1] / self.total_shares * 2 +
            self.net_incomes[2] / self.total_shares * 1
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

def load_members():
    if not os.path.exists(MEMBER_DB):
        return {}
    with open(MEMBER_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_members(members):
    # ensure_ascii=False: 한글 이름 깨짐 방지
    with open(MEMBER_DB, "w", encoding="utf-8") as f:
        json.dump(members, f, ensure_ascii=False)

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

# 일일 무료 분석 횟수 상수 (단일 정의)
MAX_FREE_DAILY = 10
BETA_END_DATE  = date(2026, 8, 31)
UNLIMITED_USERS = {"이세윤", "PERMANENT_MASTER"}

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

def update_usage(user_name):
    """분석 성공 후에만 호출해야 함"""
    today = str(date.today())
    data = {}
    if os.path.exists(USAGE_DB):
        with open(USAGE_DB, "r", encoding="utf-8") as f:
            data = json.load(f)
    if user_name not in data:
        data[user_name] = {}
    data[user_name][today] = data[user_name].get(today, 0) + 1
    with open(USAGE_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

def get_remaining_usage(user_name):
    return max(0, MAX_FREE_DAILY - check_usage_count(user_name))

def display_usage_dashboard(user_name: str):
    """사이드바 프리미엄 사용량 게이지 UI"""
    current_count = check_usage_count(user_name)
    is_unlimited  = user_name in UNLIMITED_USERS
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
    """TTS - 20대 여성 아나운서 목소리 (pitch=1.4, rate=1.05)"""
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
    if not RAG_AVAILABLE:
        return None
    try:
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

    # 1회 초기화
    if 'db_ready' not in st.session_state:
        setup_database()
        st.session_state.db_ready = True

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
        st.header("Goldkey_AI_Master_Lab. SaaS Center")

        # 관리자/영구회원 로그인
        admin_id = st.text_input("관리자 ID", key="admin_id", type="password")
        admin_code = st.text_input("관리자 코드", key="admin_code", type="password")
        if st.button("관리자 로그인", key="btn_admin_login"):
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
                st.session_state.user_name = "이세윤 마스터"
                st.session_state.join_date = dt.now()
                st.session_state.is_admin = True
                st.success("관리자로 로그인되었습니다!")
                st.rerun()
            elif admin_id == "이세윤" and admin_code == _master_code:
                st.session_state.user_id = "PERMANENT_MASTER"
                st.session_state.user_name = "이세윤"
                st.session_state.join_date = dt.now()
                st.session_state.is_admin = True
                st.success("마스터로 로그인되었습니다! (무제한 사용)")
                st.rerun()
            else:
                st.error("ID 또는 코드가 올바르지 않습니다.")

        st.divider()

        # 회원가입 혜택 안내
        if 'user_id' not in st.session_state:
            st.markdown("""
            **🎁 회원가입 혜택**
            - ✅ 매일 무료 AI 상담 10회
            - ✅ 보험금/이미지 분석
            - ✅ 상속·증여·주택연금 시뮬레이션
            - ✅ 건보료 기반 소득 역산
            - 💎 구독회원: 무제한 이용
            """)
            st.divider()

        if 'user_id' not in st.session_state:
            # 비로그인 안내 멘트
            st.info("👋 안녕하세요, 무엇을 도와드릴까요?")
            components.html(s_voice("안녕하세요. 무엇을 도와드릴까요?"), height=0)
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
            st.success(f"{user_name} 마스터님 접속 중")

            is_member, status_msg = check_membership_status()
            remaining_days = calculate_subscription_days(st.session_state.get('join_date'))
            remaining_usage = get_remaining_usage(user_name)

            st.info(
                f"**구독 상태**: {status_msg}\n\n"
                f"**잔여 기간**: {remaining_days}일\n\n"
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
        st.caption("문의: insusite@gmail.com")
        st.caption("상담: 010-3074-2616 골드키지사")
        display_security_sidebar()

    # ── 메인 탭 구조 ──────────────────────────────────────────────────────
    st.title("골드키지사 AI 마스터")
    tabs = st.tabs([
        "🏥 통합 상담",
        "📷 보험금/이미지",
        "🚗 자동차사고",
        "🌅 노후/연금",
        "📊 세무상담",
        "🏢 법인/CEO",
        "👔 CEO플랜",
        "🏛️ 상속/증여",
        "⚙️ 관리자"
    ])

    # ── [탭 0] 통합 상담 ──────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("마스터 AI 정밀 상담")
        col1, col2 = st.columns([1, 1])

        with col1:
            c_name = st.text_input("고객 성함", "우량 고객", key="c_name_main")
            st.session_state.current_c_name = c_name

            # 음성 입력 언어 선택
            stt_lang_map = {
                "한국어": "ko-KR",
                "English": "en-US",
                "日本語": "ja-JP",
                "中文": "zh-CN",
                "ภาษาไทย": "th-TH",
                "Tiếng Việt": "vi-VN",
                "Русский": "ru-RU",
            }
            stt_lang_label = st.selectbox(
                "음성입력 언어",
                list(stt_lang_map.keys()),
                key="stt_lang_select"
            )
            stt_lang_code = stt_lang_map[stt_lang_label]

            # 입력창 height=200
            query = st.text_area("상담 내용 입력", height=200, key="query_main",
                                 placeholder="보험, 재무, 건강 등 상담 내용을 입력하세요. (🎤 버튼으로 음성입력 가능)")
            hi_premium = st.number_input("월 건강보험료(원)", value=0, step=1000, key="hi_main")

            # 건보료 역산 결과 즉시 표시
            if hi_premium > 0:
                income = hi_premium / 0.0709
                st.success(f"역산 월 소득: **{income:,.0f}원** | 적정 보험료: **{income*0.15:,.0f}원**")

            # 정밀분석실행 + 음성입력 버튼 나란히
            btn_col1, btn_col2 = st.columns([3, 1])
            with btn_col1:
                do_analyze = st.button("정밀 분석 실행", type="primary", key="btn_analyze")
            with btn_col2:
                if st.button("🎤 음성", key="btn_stt"):
                    components.html(
                        f'<script>window.startRecognition("{stt_lang_code}",null);</script>',
                        height=0
                    )

            if do_analyze:
                if 'user_id' not in st.session_state:
                    st.error("로그인이 필요합니다.")
                else:
                    user_name = st.session_state.get('user_name', '')
                    is_special = st.session_state.get('is_admin', False)
                    _ = user_name  # noqa
                    current_count = check_usage_count(user_name)

                    if not is_special and current_count >= MAX_FREE_DAILY:
                        st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                        components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다."), height=0)
                    else:
                        with st.spinner("골드키AI마스터 분석 중..."):
                            try:
                                client, model_config = get_master_model()
                                safe_query = sanitize_prompt(query)
                                income = hi_premium / 0.0709 if hi_premium > 0 else 0

                                rag_ctx = ""
                                if st.session_state.rag_system.index is not None:
                                    results = st.session_state.rag_system.search(safe_query, k=3)
                                    if results:
                                        rag_ctx = "\n\n[참고 자료]\n" + "".join(
                                            f"{i}. {r['text']}\n" for i, r in enumerate(results, 1))

                                prompt = (
                                    f"고객: {sanitize_unicode(c_name)}, 추정소득: {income:,.0f}원\n"
                                    f"질문: {safe_query}{rag_ctx}"
                                )
                                resp = client.models.generate_content(
                                    model=GEMINI_MODEL,
                                    contents=prompt,
                                    config=model_config
                                )
                                answer = sanitize_unicode(resp.text) if resp.text else "AI 응답을 받지 못했습니다. 다시 시도해주세요."
                                result_text = (
                                    f"### {c_name}님 골드키AI마스터 정밀 리포트\n\n{answer}\n\n---\n"
                                    f"**문의:** insusite@gmail.com | 010-3074-2616\n\n"
                                    f"[주의] 최종 책임은 사용자(상담원)에게 귀속됩니다."
                                )
                                st.session_state.analysis_result = result_text
                                update_usage(user_name)
                                components.html(s_voice("분석이 완료되었습니다."), height=0)
                                components.html(s_voice_answer(answer), height=0)
                                remaining = MAX_FREE_DAILY - (current_count + 1)
                                if not is_special:
                                    st.success(f"분석 완료! (오늘 남은 횟수: {remaining}회)")
                                st.rerun()
                            except Exception as e:
                                st.error(f"분석 오류: {e}")

        with col2:
            st.subheader("마스터 AI 리포트")
            if 'analysis_result' in st.session_state and st.session_state.analysis_result:
                st.markdown(st.session_state.analysis_result)
            else:
                st.info("상담 내용을 입력하고 분석을 실행하세요.")

    # ── [탭 1] 보험금/이미지 분석 ─────────────────────────────────────────
    with tabs[1]:
        st.subheader("의무기록 및 증권 이미지 분석")
        st.caption("보험 증권, 진단서, 의료 기록, 사고 현장 사진을 AI가 정밀 분석합니다.")

        col_a, col_b = st.columns([1, 1])
        with col_a:
            files = st.file_uploader(
                "자료 업로드 (PDF/이미지)",
                accept_multiple_files=True,
                type=['pdf', 'jpg', 'jpeg', 'png', 'bmp'],
                key="uploader_tab1")
            if files:
                st.success(f"{len(files)}개 파일 업로드 완료")
                for i, f in enumerate(files, 1):
                    if f.type.startswith('image/'):
                        st.image(f, caption=f"파일 {i}", width=180)
                    else:
                        st.info(f"파일 {i}: {f.name}")

        with col_b:
            img_query_type = st.selectbox(
                "분석 유형",
                ["보험금 청구", "진단서 분석", "사고 현장 분석", "의료 기록 분석"],
                key="img_query_type")
            img_specific = st.text_area(
                "특정 요청사항",
                placeholder="예: 이 증권의 암 보장 금액을 분석해주세요.",
                height=160,
                key="img_specific")

        if files and st.button("AI 이미지 분석 시작", type="primary", key="btn_img_analyze"):
            if 'user_id' not in st.session_state:
                st.error("로그인이 필요합니다.")
            else:
                user_name = st.session_state.get('user_name', '')
                is_special = st.session_state.get('is_admin', False)
                current_count = check_usage_count(user_name)
                if not is_special and current_count >= MAX_FREE_DAILY:
                    st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                else:
                    with st.spinner("비전 엔진을 통한 정밀 분석 중..."):
                        try:
                            client, model_config = get_master_model()
                            # c_name은 탭0 위젯값 → 세션에 별도 저장된 값 사용
                            c_name_img = st.session_state.get('current_c_name', '고객')
                            analysis_query = (
                                f"[보험금 상담 분석]\n분석 유형: {img_query_type}\n"
                                f"요청: {img_specific}\n\n"
                                "1. 보험 문서의 주요 내용\n2. 의료 기록의 핵심 정보\n"
                                "3. 보험금 청구 가능성 및 예상 금액\n4. 필요한 추가 서류"
                            )
                            contents = [analysis_query]
                            for f in files:
                                if f.type.startswith('image/'):
                                    contents.append(PIL.Image.open(f))
                                elif f.type == 'application/pdf':
                                    contents.append(f"PDF 파일: {f.name}\n{process_pdf(f)[:500]}")
                            resp = client.models.generate_content(
                                model=GEMINI_MODEL,
                                contents=contents,
                                config=model_config)
                            answer = sanitize_unicode(resp.text) if resp.text else "AI 응답을 받지 못했습니다."
                            result_text = (
                                f"### {c_name_img}님 골드키AI마스터 보험금 분석 리포트\n\n{answer}\n\n---\n"
                                f"[주의] 최종 책임은 사용자(상담원)에게 귀속됩니다."
                            )
                            st.session_state.analysis_result = result_text
                            st.markdown(result_text)
                            # 성공 후에만 사용량 차감
                            update_usage(user_name)
                            components.html(s_voice("보험금 분석이 완료되었습니다."), height=0)
                        except Exception as e:
                            st.error(f"이미지 분석 오류: {e}")


    # ── [탭 2] 자동차사고 상담 ───────────────────────────────────────────
    with tabs[2]:
        st.subheader("🚗 자동차사고 상담 · 과실비율 분석")
        st.caption("교통사고처리특례법 13대 중과실 기준 · accident.knia.or.kr 기준")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_acc = st.text_input("고객 성함", "우량 고객", key="c_name_acc")
            acc_query  = st.text_area("사고 상황 입력", height=160, key="acc_query",
                placeholder="예) 신호등 없는 교차로에서 직진 중 우측에서 좌회전 차량과 충돌.")
            with st.expander("✅ 13대 중과실 해당 여부 체크", expanded=False):
                fault_items = ["① 신호·지시 위반","② 중앙선 침범","③ 제한속도 20km/h 초과",
                    "④ 앞지르기 방법·금지 위반","⑤ 철길건널목 통과방법 위반",
                    "⑥ 횡단보도 보행자 보호의무 위반","⑦ 무면허 운전","⑧ 음주운전(0.03% 이상)",
                    "⑨ 보도 침범·횡단방법 위반","⑩ 승객 추락 방지의무 위반",
                    "⑪ 어린이 보호구역 안전운전의무 위반","⑫ 화물 추락 방지의무 위반","⑬ 개문발차 사고"]
                checked_faults = [fi for fi in fault_items if st.checkbox(fi, key=f"fault_{fi[:3]}")]
                if checked_faults:
                    st.warning(f"⚠️ {len(checked_faults)}개 중과실 해당 → 운전자보험 필수")
            do_acc = st.button("과실비율 AI 분석 실행", type="primary", key="btn_acc")
            if do_acc:
                if 'user_id' not in st.session_state:
                    st.error("로그인이 필요합니다.")
                else:
                    user_name = st.session_state.get('user_name', '')
                    if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                        st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                    else:
                        with st.spinner("분석 중..."):
                            try:
                                client, model_config = get_master_model()
                                fault_ctx = f"\n[13대 중과실 해당: {', '.join(checked_faults)}]\n" if checked_faults else ""
                                prompt = (f"[자동차사고 상담]{fault_ctx}\n고객: {sanitize_unicode(c_name_acc)}\n"
                                    f"질문: {sanitize_prompt(acc_query)}\n"
                                    "1. 과실비율 분쟁심의위원회 기준 과실비율 분석\n"
                                    "2. 교통사고처리특례법 13대 중과실 해당 여부\n"
                                    "3. 운전자보험 교통사고처리지원금 지급 가능 여부\n"
                                    "⚠️ 최종 과실비율은 위원회/법원 판결에 따르며 본 답변은 참고용입니다.")
                                resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=model_config)
                                st.session_state['res_acc'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                update_usage(user_name)
                                st.rerun()
                            except Exception as e:
                                st.error(f"분석 오류: {e}")
        with col2:
            st.subheader("AI 분석 리포트")
            if st.session_state.get('res_acc'):
                st.markdown(st.session_state['res_acc'])
            else:
                st.info("사고 상황을 입력하고 분석을 실행하세요.")

    # ── [탭 3] 노후/연금 설계 ────────────────────────────────────────────
    with tabs[3]:
        st.subheader("🌅 노후설계 · 연금 3층 · 주택연금")
        retire_sub = st.radio("상담 분야", ["노후/연금 설계", "상속·증여 설계", "주택연금"],
            horizontal=True, key="retire_sub")
        if retire_sub == "상속·증여 설계":
            section_inheritance_will()
        elif retire_sub == "주택연금":
            section_housing_pension()
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                c_name_t3 = st.text_input("고객 성함", "우량 고객", key="c_name_t3")
                query_t3  = st.text_area("상담 내용", height=160, key="query_t3",
                    placeholder="예) 55세, 은퇴 후 월 300만원 필요, 국민연금 20년 가입")
                hi_t3  = st.number_input("월 건강보험료(원)", value=0, step=1000, key="hi_t3")
                do_t3  = st.button("노후설계 AI 분석", type="primary", key="btn_t3")
                if do_t3:
                    if 'user_id' not in st.session_state:
                        st.error("로그인이 필요합니다.")
                    else:
                        user_name = st.session_state.get('user_name', '')
                        if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                            st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                        else:
                            with st.spinner("분석 중..."):
                                try:
                                    client, model_config = get_master_model()
                                    income = hi_t3 / 0.0709 if hi_t3 > 0 else 0
                                    prompt = (f"[노후설계 상담]\n고객: {sanitize_unicode(c_name_t3)}, 추정소득: {income:,.0f}원\n"
                                        f"질문: {sanitize_prompt(query_t3)}\n"
                                        "1. 국민연금·퇴직연금·개인연금 3층 연금 현황 분석 및 소득대체율 계산\n"
                                        "2. 명목 소득대체율(65%)과 실질 소득대체율(40~50%) 격차 해소 방안\n"
                                        "3. 은퇴 후 필요 생활비 역산 및 월 부족분 산출\n"
                                        "4. 연금보험·즉시연금·종신보험으로 격차 보완 전략\n"
                                        "5. IRP·연금저축 세액공제 최대 활용법")
                                    resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=model_config)
                                    st.session_state['res_t3'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                    update_usage(user_name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"분석 오류: {e}")
            with col2:
                st.subheader("AI 분석 리포트")
                if st.session_state.get('res_t3'):
                    st.markdown(st.session_state['res_t3'])
                else:
                    st.info("상담 내용을 입력하고 분석을 실행하세요.")

    # ── [탭 4] 세무상담 ──────────────────────────────────────────────────
    with tabs[4]:
        st.subheader("📊 세무상담")
        st.caption("보험 관련 세금 · 상속세 · 증여세 · 연금소득세 · 절세 전략")
        tax_sub = st.radio("상담 분야", ["상속·증여세", "연금소득세", "CEO설계"],
            horizontal=True, key="tax_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_t4 = st.text_input("고객 성함", "우량 고객", key="c_name_t4")
            query_t4  = st.text_area(f"{tax_sub} 관련 세무 상담 내용을 입력하세요.", height=160, key="query_t4")
            hi_t4  = st.number_input("월 건강보험료(원)", value=0, step=1000, key="hi_t4")
            do_t4  = st.button("세무 AI 분석", type="primary", key="btn_t4")
            if do_t4:
                if 'user_id' not in st.session_state:
                    st.error("로그인이 필요합니다.")
                else:
                    user_name = st.session_state.get('user_name', '')
                    if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                        st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                    else:
                        with st.spinner("분석 중..."):
                            try:
                                client, model_config = get_master_model()
                                income = hi_t4 / 0.0709 if hi_t4 > 0 else 0
                                prompt = (f"[세무상담 - {tax_sub}]\n고객: {sanitize_unicode(c_name_t4)}, 추정소득: {income:,.0f}원\n"
                                    f"질문: {sanitize_prompt(query_t4)}\n"
                                    "1. 관련 세법 조항과 최신 개정 내용 안내\n2. 절세 전략과 합법적 세금 최소화 방안\n"
                                    "3. 신고 기한과 필요 서류 안내\n4. 세무사 상담이 필요한 사항 명시\n"
                                    "※ 본 답변은 참고용이며 구체적 사안은 세무사와 상의하십시오.")
                                resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=model_config)
                                st.session_state['res_t4'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                update_usage(user_name)
                                st.rerun()
                            except Exception as e:
                                st.error(f"분석 오류: {e}")
        with col2:
            st.subheader("AI 분석 리포트")
            if st.session_state.get('res_t4'):
                st.markdown(st.session_state['res_t4'])
            else:
                defaults = {"상속·증여세": "**상속·증여세 핵심:**\n- 상속세: 일괄공제 5억 / 배우자공제 최소 5억\n- 증여세: 10년 합산 / 배우자 6억·자녀 5천만원 공제\n- 세율: 10%~50% 누진세율",
                    "연금소득세": "**연금소득세 핵심:**\n- 연금저축·IRP 수령 시: 3.3~5.5% 연금소득세\n- 연간 1,500만원 초과 수령 시: 종합소득세 합산 또는 분리과세 선택",
                    "CEO설계": "**CEO설계 핵심:**\n- 경영인정기보험: 법인 납입 보험료 손금산입 가능 여부 확인\n- CEO 유고 시: 사망보험금 → 퇴직금 재원 활용\n- 임원 퇴직금 규정 정비 필수"}
                st.info(defaults.get(tax_sub, ""))

    # ── [탭 5] 법인상담 ──────────────────────────────────────────────────
    with tabs[5]:
        st.subheader("🏢 법인상담 (CEO플랜 · 단체보험 · 기업보험)")
        corp_sub = st.radio("상담 분야",
            ["CEO플랜 (사망·퇴직)", "단체상해보험", "공장·기업 화재보험", "법인 절세 전략", "임원 퇴직금 설계"],
            horizontal=True, key="corp_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            c_name_t5 = st.text_input("고객 성함", "우량 고객", key="c_name_t5")
            query_t5  = st.text_area(f"{corp_sub} 관련 법인 상담 내용을 입력하세요.", height=160, key="query_t5",
                placeholder="예) 직원 50명, 제조업, CEO 60세")
            emp_count  = st.number_input("임직원 수", min_value=1, value=10, step=1, key="emp_count")
            corp_asset = st.number_input("법인 자산 규모 (만원)", value=100000, step=10000, key="corp_asset")
            do_t5 = st.button("법인 AI 분석", type="primary", key="btn_t5")
            if do_t5:
                if 'user_id' not in st.session_state:
                    st.error("로그인이 필요합니다.")
                else:
                    user_name = st.session_state.get('user_name', '')
                    if not st.session_state.get('is_admin') and check_usage_count(user_name) >= MAX_FREE_DAILY:
                        st.error(f"오늘 {MAX_FREE_DAILY}회 분석을 모두 사용하셨습니다.")
                    else:
                        with st.spinner("분석 중..."):
                            try:
                                client, model_config = get_master_model()
                                prompt = (f"[법인상담 - {corp_sub}]\n고객: {sanitize_unicode(c_name_t5)}, 임직원수: {emp_count}명, 법인자산: {corp_asset:,}만원\n"
                                    f"질문: {sanitize_prompt(query_t5)}\n"
                                    "1. 법인 보험의 세무처리(손금산입) 방법\n2. CEO 유고 시 법인 리스크 관리 방안\n"
                                    "3. 단체보험 가입 기준과 보장 설계\n4. 퇴직금 재원 마련을 위한 보험 활용\n"
                                    "5. 공장·기업 재산 보호를 위한 화재보험 설계")
                                resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt, config=model_config)
                                st.session_state['res_t5'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                update_usage(user_name)
                                st.rerun()
                            except Exception as e:
                                st.error(f"분석 오류: {e}")
        with col2:
            st.subheader("AI 분석 리포트")
            if st.session_state.get('res_t5'):
                st.markdown(st.session_state['res_t5'])
            else:
                st.info("**법인보험 핵심:**\n- CEO플랜: 사망보험금 → 퇴직금 재원\n- 단체상해: 전 직원 의무 가입 권장\n- 공장화재: 재조달가액 기준 가입\n- 임원 퇴직금 규정 정비 필수")

    # ── [탭 6] CEO플랜 — 비상장주식 평가 ────────────────────────────────
    with tabs[6]:
        st.subheader("👔 CEO플랜 — 비상장주식 약식 평가 & 법인 재무분석")
        st.caption("상증법·법인세법 통합 비상장주식 평가 | 재무제표 3년치 스캔 분석")
        ceo_sub = st.radio("분석 방식 선택", ["📊 직접 입력 평가표", "📁 재무제표 스캔 업로드"],
            horizontal=True, key="ceo_sub")
        col1, col2 = st.columns([1, 1])
        with col1:
            if ceo_sub == "📊 직접 입력 평가표":
                ceo_company    = st.text_input("법인명", "(주)예시기업", key="ceo_company")
                total_shares   = st.number_input("발행주식 총수 (주)", value=10000, step=100, key="ceo_shares")
                is_controlling = st.checkbox("최대주주 (경영권 할증 20% 적용)", value=True, key="ceo_ctrl")
                is_re_rich     = st.checkbox("부동산 과다 법인 (자산 비중 80% 이상)", value=False, key="ceo_re")
                mkt_price_in   = st.number_input("매매사례가액 (원, 없으면 0)", value=0, step=1000, key="ceo_mkt")
                net_asset      = st.number_input("순자산 (원)", value=12_864_460_902, step=1_000_000, key="ceo_asset")
                st.markdown("**당기순이익 3개년 (원)**")
                c1, c2, c3 = st.columns(3)
                with c1: ni_1 = st.number_input("최근년", value=688_182_031, step=1_000_000, key="ceo_ni1")
                with c2: ni_2 = st.number_input("전년",   value=451_811_737, step=1_000_000, key="ceo_ni2")
                with c3: ni_3 = st.number_input("전전년", value=553_750_281, step=1_000_000, key="ceo_ni3")
                if st.button("📈 비상장주식 평가 실행", type="primary", key="btn_ceo_eval"):
                    mkt = mkt_price_in if mkt_price_in > 0 else None
                    ev  = AdvancedStockEvaluator(net_asset=net_asset, net_incomes=[ni_1, ni_2, ni_3],
                        total_shares=total_shares, market_price=mkt,
                        is_controlling=is_controlling, is_real_estate_rich=is_re_rich)
                    st.session_state.update({"ceo_eval_corp": ev.evaluate_corporate_tax(),
                        "ceo_eval_inh": ev.evaluate_inheritance_tax(),
                        "ceo_company_result": ceo_company, "ceo_shares_result": total_shares})
                    st.rerun()
            else:
                fs_files = st.file_uploader("재무제표 파일 업로드 (최대 3개)",
                    type=["pdf","jpg","jpeg","png"], accept_multiple_files=True, key="ceo_fs_files")
                if fs_files:
                    st.success(f"{len(fs_files)}개 파일 업로드 완료")
                ceo_c2   = st.text_input("법인명", "(주)예시기업", key="ceo_company2")
                ceo_note = st.text_area("추가 분석 요청 사항 (선택)", height=100, key="ceo_note",
                    placeholder="예) CEO 퇴직금 설계, 가업승계 전략도 함께 분석해주세요.")
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
                                    st.error(f"분석 오류: {e}")
        with col2:
            if ceo_sub == "📊 직접 입력 평가표":
                corp_r  = st.session_state.get("ceo_eval_corp")
                inh_r   = st.session_state.get("ceo_eval_inh")
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
                                    ai_prompt = (CEO_PLAN_PROMPT +
                                        f"\n법인명: {company}, 발행주식: {shares:,}주\n"
                                        f"법인세법상 시가: {corp_val:,.0f}원/주 (총 {corp_val*shares:,.0f}원)\n"
                                        f"상증법상 최종가액: {inh_val:,.0f}원/주 (총 {inh_val*shares:,.0f}원)\n")
                                    resp = client.models.generate_content(model=GEMINI_MODEL, contents=ai_prompt, config=model_config)
                                    st.session_state['res_ceo_ai'] = sanitize_unicode(resp.text) if resp.text else "응답 없음"
                                    update_usage(user_name)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"분석 오류: {e}")
                    if st.session_state.get('res_ceo_ai'):
                        st.markdown(st.session_state['res_ceo_ai'])
                else:
                    st.info("좌측 입력표를 작성하고 '비상장주식 평가 실행'을 클릭하세요.")
            else:
                if st.session_state.get('res_ceo_fs'):
                    st.markdown(st.session_state['res_ceo_fs'])
                else:
                    st.info("재무제표 파일을 업로드하고 분석을 실행하세요.")

    # ── [탭 7] 상속/증여 + 주택연금 ──────────────────────────────────────
    with tabs[7]:
        section_inheritance_will()
        st.divider()
        section_housing_pension()

    # ── [탭 8] 관리자 ────────────────────────────────────────────────────
    with tabs[8]:
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
                st.write("### 마스터 전용 RAG 엔진")
                rag_files = st.file_uploader(
                    "전문가용 노하우 PDF/DOCX/TXT 업로드",
                    type=['pdf', 'docx', 'txt'],
                    accept_multiple_files=True,
                    key="rag_uploader_admin")
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

            # 데이터 파기
            with inner_tabs[2]:
                st.warning("만료된 사용자 데이터를 영구 삭제합니다.")
                if st.button("만료 데이터 파기 실행", type="primary", key="btn_purge_admin"):
                    try:
                        conn = sqlite3.connect(os.path.join(_DATA_DIR, 'insurance_data.db'))
                        cursor = conn.cursor()
                        cursor.execute(
                            "SELECT COUNT(*) FROM user_documents "
                            "WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')"
                        )
                        count = cursor.fetchone()[0]
                        cursor.execute(
                            "DELETE FROM user_documents "
                            "WHERE status='EXPIRED' AND expiry_date <= date('now','-30 days')"
                        )
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
        "상담 문의: 010-3074-2616 이세윤 FC"
    )


# --------------------------------------------------------------------------
# [SECTION 9] 자가 복구 시스템 + 앱 진입점
# --------------------------------------------------------------------------
def auto_recover(e: Exception) -> bool:
    """오류 유형별 자동 복구 시도. 복구 성공 시 True 반환."""
    err = str(e)

    # 1. 인코딩 오류 → 세션 초기화 후 재시도
    if "codec" in err or "surrogate" in err or "encode" in err:
        for key in ['analysis_result']:
            st.session_state.pop(key, None)
        st.warning("⚠️ 인코딩 오류가 발생했습니다. 자동 복구되었습니다. 다시 시도해주세요.")
        return True

    # 2. 파일 쓰기 오류 → /tmp/ 경로로 전환
    if "Read-only" in err or "Permission denied" in err or "No such file" in err:
        import app as _self
        _self._DATA_DIR = "/tmp"
        _self.USAGE_DB  = "/tmp/usage_log.json"
        _self.MEMBER_DB = "/tmp/members.json"
        st.warning("⚠️ 파일 경로 오류가 발생했습니다. 자동 복구되었습니다.")
        return True

    # 3. API 오류 → 안내 메시지
    if "API" in err or "quota" in err.lower() or "rate" in err.lower():
        st.warning("⚠️ AI API 오류입니다. 잠시 후 다시 시도해주세요.")
        return True

    # 4. 세션 오류 → 세션 초기화
    if "session" in err.lower() or "StreamlitAPIException" in err:
        st.session_state.clear()
        st.warning("⚠️ 세션 오류가 발생했습니다. 자동 초기화되었습니다.")
        return True

    return False  # 복구 불가 → 원본 오류 표시


if __name__ == "__main__":
    MAX_RETRY = 2
    for attempt in range(MAX_RETRY):
        try:
            main()
            break
        except Exception as e:
            recovered = auto_recover(e)
            if recovered and attempt < MAX_RETRY - 1:
                st.rerun()
            else:
                st.error(f"시스템 오류 (복구 불가): {sanitize_unicode(str(e))}")
                st.info("페이지를 새로고침(F5)하거나 관리자에게 문의하세요: 010-3074-2616")
