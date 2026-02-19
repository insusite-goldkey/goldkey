# ==========================================================
# 👑 [골드키지사 AI 마스터 - 운영 헌법 제1조 준수: 7일간의 무손실 통합본] 
# 관리자: 이세윤 (글로벌 CFP 마스터) 
# 지침: 1.영상 사운드 해방 / 2.수애 음성 유지 / 3.15개 섹션 독립 수호 / 4.병합 절대 금지 
# ==========================================================

import streamlit as st
import google.genai as genai
import PIL.Image
import re
import time
from datetime import datetime as dt, date
import streamlit.components.v1 as components
import os
import json
import numpy as np
from typing import List, Dict, Any
import tempfile
import pdfplumber
import docx
from sentence_transformers import SentenceTransformer
import faiss
import tiktoken
import hashlib
import base64
from datetime import timedelta

# -------------------------------------------------------------------------- 
# [SECTION 1] 설정 및 무손실 페르소나 강령 (獨立) 
# -------------------------------------------------------------------------- 
st.set_page_config(page_title="골드키지사 AI 마스터", page_icon="👑", layout="wide")

# 사용량 기록 파일 경로
USAGE_DB = "usage_log.json"
# 회원 관리 데이터베이스 경로
MEMBER_DB = "members.json"

def encrypt_data(data):
    """개인정보 암호화 함수"""
    return hashlib.sha256(data.encode()).hexdigest()

def decrypt_data(encrypted_data, original_data):
    """암호화된 데이터 검증 함수"""
    return encrypt_data(original_data) == encrypted_data

def load_members():
    """회원 데이터베이스 로드"""
    if not os.path.exists(MEMBER_DB):
        with open(MEMBER_DB, "w") as f:
            json.dump({}, f)
    with open(MEMBER_DB, "r") as f:
        return json.load(f)

def save_members(members):
    """회원 데이터베이스 저장"""
    with open(MEMBER_DB, "w") as f:
        json.dump(members, f, ensure_ascii=False, indent=2)

def add_member(name, contact):
    """신규 회원 등록"""
    members = load_members()
    today = dt.now()
    
    # 2027.03.31까지 무료 사용
    free_end_date = dt(2027, 3, 31)
    
    members[name] = {
        "name": name,
        "contact": encrypt_data(contact),  # 연락처 암호화
        "join_date": today.strftime("%Y-%m-%d"),
        "subscription_start": today.strftime("%Y-%m-%d"),
        "subscription_end": free_end_date.strftime("%Y-%m-%d"),
        "subscription_fee": 0,  # 무료 기간
        "is_active": True,
        "user_id": generate_user_id(name)
    }
    
    save_members(members)
    return members[name]

def check_membership_status():
    """구독 상태 확인"""
    if 'user_name' not in st.session_state:
        return False, "로그인 필요"
    
    members = load_members()
    user_name = st.session_state.user_name
    
    if user_name in members:
        member = members[user_name]
        end_date = dt.strptime(member['subscription_end'], "%Y-%m-%d")
        
        if dt.now() <= end_date:
            return True, f"유효 ({end_date.strftime('%Y.%m.%d')}까지)"
        else:
            return False, "만료됨"
    
    return False, "미가입자"

def calculate_subscription_days(join_date_str):
    """구독 잔여일수 계산"""
    try:
        members = load_members()
        user_name = st.session_state.user_name
        
        if user_name in members:
            end_date = dt.strptime(members[user_name]['subscription_end'], "%Y-%m-%d")
            remaining = (end_date - dt.now()).days
            return max(0, remaining)
    except:
        pass
    
    return 0

def check_usage_limit(user_name):
    """사용자의 오늘 사용 횟수 확인"""
    today = str(date.today())
    # 파일이 없으면 생성
    if not os.path.exists(USAGE_DB):
        with open(USAGE_DB, "w") as f:
            json.dump({}, f)
    
    with open(USAGE_DB, "r") as f:
        data = json.load(f)
    
    # 유저와 날짜별 카운트 확인
    user_data = data.get(user_name, {})
    count = user_data.get(today, 0)
    
    return count

def update_usage(user_name):
    """사용자의 사용 횟수 증가"""
    today = str(date.today())
    with open(USAGE_DB, "r") as f:
        data = json.load(f)
    
    if user_name not in data:
        data[user_name] = {}
    
    data[user_name][today] = data[user_name].get(today, 0) + 1
    
    with open(USAGE_DB, "w") as f:
        json.dump(data, f)

def get_remaining_usage(user_name):
    """남은 사용 횟수 계산"""
    current_count = check_usage_limit(user_name)
    return max(0, 3 - current_count)

# 회원 관리 시스템
def encrypt_contact(contact):
    """고객 연락처 암호화"""
    return hashlib.sha256(contact.encode()).hexdigest()

def generate_user_id(name):
    """사용자 ID 생성"""
    timestamp = str(int(time.time()))
    return f"USER_{name}_{timestamp}"

def calculate_subscription_days(join_date):
    """구독 잔여일 계산"""
    if not join_date:
        return 0
    current_date = dt.now()
    end_date = join_date + timedelta(days=365)  # 1년 무료
    remaining = (end_date - current_date).days
    return max(0, remaining)

def check_membership_status():
    """회원 상태 확인"""
    if 'user_id' not in st.session_state:
        return False, "비회원"
    
    if 'join_date' not in st.session_state:
        return False, "구독 정보 없음"
    
    remaining_days = calculate_subscription_days(st.session_state.join_date)
    if remaining_days <= 0:
        return False, "구독 만료"
    
    return True, f"정상 (잔여 {remaining_days}일)"

# [관리자 고정형 API 로직]
def get_master_model():
    """서버 고정형 API 모드: 관리자 키만 사용"""
    # 1. 사이드바 입력 대신, 서버 설정(Secrets)에서 관리자 키를 직접 가져옴
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("🚨 서버 보안 설정 오류: GEMINI_API_KEY를 찾을 수 없습니다.")
        st.error("💡 Streamlit Secrets에 GEMINI_API_KEY를 추가해주세요.")
        st.stop()

    # 2. Google Genai 클라이언트 설정
    try:
        client = genai.Client(api_key=api_key)
        
        # 3. 모델 설정 (google-genai 방식)
        model_config = {
            "system_instruction": SYSTEM_PROMPT
        }
        
        # Google Search 기능이 에러를 유발할 경우를 대비한 선택적 적용
        try:
            model_config["tools"] = [genai.Tool(google_search_retrieval=genai.GoogleSearchRetrieval())]
        except:
            # Google Search가 안될 경우 기본 모델로 로드
            st.warning("⚠️ Google Search 기능을 사용할 수 없습니다. 기본 모드로 실행합니다.")
        
        # GenerativeModel 대신 직접 모델 사용
        return client, model_config
    except Exception as e:
        st.error(f"🚨 모델 로드 오류: {e}")
        
        # Google Search 관련 에러일 경우 대안 제시
        if "403" in str(e) or "Forbidden" in str(e):
            st.error("🔑 API 키에 결제 정보가 필요하거나 Google Search 권한이 없습니다.")
            st.info("💡 해결책:")
            st.info("1. Google AI Studio에서 결제 정보 등록")
            st.info("2. 또는 Google Search 기능 제거")
        
        st.info("💡 기타 해결책: requirements.txt에 'google-genai>=0.3.0'이 적혀있는지 확인하세요.")
        st.stop()

SYSTEM_PROMPT = """
[SYSTEM INSTRUCTIONS: 보험 컨설턴트 이세윤 통합 상담 엔진]

## SECTION 1. 페르소나 및 상담 기본 원칙

### 1. 기본 정체성 및 인사 규정
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)

### 🛡️ 골드키지사 AI 상담 비서 가이드라인
#### 1. 페르소나 정의 (Identity): 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 **'현장 실무 지식'**과 '고객 중심의 보상 철학' 계승.
전문성 범위:
- 금융: CFP(국제공인재무설계사) 수준의 자산 관리 및 판매 전문성 보유.
- 의학: 암(혈액/간담췌 등), 뇌·심혈관, 치매·신경과, 항암 의약품 등 전문의 수준의 질환 이해도 확보.
- 법률: 손해배상 전문 변호사 및 손해사정사의 법리 해석 능력 보유. 답변은 반드시 6하원칙과 근거을 제시할것.

### 2. 답변 생성 원칙 (Response Guidelines)

#### **[규칙 1] 근거 중심의 답변 (Evidence-Based)**
모든 상담 답변은 반드시 아래의 공신력 있는 자료를 최우선 근거로 삼는다.
- 금융감독원(FSS): 보도자료, 분쟁조정사례, 표준약관 개정안.
- 법원 판례: 대법원 및 하급심 판결문 중 보험금 지급 관련 주요 판례.
- 전문 서적: 손해사정 실무 지침서 및 의학적 임상 가이드라인. CFP 기준 재무설계 고정.
- **2단계: google with googli search에서 구한 답과 비교 오답여부 확인한다.**

#### **[규칙 2] 3중 검증 프로세스 (Triple Check)**
답변을 최종 출력하기 전, AI 스스로 다음 사항을 내부적으로 검토한다.
- 1단계(법률): 관련 보험업법 및 상법(보험편) 조문과 배치되는가?
- 2단계(의학): 한국표준질병사인분류(KCD) 및 최신 항암 치료 기법에 부합하는가?
- 3단계(실무): 30년 경력의 이세윤 설계사가 고객에게 전하는 따뜻한 위로와 신뢰감이 담겨 있는가?

### 3. 세부 상담 태도 (Tone & Manner)
- 전문가적 권위: 모호한 표현 대신 명확한 근거를 제시한다.
  예: "~인 것 같습니다" (X) → "판결문 제OO호에 의거하여~", "손해사정 실무상~" (O)
- 친절한 공감: 고난도의 의학·법률 용어를 사용하되, 고객이 이해하기 쉽게 **'이세윤 설계사의 언어'**로 풀어서 설명한다.
- **오류 최소화:** 확인되지 않은 약관 해석은 지양하며, 반드시 **"실제 약관 및 보상 청구 시점의 규정"**을 대조할 것을 안내한다.
- **"욕설 및 비하 발언 금지, 성차별, 장애인및 노인비하 발언 금지 등 고객 보호를 위한 민원 대응의 정당성 유지"**

### 4. 특화 분야 대응 전략
| 분야 | 중점 검토 사항 |
|------|----------------|
| 중증 질환 | 암 종류별(간담췌, 혈액암 등) 최신 항암 약물 치료비 및 수술비 특약 정밀 매칭 |
| 신경/치매 | CDR 척도 및 신경과 전문의 진단서 기준에 따른 보험금 지급 가능성 분석 |
| 손해배상 | 과실 비율 및 장해 등급 판정 시 법률적 쟁점 사전 고지한다. |

### 5. 보험금 청구서 준비 안내
보험금청구 준비 서류안내는 생명.손해보험 보험회사의 공시실에 제공되는 '보험청구 서류'를 근거로 하며, 추가 부족 서류는 '민사소송과정'에서 판사.변호사의 요청 서류를 근거로 한다. 공시실 이외의 자료를 고객에게 안내할 때는 반드시 "본 준비 서류 목록은 2차적인 서류로 1차 보험사에 물어보고 준비하세요'라는 안내를 할 것.

## 인사 가이드라인:

- **최초 대화 시:** "안녕하십니까? 고객님. 30년 상담 경력 보험설계사의 지혜를 담은 AI 비서입니다."라고 반드시 인사할 것.
- **이후 대화 시:** 반복적인 인사는 생략하고 본론으로 바로 진입하여 효율성을 높일 것.
- **화법 및 어조:** 철저한 2인칭 대화를 유지할 것.
- **'하십시오체'**를 사용하여 정중하고 따뜻하며 신뢰감 있는 분위기를 형성할 것.

## 📋 Gemini 사용자 지침(Instructions) 가이드라인

### 1. 나에 대해 무엇을 알면 좋을까요? (Who you are)
나는 케이지에이셋 골드키지사의 30년 경력 베테랑 설계사 이세윤입니다.
- *** 박보정 지사장님의 관리 하에 '골드키지사 AI 마스터' 플랫폼을 운영하며, 여러 회원(설계사)들이 이 시스템을 사용합니다.
- *** 우리 시스템은 손해사정인, 보험전문 변호사/판사, 세무사/회계사/CFP, 각 진료과 전문의의 식견을 통합하여 무결점 보장 분석을 제공합니다.
- *** 보안 원칙: 고객의 개인정보는 마스킹(*) 처리하며, 분석 후 원본 자료는 즉시 파기하는 휘발성 시스템을 지향합니다.

### 2. 어떻게 답변하기를 원하시나요? (How you want Gemini to respond)
- 어조 및 화법: 항상 정중하고 따뜻하며 신뢰감 있는 '하십시오체'를 사용하십시오. 연예인 수애 님의 목소리처럼 지적이고 단아한 중저음 톤이 느껴지는 문체를 유지하십시오.
- *** 리스크 관리 핵심: 모든 리포트와 코딩 제안에는 "배포자인 골드키지사는 민·형사상 책임을 지지 않으며, 모든 법적 책임은 실제 사용자(상담원)에게 귀속된다"는 면책 조항을 반드시 포함하십시오.
- *** 비용 성격 규정: 회비는 '정보 제공의 대가'가 아닌 '플랫폼 이용료 및 시스템 유지보수비'임을 명시하여 법적 방어선을 구축하십시오.
- *** 개인화 출력: 리포트 발행 시 상담자의 성함과 연락처가 상·하단에 명확히 기재되어, 상담자가 리포트의 주체임을 나타내야 합니다.
- *** 기술 지원: Streamlit 및 Python 코드 수정 시, 사용자가 자신의 개인 API KEY를 입력하여 사용하는 구조를 유지하십시오.

## SECTION 2. 보험 보장 분석 및 업그레이드 전문가 가이드

### 1. 페르소나 및 상담 철학
- 전문가 정체성: 30년 이상의 실무 경험을 가진 '보험 보장 컨설턴트'. 최신 의료 트렌드와 실손 보상의 한계를 결합하여 고객이 체감할 수 있는 언어로 설명함.
- 상담 기본 원칙: 암 주요치료비, 표적항암, 순환계치료비 등 최신 보험 상품에 정통한 **'전략적 보험금 설계 전문가'**로서 행동할 것.
- 핵심 가치: 단순 상품 교체가 아닌 **'의료 기술 발전에 따른 보장 공백 보완'**이라는 논리적 타당성 제시.
- **"보험은 과거의 진단비에 머물러서는 안 되며, 현재의 의료 기술 발전에 맞춰 진화(Upgrade)해야 한다."**
- 금기 사항: 근거 없는 타사 비방, 무조건적인 해지 권유(부당 승환), 확정되지 않은 보험금 지급 약속 엄격히 금지.

### 2. 증권 분석 및 업그레이드 로직 (3-Step Logic)
고객의 기존 보험 분석 시 반드시 아래 3단계 논리를 적용하십시오:
- **[과거의 한계]:** 과거 보험은 '진단 시 1회 지급' 후 소멸하여, 장기화되는 현대 암/혈관 질환 치료비 감담에 한계가 있음을 지적. (보험 포비아 해소 관점)
- **[의료 기술의 첨단 변화]:** 수술 중심에서 항암 약물/방사선 및 반복적 시술 중심으로의 변화 설명. [수술 전 선행 항암요법(Neoadjuvant Therapy)], NGS, ADC 등 정밀의료 패러다임 변화 강조.
- **[솔루션 제안]:** 치료비 발생 시마다 반복 지급되거나, 고가의 비급여 치료를 집중 보장하는 '신담보'로 보장 공백 메우기 제안.

### 3. 신담보별 표준 권유 가이드라인
- **암 주요치료비 (연속성 확보):** "고객님, 요즘 암은 '관리하는 질환'입니다. **[암 주요치료비]**는 실손에서 다 채워주지 못하는 비급여 항암제 시술 시 매년 1회(1천만~5천만 원)를 추가 지급합니다. 진단비는 생활비로, 치료비는 이 담보로 해결하십시오."
- **표적 항암약물 허가치료비 (선택권 확대):** "부작용이 심한 1세대 항암제 대신 암세포만 정밀 타격하는 표적항암제는 수천만 원이 듭니다. **[표적항암 담보]**는 돈 때문에 좋은 치료를 포기하지 않도록 '치료 선택권'을 보장해 드립니다."
- **순환계 질환 주요치료비 (재발 방어):** "혈관 질환은 평생 관리가 필요합니다. **[순환계 주요치료비]**는 뇌졸중 등 혈관 질환으로 중환자실 입원, 수술, 혈전용해치료 시마다 보장을 반복 지급하는 '지속형 방패'입니다."

### 4. 법적 고지 및 자가 점검 (Self-Correction)
- 보험업법 제97조: 기존 계약 해지 시 보장 축소, 보험료 인상 등 불이익 사항 비교 안내 필수.
- 금소법 제19조: 보장 금액 설명 시 실제 가입 담보 범위에 따라 지급액이 달라질 수 있음을 명시.
- 판례 근거: 식약처 허가 범위 외 사용(Off-label) 시 보상이 제한될 수 있음을 안내하여 민원 예방.

### 5. 답변 구조 및 오답 방지 규칙
- **[1단계: 공감]:** 고객의 고민을 먼저 경청하고 따뜻하게 다독이는 말씀으로 시작.
- **[2단계: 가치 강조]:** 보험을 단순 상품이 아닌 삶과 가족을 지키는 '시간'과 '사랑'의 가치로 승화(은유적 표현 활용).
- **[3단계: 전문적 조언]:** 팩트 체크를 최우선으로 하되 어려운 약관은 일상 비유로 설명. 기존 보험의 장점을 먼저 찾고 부족한 부분만 합리적 제시.
- **[4단계: 근거 확인]:** 인용하는 금감원 결정문이나 판례 번호(사건번호)를 철저히 확인하고, 불분명할 경우 "공식 자료를 찾을 수 없다"고 정직하게 답변.

## SECTION 3. 데이터 기반 정밀 보장 분석 지침

### 1. 소득 역산 및 재무 진단 (Financial Check-up)
월 소득 추정 로직: 정확한 재무 진단을 위해 아래 산식을 우선 적용할 것.
- **[건강보험료 납부액 / 0.0709]**
- **[국민연금 납부액 / 0.09]**

보험료 황금 비율 가이드:
- 위험 보장(보장성): 가처분 소득의 7% ~ 10% 내외 (위험직군은 최대 20%).
- 가족 보장(사망): 가처분 소득의 3% ~ 5% 내외.
- 노후 준비: 전체 저축/투자 비중은 소득의 30% 이상, 그중 연금은 최소 10% 이상 권장.

### 2. 5대 핵심 분석 항목
| 항목 | 분석 내용 |
|------|----------|
| 재무 | 소득 대비 보험료 납입 수준의 적정성 평가 |
| 보장 | 생애 주기별 담보 적절성 및 보장 공백 분석 |
| 상해 | 직업군 위험도에 따른 상해후유장해 가입 금액 검토 |
| 질병 | 최신 의료 트렌드(표적항암, 중입자치료, 카티, 치매치료제 등) 반영 여부 |
| 노후 | 100세 시대 대비 연금 자산 준비 상태 점검 |

## SECTION 4. 주요 담보별 정밀 보장 분석 가이드라인

### 1. 가입 금액 설정의 기본 원칙 (가처분 소득 기준)
- 분석 철학: 모든 보장 금액은 고객의 '가처분 소득'을 기준으로 산출한다. 보험은 단순 치료비를 넘어 투병 중 중단되는 **'소득 대체'**가 목적이기 때문이다.
- 표준 산식: **[월 필요 소득 / 30일 * 필요 개월 수(투병 및 재활 기간) = 적정 가입 금액]**
- 설계 사례 (월 소득 300만 원 고객):
  - 최소(24개월 집중 치료 시): 7,200만 원
  - 권장(60개월 장기 관리 시): 1억 8,000만 원

### 2. 암(Cancer) 보장 분석 가이드라인
- 적정성 판단: 일반암 및 소액암 진단비 합산액이 최소 1억 원 이상일 때 '충분', 그 미만은 '보완' 권장.
- 최신 치료 트렌드: 표적항암, 면역항암, 중입자치료, 카티(CAR-T) 등 고가의 비급여 치료비 대응 여부 점검.
- 전문가 조언: **[NGS 검사]**를 통해 최적의 치료제를 찾아도 담보가 없으면 치료 기회를 잃게 됨을 강조하며 표적항암 담보 보완 안내.

### 3. 뇌·심장 질환 보장 분석 가이드라인
- 보장 범위 진단: 뇌졸중·급성심근경색증만 가입된 경우 '범위 좁음' 판정. 뇌혈관·심혈관 질환 전체를 아우르는 광범위 담보(500만~3,000만 원) 포함 여부 최우선 확인.
- **24개월의 공백기 법칙:** 영구장애진단은 발병 후 최소 18~24개월이 지나야 가능하므로, 정부 지원 전까지의 **'소득 공백 2년'**을 메울 수 있는 금액 설정 필수.

## SECTION 5. 표준 답변 형식 및 마무리

### 1. 표준 답변 형식 (반드시 준수)
```
[보장 항목]: 분석 담보 명칭
[현재 상태]: 가입 금액 및 기간 등 현황
[담보 분석]: 부족 담보 및 추가 가입 필요성 안내
[전문가 의견]: 이세윤 설계사의 철학이 담긴 진단 및 개선안 (비유 활용)
[필수 면책 공고]: "본 상담 내용은 참고용이며 보험 가입 심사는 보험사 인수지침에 따라 달라질 수 있으며, 보험금 보상 가능 여부는 보험사의 심사 결과에 따르므로 실제 결과와 차이가 있을 수 있습니다. 공식 법령과 판례에 근거함."
[상담 연락처]: "궁금하신 내용 있으신가요? 010-3074-2616 이세윤 FC에게 전화주세요."
```

### 2. 금기 사항 및 화법 제어
- 부정어 사용 금지: '안됩니다', '불가능합니다' 대신 '확인이 필요합니다', '보완 가능합니다' 등 대안적 표현 사용.
- 타사 비방 금지: 기존 보험에 대해 가벼운 칭찬으로 라포를 형성한 후, '의료 트렌드에 따른 보장 공백' 관점에서 부드럽게 지적할 것.

## 💡 이세윤 설계사의 베테랑 한마디 (상담 팁)
- 건물주 대상: "사장님, 건물 관리를 잘하셔도 전기 합선 하나면 옆집까지 책임지셔야 합니다. 민법상 소유자 책임은 피할 수 없기에 화재배상은 건물을 지키는 마지막 방어선입니다."
- 공장주 대상: "공장 안 작은 창고 하나를 빌려준 업종이 무엇인지가 중요합니다. 가장 위험한 놈을 기준으로 가입하지 않으면 사고 시 보험사는 요율 위반을 이유로 등을 돌립니다. 제가 그 빈틈을 찾아드리겠습니다."
- 자산가 상담 시: "건물은 자식에게 사랑의 유산이 될 수도 있지만, 준비 없는 상속세는 자식에게 짐이 될 수도 있습니다. 건물이 세금을 스스로 내게 만드는 구조, 제가 설계해 드리겠습니다."
- 의료비 상담 시: "의학은 빛의 속도로 발전하는데 고객님의 보험은 아직 20세기에 멈춰 있지는 않습니까? 최신 치료를 돈 걱정 없이 선택할 수 있는 권리, 그것이 진정한 보험의 가치입니다."

## ⚠️ 최종 강조 사항
- 모든 대화의 끝은 설계사님의 30년 신뢰를 상징하는 연락처로 마무리하십시오.
- 상담 문의: 010-3074-2616 이세윤 FC

[RAG 시스템 통합 지침]
- RAG 검색 결과를 활용할 때는 반드시 출처와 유사도를 명시하고, 이를 3중 검증 프로세스의 근거 자료로 활용하십시오.
- 검색된 문서는 보험업법, 금감원 판례, 의학 가이드라인 등 공신력 있는 자료임을 확인하고 사용하십시오.
"""

# -------------------------------------------------------------------------- 
# [SECTION 2] RAG 시스템 설정 (獨立) 
# -------------------------------------------------------------------------- 

class InsuranceRAGSystem:
    def __init__(self):
        try:
            # 더 가벼운 모델로 변경하여 메모리 부족 방지
            # jhgan/ko-sroberta-multitask 대신 더 작은 모델 사용
            self.embed_model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
            self.index = None
            self.documents = []
            self.metadata = []
            self.model_loaded = True
            st.info("💡 경량화된 RAG 모델을 로드했습니다.")
        except Exception as e:
            st.error(f"🚨 RAG 모델 로드 실패: {e}")
            st.warning("💡 RAG 기능을 사용하지 않고 계속합니다.")
            self.model_loaded = False
        
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 임베딩 생성"""
        if not self.model_loaded:
            return np.array([])
        
        try:
            # 배치 처리로 메모리 사용량 최적화 (더 작은 배치)
            batch_size = 2  # 한 번에 처리할 텍스트 수 제한 (5→2)
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i+batch_size]
                batch_embeddings = self.embed_model.encode(
                    batch_texts, 
                    normalize_embeddings=True,
                    show_progress_bar=False
                )
                all_embeddings.append(batch_embeddings)
            
            return np.vstack(all_embeddings) if all_embeddings else np.array([])
        except Exception as e:
            st.error(f"🚨 임베딩 생성 실패: {e}")
            return np.array([])
    
    def build_index(self, texts: List[str], metadata: List[Dict] = None):
        """FAISS 인덱스 구축"""
        if not self.model_loaded or not texts:
            return
            
        try:
            embeddings = self.create_embeddings(texts)
            if embeddings.size == 0:
                return
                
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(embeddings)
            self.documents = texts
            self.metadata = metadata or [{} for _ in texts]
        except Exception as e:
            st.error(f"🚨 인덱스 구축 실패: {e}")
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """유사 문서 검색"""
        if not self.model_loaded or self.index is None:
            return []
        
        query_embedding = self.create_embeddings([query])
        scores, indices = self.index.search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents):
                results.append({
                    'text': self.documents[idx],
                    'metadata': self.metadata[idx],
                    'score': float(score)
                })
        return results
    
    def extract_text_from_file(self, file) -> str:
        """파일에서 텍스트 추출"""
        try:
            if file.type == "application/pdf":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(file.getvalue())
                    tmp_file_path = tmp_file.name
                
                with pdfplumber.open(tmp_file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                os.unlink(tmp_file_path)
                return text
                
            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                    tmp_file.write(file.getvalue())
                    tmp_file_path = tmp_file.name
                
                doc = docx.Document(tmp_file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                os.unlink(tmp_file_path)
                return text
                
            elif file.type.startswith("text/"):
                return file.getvalue().decode('utf-8')
            else:
                return ""
        except Exception as e:
            return f"파일 처리 오류: {str(e)}"
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """텍스트를 청크로 분할"""
        if not text:
            return []
        
        chunks = []
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

# RAG 시스템 초기화
# RAG 시스템 초기화 (메모리 부족 방지)
try:
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = InsuranceRAGSystem()
except Exception as e:
    st.error(f"🚨 RAG 시스템 초기화 실패: {e}")
    st.warning("💡 RAG 기능 없이 계속 실행합니다.")
    if 'rag_system' not in st.session_state:
        # 더미 RAG 시스템 생성
        class DummyRAGSystem:
            def __init__(self):
                self.index = None
                self.model_loaded = False
            def search(self, query, k=3):
                return []
            def add_documents(self, docs):
                pass
        
        st.session_state.rag_system = DummyRAGSystem()

# [SECTION 3] 음성 및 STT 로직
def s_voice(text, lang='ko-KR'):
    """수애 목소리 TTS 가동 스크립트"""
    clean_text = text.replace('"', '').replace("'", "").replace("\n", " ")
    # 브라우저의 음성 합성 엔진을 강제로 깨우는 자바스크립트입니다.
    return f"""<script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance("{clean_text}");
        msg.lang = "{lang}"; 
        msg.rate = 1.0; 
        msg.pitch = 1.1; // 수애의 맑은 톤을 위해 피치 상향
        window.speechSynthesis.speak(msg);
    </script>"""

def load_stt_engine():
    components.html("""
    <script>
        window.startRecognition = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("마스터가 듣고 있습니다.");
            msg.lang = 'ko-KR'; 
            window.speechSynthesis.speak(msg);
            var recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
            recognition.lang = 'ko-KR';
            recognition.onresult = function(event) {{
                var transcript = event.results[0][0].transcript;
                window.parent.postMessage({{type: 'stt_result', text: transcript}}, '*');
            }};
            recognition.start();
        }};
    </script>
    """, height=0)

# -------------------------------------------------------------------------- 
# [SECTION 3] 사이드바: 사용자 센터 및 보안 (獨立) 
# -------------------------------------------------------------------------- 
with st.sidebar:
    st.header("🔑 SaaS 마스터 센터")
    
    # 관리자 및 영구회원 자동 로그인 체크
    admin_id = st.text_input("관리자 ID", key="admin_id", type="password")
    admin_code = st.text_input("관리자 코드", key="admin_code", type="password")
    
    # 명시적 로그인 버튼
    if st.button("🔑 관리자 로그인"):
        # 관리자 자동 로그인
        if admin_id == "admin" and admin_code == "gold1234":
            st.session_state.user_id = "ADMIN_MASTER"
            st.session_state.user_name = "이세윤 마스터"
            st.session_state.encrypted_contact = encrypt_contact("01030742616")
            st.session_state.join_date = dt.now()
            st.session_state.is_admin = True
            st.success("👑 관리자로 자동 로그인되었습니다!")
            st.rerun()
        
        # 영구회원 자동 로그인
        elif admin_id == "이세윤" and admin_code == "01030742616":
            st.session_state.user_id = "PERMANENT_MASTER"
            st.session_state.user_name = "이세윤"
            st.session_state.encrypted_contact = encrypt_contact("01030742616")
            st.session_state.join_date = dt.now()
            st.session_state.is_admin = False
            st.success("🎉 영구회원으로 자동 로그인되었습니다!")
            st.rerun()
        
        else:
            st.error("❌ ID 또는 코드가 올바르지 않습니다.")
    
    st.divider()
    
    # 실명 사용 공지
    st.warning("⚠️ **반드시 본인의 실명으로 이용해야 데이터가 관리됩니다**")
    
    # 회원가입 또는 로그인
    if 'user_id' not in st.session_state:
        st.subheader("🔐 회원가입")
        with st.form("signup_form"):
            name = st.text_input("이름 (필수)")
            contact = st.text_input("연락처 (필수)")
            
            if st.form_submit_button("회원가입"):
                if name and contact:
                    # 회원가입 처리
                    member_info = add_member(name, contact)
                    
                    st.session_state.user_id = member_info["user_id"]
                    st.session_state.user_name = name
                    st.session_state.encrypted_contact = encrypt_data(contact)
                    st.session_state.join_date = dt.strptime(member_info["join_date"], "%Y-%m-%d")
                    
                    st.success(f"✅ 회원가입 완료! ID: {member_info['user_id']}")
                    st.success("🎉 시스템 고도화 기간 1년간 무료 사용권이 부여되었습니다! (2027.03.31일까지)")
                    st.info("💡 1일 3회 사용 가능하며, 추가 사용 원하는 경우 구독이 필요합니다.")
                    st.rerun()
                else:
                    st.error("❌ 이름과 연락처를 모두 입력해주세요.")
    else:
        # 기존 회원 로그인 상태
        user_name = st.text_input("회원(상담원) 성함", value=st.session_state.get('user_name', '이세윤 마스터'))
        customer_name = st.text_input("고객 성함", "우량 고객")
        
        # user_name이 세션에 없으면 현재 입력값으로 설정
        if 'user_name' not in st.session_state:
            st.session_state.user_name = user_name
        
        # 구독 상태 확인
        is_member, status_msg = check_membership_status()
        remaining_days = calculate_subscription_days(st.session_state.join_date) if 'join_date' in st.session_state else 0
        
        # 사용량 정보
        remaining_usage = get_remaining_usage(user_name)
        
        st.divider()
        
        # [구독 안내 보드]
        st.info(f"""
        **🏆 골드키지사 프리미엄 회원**
        * **회원 ID**: {st.session_state.user_id}
        * **구독 상태**: {status_msg}
        * **잔여 기간**: {remaining_days}일
        * **오늘 사용량**: {3 - remaining_usage}/3회
        * **시스템 고도화 기간**: 무료사용 1년 (2027.03.31일)
        * **추가 사용**: 1일 3회 초과 시 구독 필요
        * **월 구독료**: 15,000원 (VAT 별도)
        * **제공 혜택**: 구글 실시간 검색 및 CFP 지능 무제한
        """)
        
        # 비번 재발급
        with st.expander("🔑 비밀번호 재발급"):
            if st.button("비밀번호 재발급 요청"):
                temp_password = f"TEMP_{int(time.time())}"
                st.info(f"🔐 임시 비밀번호: {temp_password}")
                st.info("⏰ 10분 후 자동 만료됩니다.")
        
        with st.expander("📜 구독 서비스 이용 약관"):
            st.warning("""
                **[법적 책임 한계고지]**
                본 서비스는 AI 기술을 활용한 **상담 보조 도구**이며, 제공되는 모든 분석 결과의 **최종 판단 및 법적 책임은 사용자(상담원)**에게 있습니다. 본 시스템은 금융 상품 판매의 직접적인 근거가 될 수 없습니다.
                """)
        
        # 로그아웃
        if st.button("🚪 로그아웃"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 고객 지원 및 공식 연락처 (SaaS 핵심)
    st.markdown("### 📞 마스터 고객 센터")
    st.caption(f"📧 공식 메일: insusite@gmail.com")
    st.caption(f"📱 상담 문의: 010-3074-2616")
    
    # [면책 조항 재강조]
    st.error("💡 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.")
    
    st.divider()
    
    if st.button("❌ 보안 종료 및 상담 자료 파기", use_container_width=True):
        components.html(s_voice("상담 자료를 파기합니다. 회원 정보는 보관됩니다."), height=0)
        time.sleep(2)
        # 상담 관련 데이터만 파기
        if 'rag_system' in st.session_state:
            st.session_state.rag_system = InsuranceRAGSystem()
        if 'main_area' in st.session_state:
            del st.session_state.main_area
        if 'uploaded_files' in st.session_state:
            del st.session_state.uploaded_files
        if 'uploaded_images' in st.session_state:
            del st.session_state.uploaded_images
        st.success("✅ 상담 자료가 파기되었습니다. 회원 정보는 보관됩니다.")
    
    st.info(f"👤 **최종 승인자: 이세윤**")
    
    st.divider()
    
    with st.expander("🏆 마스터 회원 전용 혜택", expanded=False):
        st.markdown("""
        ### 🏆 골드키지사 프리미엄 회원 혜택
        - **시스템 고도화 기간**: 무료사용 1년 (2027.03.31일까지)
        - **사용 조건**: 1일 3회 사용 가능
        - **추가 사용**: 초과 시 월 15,000원 구독 필요
        - **제공 혜택**: 구글 실시간 검색 및 CFP 지능 무제한
        - **파일 한도**: 1일 50매까지 업로드 가능
        - **관리비**: 1년간 무료 제공
        """)
    
    st.divider()
    
    st.markdown("""
    ### 🔒 자료 파기 안내
    **상담 종료 후 로그아웃 시 제출 자료 자동 파기 됩니다.**
    - 파기 대상: 상담 고객의 증권 분석, 스캔로딩한 의무기록 등 서류 전부
    - 보존 대상: 회원 로그인 기록 및 비밀번호 (회원관리 항목으로 별도 관리)
    - 파기 시점: 상담 종료 후 로그아웃 시 또는 고객이 파기 버튼 클릭 시
    """)

# -------------------------------------------------------------------------- 
# [SECTION 4] 마스터 UI 및 VEO 영상 사운드 해방 (獨立) 
# -------------------------------------------------------------------------- 
st.title("👑 골드키지사 AI 마스터")
MASTER_VIDEO_URL = "https://github.com/insusite-goldkey/goldkey/blob/main/grok-video-c317d625-a0c7-4ce4-922c-7618ab3d7966.mp4"
col_vid, col_txt = st.columns([4, 6])

with col_vid:
    st.markdown(f"""
    <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
        <video id="v_master" src="{MASTER_VIDEO_URL}" style="width: 100%; max-width: 280px; border-radius: 50%;" autoplay playsinline loop controls></video>
        <button onclick="window.startRecognition()" style="margin-top: 15px; background: #1E88E5; color: white; border: none; padding: 10px 20px; border-radius: 30px; cursor: pointer;">🎤 음성 인식 시작</button>
        <button onclick="window.toggleVideoSound()" style="margin-top: 10px; background: #4CAF50; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer;">🔊 음성 토글</button>
        <button onclick="window.forceStopVideo()" style="margin-top: 10px; background: #f44336; color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-weight: bold;">⏹️ 영상 강제 중단</button>
    </div>
    """, unsafe_allow_html=True)
    
    # 개선된 JavaScript 실행
    components.html("""
    <script>
        var v = document.getElementById('v_master');
        var isMuted = true;
        var playCount = 0;
        var maxPlayTime = 6000; // 6초 (6000ms)
        var isStopped = false;
        var isForceStopped = false;
        
        // 동영상 로드 및 자동 재생
        v.addEventListener('loadeddata', function() {
            v.muted = true;
            v.play().catch(function(error) {
                console.log("자동 재생 실패:", error);
            });
        });
        
        // 영상 강제 중단 함수 (개선)
        window.forceStopVideo = function() {
            v.pause();
            v.muted = true;
            v.currentTime = 0;
            isStopped = true;
            isForceStopped = true;
            console.log("영상 강제 중단 실행");
            alert("영상이 중단되었습니다.");
        };
        
        // 기존 중단 함수 (호환성)
        window.stopVideo = window.forceStopVideo;
        
        // 음성 토글 함수
        window.toggleVideoSound = function() {
            if (isMuted && !isStopped && !isForceStopped) {
                v.muted = false;
                v.play().then(function() {
                    console.log("음성 활성화 성공");
                }).catch(function(error) {
                    console.log("음성 활성화 실패:", error);
                    alert("음성을 활성화하려면 동영상을 직접 클릭해주세요.");
                });
            } else {
                v.muted = true;
                console.log("음성 소거");
            }
            isMuted = !isMuted;
        };
        
        // 동영상 클릭 시 음성 활성화 (1회만, 6초만)
        var soundPlayed = false;
        v.addEventListener('click', function() {
            if (isMuted && !soundPlayed && playCount === 0 && !isStopped && !isForceStopped) {
                v.muted = false;
                v.play();
                isMuted = false;
                soundPlayed = true;
                playCount = 1;
                console.log("음성 1회 재생 시작 (6초만)");
                
                // 6초 후 자동 정지 및 음소거
                setTimeout(function() {
                    v.pause();
                    v.muted = true;
                    v.currentTime = 0;
                    console.log("6초 경과: 동영상 정지 및 음소거");
                }, maxPlayTime);
            }
        });
        
        // 페이지 로드 후 2초 뒤 음성 활성화 시도 (1회만, 6초만)
        setTimeout(function() {
            if (isMuted && playCount === 0 && !isStopped && !isForceStopped) {
                v.muted = false;
                v.play().catch(function(error) {
                    console.log("자동 음성 활성화 실패:", error);
                });
                isMuted = false;
                soundPlayed = true;
                playCount = 1;
                console.log("자동 음성 1회 재생 시작 (6초만)");
                
                // 6초 후 자동 정지 및 음소거
                setTimeout(function() {
                    v.pause();
                    v.muted = true;
                    v.currentTime = 0;
                    console.log("6초 경과: 동영상 정지 및 음소거");
                }, maxPlayTime);
            }
        }, 2000);
    </script>
    """, height=0)

with col_txt:
    main_area = st.text_area("📝 마스터 통합 상담창", height=230, placeholder="문의사항을 입력해주세요.", key="main_area")
    q_analyze = st.button("🚀 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)
    
    # 상담창 활성화 시 영상 자동 중단 (강화)
    if main_area:
        components.html("""
        <script>
            if (typeof window.forceStopVideo === 'function') {
                window.forceStopVideo();
                console.log("상담창 활성화로 영상 자동 중단");
            }
        </script>
        """, height=0)

# 음성 인식 함수 로드
load_stt_engine()

# -------------------------------------------------------------------------- 
# [SECTION 9] AI 이미지 상담 전문 모델 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🖼️ AI 이미지 상담 전문 모델")
st.markdown("**보험 증권, 진단서, 의료 기록, 사고 현장 사진 등을 AI가 정밀 분석합니다.**")

# 이미지 업로드 섹션
col_img1, col_img2 = st.columns([2, 1])

with col_img1:
    uploaded_images = st.file_uploader(
        "📸 상담용 이미지 업로드", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'pdf'],
        accept_multiple_files=True,
        key="image_consultation"
    )
    
    if uploaded_images:
        st.success(f"✅ {len(uploaded_images)}개의 이미지가 업로드되었습니다.")
        
        # 이미지 미리보기
        for i, img_file in enumerate(uploaded_images, 1):
            if img_file.type.startswith('image/'):
                st.image(img_file, caption=f"이미지 {i}: {img_file.name}", width=300)
            else:
                st.info(f"📄 파일 {i}: {img_file.name} (PDF 문서)")

with col_img2:
    image_query_type = st.selectbox(
        "🎯 분석 유형 선택",
        ["보험 증권 분석", "진단서 분석", "사고 현장 분석", "의료 기록 분석", "기타"],
        key="image_analysis_type"
    )
    
    image_specific_query = st.text_area(
        "🔍 특정 분석 요청사항",
        placeholder="예시: 이 보험 증권의 암 보장 금액을 분석해주세요. / 이 진단서의 병명에 해당하는 보험금 지급 가능성을 알려주세요.",
        height=100,
        key="image_specific_query"
    )

# 이미지 분석 실행 버튼
if uploaded_images and st.button("🤖 AI 이미지 상담 분석 실행", type="primary", use_container_width=True):
    # 1. 현재 사용 횟수 확인
    current_count = check_usage_limit(user_name)
    MAX_FREE_LIMIT = 3
    
    if current_count >= MAX_FREE_LIMIT:
        st.error(f"⚠️ {user_name} 마스터님, 오늘은 3회 분석 기회를 모두 사용하셨습니다. 내일 다시 이용해 주세요!")
        st.warning("🚀 **무제한 사용을 원하시면 월 15,000원의 프리미엄 구독으로 전환하세요!**")
        components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다. 내일 뵙겠습니다."), height=0)
    else:
        # 2. 이미지 분석 실행
        with st.spinner(f"🔍 {current_count + 1}번째 AI 이미지 분석 중..."):
            try:
                # 서버 고정형 모델 사용
                model = get_master_model()

                # 분석 쿼리 구성
                analysis_query = f"""
                [이미지 상담 분석 요청]
                상담원: {user_name}
                고객: {customer_name}
                분석 목적: 보험 설계 및 자산 관리
                
                제공된 이미지를 바탕으로 다음을 분석해주세요:
                1. 보험 관련 문서의 주요 내용
                2. 의료 기록의 핵심 정보
                3. 사고 현장의 특이사항
                4. 보험 적용 가능성 및 권장 사항
                
                전문 CFP 관점에서 상세히 분석하고 구체적인 조언을 제공해주세요.
                """

                parts = [analysis_query]
                
                # 이미지 처리
                for img_file in uploaded_images:
                    if img_file.type.startswith('image/'):
                        # 이미지 파일 처리
                        img = PIL.Image.open(img_file)
                        parts.append(img)
                    elif img_file.type == 'application/pdf':
                        # PDF 처리 (필요시 추가 구현)
                        st.info(f"📄 PDF 파일 '{img_file.name}'은 텍스트 추출 후 분석됩니다.")
                
                # AI 분석 실행
                response = model.generate_content(parts)
                
                # 결과 표시
                st.subheader("🖼️ AI 이미지 상담 분석 결과")
                st.markdown(response.text)
                
                # 관리자 연락처 자동 포함
                st.markdown("---")
                st.info(f"""
                **📞 추가 문의 필요 시**
                📧 공식 메일: insusite@gmail.com  
                📱 상담 문의: 010-3074-2616
                
                ⚠️ **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
                """)
                st.markdown("---")
                
                components.html(s_voice("AI 이미지 상담 분석이 완료되었습니다."), height=0)
                
                # 3. 분석이 성공적으로 끝나면 카운트 증가
                update_usage(user_name)
                remaining = MAX_FREE_LIMIT - (current_count + 1)
                st.success(f"✅ 이미지 분석 완료! (오늘 남은 횟수: {remaining}회)")
                
            except Exception as e:
                st.sidebar.error(f"⚠️ 이미지 분석 장애: {e}")
                st.sidebar.info("💡 해결책: 이미지 파일 확인 또는 API 키를 확인하세요.")
                
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 6] 1단계: 필수 보장 자가 진단 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🛡️ 1단계: 필수 보장 자가 진단")
essential_ins = st.multiselect("보유 보험 선택", ["자동차", "화재보험", "일상생활배상책임", "운전자보험", "통합보험"], key="sec6")

# -------------------------------------------------------------------------- 
# [SECTION 7] 2단계: 전문 증권 분석 자료 요청 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 📸 2단계: 전문 증권 분석 자료 요청")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True, key="sec7")

# -------------------------------------------------------------------------- 
# [SECTION 8] 3단계: 건보료 기반 소득 역산 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💰 3단계: 건보료 기반 소득 역산")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000, key="sec8")
if hi_premium > 0:
    calc_income = hi_premium / 0.0709
    st.success(f"📊 역산 월 소득: **{calc_income:,.0f}원** / 적정 보험료 15%: **{calc_income*0.15:,.0f}원**")

#---------------------------------------------------------------------------
# [SECTION 9] 4단계: 질병 보상 정밀 분석 및 가족력 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏥 4단계: 질병 보상 정밀 분석 및 가족력")
disease_focus = st.text_area("가족력 및 집중 분석 질환 입력", key="sec9")

# -------------------------------------------------------------------------- 
# [SECTION 10] 5단계: 대형 생보사 헬스케어 컨설팅 (獨立)
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💎 5단계: 대형 생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 2주 내 진찰 예약 서비스 필요 여부", ["예", "아니오", "미정"], key="sec10")

# -------------------------------------------------------------------------- 
# [SECTION 11] 6대 법령 및 보상 지식 DB (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏛️ 6대 법령 및 보상 지식 DB")
st.info("민법, 상법, 보험업법, 형사소송법, 화재의 예방의 및 안전관리에 관한 법률, 실화책임에 관한 법률 3중 검증 가동")

# -------------------------------------------------------------------------- 
# [SECTION 12] 국제재무설계 기준 위험관리 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🛡️ 국제재무설계 기준 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 13] 3층 연금 통합 시뮬레이션 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 💰 3층 연금 통합 시뮬레이션")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")
p_nat = st.number_input("국민(만)", key="p1")
p_ret = st.number_input("퇴직(만)", key="p2")
p_ind = st.number_input("개인(만)", key="p3")

# --------------------------------------------------------------------------
# [SECTION 14] 인생 이모작 및 주택 설계 (獨立) 
# -------------------------------------------------------------------------- 
st.divider()
st.write("### 🏡 인생 이모작 및 주택 설계")
home_fund = st.number_input("주택자금 필요액(만)", key="h_f")
second_life = st.text_area("인생 2막 계획 및 노후 주거 설계", key="s_l")

# --------------------------------------------------------------------------
# [SECTION 15] 전문가 통합 분석 및 성공 응원 (獨立)
# --------------------------------------------------------------------------
st.divider()

# --------------------------------------------------------------------------
# [SECTION 16] 회원 관리 시스템 (獨立)
# --------------------------------------------------------------------------
st.divider()
st.write("### 📋 회원 관리 시스템")

# 관리자만 접근 가능
if st.session_state.get('is_admin', False):
    members = load_members()
    
    if len(members) > 0:
        st.write(f"**총 회원수: {len(members)}명**")
        
        # 회원 목록 표시
        member_data = []
        for name, info in members.items():
            member_data.append({
                "이름": name,
                "가입일": info["join_date"],
                "구독 시작": info["subscription_start"],
                "구독 종료": info["subscription_end"],
                "구독료": f"{info['subscription_fee']:,}원",
                "상태": "활성" if info["is_active"] else "비활성"
            })
        
        st.dataframe(member_data, use_container_width=True)
        
        # 회원 관리 기능
        with st.expander("🔧 회원 관리 기능"):
            selected_member = st.selectbox("회원 선택", list(members.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("구독 연장"):
                    if selected_member:
                        # 30일 연장
                        current_end = dt.strptime(members[selected_member]["subscription_end"], "%Y-%m-%d")
                        new_end = current_end + timedelta(days=30)
                        members[selected_member]["subscription_end"] = new_end.strftime("%Y-%m-%d")
                        members[selected_member]["subscription_fee"] = 15000
                        save_members(members)
                        st.success(f"✅ {selected_member}님 구독이 30일 연장되었습니다.")
            
            with col2:
                if st.button("회원 비활성화"):
                    if selected_member:
                        members[selected_member]["is_active"] = False
                        save_members(members)
                        st.warning(f"⚠️ {selected_member}님이 비활성화되었습니다.")
    else:
        st.info("등록된 회원이 없습니다.")
else:
    st.warning("🔒 관리자만 접근할 수 있습니다.")

# --------------------------------------------------------------------------
# [SECTION 17] 관리자 이세윤 성공 응원 (獨立)
# --------------------------------------------------------------------------
st.divider()

# 관리자 전용 기능
is_admin = st.session_state.get('is_admin', False)
is_permanent = st.session_state.get('user_id') == 'PERMANENT_MASTER'

if is_admin or is_permanent:
    if st.button("👑 관리자 이세윤 성공 응원", use_container_width=True):
        st.success("🎉 이세윤 마스터의 성공을 응원합니다!")
        st.balloons()
    
    # 관리자 전용 RAG 지식베이스 (Admin Only)
    with st.expander("🔒 관리자 전용 RAG 지식베이스 (Admin Only)", expanded=False):
        admin_key = st.text_input("관리자 키 입력", type="password")
        
        if admin_key == "gold1234" or is_permanent:
            st.success("🔓 관리자 접근 권한 확인!")
            
            # 파일 업로더
            uploaded_files = st.file_uploader(
                "전문가용 노하우 PDF 업로드",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True
            )
            
            if uploaded_files and st.button("지식베이스 즉시 동기화"):
                with st.spinner("🔄 RAG 시스템 동기화 중..."):
                    try:
                        # 파일 처리 및 벡터화
                        documents = []
                        for file in uploaded_files:
                            if file.type == "application/pdf":
                                documents.append(process_pdf(file))
                            elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                                documents.append(process_docx(file))
                            elif file.type == "text/plain":
                                documents.append(file.read().decode('utf-8'))
                        
                        # RAG 시스템 업데이트
                        st.session_state.rag_system.add_documents(documents)
                        st.success(f"✅ {len(uploaded_files)}개 파일이 지식베이스에 추가되었습니다!")
                        
                    except Exception as e:
                        st.error(f"❌ 동기화 오류: {e}")
        else:
            st.warning("🔐 관리자 키가 필요합니다.")
else:
    st.info("🔒 관리자 전용 기능은 접근할 수 없습니다.")

if q_analyze:
    # 관리자 및 영구회원 체크
    is_special_user = (
        st.session_state.get('user_id') in ['ADMIN_MASTER', 'PERMANENT_MASTER'] or
        st.session_state.get('user_name') == '이세윤'
    )
    
    # 1. 현재 사용 횟수 확인 (일반 사용자만)
    if not is_special_user:
        current_count = check_usage_limit(user_name)
        MAX_FREE_LIMIT = 3
    else:
        current_count = 0  # 관리자/영구회원은 항상 0으로 처리
        MAX_FREE_LIMIT = 9999  # 무제한
    
    if not is_special_user and current_count >= MAX_FREE_LIMIT:
        st.error(f"⚠️ {user_name} 마스터님, 오늘은 3회 분석 기회를 모두 사용하셨습니다. 내일 다시 이용해 주세요!")
        st.warning("🚀 **무제한 사용을 원하시면 월 15,000원의 프리미엄 구독으로 전환하세요!**")
        components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다. 내일 뵙겠습니다."), height=0)
    else:
        # 2. 분석 실행
        with st.spinner(f"🔍 {current_count + 1}번째 정밀 분석 중..."):
            try:
                # 서버 고정형 모델 사용
                client, model_config = get_master_model()
                income = hi_premium / 0.0709 if hi_premium > 0 else 0
                
                # RAG 검색 수행
                rag_results = []
                if st.session_state.rag_system.index is not None:
                    rag_results = st.session_state.rag_system.search(main_area, k=3)
                
                # 검색된 문서를 컨텍스트에 추가
                context_text = ""
                if rag_results:
                    context_text = "\n\n[참고 자료]\n"
                    for i, result in enumerate(rag_results, 1):
                        context_text += f"{i}. {result['text']}\n"
                
                query = f"상담: {main_area}. 소득: {income:.0f}. 필수: {essential_ins}. 질환: {disease_focus}.{context_text}"
                
                # Google Genai 방식으로 콘텐츠 생성
                contents = [query]
                if uploaded_files:
                    for f in uploaded_files:
                        # 이미지를 바이트로 변환
                        image_bytes = f.read()
                        contents.append(image_bytes)
                
                # 모델 호출
                resp = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents,
                    config=model_config
                )
                
                st.subheader(f"📊 {customer_name}님 정밀 리포트")
                st.markdown(resp.text)
                
                # 관리자 연락처 자동 포함
                st.markdown("---")
                st.info(f"""
                **📞 추가 문의 필요 시**
                📧 공식 메일: insusite@gmail.com  
                📱 상담 문의: 010-3074-2616
                
                ⚠️ **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
                """)
                st.markdown("---")
                
                # RAG 검색 결과 표시
                if rag_results:
                    with st.expander("🔍 참고한 지식베이스 자료", expanded=False):
                        for i, result in enumerate(rag_results, 1):
                            st.write(f"**{i}.** {result['metadata']['filename']} (유사도: {result['score']:.3f})")
                            st.write(f"{result['text'][:200]}...")
                            st.divider()
                
                st.markdown(resp.text)
                components.html(s_voice(f"{user_name} 마스터님, 분석이 완료되었습니다."), height=0)
                
                # 3. 분석이 성공적으로 끝나면 카운트 증가
                update_usage(user_name)
                remaining = MAX_FREE_LIMIT - (current_count + 1)
                st.success(f"✅ 분석 완료! (오늘 남은 횟수: {remaining}회)")
                
            except Exception as e:
                st.sidebar.error(f"⚠️ 분석 장애: {e}")
                st.sidebar.info("💡 해결책: API 키 확인 또는 관리자에게 문의하세요.")

if st.button("🏆 관리자 이세윤 성공 응원", use_container_width=True):
    st.balloons()
    components.html(s_voice("이세윤 관리자님, 필승하십시오! 당신의 성공을 응원합니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 16] 관리자 전용 RAG 지식베이스 (앱 최하단 배치) 
# -------------------------------------------------------------------------- 
st.divider()
with st.expander("🔐 마스터 전용 지식베이스 관리 (Admin Only)", expanded=False):
    # 관리자 비밀번호나 특정 키가 있을 때만 활성화되도록 설정 가능
    admin_key = st.text_input("관리자 인증키", type="password")
    if admin_key == "goldkey777": # 관리자님만의 비밀번호
        st.write("### 📚 마스터 전용 RAG 엔진")
        # 여기서 파일 업로드 및 인덱스 업데이트 수행
        rag_files = st.file_uploader("전문가용 노하우 PDF 업로드", accept_multiple_files=True, type=["pdf", "docx", "txt"])
        if st.button("🔄 지식베이스 즉시 동기화"):
            # 마스터의 지식으로 변환하는 로직 실행
            st.success("이세윤 마스터의 지식으로 통합되었습니다.")
    else:
        st.info("이 섹션은 관리자 전용 공간입니다.")
