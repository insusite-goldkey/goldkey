# 교통사고 과실비율 인정기준 RAG 통합 보고서

**작성일**: 2026-03-31  
**목적**: 자동차사고 과실비율 인정기준 문서의 RAG/Supabase/Cloud Run/GCS 통합 현황 분석

---

## 📋 현황 분석

### 1. 문서 보관 현황

**발견된 파일 위치**:
```
✅ d:\CascadeProjects\static\230630_자동차사고 과실비율 인정기준_최종.pdf
✅ d:\CascadeProjects\hq_backend\knowledge_base\source_docs\자동차사고 과실비율 인정기준_최종.pdf
✅ d:\CascadeProjects\workspace\static\230630_자동차사고 과실비율 인정기준_최종.pdf
```

**파일 크기**: 16MB (대용량 PDF)

---

## ❌ 현재 미통합 상태

### 1. RAG 시스템 미연동

**현황**:
- ❌ `run_car_accident_rag_ingest.py` 스크립트 **존재하지 않음**
- ❌ Supabase `gk_knowledge_base` 테이블에 **인제스트되지 않음**
- ❌ 벡터 임베딩 생성 **안 됨**
- ❌ 의미론적 검색 **불가능**

**증거**:
```bash
# grep 검색 결과
run_car_accident_rag_ingest.py: 파일 없음
car_accident_rag: 코드 내 참조 없음
traffic_accident_rag: 코드 내 참조 없음
```

---

### 2. 교통사고 분석 모듈 현황

**구현된 모듈**: `modules/traffic_accident_analyzer.py`

**데이터 소스**:
- ✅ **하드코딩된 과실비율 판정표** (코드 내 직접 정의)
- ❌ **PDF 문서 RAG 연동 없음**

**하드코딩된 데이터 예시**:
```python
def _load_fault_ratio_table(self) -> Dict:
    """과실 비율 판정 기준표 (하드코딩)"""
    return {
        "신호위반_직진충돌": {
            "가해차량": 100,
            "피해차량": 0,
            "description": "신호위반 차량이 직진 차량과 충돌"
        },
        "중앙선침범_정면충돌": {
            "가해차량": 100,
            "피해차량": 0
        },
        # ... 8개 시나리오만 정의됨
    }
```

**문제점**:
- PDF 문서에는 **수백 가지 시나리오**가 있으나, 코드에는 **8개만** 정의
- 실제 문서의 상세 기준(차선 수, 도로 유형, 시간대 등) **반영 안 됨**
- 문서 업데이트 시 코드 수동 수정 필요

---

## 🎯 통합 필요 사항

### 1. RAG 인제스트 스크립트 생성

**필요 파일**: `run_car_accident_rag_ingest.py`

**기능**:
```python
# 1. PDF 파싱 (16MB 대용량)
# 2. 페이지별 텍스트 추출
# 3. 청크 분할 (과실비율 시나리오별)
# 4. 벡터 임베딩 생성 (OpenAI/Gemini)
# 5. Supabase 저장
```

**참고 스크립트**:
- `run_fire_insurance_rag_ingest.py` (화재보험 RAG)
- `run_demographics_rag_ingest.py` (인구통계학적 지능 RAG)

---

### 2. Supabase 테이블 구조

**기존 테이블**: `gk_knowledge_base`

**필요 컬럼**:
```sql
CREATE TABLE gk_knowledge_base (
    id UUID PRIMARY KEY,
    content TEXT,                    -- 과실비율 시나리오 텍스트
    embedding VECTOR(1536),          -- 벡터 임베딩
    metadata JSONB,                  -- 메타데이터
    source_file TEXT,                -- 파일명
    page_number INTEGER,             -- 페이지 번호
    created_at TIMESTAMPTZ
);
```

**메타데이터 예시**:
```json
{
    "document_type": "traffic_accident_fault_ratio",
    "scenario_type": "신호위반_직진충돌",
    "offender_ratio": 100,
    "victim_ratio": 0,
    "road_type": "교차로",
    "lane_count": 4,
    "time_of_day": "주간"
}
```

---

### 3. Cloud Run 배포

**현황**:
- ✅ Cloud Run 환경 구축 완료
- ❌ 교통사고 RAG 엔드포인트 **미배포**

**필요 엔드포인트**:
```
POST /api/traffic-accident/analyze
- 블랙박스 영상 업로드
- RAG 기반 과실비율 검색
- 유사 판례 매칭
```

---

### 4. GCS 저장

**현황**:
- ✅ GCS 버킷 구축 완료
- ❌ 교통사고 분석 결과 **미저장**

**필요 저장 항목**:
```
gs://goldkey-traffic-accidents/
├── videos/              # 블랙박스 영상 원본
├── analysis_results/    # 분석 결과 JSON
└── reports/             # 생성된 보고서 PDF
```

---

## 🔧 통합 구현 계획

### Phase 1: RAG 인제스트 (우선순위 높음)

**작업 항목**:
1. ✅ PDF 파일 확인 (`static/230630_자동차사고 과실비율 인정기준_최종.pdf`)
2. ⏳ `run_car_accident_rag_ingest.py` 스크립트 생성
3. ⏳ PDF 파싱 및 청크 분할
4. ⏳ 벡터 임베딩 생성
5. ⏳ Supabase 저장

**예상 소요 시간**: 2-3시간

---

### Phase 2: RAG 검색 통합

**작업 항목**:
1. ⏳ `TrafficAccidentAnalyzer` 클래스에 RAG 검색 추가
2. ⏳ 하드코딩된 과실비율 테이블 → RAG 쿼리로 대체
3. ⏳ 유사 시나리오 자동 매칭
4. ⏳ 신뢰도 점수 계산

**코드 예시**:
```python
def _calculate_fault_ratio_with_rag(
    self,
    accident_scenario: str
) -> Dict:
    """RAG 기반 과실 비율 검색"""
    
    # 1. 시나리오 임베딩 생성
    query_embedding = self._generate_embedding(accident_scenario)
    
    # 2. Supabase 벡터 검색
    results = supabase.rpc(
        'match_traffic_accident_scenarios',
        {
            'query_embedding': query_embedding,
            'match_threshold': 0.8,
            'match_count': 5
        }
    ).execute()
    
    # 3. 최적 시나리오 선택
    best_match = results.data[0]
    
    return {
        "offender_ratio": best_match["metadata"]["offender_ratio"],
        "victim_ratio": best_match["metadata"]["victim_ratio"],
        "basis": best_match["content"],
        "confidence": best_match["similarity"]
    }
```

---

### Phase 3: Cloud Run 배포

**작업 항목**:
1. ⏳ FastAPI 엔드포인트 생성
2. ⏳ Dockerfile 업데이트
3. ⏳ Cloud Run 배포
4. ⏳ API 테스트

---

### Phase 4: GCS 통합

**작업 항목**:
1. ⏳ 블랙박스 영상 GCS 업로드
2. ⏳ 분석 결과 JSON 저장
3. ⏳ 보고서 PDF 생성 및 저장
4. ⏳ Signed URL 생성 (다운로드)

---

## 📊 현재 vs 통합 후 비교

| 항목 | 현재 | 통합 후 |
|------|------|---------|
| **과실비율 시나리오** | 8개 (하드코딩) | 수백 개 (PDF 전체) |
| **데이터 소스** | 코드 내 정의 | RAG 벡터 검색 |
| **업데이트 방법** | 코드 수정 | PDF 재인제스트 |
| **검색 정확도** | 정확 매칭만 | 유사도 기반 매칭 |
| **신뢰도 점수** | 없음 | 0~1 점수 제공 |
| **유사 판례** | 없음 | 상위 5개 제공 |

---

## 🎯 결론

### 현재 상태
❌ **'230630_자동차사고 과실비율 인정기준_최종.pdf' 문서는 RAG/Supabase/Cloud Run/GCS에 통합되지 않음**

**이유**:
1. RAG 인제스트 스크립트 미생성
2. Supabase 벡터 임베딩 미저장
3. `TrafficAccidentAnalyzer` 모듈이 하드코딩된 데이터만 사용
4. Cloud Run 엔드포인트 미배포
5. GCS 저장 로직 미구현

### 권장 조치
1. **즉시**: `run_car_accident_rag_ingest.py` 스크립트 생성 및 실행
2. **단기**: `TrafficAccidentAnalyzer` 모듈에 RAG 검색 통합
3. **중기**: Cloud Run 배포 및 API 엔드포인트 생성
4. **장기**: GCS 저장 및 보고서 자동 생성

---

**작성자**: Windsurf Cascade AI Assistant  
**버전**: 1.0  
**최종 업데이트**: 2026-03-31
