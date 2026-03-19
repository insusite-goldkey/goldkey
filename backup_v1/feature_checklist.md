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

## H. 카카오/SMS 발송 · PDF 다운로드 · GP200 브랜딩 (v1.4.0)

| # | 기능 | 파일 | 상태 | 비고 |
|---|------|------|------|------|
| H-1 | 카카오 알림톡 발송 (비즈메시지 API) | `modules/kakao_sender.py` | 🔧 | API 키 미설정 시 오류 안내, SMS 자동 폴백 |
| H-2 | SMS 폴백 발송 (솔라API HMAC-SHA256) | `modules/kakao_sender.py` | 🔧 | SMS_API_KEY / SMS_API_SECRET / SMS_SENDER_NUM 필요 |
| H-3 | 실제 PDF 생성 (reportlab A4) | `modules/pdf_generator.py` | 🔧 | 한글폰트(NanumGothic/맑은고딕) 자동 감지, 없으면 Helvetica |
| H-4 | PDF 다운로드 버튼 (모든 보고서 탭) | `app.py` → `_render_report_send_ui` | 🔧 | show_result() 경유, 탭별 key 자동 분리 |
| H-5 | 카카오/SMS 발송 UI (모든 보고서 탭) | `app.py` → `_render_report_send_ui` | 🔧 | t0·t1·t2·t3·cancer·brain·heart·disability·report43 등 전체 |
| H-6 | GP200 브랜딩 푸터 — PDF | `modules/pdf_generator.py` | 🔧 | 담당: {소속회사} {지점} {성명} 마스터 \| {연락처} |
| H-7 | GP200 브랜딩 푸터 — 카카오/SMS | `modules/kakao_sender.py` | 🔧 | [발송: {소속회사} {성명} 설계사] 메시지 하단 자동 삽입 |
| H-8 | GP200 사용자 정보 입력 (설정 페이지) | `app.py` (사이드바 설정) | 🔧 | 회사명 지능형 자동완성(GA/원수사 DB), 지점·성명·연락처 |
| H-9 | 내 보고서 미리보기 (설정 페이지) | `app.py` §23950 | 🔧 | PDF 리포트 + 카카오 메시지 형태 동시 미리보기 |

---

## I. 관리자 필수 설정 (Secrets / 환경변수)

| 키 이름 | 용도 | 미설정 시 동작 |
|---------|------|---------------|
| `KAKAO_API_KEY` | 카카오 알림톡 App Key | 카카오 발송 불가 → SMS 폴백 시도 |
| `KAKAO_SENDER_KEY` | 카카오 플러스친구 채널 Key | 카카오 발송 불가 |
| `KAKAO_TEMPLATE_ID` | 알림톡 템플릿 코드 | 기본값 `goldkey_report_v1` 사용 |
| `SMS_API_KEY` | 솔라API(Solapi) API Key | SMS 발송 불가 |
| `SMS_API_SECRET` | 솔라API API Secret | SMS 발송 불가 |
| `SMS_SENDER_NUM` | 사전 등록된 발신번호 | SMS 발송 불가 |

> **설정 방법**: HuggingFace Spaces → Settings → Repository secrets 에 위 키를 추가하거나,
> 로컬 개발 시 `.streamlit/secrets.toml` 에 `[default]` 섹션으로 추가.
> API 키 없이도 앱은 정상 실행됨 (발송 버튼 클릭 시 안내 메시지 표시).

---

## 점검 이력

| 날짜 | 점검자 | 주요 내용 |
|------|--------|-----------|
| 2026-02-28 | Cascade AI | 초기 점검표 작성, v1.3.0 기준 |
| 2026-03-09 | Cascade AI | v1.4.0 — kakao_sender·pdf_generator 신규, GP200 브랜딩 파이프라인, 전체 보고서 탭 발송 UI 통합 완료 |
