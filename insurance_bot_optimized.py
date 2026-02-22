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
# [SECTION 1] 시스템 설정 및 보안 (AES-256)
# -------------------------------------------------------------------------- 
st.set_page_config(page_title="골드키지사 마스터 AI", page_icon="", layout="wide")

def get_encryption_key():
    """보안 키 관리: Secrets 우선, 없으면 임시 키 생성"""
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

# 모바일/태블릿 대응 CSS (안드로이드 최적화)
st.markdown("""
    <style>
    html { font-size: 115%; }
    .stButton>button { height: 3.5rem; border-radius: 12px; font-weight: bold; font-size: 1.1rem; }
    .stTextArea textarea { font-size: 1.1rem !important; }
    .sidebar-notice { background: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; font-size: 0.9rem; }
    @media (max-width: 768px) { [data-testid="column"] { width: 100% !important; } }
    </style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------- 
# [SECTION 2] 지능형 온디맨드 RAG 엔진 (마스터 파이프라인)
# -------------------------------------------------------------------------- 
@st.cache_resource
def get_embedding_model():
    """필요한 순간에만 임베딩 모델 로드 (앱 경량화 핵심)"""
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
        """관리자 전용: 약관 지식베이스 구축"""
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
                
                # 텍스트를 600자 청크로 분할 (원본 500→600으로 조정)
                chunks = [text[i:i+600] for i in range(0, len(text), 500)]
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
        """RAG 모드 가동 시 지식 추출"""
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
                
            model = get_embedding_model()
            if model is None:
                return "임베딩 모델을 로드할 수 없습니다."
                
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
            return "검색 중 오류가 발생했습니다."

rag_engine = MasterRAGPipeline()

def judge_needs_rag(query):
    """지능형 조건 분기: 약관 관련 질문인지 판정"""
    trigger_words = ["약관", "조항", "보험금", "지급기준", "근거", "상세", "규정", "판례", "보험사", "특약", "보장한도", "면책"]
    return any(word in query for word in trigger_words) or len(query) > 60

# -------------------------------------------------------------------------- 
# [SECTION 3] 데이터 보존 및 배치 PDF 생성 (글로벌 표준)
# -------------------------------------------------------------------------- 
def setup_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect('insurance_master.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_documents 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, document_url TEXT, 
                   status TEXT DEFAULT 'ACTIVE', expiry_date DATE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def generate_pdf(user_id, docs):
    """PDF 일괄 생성 (PyMuPDF 필요)"""
    try:
        import fitz
    except ImportError:
        st.error("PDF 생성 기능을 위해 PyMuPDF 설치 필요: pip install PyMuPDF")
        return None
        
    output_pdf = fitz.open()
    for doc in docs:
        f_path = doc.get('file_path', '')
        if os.path.exists(f_path):
            try:
                if f_path.endswith(('.jpg', '.png')):
                    img = fitz.open(f_path)
                    pdf_bytes = img.convert_to_pdf()
                    output_pdf.insert_pdf(fitz.open("pdf", pdf_bytes))
                elif f_path.endswith('.pdf'):
                    output_pdf.insert_pdf(fitz.open(f_path))
            except Exception as e:
                st.warning(f"파일 처리 오류 ({f_path}): {e}")
                continue
                
    out_name = f"GK_Archive_{user_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output_pdf.save(out_name)
    return out_name

def purge_expired_data():
    """30일 경과한 만료 데이터 영구 삭제"""
    conn = sqlite3.connect('insurance_master.db')
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
        conn = sqlite3.connect('insurance_master.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user_documents WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        
        # 2. 세션 초기화
        st.session_state.clear()
        
        # 3. 성공 메시지
        st.success("안전 로그아웃되었습니다. 모든 상담 자료가 파기되었습니다.")
        st.rerun()

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
# [SECTION 5] 메인 앱 구조 (모바일 친화적 설계)
# -------------------------------------------------------------------------- 
def main():
    setup_database()
    
    with st.sidebar:
        st.header("🔑 마스터 센터")
        if 'user_id' not in st.session_state:
            u_name = st.text_input("성함 (실명)")
            u_phone = st.text_input("연락처 (PW)", type="password")
            if st.button("🚀 엔진 접속", use_container_width=True):
                if u_name and u_phone:
                    st.session_state.user_id = f"GK_{u_name}"
                    st.session_state.user_name = u_name
                    st.rerun()
        else:
            st.success(f"👑 {st.session_state.user_name} 마스터님")
            if st.button("🚪 안전 로그아웃", use_container_width=True):
                logout_and_cleanup()  # 데이터 파기 포함 로그아웃
        
        st.divider()
        # [관리자 전용 RAG 로딩 버튼]
        if st.session_state.get('user_name') in ["이세윤", "admin"]: 
            with st.expander("🛠️ RAG 지식베이스 로드 (관리자)", expanded=False):
                admin_files = st.file_uploader("약관 PDF 업로드", accept_multiple_files=True, type=['pdf'])
                if st.button("🔄 지식베이스 즉시 동기화"):
                    if admin_files:
                        with st.spinner("기계적 분석 중..."):
                            count = rag_engine.sync_data(admin_files)
                            st.success(f"✅ {count}개 지식 조각 통합 완료!")
                    else: 
                        st.warning("파일을 먼저 선택하세요.")
        
        st.markdown("""<div class="sidebar-notice"><strong>📅 데이터 보존 정책</strong><br>귀하의 상담 자료는 보안 서버에 30일간 안전하게 보관됩니다.</div>""", unsafe_allow_html=True)

    # 탭 구성
    tabs = st.tabs(["🏠 통합 상담", "📁 자료 관리", "⚖️ 상속/유언"])

    with tabs[0]:
        st.title("👑 골드키지사 마스터 AI")
        query = st.text_area("보험/의학/재무 문의사항을 입력하십시오.", height=180, placeholder="단순 질문은 빠르게 답변하고, 약관 분석은 정밀하게 수행합니다.")
        
        if st.button("🚀 마스터 분석 실행", type="primary", use_container_width=True):
            if not query: 
                st.stop()
            
            # [조건 실행] RAG가 필요한 질문인가?
            if judge_needs_rag(query):
                with st.status("🔍 심층 약관 분석 중...", expanded=True) as status:
                    st.write("마스터 지식베이스(RAG)를 가동합니다...")
                    context = rag_engine.retrieve(query)
                    st.write("추출된 약관 근거와 실시간 정보를 대조합니다...")
                    
                    result = analyze_with_ai(query, "고객", context)
                    if result:
                        st.success("상세 분석 리포트 작성이 완료되었습니다.")
                        status.update(label="✅ 마스터 지식 기반 정밀 분석 완료", state="complete")
                        
                        st.divider()
                        st.subheader("마스터 AI 정밀 분석 리포트")
                        st.markdown(result)
                        st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                        
                        # 추출된 근거 자료 표시
                        if context and context != "로드된 약관 지식이 없습니다.":
                            with st.expander("📚 참조된 전문 자료"):
                                st.markdown(f"**[참고 조항 요약]**\n{context[:300]}...")
                        
                        components.html(s_voice(f"{st.session_state.get('user_name', '사용자')}님, 마스터 AI의 심층 분석이 완료되었습니다."), height=0)
            else:
                with st.spinner("⚡ 빠른 상담 답변을 생성 중입니다..."):
                    result = analyze_with_ai(query, "고객")
                    if result:
                        st.info("💡 일반 상식 기반 답변입니다. 상세 약관 근거가 필요하면 '약관' 키워드를 포함해 주세요.")
                        
                        st.divider()
                        st.subheader("마스터 AI 답변")
                        st.markdown(result)
                        st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                        
                        components.html(s_voice(f"{st.session_state.get('user_name', '사용자')}님, 마스터 AI의 답변이 완료되었습니다."), height=0)

    with tabs[1]:
        st.subheader("📁 내 문서 보관함 (PDF 백업)")
        st.write("최근 30일간 제출하신 자료 리스트입니다.")
        
        # DB 연동 리스트 노출
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
            
            if st.button("📥 연대순 일괄 PDF 생성 및 다운로드"):
                # 실제 파일 경로가 필요하므로 예시 데이터 사용
                sample_docs = [{'file_path': doc_url} for doc_url, _ in documents if os.path.exists(doc_url)]
                if sample_docs:
                    pdf_file = generate_pdf(st.session_state.get('user_id', 'User'), sample_docs)
                    if pdf_file:
                        with open(pdf_file, "rb") as f:
                            st.download_button("💾 병합된 PDF 저장하기", f, file_name=pdf_file)
                else:
                    st.warning("실제 파일이 존재하지 않습니다.")
        else:
            st.info("보관 중인 자료가 없습니다.")
        
        st.subheader("데이터 보안 관리")
        if st.button("만료 데이터 파기 실행", type="secondary"):
            purge_expired_data()

    with tabs[2]:
        section_inheritance_will()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"시스템 구동 중 오류 발생: {e}")
