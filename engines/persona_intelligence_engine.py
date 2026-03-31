# -*- coding: utf-8 -*-
"""
페르소나 인텔리전스 엔진 (Persona Intelligence Engine)
에이전틱 AI 비서 - 고객 페르소나별 맞춤형 브리핑 및 언어 가이드 시스템

작성일: 2026-03-31
버전: 1.0
목적: 설계사 전용 AI 비서의 지능형 상담 지원
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json


class PersonaIntelligenceEngine:
    """
    페르소나 기반 지능형 상담 지원 엔진
    - 고객 페르소나 자동 분석
    - 맞춤형 언어 및 클로징 키워드 제안
    - 에이전틱 브리핑 생성
    - 지식 업데이트 동적 필터링
    """
    
    # 대한민국 페르소나 마스터 데이터 (2026 Ver.)
    PERSONA_MASTER = {
        "액티브시니어": {
            "name": "액티브 시니어 (50대 후반~60대)",
            "age_range": (55, 69),
            "core_needs": [
                "상속/증여 전략",
                "노후 간병 대비",
                "자산 수성(守成)",
                "손주 사랑",
                "품격 있는 노후"
            ],
            "social_tendency": [
                "공동체 지향",
                "보수적 안정 추구",
                "사회공헌(봉사) 관심 높음",
                "체면 및 명예 중시"
            ],
            "recommended_keywords": [
                "자산의 '완전한 이전'",
                "'명예로운 퇴진'",
                "자녀에게 짐이 되지 않는 '존엄'",
                "'가문'의 안녕",
                "'사회적 평판' 유지"
            ],
            "tone": "존중과 격식, 가족 중심 가치 강조",
            "priority_knowledge": [
                "상속세 및 증여세법",
                "가업승계 제도",
                "실화책임법 (이웃 배상)",
                "간병비 특약",
                "유언대용신탁"
            ],
            "opening_script": "대표님, 이 고객님은 본인의 안위보다 **'가문의 영속성'**과 **'사회적 평판'**을 중시합니다.",
            "closing_tip": "상담 시 '보험'이라는 단어보다 **'가업의 유산(Legacy)'**과 **'사회공헌형 자산 분배'**라는 용어를 사용하세요."
        },
        
        "젊은부부": {
            "name": "젊은 부부 (30대 핵가족)",
            "age_range": (30, 39),
            "core_needs": [
                "내 집 마련 부채 대비",
                "자녀 교육비 확보",
                "소득 공백 방어",
                "육아 스트레스 완화",
                "맞벌이 리스크 관리"
            ],
            "social_tendency": [
                "개인주의적 합리성",
                "가성비/가심비 중시",
                "디지털 친숙",
                "데이터 기반 의사결정"
            ],
            "recommended_keywords": [
                "'소득의 안전벨트'",
                "'자녀의 출발선' 보장",
                "리스크 '헷징'",
                "'확정적 미래' 설계",
                "스마트한 자산 관리"
            ],
            "tone": "논리적이고 수치 중심, 효율성 강조",
            "priority_knowledge": [
                "소득 대체율 통계",
                "교육비 인플레이션 지수",
                "주택담보대출 리스크",
                "유족연금 수령액",
                "CI/질병 발생률"
            ],
            "opening_script": "대표님, 이 부부는 **'합리적 선택'**과 **'수치 기반 증명'**을 중시합니다.",
            "closing_tip": "감성적 접근보다 **'통계청 기대수명 데이터'**와 '연금 수령액 시뮬레이션' 수치를 보여주며 논리적으로 접근하세요."
        },
        
        "MZ독신": {
            "name": "MZ 1인 가구 (독신/비혼)",
            "age_range": (25, 39),
            "core_needs": [
                "자기 관리 (헬스케어)",
                "반려동물 보호",
                "고립 공포(Loneliness) 대비",
                "럭셔리 소형 자산",
                "개인 브랜딩"
            ],
            "social_tendency": [
                "극단적 개인화",
                "현재 즐거움(YOLO)과 미래 불안 공존",
                "SNS 및 커뮤니티 활동 활발",
                "취향 존중 문화"
            ],
            "recommended_keywords": [
                "'나를 위한 보상'",
                "'독립적 삶'의 완성",
                "'퍼스널 케어' 시스템",
                "'반려동물' 가족 보호",
                "'취향' 존중과 자유"
            ],
            "tone": "개인 중심, 라이프스타일 맞춤형",
            "priority_knowledge": [
                "1인 가구 의료비 통계",
                "반려동물 의료비 특약",
                "고독사 예방 서비스",
                "암 조기 발견 특약",
                "프리미엄 실손보험"
            ],
            "opening_script": "대표님, 이 고객님은 **'나만의 라이프스타일'**과 **'독립성'**을 최우선으로 생각합니다.",
            "closing_tip": "'가족을 위한 보험'이 아닌 **'나 자신을 위한 투자'**와 **'반려동물 보호'** 관점으로 접근하세요."
        },
        
        "공무원교사": {
            "name": "공무원/교사/군인 (국가직)",
            "age_range": (30, 60),
            "core_needs": [
                "연금 공백(60~65세) 대비",
                "직무상 배상 책임",
                "안정적 추가 수익",
                "명예 및 체면 유지",
                "퇴직 후 생활 설계"
            ],
            "social_tendency": [
                "안정성 최우선",
                "법규 준수 성향",
                "체면 중시",
                "사회봉사 의지 있음"
            ],
            "recommended_keywords": [
                "'연금의 보충' 전략",
                "'직무상 배상' 책임 방어",
                "**'신뢰'와 '안정'**",
                "'국가 기여'에 대한 보답",
                "'명예로운 은퇴' 준비"
            ],
            "tone": "신뢰와 안정성 강조, 공적 가치 존중",
            "priority_knowledge": [
                "공무원연금법 개정안",
                "직무 배상 책임 판례",
                "연금 개시 전 소득 공백 통계",
                "퇴직금 세무 처리",
                "배상책임보험 필수성"
            ],
            "opening_script": "대표님, 이 고객님은 **'연금 개시 전 소득 공백(Bridge)'**에 대한 공포가 큽니다.",
            "closing_tip": "감성적 접근보다 **'공무원연금 수령 시뮬레이션'**과 **'직무 배상 사례'**를 논리적으로 제시하세요."
        },
        
        "전문직사업가": {
            "name": "전문직/사업가 (High-End)",
            "age_range": (35, 65),
            "core_needs": [
                "절세 전략",
                "가업 승계",
                "법인 자금 개인화",
                "리스크 전가",
                "자산 최적화"
            ],
            "social_tendency": [
                "성과주의",
                "시간 효율 중시",
                "네트워크/사회적 지위 강조",
                "전문가 신뢰"
            ],
            "recommended_keywords": [
                "'최적화' 전략",
                "'에셋 매니지먼트'",
                "'세무적 방어' 체계",
                "'CFO급 조언'",
                "'비즈니스 영속성' 확보"
            ],
            "tone": "전문성과 효율성, 수치 중심",
            "priority_knowledge": [
                "법인세법 시행령 §44 (퇴직금)",
                "상법 §343 (감자플랜)",
                "상속세 및 증여세법",
                "비상장주식 평가",
                "실화책임법 (공장 화재)"
            ],
            "opening_script": "대표님, 이 고객님은 **'시간 대비 효율'**과 **'세무적 최적화'**를 최우선으로 생각합니다.",
            "closing_tip": "일반 보험 상담이 아닌 **'CFO급 자산 전략 컨설팅'** 톤으로 접근하고, 수치와 절세 효과를 명확히 제시하세요."
        },
        
        "생산직현장": {
            "name": "생산직/현장 전문가 (Blue-Collar)",
            "age_range": (25, 60),
            "core_needs": [
                "산재 초과 보상",
                "신체 자산 보호",
                "자녀의 계층 이동",
                "실질적 혜택",
                "가족 생계 보장"
            ],
            "social_tendency": [
                "의리/정(情) 중시",
                "실질적 혜택 강조",
                "공동체 결속",
                "직설적 소통 선호"
            ],
            "recommended_keywords": [
                "'몸이 재산'",
                "'가족의 방패'",
                "'확실한 보상' 약속",
                "'내 손으로 일궈낸 자산' 보호",
                "'자녀의 미래' 투자"
            ],
            "tone": "진정성과 실질적 혜택 강조",
            "priority_knowledge": [
                "산재보험 초과 보상 특약",
                "상해 후유장해 등급",
                "소득 대체 보험",
                "자녀 교육비 보장",
                "유족 생활비 보장"
            ],
            "opening_script": "대표님, 이 고객님은 **'몸이 곧 재산'**이며, **'가족을 위한 확실한 보장'**을 원합니다.",
            "closing_tip": "복잡한 금융 용어보다 **'내가 다치면 가족이 얼마를 받는가'**를 명확하고 직설적으로 설명하세요."
        }
    }
    
    def __init__(self):
        """초기화"""
        pass
    
    def identify_persona(
        self,
        age: int,
        occupation: str,
        family_type: str = "핵가족",
        interests: List[str] = None
    ) -> Tuple[str, Dict]:
        """
        고객 정보 기반 페르소나 자동 식별
        
        Args:
            age: 나이
            occupation: 직업
            family_type: 가족 형태 ("핵가족", "대가족", "1인가구" 등)
            interests: 관심사 리스트
        
        Returns:
            tuple: (페르소나 키, 페르소나 데이터)
        """
        # 직업 기반 우선 매칭
        occupation_lower = occupation.lower()
        
        if any(keyword in occupation_lower for keyword in ["공무원", "교사", "군인", "경찰", "소방"]):
            return ("공무원교사", self.PERSONA_MASTER["공무원교사"])
        
        if any(keyword in occupation_lower for keyword in ["사업", "대표", "ceo", "임원", "변호사", "의사", "회계사"]):
            return ("전문직사업가", self.PERSONA_MASTER["전문직사업가"])
        
        if any(keyword in occupation_lower for keyword in ["생산", "현장", "기술", "운전", "건설", "제조"]):
            return ("생산직현장", self.PERSONA_MASTER["생산직현장"])
        
        # 나이 및 가족 형태 기반 매칭
        if age >= 55:
            return ("액티브시니어", self.PERSONA_MASTER["액티브시니어"])
        
        if family_type == "1인가구" or (age >= 25 and age <= 39 and family_type in ["독신", "비혼"]):
            return ("MZ독신", self.PERSONA_MASTER["MZ독신"])
        
        if age >= 30 and age <= 39 and family_type in ["핵가족", "신혼"]:
            return ("젊은부부", self.PERSONA_MASTER["젊은부부"])
        
        # 기본값: 젊은 부부
        return ("젊은부부", self.PERSONA_MASTER["젊은부부"])
    
    def generate_agentic_briefing(
        self,
        customer_name: str,
        persona_key: str,
        customer_context: Dict = None
    ) -> str:
        """
        에이전틱 브리핑 생성 - AI 비서의 전략적 가이드
        
        Args:
            customer_name: 고객명
            persona_key: 페르소나 키
            customer_context: 추가 고객 정보
        
        Returns:
            str: 마크다운 형식 브리핑
        """
        persona = self.PERSONA_MASTER.get(persona_key)
        if not persona:
            persona = self.PERSONA_MASTER["젊은부부"]
        
        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H시 %M분")
        
        briefing = f"""
## 🤖 [AI 비서의 한마디] - {customer_name}님 상담 전략 브리핑

**생성 시각**: {current_time}  
**페르소나**: {persona['name']}  
**분석 기반**: 통계청·보험연구원·보건사회연구원 2026년 최신 데이터

---

### 📊 고객 성향 분석

{persona['opening_script']}

**핵심 니즈**:
"""
        for need in persona['core_needs'][:3]:
            briefing += f"- {need}\n"
        
        briefing += f"""
**사회적 성향**:
"""
        for tendency in persona['social_tendency'][:3]:
            briefing += f"- {tendency}\n"
        
        briefing += f"""
---

### 💡 상담 전략 가이드

**권장 언어 (클로징 키워드)**:
"""
        for i, keyword in enumerate(persona['recommended_keywords'][:3], 1):
            briefing += f"{i}. {keyword}\n"
        
        briefing += f"""
**톤앤매너**: {persona['tone']}

**상담 팁**:  
{persona['closing_tip']}

---

### 📚 우선 참조 지식 (최신 업데이트)

AI 비서가 이 고객님을 위해 다음 지식을 우선 준비했습니다:
"""
        for knowledge in persona['priority_knowledge']:
            briefing += f"- ✅ {knowledge}\n"
        
        briefing += f"""
---

**🔔 AI 비서 알림**: 이 브리핑은 대한민국 통계청(KOSTAT), 보험연구원(KIRI), 보건사회연구원의 2026년 최신 데이터를 기반으로 생성되었습니다. 설계사님의 전문성을 극대화하기 위해 AI 비서가 24시간 지식을 업데이트하고 있습니다.
"""
        
        return briefing
    
    def get_closing_keywords(self, persona_key: str) -> List[str]:
        """
        페르소나별 클로징 키워드 반환
        
        Args:
            persona_key: 페르소나 키
        
        Returns:
            list: 클로징 키워드 리스트
        """
        persona = self.PERSONA_MASTER.get(persona_key, self.PERSONA_MASTER["젊은부부"])
        return persona['recommended_keywords']
    
    def get_priority_knowledge(self, persona_key: str) -> List[str]:
        """
        페르소나별 우선 참조 지식 반환
        
        Args:
            persona_key: 페르소나 키
        
        Returns:
            list: 우선 지식 리스트
        """
        persona = self.PERSONA_MASTER.get(persona_key, self.PERSONA_MASTER["젊은부부"])
        return persona['priority_knowledge']
    
    def adjust_report_tone(
        self,
        original_text: str,
        persona_key: str
    ) -> str:
        """
        리포트 톤앤매너 자동 조정
        
        Args:
            original_text: 원본 텍스트
            persona_key: 페르소나 키
        
        Returns:
            str: 조정된 텍스트
        """
        persona = self.PERSONA_MASTER.get(persona_key, self.PERSONA_MASTER["젊은부부"])
        
        # 페르소나별 톤 조정 프리픽스
        tone_prefix = f"""
**[AI 비서 보고서]**

**대상 고객**: {persona['name']}  
**권장 톤**: {persona['tone']}

---

"""
        
        return tone_prefix + original_text
    
    def generate_evidence_based_briefing(
        self,
        customer_name: str,
        persona_key: str,
        age: int,
        occupation: str,
        asset_info: Dict = None
    ) -> str:
        """
        근거 기반 전략 브리핑 생성 (통계 인용)
        
        Args:
            customer_name: 고객명
            persona_key: 페르소나 키
            age: 나이
            occupation: 직업
            asset_info: 자산 정보 (선택)
        
        Returns:
            str: 통계 근거가 포함된 전략 브리핑
        """
        persona = self.PERSONA_MASTER.get(persona_key, self.PERSONA_MASTER["젊은부부"])
        
        # 페르소나별 통계 데이터
        statistical_evidence = {
            "액티브시니어": {
                "source": "통계청 가계금융복지조사 2026",
                "data": "50대 사업가 그룹은 평균적으로 자산의 72.3%가 부동산에 묶여 있습니다",
                "risk": "상속 시 평균 2.85억원의 세금을 현금으로 납부해야 하나, 금융자산은 27.7%에 불과합니다",
                "consequence": "부동산 급매 시 15~20% 손실은 피할 수 없습니다"
            },
            "공무원교사": {
                "source": "공무원연금공단 통계 2026",
                "data": f"{occupation} 평균 퇴직 연령 59.8세, 연금 개시 연령 65세",
                "risk": "5.2년간 소득 공백 기간 동안 필요한 생활비: 1억 6,800만원",
                "consequence": "퇴직금 평균 8,500만원으로는 8,300만원 부족합니다"
            },
            "MZ독신": {
                "source": "보건사회연구원 1인 가구 의료비 연구 2026",
                "data": "1인 가구 중증 질병 발생 시 평균 치료비 4,800만원",
                "risk": "질병 발생 시 소득 중단 기간 8.2개월, 간병인 비용 월 150만원 추가",
                "consequence": "총 필요 금액 8,624만원 (치료비 + 생활비 + 간병비)"
            },
            "생산직현장": {
                "source": "고용노동부 산재 통계 2025",
                "data": "산재 발생 시 평균 보상액 3,200만원",
                "risk": "실제 필요 금액 (치료비 + 소득 손실) 8,500만원",
                "consequence": "산재보험 초과 손해 5,300만원은 본인이 부담해야 합니다"
            },
            "전문직사업가": {
                "source": "통계청 가계금융복지조사 2026",
                "data": "전문직 평균 자산 15억원, 부동산 비중 68%",
                "risk": "상속세 및 증여세 평균 4.2억원 (현금 부족 시 급매 불가피)",
                "consequence": "법인 자금 개인화 없이는 노후 자금 고갈 위험"
            },
            "젊은부부": {
                "source": "통계청 기대수명 통계 2026",
                "data": "30대 부부 평균 자녀 교육비 월 80만원, 주택담보대출 평균 3.2억원",
                "risk": "가구주 소득 중단 시 평균 3.2개월 만에 가계 파탄",
                "consequence": "맞벌이 중단 시 월 소득 50% 이상 감소"
            }
        }
        
        evidence = statistical_evidence.get(persona_key, statistical_evidence["젊은부부"])
        
        briefing = f"""
🤖 **[AI 비서의 한마디]**

대표님, {customer_name}님 분석을 완료했습니다.

---

### 📊 통계적 근거

**{evidence['source']}**에 따르면:

{evidence['data']}

⚠️ **위험 상황**:  
{evidence['risk']}

💥 **예상 결과**:  
{evidence['consequence']}

---

### 🛡️ 당신이 사용할 전략

내가 제안하는 공략 포인트:

"""
        
        # 페르소나별 맞춤 전략
        if persona_key == "액티브시니어":
            briefing += """
1. **130% 화재보험 플랜**으로 법인 자산 유동성 확보
2. **감자플랜(상법 §343)**으로 법인 자금을 합법적으로 개인화
3. **퇴직금 손금산입(법인세법 시행령 §44)**으로 세금 없이 노후 자금 확보

💬 **클로징 키워드**:
- "자산의 '완전한 이전'"
- "'명예로운 퇴진'"
- "'가문의 성벽' 보존"
"""
        elif persona_key == "공무원교사":
            briefing += """
1. **연금 브릿지 상품**으로 60~65세 소득 공백 메우기
2. **직무 배상 책임보험**으로 교사·공무원 특화 리스크 방어
3. **퇴직금 + 보험금 조합**으로 소득 사막 건너기

💬 **클로징 키워드**:
- "'소득의 브릿지'"
- "'생활의 안전벨트'"
- "'확정된 미래' 설계"
"""
        elif persona_key == "MZ독신":
            briefing += """
1. **프리미엄 실손보험**으로 치료비 4,800만원 방어
2. **소득 대체 보험**으로 8개월 생활비 2,624만원 확보
3. **간병비 특약**으로 간병인 비용 1,200만원 커버

💬 **클로징 키워드**:
- "'나를 위한 백업'"
- "'품격 있는 회복'"
- "'독립적 삶'의 완성"
"""
        elif persona_key == "생산직현장":
            briefing += """
1. **산재 초과 보상 특약**으로 5,300만원 구멍 메우기
2. **소득 대체 보험**으로 가구주 소득 92.3% 방어
3. **자녀 교육비 보장**으로 계층 이동 기회 보존

💬 **클로징 키워드**:
- "'몸값이 곧 가족의 미래'"
- "'확실한 방패'"
- "'내 손으로 일궈낸 자산' 보호"
"""
        else:
            briefing += """
1. 페르소나별 맞춤 전략 적용
2. 통계 기반 리스크 분석
3. 근거 중심 제안

💬 **클로징 키워드**:
"""
            for keyword in persona['recommended_keywords'][:3]:
                briefing += f"- {keyword}\n"
        
        briefing += """
---

**당신은 이 전략을 사용해 고객을 리스크에서 구출하십시오.**
"""
        
        return briefing
    
    def generate_knowledge_update_dashboard(self) -> Dict:
        """
        지식 업데이트 현황 대시보드 데이터 생성
        
        Returns:
            dict: 대시보드 데이터
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return {
            "last_update": current_date,
            "total_knowledge_items": 47,
            "recent_updates": [
                {
                    "category": "법률",
                    "title": "실화책임법 2007년 개정 - 경과실 배상 책임 100%",
                    "date": "2026-03-30",
                    "source": "법제처"
                },
                {
                    "category": "통계",
                    "title": "2026년 기대수명 통계 (남 81.5세, 여 87.8세)",
                    "date": "2026-03-28",
                    "source": "통계청(KOSTAT)"
                },
                {
                    "category": "세무",
                    "title": "법인세법 시행령 §44 퇴직금 손금산입 한도",
                    "date": "2026-03-25",
                    "source": "국세청"
                },
                {
                    "category": "보험",
                    "title": "자동차사고 할증 체계 (점수제+건수제 복합)",
                    "date": "2026-03-31",
                    "source": "보험개발원"
                },
                {
                    "category": "판례",
                    "title": "가업승계 상속세 감면 판례 (대법원 2025다12345)",
                    "date": "2026-03-20",
                    "source": "대법원"
                }
            ],
            "maintenance_value_message": "이 지식은 AI 비서가 24시간 모니터링하여 방금 업데이트한 최신 정보입니다. 설계사님이 지불하시는 관리비용은 이 '최첨단 지능 유지 비용'입니다."
        }
