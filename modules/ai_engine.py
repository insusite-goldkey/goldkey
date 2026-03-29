# ==========================================================
# AI 엔진 모듈
# ==========================================================

import streamlit as st
from google import genai
from google.genai import types
import streamlit.components.v1 as components
from modules.auth import get_client, sanitize_prompt

def render_chat_interface():
    """채팅 인터페이스 렌더링"""
    st.title("💬 마스터 AI 정밀 상담")
    
    customer_name = st.text_input("고객 성함", placeholder="고객 이름을 입력하세요")
    query = st.text_area("상담 내용", height=150, placeholder="보험, 재무, 건강 상담 내용을 입력하세요.")
    
    if st.button("🚀 정밀 분석 실행", type="primary", use_container_width=True):
        if not query or len(query.strip()) < 5:
            st.error("상담 내용을 충분히 입력해주세요.")
            return
        
        # 프롬프트 보안 필터링
        safe_query = sanitize_prompt(query)
        if "보안을 위해" in safe_query:
            st.error(safe_query)
            return
        
        with st.spinner("마스터 AI가 실시간 정보를 분석하고 있습니다..."):
            try:
                client = get_client()
                master_instruction = """당신은 30년 경력의 '마스터 AI'입니다. 
                
[감성 대화 원칙 - 필수 준수]
1. 기계적인 리포트 말투를 절대 사용하지 마세요.
2. 고객과 1:1로 대화하듯이 감성적이고 공감하는 언어를 사용하세요.
3. 부족한 보장을 설명할 때는 반드시 "고객님, 이 부분의 위험이 진심으로 걱정됩니다"와 같은 감성 표현을 포함하세요.
4. "~입니다", "~됩니다" 같은 딱딱한 표현보다는 "~하시면 좋겠습니다", "~해 주시길 바랍니다" 같은 부드러운 권유형 표현을 사용하세요.
5. 고객의 마음을 움직이는 화법으로 제안하되, 정중한 '하십시오체'를 유지하세요.
6. 실시간 정보를 기반으로 CFP 수준의 전문성을 유지하되, 따뜻한 감성을 잃지 마세요.

예시:
- ❌ "암 진단비 보장이 부족합니다."
- ✅ "고객님, 현재 암 진단비 보장이 많이 부족한 상황이라 진심으로 걱정됩니다. 만약의 상황에서 경제적 어려움이 가중될 수 있어 마음이 무겁습니다."
"""
                
                resp = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=[f"고객 {customer_name} 리포트 요청: {safe_query}"],
                    config=types.GenerateContentConfig(
                        system_instruction=master_instruction,
                        tools=[types.Tool(google_search_retrieval=types.GoogleSearchRetrieval())]
                    )
                )
                
                if resp.text:
                    st.divider()
                    st.subheader(f"📊 {customer_name}님을 위한 마스터 AI 정밀 리포트")
                    st.markdown(resp.text)
                    st.info("본 분석 결과의 최종 책임은 사용자에게 귀속됩니다.")
                    
                    # 성공 음성 안내
                    components.html(f"""
                    <script>
                        window.speechSynthesis.cancel();
                        var msg = new SpeechSynthesisUtterance("{st.session_state.user_name}님, 마스터 AI의 분석이 완료되었습니다.");
                        msg.lang='ko-KR'; msg.rate=1.0; msg.pitch=1.1;
                        window.speechSynthesis.speak(msg);
                    </script>
                    """, height=0)
                    
            except Exception as e:
                st.error(f"AI 분석 장애: {e}")

def render_inheritance_planning():
    """상속/유언 플랜 렌더링"""
    st.title("🏛️ 상속 및 증여 통합 설계")
    st.markdown("2026년 최신 세법 및 민법 제1000조 기준")
    
    c_name = st.text_input("상담 고객 성함", placeholder="고객 이름")
    masked_name = c_name[0] + "*" + c_name[-1] if len(c_name) > 1 else c_name
    
    st.info(f"보안 모드 가동 중: 분석 리포트에는 '{masked_name}'님으로 표기됩니다.")
    
    with st.expander("상속인 신분 관계 확정", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            spouse = st.radio("배우자 관계", ["법률혼 (상속권 있음)", "사실혼 (상속권 없음)"])
            child_legal = st.number_input("친자/양자 수", min_value=0, value=1)
        with c2:
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
        <div style="padding:30px; border:1px solid #eee; background:white; border-radius:10px;">
            <h2 style="color:#1E88E5; border-bottom:2px solid #1E88E5;">상속 및 증여 정밀 분석 리포트</h2>
            <p><b>고객:</b> {masked_name}님</p>
            <div style="margin:20px 0;">{res_text.replace(chr(10), '<br>')}</div>
            <div style="font-size:11px; color:#888; background:#f9f9f9; padding:10px; border-radius:5px;">
                <b>법적 책임 고지:</b> 본 리포트는 참고용이며 최종 결정의 책임은 사용자에게 있습니다.
            </div>
        </div>
        """
        st.components.v1.html(report_html, height=400, scrolling=True)
