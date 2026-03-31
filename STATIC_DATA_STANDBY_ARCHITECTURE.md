# 정적 데이터 스탠바이 아키텍처 설계서

**Goldkey AI Masters 2026 — LLM 우회 정밀 연산 시스템**  
**작성일**: 2026-03-30  
**목적**: 고정된 수식/표 데이터를 서버 메모리에 상시 대기시켜 LLM 없이 100% 정확한 수학 연산 수행

---

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [Phase 1: 데이터 발굴 및 구조화](#phase-1-데이터-발굴-및-구조화)
3. [Phase 2: HQ 서버 내장 및 스탠바이](#phase-2-hq-서버-내장-및-스탠바이)
4. [Phase 3: 무결점 연산 라우팅](#phase-3-무결점-연산-라우팅)
5. [16대 보장항목 매핑 시스템](#16대-보장항목-매핑-시스템)
6. [3-Way 비교 엔진](#3-way-비교-엔진)
7. [디렉토리 구조](#디렉토리-구조)
8. [데이터 흐름도](#데이터-흐름도)

---

## 아키텍처 개요

### 핵심 원칙
1. **LLM 우회**: 수학 연산은 LLM에게 묻지 않고 파이썬 엔진이 직접 처리
2. **메모리 스탠바이**: 서버 부팅 시 JSON 데이터를 전역 변수로 메모리 적재
3. **정확성 보장**: 고정된 수식/표는 100% 정확한 값만 도출
4. **LLM 역할 제한**: LLM은 최종 숫자를 감성 문장으로 포장하는 용도로만 사용

### 전체 구조도
```
┌─────────────────────────────────────────────────────────────────┐
│                    Phase 1: 데이터 발굴 (PRO)                      │
├─────────────────────────────────────────────────────────────────┤
│  웹 수집 → JSON 변환 → 검증 → WINDSURF 전달                        │
│  - 호프만 계수표                                                    │
│  - KCD 코드표                                                      │
│  - 16대 보장항목 매핑표                                             │
│  - KB 스탠다드 기준                                                │
│  - 트리니티 배분율                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Phase 2: 서버 내장 및 스탠바이 (WINDSURF)              │
├─────────────────────────────────────────────────────────────────┤
│  hq_backend/knowledge_base/static/                              │
│  ├── hoffman_table.json                                         │
│  ├── kcd_codes.json                                             │
│  ├── coverage_16_categories_mapping.json                        │
│  ├── kb_trinity_standards.json                                  │
│  └── ...                                                         │
│                                                                  │
│  서버 부팅 시 → 전역 변수 메모리 적재 → 상시 대기                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              Phase 3: 무결점 연산 라우팅 (실행)                     │
├─────────────────────────────────────────────────────────────────┤
│  CRM 입력 → Supabase → HQ 라우터 → Static Engine → 결과 도출      │
│                                    ↓                             │
│                              LLM (감성 포장만)                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: 데이터 발굴 및 구조화

### 대상 데이터 목록

#### 1. 교통사고 관련 (2500, 4200, 9100)
- **호프만 계수표**: 교통사고 합의금 산출용 (1~240개월)
- **과실비율표**: 사고 유형별 과실 비율
- **위자료 기준표**: 상해 등급별 위자료 금액

#### 2. 장해 산출 관련 (2300)
- **맥브라이드 장해평가표**: 신체 부위별 장해율
- **노동능력상실률표**: 연령별 노동능력 상실률

#### 3. 비상장주식 평가 (5400)
- **상증세법 수식**: 순손익가치 + 순자산가치 가중평균
- **업종별 PER 기준표**: 업종별 평균 PER

#### 4. 보험증권 분석 (1200, 4100) — **신규 추가**
- **16대 보장항목 매핑표**: 보험사별 특약명 → 16대 표준 항목 매핑
- **KB 스탠다드 기준**: 16대 항목별 권장 가입금액 (고정값)
- **트리니티 배분율**: 16대 항목별 소득 비례 배분 비율

### JSON 구조 예시

#### hoffman_table.json
```json
{
  "metadata": {
    "name": "호프만 계수표",
    "description": "교통사고 합의금 산출용 중간이자 공제 계수",
    "source": "대법원 2019. 2. 21. 선고 2018다248909 전원합의체 판결",
    "annual_interest_rate": 0.05,
    "last_updated": "2026-03-30"
  },
  "coefficients": {
    "1": 0.9958,
    "2": 1.9834,
    "3": 2.9630,
    "12": 11.6189,
    "24": 22.1106,
    "36": 31.9468,
    "60": 51.7256,
    "120": 90.0735,
    "180": 117.6041,
    "240": 150.3245
  }
}
```

#### coverage_16_categories_mapping.json
```json
{
  "metadata": {
    "name": "16대 보장항목 매핑표",
    "description": "보험사별 특약명을 16대 표준 항목으로 자동 분류",
    "categories": [
      "사망", "상해장해", "암진단비", "뇌혈관질환", "허혈성심장질환",
      "1~5종수술비", "120대수술비", "입원일당", "배상책임", "운전자",
      "표적항암", "치매간병", "연금", "화재", "고액치료비", "기타"
    ],
    "last_updated": "2026-03-30"
  },
  "mappings": {
    "사망": {
      "keywords": ["사망", "유족", "장례", "death", "사망보험금"],
      "insurance_companies": {
        "삼성화재": ["일반사망", "재해사망", "교통재해사망"],
        "현대해상": ["사망보험금", "재해사망보험금"],
        "KB손해보험": ["사망", "재해사망"],
        "메리츠화재": ["사망담보", "재해사망담보"]
      }
    },
    "상해장해": {
      "keywords": ["장해", "후유장해", "disability", "장해지급률"],
      "insurance_companies": {
        "삼성화재": ["일반상해후유장해", "교통상해후유장해"],
        "현대해상": ["상해후유장해보험금"],
        "KB손해보험": ["후유장해", "상해후유장해"],
        "메리츠화재": ["장해담보"]
      }
    },
    "암진단비": {
      "keywords": ["암진단", "암", "cancer", "악성신생물", "암확정"],
      "insurance_companies": {
        "삼성화재": ["암진단비", "일반암진단비", "유사암진단비"],
        "현대해상": ["암진단금", "암보험금"],
        "KB손해보험": ["암진단", "일반암", "소액암"],
        "메리츠화재": ["암진단담보", "일반암담보"]
      }
    },
    "뇌혈관질환": {
      "keywords": ["뇌출혈", "뇌경색", "뇌졸중", "stroke", "뇌혈관"],
      "insurance_companies": {
        "삼성화재": ["뇌출혈진단비", "뇌경색진단비"],
        "현대해상": ["뇌혈관질환진단금"],
        "KB손해보험": ["뇌출혈", "뇌경색"],
        "메리츠화재": ["뇌혈관질환담보"]
      }
    },
    "허혈성심장질환": {
      "keywords": ["심근경색", "협심증", "심장", "heart", "허혈성"],
      "insurance_companies": {
        "삼성화재": ["급성심근경색진단비", "협심증진단비"],
        "현대해상": ["허혈성심장질환진단금"],
        "KB손해보험": ["심근경색", "협심증"],
        "메리츠화재": ["허혈성심장질환담보"]
      }
    },
    "1~5종수술비": {
      "keywords": ["수술비", "수술", "surgery", "1종", "2종", "3종", "4종", "5종"],
      "insurance_companies": {
        "삼성화재": ["수술비(1~5종)", "일반수술비"],
        "현대해상": ["수술보험금"],
        "KB손해보험": ["수술비"],
        "메리츠화재": ["수술담보"]
      }
    },
    "120대수술비": {
      "keywords": ["120대수술", "특정수술", "major surgery"],
      "insurance_companies": {
        "삼성화재": ["120대수술비"],
        "현대해상": ["특정수술보험금"],
        "KB손해보험": ["120대수술"],
        "메리츠화재": ["특정수술담보"]
      }
    },
    "입원일당": {
      "keywords": ["입원", "입원일당", "hospitalization", "병원입원"],
      "insurance_companies": {
        "삼성화재": ["질병입원일당", "상해입원일당"],
        "현대해상": ["입원비"],
        "KB손해보험": ["입원일당"],
        "메리츠화재": ["입원담보"]
      }
    },
    "배상책임": {
      "keywords": ["배상책임", "liability", "대인", "대물"],
      "insurance_companies": {
        "삼성화재": ["일상생활배상책임"],
        "현대해상": ["배상책임보험금"],
        "KB손해보험": ["배상책임"],
        "메리츠화재": ["배상책임담보"]
      }
    },
    "운전자": {
      "keywords": ["운전자", "driver", "자동차사고", "교통사고"],
      "insurance_companies": {
        "삼성화재": ["운전자보험"],
        "현대해상": ["운전자특약"],
        "KB손해보험": ["운전자"],
        "메리츠화재": ["운전자담보"]
      }
    }
  }
}
```

#### kb_trinity_standards.json
```json
{
  "metadata": {
    "name": "KB 스탠다드 & 트리니티 기준",
    "description": "16대 항목별 권장 가입금액 및 소득 비례 배분율",
    "source": "KB손해보험 7대 스탠다드 + 트리니티 가치 엔진",
    "last_updated": "2026-03-30"
  },
  "kb_standards": {
    "사망": {
      "amount": 100000000,
      "unit": "원",
      "description": "일반상해 사망"
    },
    "상해장해": {
      "amount": 100000000,
      "unit": "원",
      "description": "일반상해 후유장해 (80% 이상)"
    },
    "암진단비": {
      "amount": 50000000,
      "unit": "원",
      "description": "일반암 진단비"
    },
    "뇌혈관질환": {
      "amount": 30000000,
      "unit": "원",
      "description": "뇌출혈/뇌경색 진단비"
    },
    "허혈성심장질환": {
      "amount": 30000000,
      "unit": "원",
      "description": "급성심근경색/협심증 진단비"
    },
    "1~5종수술비": {
      "amount": 5000000,
      "unit": "원",
      "description": "수술비 (5종 기준)"
    },
    "120대수술비": {
      "amount": 10000000,
      "unit": "원",
      "description": "특정 고액 수술비"
    },
    "입원일당": {
      "amount": 50000,
      "unit": "원/일",
      "description": "질병/상해 입원일당"
    },
    "배상책임": {
      "amount": 100000000,
      "unit": "원",
      "description": "일상생활 배상책임"
    },
    "운전자": {
      "amount": 30000000,
      "unit": "원",
      "description": "자동차사고 벌금/변호사비용"
    },
    "표적항암": {
      "amount": 10000000,
      "unit": "원",
      "description": "표적항암약물허가치료비"
    },
    "치매간병": {
      "amount": 30000000,
      "unit": "원",
      "description": "치매진단비 + 간병비"
    },
    "연금": {
      "amount": 1000000,
      "unit": "원/월",
      "description": "노후 연금"
    },
    "화재": {
      "amount": 50000000,
      "unit": "원",
      "description": "주택화재 (임차인)"
    },
    "고액치료비": {
      "amount": 20000000,
      "unit": "원",
      "description": "고액암/뇌/심장 치료비"
    },
    "기타": {
      "amount": 0,
      "unit": "원",
      "description": "기타 특약"
    }
  },
  "trinity_ratios": {
    "description": "가처분소득 대비 16대 항목 배분 비율 (합계 100%)",
    "base_premium_ratio": 0.12,
    "distribution": {
      "사망": 0.15,
      "상해장해": 0.15,
      "암진단비": 0.20,
      "뇌혈관질환": 0.10,
      "허혈성심장질환": 0.10,
      "1~5종수술비": 0.05,
      "120대수술비": 0.05,
      "입원일당": 0.05,
      "배상책임": 0.03,
      "운전자": 0.03,
      "표적항암": 0.03,
      "치매간병": 0.03,
      "연금": 0.02,
      "화재": 0.01,
      "고액치료비": 0.03,
      "기타": 0.02
    }
  },
  "calculation_formula": {
    "trinity_amount": "disposable_income * 0.12 * distribution_ratio",
    "shortage": "max(0, kb_standard - current_amount)",
    "recommended": "max(kb_standard, trinity_amount)"
  }
}
```

---

## Phase 2: HQ 서버 내장 및 스탠바이

### 디렉토리 구조
```
d:\CascadeProjects\
├── hq_backend\
│   ├── knowledge_base\
│   │   └── static\
│   │       ├── hoffman_table.json
│   │       ├── kcd_codes.json
│   │       ├── coverage_16_categories_mapping.json
│   │       ├── kb_trinity_standards.json
│   │       ├── fault_ratio_table.json
│   │       └── mcbride_disability_table.json
│   ├── engines\
│   │   └── static_calculators\
│   │       ├── __init__.py
│   │       ├── static_data_loader.py  (전역 변수 로더)
│   │       ├── damages_calculator.py  (교통사고 합의금)
│   │       ├── disability_calculator.py  (장해 산출)
│   │       ├── coverage_calculator.py  (증권 분석) ← 신규
│   │       └── stock_valuation_calculator.py  (비상장주식)
│   └── routers\
│       └── static_engine_router.py  (라우팅 로직)
└── app.py
```

### 전역 변수 로더 (static_data_loader.py)
```python
"""
정적 데이터 전역 변수 로더
서버 부팅 시 JSON 파일들을 메모리에 적재하여 상시 대기
"""
import json
import os
from pathlib import Path

# 정적 데이터 디렉토리 경로
STATIC_DATA_DIR = Path(__file__).parent.parent / "knowledge_base" / "static"

# 전역 변수 (서버 부팅 시 즉시 메모리 적재)
HOFFMAN_DATA = None
KCD_CODES = None
COVERAGE_16_MAPPING = None
KB_TRINITY_STANDARDS = None
FAULT_RATIO_TABLE = None
MCBRIDE_DISABILITY_TABLE = None

def load_static_data():
    """서버 부팅 시 모든 정적 데이터를 메모리에 적재 (Standby)"""
    global HOFFMAN_DATA, KCD_CODES, COVERAGE_16_MAPPING, KB_TRINITY_STANDARDS
    global FAULT_RATIO_TABLE, MCBRIDE_DISABILITY_TABLE
    
    try:
        # 호프만 계수표
        with open(STATIC_DATA_DIR / "hoffman_table.json", "r", encoding="utf-8") as f:
            HOFFMAN_DATA = json.load(f)
        
        # KCD 코드표
        with open(STATIC_DATA_DIR / "kcd_codes.json", "r", encoding="utf-8") as f:
            KCD_CODES = json.load(f)
        
        # 16대 보장항목 매핑표
        with open(STATIC_DATA_DIR / "coverage_16_categories_mapping.json", "r", encoding="utf-8") as f:
            COVERAGE_16_MAPPING = json.load(f)
        
        # KB/트리니티 기준
        with open(STATIC_DATA_DIR / "kb_trinity_standards.json", "r", encoding="utf-8") as f:
            KB_TRINITY_STANDARDS = json.load(f)
        
        # 과실비율표
        with open(STATIC_DATA_DIR / "fault_ratio_table.json", "r", encoding="utf-8") as f:
            FAULT_RATIO_TABLE = json.load(f)
        
        # 맥브라이드 장해평가표
        with open(STATIC_DATA_DIR / "mcbride_disability_table.json", "r", encoding="utf-8") as f:
            MCBRIDE_DISABILITY_TABLE = json.load(f)
        
        print("✅ 정적 데이터 메모리 적재 완료 (Standby)")
        return True
    
    except FileNotFoundError as e:
        print(f"❌ 정적 데이터 파일 없음: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON 파싱 오류: {e}")
        return False

# 서버 부팅 시 자동 실행
load_static_data()
```

---

## Phase 3: 무결점 연산 라우팅

### 증권 분석 엔진 (coverage_calculator.py)
```python
"""
가족 통합 증권 분석 엔진
16대 보장항목 매핑 및 3-Way 비교 (현재/트리니티/KB)
"""
from typing import List, Dict
from .static_data_loader import COVERAGE_16_MAPPING, KB_TRINITY_STANDARDS

class CoverageCalculator:
    """증권 분석 및 3-Way 비교 엔진"""
    
    def __init__(self):
        self.mapping = COVERAGE_16_MAPPING
        self.standards = KB_TRINITY_STANDARDS
    
    def aggregate_by_family(self, ocr_data: List[Dict]) -> Dict[str, List[Dict]]:
        """
        OCR로 추출된 여러 증권을 피보험자(가족 구성원) 기준으로 그룹화
        
        Args:
            ocr_data: OCR 추출 데이터 리스트
                [
                    {
                        "insured_name": "홍길동",
                        "insurance_company": "삼성화재",
                        "coverages": [
                            {"name": "일반암진단비", "amount": 30000000},
                            {"name": "뇌출혈진단비", "amount": 20000000}
                        ]
                    },
                    ...
                ]
        
        Returns:
            가족 구성원별 그룹화된 데이터
                {
                    "홍길동": [증권1, 증권2, ...],
                    "김영희": [증권3, ...],
                    ...
                }
        """
        family_data = {}
        
        for policy in ocr_data:
            insured_name = policy.get("insured_name", "미확인")
            if insured_name not in family_data:
                family_data[insured_name] = []
            family_data[insured_name].append(policy)
        
        return family_data
    
    def map_to_16_categories(self, coverages: List[Dict], insurance_company: str) -> Dict[str, int]:
        """
        보험사별 특약명을 16대 표준 항목으로 자동 매핑 및 합산
        
        Args:
            coverages: 특약 리스트
                [
                    {"name": "일반암진단비", "amount": 30000000},
                    {"name": "뇌출혈진단비", "amount": 20000000}
                ]
            insurance_company: 보험사명 (예: "삼성화재")
        
        Returns:
            16대 항목별 합산 금액
                {
                    "암진단비": 30000000,
                    "뇌혈관질환": 20000000,
                    ...
                }
        """
        category_sums = {cat: 0 for cat in self.mapping["metadata"]["categories"]}
        
        for coverage in coverages:
            coverage_name = coverage["name"]
            coverage_amount = coverage["amount"]
            
            # 16대 항목 중 매칭되는 카테고리 찾기
            matched = False
            for category, mapping_data in self.mapping["mappings"].items():
                # 보험사별 특약명 매칭
                company_coverages = mapping_data["insurance_companies"].get(insurance_company, [])
                if coverage_name in company_coverages:
                    category_sums[category] += coverage_amount
                    matched = True
                    break
                
                # 키워드 매칭 (보험사 매핑에 없는 경우)
                if not matched:
                    for keyword in mapping_data["keywords"]:
                        if keyword in coverage_name:
                            category_sums[category] += coverage_amount
                            matched = True
                            break
            
            # 매칭 실패 시 "기타"로 분류
            if not matched:
                category_sums["기타"] += coverage_amount
        
        return category_sums
    
    def calculate_3way_comparison(
        self, 
        current_data: Dict[str, int], 
        disposable_income: int
    ) -> List[Dict]:
        """
        3-Way 비교: 현재 가입금액 vs 트리니티 권장액 vs KB 스탠다드
        
        Args:
            current_data: 현재 가입금액 (16대 항목별)
                {
                    "암진단비": 30000000,
                    "뇌혈관질환": 20000000,
                    ...
                }
            disposable_income: 가처분소득 (만원)
        
        Returns:
            3-Way 비교 결과
                [
                    {
                        "category": "암진단비",
                        "current": 30000000,
                        "trinity": 36000000,
                        "kb_standard": 50000000,
                        "shortage_vs_trinity": 6000000,
                        "shortage_vs_kb": 20000000,
                        "recommended": 50000000,
                        "priority": "high"
                    },
                    ...
                ]
        """
        results = []
        
        # 트리니티 기준 계산
        base_premium = disposable_income * 10000 * self.standards["trinity_ratios"]["base_premium_ratio"]
        
        for category in self.standards["metadata"]["categories"]:
            current_amount = current_data.get(category, 0)
            kb_amount = self.standards["kb_standards"][category]["amount"]
            trinity_ratio = self.standards["trinity_ratios"]["distribution"][category]
            trinity_amount = int(base_premium * trinity_ratio)
            
            # 부족 금액 계산
            shortage_vs_trinity = max(0, trinity_amount - current_amount)
            shortage_vs_kb = max(0, kb_amount - current_amount)
            
            # 권장 금액 (KB와 트리니티 중 큰 값)
            recommended = max(kb_amount, trinity_amount)
            
            # 우선순위 결정
            shortage_rate = (shortage_vs_kb / kb_amount * 100) if kb_amount > 0 else 0
            if shortage_rate >= 70:
                priority = "긴급"
            elif shortage_rate >= 40:
                priority = "중요"
            else:
                priority = "보통"
            
            results.append({
                "category": category,
                "current": current_amount,
                "trinity": trinity_amount,
                "kb_standard": kb_amount,
                "shortage_vs_trinity": shortage_vs_trinity,
                "shortage_vs_kb": shortage_vs_kb,
                "recommended": recommended,
                "shortage_rate": round(shortage_rate, 1),
                "priority": priority
            })
        
        # 부족률 높은 순으로 정렬
        results.sort(key=lambda x: x["shortage_rate"], reverse=True)
        
        return results
    
    def analyze_family_policies(
        self, 
        ocr_data: List[Dict], 
        family_income_data: Dict[str, int]
    ) -> Dict:
        """
        가족 전체 증권 통합 분석
        
        Args:
            ocr_data: OCR 추출 데이터 리스트
            family_income_data: 가족 구성원별 가처분소득
                {
                    "홍길동": 150,  # 만원
                    "김영희": 100,
                    ...
                }
        
        Returns:
            가족 구성원별 3-Way 비교 결과
                {
                    "홍길동": {
                        "current_coverages": {...},
                        "3way_comparison": [...]
                    },
                    ...
                }
        """
        # 1. 가족 구성원별 그룹화
        family_data = self.aggregate_by_family(ocr_data)
        
        # 2. 구성원별 분석
        family_analysis = {}
        
        for member_name, policies in family_data.items():
            # 구성원의 모든 증권 통합
            all_coverages = []
            for policy in policies:
                insurance_company = policy.get("insurance_company", "기타")
                coverages = policy.get("coverages", [])
                
                # 16대 항목으로 매핑
                mapped = self.map_to_16_categories(coverages, insurance_company)
                all_coverages.append(mapped)
            
            # 16대 항목별 합산
            total_current = {cat: 0 for cat in self.standards["metadata"]["categories"]}
            for cov in all_coverages:
                for cat, amount in cov.items():
                    total_current[cat] += amount
            
            # 3-Way 비교
            disposable_income = family_income_data.get(member_name, 150)  # 기본값 150만원
            comparison = self.calculate_3way_comparison(total_current, disposable_income)
            
            family_analysis[member_name] = {
                "current_coverages": total_current,
                "disposable_income": disposable_income,
                "3way_comparison": comparison,
                "total_shortage_vs_kb": sum(item["shortage_vs_kb"] for item in comparison),
                "high_priority_items": [item for item in comparison if item["priority"] == "긴급"]
            }
        
        return family_analysis
```

---

## 16대 보장항목 매핑 시스템

### 매핑 로직
1. **보험사별 특약명 우선 매칭**: 정확한 특약명으로 먼저 매칭
2. **키워드 매칭**: 보험사 매핑에 없는 경우 키워드로 매칭
3. **기타 분류**: 매칭 실패 시 "기타"로 분류

### 지원 보험사
- 삼성화재
- 현대해상
- KB손해보험
- 메리츠화재
- (추가 보험사는 JSON에 계속 확장 가능)

---

## 3-Way 비교 엔진

### 비교 기준
1. **현재 가입금액 (Current)**: 기존 증권 합산
2. **트리니티 권장액 (Trinity)**: 가처분소득 × 12% × 배분율
3. **KB 스탠다드 (KB Standard)**: 고정 권장 금액

### 부족 금액 계산
```python
shortage_vs_trinity = max(0, trinity_amount - current_amount)
shortage_vs_kb = max(0, kb_amount - current_amount)
recommended = max(kb_amount, trinity_amount)
```

### 우선순위 결정
- **긴급**: 부족률 70% 이상
- **중요**: 부족률 40~70%
- **보통**: 부족률 40% 미만

---

## 데이터 흐름도

### 전체 워크플로우
```
1. CRM: 가족 증권 스캔
   ↓
2. OCR: 피보험자명, 보험사, 특약 추출
   ↓
3. HQ Static Engine: 16대 항목 매핑 (LLM 없음)
   ↓
4. HQ Static Engine: 3-Way 비교 계산 (LLM 없음)
   ↓
5. HQ Report Generator: 결과 JSON 생성
   ↓
6. LLM: 감성 문장 포장 (선택)
   ↓
7. CRM: 3-Way 대조표 렌더링
```

### 메모리 흐름
```
서버 부팅
    ↓
static_data_loader.py 실행
    ↓
JSON 파일들 → 전역 변수 메모리 적재
    ↓
상시 대기 (Standby)
    ↓
요청 발생 시 즉시 참조 (I/O 없음)
```

---

## 다음 단계

1. ✅ 아키텍처 설계 완료
2. ⏳ JSON 스켈레톤 생성
3. ⏳ 파이썬 엔진 구축
4. ⏳ 라우터 연동
5. ⏳ 테스트 및 검증
