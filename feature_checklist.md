# Goldkey AI Master Lab. — 전체 기능 점검표
> 버전: v1.3.0 | 최종 점검일: 2026-02-28

## 범례
| 아이콘 | 상태 |
|--------|------|
| ✅ | 정상 작동 |
| ⚠️ | 부분 작동 / 제약 있음 |
| ❌ | 미작동 / 미구현 |
| 🔧 | 수정 완료 (이번 세션) |
| 🚧 | 개발 예정 |

---

## A. Smart Analysis & Hub

| # | 기능 | 탭 ID | 상태 | 비고 |
|---|------|--------|------|------|
| A-1 | 보험증권 분석 (AI Vision) | `policy_scan` | ✅ | Gemini Vision 기반, 텍스트·스캔 PDF 모두 지원 |
| A-2 | 보험증권 PDF 텍스트 추출 | `policy_scan` | ⚠️ | pypdf 기반 — 이미지 스캔 PDF는 Vision fallback |
| A-3 | 이미지 전처리 (이진화·투영변환) | `policy_scan` | 🔧 | policy_ocr_engine.py 신규 구현 (OpenCV, graceful) |
| A-4 | OCR 오타 퍼지 교정 | `policy_scan` | 🔧 | rapidfuzz 기반, 보험 도메인 사전 82종 |
| A-5 | 개인정보 마스킹 (주민번호·전화번호) | `policy_scan` | 🔧 | OCR 텍스트 즉시 마스킹, 엔진 단 처리 |
| A-6 | 담보명 표준화 (Fuzzy STD 매핑) | `policy_scan` | ✅ | _STD_NAME_MAP 10종 + rapidfuzz 교정 |
| A-7 | SSOT 스캔허브 연동 | `policy_scan` | ✅ | ssot_full_text / ssot_coverages 경로 |
| A-8 | 상품별 전용 AI 프롬프트 | `policy_scan` | ✅ | 운전자/암/치매간병/실손/뇌심장 5종 분기 |
| A-9 | JSON 파싱 (중첩 중괄호 안전) | `policy_scan` | ✅ | 깊이 카운팅 + fallback 2단계 |
| A-10 | 디지털 카탈로그 관리 | `catalog` | ❌ | Hybrid RAG 백엔드 미연동 → 🚧 별도 서버 필요 |
| A-11 | 개인문서 RAG | `rag_personal` | ❌ | HYBRID_BACKEND_URL 미설정 시 전혀 작동 안 함 → 🚧 |
| A-12 | 이미지 분석 탭 | `img` | 🔧 | _auth_gate 추가 완료 |
| A-13 | 대용량 PDF (10MB+) | `policy_scan` | ⚠️ | HF Spaces 메모리 512MB 한계 — 8페이지 상한 적용 |

---

## B. Expert Consulting

| # | 기능 | 탭 ID | 상태 | 비고 |
|---|------|--------|------|------|
| B-1 | 신규보험 상품 상담 | `t0` | ✅ | _auth_gate + ai_query_block |
| B-2 | 보험금 상담·민원·손해사정 | `t1` | ✅ | |
| B-3 | 기본보험 상담 | `t2` | ✅ | |
| B-4 | 통합보험 설계 | `t3` | ✅ | |
| B-5 | 암·뇌·심장 중증질환 상담 | `cancer` | ✅ | |
| B-6 | 뇌질환 전용 상담 | `brain` | ✅ | |
| B-7 | 심장질환 전용 상담 | `heart` | ✅ | |
| B-8 | 상해 통합 관리 (LCRM) | `injury` | ✅ | |
| B-9 | 장해보험금 산출 | `disability` | ✅ | _auth_gate 누락 확인 필요 |
| B-10 | 자동차사고 상담·과실비율 | `t4` | ✅ | |

---

## C. Wealth & Corporate

| # | 기능 | 탭 ID | 상태 | 비고 |
|---|------|--------|------|------|
| C-1 | 노후설계·연금 3층·상속·증여 | `t5` | ✅ | |
| C-2 | 세무상담 | `t6` | ✅ | |
| C-3 | 법인상담 (CEO플랜·단체·기업) | `t7` | ✅ | |
| C-4 | CEO플랜 (비상장주식 약식 평가) | `t8` | ✅ | |
| C-5 | 화재보험 재조달가액 산출 | `fire` | 🔧 | product_key 누락 수정 완료 |
| C-6 | 배상책임보험 상담 | `liability` | ✅ | |

---

## D. Life & Care

| # | 기능 | 탭 ID | 상태 | 비고 |
|---|------|--------|------|------|
| D-1 | 고객 관리 탭 | `customer_mgmt` | 🔧 | Supabase 연결 실패 시 st.stop → st.error 개선 |
| D-2 | CRM sync 타이밍 | `customer_mgmt` | ⚠️ | 등록 직후 rerun 전 데이터 유실 가능 — 모니터링 필요 |
| D-3 | 고객자료 통합저장 (개인문서 RAG) | — | ❌ | Hybrid RAG 미완성 → 🚧 |

---

## E. 공통 인프라·UX

| # | 기능 | 상태 | 비고 |
|---|------|------|------|
| E-1 | 앱 버전 태그 | 🔧 | 사이드바 v1.3.0 뱃지 추가 완료 |
| E-2 | _auth_gate 전체 탭 적용 | ✅ (일부 ⚠️) | img탭 누락 수정 완료, disability 탭 확인 필요 |
| E-3 | STT 지연 초기화 | ⚠️ | 홈 렌더 후 지연 초기화 — 첫 탭 진입 시 미초기화 가능 |
| E-4 | load_stt_engine 타이밍 | ⚠️ | home_rendered + _rag_sync_done 플래그로 1회만 sync |
| E-5 | 업로드 파일 메모리 임시 저장 | ⚠️ | HF Spaces 재시작 시 소실 — 현재 구조상 불가피 |
| E-6 | HYBRID_BACKEND_URL 미설정 | ❌ | FastAPI 백엔드 미연결 — RAG 기능 전체 비활성화 |
| E-7 | 빈 페이지 방지 | ⚠️ | 미구현 기능 준비중 안내 필요 — 점검 예정 |
| E-8 | 전역 CSS (WCAG 2.1 AA) | ✅ | #0ea5e9 대비비 5.2:1, 최소 16px, 44dp 터치타겟 |
| E-9 | 사이드바 메뉴 버튼 반응 | ✅ | lazy-dispatch 구조 — st.stop() 정상 처리 |

---

## F. OCR 후처리 엔진 (신규, v1.3.0)

| # | 기능 | 파일 | 상태 | 비고 |
|---|------|------|------|------|
| F-1 | 이미지 전처리 (CLAHE·이진화·블러) | `policy_ocr_engine.py` | 🔧 | OpenCV 미설치 시 graceful 비활성 |
| F-2 | 투영 변환 (기울어진 문서 보정) | `policy_ocr_engine.py` | 🔧 | 4꼭짓점 자동 검출, 30% 이상일 때만 적용 |
| F-3 | 개인정보 마스킹 (주민번호·전화) | `policy_ocr_engine.py` | 🔧 | OCR raw text → 즉시 마스킹 |
| F-4 | 날짜 정규화 (YYYY-MM-DD) | `policy_ocr_engine.py` | 🔧 | YYYY.MM.DD / YY년MM월DD일 패턴 |
| F-5 | 금액 정규화 | `policy_ocr_engine.py` | 🔧 | 콤마 오인식 / '만 원' 공백 제거 |
| F-6 | 도메인 사전 교정 (82종) | `policy_ocr_engine.py` | 🔧 | 완전 일치 → 부분 포함 → 퍼지 매칭 3단계 |
| F-7 | 퍼지 매칭 (rapidfuzz, 82% 임계값) | `policy_ocr_engine.py` | 🔧 | rapidfuzz 미설치 시 fuzzywuzzy fallback |

---

## G. 알려진 구조적 제약 (현 아키텍처에서 해결 불가)

| # | 항목 | 설명 |
|---|------|------|
| G-1 | Hybrid RAG 백엔드 | FastAPI 별도 서버 필요 — HF Spaces 단독 배포 구조에서 미연결 |
| G-2 | LayoutLM 기반 위치 분석 | GPU 서버 필요 — 현재 CPU-only HF Spaces에서 실행 불가 |
| G-3 | CLOVA OCR 연동 | Naver API 키 + 전용 계약 필요 — 현재 Gemini Vision으로 대체 운영 |
| G-4 | 파일 영구 저장 | HF Spaces 재시작 시 tmp 소실 — Supabase Storage 연동 필요 |

---

## 점검 이력

| 날짜 | 점검자 | 주요 내용 |
|------|--------|-----------|
| 2026-02-28 | Cascade AI | 초기 점검표 작성, v1.3.0 기준 |
