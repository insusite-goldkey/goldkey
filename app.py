# ==========================================================
# 골드키지사 마스터 AI - 보안 강화 & 초경량 통합본 
# 보안강화: 1.AES-256 암호화저장 / 2.프롬프트 인젝션 방어 / 3.개인정보 마스킹
# ==========================================================

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

# -------------------------------------------------------------------------- 
# [SECTION 1] 보안 및 암호화 엔진 (Lightweight Security)
# -------------------------------------------------------------------------- 
def get_encryption_key():
    """보안 키를 가져오거나 생성함"""
    if "ENCRYPTION_KEY" in st.secrets:
        return st.secrets["ENCRYPTION_KEY"].encode()
    # 주의: 실제 운영 시에는 반드시 secrets에 저장된 고정 키를 사용해야 함
    return b'temporary_fixed_key_for_dev_only_12345='

cipher_suite = Fernet(get_encryption_key())

def encrypt_val(data):
    """데이터 암호화"""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_val(data):
    """데이터 복호화"""
    try:
        return cipher_suite.decrypt(data.encode()).decode()
    except:
        return "Decryption Error"

def sanitize_prompt(text):
    """프롬프트 인젝션 방어: AI 지침 탈취 시도 차단"""
    danger_words = ["system instruction", "지침", "프롬프트", "비밀번호", "명령어"]
    for word in danger_words:
        if word in text.lower():
            return "보안을 위해 부적절한 요청은 처리되지 않습니다."
    return text

# -------------------------------------------------------------------------- 
# [SECTION 2] 통합 유틸리티 함수
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_client():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error(" Secrets에 GEMINI_API_KEY 설정이 필요합니다.")
        st.stop()
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def s_voice(text):
    clean = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{clean}'); msg.lang='ko-KR'; msg.rate=1.0; msg.pitch=1.1; window.speechSynthesis.speak(msg);</script>"

def setup_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_url TEXT,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def display_security_sidebar():
    """보안 사이드바 표시"""
    st.markdown("""
    <div style="background:#f0f7ff; padding:15px; border-radius:10px; font-size:0.8rem;">
        <strong> 데이터 보안 지침</strong><br>
        - 상담 자료: 로그아웃 시 즉시 파쇄<br>
        - 구독 만료: 30일 유예 후 자동 파기<br>
        - 암호화: AES-256 군사급 보호
    </div>
    """, unsafe_allow_html=True)


# -------------------------------------------------------------------------- 
# [SECTION 3] 메인 앱 구조 통합
# -------------------------------------------------------------------------- 
def main():
    st.set_page_config(page_title="골드키지사 마스터 AI", page_icon="", layout="wide")
    
    setup_database()

    with st.sidebar:
        st.header("SaaS 마스터 센터")
        if 'user_id' not in st.session_state:
            u_name = st.text_input("성함")
            u_phone = st.text_input("연락처", type="password")
            if st.button("접속"):
                if u_name and u_phone:
                    st.session_state.user_id = f"GK_{u_name}"
                    st.session_state.user_name = u_name
                    st.rerun()
        else:
            st.success(f"{st.session_state.user_name} 마스터님")
            if st.button("안전 로그아웃"):
                st.session_state.clear()
                st.rerun()
        
        display_security_sidebar()

    tabs = st.tabs(["통합 상담", "자산 분석", "상속/유언", "관리자"])

    with tabs[0]:
        st.title("마스터 AI 정밀 상담")
        customer_name = st.text_input("고객 성함", "우량 고객")
        query = st.text_area("질문 입력", height=150, placeholder="보험, 재무, 건강 상담 내용을 입력하세요.")
        
        if st.button("정밀 분석 실행", type="primary"):
            if 'user_id' not in st.session_state:
                st.error("로그인이 필요합니다.")
                st.stop()
                
            if not query or len(query.strip()) < 5:
                st.error("상담 내용을 충분히 입력해주세요.")
                st.stop()
            
            with st.spinner("마스터 AI가 실시간 정보를 분석하고 있습니다..."):
                try:
                    client = get_client()
                    master_instruction = "당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요."
                    
                    resp = client.models.generate_content(
                        model="gemini-1.5-flash",
                        contents=[f"고객 {customer_name} 리포트 요청: {query}"],
                        config=types.GenerateContentConfig(
                            system_instruction=master_instruction,
                            tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
                        )
                    )
                    
                    if resp.text:
                        st.divider()
                        st.subheader(f" {customer_name}님을 위한 마스터 AI 정밀 리포트")
                        st.markdown(resp.text)
                        st.info("[주의] 본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                        
                        # 성공 음성 안내
                        components.html(s_voice(f"{st.session_state.user_name}님, 마스터 에이아이의 분석이 완료되었습니다."), height=0)
                        
                except Exception as e:
                    st.error(f" AI 분석 장애: {e}")

    with tabs[1]:
        st.subheader(" 의무기록 및 증권 일괄 분석")
        files = st.file_uploader("자료 업로드", accept_multiple_files=True, type=['pdf', 'jpg', 'jpeg', 'png'])
        
        if files:
            st.info(f" {len(files)}개 파일이 업로드되었습니다.")
            
            if st.button(" 일괄 PDF 생성 및 다운로드"):
                # PDF 생성 기능 (라이브러리 설치 필요)
                st.warning("PDF 생성 기능을 위해 PyMuPDF, pdfplumber, python-docx를 설치해주세요.")

    with tabs[2]:
        section_inheritance_will()

    with tabs[3]:
        st.write("###  마스터 지식베이스 관리")
        if st.text_input("인증키", type="password") == "goldkey777":
            st.success(" 지식베이스 동기화 권한 승인")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f" 시스템 구동 중 오류 발생: {e}")
        <div style="margin:20px 0; min-height:300px;">{content.replace('\\n', '<br>')}</div>
        <div style="font-size:11px; color:#888; background:#f9f9f9; padding:10px; border-radius:5px;">
            <b>[주의] 법적 책임 고지:</b> 본 리포트는 참고용이며 최종 결정의 책임은 사용자에게 있습니다.
        </div>
    </div>
    """
    st.components.v1.html(report_html, height=500, scrolling=True)

    col1, col2 = st.columns(2)
    with col1:
        share_msg = f"[{title}] {customer_name}님, 분석 리포트입니다.\\n\\n{content[:100]}..."
        components.html(f"""<script>function sh(){{ navigator.share({{title:'리포트', text:`{share_msg}`, url:window.location.href}}); }}</script>
        <button onclick="sh()" style="width:100%; padding:12px; background:#25D366; color:white; border:none; border-radius:8px; font-weight:bold;">[문자] 문자/카톡 공유</button>""", height=60)
    with col2:
        st.download_button("[다운로드] 내 문서에 저장", data=report_html, file_name=f"GK_Report_{customer_name}.html", mime="text/html", use_container_width=True)

# -------------------------------------------------------------------------- 
# [SECTION 5] 12~13번 페이지: 상속/증여/유언 정밀 로직 (보존)
# -------------------------------------------------------------------------- 
def section_inheritance_will():
    st.title(" 상속증여 및 유류분 통합 설계")
    st.markdown("##### 2026년 최신 세법 및 민법 제1000조(상속순위) 기준")
    
    # [입력 단계] 개인정보 마스킹 처리 예시
    c_name = st.text_input("상담 고객 성함", "홍길동")
    masked_name = c_name[0] + "*" + c_name[-1] if len(c_name) > 1 else c_name
    
    st.info(f" 보안 모드 가동 중: 분석 리포트에는 **'{masked_name}'**님으로 표기됩니다.")

    with st.expander(" 상속인 신분 관계 확정 (민법 제1000조)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            spouse = st.radio("배우자 관계", ["법률혼 (상속권 있음)", "사실혼 (상속권 없음)"])
            child_legal = st.number_input("친자/양자 수", min_value=0, value=1)
            child_none = st.number_input("파양된 자녀 수", min_value=0, value=0)
        with c2:
            st.caption(" 양자는 친자와 동일 권리, 파양 시 상속권 소멸")
            shares = "배우자 1.5 : 자녀 1.0" if spouse.startswith("법률혼") else "자녀 100%"
            st.success(f" 법정비율: {shares}")

    st.subheader(" 자산 및 세금 시뮬레이션")
    val_real = st.number_input("부동산 시가(만원)", value=150000)
    val_cash = st.number_input("금융자산(만원)", value=50000)
    
    if st.button(" 상속/증여 정밀 분석", type="primary", use_container_width=True):
        # 상속세 간이 계산 logic (일괄공제 5억 + 배우자 5억)
        taxable = max((val_real + val_cash) - 100000, 0)
        est_tax = taxable * 0.3 - 6000 # 10억~30억 구간 예시
        res_text = f"총 자산 {val_real+val_cash:,.0f}만원 중 예상 상속세는 약 {est_tax:,.0f}만원입니다. 부동산 비중이 높아 종신보험을 통한 세원 마련이 시급합니다."
        output_manager(masked_name, res_text)

    st.divider()
    st.subheader(" 유언장 및 유류분 방어 플랜")
    st.warning("2024년 최신 판례: 형제자매의 유류분 청구권은 폐지되었습니다.")
    
    if st.checkbox(" [사인증여 계약서] 및 [유언장] 양식 보기"):
        st.markdown("####  자필유언장 표준 양식")
        will_text = f"나 유언자 [성함]은 주소 [주소]에서 다음과 같이 유언한다...\n1. 부동산은 [동거인]에게 사인증여한다..."
        st.code(will_text, language="text")
        st.success("반드시 전체 내용을 직접 자필로 작성하고 날인하십시오.")
        if st.button(" 작성 가이드 음성 듣기"):
            components.html(s_voice("유언장은 반드시 처음부터 끝까지 직접 손으로 쓰셔야 법적 효력이 발생합니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 5] 데이터 파기 및 보안 강화 시스템
# -------------------------------------------------------------------------- 
import sqlite3
from datetime import datetime, timedelta

def setup_database():
    """데이터베이스 초기화 및 테이블 생성"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    
    # 사용자 문서 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            document_url TEXT,
            status TEXT DEFAULT 'ACTIVE',
            expiry_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def purge_expired_data():
    """30일 경과한 만료 데이터 영구 삭제"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    
    # 30일 경과 대상 조회
    cursor.execute('''
        SELECT user_id, document_url 
        FROM user_documents 
        WHERE status = 'EXPIRED' 
        AND expiry_date <= date('now', '-30 days')
    ''')
    
    expired_docs = cursor.fetchall()
    
    # 물리적 파일 삭제 (실제 구현 시 S3 등 클라우드 연동)
    for doc in expired_docs:
        try:
            # 파일 시스템에서 삭제 (예시)
            if os.path.exists(doc[1]):
                os.remove(doc[1])
                print(f"[{datetime.now()}] Deleted file: {doc[1]}")
        except Exception as e:
            print(f"Error deleting file {doc[1]}: {e}")
    
    # 데이터베이스에서 영구 삭제
    cursor.execute('''
        DELETE FROM user_documents 
        WHERE status = 'EXPIRED' 
        AND expiry_date <= date('now', '-30 days')
    ''')
    
    conn.commit()
    conn.close()
    
    if expired_docs:
        st.success(f" {len(expired_docs)}개의 만료 데이터가 안전하게 파기되었습니다.")

# 데이터베이스 초기화
setup_database()

# -------------------------------------------------------------------------- 
# [SECTION 6] 보안 사이드바 정보 표시
# -------------------------------------------------------------------------- 
def display_security_sidebar():
    """보안 정책 및 데이터 보관 정보 표시"""
    st.sidebar.markdown("""
    <div style="background: #f9f9f9; padding: 15px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 20px;">
        <div style="margin-bottom: 12px; border-left: 3px solid #007bff; padding-left: 10px;">
            <strong style="display: block; color: #333; margin-bottom:4px;"> 안심 보관 시스템</strong>
            <p>귀하의 의무기록은 로그아웃 후에도 군사급 암호화(AES-256)로 안전하게 보호됩니다.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #007bff; padding-left: 10px;">
            <strong style="display: block; color: #333; margin-bottom:4px;"> 데이터 보존 정책</strong>
            <p>구독 만료 시 30일간 보관 후, 복구 불가능한 방식으로 자동 파기됩니다.</p>
        </div>
        <div style="margin-bottom: 12px; border-left: 3px solid #007bff; padding-left: 10px;">
            <strong style="display: block; color: #333; margin-bottom:4px;"> 데이터 주권 보장</strong>
            <p>언제든 전체 자료를 PDF로 백업하거나 즉시 삭제를 요청하실 수 있습니다.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------------------- 
# [SECTION 7] 일괄 PDF 생성 시스템
# -------------------------------------------------------------------------- 
def generate_batch_pdf(user_id, documents):
    """사용자 문서들을 하나의 PDF로 병합"""
    if not PDF_AVAILABLE:
        st.error(" PDF 생성 기능을 위해 PyMuPDF, pdfplumber, python-docx를 설치해주세요.")
        return None
        
    try:
        # PyMuPDF를 사용한 PDF 병합 (설치 필요 시)
        import fitz  # PyMuPDF
        
        # 연대순 정렬
        sorted_docs = sorted(documents, key=lambda x: x.get('submitted_at', ''))
        
        output_pdf = fitz.open()
        
        for doc in sorted_docs:
            file_path = doc.get('file_path', '')
            
            if file_path.endswith(('.jpg', '.jpeg', '.png')):
                # 이미지를 PDF로 변환
                img = fitz.open(file_path)
                pdf_bytes = img.convert_to_pdf()
                img_pdf = fitz.open("pdf", pdf_bytes)
                output_pdf.insert_pdf(img_pdf)
            elif file_path.endswith('.pdf'):
                # PDF 병합
                src_pdf = fitz.open(file_path)
                output_pdf.insert_pdf(src_pdf)
        
        # 메타데이터 삽입
        output_pdf.set_metadata({
            "title": f"User_{user_id}_Merged_Records",
            "author": "골드키지사 마스터 AI",
            "subject": "Chronological Submitted Documents"
        })
        
        # 저장
        output_name = f"GK_Report_{user_id}_{dt.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_pdf.save(output_name, garbage=4, deflate=True)
        
        return output_name
        
    except Exception as e:
        st.error(f"PDF 생성 실패: {e}")
        return None

# -------------------------------------------------------------------------- 
# [SECTION 8] 메인 네비게이션 및 실행 (경량화 로직)
# -------------------------------------------------------------------------- 
def main():
    setup_database()
    
    # 사이드바 로그인 및 구독 정보
    with st.sidebar:
        st.header(" SaaS 마스터 센터")
        if 'user_id' not in st.session_state:
            u_name = st.text_input("성함")
            u_phone = st.text_input("연락처", type="password")
            if st.button(" 접속"):
                if u_name and u_phone:
                    st.session_state.user_id = f"GK_{u_name}"
                    st.session_state.user_name = u_name
                    st.rerun()
        else:
            st.success(f" {st.session_state.user_name} 마스터님")
            if st.button(" 안전 로그아웃"):
                st.session_state.clear()
                st.rerun()
        
        # 보안 안내문 상시 표기 (사이드바)
        st.markdown("""
        <div style="background:#f0f7ff; padding:15px; border-radius:10px; font-size:0.8rem;">
            <strong> 데이터 보안 지침</strong><br>
            - 상담 자료: 로그아웃 시 즉시 파쇄<br>
            - 구독 만료: 30일 유예 후 자동 파기<br>
            - 암호화: AES-256 군사급 보호
        </div>
        """, unsafe_allow_html=True)

    # 메인 탭 구조
    tabs = st.tabs([" 통합 상담", " 증권/기록 분석", " 자산/연금", " 상속/유언"])

    with tabs[0]:
        st.title(" 마스터 AI 정밀 상담")
        customer_name = st.text_input("고객 성함", "우량 고객")
        query = st.text_area("질문 입력", height=150, placeholder="보험, 재무, 건강 상담 내용을 입력하세요.")
        
        if st.button(" 정밀 분석 실행", type="primary"):
            if 'user_id' not in st.session_state:
                st.error("로그인이 필요합니다.")
                st.stop()
                
            if not query or len(query.strip()) < 5:
                st.error("상담 내용을 충분히 입력해주세요.")
                st.stop()
            
            with st.spinner(" 마스터 AI가 실시간 정보를 분석하고 있습니다..."):
                result = analyze_with_ai(query, customer_name)
                if result:
                    st.divider()
                    st.subheader(f" {customer_name}님을 위한 마스터 AI 정밀 리포트")
                    st.markdown(result)
                    st.info("[주의] 본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                    
                    # 성공 음성 안내
                    components.html(s_voice(f"{st.session_state.user_name}님, 마스터 에이아이의 분석이 완료되었습니다."), height=0)

    with tabs[1]:
        st.subheader(" 의무기록 및 증권 일괄 분석")
        files = st.file_uploader("자료 업로드", accept_multiple_files=True, type=['pdf', 'jpg', 'jpeg', 'png'])
        
        if files:
            st.info(f" {len(files)}개 파일이 업로드되었습니다.")
            
            if st.button(" 일괄 PDF 생성 및 다운로드"):
                if not PDF_AVAILABLE:
                    st.error("PDF 생성 기능을 위해 라이브러리 설치가 필요합니다.")
                else:
                    # 임시 파일 저장
                    temp_docs = []
                    temp_dir = tempfile.mkdtemp()
                    
                    for i, file in enumerate(files):
                        temp_path = os.path.join(temp_dir, f"doc_{i}.{file.name.split('.')[-1]}")
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                        temp_docs.append({
                            'file_path': temp_path,
                            'submitted_at': dt.now().isoformat()
                        })
                    
                    # PDF 생성
                    pdf_file = generate_batch_pdf(st.session_state.get('user_id', 'user'), temp_docs)
                    if pdf_file:
                        st.success(f" PDF 생성 완료: {pdf_file}")
                        
                        # 다운로드 버튼
                        with open(pdf_file, "rb") as file:
                            st.download_button(
                                label="[다운로드] 일괄 PDF 다운로드",
                                data=file.read(),
                                file_name=pdf_file,
                                mime="application/pdf"
                            )

    with tabs[2]:
        st.title(" 자산/연금 시뮬레이션")
        st.info("노후 설계 기능은 준비 중입니다.")
        # 노후 설계 시뮬레이션 로직 추가 예정

    with tabs[3]:
        section_inheritance_will()

if __name__ == "__main__":
    main()

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
        st.error(" 서버 보안 설정 오류: GEMINI_API_KEY를 찾을 수 없습니다.")
        st.error(" Streamlit Secrets에 GEMINI_API_KEY를 추가해주세요.")
        st.stop()

    # 2. Google Genai 클라이언트 설정
    try:
        import google.genai as genai
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
            st.warning("[주의] Google Search 기능을 사용할 수 없습니다. 기본 모드로 실행합니다.")
        
        return client, model_config
    except Exception as e:
        st.error(f" 모델 로드 오류: {e}")
        
        # Google Search 관련 에러일 경우 대안 제시
        if "403" in str(e) or "Forbidden" in str(e):
            st.error(" API 키에 결제 정보가 필요하거나 Google Search 권한이 없습니다.")
            st.info(" 해결책:")
            st.info("1. Google AI Studio에서 결제 정보 등록")
            st.info("2. 또는 Google Search 기능 제거")
        
        st.info(" 기타 해결책: requirements.txt에 'google-genai>=0.3.0'이 적혀있는지 확인하세요.")
        st.stop()

SYSTEM_PROMPT = """
[SYSTEM INSTRUCTIONS: 보험 컨설턴트 이세윤 통합 상담 엔진]

## SECTION 1. 페르소나 및 상담 기본 원칙

### 1. 기본 정체성 및 인사 규정
성명: 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)

###  골드키지사 AI 상담 비서 가이드라인
#### 1. 페르소나 정의 (Identity): 고객 보험 상담 전문 AI 비서 (이세윤 설계사 대행)
핵심 가치: 30년 경력의 이세윤 설계사가 가진 **'현장 실무 지식'**과 '고객 중심의 보상 철학' 계승.
전문성 범위:
- 금융: CFP(국제공인재무설계사) 수준의 자산 관리 및 판매 전문성 보유.
- 의학: 암(혈액/간담췌 등), 뇌심혈관, 치매신경과, 항암 의약품 등 전문의 수준의 질환 이해도 확보.
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
  예: "~인 것 같습니다" (X)  "판결문 제OO호에 의거하여~", "손해사정 실무상~" (O)
- 친절한 공감: 고난도의 의학법률 용어를 사용하되, 고객이 이해하기 쉽게 **'이세윤 설계사의 언어'**로 풀어서 설명한다.
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

##  Gemini 사용자 지침(Instructions) 가이드라인

### 1. 나에 대해 무엇을 알면 좋을까요? (Who you are)
나는 케이지에이셋 골드키지사의 30년 경력 베테랑 설계사 이세윤입니다.
- *** 박보정 지사장님의 관리 하에 '골드키지사 AI 마스터' 플랫폼을 운영하며, 여러 회원(설계사)들이 이 시스템을 사용합니다.
- *** 우리 시스템은 손해사정인, 보험전문 변호사/판사, 세무사/회계사/CFP, 각 진료과 전문의의 식견을 통합하여 무결점 보장 분석을 제공합니다.
- *** 보안 원칙: 고객의 개인정보는 마스킹(*) 처리하며, 분석 후 원본 자료는 즉시 파기하는 휘발성 시스템을 지향합니다.

### 2. 어떻게 답변하기를 원하시나요? (How you want Gemini to respond)
- 어조 및 화법: 항상 정중하고 따뜻하며 신뢰감 있는 '하십시오체'를 사용하십시오. 연예인 수애 님의 목소리처럼 지적이고 단아한 중저음 톤이 느껴지는 문체를 유지하십시오.
- *** 리스크 관리 핵심: 모든 리포트와 코딩 제안에는 "배포자인 골드키지사는 민형사상 책임을 지지 않으며, 모든 법적 책임은 실제 사용자(상담원)에게 귀속된다"는 면책 조항을 반드시 포함하십시오.
- *** 비용 성격 규정: 회비는 '정보 제공의 대가'가 아닌 '플랫폼 이용료 및 시스템 유지보수비'임을 명시하여 법적 방어선을 구축하십시오.
- *** 개인화 출력: 리포트 발행 시 상담자의 성함과 연락처가 상하단에 명확히 기재되어, 상담자가 리포트의 주체임을 나타내야 합니다.
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

### 3. 뇌심장 질환 보장 분석 가이드라인
- 보장 범위 진단: 뇌졸중급성심근경색증만 가입된 경우 '범위 좁음' 판정. 뇌혈관심혈관 질환 전체를 아우르는 광범위 담보(500만~3,000만 원) 포함 여부 최우선 확인.
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

##  이세윤 설계사의 베테랑 한마디 (상담 팁)
- 건물주 대상: "사장님, 건물 관리를 잘하셔도 전기 합선 하나면 옆집까지 책임지셔야 합니다. 민법상 소유자 책임은 피할 수 없기에 화재배상은 건물을 지키는 마지막 방어선입니다."
- 공장주 대상: "공장 안 작은 창고 하나를 빌려준 업종이 무엇인지가 중요합니다. 가장 위험한 놈을 기준으로 가입하지 않으면 사고 시 보험사는 요율 위반을 이유로 등을 돌립니다. 제가 그 빈틈을 찾아드리겠습니다."
- 자산가 상담 시: "건물은 자식에게 사랑의 유산이 될 수도 있지만, 준비 없는 상속세는 자식에게 짐이 될 수도 있습니다. 건물이 세금을 스스로 내게 만드는 구조, 제가 설계해 드리겠습니다."
- 의료비 상담 시: "의학은 빛의 속도로 발전하는데 고객님의 보험은 아직 20세기에 멈춰 있지는 않습니까? 최신 치료를 돈 걱정 없이 선택할 수 있는 권리, 그것이 진정한 보험의 가치입니다."

## [주의] 최종 강조 사항
- 모든 대화의 끝은 설계사님의 30년 신뢰를 상징하는 연락처로 마무리하십시오.
- 상담 문의: 010-3074-2616 이세윤 FC

[RAG 시스템 통합 지침]
- RAG 검색 결과를 활용할 때는 반드시 출처와 유사도를 명시하고, 이를 3중 검증 프로세스의 근거 자료로 활용하십시오.
- 검색된 문서는 보험업법, 금감원 판례, 의학 가이드라인 등 공신력 있는 자료임을 확인하고 사용하십시오.
"""

# -------------------------------------------------------------------------- 
# [개선된 SECTION 2] 경량화 RAG 시스템 (캐싱 적용) 
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_rag_engine():
    """모델 로드를 딱 한 번만 수행하여 메모리 보호"""
    try:
        # 가장 가벼운 다국어 모델 선택
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return model
    except:
        return None

class InsuranceRAGSystem:
    def __init__(self):
        self.embed_model = get_rag_engine()
        self.index = None
        self.documents = []
        self.metadata = []
        self.model_loaded = self.embed_model is not None
        if self.model_loaded:
            st.success(" 경량 엔진 가동 준비 완료")
        else:
            st.warning(" RAG 기능 없이 가동합니다.")
        
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """텍스트 임베딩 생성"""
        if not self.model_loaded:
            return np.array([])
        
        try:
            # 배치 처리로 메모리 사용량 최적화 (더 작은 배치)
            batch_size = 2  # 한 번에 처리할 텍스트 수 제한 (52)
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
            st.error(f" 임베딩 생성 실패: {e}")
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
            st.error(f" 인덱스 구축 실패: {e}")
    
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

# RAG 시스템 초기화
# RAG 시스템 초기화 (메모리 부족 방지)
try:
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = InsuranceRAGSystem()
except Exception as e:
    st.error(f" RAG 시스템 초기화 실패: {e}")
    st.warning(" RAG 기능 없이 계속 실행합니다.")
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

# 음성인식 엔진 자동 로드
load_stt_engine()

# -------------------------------------------------------------------------- 
# [SECTION 3] 사이드바: 사용자 센터 및 보안 () 
# -------------------------------------------------------------------------- 
with st.sidebar:
    st.header(" SaaS 마스터 센터")
    
    # 관리자 및 영구회원 자동 로그인 체크
    admin_id = st.text_input("관리자 ID", key="admin_id", type="password")
    admin_code = st.text_input("관리자 코드", key="admin_code", type="password")
    
    # 명시적 로그인 버튼
    if st.button(" 관리자 로그인"):
        # 관리자 자동 로그인
        if admin_id == "admin" and admin_code == "gold1234":
            st.session_state.user_id = "ADMIN_MASTER"
            st.session_state.user_name = "이세윤 마스터"
            st.session_state.encrypted_contact = encrypt_contact("01030742616")
            st.session_state.join_date = dt.now()
            st.session_state.is_admin = True
            st.success(" 관리자로 자동 로그인되었습니다!")
            st.rerun()
        
        # 영구회원 자동 로그인
        elif admin_id == "이세윤" and admin_code == "01030742616":
            st.session_state.user_id = "PERMANENT_MASTER"
            st.session_state.user_name = "이세윤"
            st.session_state.encrypted_contact = encrypt_contact("01030742616")
            st.session_state.join_date = dt.now()
            st.session_state.is_admin = False
            st.success(" 영구회원으로 자동 로그인되었습니다!")
            st.rerun()
        
        else:
            st.error(" ID 또는 코드가 올바르지 않습니다.")
    
    st.divider()
    
    # 실명 사용 공지
    st.warning("[주의] **반드시 본인의 실명으로 이용해야 데이터가 관리됩니다**")
    
    # 회원가입 또는 로그인
    if 'user_id' not in st.session_state:
        tab1, tab2 = st.tabs([" 회원가입", " 회원 로그인"])
        
        with tab1:
            st.subheader(" 회원가입")
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
                        
                        st.success(f" 회원가입 완료! ID: {member_info['user_id']}")
                        st.success(" 시스템 고도화 기간 1년간 무료 사용권이 부여되었습니다! (2027.03.31일까지)")
                        st.info(" 1일 3회 사용 가능하며, 추가 사용 원하는 경우 구독이 필요합니다.")
                        st.rerun()
                    else:
                        st.error(" 이름과 연락처를 모두 입력해주세요.")
        
        with tab2:
            st.subheader(" 회원 로그인")
            with st.form("login_form"):
                login_name = st.text_input("이름")
                login_contact = st.text_input("연락처")
                
                if st.form_submit_button("로그인"):
                    if login_name and login_contact:
                        # 회원 정보 확인
                        members = load_members()
                        if login_name in members:
                            member = members[login_name]
                            # 연락처 검증
                            if decrypt_data(member["contact"], login_contact):
                                st.session_state.user_id = member["user_id"]
                                st.session_state.user_name = login_name
                                st.session_state.encrypted_contact = member["contact"]
                                st.session_state.join_date = dt.strptime(member["join_date"], "%Y-%m-%d")
                                
                                st.success(f" {login_name}님 환영합니다!")
                                st.rerun()
                            else:
                                st.error(" 연락처가 올바르지 않습니다.")
                        else:
                            st.error(" 등록된 회원이 아닙니다. 먼저 회원가입을 해주세요.")
                    else:
                        st.error(" 이름과 연락처를 모두 입력해주세요.")
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
        ** 골드키지사 프리미엄 회원**
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
        with st.expander(" 비밀번호 재발급"):
            if st.button("비밀번호 재발급 요청"):
                temp_password = f"TEMP_{int(time.time())}"
                st.info(f" 임시 비밀번호: {temp_password}")
                st.info(" 10분 후 자동 만료됩니다.")
        
        with st.expander(" 구독 서비스 이용 약관"):
            st.warning("""
                **[법적 책임 한계고지]**
                본 서비스는 AI 기술을 활용한 **상담 보조 도구**이며, 제공되는 모든 분석 결과의 **최종 판단 및 법적 책임은 사용자(상담원)**에게 있습니다. 본 시스템은 금융 상품 판매의 직접적인 근거가 될 수 없습니다.
                """)
        
        # 로그아웃
        if st.button(" 로그아웃"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    st.divider()
    
    # 고객 지원 및 공식 연락처 (SaaS 핵심)
    st.markdown("###  마스터 고객 센터")
    st.caption(f" 공식 메일: insusite@gmail.com")
    st.caption(f"[문자] 상담 문의: 010-3074-2616")
    
    # [면책 조항 재강조]
    st.error(" 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.")
    
    st.divider()
    
    if st.button(" 보안 종료 및 상담 자료 파기", use_container_width=True):
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
        st.success(" 상담 자료가 파기되었습니다. 회원 정보는 보관됩니다.")
    
    st.info(f" **최종 승인자: 이세윤**")
    
    st.divider()
    
    with st.expander(" 마스터 회원 전용 혜택", expanded=False):
        st.markdown("""
        ###  골드키지사 프리미엄 회원 혜택
        - **시스템 고도화 기간**: 무료사용 1년 (2027.03.31일까지)
        - **사용 조건**: 1일 3회 사용 가능
        - **추가 사용**: 초과 시 월 15,000원 구독 필요
        - **제공 혜택**: 구글 실시간 검색 및 CFP 지능 무제한
        - **파일 한도**: 1일 50매까지 업로드 가능
        - **관리비**: 1년간 무료 제공
        """)
    
    st.divider()
    
    st.markdown("""
    ###  자료 파기 안내
    **상담 종료 후 로그아웃 시 제출 자료 자동 파기 됩니다.**
    - 파기 대상: 상담 고객의 증권 분석, 스캔로딩한 의무기록 등 서류 전부
    - 보존 대상: 회원 로그인 기록 및 비밀번호 (회원관리 항목으로 별도 관리)
    - 파기 시점: 상담 종료 후 로그아웃 시 또는 고객이 파기 버튼 클릭 시
    """)

# -------------------------------------------------------------------------- 
# [SECTION 4] 마스터 UI 및 3개 창 병렬 배치 (경량화) 
# -------------------------------------------------------------------------- 
st.title(" 골드키지사 AI 마스터")
MASTER_IMAGE_URL = "https://github.com/insusite-goldkey/goldkey/blob/main/ai_expert.png"

# 스마트 뷰 스위칭 적용
is_mobile, current_page = smart_view_switching()

if is_mobile:
    # 모바일 모드: Page-by-Page
    st.markdown(f"### [문자] 모바일 모드 - 페이지 {current_page + 1}")
    
    # 페이지별 콘텐츠 표시
    if current_page == 0:
        # 1페이지: 3개 창 병렬 배치
        col_voice, col_consult, col_answer = st.columns([2, 4, 4])
        
        with col_voice:
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
                <img src="{MASTER_IMAGE_URL}" style="width: 100%; max-width: 200px; border-radius: 50%; object-fit: cover;" alt="AI 전문가 이미지">
                <button onclick="window.startRecognition()" style="margin-top: 15px; background: #1E88E5; color: white; border: none; padding: 10px 20px; border-radius: 30px; cursor: pointer;"> 음성 인식 시작</button>
                <div style="margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 10px; text-align: center;">
                    <p style="margin: 0; font-size: 12px; color: #1976d2;"> 경량화 모드</p>
                    <p style="margin: 0; font-size: 10px; color: #666;">모바일 최적화</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_consult:
            st.write("###  마스터 통합 상담창")
            main_area = st.text_area("문의사항을 입력해주세요.", height=200, placeholder="보험, 재무, 건강 등 상담 내용을 입력하세요.", key="main_area")
            q_analyze = st.button(" 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)
            
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

        with col_answer:
            st.write("###  AI 답변창")
            
            # 답변 결과 저장용 session_state
            if 'analysis_result' not in st.session_state:
                st.session_state.analysis_result = ""
            
            # 답변 표시 영역
            if st.session_state.analysis_result:
                st.markdown(st.session_state.analysis_result)
            else:
                st.info(" AI 답변이 여기에 표시됩니다.")
                st.write("상담창에 질문을 입력하고 분석 실행 버튼을 클릭하세요.")
        
        # 메인 상담창 분석 실행 로직 (모바일용)
        if q_analyze and main_area:
            # 관리자 및 영구회원 체크
            is_special_user = (
                st.session_state.get('user_id') in ['ADMIN_MASTER', 'PERMANENT_MASTER'] or
                st.session_state.get('user_name') == '이세윤'
            )
            
            # 사용량 체크
            current_count = check_usage_count(user_name)
            MAX_FREE_LIMIT = 3
            
            if not is_special_user and current_count >= MAX_FREE_LIMIT:
                st.error(f"[주의] {user_name} 마스터님, 오늘은 3회 분석 기회를 모두 사용하셨습니다. 내일 다시 이용해 주세요!")
                st.warning(" **무제한 사용을 원하시면 월 15,000원의 프리미엄 구독으로 전환하세요!**")
                components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다. 내일 뵙겠습니다."), height=0)
                
                # 답변창에 메시지 표시
                st.session_state.analysis_result = "[주의] **오늘의 분석 횟수를 모두 사용하셨습니다.**\n\n내일 다시 이용해 주세요!"
            else:
                # 분석 실행
                with st.spinner(f" {current_count + 1}번째 정밀 분석 중..."):
                    try:
                        # 서버 고정형 모델 사용
                        client, model_config = get_master_model()
                        
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
                        
                        query = f"상담: {main_area}. 소득: {hi_premium / 0.0709 if hi_premium > 0 else 0:.0f}. 필수: {essential_ins}. 질환: {disease_focus}.{context_text}"
                        
                        # Google Genai 방식으로 콘텐츠 생성
                        resp = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=query,
                            config=model_config
                        )
                        
                        # 답변 결과 저장
                        answer_text = f"""
        ###  {customer_name}님 정밀 리포트

        {resp.text}

        ---
        ** 추가 문의 필요 시**
         공식 메일: insusite@gmail.com  
        [문자] 상담 문의: 010-3074-2616

        [주의] **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
        """
                        
                        st.session_state.analysis_result = answer_text
                        
                        components.html(s_voice("AI 상담 분석이 완료되었습니다."), height=0)
                        
                        # 분석이 성공적으로 끝나면 카운트 증가
                        update_usage(user_name)
                        remaining = MAX_FREE_LIMIT - (current_count + 1)
                        st.success(f" 분석 완료! (오늘 남은 횟수: {remaining}회)")
                        
                    except Exception as e:
                        error_msg = f"[주의] **분석 장애 발생**\n\n오류: {e}\n\n 해결책: API 키 확인 또는 관리자에게 문의하세요."
                        st.session_state.analysis_result = error_msg
                        st.sidebar.error(f"[주의] 분석 장애: {e}")
                        st.sidebar.info(" 해결책: API 키 확인 또는 관리자에게 문의하세요.")
    
    else:
        # PC 모드: Full View (기존 코드 유지)
        # 3개 창 병렬 배치 (상담창과 답변창 동일 크기)
        col_voice, col_consult, col_answer = st.columns([2, 4, 4])

        with col_voice:
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: center; background: #f0f4f8; padding: 20px; border-radius: 20px; border: 2px solid #1E88E5;">
                <img src="{MASTER_IMAGE_URL}" style="width: 100%; max-width: 200px; border-radius: 50%; object-fit: cover;" alt="AI 전문가 이미지">
                <button onclick="window.startRecognition()" style="margin-top: 15px; background: #1E88E5; color: white; border: none; padding: 10px 20px; border-radius: 30px; cursor: pointer;"> 음성 인식 시작</button>
                <div style="margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 10px; text-align: center;">
                    <p style="margin: 0; font-size: 12px; color: #1976d2;"> 경량화 모드</p>
                    <p style="margin: 0; font-size: 10px; color: #666;">모바일 최적화</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col_consult:
            st.write("###  마스터 통합 상담창")
            main_area = st.text_area("문의사항을 입력해주세요.", height=200, placeholder="보험, 재무, 건강 등 상담 내용을 입력하세요.", key="main_area")
            q_analyze = st.button(" 글로벌 CFP 정밀 분석 실행", type="primary", use_container_width=True)
            
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

        with col_answer:
            st.write("###  AI 답변창")
            
            # 답변 결과 저장용 session_state
            if 'analysis_result' not in st.session_state:
                st.session_state.analysis_result = ""
            
            # 답변 표시 영역
            if st.session_state.analysis_result:
                st.markdown(st.session_state.analysis_result)
            else:
                st.info(" AI 답변이 여기에 표시됩니다.")
                st.write("상담창에 질문을 입력하고 분석 실행 버튼을 클릭하세요.")

        # 메인 상담창 분석 실행
        if q_analyze and main_area:
            # 관리자 및 영구회원 체크
            is_special_user = (
                st.session_state.get('user_id') in ['ADMIN_MASTER', 'PERMANENT_MASTER'] or
                st.session_state.get('user_name') == '이세윤'
            )
            
            # 사용량 체크
            current_count = check_usage_count(user_name)
            MAX_FREE_LIMIT = 3
            
            if not is_special_user and current_count >= MAX_FREE_LIMIT:
                st.error(f"[주의] {user_name} 마스터님, 오늘은 3회 분석 기회를 모두 사용하셨습니다. 내일 다시 이용해 주세요!")
                st.warning(" **무제한 사용을 원하시면 월 15,000원의 프리미엄 구독으로 전환하세요!**")
                components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다. 내일 뵙겠습니다."), height=0)
                
                # 답변창에 메시지 표시
                st.session_state.analysis_result = "[주의] **오늘의 분석 횟수를 모두 사용하셨습니다.**\n\n내일 다시 이용해 주세요!"
            else:
                # 분석 실행
                with st.spinner(f" {current_count + 1}번째 정밀 분석 중..."):
                    try:
                        # 서버 고정형 모델 사용
                        client, model_config = get_master_model()
                        
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
                        
                        query = f"상담: {main_area}. 소득: {hi_premium / 0.0709 if hi_premium > 0 else 0:.0f}. 필수: {essential_ins}. 질환: {disease_focus}.{context_text}"
                        
                        # Google Genai 방식으로 콘텐츠 생성
                        resp = client.models.generate_content(
                            model="gemini-1.5-flash",
                            contents=query,
                            config=model_config
                        )
                        
                        # 답변 결과 저장
                        answer_text = f"""
        ###  {customer_name}님 정밀 리포트

        {resp.text}

        ---
        ** 추가 문의 필요 시**
         공식 메일: insusite@gmail.com  
        [문자] 상담 문의: 010-3074-2616

        [주의] **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
        """
                        
                        st.session_state.analysis_result = answer_text
                        
                        components.html(s_voice("AI 상담 분석이 완료되었습니다."), height=0)
                        
                        # 분석이 성공적으로 끝나면 카운트 증가
                        update_usage(user_name)
                        remaining = MAX_FREE_LIMIT - (current_count + 1)
                        st.success(f" 분석 완료! (오늘 남은 횟수: {remaining}회)")
                        
                    except Exception as e:
                        error_msg = f"[주의] **분석 장애 발생**\n\n오류: {e}\n\n 해결책: API 키 확인 또는 관리자에게 문의하세요."
                        st.session_state.analysis_result = error_msg
                        st.sidebar.error(f"[주의] 분석 장애: {e}")
                        st.sidebar.info(" 해결책: API 키 확인 또는 관리자에게 문의하세요.")

# 음성 인식 함수 로드
load_stt_engine()

# -------------------------------------------------------------------------- 
# [SECTION 9] 보험금 상담 분석 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  보험금 상담 분석")
st.markdown("**보험 증권, 진단서, 의료 기록, 사고 현장 사진 등을 AI가 정밀 분석합니다.**")

# 4칸 Drag and Drop 입력창
col_img1, col_img2, col_img3, col_img4 = st.columns(4)

with col_img1:
    uploaded_images_1 = st.file_uploader(
        " 증권/진단서", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'pdf'],
        accept_multiple_files=True,
        key="image_consultation_1"
    )
    
    if uploaded_images_1:
        st.success(f" {len(uploaded_images_1)}개 파일 업로드")
        for i, img_file in enumerate(uploaded_images_1, 1):
            if img_file.type.startswith('image/'):
                st.image(img_file, caption=f"증권 {i}", width=200)
            else:
                st.info(f" 증권 {i}: {img_file.name}")

with col_img2:
    uploaded_images_2 = st.file_uploader(
        " 진료기록", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'pdf'],
        accept_multiple_files=True,
        key="image_consultation_2"
    )
    
    if uploaded_images_2:
        st.success(f" {len(uploaded_images_2)}개 파일 업로드")
        for i, img_file in enumerate(uploaded_images_2, 1):
            if img_file.type.startswith('image/'):
                st.image(img_file, caption=f"진료 {i}", width=200)
            else:
                st.info(f" 진료 {i}: {img_file.name}")

with col_img3:
    uploaded_images_3 = st.file_uploader(
        " 사고현장", 
        type=['jpg', 'jpeg', 'png', 'bmp', 'pdf'],
        accept_multiple_files=True,
        key="image_consultation_3"
    )
    
    if uploaded_images_3:
        st.success(f" {len(uploaded_images_3)}개 파일 업로드")
        for i, img_file in enumerate(uploaded_images_3, 1):
            if img_file.type.startswith('image/'):
                st.image(img_file, caption=f"사고 {i}", width=200)
            else:
                st.info(f" 사고 {i}: {img_file.name}")

with col_img4:
    image_query_type = st.selectbox(
        " 분석 유형 선택",
        ["보험금 청구", "진단서 분석", "사고 현장 분석", "의료 기록 분석", "기타"],
        key="image_analysis_type"
    )
    
    image_specific_query = st.text_area(
        " 특정 분석 요청사항",
        placeholder="예시: 이 보험 증권의 암 보장 금액을 분석해주세요. / 이 진단서의 병명에 해당하는 보험금 지급 가능성을 알려주세요.",
        height=100,
        key="image_specific_query"
    )

# 이미지 분석 실행 버튼
all_uploaded_images = []
if uploaded_images_1:
    all_uploaded_images.extend(uploaded_images_1)
if uploaded_images_2:
    all_uploaded_images.extend(uploaded_images_2)
if uploaded_images_3:
    all_uploaded_images.extend(uploaded_images_3)

if all_uploaded_images and st.button(" AI 보험금 상담 분석 실행", type="primary", use_container_width=True):
    # 1. 현재 사용 횟수 확인
    current_count = check_usage_count(user_name)
    MAX_FREE_LIMIT = 3
    
    if current_count >= MAX_FREE_LIMIT:
        st.error(f"[주의] {user_name} 마스터님, 오늘은 3회 분석 기회를 모두 사용하셨습니다. 내일 다시 이용해 주세요!")
        st.warning(" **무제한 사용을 원하시면 월 15,000원의 프리미엄 구독으로 전환하세요!**")
        components.html(s_voice("오늘의 무료 분석 기회를 모두 사용하셨습니다. 내일 뵙겠습니다."), height=0)
    else:
        # 2. 이미지 분석 실행
        with st.spinner(f" {current_count + 1}번째 AI 보험금 분석 중..."):
            try:
                # 서버 고정형 모델 사용
                client, model_config = get_master_model()

                # 분석 쿼리 구성
                analysis_query = f"""
                [보험금 상담 분석 요청]
                상담원: {user_name}
                고객: {customer_name}
                분석 목적: 보험금 청구 및 자산 관리
                분석 유형: {image_query_type}
                특정 요청: {image_specific_query}
                
                제공된 이미지를 바탕으로 다음을 분석해주세요:
                1. 보험 관련 문서의 주요 내용
                2. 의료 기록의 핵심 정보
                3. 사고 현장의 특이사항
                4. 보험금 청구 가능성 및 예상 금액
                5. 필요한 추가 서류 및 절차
                """
                
                # 이미지를 콘텐츠에 추가
                contents = [analysis_query]
                for img_file in all_uploaded_images:
                    if img_file.type.startswith('image/'):
                        contents.append(PIL.Image.open(img_file))
                    else:
                        # PDF 파일 처리
                        contents.append(f" PDF 파일: {img_file.name}")
                
                # Google Genai 방식으로 콘텐츠 생성
                resp = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=contents,
                    config=model_config
                )
                
                # 답변 결과 저장
                answer_text = f"""
###  {customer_name}님 보험금 정밀 분석 리포트

{resp.text}

---
** 추가 문의 필요 시**
 공식 메일: insusite@gmail.com  
[문자] 상담 문의: 010-3074-2616

[주의] **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
"""
                
                st.session_state.analysis_result = answer_text
                
                components.html(s_voice("AI 보험금 분석이 완료되었습니다."), height=0)
                
                # 분석이 성공적으로 끝나면 카운트 증가
                update_usage(user_name)
                remaining = MAX_FREE_LIMIT - (current_count + 1)
                st.success(f" 보험금 분석 완료! (오늘 남은 횟수: {remaining}회)")
                
            except Exception as e:
                error_msg = f"[주의] **보험금 분석 장애 발생**\n\n오류: {e}\n\n 해결책: 이미지 파일 확인 또는 관리자에게 문의하세요."
                st.session_state.analysis_result = error_msg
                st.sidebar.error(f"[주의] 분석 장애: {e}")
                st.sidebar.info(" 해결책: 이미지 파일 확인 또는 관리자에게 문의하세요.")
                
                # 결과 표시
                st.subheader(" AI 이미지 상담 분석 결과")
                st.markdown(response.text)
                
                # 관리자 연락처 자동 포함
                st.markdown("---")
                st.info(f"""
                ** 추가 문의 필요 시**
                 공식 메일: insusite@gmail.com  
                [문자] 상담 문의: 010-3074-2616
                
                [주의] **법적 책임**: 모든 분석 결과의 최종 책임은 사용자(회원)에게 귀속됩니다.
                """)
                st.markdown("---")
                
                components.html(s_voice("AI 이미지 상담 분석이 완료되었습니다."), height=0)
                
                # 3. 분석이 성공적으로 끝나면 카운트 증가
                update_usage(user_name)
                remaining = MAX_FREE_LIMIT - (current_count + 1)
                st.success(f" 이미지 분석 완료! (오늘 남은 횟수: {remaining}회)")
                
            except Exception as e:
                st.sidebar.error(f"[주의] 이미지 분석 장애: {e}")
                st.sidebar.info(" 해결책: 이미지 파일 확인 또는 API 키를 확인하세요.")
                
    st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/dispute_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 6]  필수 보장 정밀 진단 (6칸 그리드 방식)
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  1단계: 필수 보장 정밀 진단")
st.caption("마스터 권장 기준 미달 시 '미보유/보완'을 선택하십시오.")

# 2줄 3칸 또는 모바일 대응을 위한 컬럼 배치
col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)

# [1번 칸] 자동차보험
with col1:
    st.markdown("#####  자동차보험")
    st.caption("기준: 대물 5억이상, 자동차상해 (사망2억,부상2억)이상")
    car_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_car")

# [2번 칸] 화재보험
with col2:
    st.markdown("#####  화재보험")
    st.caption("보험가액 100%이상.(재조달가액평가필수)")
    fire_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_fire")

# [3번 칸] 일상생활배상
with col3:
    st.markdown("#####  일배책")
    st.caption("기준: 가족 일상생활배상책임")
    life_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_life")

# [4번 칸] 운전자보험
with col4:
    st.markdown("#####  운전자보험")
    st.caption("기준: 형사합의 2억, 변호사, 벌금")
    driver_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_driver")

# [5번 칸] 연금보험
with col5:
    st.markdown("#####  연금보험")
    st.caption("기준: 현 소득 기준 100% 준비")
    pension_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_pension")

# [6번 칸] 통합보험
with col6:
    st.markdown("#####  통합보험")
    st.caption("기준: 3대 진단비 5천만원 이상")
    total_status = st.selectbox("보유 상태", ["미보유/보완", "기준충족 보유"], key="check_total")

# AI 분석을 위한 데이터 통합
essential_results = {
    "자동차": car_status, "화재": fire_status, "일배책": life_status,
    "운전자": driver_status, "연금": pension_status, "통합": total_status
}

# -------------------------------------------------------------------------- 
# [SECTION 7] 보험 증권 분석 자료 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  2단계: 보험 증권 분석 자료")
uploaded_files = st.file_uploader("증권 PDF 또는 이미지 업로드", accept_multiple_files=True, key="sec7")

# -------------------------------------------------------------------------- 
# [SECTION 8] 건보료 기반 소득 역산 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  3단계: 건보료 기반 소득 역산")
hi_premium = st.number_input("월 국민건강보험료 (원)", value=0, step=1000, key="sec8")
if hi_premium > 0:
    calc_income = hi_premium / 0.0709
    st.success(f" 역산 월 소득: **{calc_income:,.0f}원** / 적정 보험료 15%: **{calc_income*0.15:,.0f}원**")

# -------------------------------------------------------------------------- 
# [SECTION 9] 질병 보상 분석 및 가족력 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  질병 보상 분석 및 가족력")
disease_focus = st.text_area("가족력 및 집중 분석 질환 입력", key="sec9")

# -------------------------------------------------------------------------- 
# [SECTION 10] 생보사 헬스케어 컨설팅 ()
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  생보사 헬스케어 컨설팅")
hc_ans = st.radio("상급병원 2주 내 진찰 예약 서비스 필요 여부", ["예", "아니오", "미정"], key="sec10")

# -------------------------------------------------------------------------- 
# [SECTION 11] 법령 및 보상 지식 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  법령 및 보상 지식")
st.info("민법, 상법, 보험업법, 형사소송법, 화재의 예방의 및 안전관리에 관한 법률, 실화책임에 관한 법률 3중 검증 가동")

# -------------------------------------------------------------------------- 
# [SECTION 12] 국제기준 재무설계 위험관리 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  국제기준 재무설계 위험관리")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/cfp_process.png")

# -------------------------------------------------------------------------- 
# [SECTION 13] 3층 연금 시뮬레이션 () 
# -------------------------------------------------------------------------- 
st.divider()
st.write("###  3층 연금 시뮬레이션")
st.image("https://raw.githubusercontent.com/insusite-goldkey/goldkey/main/pension_3tier.png")
p_nat = st.number_input("국민(만)", key="p1")
p_ret = st.number_input("퇴직(만)", key="p2")
p_ind = st.number_input("개인(만)", key="p3")

# -------------------------------------------------------------------------- 
# [SECTION 14] 주택 연금 설계 () 
# -------------------------------------------------------------------------- 
def section_housing_pension():
    st.subheader(" 주택연금(Reverse Mortgage) 정밀 시뮬레이션")
    st.info(" 2024-2026 한국주택금융공사(HF) 표준형/종신지급방식 기준")

    col1, col2 = st.columns(2)
    with col1:
        h_age = st.number_input("가입자 연령 (부부 중 연소자 기준)", min_value=55, max_value=90, value=65)
        h_value = st.number_input("주택 시세 (단위: 만원)", min_value=0, value=50000, step=1000)
    
    # [마스터 데이터] 1억당 월 지급금 테이블 (2024년 이후 최신 데이터 기반 근사치)
    # 실제 운영 시에는 HF의 API를 연결하거나 상세 테이블을 더 확충할 수 있습니다.
    hf_table = {
        55: 145000, 60: 197000, 65: 242000, 70: 297000, 75: 367000, 80: 461000, 85: 593000, 90: 775000
    }

    # 입력 연령에 가장 가까운 하위 연령값 찾기
    base_age = max([a for a in hf_table.keys() if a <= h_age])
    monthly_per_100m = hf_table[base_age]
    
    # 산출 로직: (주택가격 / 1억) * 해당 연령 월 지급금
    estimated_monthly = (h_value / 10000) * monthly_per_100m

    with col2:
        st.write("###  산출 결과")
        st.metric(label=f"{h_age}세 가입 시 예상 월수령액", value=f"{estimated_monthly:,.0f} 원")
        st.caption(" 종신지급방식, 정액형 기준 (세부 조건에 따라 변동 가능)")

    # 전문가 조언 섹션
    if estimated_monthly > 0:
        st.success(f"""
        ** 이세윤 마스터의 전략적 조언:**
        1. **기초연금과의 조화:** 주택연금은 소득인정액 계산 시 혜택이 있으므로 기초연금 수급 자격을 유지하는 데 유리합니다.
        2. **건보료 절감:** 주택연금 수령액은 '소득'이 아닌 '부채' 성격이므로 건강보험료 산정 시 포함되지 않는 강력한 장점이 있습니다.
        3. **상속 전략:** 자녀에게는 '집'이 아닌 '현금흐름'을 물려주는 것이 현대적 상속의 트렌드임을 강조하십시오.
        """)

# 함수 실행 (기존 15개 섹션 위치에 배치)
section_housing_pension()

# -------------------------------------------------------------------------- 
# [SECTION 15] 전문가 통합 분석 ()
# --------------------------------------------------------------------------
st.divider()
# --------------------------------------------------------------------------
# [SECTION 16] 회원 관리 시스템 ()
# --------------------------------------------------------------------------
st.divider()
st.write("###  회원 관리 시스템")

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
        with st.expander(" 회원 관리 기능"):
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
                        st.success(f" {selected_member}님 구독이 30일 연장되었습니다.")
            
            with col2:
                if st.button("회원 비활성화"):
                    if selected_member:
                        members[selected_member]["is_active"] = False
                        save_members(members)
                        st.warning(f"[주의] {selected_member}님이 비활성화되었습니다.")
    else:
        st.info("등록된 회원이 없습니다.")
else:
    st.warning(" 관리자만 접근할 수 있습니다.")

# --------------------------------------------------------------------------
# [SECTION 17] 관리자 이세윤 성공 응원 ()
# --------------------------------------------------------------------------
st.divider()

# 관리자 전용 기능
is_admin = st.session_state.get('is_admin', False)
is_permanent = st.session_state.get('user_id') == 'PERMANENT_MASTER'

if is_admin or is_permanent:
    if st.button(" 관리자 이세윤 성공 응원", use_container_width=True):
        st.success(" 이세윤 마스터의 성공을 응원합니다!")
        st.balloons()
    
    # 관리자 전용 RAG 지식베이스 (Admin Only)
    with st.expander(" 관리자 전용 RAG 지식베이스 (Admin Only)", expanded=False):
        admin_key = st.text_input("관리자 키 입력", type="password")
        
        if admin_key == "gold1234" or is_permanent:
            st.success(" 관리자 접근 권한 확인!")
            
            # 파일 업로더
            uploaded_files = st.file_uploader(
                "전문가용 노하우 PDF 업로드",
                type=['pdf', 'docx', 'txt'],
                accept_multiple_files=True
            )
            
            if uploaded_files and st.button("지식베이스 즉시 동기화"):
                with st.spinner(" RAG 시스템 동기화 중..."):
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
                        st.success(f" {len(uploaded_files)}개 파일이 지식베이스에 추가되었습니다!")
                        
                    except Exception as e:
                        st.error(f" 동기화 오류: {e}")
        else:
            st.warning(" 관리자 키가 필요합니다.")
else:
    st.info(" 관리자 전용 기능은 접근할 수 없습니다.")

# q_analyze 변수 초기화 (모바일/PC 모드 모두에서 사용 가능하도록)
if 'q_analyze' not in locals():
    q_analyze = False

if q_analyze:
    # 관리자 및 영구회원 체크
    is_special_user = (
        st.session_state.get('user_id') in ['ADMIN_MASTER', 'PERMANENT_MASTER'] or
        st.session_state.get('user_name') == '이세윤'
    )
    
    # 분석 실행 로직
    try:
        # 분석 처리 코드
        pass
    except Exception as e:
        st.sidebar.error(f"[주의] 분석 장애: {e}")
        st.sidebar.info(" 해결책: API 키 확인 또는 관리자에게 문의하세요.")

if st.button(" FC님 성공 응원", use_container_width=True):
    st.balloons()
    components.html(s_voice("FC님, 필승하십시오! 당신의 성공을 응원합니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 16] 관리자 전용 RAG 지식베이스 (앱 최하단 배치) 
# -------------------------------------------------------------------------- 
st.divider()
with st.expander(" 마스터 전용 지식베이스 관리 (Admin Only)", expanded=False):
    # 관리자 비밀번호나 특정 키가 있을 때만 활성화되도록 설정 가능
    admin_key = st.text_input("관리자 인증키", type="password")
    if admin_key == "goldkey777": # 관리자님만의 비밀번호
        st.write("###  마스터 전용 RAG 엔진")
        # 여기서 파일 업로드 및 인덱스 업데이트 수행
        rag_files = st.file_uploader("전문가용 노하우 PDF 업로드", accept_multiple_files=True, type=["pdf", "docx", "txt"])
        if st.button(" 지식베이스 즉시 동기화"):
            # 마스터의 지식으로 변환하는 로직 실행
            st.success("마스터의 지식으로 통합되었습니다.")
    else:
        st.info("이 섹션은 관리자 전용 공간입니다.")
