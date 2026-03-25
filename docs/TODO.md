# 💎 Goldkey AI Masters 2026: 개발 로드맵 (Master Task Tracker)

> **규칙:**
> 1. 모든 작업 시작 전 이 파일을 읽고 진행 상황을 업데이트한다.
> 2. `[ ]` 미완료, `[working]` 진행중, `[x]` 완료로 표시한다.
> 3. 한 번에 하나의 태스크만 수행하며, 완료 후 설계자의 승인을 받는다.

---

## 🏗️ Phase 1: 시스템 아키텍처 혁신 (블록화)

- [x] `blocks/` 폴더 생성 및 UI 컴포넌트 분리 (Decoupling) — *2026-03-23: `blocks/*.py` 8모듈, `crm_app`에서 트리니티·내보·증권분석·네비·액션그리드·상담센터·스캔브리지 연결 검수 완료*
- [x] `app.py` & `crm_app.py`를 렌더링 껍데기로 단순화 — *2026-03-24: 진입점만 유지, 본문은 `hq_app_impl.py` / `crm_app_impl.py`; rerun 시 `importlib.reload` 단일 실행*
- [ ] `rules.json` 기반의 설정 중심 UI (Config-driven) 구축 (GP-44)

## 🎙️ Phase 2: 전역 AI 음성 및 지능형 브리핑

- [ ] `shared_components.py` 내 Gemini Pro TTS (Zephyr, Korean) 통합 엔진 구축
- [ ] 기기 위도/경도 기반 날씨/뉴스 모닝 브리핑 로직 정정
- [ ] 전역 텍스트 한국어 정규화 및 인코딩 오류(깨짐) 수정

## 📱 Phase 3: CRM UI/UX 리모델링

- [ ] 로그인 랜딩 페이지를 '메인 대시보드(달력)'로 변경
- [ ] 수직 액션 버튼 삭제 및 달력 하단 '수평 반응형 그리드' 이전 설치
- [ ] 유동적 타이포그래피(clamp) 및 반응형 박스 모델 전역 적용
- [ ] '메인 대시보드' ↔ '고객상세화면' 왕복 네비게이션 버튼 설치

## ⚖️ Phase 4: 상담 센터(Consultation Center) 5:5 복원

- [ ] 화면 중앙 5:5 분할 레이아웃 구현
- [ ] **좌측:** 건보료 입력, 트리니티/Nibo 연동, 증권 스캔 팝업(5줄+스크롤)
- [ ] **우측:** 'AI 증권분석 보고서' (트리니티 산출 박스 + AI 분석 박스, 각 5줄+스크롤)
- [ ] 최하단 AI 피드백 블록 이동 및 `[HQ] 앱 이동` 액션 모듈 설치

---

**마지막 업데이트:** 2026-03-24

**현재 집중 작업:** `[승인 대기]` 전 시스템 가동 1분컷 체크 완료 — Cloud Run 필수 ENV 일부 누락(HEAD_API_USER_ID/CORS/HEAD_API_URL), Supabase 키 401 지속으로 Green Light 보류

**진행률 (Phase 1 전체):** 약 **66%** (3개 중 2개 완료)

---

### HEAD API (1단계 완료 요약)

| 항목 | 내용 |
|------|------|
| 폴더 | `head_api/` — `main.py`, `routers/trinity.py` |
| 엔드포인트 | `POST /api/v1/analyze/trinity`, `GET /health` |
| HQ 연동 | `head_api_client.fetch_trinity_metrics` — `hq_app_impl.py` 통합 갭 분석 트리니티 카드 |
| 환경변수 | `HEAD_API_URL` (기본 `http://127.0.0.1:8800`), `HEAD_API_LOCAL_FALLBACK` (개발 폴백) |
| 실행 | `uvicorn head_api.main:app --host 0.0.0.0 --port 8800` (프로젝트 루트에서) |
