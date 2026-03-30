# Goldkey AI Masters 2026 — STEP 1~12 마스터플랜
**최종 확정 아키텍처 (2026-03-30)**  
**설계자 승인 필수 — 이 구조는 앱의 DNA이며 절대 변경 불가**

---

## 📋 12단계 워크플로우 전체 구조

### STEP 1: 고객 정보 동기화 (Customer Information Sync)
**접근 권한**: Basic (무료)  
**코인 차감**: 0  
**구현 위치**: HQ `hq_app_impl.py` line 12950-13001  
**기능**: 메인 파트에서 입력된 고객 정보(이름, 주민번호, 연락처, 통신사, 연령대, 성별)를 자동으로 불러오고 수정 가능

**CRM 연동**: `crm_consultation_center_block.py` — 고객 상담 센터에서 입력된 정보를 HQ로 SSO 전달

---

### STEP 2: 내보험다보여 동의 SMS 발송 (Insurance Consent SMS)
**접근 권한**: Basic (무료)  
**코인 차감**: 0  
**구현 위치**: HQ `hq_app_impl.py` line 13004-13072  
**기능**: 금융감독원 내보험다보여 개인정보 제공 동의 요청 SMS 자동 발송 (한국신용정보원 연동)

**발송 방식**:
- 📱 SMS 자동발송 (권장)
- 🔗 URL 복사 후 안내
- ✍️ 현장 서면 동의

---

### STEP 3: 보험 가입 현황 수집 & 정형화 (Policy Data Collection)
**접근 권한**: Basic (무료)  
**코인 차감**: 0  
**구현 위치**: HQ `hq_app_impl.py` line 13075-13146  
**기능**: 내보험다보여 API 연동 또는 수동 입력으로 보험 가입 현황 수집 및 담보 파싱

**입력 방식**:
- ✏️ 직접 입력
- 📋 보장 목록 붙여넣기
- 🤖 자동 수집 (내보험다보여 API)

**CRM 연동**: `crm_nibo_screen_block.py` — 내보험다보여 5단계 워크플로우

---

### STEP 4: KB 스탠다드 × 데이터 요새 교차분석 (KB Standard Analysis)
**접근 권한**: Pro (구독 활성 또는 150코인 이상)  
**코인 차감**: 3  
**구현 위치**: HQ `hq_app_impl.py` line 13149-13245  
**기능**: KB손해보험 7대 보장 분류 + KOSIS 연령별 발병 가중치 결합 분석

**분석 엔진**:
- `render_kb_standard_dashboard()` — KB 7대 스탠다드 대시보드
- `render_vascular_chart()` — 연령대별 혈관질환 발병률 추이
- `render_life_stat_dashboard()` — KOSIS 10대 사인 × 5대 암 상세 데이터

**CRM 연동**: `crm_coverage_analysis_block.py` — KB 보장 분석

---

### STEP 5: 카카오톡 알림톡 리포트 발송 (Kakao Report Delivery)
**접근 권한**: Pro  
**코인 차감**: 1  
**구현 위치**: HQ `hq_app_impl.py` line 13248-13296  
**기능**: KB 분석 결과를 카카오톡 알림톡으로 고객에게 발송

**자동 저장**:
- `trinity_engine.save_analysis_to_db()` — gk_unified_reports 테이블에 분석 결과 저장
- `upload_customer_profile_gcs()` — GCS 암호화 저장 (선택)

**CRM 연동**: `crm_kakao_share_block.py` — 카카오톡 공유 기능

---

### STEP 6: 증권/의무기록 OCR 스캔 (Document OCR Scan)
**접근 권한**: Pro  
**코인 차감**: 3  
**구현 위치**: CRM `crm_scan_block.py`  
**기능**: 보험증권, 의무기록, 진단서, 처방전 등을 Gemini Vision API로 OCR 분석

**4자 동시 연동**:
1. GCS 저장 (원본 파일 + 정밀 JSON)
2. Supabase 기록 (gk_scan_files)
3. Cloud Run 연산 (AI 분석 엔진)
4. HQ 사령부 관제 (gp193_live_context)

**HQ 연동**: `crm_hq_scan_bridge.py` — CRM→HQ 스캔 요청 전달

---

### STEP 7: 트리니티 가치 엔진 분석 (Trinity Value Analysis)
**접근 권한**: Pro  
**코인 차감**: 3  
**구현 위치**: CRM `crm_trinity_block.py`  
**기능**: 트리니티 계산법 (소득 추정 × 보장 가치 × 위험 점수) 기반 고객 가치 분석

**분석 항목**:
- 추정 소득 (건강보험료 기반)
- 보장 가치 (현재 가입 보험 총액)
- 위험 점수 (연령, 직업, 건강 상태)

---

### STEP 8: 인맥 관계망 시각화 (Network Relationship Map)
**접근 권한**: Basic  
**코인 차감**: 0  
**구현 위치**: CRM `crm_phase1_network_block.py`  
**기능**: 고객-가족-소개자 관계망을 시각적으로 표시 (D3.js 기반 네트워크 그래프)

**데이터 소스**:
- `gk_people` — 인물 본부
- `gk_relationships` — 관계망 (배우자/자녀/부모/형제/소개자/법인직원)

---

### STEP 9: 보험 계약 관리 (Insurance Contract Management)
**접근 권한**: Basic  
**코인 차감**: 0  
**구현 위치**: CRM `crm_insurance_contracts_block.py`  
**기능**: A/B/C 파트 보험 계약 CRUD (생성, 조회, 수정, 삭제)

**데이터 소스**:
- `gk_policies` — 증권 본부
- `gk_policy_roles` — 증권-인물 연결 (계약자/피보험자/수익자)

---

### STEP 10: 보험 만기 알림 자동화 (Expiry Alert Automation)
**접근 권한**: Basic  
**코인 차감**: 0  
**구현 위치**: CRM `crm_expiry_alerts_block.py`  
**기능**: 보험 만기일 30일 전 자동 알림 (SMS/카카오톡)

**스케줄링**:
- Cloud Scheduler → Cloud Function (매일 00:00 실행)
- 만기일 30일 전 회원에게 알림 발송

---

### STEP 11: 증권 해지 처리 (Policy Cancellation)
**접근 권한**: Basic  
**코인 차감**: 0  
**구현 위치**: CRM `crm_policy_cancellation_block.py`  
**기능**: 보험 증권 해지 신청 및 처리 (Soft Delete)

**처리 방식**:
- `gk_policies.is_deleted = TRUE` 설정
- 실제 데이터 삭제 금지 (감사 추적 보존)

---

### STEP 12: 데이터 요새 관리 (Data Fortress Management)
**접근 권한**: Basic  
**코인 차감**: 0  
**구현 위치**: CRM `zombie_tables_crud.py`  
**기능**: 4대 좀비 테이블 (people, relationships, policies, policy_roles) CRUD 관리

**관리 기능**:
- 인물 등록/수정/삭제
- 관계 연결/해제
- 증권 등록/수정/삭제
- 역할 할당/변경

---

## 🎯 12단계 네비게이션 UI 구조

### HQ 앱 (goldkey-ai)

```
┌─────────────────────────────────────────────────────────────────┐
│                    HQ 메인 네비게이션                            │
└─────────────────────────────────────────────────────────────────┘

📊 대시보드 (M-SECTION)
  └─ 전략 대시보드 (가족관계도, 보장공백 차트)

🔬 N-SECTION: 내보험다보여 특수작전 파트
  ├─ STEP 1: 고객 정보 동기화
  ├─ STEP 2: 내보험다보여 동의 SMS 발송
  ├─ STEP 3: 보험 가입 현황 수집 & 정형화
  ├─ STEP 4: KB 스탠다드 × 데이터 요새 교차분석 [Pro, 3코인]
  └─ STEP 5: 카카오톡 알림톡 리포트 발송 [Pro, 1코인]

🔍 GK-SEC-10: 통합 증권분석 센터
  └─ 보험증권 AI 분석 (Gemini Vision API)
```

---

### CRM 앱 (goldkey-crm)

```
┌─────────────────────────────────────────────────────────────────┐
│                    CRM 메인 네비게이션                           │
└─────────────────────────────────────────────────────────────────┘

👥 고객 목록 (Dashboard)
  └─ 고객 표 + 액션 그리드

📝 고객 상담 센터 (5:5 분할 UI)
  ├─ STEP 1: 고객 정보 입력
  ├─ STEP 2: 내보험다보여 동의 SMS
  └─ STEP 3: 보험 가입 현황 수집

🔬 분석 센터
  ├─ STEP 4: KB 보장 분석 [Pro, 3코인]
  ├─ STEP 5: 카카오톡 리포트 발송 [Pro, 1코인]
  ├─ STEP 6: OCR 스캔 분석 [Pro, 3코인]
  └─ STEP 7: 트리니티 가치 분석 [Pro, 3코인]

🗺️ 관계망 관리
  └─ STEP 8: 인맥 관계망 시각화 [Basic, 0코인]

📋 계약 관리
  ├─ STEP 9: 보험 계약 관리 [Basic, 0코인]
  ├─ STEP 10: 만기 알림 자동화 [Basic, 0코인]
  └─ STEP 11: 증권 해지 처리 [Basic, 0코인]

🏰 데이터 요새
  └─ STEP 12: 4대 테이블 관리 [Basic, 0코인]
```

---

## 🔐 권한 체크 로직 (3단계 검증)

### [1단계] 프로 등급 체크
```python
from modules.calendar_ai_helper import check_pro_tier

if not check_pro_tier(user_id):
    render_hard_lock_screen(user_id, feature_name="STEP 4: KB 분석")
    return
```

### [2단계] 코인 차감
```python
from modules.credit_manager import check_and_deduct_credit

if not check_and_deduct_credit(user_id, 3, "STEP 4: KB 분석"):
    return  # 하드 락 화면 자동 표시
```

### [3단계] 유료 회원 검증 (CRM 자동 로그인)
```python
from shared_components import verify_crm_auto_login

result = verify_crm_auto_login(contact_hash, pin)
if not result["success"]:
    st.error(result["message"])
    return
```

---

## 📊 코인 차감 규칙 요약

| STEP | 기능명 | 접근 권한 | 코인 차감 |
|------|--------|-----------|-----------|
| STEP 1 | 고객 정보 동기화 | Basic | 0 |
| STEP 2 | 내보험다보여 동의 SMS | Basic | 0 |
| STEP 3 | 보험 가입 현황 수집 | Basic | 0 |
| **STEP 4** | **KB 스탠다드 분석** | **Pro** | **3** |
| **STEP 5** | **카카오톡 리포트 발송** | **Pro** | **1** |
| **STEP 6** | **OCR 스캔 분석** | **Pro** | **3** |
| **STEP 7** | **트리니티 가치 분석** | **Pro** | **3** |
| STEP 8 | 인맥 관계망 시각화 | Basic | 0 |
| STEP 9 | 보험 계약 관리 | Basic | 0 |
| STEP 10 | 만기 알림 자동화 | Basic | 0 |
| STEP 11 | 증권 해지 처리 | Basic | 0 |
| STEP 12 | 데이터 요새 관리 | Basic | 0 |

---

## 🚀 구현 우선순위

### Phase 1: 즉시 조치 (1주일 이내)
1. ✅ 12단계 네비게이션 UI 구현 (HQ/CRM)
2. ✅ 월간 구독 자동 갱신 로직 (Lazy Evaluation)
3. ✅ 하드 락 UI 전면 통일 + 리워드 유도 버튼

### Phase 2: 단기 개선 (1개월 이내)
4. ✅ 모바일 최적화 100% 달성
5. ✅ 그리드/플로우차트 레이아웃 확대 적용

### Phase 3: 중장기 개선 (3개월 이내)
6. ✅ 코인 환불 정책 문서화 및 UI 추가
7. ✅ 분석 결과 캐싱 최적화

---

**작성일**: 2026-03-30 09:12 KST  
**설계자**: Goldkey AI Masters 2026 Team  
**승인 상태**: 최종 확정 ✅
