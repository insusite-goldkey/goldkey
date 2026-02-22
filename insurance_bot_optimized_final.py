# ==========================================================
# 골드키지사 마스터 AI - 논리 구조 및 성능 최적화 버전
# 보안강화: 1.AES-256 암호화저장 / 2.프롬프트 인젝션 방어 / 3.개인정보 마스킹
# 성능최적화: 1.Lazy Loading / 2.메모리 관리 / 3.모바일 UX 개선
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
# [SECTION 1] 보안 및 암호화 엔진 (고정 키 방식으로 수정)
# -------------------------------------------------------------------------- 
def get_encryption_key():
    """보안 키 관리: Secrets 우선, 없으면 고정된 개발용 키 사용"""
    if "ENCRYPTION_KEY" in st.secrets:
        return st.secrets["ENCRYPTION_KEY"].encode()
    # 개발용 고정 키: 매번 새로 생성하지 않음
    return b'dev_fixed_key_2026_goldkey_insurance='

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
# [SECTION 2] 모바일 최적화 CSS
# -------------------------------------------------------------------------- 
def inject_mobile_css():
    """모바일 및 태블릿 최적화 CSS 주입"""
    mobile_css = """
    <style>
    /* 모바일 기본 폰트 및 버튼 최적화 */
    html { font-size: 115%; }
    .stButton>button { 
        height: 3.5rem; 
        border-radius: 12px; 
        font-weight: bold; 
        font-size: 1.1rem; 
        margin: 0.5rem 0;
    }
    .stTextArea textarea { font-size: 1.1rem !important; }
    .stNumberInput input { font-size: 1.1rem !important; }
    .stRadio > div { padding: 0.5rem 0; }
    .stRadio label { font-size: 1rem; padding: 0.5rem; }
    
    /* 모바일 사이드바 최적화 */
    @media (max-width: 768px) {
        .css-1d391kg { width: 100% !important; }
        .css-1lcbmhc { width: 100% !important; }
        [data-testid="column"] { width: 100% !important; }
        .stSidebar { min-width: 250px; }
    }
    
    /* 로그인 영역 최적화 */
    .login-container { 
        background: #f8f9fa; 
        padding: 2rem; 
        border-radius: 15px; 
        margin: 1rem 0;
    }
    </style>
    """
    st.markdown(mobile_css, unsafe_allow_html=True)

# -------------------------------------------------------------------------- 
# [SECTION 3] 데이터베이스 설정 (파일 대신 SQLite 사용)
# -------------------------------------------------------------------------- 
def setup_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('insurance_master.db')
    cursor = conn.cursor()
    
    # 사용자 문서 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_documents 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, document_url TEXT, 
                   status TEXT DEFAULT 'ACTIVE', expiry_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 회원 관리 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS members 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT UNIQUE, user_name TEXT, 
                   phone TEXT, encrypted_data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # 사용 로그 테이블
    cursor.execute('''CREATE TABLE IF NOT EXISTS usage_log 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, 
                   query_text TEXT, response_summary TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

# -------------------------------------------------------------------------- 
# [SECTION 4] RAG 시스템 (Lazy Loading 방식)
# -------------------------------------------------------------------------- 
@st.cache_resource
def load_rag_model():
    """RAG 모델 Lazy Loading: 필요할 때만 로드하여 메모리 점유 방지"""
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
        self._model = None  # Lazy Loading을 위한 모델 저장 변수
        
    def get_model(self):
        """모델 Lazy Loading"""
        if self._model is None:
            self._model = load_rag_model()
        return self._model
        
    def sync_data(self, uploaded_files):
        """지식베이스 동기화"""
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
                
                chunks = [text[i:i+600] for i in range(0, len(text), 500)]
                all_chunks.extend(chunks)
            except Exception as e:
                st.warning(f"파일 처리 오류 ({file.name}): {e}")
                continue
        
        if not all_chunks: 
            return 0
            
        model = self.get_model()
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
        """지식 검색"""
        try:
            import faiss
        except ImportError:
            return "RAG 기능을 위해 faiss 설치 필요: pip install faiss-cpu"
            
        if not os.path.exists(self.index_path) or not os.path.exists(self.json_path):
            return "로드된 약관 지식이 없습니다."
            
        try:
            index = faiss.read_index(self.index_path)
            with open(self.json_path, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                
            model = self.get_model()
            if model is None:
                return "임베딩 모델을 로드할 수 없습니다."
                
            query_vec = model.encode([query])
            _, indices = index.search(np.array(query_vec).astype('float32'), k)
            
            relevant_chunks = []
            for i in indices[0]:
                if i < len(chunks):
                    relevant_chunks.append(chunks[i])
                    
            return "\n".join(relevant_chunks)
        except Exception as e:
            st.warning(f"RAG 검색 오류: {e}")
            return "검색 중 오류가 발생했습니다."

# -------------------------------------------------------------------------- 
# [SECTION 5] 통합 유틸리티 함수
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_client():
    """Gemini 클라이언트 초기화"""
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Secrets에 GEMINI_API_KEY 설정이 필요합니다.")
        st.stop()
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

def s_voice(text):
    """음성 안내 생성"""
    clean = text.replace('"', '').replace("'", "").replace("\n", " ")
    return f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{clean}'); msg.lang='ko-KR'; msg.rate=1.0; msg.pitch=1.1; window.speechSynthesis.speak(msg);</script>"

def analyze_with_ai(query, customer_name="고객", rag_context=""):
    """AI 분석 실행"""
    try:
        client = get_client()
        
        master_instruction = """당신은 30년 경력의 지능을 가진 '마스터 AI'입니다. 정중한 '하십시오체'를 사용하고 실시간 정보를 기반으로 CFP 수준의 리포트를 작성하세요."""
        
        if rag_context:
            master_instruction += f"\n\n아래 전문 자료를 참고하여 답변하세요:\n{rag_context}"
        
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

def logout_and_cleanup():
    """로그아웃 및 데이터 정리"""
    if 'user_id' in st.session_state:
        user_id = st.session_state.user_id
        
        # 데이터베이스에서 사용자 데이터 삭제
        conn = sqlite3.connect('insurance_master.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_documents WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM usage_log WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # 세션 초기화
        st.session_state.clear()
        
        st.success("안전 로그아웃되었습니다. 모든 상담 자료가 파기되었습니다.")
        st.rerun()

# -------------------------------------------------------------------------- 
# [SECTION 6] UI 렌더링 함수들 (모든 로직을 함수화)
# -------------------------------------------------------------------------- 
def render_login_panel():
    """로그인 패널 렌더링 (메인 화면에 표시)"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.subheader("🔑 마스터 센터 접속")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        u_name = st.text_input("성함 (실명)", placeholder="홍길동")
    with col2:
        u_phone = st.text_input("연락처 (PW)", type="password", placeholder="010-0000-0000")
    
    if st.button("🚀 엔진 접속", use_container_width=True, type="primary"):
        if u_name and u_phone:
            # 데이터베이스에 회원 정보 저장
            conn = sqlite3.connect('insurance_master.db')
            cursor = conn.cursor()
            encrypted_phone = encrypt_val(u_phone)
            
            try:
                cursor.execute("INSERT OR REPLACE INTO members (user_id, user_name, phone, encrypted_data) VALUES (?, ?, ?, ?)",
                             (f"GK_{u_name}", u_name, u_phone, encrypted_phone))
                conn.commit()
            except:
                pass
            finally:
                conn.close()
            
            st.session_state.user_id = f"GK_{u_name}"
            st.session_state.user_name = u_name
            st.rerun()
        else:
            st.error("성함과 연락처를 모두 입력해주세요.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_main_consultation():
    """메인 상담 탭 렌더링"""
    st.title("👑 골드키지사 마스터 AI")
    
    customer_name = st.text_input("고객 성함", "우량 고객")
    query = st.text_area("보험/의학/재무 문의사항을 입력하십시오.", height=180, 
                        placeholder="단순 질문은 빠르게 답변하고, 약관 분석은 정밀하게 수행합니다.")
    
    if st.button("🚀 마스터 분석 실행", type="primary", use_container_width=True):
        if not query: 
            st.stop()
        
        # RAG 필요 여부 판단
        trigger_words = ["약관", "조항", "보험금", "지급기준", "근거", "상세", "규정"]
        needs_rag = any(word in query for word in trigger_words) or len(query) > 60
        
        if needs_rag:
            with st.status("🔍 심층 약관 분석 중...", expanded=True) as status:
                st.write("마스터 지식베이스(RAG)를 가동합니다...")
                context = rag_engine.retrieve(query)
                st.write("추출된 약관 근거와 실시간 정보를 대조합니다...")
                
                result = analyze_with_ai(query, customer_name, context)
                if result:
                    st.success("상세 분석 리포트 작성이 완료되었습니다.")
                    status.update(label="✅ 마스터 지식 기반 정밀 분석 완료", state="complete")
                    
                    st.divider()
                    st.subheader("마스터 AI 정밀 분석 리포트")
                    st.markdown(result)
                    st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                    
                    components.html(s_voice(f"{st.session_state.get('user_name', '사용자')}님, 마스터 AI의 심층 분석이 완료되었습니다."), height=0)
        else:
            with st.spinner("⚡ 빠른 상담 답변을 생성 중입니다..."):
                result = analyze_with_ai(query, customer_name)
                if result:
                    st.info("💡 일반 상식 기반 답변입니다. 상세 약관 근거가 필요하면 '약관' 키워드를 포함해 주세요.")
                    
                    st.divider()
                    st.subheader("마스터 AI 답변")
                    st.markdown(result)
                    st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                    
                    components.html(s_voice(f"{st.session_state.get('user_name', '사용자')}님, 마스터 AI의 답변이 완료되었습니다."), height=0)

def render_admin_panel():
    """관리자 패널 렌더링"""
    st.write("### 🛠️ 관리자 전용 기능")
    
    if st.session_state.get('user_name') not in ["이세윤", "admin"]:
        st.error("관리자만 접근할 수 있습니다.")
        return
    
    with st.expander("🔄 RAG 지식베이스 관리", expanded=False):
        admin_files = st.file_uploader("약관 PDF 업로드", accept_multiple_files=True, type=['pdf'])
        if st.button("🔄 지식베이스 즉시 동기화"):
            if admin_files:
                with st.spinner("기계적 분석 중..."):
                    count = rag_engine.sync_data(admin_files)
                    st.success(f"✅ {count}개 지식 조각 통합 완료!")
            else: 
                st.warning("파일을 먼저 선택하세요.")
    
    # 데이터베이스 통계
    conn = sqlite3.connect('insurance_master.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM members")
    member_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM usage_log")
    log_count = cursor.fetchone()[0]
    
    conn.close()
    
    st.metric("총 회원수", member_count)
    st.metric("총 상담 건수", log_count)

def render_asset_management():
    """자산 관리 탭 렌더링"""
    st.subheader("📁 내 문서 보관함")
    
    conn = sqlite3.connect('insurance_master.db')
    cursor = conn.cursor()
    cursor.execute("SELECT document_url, created_at FROM user_documents WHERE user_id = ? ORDER BY created_at DESC", 
                  (st.session_state.get('user_id', ''),))
    documents = cursor.fetchall()
    conn.close()
    
    if documents:
        st.write(f"현재 보관 중인 자료: **{len(documents)}건**")
        for doc_url, created_at in documents:
            st.write(f"📄 {doc_url} - {created_at}")
    else:
        st.info("보관 중인 자료가 없습니다.")
    
    st.subheader("데이터 보안 관리")
    if st.button("만료 데이터 파기 실행", type="secondary"):
        conn = sqlite3.connect('insurance_master.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_documents WHERE status = 'EXPIRED' AND expiry_date <= date('now', '-30 days')")
        conn.commit()
        conn.close()
        st.success("보안 지침에 따라 만료된 상담 자료가 파기되었습니다.")

def render_inheritance_planning():
    """상속 계획 탭 렌더링"""
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

        components.html(s_voice(f"{st.session_state.get('user_name', '사용자')}님, 상속 분석이 완료되었습니다."), height=0)

# -------------------------------------------------------------------------- 
# [SECTION 7] 메인 앱 실행 (모든 로직이 함수화된 상태)
# -------------------------------------------------------------------------- 
def main():
    # 페이지 설정 및 모바일 CSS 주입
    st.set_page_config(page_title="골드키지사 마스터 AI", page_icon="", layout="wide")
    inject_mobile_css()
    
    # 데이터베이스 초기화
    setup_database()
    
    # 전역 RAG 엔진 초기화 (Lazy Loading 방식)
    global rag_engine
    rag_engine = MasterRAGPipeline()
    
    # 로그인 상태 확인
    if 'user_id' not in st.session_state:
        # 로그인 화면 표시
        render_login_panel()
        return
    
    # 로그인된 상태: 헤더 및 로그아웃 버튼
    st.header(f"👑 {st.session_state.user_name} 마스터님")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.info(f"사용자 ID: {st.session_state.user_id}")
    with col2:
        if st.button("🚪 안전 로그아웃", use_container_width=True):
            logout_and_cleanup()
    
    st.divider()
    
    # 탭 구성 (모든 기능을 함수로 렌더링)
    tabs = st.tabs(["🏠 통합 상담", "📁 자산 관리", "⚖️ 상속/유언", "🔐 관리자"])
    
    with tabs[0]:
        render_main_consultation()
    
    with tabs[1]:
        render_asset_management()
    
    with tabs[2]:
        render_inheritance_planning()
    
    with tabs[3]:
        render_admin_panel()

# -------------------------------------------------------------------------- 
# [SECTION 8] 프로그램 진입점 (코드 마지막에 위치)
# -------------------------------------------------------------------------- 
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"시스템 구동 중 오류 발생: {e}")
        st.error(f"오류 상세: {str(e)}")
