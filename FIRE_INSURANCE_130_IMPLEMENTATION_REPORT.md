# 법인화재보험 130% 플랜 구현 완료 보고서

**작성일**: 2026-03-31  
**작성자**: Cascade AI  
**프로젝트**: Goldkey AI Masters 2026 - 법인화재보험 논리 체계 구축

---

## 📋 목차

1. [구현 개요](#구현-개요)
2. [생성된 파일 목록](#생성된-파일-목록)
3. [핵심 논리 체계](#핵심-논리-체계)
4. [엔진 구현 상세](#엔진-구현-상세)
5. [RAG 저장 전략](#rag-저장-전략)
6. [다음 단계](#다음-단계)

---

## 구현 개요

### 목적

법인화재보험 관련 법률, 경제 지표, 수학적 시뮬레이션을 결합한 **130% 플랜 논리 체계**를 구축하여:
1. Cloud Run (HQ 앱)에서 AI 분석 시 활용
2. Supabase RAG 시스템에 지식 저장
3. GCS에 백업 저장
4. 중앙센터(gk_sec09)에서 필요 시 인출

### 핵심 논리

**"물가 상승률(연 8%)이 감가율(연 3%)을 이기기 때문에, 5년 만기 장기 보험은 130% 가입이 필수"**

---

## 생성된 파일 목록

### 1. 엔진 모듈

#### `d:\CascadeProjects\engines\fire_insurance_expert.py`

**클래스**: `FireInsuranceExpert`

**핵심 기능**:
- 미래 시점 보험가액 계산 (`calculate_future_insurance_value`)
- 다년도 시뮬레이션 (`simulate_multi_year`)
- 비례보상 리스크 체크 (`check_proportional_liability_risk`)
- 만기별 권장 가입 비율 (`get_recommended_coverage_ratio`)
- CEO 맞춤형 권고안 생성 (`generate_ceo_recommendation`)
- 법인세 절세 효과 계산 (`calculate_tax_benefit`)
- 이웃 공장 연소 리스크 분석 (`analyze_neighbor_fire_risk`)

**경제 지표 상수**:
```python
ANNUAL_CONSTRUCTION_INFLATION = 0.08  # 건설공사비 지수(CCI) 상승률 8%
ANNUAL_WAGE_GROWTH = 0.04             # 인건비 상승률 4%
ANNUAL_DEPRECIATION_RATE = 0.03       # 연간 감가율 3%
```

**만기별 권장 가입 비율**:
```python
COVERAGE_RATIO_MAP = {
    1: 1.15,   # 1년 소멸식: 115%
    3: 1.25,   # 3년 장기: 125%
    5: 1.30,   # 5년 장기: 130%
}
```

### 2. RAG 지식 베이스 (source_docs)

#### `d:\CascadeProjects\source_docs\법인화재보험_130프로_논리_완결판.md`

**내용**:
- 법률적 리스크 진단 (실화법, 민법, 상법)
- 전문 용어 정의 (재조달가액, 보험가액, 보험가입금액)
- 5개년 장기보험 수학적 시뮬레이션
- 130% 플랜의 전략적 필요성
- CEO 설득 화법
- 약관 및 판례 근거

**분량**: 약 1,200줄

#### `d:\CascadeProjects\source_docs\실화책임법_2007개정_법인리스크.md`

**내용**:
- 실화법 개정의 배경 (가해자 보호 → 피해자 구제)
- 법인 대표님이 반드시 알아야 할 3대 리스크
- 실전 컨설팅 화법 ("A공장과 B공장의 잔인한 운명")
- 보험 설계 시 필살기 (배상책임 한도 극대화, 구상권 방어, 130% 플랜)
- 관련 법률 전문 (실화법, 민법 750조, 758조, 765조, 형법 170조, 171조)
- 사고 상황별 법률 매핑표

**분량**: 약 600줄

#### `d:\CascadeProjects\source_docs\재조달가액_보험가액_용어정의.md`

**내용**:
- 핵심 용어 정의 (재조달가액, 보험가액, 보험가입금액)
- 재조달가액과 보험가액의 관계 (공식 및 시점별 변화)
- 시가 vs 보험가액 vs 재조달가액 비교표
- CEO가 직면하는 현금 유출의 정체
- 재조달가액 특약의 법리
- 약관상 정의
- 실무 적용 예시

**분량**: 약 500줄

---

## 핵심 논리 체계

### 1. 보험가액 계산 공식

```
보험가액(t년 후) = [재조달가액 × (1 + 물가상승률)^t] × [1 - (감가율 × t)]

여기서:
- 재조달가액: 최초 가입 시점의 재조달가액
- 물가상승률: 연간 건설공사비 지수(CCI) 상승률 (8%)
- 감가율: 연간 감가율 (3%)
- t: 경과 연수
```

### 2. 5년 만기 시뮬레이션 결과

| 경과 연수 | 재조달가액 | 누적 감가율 | 보험가액 | 비율 |
|----------|-----------|------------|---------|------|
| 가입 시점 | 10.0억 | 0% | 10.0억 | 100% |
| 1년 후 | 10.8억 | 3% | 10.5억 | 105% |
| 3년 후 | 12.6억 | 9% | 11.5억 | 115% |
| **5년 후** | **14.7억** | **15%** | **12.5억** | **125%** |

**결론**: 5년 뒤 보험가액은 약 125%로 수렴 → **130% 가입 필수**

### 3. 비례보상 산식

```
지급보험금 = 손해액 × (보험가입금액 / 보험가액 × 80%)
```

**위험**:
- 보험가입금액 < 보험가액 × 80% → 일부보험 → 비례보상 발생
- 5년 뒤 보험가액 12.5억 × 80% = 10억
- 120% 가입(12억) < 10억 → 비례보상 위험
- **130% 가입(13억) > 10억 → 비례보상 회피**

---

## 엔진 구현 상세

### FireInsuranceExpert 클래스 주요 메서드

#### 1. calculate_future_insurance_value()

**기능**: 미래 시점의 보험가액 계산

**입력**:
- `initial_replacement_cost`: 최초 재조달가액
- `years`: 경과 연수
- `inflation_rate`: 연간 물가 상승률 (기본 8%)
- `depreciation_rate`: 연간 감가율 (기본 3%)

**출력**:
```python
{
    'future_replacement_cost': 미래 재조달가액,
    'cumulative_depreciation_rate': 누적 감가율,
    'future_insurance_value': 미래 보험가액,
    'insurance_value_ratio': 보험가액 비율 (초기 대비 %)
}
```

#### 2. check_proportional_liability_risk()

**기능**: 비례보상 리스크 체크

**입력**:
- `insured_amount`: 보험가입금액
- `future_insurance_value`: 미래 보험가액
- `coverage_threshold`: 비례보상 기준 (기본 80%)

**출력**:
```python
{
    'is_under_insured': 일부보험 여부,
    'coverage_ratio': 가입 비율,
    'proportional_penalty': 비례보상 패널티 비율,
    'warning_message': 경고 메시지
}
```

#### 3. generate_ceo_recommendation()

**기능**: CEO 맞춤형 권고안 생성

**입력**:
- `company_name`: 법인명
- `initial_replacement_cost`: 현재 재조달가액
- `insurance_period_years`: 보험 기간
- `current_insured_amount`: 현재 가입금액 (선택)

**출력**:
- 종합 권고안 딕셔너리
- CEO 설득 화법 스크립트 (마크다운 형식)

#### 4. analyze_neighbor_fire_risk()

**기능**: 이웃 공장 연소 리스크 분석

**입력**:
- `factory_type`: 우리 공장 업종
- `neighbor_factory_types`: 이웃 공장 업종 리스트
- `industrial_complex_density`: 산업단지 밀집도 (상/중/하)

**출력**:
```python
{
    'risk_level': 리스크 레벨 (상/중/하),
    'recommended_liability_limit': 권장 배상책임 한도,
    'warning_message': 경고 메시지
}
```

---

## RAG 저장 전략

### 1. Supabase RAG 인제스트

**대상 파일**:
- `법인화재보험_130프로_논리_완결판.md`
- `실화책임법_2007개정_법인리스크.md`
- `재조달가액_보험가액_용어정의.md`

**인제스트 방법**:
- GP193 전역 인제스트 후크 활용
- `source_tab`: `fire_insurance_knowledge`
- `doc_type`: `법률_논리`

**활용**:
- AI 분석 시 RAG 검색으로 관련 지식 자동 인출
- CEO 권고안 생성 시 법률 근거 자동 삽입

### 2. GCS 백업

**저장 경로**:
```
gs://goldkey-ai-storage/knowledge_base/fire_insurance/
├── 법인화재보험_130프로_논리_완결판.md
├── 실화책임법_2007개정_법인리스크.md
└── 재조달가액_보험가액_용어정의.md
```

### 3. Cloud Run 연동

**HQ 앱 (`hq_app_impl.py`) 연동 지점**:

#### [t7] 법인상담(CEO플랜) 탭
- 법인화재보험 상담 시 `FireInsuranceExpert` 엔진 호출
- CEO 권고안 자동 생성
- 법률 근거 자동 표시

#### [gk_sec09] VVIP CEO 통합 경영 전략 센터
- 9950: 법인화재보험 120% → **130% 플랜**으로 업데이트
- 재조달가액 vs 보험가액 비교 그래프
- 5년 시뮬레이션 결과 시각화

---

## 다음 단계

### 1. HQ 앱 통합 (우선순위: 높음)

**작업**:
- `hq_app_impl.py`의 `t7` 탭에 화재보험 상담 블록 추가
- `FireInsuranceExpert` 엔진 import 및 호출
- CEO 권고안 UI 렌더링

**예상 코드**:
```python
from engines.fire_insurance_expert import FireInsuranceExpert

# t7 탭 내부
if st.button("🔥 법인화재보험 130% 플랜 분석"):
    expert = FireInsuranceExpert()
    recommendation = expert.generate_ceo_recommendation(
        company_name=company_name,
        initial_replacement_cost=initial_rc,
        insurance_period_years=5,
        current_insured_amount=current_amount
    )
    st.markdown(recommendation['ceo_script'])
```

### 2. RAG 인제스트 실행 (우선순위: 높음)

**작업**:
- `source_docs` 폴더의 3개 마크다운 파일을 Supabase RAG에 인제스트
- `register_rag_scheduler.ps1` 실행 또는 수동 업로드

**명령어**:
```powershell
# PowerShell에서 실행
.\register_rag_scheduler.ps1
```

### 3. GCS 백업 (우선순위: 중간)

**작업**:
- 3개 마크다운 파일을 GCS에 업로드
- `utils/gcs_master_sync.py` 활용

### 4. gk_sec09 업데이트 (우선순위: 중간)

**작업**:
- 9950 (법인화재보험 120%) → **130% 플랜**으로 명칭 변경
- 시뮬레이션 그래프 추가
- 법률 근거 자동 표시 기능 추가

### 5. CRM 앱 연동 (우선순위: 낮음)

**작업**:
- `crm_app_impl.py`에 간단한 화재보험 상담 링크 추가
- HQ 앱의 `t7` 탭으로 리다이렉트

---

## 요약

### 생성된 자산

1. **엔진**: `fire_insurance_expert.py` (약 400줄)
2. **지식 베이스**: 3개 마크다운 파일 (총 약 2,300줄)
3. **보고서**: 본 파일

### 핵심 논리

- **물가 상승률(8%) > 감가율(3%)** → 5년 뒤 보험가액 125% 상승
- **130% 가입** = 비례보상 방어 + 물가 변동 안전 마진
- **재조달가액 특약** = 감가액을 보험사 돈으로 충당

### 활용 방안

- **Cloud Run**: AI 분석 시 자동 인출
- **Supabase RAG**: 지식 검색 및 자동 삽입
- **GCS**: 백업 및 버전 관리
- **중앙센터 (gk_sec09)**: CEO 전략 리포트 생성

---

**본 구현은 GP 제53조 [코딩 원칙 및 개발 5대 수칙]을 준수하여 작성되었습니다.**
