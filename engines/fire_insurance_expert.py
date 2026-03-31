"""
법인화재보험 전문가 엔진 (Fire Insurance Expert Engine)

[GP-FIRE-130] 130% 플랜 논리 체계 구현
- 실화책임법 개정 지식 기반 리스크 분석
- 물가 상승률 vs 감가율 시뮬레이션
- 비례보상 방어 논리
- CEO 설득 화법 자동 생성
"""

from typing import Dict, List, Tuple, Optional
import math


class FireInsuranceExpert:
    """법인화재보험 전문가 엔진"""
    
    # 경제 지표 상수 (2026년 기준)
    ANNUAL_CONSTRUCTION_INFLATION = 0.08  # 건설공사비 지수(CCI) 상승률 8%
    ANNUAL_WAGE_GROWTH = 0.04             # 인건비 상승률 4%
    ANNUAL_DEPRECIATION_RATE = 0.03       # 연간 감가율 3%
    
    # 만기별 권장 가입 비율
    COVERAGE_RATIO_MAP = {
        1: 1.15,   # 1년 소멸식: 115%
        3: 1.25,   # 3년 장기: 125%
        5: 1.30,   # 5년 장기: 130%
    }
    
    def __init__(self):
        """초기화"""
        pass
    
    def calculate_future_insurance_value(
        self,
        initial_replacement_cost: float,
        years: int,
        inflation_rate: Optional[float] = None,
        depreciation_rate: Optional[float] = None
    ) -> Dict[str, float]:
        """
        미래 시점의 보험가액 계산
        
        Args:
            initial_replacement_cost: 최초 재조달가액 (원)
            years: 경과 연수
            inflation_rate: 연간 물가 상승률 (기본값: CCI 8%)
            depreciation_rate: 연간 감가율 (기본값: 3%)
        
        Returns:
            {
                'future_replacement_cost': 미래 재조달가액,
                'cumulative_depreciation_rate': 누적 감가율,
                'future_insurance_value': 미래 보험가액,
                'insurance_value_ratio': 보험가액 비율 (초기 대비 %)
            }
        """
        if inflation_rate is None:
            inflation_rate = self.ANNUAL_CONSTRUCTION_INFLATION
        if depreciation_rate is None:
            depreciation_rate = self.ANNUAL_DEPRECIATION_RATE
        
        # 미래 재조달가액 (복리)
        future_rc = initial_replacement_cost * math.pow(1 + inflation_rate, years)
        
        # 누적 감가율 (단순 누적)
        cumulative_depreciation = depreciation_rate * years
        
        # 미래 보험가액 = 재조달가액 × (1 - 누적감가율)
        future_iv = future_rc * (1 - cumulative_depreciation)
        
        # 보험가액 비율 (초기 재조달가액 대비 %)
        iv_ratio = (future_iv / initial_replacement_cost) * 100
        
        return {
            'future_replacement_cost': future_rc,
            'cumulative_depreciation_rate': cumulative_depreciation,
            'future_insurance_value': future_iv,
            'insurance_value_ratio': iv_ratio
        }
    
    def simulate_multi_year(
        self,
        initial_replacement_cost: float,
        max_years: int = 5
    ) -> List[Dict]:
        """
        다년도 시뮬레이션 (1년~max_years)
        
        Args:
            initial_replacement_cost: 최초 재조달가액
            max_years: 최대 시뮬레이션 연수
        
        Returns:
            연도별 시뮬레이션 결과 리스트
        """
        results = []
        
        for year in range(0, max_years + 1):
            if year == 0:
                results.append({
                    'year': 0,
                    'future_replacement_cost': initial_replacement_cost,
                    'cumulative_depreciation_rate': 0.0,
                    'future_insurance_value': initial_replacement_cost,
                    'insurance_value_ratio': 100.0
                })
            else:
                result = self.calculate_future_insurance_value(
                    initial_replacement_cost, year
                )
                result['year'] = year
                results.append(result)
        
        return results
    
    def check_proportional_liability_risk(
        self,
        insured_amount: float,
        future_insurance_value: float,
        coverage_threshold: float = 0.8
    ) -> Dict[str, any]:
        """
        비례보상 리스크 체크
        
        Args:
            insured_amount: 보험가입금액
            future_insurance_value: 미래 보험가액
            coverage_threshold: 비례보상 기준 (기본 80%)
        
        Returns:
            {
                'is_under_insured': 일부보험 여부,
                'coverage_ratio': 가입 비율 (보험가입금액 / 보험가액),
                'proportional_penalty': 비례보상 패널티 비율,
                'warning_message': 경고 메시지
            }
        """
        coverage_ratio = insured_amount / future_insurance_value
        threshold_amount = future_insurance_value * coverage_threshold
        
        is_under_insured = insured_amount < threshold_amount
        
        if is_under_insured:
            # 비례보상 패널티 = (가입금액 / (보험가액 × 80%))
            proportional_penalty = insured_amount / threshold_amount
            warning_message = (
                f"⚠️ 일부보험 상태입니다. 보험금이 약 {(1 - proportional_penalty) * 100:.1f}% 삭감될 위험이 있습니다."
            )
        else:
            proportional_penalty = 1.0
            warning_message = "✅ 비례보상 위험이 없습니다."
        
        return {
            'is_under_insured': is_under_insured,
            'coverage_ratio': coverage_ratio,
            'proportional_penalty': proportional_penalty,
            'warning_message': warning_message
        }
    
    def get_recommended_coverage_ratio(self, insurance_period_years: int) -> float:
        """
        보험 기간에 따른 권장 가입 비율
        
        Args:
            insurance_period_years: 보험 기간 (년)
        
        Returns:
            권장 가입 비율 (예: 1.30 = 130%)
        """
        return self.COVERAGE_RATIO_MAP.get(insurance_period_years, 1.30)
    
    def generate_ceo_recommendation(
        self,
        company_name: str,
        initial_replacement_cost: float,
        insurance_period_years: int,
        current_insured_amount: Optional[float] = None
    ) -> Dict[str, any]:
        """
        CEO 맞춤형 권고안 생성
        
        Args:
            company_name: 법인명
            initial_replacement_cost: 현재 재조달가액
            insurance_period_years: 보험 기간
            current_insured_amount: 현재 가입금액 (선택)
        
        Returns:
            종합 권고안 딕셔너리
        """
        # 권장 가입 비율
        recommended_ratio = self.get_recommended_coverage_ratio(insurance_period_years)
        recommended_amount = initial_replacement_cost * recommended_ratio
        
        # 만기 시점 시뮬레이션
        future_result = self.calculate_future_insurance_value(
            initial_replacement_cost, insurance_period_years
        )
        
        # 현재 가입금액이 있다면 리스크 체크
        risk_analysis = None
        if current_insured_amount:
            risk_analysis = self.check_proportional_liability_risk(
                current_insured_amount,
                future_result['future_insurance_value']
            )
        
        # CEO 화법 생성
        ceo_script = self._generate_ceo_script(
            company_name,
            initial_replacement_cost,
            insurance_period_years,
            future_result,
            recommended_ratio,
            recommended_amount,
            current_insured_amount,
            risk_analysis
        )
        
        return {
            'company_name': company_name,
            'initial_replacement_cost': initial_replacement_cost,
            'insurance_period_years': insurance_period_years,
            'recommended_ratio': recommended_ratio,
            'recommended_amount': recommended_amount,
            'future_result': future_result,
            'current_insured_amount': current_insured_amount,
            'risk_analysis': risk_analysis,
            'ceo_script': ceo_script
        }
    
    def _generate_ceo_script(
        self,
        company_name: str,
        initial_rc: float,
        years: int,
        future_result: Dict,
        recommended_ratio: float,
        recommended_amount: float,
        current_amount: Optional[float],
        risk_analysis: Optional[Dict]
    ) -> str:
        """CEO 설득 화법 생성 (내부 메서드)"""
        
        future_rc = future_result['future_replacement_cost']
        future_iv = future_result['future_insurance_value']
        iv_ratio = future_result['insurance_value_ratio']
        
        script = f"""
# 🏢 {company_name} 법인화재보험 전략 리포트

## 📊 현황 분석

- **현재 재조달가액**: {initial_rc:,.0f}원
- **보험 기간**: {years}년
- **{years}년 뒤 예상 재조달가액**: {future_rc:,.0f}원 (약 {(future_rc/initial_rc - 1)*100:.1f}% 상승)
- **{years}년 뒤 보험가액** (법적 보상 기준): {future_iv:,.0f}원 (약 {iv_ratio:.1f}%)

## ⚠️ 핵심 리스크

### 1. 물가 vs 감가의 힘겨루기

대표님, 공장이 낡으니까 시간이 갈수록 보험 가입 금액을 줄여도 된다고 생각하시죠? **천만의 말씀입니다.**

- **물가 상승 속도**: 연 {self.ANNUAL_CONSTRUCTION_INFLATION*100:.0f}% (건설공사비 지수)
- **감가 속도**: 연 {self.ANNUAL_DEPRECIATION_RATE*100:.0f}%
- **결과**: 물가 상승이 감가보다 훨씬 빠릅니다!

{years}년 뒤에 이 공장은 낡아서 가치가 떨어졌음에도 불구하고, **다시 지으려면 {future_rc:,.0f}원**이 듭니다.

### 2. 비례보상의 공포
"""
        
        if risk_analysis and risk_analysis['is_under_insured']:
            script += f"""
**⚠️ 현재 가입금액 {current_amount:,.0f}원은 위험합니다!**

{years}년 뒤 보험가액({future_iv:,.0f}원)보다 적게 가입되어 있어, 사고 시 보험금이 약 **{(1 - risk_analysis['proportional_penalty'])*100:.1f}% 삭감**될 위험이 있습니다.
"""
        
        script += f"""

## ✅ 전문가 권고안

### {int(recommended_ratio*100)}% 플랜 ({recommended_amount:,.0f}원)

**왜 {int(recommended_ratio*100)}%인가?**

1. **{years}년 뒤 보험가액 방어**: {future_iv:,.0f}원을 완벽히 커버
2. **비례보상 원천 차단**: 어떤 상황에서도 보험금 삭감 없음
3. **물가 변동 안전 마진**: 예상보다 물가가 더 올라도 방어

### 실전 클로징 멘트

> "대표님, {years}년 장기 보험을 100%로 가입하는 것은 시간이 갈수록 보상권이 줄어드는 '역주행'입니다.
> 
> 제가 제안하는 **{int(recommended_ratio*100)}% 플랜**은 {years}년 뒤 어떤 인플레이션이 와도 대표님의 재기 자금을 1원도 깎이지 않게 묶어두는 **'물가 방어막'**입니다."

## 📋 법적 근거

- **실화책임법** (2007년 개정): 경과실로도 배상 책임 100% 발생
- **민법 제758조**: 공작물 소유자 무과실 책임
- **상법 제676조**: 보험가액은 사고 시점 기준

---

**본 리포트는 최신 법률 및 경제 지표를 근거로 작성되었습니다.**
"""
        
        return script.strip()
    
    def calculate_tax_benefit(
        self,
        annual_premium: float,
        corporate_tax_rate: float = 0.22
    ) -> Dict[str, float]:
        """
        법인세 절세 효과 계산
        
        Args:
            annual_premium: 연간 보험료
            corporate_tax_rate: 법인세율 (기본 22%)
        
        Returns:
            {
                'annual_premium': 연간 보험료,
                'tax_deduction': 손금산입액,
                'tax_saving': 법인세 절감액
            }
        """
        tax_deduction = annual_premium
        tax_saving = annual_premium * corporate_tax_rate
        
        return {
            'annual_premium': annual_premium,
            'tax_deduction': tax_deduction,
            'tax_saving': tax_saving
        }
    
    def analyze_neighbor_fire_risk(
        self,
        factory_type: str,
        neighbor_factory_types: List[str],
        industrial_complex_density: str = "중"
    ) -> Dict[str, any]:
        """
        이웃 공장 연소 리스크 분석
        
        Args:
            factory_type: 우리 공장 업종
            neighbor_factory_types: 이웃 공장 업종 리스트
            industrial_complex_density: 산업단지 밀집도 (상/중/하)
        
        Returns:
            리스크 분석 결과
        """
        # 고위험 업종 리스트
        high_risk_types = [
            "반도체", "정밀기계", "전자부품", "화학", "석유화학",
            "의약품", "바이오", "디스플레이"
        ]
        
        # 이웃 공장 중 고위험 업종 체크
        high_risk_neighbors = [
            n for n in neighbor_factory_types
            if any(hr in n for hr in high_risk_types)
        ]
        
        # 리스크 레벨 판정
        if len(high_risk_neighbors) >= 2 or industrial_complex_density == "상":
            risk_level = "상"
            recommended_liability_limit = 30_00000000  # 30억
        elif len(high_risk_neighbors) >= 1 or industrial_complex_density == "중":
            risk_level = "중"
            recommended_liability_limit = 20_00000000  # 20억
        else:
            risk_level = "하"
            recommended_liability_limit = 10_00000000  # 10억
        
        return {
            'factory_type': factory_type,
            'neighbor_factory_types': neighbor_factory_types,
            'high_risk_neighbors': high_risk_neighbors,
            'industrial_complex_density': industrial_complex_density,
            'risk_level': risk_level,
            'recommended_liability_limit': recommended_liability_limit,
            'warning_message': self._generate_neighbor_risk_message(
                high_risk_neighbors, risk_level, recommended_liability_limit
            )
        }
    
    def _generate_neighbor_risk_message(
        self,
        high_risk_neighbors: List[str],
        risk_level: str,
        recommended_limit: float
    ) -> str:
        """이웃 공장 리스크 경고 메시지 생성"""
        
        if risk_level == "상":
            return f"""
⚠️ **고위험 경고**: 주변에 {', '.join(high_risk_neighbors)} 등 고가 설비 공장이 있습니다.
연소 확대 시 배상액이 수십억~수백억에 달할 수 있습니다.
**화재배상책임(대물) 한도를 최소 {recommended_limit:,.0f}원 이상으로 설정하십시오.**
"""
        elif risk_level == "중":
            return f"""
⚠️ **중위험 주의**: 산업단지 내 연소 확대 가능성이 있습니다.
**화재배상책임(대물) 한도를 최소 {recommended_limit:,.0f}원으로 권장합니다.**
"""
        else:
            return f"""
✅ **저위험**: 현재 주변 환경은 비교적 안전합니다.
기본 화재배상책임(대물) {recommended_limit:,.0f}원 권장.
"""


# 사용 예시
if __name__ == "__main__":
    expert = FireInsuranceExpert()
    
    # CEO 권고안 생성
    recommendation = expert.generate_ceo_recommendation(
        company_name="골드키 정밀기계(주)",
        initial_replacement_cost=10_00000000,  # 10억
        insurance_period_years=5,
        current_insured_amount=10_00000000  # 현재 10억 가입
    )
    
    print(recommendation['ceo_script'])
    print("\n" + "="*80 + "\n")
    
    # 이웃 공장 리스크 분석
    neighbor_risk = expert.analyze_neighbor_fire_risk(
        factory_type="일반 기계",
        neighbor_factory_types=["반도체 부품", "정밀 금형"],
        industrial_complex_density="상"
    )
    
    print(neighbor_risk['warning_message'])
