# ══════════════════════════════════════════════════════════════════════════════
# [BLOCK] total_loss_simulator.py
# 자동차 전손/미수선 시뮬레이터 - 최적 전략 분석 및 준비서류 안내
# ══════════════════════════════════════════════════════════════════════════════

from __future__ import annotations
import streamlit as st
import os
from typing import Dict, Optional
import google.generativeai as genai


def calculate_total_loss_strategy(
    vehicle_value: int,
    repair_cost: int,
    salvage_value: int
) -> Dict:
    """
    전손/미수선 전략 계산
    
    Args:
        vehicle_value: 차량 가액 (원)
        repair_cost: 예상 수리비 (원)
        salvage_value: 잔존물 예상 매각가 (원)
    
    Returns:
        {
            "case_type": str,  # "absolute_total_loss", "constructive_total_loss", "economic_total_loss", "repair_recommended"
            "repair_ratio": float,  # 수리비 비율 (%)
            "total_loss_amount": int,  # 전손 시 수령액
            "unrepaired_amount": int,  # 미수선 시 수령액 (보험금 + 매각가)
            "unrepaired_insurance": int,  # 미수선 보험금 (수리비의 80%)
            "salvage_negotiation_amount": int,  # 잔존물 차주 보유 협의 시 수령액
            "recommended_strategy": str,  # 추천 전략
            "profit_difference": int,  # 최대 수익 차액
            "case_description": str,  # 케이스 설명
            "negotiation_difficulty": str,  # 협의 난이도
            "action_steps": list  # 실행 단계
        }
    """
    
    # 수리비 비율 계산
    repair_ratio = (repair_cost / vehicle_value * 100) if vehicle_value > 0 else 0
    
    # 전손 시 수령액
    total_loss_amount = vehicle_value
    
    # 미수선 시 수령액 (수리비의 80% + 차량 매각가)
    unrepaired_insurance = int(repair_cost * 0.8)
    unrepaired_amount = unrepaired_insurance + salvage_value
    
    # 잔존물 차주 보유 협의 시 수령액 (차량 가액 - 잔존물 가치 + 실제 매각가)
    # 실제 매각가는 잔존물 가치보다 높을 수 있다고 가정 (20% 추가)
    estimated_actual_salvage = int(salvage_value * 1.2)
    salvage_negotiation_amount = (vehicle_value - salvage_value) + estimated_actual_salvage
    
    # 케이스 판별
    if repair_cost > vehicle_value:
        # 추정전손
        case_type = "constructive_total_loss"
        case_description = "🔴 **추정 전손 대상**입니다. 수리비가 차량 가액을 초과하여 자동으로 전손 처리됩니다."
        negotiation_difficulty = "협의 불필요 (자동 전손)"
        
        # 미수선이 더 유리한지 확인
        if unrepaired_amount > total_loss_amount:
            recommended_strategy = "미수선 + 매각"
            profit_difference = unrepaired_amount - total_loss_amount
            action_steps = [
                "1️⃣ 보험사에 '미수선 처리' 의사 통보",
                "2️⃣ 미수선 보험금(수리비의 80%) 수령",
                "3️⃣ 사고 차량을 중고차 시장에 매각",
                f"4️⃣ 총 수령액: {unrepaired_amount:,}원 (전손 대비 +{profit_difference:,}원)"
            ]
        else:
            recommended_strategy = "전손 처리"
            profit_difference = 0
            action_steps = [
                "1️⃣ 보험사에 전손 처리 동의",
                "2️⃣ 차량 가액 100% 수령",
                "3️⃣ 잔존물 소유권을 보험사에 양도",
                f"4️⃣ 총 수령액: {total_loss_amount:,}원"
            ]
    
    elif repair_ratio >= 80:
        # 임의전손 협의 가능 (높은 확률)
        case_type = "economic_total_loss"
        case_description = f"🟠 **임의 전손 협의 가능 구간**입니다. (수리비 {repair_ratio:.1f}%) 보험사 설득이 비교적 용이합니다."
        negotiation_difficulty = "협의 가능성 높음"
        
        # 3가지 전략 비교
        strategies = {
            "전손 처리": total_loss_amount,
            "미수선 + 매각": unrepaired_amount,
            "잔존물 차주 보유 협의": salvage_negotiation_amount
        }
        
        recommended_strategy = max(strategies, key=strategies.get)
        max_amount = strategies[recommended_strategy]
        profit_difference = max_amount - total_loss_amount
        
        if recommended_strategy == "잔존물 차주 보유 협의":
            action_steps = [
                "1️⃣ 보험사에 '잔존물 차주 보유 + 차액 정산' 제안",
                "2️⃣ 제3자 감정평가로 잔존물 가치 산정",
                f"3️⃣ 보험금 수령: {vehicle_value - salvage_value:,}원",
                f"4️⃣ 잔존물 직접 매각: 약 {estimated_actual_salvage:,}원",
                f"5️⃣ 총 수령액: {salvage_negotiation_amount:,}원 (전손 대비 +{profit_difference:,}원)"
            ]
        elif recommended_strategy == "미수선 + 매각":
            action_steps = [
                "1️⃣ 보험사에 '미수선 처리' 의사 통보",
                f"2️⃣ 미수선 보험금 수령: {unrepaired_insurance:,}원",
                f"3️⃣ 사고 차량 매각: 약 {salvage_value:,}원",
                f"4️⃣ 총 수령액: {unrepaired_amount:,}원 (전손 대비 +{profit_difference:,}원)"
            ]
        else:
            action_steps = [
                "1️⃣ 보험사에 전손 처리 협의 요청",
                "2️⃣ '수리 후 차량 가치 하락' 강조",
                "3️⃣ '대차료 장기 부담' 강조",
                f"4️⃣ 총 수령액: {total_loss_amount:,}원"
            ]
    
    elif repair_ratio >= 60:
        # 임의전손 협의 가능 (보통)
        case_type = "economic_total_loss"
        case_description = f"🟡 **임의 전손 협의 가능 구간**입니다. (수리비 {repair_ratio:.1f}%) 보험사 설득이 필요합니다."
        negotiation_difficulty = "협의 가능성 보통"
        
        # 미수선이 가장 확실한 전략
        if unrepaired_amount > total_loss_amount:
            recommended_strategy = "미수선 + 매각"
            profit_difference = unrepaired_amount - total_loss_amount
            action_steps = [
                "1️⃣ 보험사에 '미수선 처리' 의사 통보 (전손 협의보다 확실)",
                f"2️⃣ 미수선 보험금 수령: {unrepaired_insurance:,}원",
                f"3️⃣ 사고 차량 매각: 약 {salvage_value:,}원",
                f"4️⃣ 총 수령액: {unrepaired_amount:,}원 (전손 대비 +{profit_difference:,}원)"
            ]
        else:
            recommended_strategy = "전손 협의 시도"
            profit_difference = 0
            action_steps = [
                "1️⃣ 보험사에 전손 처리 협의 요청",
                "2️⃣ '잔존물 매각으로 보험사 손해 감소' 강조",
                "3️⃣ 협의 실패 시 미수선 처리로 전환",
                f"4️⃣ 전손 성공 시 수령액: {total_loss_amount:,}원"
            ]
    
    else:
        # 수리 권장
        case_type = "repair_recommended"
        case_description = f"🟢 **수리 후 사용 권장**입니다. (수리비 {repair_ratio:.1f}%) 전손 협의가 어렵습니다."
        negotiation_difficulty = "협의 어려움"
        
        if unrepaired_amount > vehicle_value * 0.7:  # 미수선이 차량 가액의 70% 이상이면 고려
            recommended_strategy = "미수선 + 매각"
            profit_difference = unrepaired_amount - int(vehicle_value * 0.7)
            action_steps = [
                "1️⃣ 보험사에 '미수선 처리' 의사 통보",
                f"2️⃣ 미수선 보험금 수령: {unrepaired_insurance:,}원",
                f"3️⃣ 사고 차량 매각: 약 {salvage_value:,}원",
                f"4️⃣ 총 수령액: {unrepaired_amount:,}원"
            ]
        else:
            recommended_strategy = "수리 후 사용"
            profit_difference = 0
            action_steps = [
                "1️⃣ 수리비 100% 보험 처리",
                "2️⃣ 수리 완료 후 차량 계속 사용",
                "3️⃣ 격락손해금 청구 검토 (차량 연식 3년 이내)",
                f"4️⃣ 수리비: {repair_cost:,}원"
            ]
    
    return {
        "case_type": case_type,
        "repair_ratio": repair_ratio,
        "total_loss_amount": total_loss_amount,
        "unrepaired_amount": unrepaired_amount,
        "unrepaired_insurance": unrepaired_insurance,
        "salvage_negotiation_amount": salvage_negotiation_amount,
        "recommended_strategy": recommended_strategy,
        "profit_difference": profit_difference,
        "case_description": case_description,
        "negotiation_difficulty": negotiation_difficulty,
        "action_steps": action_steps
    }


def get_required_documents(owner_type: str) -> Dict:
    """
    차주 유형별 준비서류 반환
    
    Args:
        owner_type: "individual", "sole_proprietor", "corporation"
    
    Returns:
        {
            "required": list,  # 필수 서류
            "optional": list,  # 선택 서류
            "critical_notes": list  # 중요 주의사항
        }
    """
    
    if owner_type == "individual":
        return {
            "required": [
                "📄 자동차 매도용 인감증명서 (발급일로부터 3개월 이내)",
                "📄 자동차등록증 원본",
                "📄 신분증 사본 (주민등록증 또는 운전면허증)",
                "📄 통장 사본 (보험금 입금 계좌)"
            ],
            "optional": [
                "📄 압류/저당 해지 서류 (해당 시)",
                "📄 자동차세 완납 증명서 (해당 시)"
            ],
            "critical_notes": [
                "⚠️ **인감증명서 매수인 정보 기재 필수**: 보험사명, 사업자등록번호 반드시 기재",
                "⚠️ 용도: '자동차 매도용'으로 명시",
                "⚠️ 백지 인감증명서는 보험사 접수 거부"
            ]
        }
    
    elif owner_type == "sole_proprietor":
        return {
            "required": [
                "📄 자동차 매도용 인감증명서 (사업자 인감 사용)",
                "📄 사업자등록증 사본",
                "📄 자동차등록증 원본",
                "📄 대표자 신분증 사본",
                "📄 사업자 통장 사본"
            ],
            "optional": [
                "📄 사업자 폐업 시 폐업 사실 증명서",
                "📄 압류/저당 해지 서류 (해당 시)"
            ],
            "critical_notes": [
                "⚠️ **인감증명서 매수인 정보 기재 필수**: 보험사명, 사업자등록번호 반드시 기재",
                "⚠️ 사업자 인감 사용 필수",
                "⚠️ 용도: '자동차 매도용'으로 명시"
            ]
        }
    
    else:  # corporation
        return {
            "required": [
                "📄 자동차 매도용 법인 인감증명서 (발급일로부터 3개월 이내)",
                "📄 법인 인감도장 날인된 위임장 (보험사 양식)",
                "📄 법인등기부등본 (발급일로부터 3개월 이내)",
                "📄 사업자등록증 사본",
                "📄 자동차등록증 원본",
                "📄 대표이사 신분증 사본",
                "📄 법인 통장 사본"
            ],
            "optional": [
                "📄 이사회 결의서 (고가 차량 또는 내규 상 필요 시)",
                "📄 압류/저당 해지 서류 (해당 시)"
            ],
            "critical_notes": [
                "⚠️ **인감증명서 매수인 정보 기재 필수**: 보험사명, 사업자등록번호 반드시 기재",
                "⚠️ 법인 인감도장 날인 필수",
                "⚠️ 법인등기부등본 유효기간 확인 (3개월 이내)"
            ]
        }


def generate_kakao_guide(
    customer_name: str,
    strategy_result: Dict,
    documents: Dict,
    gemini_api_key: str
) -> str:
    """
    고객용 전손 가이드 카카오톡 메시지 생성
    
    Args:
        customer_name: 고객 이름
        strategy_result: 전략 계산 결과
        documents: 준비서류
        gemini_api_key: Gemini API 키
    
    Returns:
        카카오톡 메시지 형식의 가이드
    """
    
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
당신은 친절한 자동차 보험 전문 설계사입니다. 고객에게 **전손 처리 가이드**를 카카오톡으로 보낼 메시지로 작성하세요.

**고객 정보**:
- 고객명: {customer_name}

**분석 결과**:
- 케이스: {strategy_result['case_description']}
- 수리비 비율: {strategy_result['repair_ratio']:.1f}%
- 추천 전략: {strategy_result['recommended_strategy']}
- 최대 수령 예상액: {strategy_result['unrepaired_amount']:,}원

**실행 단계**:
{chr(10).join(strategy_result['action_steps'])}

**준비 서류**:
필수:
{chr(10).join(documents['required'])}

선택 (해당 시):
{chr(10).join(documents['optional'])}

**중요 주의사항**:
{chr(10).join(documents['critical_notes'])}

**요구사항**:
1. 친절하고 전문적인 말투 사용 (~요, ~습니다)
2. 이모지 적절히 사용 (🚗, 💰, 📄, ⚠️, ✅ 등)
3. 카카오톡 메시지 길이에 맞게 간결하게 (최대 800자)
4. 전문 용어는 쉽게 풀어서 설명
5. 인사말과 마무리 인사 포함
6. **인감증명서 매수인 정보 기재**를 빨간색으로 강조 (⚠️ 사용)

**출력 형식**:
🚗 [전손 처리 가이드]

안녕하세요, {customer_name}님.

[분석 결과 요약]
[추천 전략 및 예상 수령액]

📋 **실행 단계**
[단계별 안내]

📄 **준비 서류**
[필수 서류 리스트]

⚠️ **반드시 확인하세요!**
[중요 주의사항 - 특히 인감증명서 매수인 정보 기재 강조]

궁금하신 점 있으시면 언제든 연락 주세요!
"""
        
        response = model.generate_content(prompt)
        return response.text.strip()
    
    except Exception as e:
        return f"❌ 가이드 생성 실패: {e}\n\n수동으로 작성하시거나 다시 시도해 주세요."


def render_total_loss_simulator_block(
    customer_name: str = "고객",
    key_prefix: str = "total_loss_sim"
) -> None:
    """
    전손/미수선 시뮬레이터 UI 블록
    
    Args:
        customer_name: 고객 이름
        key_prefix: 세션 키 접두사
    """
    
    st.markdown("""
    <div style='background:linear-gradient(135deg,#fef3c7 0%,#fde68a 50%,#fcd34d 100%);
      border-radius:14px;padding:18px 22px 14px 22px;margin-bottom:16px;border-left:4px solid #f59e0b;'>
      <div style='color:#92400e;font-size:1.15rem;font-weight:900;letter-spacing:0.04em;'>
    🚗 전손/미수선 시뮬레이터
      </div>
      <div style='color:#78350f;font-size:0.80rem;margin-top:5px;'>
    차량 가액과 수리비를 입력하면 최적의 전략을 AI가 분석합니다
      </div>
    </div>""", unsafe_allow_html=True)
    
    # 세션 초기화
    if f"{key_prefix}_result" not in st.session_state:
        st.session_state[f"{key_prefix}_result"] = None
    if f"{key_prefix}_owner_type" not in st.session_state:
        st.session_state[f"{key_prefix}_owner_type"] = "individual"
    if f"{key_prefix}_kakao_guide" not in st.session_state:
        st.session_state[f"{key_prefix}_kakao_guide"] = ""
    
    # 입력 섹션
    st.markdown("### 📊 차량 정보 입력")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        vehicle_value = st.number_input(
            "차량 가액 (원)",
            min_value=0,
            max_value=500_000_000,
            value=20_000_000,
            step=1_000_000,
            key=f"{key_prefix}_vehicle_value",
            help="보험사가 산정한 차량의 시가"
        )
    
    with col2:
        repair_cost = st.number_input(
            "예상 수리비 (원)",
            min_value=0,
            max_value=500_000_000,
            value=16_000_000,
            step=500_000,
            key=f"{key_prefix}_repair_cost",
            help="정비업체에서 견적받은 수리비"
        )
    
    with col3:
        salvage_value = st.number_input(
            "잔존물 예상 매각가 (원)",
            min_value=0,
            max_value=500_000_000,
            value=8_000_000,
            step=500_000,
            key=f"{key_prefix}_salvage_value",
            help="사고 차량을 중고차 시장에 매각할 경우 예상 가격"
        )
    
    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
    
    # 계산 버튼
    if st.button(
        "🔍 최적 전략 분석",
        type="primary",
        use_container_width=True,
        key=f"{key_prefix}_calculate_btn"
    ):
        if vehicle_value == 0:
            st.error("❌ 차량 가액을 입력해 주세요.")
        elif repair_cost == 0:
            st.error("❌ 예상 수리비를 입력해 주세요.")
        else:
            with st.spinner("🤖 AI가 최적의 전략을 분석하고 있습니다..."):
                result = calculate_total_loss_strategy(
                    vehicle_value=vehicle_value,
                    repair_cost=repair_cost,
                    salvage_value=salvage_value
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
        st.markdown("### 💰 전략별 수령액 비교")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="전손 처리",
                value=f"{result['total_loss_amount']:,}원",
                delta=None if result['recommended_strategy'] == "전손 처리" else None
            )
            if result['recommended_strategy'] == "전손 처리":
                st.success("✅ 추천 전략")
        
        with col2:
            st.metric(
                label="미수선 + 매각",
                value=f"{result['unrepaired_amount']:,}원",
                delta=f"+{result['unrepaired_amount'] - result['total_loss_amount']:,}원" if result['unrepaired_amount'] > result['total_loss_amount'] else None
            )
            if result['recommended_strategy'] == "미수선 + 매각":
                st.success("✅ 추천 전략")
        
        with col3:
            st.metric(
                label="잔존물 차주 보유 협의",
                value=f"{result['salvage_negotiation_amount']:,}원",
                delta=f"+{result['salvage_negotiation_amount'] - result['total_loss_amount']:,}원" if result['salvage_negotiation_amount'] > result['total_loss_amount'] else None
            )
            if result['recommended_strategy'] == "잔존물 차주 보유 협의":
                st.success("✅ 추천 전략")
        
        st.markdown("<div style='margin-bottom:16px;'></div>", unsafe_allow_html=True)
        
        # 추천 전략
        st.markdown("### 🎯 추천 전략")
        st.info(f"**{result['recommended_strategy']}** (협의 난이도: {result['negotiation_difficulty']})")
        
        if result['profit_difference'] > 0:
            st.success(f"💡 이 전략을 선택하면 전손 대비 **+{result['profit_difference']:,}원** 더 받을 수 있습니다!")
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # 실행 단계
        st.markdown("### 📝 실행 단계")
        for step in result['action_steps']:
            st.markdown(f"- {step}")
        
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:20px 0;'>", unsafe_allow_html=True)
        
        # 준비서류 안내
        st.markdown("### 📄 전손 처리 준비서류 안내")
        
        owner_type = st.radio(
            "차주 유형을 선택하세요",
            options=["individual", "sole_proprietor", "corporation"],
            format_func=lambda x: {
                "individual": "👤 개인",
                "sole_proprietor": "💼 개인사업자",
                "corporation": "🏢 법인"
            }[x],
            key=f"{key_prefix}_owner_type_radio",
            horizontal=True
        )
        
        st.session_state[f"{key_prefix}_owner_type"] = owner_type
        
        documents = get_required_documents(owner_type)
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # 필수 서류
        st.markdown("#### ✅ 필수 서류")
        for doc in documents['required']:
            st.markdown(f"- {doc}")
        
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        
        # 선택 서류
        st.markdown("#### 📋 선택 서류 (해당 시)")
        for doc in documents['optional']:
            st.markdown(f"- {doc}")
        
        st.markdown("<div style='margin-bottom:8px;'></div>", unsafe_allow_html=True)
        
        # 중요 주의사항
        st.markdown("#### ⚠️ 반드시 확인하세요!")
        for note in documents['critical_notes']:
            st.error(note)
        
        st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
        
        # 체크리스트
        st.markdown("#### ✔️ 전손 처리 전 체크리스트")
        
        checklist = [
            "인감증명서 유효기간 확인 (3개월 이내)",
            "매수인 정보 기재 여부 확인 (빨간색 강조)",
            "자동차등록증 원본 여부 확인",
            "압류/저당 해지 여부 확인",
            "하이패스 카드 회수 여부 확인",
            "개인 소지품 회수 여부 확인 (블랙박스 SD 카드 포함)",
            "보험료 환급 신청 여부 확인"
        ]
        
        for item in checklist:
            st.checkbox(item, key=f"{key_prefix}_checklist_{item}")
        
        st.markdown("<hr style='border:none;border-top:1px solid #e2e8f0;margin:20px 0;'>", unsafe_allow_html=True)
        
        # 고객용 가이드 발송
        st.markdown("### 📱 고객용 가이드 발송")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button(
                "✨ 카톡 가이드 생성",
                type="primary",
                use_container_width=True,
                key=f"{key_prefix}_generate_kakao_btn"
            ):
                with st.spinner("🤖 Gemini가 고객용 가이드를 작성하고 있습니다..."):
                    gemini_api_key = os.getenv("GEMINI_API_KEY")
                    
                    if not gemini_api_key:
                        st.error("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
                    else:
                        kakao_guide = generate_kakao_guide(
                            customer_name=customer_name,
                            strategy_result=result,
                            documents=documents,
                            gemini_api_key=gemini_api_key
                        )
                        st.session_state[f"{key_prefix}_kakao_guide"] = kakao_guide
                        st.rerun()
        
        with col2:
            if st.session_state.get(f"{key_prefix}_kakao_guide"):
                if st.button(
                    "📋 클립보드에 복사",
                    use_container_width=True,
                    key=f"{key_prefix}_copy_btn"
                ):
                    st.success("✅ 클립보드에 복사되었습니다! 카카오톡에 붙여넣기 하세요.")
        
        # 생성된 가이드 표시
        kakao_guide = st.session_state.get(f"{key_prefix}_kakao_guide")
        if kakao_guide:
            st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📱 생성된 카카오톡 메시지")
            st.text_area(
                "kakao_guide_preview",
                value=kakao_guide,
                height=400,
                key=f"{key_prefix}_kakao_guide_preview",
                label_visibility="collapsed"
            )
