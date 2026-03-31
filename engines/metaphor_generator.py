# -*- coding: utf-8 -*-
"""
은유적 후킹 언어 생성기 (Metaphor Generator)
에이전틱 AI 비서 - 기술 용어를 전략적 은유로 변환

작성일: 2026-03-31
버전: 1.0
목적: 딱딱한 기술 용어에 비유적 갈고리(Hook)를 걸어 전략적 언어로 변환
"""

from typing import Dict, List, Optional, Tuple
import re


class MetaphorGenerator:
    """
    은유적 후킹 언어 생성기
    - 기술 용어 → 전략적 은유 자동 변환
    - 숫자 출력 시 위험성 은유 자동 삽입
    - 에이전틱 AI 비서 톤앤매너 적용
    """
    
    # 표준 은유 사전
    METAPHOR_DICTIONARY = {
        # 보험 핵심 개념
        "인플레이션": "자산의 가치를 갉아먹는 보이지 않는 좀벌레",
        "물가상승": "자산의 가치를 갉아먹는 보이지 않는 좀벌레",
        "일부보험": "사고 시점에 작동하지 않는 반쪽짜리 브레이크",
        "비례보상": "절반만 작동하는 에어백",
        "가업승계": "가문의 유산을 보존하는 성벽",
        "상속": "가문의 재산을 삼키는 거대한 세금 괴물",
        "상속세": "가문의 재산을 삼키는 거대한 세금 괴물",
        
        # 보장 관련
        "보장공백": "당신의 방패에 뚫린 구멍",
        "보장부족": "당신의 방패에 뚫린 구멍",
        "갭": "당신의 방패에 뚫린 구멍",
        
        # 자동차보험
        "할증": "보험료라는 세금이 폭등하는 지뢰밭",
        "환입": "지뢰를 제거하는 유일한 해체 도구",
        "페이백": "지뢰를 제거하는 유일한 해체 도구",
        "사고건수": "보험료 폭등 지뢰밭을 걷는 발걸음",
        
        # 화재보험
        "재조달가액": "불타버린 집을 다시 지을 수 있는 실탄",
        "보험가액": "불타버린 집을 다시 지을 수 있는 실탄",
        "실화책임": "이웃 공장의 불씨가 당신의 재산을 태우는 리스크",
        
        # 경제적 리스크
        "소득공백": "가족의 생계를 위협하는 블랙홀",
        "소득대체": "가족의 생계를 위협하는 블랙홀을 메우는 안전망",
        "연금공백": "60세부터 65세까지의 무방비 지대",
        "브릿지": "60세부터 65세까지의 무방비 지대를 건너는 다리",
        
        # 의료 관련
        "경상환자": "보험사가 던져주는 반쪽짜리 밧줄",
        "치료비본인부담": "보험사가 던져주는 반쪽짜리 밧줄",
        "실손보험": "의료비라는 폭탄을 막아주는 방탄복",
        
        # 법인 관련
        "법인세": "기업의 이익을 삼키는 세금 괴물",
        "손금산입": "세금 괴물의 입을 줄이는 합법적 무기",
        "감자플랜": "유가족에게 현금을 쥐여주는 비밀 통로",
        "퇴직금": "법인에서 세금 없이 내 노후자금을 꺼내는 합법적 출구"
    }
    
    # 숫자 위험성 은유 템플릿
    NUMERIC_RISK_TEMPLATES = {
        "보장액_부족": "{amount:,}원은 물가 상승이라는 좀벌레가 {years}년간 갉아먹으면 실질 가치 {real_value:,}원으로 추락합니다.",
        "재조달가액_증가": "{years}년 후 재조달가액은 {future_value:,}원으로 폭등하지만, 현재 {current_value:,}원 가입은 반쪽짜리 브레이크입니다.",
        "사고점수_위험": "사고 점수 {score}점은 등급 {grade_drop}단계 하락이라는 지뢰를 밟는 것입니다.",
        "건수_위험": "{count}건의 사고는 보험료 폭등 지뢰밭에서 {count}번째 발걸음입니다.",
        "소득공백_위험": "연 소득 {income:,}원이 {years}년간 사라지면 총 {total_loss:,}원이라는 블랙홀이 가족을 삼킵니다.",
        "상속세_위험": "상속 재산 {asset:,}원에 대한 상속세 {tax:,}원은 가문의 재산을 삼키는 세금 괴물입니다."
    }
    
    # 전략적 프레임 템플릿
    STRATEGIC_FRAMES = {
        "위기상황": "⚠️ 현재 당신의 고객은 {situation}라는 {metaphor} 앞에 서 있습니다.",
        "대안제시": "내가 제안하는 {solution}은 {metaphor}를 넘을 수 있는 유일한 {tool}입니다.",
        "행동촉구": "당신은 이 {tool}를 사용해 고객을 {risk}에서 구출하십시오.",
        "경고": "⚠️ 이대로라면 {consequence}입니다. {action}하십시오."
    }
    
    def __init__(self):
        """초기화"""
        pass
    
    def add_metaphor(self, text: str, keyword: str) -> str:
        """
        기술 용어에 은유 추가
        
        Args:
            text: 원본 텍스트
            keyword: 은유를 추가할 키워드
        
        Returns:
            str: 은유가 추가된 텍스트
        """
        metaphor = self.METAPHOR_DICTIONARY.get(keyword)
        if not metaphor:
            return text
        
        # 키워드 뒤에 은유 추가
        pattern = re.compile(f"({keyword})", re.IGNORECASE)
        replacement = f"\\1({metaphor})"
        
        return pattern.sub(replacement, text, count=1)
    
    def generate_numeric_risk_metaphor(
        self,
        risk_type: str,
        **kwargs
    ) -> str:
        """
        숫자 위험성 은유 생성
        
        Args:
            risk_type: 위험 유형 (보장액_부족, 재조달가액_증가 등)
            **kwargs: 템플릿에 필요한 변수들
        
        Returns:
            str: 은유적 위험성 설명
        """
        template = self.NUMERIC_RISK_TEMPLATES.get(risk_type)
        if not template:
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError:
            return ""
    
    def create_strategic_frame(
        self,
        frame_type: str,
        **kwargs
    ) -> str:
        """
        전략적 프레임 생성
        
        Args:
            frame_type: 프레임 유형 (위기상황, 대안제시, 행동촉구, 경고)
            **kwargs: 템플릿에 필요한 변수들
        
        Returns:
            str: 전략적 프레임 문장
        """
        template = self.STRATEGIC_FRAMES.get(frame_type)
        if not template:
            return ""
        
        try:
            return template.format(**kwargs)
        except KeyError:
            return ""
    
    def convert_passive_to_active(self, text: str) -> str:
        """
        수동태를 능동태로 변환
        
        Args:
            text: 원본 텍스트
        
        Returns:
            str: 능동태로 변환된 텍스트
        """
        # 수동태 패턴 → 능동태 변환
        conversions = {
            "분석되었습니다": "내가 분석한 결과",
            "권장됩니다": "당신은 이것을 실행해야 합니다",
            "제안합니다": "당신은 이 카드를 꺼내야 합니다",
            "예상됩니다": "내가 예측한 바로는",
            "발견되었습니다": "내가 발견했습니다",
            "확인되었습니다": "내가 확인했습니다"
        }
        
        for passive, active in conversions.items():
            text = text.replace(passive, active)
        
        return text
    
    def generate_crisis_scenarios(
        self,
        customer_context: Dict
    ) -> List[Dict]:
        """
        3가지 위기 시나리오 자동 생성
        
        Args:
            customer_context: 고객 컨텍스트 정보
        
        Returns:
            list: 3가지 위기 시나리오
        """
        scenarios = [
            {
                "type": "최악의 경우 (Worst Case)",
                "icon": "🔴",
                "description": "현재 상태 유지 시 발생할 최대 손실",
                "template": "{risk}가 발생하면 {loss}라는 재앙이 가족을 덮칩니다."
            },
            {
                "type": "현실적 위험 (Realistic Risk)",
                "icon": "⚠️",
                "description": "통계적으로 가장 발생 가능성 높은 리스크",
                "template": "통계청 데이터 기준, {probability}% 확률로 {risk}가 발생합니다."
            },
            {
                "type": "기회 상실 (Opportunity Loss)",
                "icon": "💸",
                "description": "지금 행동하지 않으면 놓치는 혜택",
                "template": "지금 결정하지 않으면 {benefit}를 영원히 놓칩니다."
            }
        ]
        
        return scenarios
    
    def apply_agentic_tone(self, text: str) -> str:
        """
        에이전틱 AI 비서 톤앤매너 적용
        
        Args:
            text: 원본 텍스트
        
        Returns:
            str: 에이전틱 톤이 적용된 텍스트
        """
        # 1. 수동태 → 능동태
        text = self.convert_passive_to_active(text)
        
        # 2. 3인칭 → 1·2인칭
        third_person_conversions = {
            "고객은": "당신의 고객은",
            "설계사는": "당신은",
            "보험사는": "보험사라는 적은",
            "통계에 따르면": "내가 분석한 통계에 따르면",
            "데이터에 따르면": "내가 수집한 데이터에 따르면"
        }
        
        for third, first_second in third_person_conversions.items():
            text = text.replace(third, first_second)
        
        # 3. 방관자적 표현 → 전략적 표현
        observer_to_strategic = {
            "참고하시기 바랍니다": "이것을 무기로 사용하십시오",
            "고려해보세요": "즉시 실행하십시오",
            "도움이 될 것입니다": "승리를 보장합니다",
            "유용합니다": "당신의 무기가 됩니다"
        }
        
        for observer, strategic in observer_to_strategic.items():
            text = text.replace(observer, strategic)
        
        return text
    
    def generate_secretary_briefing_header(
        self,
        customer_name: str,
        risk_summary: str,
        strategy_summary: str
    ) -> str:
        """
        AI 비서 브리핑 헤더 생성
        
        Args:
            customer_name: 고객명
            risk_summary: 리스크 요약
            strategy_summary: 전략 요약
        
        Returns:
            str: 마크다운 형식 브리핑 헤더
        """
        return f"""
🤖 **[AI 비서의 한마디]**

대표님, {customer_name}님 분석을 완료했습니다.

⚠️ **위험 상황**:  
{risk_summary}

🛡️ **권장 전략**:  
{strategy_summary}

당신은 이 전략을 사용해 고객을 리스크에서 구출하십시오.
"""
    
    def add_legal_citation_footer(
        self,
        sources: List[str]
    ) -> str:
        """
        법적 근거 및 데이터 출처 푸터 생성
        
        Args:
            sources: 출처 리스트
        
        Returns:
            str: 마크다운 형식 푸터
        """
        footer = "\n---\n\n📚 **법적 근거 및 데이터 출처**\n\n"
        
        for source in sources:
            footer += f"- {source}\n"
        
        footer += "\n* 본 보고서는 AI 비서가 최신 법령 및 통계를 기반으로 작성하였으며, 법적 효력이 없는 참고 자료입니다.\n"
        
        return footer
    
    def enhance_number_with_metaphor(
        self,
        number: float,
        context: str,
        unit: str = "원"
    ) -> str:
        """
        숫자에 은유적 설명 추가
        
        Args:
            number: 숫자
            context: 컨텍스트 (보장액, 재조달가액 등)
            unit: 단위
        
        Returns:
            str: 은유가 추가된 숫자 표현
        """
        formatted_number = f"{number:,.0f}{unit}"
        
        # 컨텍스트별 은유 추가
        if "보장액" in context or "가입금액" in context:
            if number < 50000000:  # 5천만원 미만
                metaphor = " (물가 상승이라는 좀벌레가 갉아먹으면 실질 가치 급락)"
            else:
                metaphor = " (현재는 충분하지만 5년 후 좀벌레의 공격 대비 필요)"
        elif "재조달가액" in context:
            metaphor = " (불타버린 집을 다시 지을 수 있는 실탄)"
        elif "상속세" in context:
            metaphor = " (가문의 재산을 삼키는 세금 괴물)"
        elif "소득" in context:
            metaphor = " (가족 생계의 생명줄)"
        else:
            metaphor = ""
        
        return formatted_number + metaphor
    
    def convert_to_strategic_language(
        self,
        original_report: str,
        customer_name: str = "",
        add_briefing: bool = True
    ) -> str:
        """
        기존 리포트를 전략적 언어로 전면 변환
        
        Args:
            original_report: 원본 리포트
            customer_name: 고객명
            add_briefing: 브리핑 헤더 추가 여부
        
        Returns:
            str: 전략적 언어로 변환된 리포트
        """
        # 1. 에이전틱 톤 적용
        report = self.apply_agentic_tone(original_report)
        
        # 2. 주요 키워드에 은유 추가
        for keyword in self.METAPHOR_DICTIONARY.keys():
            if keyword in report:
                report = self.add_metaphor(report, keyword)
        
        # 3. 브리핑 헤더 추가 (옵션)
        if add_briefing and customer_name:
            # 리스크와 전략 자동 추출 (간단한 휴리스틱)
            risk_keywords = ["위험", "리스크", "공백", "부족"]
            strategy_keywords = ["제안", "권장", "전략", "플랜"]
            
            risk_summary = "분석 중 발견된 리스크를 확인하십시오"
            strategy_summary = "아래 전략을 즉시 실행하십시오"
            
            briefing = self.generate_secretary_briefing_header(
                customer_name,
                risk_summary,
                strategy_summary
            )
            
            report = briefing + "\n\n" + report
        
        return report


# 전역 인스턴스 (싱글톤 패턴)
_metaphor_generator_instance = None

def get_metaphor_generator() -> MetaphorGenerator:
    """
    MetaphorGenerator 싱글톤 인스턴스 반환
    
    Returns:
        MetaphorGenerator: 전역 인스턴스
    """
    global _metaphor_generator_instance
    if _metaphor_generator_instance is None:
        _metaphor_generator_instance = MetaphorGenerator()
    return _metaphor_generator_instance
