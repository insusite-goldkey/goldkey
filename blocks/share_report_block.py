# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] share_report_block.py
# Phase 7: 선택적 요약 및 카카오톡 공유 기능
# AI 분석 결과를 고객 친화적으로 요약하여 카카오톡으로 공유
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import os
from typing import Dict, Optional, List

# ── [GP-SEC] google.generativeai 조건부 import (설치 실패 시 앱 시작 차단 방지) ──
try:
    import google.generativeai as genai
    _GENAI_OK = True
except ImportError:
    genai = None
    _GENAI_OK = False


# ══════════════════════════════════════════════════════════════════════════════
# 대한민국 주요 보험사 콜센터 번호
# ══════════════════════════════════════════════════════════════════════════════

INSURANCE_CALL_CENTERS = {
    "삼성화재": "1588-5114",
    "현대해상": "1588-5656",
    "DB손해보험": "1588-0100",
    "KB손해보험": "1544-0114",
    "메리츠화재": "1566-7711",
    "한화손해보험": "1566-8000",
    "롯데손해보험": "1588-3344",
    "흥국화재": "1688-1688",
    "MG손해보험": "1588-5959",
    "AXA손해보험": "1566-1566",
    "처브손해보험": "1566-5959",
    "하나손해보험": "1566-3000",
    "삼성생명": "1588-3114",
    "한화생명": "1588-6363",
    "교보생명": "1588-1001",
    "신한생명": "1588-5580",
    "동양생명": "1588-1500",
    "미래에셋생명": "1588-3344",
    "KB생명": "1544-0114",
    "메트라이프생명": "1588-9600",
    "푸르덴셜생명": "1588-1004",
    "AIA생명": "1588-9898",
    "기타 (직접 입력)": ""
}

# 면책 조항 (법적 민원 방지)
DISCLAIMER_TEXT = "\n\n⚠️ ※ 본 안내는 고객님의 이해를 돕기 위한 참고용이며, 실제 보험금 지급 여부는 가입하신 특약 및 보험사의 최종 심사 결과에 따라 달라질 수 있습니다."


def generate_kakao_friendly_summary(
    original_content: str,
    summary_option: str,
    gemini_api_key: str,
    insurance_company: str = "",
    call_center_number: str = ""
) -> str:
    """
    Gemini 1.5 Pro를 사용하여 카카오톡 메시지에 적합한 친절한 요약본 생성
    
    Args:
        original_content: 원본 분석 결과
        summary_option: 요약 옵션 (A/B/C/D)
        gemini_api_key: Gemini API 키
        insurance_company: 선택한 보험사명
        call_center_number: 보험사 콜센터 번호
    
    Returns:
        카카오톡 메시지 형식의 요약본
    """
    if not _GENAI_OK:
        return "⚠️ AI 요약 기능을 사용할 수 없습니다. google-generativeai 패키지가 설치되지 않았습니다."
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        # 옵션별 프롬프트 설정
        if summary_option == "A":
            prompt = f"""
당신은 친절한 보험 설계사입니다. 아래 의료 분석 결과를 고객에게 카카오톡으로 보낼 메시지로 변환하세요.

**요구사항**:
1. **진단 및 치료 소견만** 포함 (보험금 청구 관련 내용은 제외)
2. 친절하고 전문적인 말투 사용 (~요, ~습니다)
3. 이모지 적절히 사용 (🏥, 💊, 📋, 💡, ✅ 등)
4. 카카오톡 메시지 길이에 맞게 간결하게 (최대 500자)
5. 전문 용어는 쉽게 풀어서 설명
6. 인사말과 마무리 인사 포함

**원본 분석 결과**:
{original_content}

**출력 형식**:
🏥 [진단 및 치료 소견 안내]

안녕하세요, [고객명]님.

[진단 내용 요약]
[향후 치료 방향]

궁금하신 점 있으시면 언제든 연락 주세요!

**중요**: 메시지 마지막에 보험사 콜센터 정보와 면책 조항을 반드시 포함하세요.
"""
        
        elif summary_option == "B":
            prompt = f"""
당신은 친절한 보험 설계사입니다. 아래 의료 분석 결과를 바탕으로 **보험금 청구 안내 메시지**를 작성하세요.

**요구사항**:
1. **보험금 청구 및 준비 서류만** 포함 (의료 소견은 간략히)
2. 친절하고 전문적인 말투 사용 (~요, ~습니다)
3. 이모지 적절히 사용 (📄, 💰, ✅, 📋, 💡 등)
4. 카카오톡 메시지 길이에 맞게 간결하게 (최대 600자)
5. 실손보험과 후유장해 구분하여 설명
6. 필요 서류를 체크리스트 형식으로 제시

**원본 분석 결과**:
{original_content}

**출력 형식**:
📄 [보험금 청구 안내]

안녕하세요, [고객명]님.

[청구 가능 항목 및 필요 서류]

궁금하신 점 있으시면 언제든 연락 주세요!

**중요**: 메시지 마지막에 보험사 콜센터 정보와 면책 조항을 반드시 포함하세요.
"""
        
        elif summary_option == "C":  # 옵션 C: 전체 요약
            prompt = f"""
당신은 친절한 보험 설계사입니다. 아래 의료 분석 결과를 고객에게 카카오톡으로 보낼 **전체 요약 메시지**로 작성하세요.

**요구사항**:
1. **진단/치료 + 보험금 청구** 모두 포함
2. 친절하고 전문적인 말투 사용 (~요, ~습니다)
3. 이모지 적절히 사용 (🏥, 💊, 📄, 💰, ✅, 💡 등)
4. 카카오톡 메시지 길이에 맞게 간결하게 (최대 700자)
5. 전문 용어는 쉽게 풀어서 설명
6. 섹션별로 구분하여 가독성 높이기

**원본 분석 결과**:
{original_content}

**출력 형식**:
📋 **전체 요약**

안녕하세요, [고객명]님.

📋 **진단 요약**
[진단 내용]

💊 **치료 방향**
[치료 계획]

💰 **보험금 청구 안내**
[청구 가능 항목 및 필요 서류]

궁금하신 점 있으시면 언제든 연락 주세요!

**중요**: 메시지 마지막에 보험사 콜센터 정보와 면책 조항을 반드시 포함하세요.
"""
        
        elif summary_option == "D":  # 옵션 D: 근접사고 및 현장조사 대처 요령
            prompt = f"""
당신은 경험 많은 보험 설계사입니다. 고객이 **가입 1~3개월 내 사고(근접사고)**로 보험사에서 손해사정인(조사자)이 파견되는 상황입니다. 
아래 의료 분석 결과를 바탕으로, 고객이 현장조사 및 병원 진료 시 주의해야 할 사항을 **전문적이고 단호하면서도 안심시키는 말투**로 안내하세요.

**핵심 지식: 현장조사 서류 서명 가이드**

**⭕ 서명해도 되는 서류 (기본 필수 서류)**:
1. 개인정보 수집·이용·제공 동의서 (보험금 심사 필수 서류)
2. 의무기록 열람 및 사본발급 위임장/동의서 (단, 병원명이 명시된 것만! 백지 위임장은 절대 금지)

**❌ 절대 서명하면 안 되는 서류 (독소 조항 4대장)**:
1. **국민건강보험공단 요양급여내역 발급 위임장**
   - 위험성: 과거 5~10년 치 모든 병원/약국 진료 기록을 보험사가 전부 조회할 수 있는 '프리패스 권한'. 이번 사고와 무관한 과거 감기, 염좌 등 사소한 기록까지 다 뒤져서 '고지의무 위반' 꼬투리를 잡고 보험을 해지하려는 목적. 의무 서류가 아님!

2. **국세청 연말정산 의료비 내역 조회 동의서**
   - 위험성: 건강보험공단 서류와 똑같은 목적으로, 고객이 긁은 병원비 카드 내역을 추적해 과거 병력을 털어보려는 서류. 절대 서명 금지.

3. **의료자문 동의서 (제3의료기관 자문 동의서)**
   - 위험성: 현재 주치의의 진단을 믿지 못하겠으니, 보험사와 연계된 다른 의사에게 서류만 보내서 다시 판정받겠다는 동의서. 십중팔구 고객에게 불리한 결과(기왕증 100%, 장해 없음 등)가 나오며, 보험금 삭감의 합법적 근거가 됨.

4. **백지 위임장 (병원명이 적히지 않은 위임장)**
   - 위험성: 보험사가 임의로 병원명을 채워 넣어 과거 병력을 무제한 조회할 수 있음.

**요구사항**:
1. **조사자 미팅 시 대처 방안** - 위 서류 서명 가이드를 명확히 분류하여 설명
2. **병원 진료 시 절대 주의사항** (과거 병력 언급 금지, 인과관계 명확히)
3. **향후 치료 방향** (조사 기간 중 비급여 치료 보류 권장)
4. 전문적이고 단호하면서도 고객을 안심시키는 말투 (~요, ~습니다)
5. 이모지 적절히 사용 (⭕, ❌, 🚨, ⚠️, 📝, 🛡️, 💡 등)
6. 카카오톡 메시지 길이에 맞게 간결하게 (최대 1000자)
7. 법적 책임을 회피하는 표현 사용 ("가급적", "권장", "통상적으로" 등)
8. 조사자가 압박해도 단호히 거부할 수 있는 대응 멘트 포함

**원본 분석 결과**:
{original_content}

**출력 형식**:
🚨 [보험사 현장조사 대처 및 치료 주의사항 안내]

안녕하세요, [고객명]님.
가입하신 지 얼마 되지 않아 사고가 발생하여(근접사고) 보험사에서 통상적인 확인 절차로 손해사정인(조사자)을 파견하게 되었습니다. 너무 걱정하지 마시고 아래 사항만 주의해 주시면 됩니다!

1️⃣ **조사자 미팅 시 대처 방안 (서명 주의!)**

⭕ **서명해도 되는 서류**:
- 개인정보 수집·이용·제공 동의서 (필수)
- 의무기록 열람 위임장 (단, 병원명이 명시된 것만!)

❌ **절대 서명하면 안 되는 서류**:
- 국민건강보험공단 요양급여내역 위임장 (과거 5~10년 병력 전부 조회 → 고지의무 위반 꼬투리)
- 국세청 연말정산 조회 동의서 (카드 내역으로 과거 병력 추적)
- 의료자문 동의서 (보험사 유리한 자문 결과로 보험금 삭감)
- 백지 위임장 (병원명 없는 위임장)

💡 **대응 멘트**: "병원 의무기록 떼는 위임장만 해드리고, 건강보험공단 조회나 의료자문 동의서는 제 담당 설계사님이 절대 해주지 말라고 하셨습니다."

2️⃣ **병원 진료 시 절대 주의사항 (초진 차트 방어)**
- 말조심: "예전부터 아팠다" 또는 "몇 년 전에도 삐끗했다"는 발언 절대 금물
- 명확한 인과관계: 반드시 "이번 사고로 처음 심하게 아프기 시작했다"고 명확히 말씀하세요

3️⃣ **향후 치료 방향**
- 조사 결과가 나올 때까지는 비급여 도수치료나 고가 MRI는 보류될 수 있으니, 우선 급여 물리치료와 약물치료 위주로 진행하시기를 권장합니다.

서명 전 헷갈리시면 언제든 사진 찍어 보내주세요!

**중요**: 메시지 마지막에 보험사 콜센터 정보와 면책 조항을 반드시 포함하세요.
"""
        
        else:  # 옵션 E: 보험사기 경고 및 대처 가이드
            prompt = f"""
당신은 경험 많은 보험 설계사입니다. 고객님께서 **미세 충돌 사고**를 당하셨는데, 상대방이 과장된 청구를 할 가능성이 있는 상황입니다.
아래 AI 분석 결과를 바탕으로, 고객이 **연성 보험사기(Soft Fraud)**에 대응할 수 있도록 **전문적이고 단호한 법적 가이드**를 작성하세요.

**핵심 지식: 연성 보험사기 대응 4단계**

**1단계: 객관적 증거 확보**
- 마디모(Madimo) 프로그램 신청: 도로교통공단(1577-1120)의 충격량 분석을 통해 '인명 피해가 발생할 정도의 충격이 아님'을 과학적으로 증명
- AI 정밀 분석 리포트: 본 앱이 제공한 "물리 법칙에 위배되는 과장된 신체 움직임" 분석 자료를 증거로 활용

**2단계: 보험사 SIU(사기조사팀) 연계**
- 해당 보험사 SIU에 '보험사기 의심 건'으로 정식 조사 의뢰
- 과거 유사업종 및 동일 부위 반복 청구 이력 확인 요청

**3단계: 법적 고지 및 압박**
- 보험사기방지 특별법 제8조 안내: "거짓이나 그 밖의 부정한 방법으로 보험금을 청구하거나 수령한 자는 10년 이하의 징역 또는 5천만 원 이하의 벌금에 처한다"
- 내용증명 또는 문자로 법적 처벌 수위 고지
- 금융감독원(1332) 보험사기 신고 센터 접수 예고

**4단계: 채무부존재 확인 소송 (최후의 수단)**
- 치료비 지급을 거부하고, 법원에 "배상 책임 없음"을 확인하는 소송 제기
- 소송 부담감으로 상대방이 합의를 포기하는 경우가 많음

**요구사항**:
1. **분석 결과 요약** - AI가 감지한 미세 충돌 및 과장 행동 증거를 명확히 설명
2. **법적 근거 제시** - 보험사기방지 특별법 제8조 명시
3. **대응 단계 안내** - 위 4단계를 순서대로 설명
4. **주요 연락처 제공** - 금융감독원(1332), 도로교통공단(1577-1120), 경찰청(112)
5. 전문적이고 단호하면서도 고객을 안심시키는 말투 (~요, ~습니다)
6. 이모지 적절히 사용 (🚨, ⚖️, 📋, 🔍, 💡, ⚠️ 등)
7. 카카오톡 메시지 길이에 맞게 간결하게 (최대 1000자)

**원본 분석 결과**:
{original_content}

**출력 형식**:
🚨 [보험사기 경고 및 대처 가이드]

안녕하세요, [고객명]님.

해당 사고는 미세 접촉으로 분석되었으며, 상대방의 청구가 과도할 경우 '연성 보험사기(Soft Fraud)'에 해당할 가능성이 높습니다.

📊 **AI 분석 결과**
[미세 충돌 판별 및 과장 행동 감지 내용]

⚖️ **법적 근거**
보험사기방지 특별법 제8조: "거짓이나 그 밖의 부정한 방법으로 보험금을 청구하거나 수령한 자는 10년 이하의 징역 또는 5천만 원 이하의 벌금에 처한다."

🛡️ **대응 방법**
1️⃣ 마디모(Madimo) 신청 (1577-1120)
2️⃣ 보험사 SIU 조사 의뢰
3️⃣ 법적 고지 (내용증명 발송)
4️⃣ 금융감독원 신고 (1332)

강력히 대응하실 것을 권고드립니다!

**중요**: 메시지 마지막에 보험사 콜센터 정보와 면책 조항을 반드시 포함하세요.
"""
        
        # Gemini API 호출
        response = model.generate_content(prompt)
        summary = response.text.strip()
        
        # 보험사 콜센터 정보 추가
        if insurance_company and call_center_number:
            summary += f"\n\n📞 [{insurance_company}] 보상청구 콜센터: {call_center_number}"
        
        # 면책 조항 추가 (항상 포함)
        summary += DISCLAIMER_TEXT
        
        return summary
    
    except Exception as e:
        return f"❌ 요약 생성 실패: {e}\n\n원본 내용을 그대로 사용하세요."


def render_share_report_block(
    analysis_content: str,
    customer_name: str = "고객",
    block_title: str = "AI 분석 결과",
    key_prefix: str = "share_report"
) -> None:
    """
    AI 분석 결과 공유용 UI 블록
    
    Args:
        analysis_content: 원본 분석 결과 (의무기록 해석, 영상 분석 등)
        customer_name: 고객 이름
        block_title: 블록 제목
        key_prefix: 세션 키 접두사
    """
    
    if not _GENAI_OK:
        st.warning("⚠️ AI 요약 기능을 사용할 수 없습니다. google-generativeai 패키지가 설치되지 않았습니다.")
        return
    
    if not analysis_content or len(analysis_content.strip()) < 10:
        st.info("💡 분석 결과가 없습니다. 먼저 AI 분석을 실행하세요.")
        return
    
    # 세션 초기화
    if f"{key_prefix}_summary" not in st.session_state:
        st.session_state[f"{key_prefix}_summary"] = ""
    if f"{key_prefix}_option" not in st.session_state:
        st.session_state[f"{key_prefix}_option"] = "C"
    
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    
    # 공유 섹션 헤더
    st.markdown("""
    <div style='background:linear-gradient(135deg,#e0f2fe 0%,#bae6fd 50%,#7dd3fc 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #0284c7;'>
      <div style='color:#075985;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    📱 고객에게 카톡으로 보내기
      </div>
      <div style='color:#0c4a6e;font-size:0.80rem;margin-top:5px;'>
    AI 분석 결과를 고객 친화적으로 요약하여 카카오톡으로 공유하세요
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 요약 옵션 선택
    # 보험사 선택
    st.markdown("### 🏢 청구할 보험사 선택")
    
    insurance_company = st.selectbox(
        "보험금을 청구할 보험사를 선택하세요",
        options=list(INSURANCE_CALL_CENTERS.keys()),
        key=f"{key_prefix}_insurance_select",
        help="선택한 보험사의 콜센터 번호가 메시지에 자동으로 포함됩니다."
    )
    
    # 기타 선택 시 직접 입력
    if insurance_company == "기타 (직접 입력)":
        col_a, col_b = st.columns(2)
        with col_a:
            custom_insurance_name = st.text_input(
                "보험사명",
                key=f"{key_prefix}_custom_insurance_name",
                placeholder="예: ABC생명"
            )
        with col_b:
            custom_call_center = st.text_input(
                "콜센터 번호",
                key=f"{key_prefix}_custom_call_center",
                placeholder="예: 1588-0000"
            )
        
        if custom_insurance_name and custom_call_center:
            insurance_company = custom_insurance_name
            call_center_number = custom_call_center
        else:
            call_center_number = ""
    else:
        call_center_number = INSURANCE_CALL_CENTERS.get(insurance_company, "")
    
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    # 요약 옵션 선택
    st.markdown("### 📝 요약 옵션 선택")
    
    summary_option = st.radio(
        "고객에게 보낼 내용을 선택하세요",
        options=["A", "B", "C", "D", "E"],
        format_func=lambda x: {
            "A": "🏥 진단 및 치료 소견 요약 (현재 상태와 향후 치료 방향만 친절하게)",
            "B": "📄 보험금 청구 및 준비 서류 (실손/후유장해 청구 팁과 필요 서류만 명확하게)",
            "C": "📋 전체 요약 (진단 + 치료 + 보험금 청구를 간결하게 통합)",
            "D": "🚨 근접사고 및 현장조사 대처 요령 (가입 1~3개월 내 사고 시 조사자 미팅 및 병원 진료 주의사항)",
            "E": "🚨 보험사기 경고 및 대처 가이드 (미세 충돌 시 과장 청구 의심 시 법적 대응 방법)"
        }[x],
        key=f"{key_prefix}_option_radio",
        horizontal=False
    )
    
    st.session_state[f"{key_prefix}_option"] = summary_option
    
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    # 요약본 생성 버튼
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if st.button(
            "✨ 요약본 생성",
            type="primary",
            use_container_width=True,
            key=f"{key_prefix}_generate_btn"
        ):
            with st.spinner("🤖 Gemini가 카카오톡 메시지를 작성하고 있습니다..."):
                gemini_api_key = os.getenv("GEMINI_API_KEY")
                
                if not gemini_api_key:
                    st.error("❌ GEMINI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
                else:
                    summary = generate_kakao_friendly_summary(
                        original_content=analysis_content,
                        summary_option=summary_option,
                        gemini_api_key=gemini_api_key,
                        insurance_company=insurance_company,
                        call_center_number=call_center_number
                    )
                    
                    # 고객 이름 치환
                    summary = summary.replace("[고객명]", customer_name)
                    
                    st.session_state[f"{key_prefix}_summary"] = summary
                    st.success("✅ 요약본이 생성되었습니다!")
    
    with col2:
        if st.session_state[f"{key_prefix}_summary"]:
            if st.button(
                "🔄 다시 생성",
                use_container_width=True,
                key=f"{key_prefix}_regenerate_btn"
            ):
                st.session_state[f"{key_prefix}_summary"] = ""
                st.rerun()
    
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    
    # 요약본 표시 및 수정
    if st.session_state[f"{key_prefix}_summary"]:
        st.markdown("### 📱 카카오톡 메시지 미리보기")
        
        # 텍스트 박스로 수정 가능하게
        edited_summary = st.text_area(
            "메시지를 수정할 수 있습니다",
            value=st.session_state[f"{key_prefix}_summary"],
            height=300,
            key=f"{key_prefix}_summary_textarea",
            help="메시지를 직접 수정한 후 복사하거나 공유하세요"
        )
        
        st.session_state[f"{key_prefix}_summary"] = edited_summary
        
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        
        # 복사 및 공유 버튼
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            # 클립보드 복사 버튼
            # f-string 내부에서 백슬래시를 사용할 수 없으므로 미리 이스케이프 처리
            # JavaScript에서 사용할 JSON 문자열로 변환
            import json
            json_safe_summary = json.dumps(edited_summary)
            
            copy_button_html = f"""
            <button onclick="copyToClipboard()" style="
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 20px;
                font-size: 0.95rem;
                font-weight: 700;
                cursor: pointer;
                width: 100%;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: all 0.2s;
            " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.15)';" 
               onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)';">
                📋 복사하기
            </button>
            
            <script>
            function copyToClipboard() {{
                const text = {json_safe_summary};
                navigator.clipboard.writeText(text).then(function() {{
                    alert('✅ 클립보드에 복사되었습니다!' + String.fromCharCode(10) + '카카오톡에 붙여넣기(Ctrl+V) 하세요.');
                }}, function(err) {{
                    alert('❌ 복사 실패: ' + err);
                }});
            }}
            </script>
            """
            st.components.v1.html(copy_button_html, height=60)
        
        with col2:
            # 카카오톡 공유 버튼 (딥링크)
            from urllib.parse import quote
            encoded_text = quote(edited_summary[:500])
            kakao_deeplink = f"kakaotalk://send?text={encoded_text}"
            
            kakao_button_html = f"""
            <a href="{kakao_deeplink}" target="_blank" style="text-decoration: none;">
                <button style="
                    background: linear-gradient(135deg, #FEE500 0%, #FFCD00 100%);
                    color: #3C1E1E;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 20px;
                    font-size: 0.95rem;
                    font-weight: 700;
                    cursor: pointer;
                    width: 100%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: all 0.2s;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 4px 8px rgba(0,0,0,0.15)';" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.1)';">
                    💬 카톡 공유
                </button>
            </a>
            """
            st.components.v1.html(kakao_button_html, height=60)
        
        with col3:
            st.caption("💡 **복사하기**: 클립보드에 복사 → 카톡에 붙여넣기")
            st.caption("💡 **카톡 공유**: 카카오톡 앱으로 바로 전송 (모바일)")
        
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        
        # 안내 메시지
        st.info("""
        **📱 카카오톡 전송 방법**:
        
        1. **PC에서**: "복사하기" 버튼 클릭 → 카카오톡 PC 버전에서 붙여넣기 (Ctrl+V)
        2. **모바일에서**: "카톡 공유" 버튼 클릭 → 카카오톡 앱에서 대화방 선택
        3. **직접 수정**: 위 텍스트 박스에서 메시지를 수정한 후 복사/공유
        """)


# ══════════════════════════════════════════════════════════════════════════════
# 테스트 코드
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    st.set_page_config(page_title="공유 블록 테스트", layout="wide")
    
    st.title("📱 공유 블록 테스트")
    
    # 테스트용 더미 분석 결과
    test_content = """
    # 의무기록 해석 결과
    
    **진단명**: 요추 추간판 탈출증 (L4-L5, L5-S1)
    
    **주요 소견**:
    - 2개월간 지속된 요통 및 좌측 다리 저림
    - MRI: 경막낭 압박 확인
    - 낙상 사고 병력 있음
    
    **치료 계획**:
    - 현재: 물리치료 + 약물치료
    - 향후: 보존적 치료 실패 시 미세현미경 디스크 제거술 권유
    
    **보험금 청구**:
    - 실손보험: 치료비 전액 청구 가능
    - 후유장해: 수술 후 6개월 시점에 신경학적 장해 평가 필요
    """
    
    render_share_report_block(
        analysis_content=test_content,
        customer_name="홍길동",
        block_title="의무기록 AI 분석 결과"
    )
