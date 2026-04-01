# ══════════════════════════════════════════════════════════════════════════════
# [GP-CORE-PROTOCOL] 25개 핵심 분류 체계 통합 가이드
# ══════════════════════════════════════════════════════════════════════════════
# 작성일: 2026-04-01
# 목적: 4대 프로토콜 기반 25개 섹터 체계를 기존 시스템에 통합하는 단계별 가이드
# ══════════════════════════════════════════════════════════════════════════════

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [STEP 1: 데이터 레이어 매핑](#step-1-데이터-레이어-매핑)
3. [STEP 2: hq_app_impl.py 통합](#step-2-hq_app_implpy-통합)
4. [STEP 3: 직업-섹터 자동 매핑](#step-3-직업-섹터-자동-매핑)
5. [STEP 4: GCS 경로 재편](#step-4-gcs-경로-재편)
6. [STEP 5: RAG 지식 베이스 확장](#step-5-rag-지식-베이스-확장)
7. [검증 체크리스트](#검증-체크리스트)

---

## 🏗️ 아키텍처 개요

### 4대 상위 프로토콜 (CORE PROTOCOLS)

```
🛡️ PSP (Personal Security Protocol) — 인적 보안 프로토콜
   └─ 10개 섹터: 암, 뇌혈관, 심장질환, 실손의료비, 수술/입원, 치매/간병, 치아, 종신/정기, 연금, 상해/레저

🏛️ APP (Asset Protection Protocol) — 자산 보호 프로토콜
   └─ 6개 섹터: 자동차, 운전자, 주택화재, 개인공장화재, 법인공장화재, 상가화재

⚖️ BRP (Business Risk Protocol) — 비즈니스 리스크 프로토콜
   └─ 5개 섹터: PL(제조물책임), 전문직배상책임, 단체보험, 근로자재해, 법인전환리스크

💎 WOP (Wealth Optimization Protocol) — 부의 이전 및 최적화 프로토콜
   └─ 4개 섹터: CEO플랜, 상속세/증여세, 가업승계, 비상장주식평가
```

### 핵심 파일 구조

```
d:\CascadeProjects\
├── GP_CORE_PROTOCOL_TAXONOMY.py        # 25개 섹터 정의 (마스터 파일)
├── GP_JOB_SECTOR_MAPPING.py            # 직업-섹터 자동 매핑 로직
├── hq_app_impl.py                      # HQ 앱 구현체 (통합 대상)
├── crm_app_impl.py                     # CRM 앱 구현체
├── db_utils.py                         # GCS 경로 재편 대상
└── hq_backend/
    └── knowledge_base/
        └── schema/
            └── gk_knowledge_base.sql   # RAG 카테고리 확장 대상
```

---

## 🔧 STEP 1: 데이터 레이어 매핑

### 1.1 기존 시스템과의 매핑 관계

| 기존 시스템 | CORE PROTOCOL | 비고 |
|------------|---------------|------|
| `_WAR_ROOM_CATEGORIES` (5개) | `CORE_SECTORS` (25개) | 확장 필요 |
| `war_room_key` | `sector_id` + `war_room_key` | 호환 레이어 유지 |
| 직업 분류 (`_JOB_TREE_DB`) | `_JOB_SECTOR_MAPPING` | 신규 매핑 테이블 |
| GCS 경로 (평면 구조) | 4대 프로토콜 계층 구조 | 재편 필요 |

### 1.2 논리적 분리 원칙

```python
# ❌ 기존 방식 (내부 코드 = 사용자 UI)
_WAR_ROOM_CATEGORIES = [
    {"key": "cancer", "label": "🎗️ 암", ...}
]

# ✅ 신규 방식 (논리적 분리)
# 내부 코드: CORE_SECTORS (sector_id = "PSP-01")
# 사용자 UI: "🛡️ 인적 보안 프로토콜 > 🎗️ 암"
# 호환 레이어: war_room_key = "cancer"
```

---

## 🔌 STEP 2: hq_app_impl.py 통합

### 2.1 임포트 추가

**위치**: `hq_app_impl.py` 상단 (line ~50)

```python
# ══════════════════════════════════════════════════════════════════════════════
# [GP-CORE-PROTOCOL] 25개 핵심 분류 체계 임포트
# ══════════════════════════════════════════════════════════════════════════════
from GP_CORE_PROTOCOL_TAXONOMY import (
    CORE_PROTOCOLS,
    CORE_SECTORS,
    get_protocol_by_id,
    get_sector_by_id,
    get_sectors_by_protocol,
    get_sector_by_war_room_key,
    generate_war_room_categories,
    generate_gcs_path,
)

from GP_JOB_SECTOR_MAPPING import (
    recommend_sectors_by_job,
    get_sector_priority_by_customer,
)
```

### 2.2 _WAR_ROOM_CATEGORIES 교체

**위치**: `hq_app_impl.py` line 10453

```python
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [기존 코드 - 주석 처리 또는 삭제]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# _WAR_ROOM_CATEGORIES: list[dict] = [
#     {"key": "cancer",     "label": "🎗️ 암",      "color": "#dc2626", "bg": "#fff1f2"},
#     {"key": "integrated", "label": "🛡️ 통합",    "color": "#7c3aed", "bg": "#f5f3ff"},
#     {"key": "pension",    "label": "💰 연금",     "color": "#d97706", "bg": "#fffbeb"},
#     {"key": "driver",     "label": "🚗 운전자",   "color": "#0369a1", "bg": "#f0f9ff"},
#     {"key": "auto",       "label": "🚙 자동차",   "color": "#065f46", "bg": "#f0fdf4"},
# ]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# [신규 코드 - CORE_PROTOCOL 기반 동적 생성]
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
_WAR_ROOM_CATEGORIES: list[dict] = generate_war_room_categories()
```

### 2.3 섹터별 거절 처리 스크립트 확장

**위치**: `hq_app_impl.py` line 10461

```python
_WAR_ROOM_REJECT_MAP: dict = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [PSP] 인적 보안 프로토콜
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "cancer":     ["암보험 가격이 너무 비싸요", "암은 내 가족에 없어요", "나는 건강해요"],
    "brain":      ["뇌질환은 나이 들어서 걱정하면 돼요", "가족력 없어요", "건강검진 이상 없어요"],
    "heart":      ["심장은 괜찮아요", "운동 열심히 해요", "혈압 정상이에요"],
    "medical":    ["실손은 이미 있어요", "중복 가입 안 돼요", "보험료 아까워요"],
    "surgery":    ["수술 안 받을 거예요", "건강해요", "필요 없을 것 같아요"],
    "dementia":   ["아직 젊어요", "치매는 나중 문제예요", "가족이 돌봐줄 거예요"],
    "dental":     ["치아는 관리 잘해요", "임플란트 비싸요", "필요 없어요"],
    "life":       ["사망보험은 무서워요", "아직 젊어요", "필요성 못 느껴요"],
    "pension":    ["국민연금 있잖아요", "나중에 생각할게요", "지금은 여유가 없어요"],
    "accident":   ["사고 안 나요", "조심해요", "필요 없을 것 같아요"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [APP] 자산 보호 프로토콜
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "auto":       ["사고 안 나요", "보험료 아깝다", "필요없을 것 같아요"],
    "driver":     ["사고 안 나요", "운전 잘해요", "자동차보험 있잖아요"],
    "home_fire":  ["화재 안 나요", "아파트는 안전해요", "보험료 아까워요"],
    "personal_factory": ["공장 화재 안 나요", "소방시설 잘 되어 있어요", "보험료 비싸요"],
    "corp_factory": ["법인 화재보험 비싸요", "화재 안 나요", "소방시설 완비했어요"],
    "commercial_fire": ["상가 화재 안 나요", "관리 잘해요", "보험료 부담돼요"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [BRP] 비즈니스 리스크 프로토콜
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "pl":         ["제품 결함 없어요", "PL 사고 안 나요", "보험료 비싸요"],
    "professional": ["배상 사고 안 나요", "전문직 보험 비싸요", "필요 없어요"],
    "group":      ["단체보험 비용 부담돼요", "직원들 반발해요", "나중에 할게요"],
    "workers_comp": ["산재보험 있잖아요", "사고 안 나요", "비용 부담돼요"],
    "corp_conversion": ["법인 전환 안 해요", "개인사업자로 충분해요", "세금 더 나올 것 같아요"],
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [WOP] 부의 이전 및 최적화 프로토콜
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    "ceo_plan":   ["CEO 플랜 비싸요", "나중에 할게요", "필요성 못 느껴요"],
    "inheritance_tax": ["상속세 걱정 안 해요", "재산 많지 않아요", "나중에 생각할게요"],
    "succession": ["가업승계 아직 멀었어요", "자녀가 안 물려받을 거예요", "비용 부담돼요"],
    "stock_valuation": ["비상장주식 없어요", "평가 필요 없어요", "비용 아까워요"],
}
```

---

## 🎯 STEP 3: 직업-섹터 자동 매핑

### 3.1 고객 정보 입력 시 섹터 자동 추천

**위치**: `hq_app_impl.py` 또는 `crm_app_impl.py` 고객 정보 입력 폼

```python
# 고객 직업 입력 후 섹터 자동 추천
if customer_job:
    # 직업 정보 조회 (기존 _JOB_TREE_DB에서)
    job_info = get_job_info_from_tree(customer_job)  # 기존 함수 활용
    
    # 섹터 추천
    recommended_sectors = recommend_sectors_by_job(
        job_name=customer_job,
        job_grade=job_info.get("grade") if job_info else None,
        job_flags=job_info.get("flags") if job_info else None,
        top_k=5,
    )
    
    # UI 표시
    if recommended_sectors:
        st.info("💡 **추천 상담 섹터** (직업 기반 자동 분석)")
        for idx, rec in enumerate(recommended_sectors, 1):
            sector = get_sector_by_war_room_key(rec["sector_key"])
            if sector:
                st.markdown(
                    f"{idx}. {sector['icon']} **{sector['sector_name']}** "
                    f"(점수: {rec['score']:.0f}, {rec['reason']})"
                )
```

### 3.2 고객 프로필 기반 섹터 우선순위

```python
# 고객 상세 정보 기반 섹터 우선순위
priority_sectors = get_sector_priority_by_customer(
    job=customer_job,
    age=customer_age,
    is_ceo=customer_is_ceo,
    has_factory=customer_has_factory,
    has_commercial=customer_has_commercial,
)

# 세션 상태에 저장
st.session_state["customer_priority_sectors"] = priority_sectors
```

---

## 📁 STEP 4: GCS 경로 재편

### 4.1 기존 GCS 경로 구조

```
# 기존 (평면 구조)
encrypted_profiles/{agent_id}/{person_id}_profile.enc
reports/{agent_id}/{person_id}/report_20260401.pdf
```

### 4.2 신규 GCS 경로 구조 (4대 프로토콜 기반)

```
# 신규 (계층 구조)
PSP/PSP-01/{agent_id}/{person_id}/report/cancer_analysis_20260401.pdf
APP/APP-05/{agent_id}/{person_id}/policy/factory_fire_policy.pdf
BRP/BRP-01/{agent_id}/{person_id}/consultation/pl_consultation_20260401.pdf
WOP/WOP-01/{agent_id}/{person_id}/analysis/ceo_plan_analysis_20260401.pdf
```

### 4.3 db_utils.py 수정

**위치**: `db_utils.py` GCS 업로드 함수

```python
from GP_CORE_PROTOCOL_TAXONOMY import generate_gcs_path

def upload_sector_report_gcs(
    protocol_id: str,
    sector_id: str,
    agent_id: str,
    person_id: str,
    file_type: str,
    file_content: bytes,
    filename: str,
) -> dict:
    """
    4대 프로토콜 기반 GCS 업로드
    
    Args:
        protocol_id: 프로토콜 ID (PSP, APP, BRP, WOP)
        sector_id: 섹터 ID (PSP-01, APP-05 등)
        agent_id: 설계사 ID
        person_id: 고객 ID
        file_type: 파일 유형 (report, policy, analysis, consultation)
        file_content: 파일 내용 (바이트)
        filename: 파일명
    
    Returns:
        {"success": True, "gcs_path": "...", "public_url": "..."}
    """
    # GCS 경로 생성
    gcs_path = generate_gcs_path(
        protocol_id=protocol_id,
        sector_id=sector_id,
        agent_id=agent_id,
        person_id=person_id,
        file_type=file_type,
        filename=filename,
    )
    
    # GCS 업로드 (기존 로직 활용)
    try:
        bucket = storage.Client().bucket(_GCS_BUCKET_NAME)
        blob = bucket.blob(gcs_path)
        blob.upload_from_string(file_content)
        
        return {
            "success": True,
            "gcs_path": gcs_path,
            "public_url": blob.public_url if blob.public else None,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## 📚 STEP 5: RAG 지식 베이스 확장

### 5.1 document_category 확장

**위치**: `hq_backend/knowledge_base/schema/gk_knowledge_base.sql`

```sql
-- 기존 카테고리 예시
-- "법인컨설팅", "화재보험", "배상책임"

-- 신규 카테고리 (25개 섹터 기반)
-- PSP 프로토콜
INSERT INTO gk_knowledge_base (document_name, document_category, ...) VALUES
('암보험_약관_요약.pdf', 'PSP-01-암', ...),
('뇌혈관질환_가이드.pdf', 'PSP-02-뇌혈관', ...),
('심장질환_상담_매뉴얼.pdf', 'PSP-03-심장질환', ...),
...

-- APP 프로토콜
('법인공장화재_실무.pdf', 'APP-05-법인공장화재', ...),
('상가화재_특약_가이드.pdf', 'APP-06-상가화재', ...),
...

-- BRP 프로토콜
('PL보험_실무_가이드.pdf', 'BRP-01-PL보험', ...),
('단체보험_설계_매뉴얼.pdf', 'BRP-03-단체보험', ...),
...

-- WOP 프로토콜
('CEO플랜_세무_가이드.pdf', 'WOP-01-CEO플랜', ...),
('가업승계_실무.pdf', 'WOP-03-가업승계', ...),
...
```

### 5.2 RAG 검색 시 섹터 필터링

```python
# 섹터별 RAG 검색
def search_sector_knowledge(sector_id: str, query: str, top_k: int = 5):
    """섹터 ID 기반 RAG 지식 검색"""
    sector = get_sector_by_id(sector_id)
    if not sector:
        return []
    
    # document_category 필터링
    category_filter = f"{sector_id}-{sector['sector_name']}"
    
    # Supabase RAG 검색 (기존 함수 활용)
    results = supabase.rpc(
        "search_knowledge_base",
        {
            "query_embedding": get_embedding(query),
            "filter_category": category_filter,
            "match_count": top_k,
        }
    ).execute()
    
    return results.data
```

---

## ✅ 검증 체크리스트

### Phase 1: 기본 통합 (필수)

- [ ] `GP_CORE_PROTOCOL_TAXONOMY.py` 검증 통과 (25개 섹터 확인)
- [ ] `GP_JOB_SECTOR_MAPPING.py` 테스트 통과
- [ ] `hq_app_impl.py`에 임포트 추가 완료
- [ ] `_WAR_ROOM_CATEGORIES` 동적 생성으로 교체 완료
- [ ] 기존 5개 섹터 정상 작동 확인 (암, 통합, 연금, 운전자, 자동차)

### Phase 2: 섹터 확장 (중요)

- [ ] 20개 신규 섹터 거절 처리 스크립트 추가 완료
- [ ] 각 섹터별 AI 프롬프트 상수 추가 (선택)
- [ ] War Room UI에서 25개 섹터 정상 표시 확인
- [ ] 섹터 선택 시 해당 섹터 스크립트 정상 호출 확인

### Phase 3: 직업-섹터 매핑 (중요)

- [ ] 고객 직업 입력 시 섹터 자동 추천 UI 구현
- [ ] 추천 섹터 클릭 시 해당 섹터로 자동 이동 구현
- [ ] 고객 프로필 기반 섹터 우선순위 세션 저장 확인

### Phase 4: GCS 재편 (선택)

- [ ] `generate_gcs_path()` 함수 통합 완료
- [ ] 신규 업로드 파일 4대 프로토콜 경로로 저장 확인
- [ ] 기존 파일 마이그레이션 계획 수립 (선택)

### Phase 5: RAG 확장 (선택)

- [ ] `gk_knowledge_base` 테이블에 25개 섹터 카테고리 추가
- [ ] 각 섹터별 최소 5개 이상 PDF 문서 인제스트
- [ ] 섹터별 RAG 검색 정상 작동 확인

---

## 🚀 배포 전 최종 점검

### 1. Python 구문 검사

```powershell
python -c "import ast; src=open('d:/CascadeProjects/hq_app_impl.py', encoding='utf-8-sig').read(); ast.parse(src); print('SYNTAX OK')"
```

### 2. 통합 테스트

```python
# hq_app_impl.py 최상단에 추가 (임시 테스트)
if __name__ == "__main__":
    print("=" * 80)
    print("[GP-CORE-PROTOCOL] 통합 테스트")
    print("=" * 80)
    
    # 1. War Room 카테고리 생성 확인
    cats = generate_war_room_categories()
    print(f"\n✅ War Room 카테고리 생성: {len(cats)}개")
    
    # 2. 직업-섹터 매핑 확인
    recs = recommend_sectors_by_job("제조업 대표", job_grade=1, top_k=5)
    print(f"\n✅ 직업-섹터 매핑: {len(recs)}개 추천")
    
    # 3. GCS 경로 생성 확인
    path = generate_gcs_path("PSP", "PSP-01", "agent_123", "person_456", "report", "test.pdf")
    print(f"\n✅ GCS 경로 생성: {path}")
    
    print("\n" + "=" * 80)
    print("통합 테스트 완료")
    print("=" * 80)
```

### 3. 배포

```powershell
# HQ 배포
powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\backup_and_push.ps1"

# CRM 배포 (필요 시)
powershell -ExecutionPolicy Bypass -File "D:\CascadeProjects\deploy_crm.ps1"
```

---

## 📞 문의 및 지원

**작성자**: Windsurf Cascade AI Assistant  
**작성일**: 2026-04-01  
**버전**: v1.0

**관련 파일**:
- `GP_CORE_PROTOCOL_TAXONOMY.py` - 25개 섹터 정의
- `GP_JOB_SECTOR_MAPPING.py` - 직업-섹터 매핑
- `hq_app_impl.py` - HQ 앱 통합 대상
- `db_utils.py` - GCS 경로 재편 대상

**참고 문서**:
- `Constitution.md` - GP 가이딩 프로토콜
- `.windsurfrules` - 코어 룰
- `GP_CORE_RULES.md` - 4대 코어 룰

---

**END OF DOCUMENT**
