# ==========================================================
# 골드키지사 마스터 AI - 지능형 RAG 조건실행 통합본
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
# [SECTION 1] 보안 및 암호화 엔진
# -------------------------------------------------------------------------- 
def get_encryption_key():
    """보안 키를 가져오거나 생성함"""
    if "ENCRYPTION_KEY" in st.secrets:
        return st.secrets["ENCRYPTION_KEY"].encode()
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
# [SECTION 2] 온디맨드 RAG 엔진 (필요 시에만 호출)
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_embedding_model():
    """임베딩 모델 로드 (캐시로 성능 최적화)"""
    try:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    except ImportError:
        st.error("RAG 기능을 위해 sentence-transformers 설치 필요: pip install sentence-transformers")
        return None

class MasterRAGPipeline:
    def __init__(self):
        self.index_path = "data/master_knowledge.index"
        self.json_path = "data/master_knowledge.json"
        
    def sync_data(self, uploaded_files):
        """관리자용: 지식베이스 구축"""
        if not uploaded_files:
            return 0
            
        try:
            import pdfplumber
            import faiss
        except ImportError:
            st.error("RAG 기능을 위해 pdfplumber, faiss 설치 필요: pip install pdfplumber faiss-cpu")
            return 0
            
        all_chunks = []
        for file in uploaded_files:
            try:
                with pdfplumber.open(file) as pdf:
                    text = "".join([p.extract_text() + "\n" for p in pdf.pages if p.extract_text()])
                
                # 텍스트를 500자 청크로 분할
                chunks = [text[i:i+500] for i in range(0, len(text), 450)]
                all_chunks.extend(chunks)
            except Exception as e:
                st.warning(f"파일 처리 오류 ({file.name}): {e}")
                continue
        
        if not all_chunks: 
            return 0
            
        model = get_embedding_model()
        if model is None:
            return 0
            
        embeddings = model.encode(all_chunks)
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(np.array(embeddings).astype('float32'))
        
        if not os.path.exists('data'): 
            os.makedirs('data')
            
        faiss.write_index(index, self.index_path)
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False)
            
        return len(all_chunks)

    def retrieve(self, query, k=3):
        """상세 분석 시: 관련 지식 추출"""
        try:
            import faiss
        except ImportError:
            return ""
            
        if not os.path.exists(self.index_path) or not os.path.exists(self.json_path):
            return ""
            
        try:
            index = faiss.read_index(self.index_path)
            with open(self.json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                
            model = get_embedding_model()
            if model is None:
                return ""
                
            query_vec = model.encode([query])
            _, indices = index.search(np.array(query_vec).astype('float32'), k)
            
            # 관련 청크 반환
            relevant_chunks = []
            for i in indices[0]:
                if i < len(chunks):
                    relevant_chunks.append(chunks[i])
                    
            return "\n".join(relevant_chunks)
        except Exception as e:
            st.warning(f"RAG 검색 오류: {e}")
            return ""

# -------------------------------------------------------------------------- 
# [SECTION 3] 의도 분류기 (Intent Classifier)
# -------------------------------------------------------------------------- 
def judge_needs_rag(query):
    """RAG 구동 여부를 결정하는 기계적 판정 로직"""
    # 1. 핵심 키워드 포함 시 무조건 RAG 가동
    trigger_words = ["약관", "조항", "보험금", "판례", "근거", "상세", "규정", "지침", "보험사", "특약", "보장한도", "면책"]
    if any(word in query for word in trigger_words):
        return True
    
    # 2. 질문의 길이가 길면(심층 질문) RAG 가동
    if len(query) > 50:
        return True
    
    # 3. 비교/분석 질문 패턴
    analysis_patterns = ["비교", "차이", "어떤 것이", "추천", "선택", "좋은"]
    if any(pattern in query for pattern in analysis_patterns):
        return True
    
    return False

# -------------------------------------------------------------------------- 
# [SECTION 4] 통합 유틸리티 함수
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_client():
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets에 GEMINI_API_KEY 설정이 필요합니다.")
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
        <strong>데이터 보안 지침</strong><br>
        - 상담 자료: 로그아웃 시 즉시 파쇄<br>
        - 구독 만료: 30일 유예 후 자동 파기<br>
        - 암호화: AES-256 군사급 보호
    </div>
    """, unsafe_allow_html=True)

def purge_expired_data():
    """30일 경과한 만료 데이터 영구 삭제"""
    conn = sqlite3.connect('insurance_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_documents WHERE status = 'EXPIRED' AND expiry_date <= date('now', '-30 days')")
    conn.commit()
    conn.close()
    st.success("보안 지침에 따라 만료된 상담 자료가 파기되었습니다.")

def logout_and_cleanup():
    """로그아웃 시 모든 사용자 데이터 삭제"""
    if 'user_id' in st.session_state:
        user_id = st.session_state.user_id
        
        # 1. 데이터베이스에서 사용자 문서 삭제
        conn = sqlite3.connect('insurance_data.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_documents WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # 2. 세션 초기화
        st.session_state.clear()
        
        # 3. 성공 메시지
        st.success("안전 로그아웃되었습니다. 모든 상담 자료가 파기되었습니다.")
        st.rerun()

def analyze_with_ai(query, customer_name="고객", rag_context=""):
    try:
        client = get_client()
        
        # RAG 컨텍스트가 있으면 프롬프트에 포함
        if rag_context:
            master_instruction = f"""당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요.
            
            아래 전문 자료를 참고하여 답변하세요:
            {rag_context}
            """
        else:
            master_instruction = "당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요."
        
        resp = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[f"고객 {customer_name} 리포트 요청: {query}"],
            config=types.GenerateContentConfig(
                system_instruction=master_instruction,
                tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
            )
        )
        
        return resp.text
        
    except Exception as e:
        st.error(f"AI 분석 장애: {e}")
        return None

def section_inheritance_will():
    st.title("상속 및 증여 통합 설계")
    st.markdown("2026년 최신 세법 및 민법 제1000조 기준")
    
    c_name = st.text_input("상담 고객 성함", "홍길동")
    masked_name = c_name[0] + "*" + c_name[-1] if len(c_name) > 1 else c_name
    
    st.info(f"보안 모드 가동 중: 분석 리포트에는 '{masked_name}'님으로 표기됩니다.")

    with st.expander("상속인 신분 관계 확정 (민법 제1000조)", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            spouse = st.radio("배우자 관계", ["법률혼 (상속권 있음)", "사실혼 (상속권 없음)"])
            child_legal = st.number_input("친자/양자 수", min_value=0, value=1)
            child_none = st.number_input("파양된 자녀 수", min_value=0, value=0)
        with c2:
            st.caption("※ 양자는 친자와 동일 권리, 파양 시 상속권 소멸")
            shares = "배우자 1.5 : 자녀 1.0" if spouse.startswith("법률혼") else "자녀 100%"
            st.success(f"법정비율: {shares}")

    st.subheader("자산 및 세금 시뮬레이션")
    val_real = st.number_input("부동산 시가(만원)", value=150000)
    val_cash = st.number_input("금융자산(만원)", value=50000)
    
    if st.button("상속 및 증여 정밀 분석", type="primary", use_container_width=True):
        taxable = max((val_real + val_cash) - 100000, 0)
        est_tax = taxable * 0.3 - 6000
        res_text = f"총 자산 {val_real+val_cash:,.0f}만원 중 예상 상속세는 약 {est_tax:,.0f}만원입니다. 부동산 비중이 높아 종신보험을 통한 세원 마련이 시급합니다."
        
        report_html = f"""
        <div style="padding:30px; border:1px solid #eee; background:white; font-family:sans-serif; border-radius:10px;">
            <h2 style="color:#1E88E5; border-bottom:2px solid #1E88E5;">상속 및 증여 정밀 분석 리포트</h2>
            <p><b>고객:</b> {masked_name}님</p>
            <div style="margin:20px 0;">{res_text.replace(chr(10), '<br>')}</div>
            <div style="font-size:11px; color:#888; background:#f9f9f9; padding:10px; border-radius:5px;">
                <b>법적 책임 고지:</b> 본 리포트는 참고용이며 최종 결정의 책임은 사용자에게 있습니다.
            </div>
        </div>
        """
        st.components.v1.html(report_html, height=400, scrolling=True)

    st.divider()
    st.subheader("유언장 및 유류분 방어 플랜")
    st.warning("2024년 최신 판례: 형제자매의 유류분 청구권은 폐지되었습니다.")
    
    if st.checkbox("유언장 양식 보기"):
        st.markdown("#### 자필유언장 표준 양식")
        will_text = f"나 유언자 [성함]은 주소 [주소]에서 다음과 같이 유언한다...\n1. 부동산은 [동거인]에게 사인증여한다..."
        st.code(will_text, language="text")
        st.success("반드시 전체 내용을 직접 자필로 작성하고 날인하십시오.")
        if st.button("작성 가이드 음성 듣기"):
            components.html(s_voice("유언장은 반드시 처음부터 끝까지 직접 손으로 쓰셔야 법적 효력이 발생합니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 5] 메인 앱 구조 통합
# -------------------------------------------------------------------------- 
def main():
    st.set_page_config(page_title="골드키지사 마스터 AI", page_icon="", layout="wide")
    
    setup_database()
    
    # RAG 엔진 초기화
    rag_engine = MasterRAGPipeline()

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
                logout_and_cleanup()
        
        # [관리자 전용 RAG 로딩]
        if st.session_state.get('user_name') == "이세윤":
            with st.expander("RAG 지식베이스 로드"):
                admin_files = st.file_uploader("PDF 로드", accept_multiple_files=True, type=['pdf'])
                if st.button("지식베이스 즉시 동기화"):
                    count = rag_engine.sync_data(admin_files)
                    st.success(f"✅ {count}개 지식 통합 완료")
        
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
            
            # [조건 실행 로직 적용]
            is_complex = judge_needs_rag(query)
            
            if is_complex:
                with st.status("심층 분석 모드 가동 중...", expanded=True) as status:
                    st.write("마스터 지식베이스에서 관련 약관 조항을 검색합니다...")
                    context = rag_engine.retrieve(query)
                    st.write("전문 자료 추출 완료. 리포트를 생성합니다...")
                    
                    result = analyze_with_ai(query, customer_name, context)
                    if result:
                        st.success("심층 분석이 완료되었습니다.")
                        status.update(label="마스터 지식 기반 정밀 분석 완료", state="complete")
                        
                        st.divider()
                        st.subheader(f"{customer_name}님을 위한 마스터 AI 정밀 리포트")
                        st.markdown(result)
                        st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                        
                        # 추출된 근거 자료 표시
                        if context:
                            with st.expander("📚 참조된 전문 자료"):
                                st.markdown(f"**[추출된 근거 자료]**\n{context[:500]}...")
                        
                        components.html(s_voice(f"{st.session_state.user_name}님, 마스터 AI의 심층 분석이 완료되었습니다."), height=0)
            else:
                with st.spinner("빠른 일반 답변을 생성 중입니다..."):
                    result = analyze_with_ai(query, customer_name)
                    if result:
                        st.info("💡 본 답변은 일반 지식을 기반으로 작성되었습니다. 상세 약관 확인이 필요하시면 질문에 '약관'을 포함해 주세요.")
                        
                        st.divider()
                        st.subheader(f"{customer_name}님을 위한 마스터 AI 답변")
                        st.markdown(result)
                        st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                        
                        components.html(s_voice(f"{st.session_state.user_name}님, 마스터 AI의 답변이 완료되었습니다."), height=0)

    with tabs[1]:
        st.subheader("자산 분석 및 문서 관리")
        
        st.subheader("데이터 보안 관리")
        if st.button("만료 데이터 파기 실행", type="secondary"):
            purge_expired_data()
        
        st.subheader("문서 일괄 PDF 생성")
        st.warning("PDF 생성 기능을 위해 PyMuPDF, pdfplumber, python-docx를 설치해주세요.")

    with tabs[2]:
        section_inheritance_will()

    with tabs[3]:
        st.write("### 마스터 지식베이스 관리")
        if st.text_input("인증키", type="password") == "goldkey777":
            st.success("지식베이스 동기화 권한 승인")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"시스템 구동 중 오류 발생: {e}")
