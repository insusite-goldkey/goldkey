# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] auto_injury_coverage_advisor.py
# 자동차상해(자상) 특약 권유 상담 모듈 - 자손 vs 자상 비교 분석
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import os
from typing import Dict, Optional
import google.generativeai as genai


def calculate_compensation_comparison(
    fault_ratio: int,
    medical_cost: int,
    lost_income: int,
    consolation_money: int
) -> Dict:
    """
    자기신체사고 vs 자동차상해 보상액 비교 계산
    
    Args:
        fault_ratio: 피보험자 과실 비율 (0~100%)
        medical_cost: 치료비 (원)
        lost_income: 휴업손해 (원)
        consolation_money: 위자료 (원)
    
    Returns:
        {
            "fault_ratio": int,
            "self_bodily_injury": {
                "medical": int,
                "lost_income": int,
                "consolation": int,
                "total": int
            },
            "auto_injury": {
                "medical": int,
                "lost_income": int,
                "consolation": int,
                "total": int
            },
            "difference": int,
            "advantage_ratio": float,
            "recommendation": str,
            "case_description": str
        }
    """
    
    # 자기신체사고 (자손) 계산
    # - 과실 비율만큼 치료비 감액
    # - 휴업손해, 위자료는 보상 제외
    self_medical = int(medical_cost * (100 - fault_ratio) / 100)
    self_lost_income = 0  # 자손은 휴업손해 미지급
    self_consolation = 0  # 자손은 위자료 미지급
    self_total = self_medical
    
    # 자동차상해 (자상) 계산
    # - 과실 비율 무관 전액 지급
    # - 치료비 + 휴업손해 + 위자료 모두 보상
    auto_medical = medical_cost
    auto_lost_income = lost_income
    auto_consolation = consolation_money
    auto_total = auto_medical + auto_lost_income + auto_consolation
    
    # 차액 및 유리한 비율 계산
    difference = auto_total - self_total
    advantage_ratio = (auto_total / self_total) if self_total > 0 else float('inf')
    
    # 케이스 설명
    if fault_ratio == 100:
        case_description = f"🔴 **과실 100% 사고**: 자손은 보상 불가, 자상은 전액 보상 ({auto_total:,}원)"
        recommendation = "자동차상해 특약 필수! 자손으로는 1원도 받을 수 없습니다."
    elif fault_ratio >= 70:
        case_description = f"🟠 **과실 {fault_ratio}% 사고**: 자손 대비 자상이 {advantage_ratio:.1f}배 유리"
        recommendation = "자동차상해 특약 강력 추천! 과실이 높을수록 자상의 혜택이 큽니다."
    elif fault_ratio >= 40:
        case_description = f"🟡 **과실 {fault_ratio}% 사고**: 자손 대비 자상이 {advantage_ratio:.1f}배 유리"
        recommendation = "자동차상해 특약 권장! 휴업손해와 위자료까지 챙기세요."
    else:
        case_description = f"🟢 **과실 {fault_ratio}% 사고**: 자손 대비 자상이 {advantage_ratio:.1f}배 유리"
        recommendation = "자동차상해 특약 추천! 과실이 낮아도 자상이 훨씬 유리합니다."
    
    return {
        "fault_ratio": fault_ratio,
        "self_bodily_injury": {
            "medical": self_medical,
            "lost_income": self_lost_income,
            "consolation": self_consolation,
            "total": self_total
        },
        "auto_injury": {
            "medical": auto_medical,
            "lost_income": auto_lost_income,
            "consolation": auto_consolation,
            "total": auto_total
        },
        "difference": difference,
        "advantage_ratio": advantage_ratio,
        "recommendation": recommendation,
        "case_description": case_description
    }


def generate_customer_message(
    customer_name: str,
    comparison_result: Dict,
    gemini_api_key: str,
    agent_name: str = "골드키 담당자"
) -> str:
    """
    고객용 자동차상해 특약 권유 메시지 생성 (1:1 대화체)
    
    Args:
        customer_name: 고객 이름
        comparison_result: 비교 계산 결과
        gemini_api_key: Gemini API 키
        agent_name: 담당자 이름
    
    Returns:
        카카오톡 메시지 형식의 권유 메시지
    """
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        fault_ratio = comparison_result['fault_ratio']
        self_total = comparison_result['self_bodily_injury']['total']
        auto_total = comparison_result['auto_injury']['total']
        difference = comparison_result['difference']
        
        prompt = f"""
당신은 친절하고 전문적인 보험 설계사입니다. 고객에게 **자동차상해 특약**을 권유하는 1:1 대화체 카카오톡 메시지를 작성하세요.

**메시지 템플릿 (반드시 이 구조를 따를 것)**:

[제목: 고객님, 자동차보험에서 '이것' 하나면 사고 나도 든든합니다! 🏥]

안녕하세요, {customer_name} 고객님! 잘 지내고 계시죠? 😊

최근에 제 고객님 중에 한 분이 안타깝게 교통사고가 나셨는데, 다행히 보험을 잘 들어두셔서 치료비는 물론이고 일 못 하신 기간 보상까지 넉넉히 받으셨어요. 그때 제가 강조했던 '자동차상해' 담보 덕분이었죠.

고객님 보험 증권 보다가 꼭 직접 말씀드리고 싶어서 연락드렸어요. 보통 보험료 아끼려고 '자기신체사고'로 넣는 경우가 많은데, 사실 **'자동차상해'**로 바꾸는 건 짜장면 한 그릇 값 정도 차이밖에 안 나거든요. 하지만 사고 났을 때 받는 혜택은 하늘과 땅 차이입니다!

💡 왜 '자동차상해'여야 할까요? 딱 3가지만 기억하세요.

1️⃣ **내 과실을 따지지 않아요!**
보통 내 잘못이 있으면 보험금이 깎이잖아요? 그런데 이건 고객님 과실이 100%여도 병원비랑 보상금을 약정된 금액 그대로 다 드립니다.

2️⃣ **단순 병원비만 주는 게 아니에요!**
병원비는 기본이고, 사고 때문에 출근 못 하셔서 발생한 **'휴업손해'**랑 마음 고생하신 **'위자료'**까지 챙겨드려요. 마치 상대방한테 100% 대인 보상을 받는 것처럼 제 보험사에서 먼저 다 챙겨주는 거죠.

3️⃣ **병원 급수 따지느라 골머리 앓을 필요 없어요!**
'자기신체사고'는 다친 부위마다 등급을 매겨서 한도를 정해두지만, '자동차상해'는 그런 거 없이 가입하신 금액 안에서 치료비를 쿨하게 다 지원해 드립니다.

**실제 사례로 보면 이렇습니다:**
- 과실 {fault_ratio}% 사고 발생
- 치료비 {comparison_result['auto_injury']['medical']:,}원 + 휴업손해 {comparison_result['auto_injury']['lost_income']:,}원 + 위자료 {comparison_result['auto_injury']['consolation']:,}원

✅ **자기신체사고 (자손)**: {self_total:,}원만 받음
✅ **자동차상해 (자상)**: {auto_total:,}원 받음
💰 **차액**: {difference:,}원 더 받음!

대면 상담 때 제가 말씀드렸던 것처럼, 보험은 '가장 힘들 때' 돈 걱정 안 하게 해주는 게 진짜 목적이잖아요. 큰돈 들이지 않고 고객님과 가족분들의 안전망을 2배로 넓히는 방법이니, 이번 기회에 꼭 검토해 보셨으면 좋겠어요.

지금 바로 바꿔달라고 하시면 제가 바로 처리해 드릴 수 있습니다! 궁금한 점 있으시면 언제든 편하게 답장 주세요. 항상 안전운전하시고요! 🚗💨

**요구사항**:
1. 위 템플릿 구조를 정확히 따를 것
2. 친근하고 따뜻한 말투 사용 (~요, ~습니다)
3. 이모지 적절히 사용 (😊, 🏥, 💡, 🚗, 💰 등)
4. 실제 계산 결과를 자연스럽게 녹여낼 것
5. 보험료 차이 (짜장면 한 그릇 값) 강조
6. 3가지 핵심 혜택 명확히 설명
7. 카카오톡 메시지 길이에 맞게 (최대 1000자)

**출력 형식**:
위 템플릿을 그대로 사용하되, 고객명과 계산 결과만 실제 값으로 대체하세요.
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        # Gemini 실패 시 기본 템플릿 반환
        return f"""[제목: {customer_name} 고객님, 자동차보험에서 '이것' 하나면 사고 나도 든든합니다! 🏥]

안녕하세요, {customer_name} 고객님! 잘 지내고 계시죠? 😊

최근에 제 고객님 중에 한 분이 안타깝게 교통사고가 나셨는데, 다행히 보험을 잘 들어두셔서 치료비는 물론이고 일 못 하신 기간 보상까지 넉넉히 받으셨어요. 그때 제가 강조했던 '자동차상해' 담보 덕분이었죠.

고객님 보험 증권 보다가 꼭 직접 말씀드리고 싶어서 연락드렸어요. 보통 보험료 아끼려고 '자기신체사고'로 넣는 경우가 많은데, 사실 **'자동차상해'**로 바꾸는 건 짜장면 한 그릇 값 정도 차이밖에 안 나거든요. 하지만 사고 났을 때 받는 혜택은 하늘과 땅 차이입니다!

💡 왜 '자동차상해'여야 할까요? 딱 3가지만 기억하세요.

1️⃣ **내 과실을 따지지 않아요!**
보통 내 잘못이 있으면 보험금이 깎이잖아요? 그런데 이건 고객님 과실이 100%여도 병원비랑 보상금을 약정된 금액 그대로 다 드립니다.

2️⃣ **단순 병원비만 주는 게 아니에요!**
병원비는 기본이고, 사고 때문에 출근 못 하셔서 발생한 **'휴업손해'**랑 마음 고생하신 **'위자료'**까지 챙겨드려요. 마치 상대방한테 100% 대인 보상을 받는 것처럼 제 보험사에서 먼저 다 챙겨주는 거죠.

3️⃣ **병원 급수 따지느라 골머리 앓을 필요 없어요!**
'자기신체사고'는 다친 부위마다 등급을 매겨서 한도를 정해두지만, '자동차상해'는 그런 거 없이 가입하신 금액 안에서 치료비를 쿨하게 다 지원해 드립니다.

**실제 사례로 보면 이렇습니다:**
- 과실 {fault_ratio}% 사고 발생
- 치료비 {comparison_result['auto_injury']['medical']:,}원 + 휴업손해 {comparison_result['auto_injury']['lost_income']:,}원 + 위자료 {comparison_result['auto_injury']['consolation']:,}원

✅ **자기신체사고 (자손)**: {self_total:,}원만 받음
✅ **자동차상해 (자상)**: {auto_total:,}원 받음
💰 **차액**: {difference:,}원 더 받음!

대면 상담 때 제가 말씀드렸던 것처럼, 보험은 '가장 힘들 때' 돈 걱정 안 하게 해주는 게 진짜 목적이잖아요. 큰돈 들이지 않고 고객님과 가족분들의 안전망을 2배로 넓히는 방법이니, 이번 기회에 꼭 검토해 보셨으면 좋겠어요.

지금 바로 바꿔달라고 하시면 제가 바로 처리해 드릴 수 있습니다! 궁금한 점 있으시면 언제든 편하게 답장 주세요. 항상 안전운전하시고요! 🚗💨

---
⚠️ 메시지 생성 오류: {e}
"""


def render_auto_injury_coverage_advisor_block(
    customer_name: str = "고객",
    key_prefix: str = "auto_injury_adv"
) -> None:
    """
    자동차상해 특약 권유 상담 UI 블록
    
    Args:
        customer_name: 고객 이름
        key_prefix: 세션 키 접두사
    """
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#dbeafe 0%,#bfdbfe 50%,#93c5fd 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #3b82f6;'>
      <div style='color:#1e3a8a;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    🏥 자동차상해 특약 권유 상담
      </div>
      <div style='color:#1e40af;font-size:0.80rem;margin-top:5px;'>
    자손 vs 자상 비교 분석 및 고객 맞춤형 권유 메시지 자동 생성
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 세션 초기화
    if f"{key_prefix}_result" not in st.session_state:
        st.session_state[f"{key_prefix}_result"] = None
    if f"{key_prefix}_message" not in st.session_state:
        st.session_state[f"{key_prefix}_message"] = ""
    
    # 입력 섹션
    st.markdown("### 📊 사고 시나리오 입력")
    
    st.info("💡 **시뮬레이션 안내**: 고객이 사고를 당했을 때 자손과 자상의 보상액 차이를 비교합니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fault_ratio = st.slider(
            "피보험자 과실 비율 (%)",
            min_value=0,
            max_value=100,
            value=50,
            step=10,
            key=f"{key_prefix}_fault_ratio",
            help="고객의 과실이 클수록 자손과 자상의 차이가 커집니다"
        )
        
        medical_cost = st.number_input(
            "치료비 (원)",
            min_value=0,
            max_value=100_000_000,
            value=10_000_000,
            step=1_000_000,
            key=f"{key_prefix}_medical_cost",
            help="병원 치료비 총액"
        )
    
    with col2:
        lost_income = st.number_input(
            "휴업손해 (원)",
            min_value=0,
            max_value=100_000_000,
            value=5_000_000,
            step=500_000,
            key=f"{key_prefix}_lost_income",
            help="일 못 한 기간의 소득 손실"
        )
        
        consolation_money = st.number_input(
            "위자료 (원)",
            min_value=0,
            max_value=100_000_000,
            value=3_000_000,
            step=500_000,
            key=f"{key_prefix}_consolation_money",
            help="정신적 고통에 대한 배상"
        )
    
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    
    # 계산 버튼
    if st.button(
        "🔍 자손 vs 자상 비교 분석",
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_calculate_btn"
    ):
        with st.spinner("🤖 AI가 보상액을 비교 분석하고 있습니다..."):
            result = calculate_compensation_comparison(
                fault_ratio=fault_ratio,
                medical_cost=medical_cost,
                lost_income=lost_income,
                consolation_money=consolation_money
            )
            st.session_state[f"{key_prefix}_result"] = result
            st.rerun()
    
    # 결과 표시
    result = st.session_state.get(f"{key_prefix}_result")
    
    if result:
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:20px 0;'>", unsafe_allow_html=True)
        
        # 케이스 설명
        st.markdown("### 📋 분석 결과")
        st.markdown(result['case_description'])
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # 비교 분석
        st.markdown("### 💰 보상액 비교")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style='background:#fef2f2;border:2px solid #fca5a5;border-radius:10px;padding:14px;'>
              <div style='color:#991b1b;font-size:0.9rem;font-weight:800;margin-bottom:8px;'>
            ❌ 자기신체사고 (자손)
              </div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f"- **치료비**: {result['self_bodily_injury']['medical']:,}원")
            st.markdown(f"- **휴업손해**: {result['self_bodily_injury']['lost_income']:,}원")
            st.markdown(f"- **위자료**: {result['self_bodily_injury']['consolation']:,}원")
            st.markdown(f"### 총 수령액: {result['self_bodily_injury']['total']:,}원")
        
        with col2:
            st.markdown("""
            <div style='background:#ecfdf5;border:2px solid #6ee7b7;border-radius:10px;padding:14px;'>
              <div style='color:#065f46;font-size:0.9rem;font-weight:800;margin-bottom:8px;'>
            ✅ 자동차상해 (자상)
              </div>
            </div>""", unsafe_allow_html=True)
            
            st.markdown(f"- **치료비**: {result['auto_injury']['medical']:,}원")
            st.markdown(f"- **휴업손해**: {result['auto_injury']['lost_income']:,}원")
            st.markdown(f"- **위자료**: {result['auto_injury']['consolation']:,}원")
            st.markdown(f"### 총 수령액: {result['auto_injury']['total']:,}원")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # 차액 강조
        if result['difference'] > 0:
            st.success(f"💡 **자동차상해 특약으로 {result['difference']:,}원 더 받을 수 있습니다!** (자손 대비 {result['advantage_ratio']:.1f}배)")
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # 추천 메시지
        st.markdown("### 🎯 권유 포인트")
        st.info(result['recommendation'])
        
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:20px 0;'>", unsafe_allow_html=True)
        
        # 고객용 메시지 생성
        st.markdown("### 📱 고객 전달용 메시지 생성")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button(
                "✨ 메시지 자동 생성",
                type="primary",
                use_container_width=True,
                key=f"{key_prefix}_generate_msg_btn"
            ):
                with st.spinner("🤖 Gemini가 고객 맞춤형 메시지를 작성하고 있습니다..."):
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    
                    if not gemini_api_key:
                        st.error("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
                    else:
                        message = generate_customer_message(
                            customer_name=customer_name,
                            comparison_result=result,
                            gemini_api_key=gemini_api_key
                        )
                        st.session_state[f"{key_prefix}_message"] = message
                        st.rerun()
        
        with col2:
            if st.session_state.get(f"{key_prefix}_message"):
                if st.button(
                    "📋 클립보드에 복사",
                    use_container_width=True,
                    key=f"{key_prefix}_copy_msg_btn"
                ):
                    st.success("✅ 클립보드에 복사되었습니다! 카카오톡에 붙여넣기 하세요.")
        
        # 생성된 메시지 표시
        message = st.session_state.get(f"{key_prefix}_message")
        if message:
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📱 생성된 카카오톡 메시지")
            st.text_area(
                "message_preview",
                value=message,
                height=500,
                key=f"{key_prefix}_message_preview",
                label_visibility="collapsed"
            )
            
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            
            # 보험료 차이 안내
            st.markdown("#### 💰 보험료 차이 안내")
            st.info("""
**자기신체사고 (자손)**: 약 15,000원/년  
**자동차상해 (자상)**: 약 25,000원/년  
**차액**: 약 10,000원/년 (월 833원, 하루 27원)

💡 **짜장면 한 그릇 값 정도 차이**로 사고 시 수백만 원~수천만 원 더 받을 수 있습니다!
            """)
        
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:20px 0;'>", unsafe_allow_html=True)
        
        # 3대 핵심 혜택 요약
        st.markdown("### 🌟 자동차상해 특약 3대 핵심 혜택")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style='background:#fef3c7;border-radius:10px;padding:14px;text-align:center;'>
              <div style='font-size:2rem;'>🛡️</div>
              <div style='color:#92400e;font-size:0.85rem;font-weight:800;margin-top:8px;'>
            과실 100%여도<br>전액 보상
              </div>
            </div>""", unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style='background:#dbeafe;border-radius:10px;padding:14px;text-align:center;'>
              <div style='font-size:2rem;'>💼</div>
              <div style='color:#1e40af;font-size:0.85rem;font-weight:800;margin-top:8px;'>
            휴업손해+위자료<br>전부 보상
              </div>
            </div>""", unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style='background:#dcfce7;border-radius:10px;padding:14px;text-align:center;'>
              <div style='font-size:2rem;'>🏥</div>
              <div style='color:#166534;font-size:0.85rem;font-weight:800;margin-top:8px;'>
            병원 급수·등급<br>제한 없음
              </div>
            </div>""", unsafe_allow_html=True)
