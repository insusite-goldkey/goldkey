# Windsurf → Cursor 인수인계 보고서

> **저장 위치:** `d:\CascadeProjects\docs\CURSOR_HANDOVER_REPORT.md`  
> **목적:** Windsurf에서 나온 산출물을 Cursor·레포 기준으로 **무엇을 어떻게 넘길지** 고정한다.  
> **한 줄 요약:** *대화가 아니라 레포에 남는 산출물이 인수인계다.*

---

## 1. 반드시 넘겨야 할 것

| 항목 | 설명 |
|------|------|
| **소스 코드** | 수정한 `.py` 등 — 저장 후 **Git 커밋·push가 곧 인계** |
| **신규 파일** | 새 모듈·스크립트·설정 — **레포 경로에 존재**해야 Cursor가 인식 |
| **GP·제품 문서** | 조항 요약·페르소나·아키텍처 — **`docs/*.md`에 반영** |
| **배포 메모** | 서비스명·리전·환경변수 **이름**(값은 비밀 제외) — 아래 §7·`deploy/`와 연동 |

---

## 2. 함께 넘기면 좋은 메타

| 항목 | 기록 위치 |
|------|-----------|
| 의도 한 줄 | 커밋 메시지 첫 줄 |
| 영향 범위 (HQ / CRM / 공통) | 커밋 본문 또는 `docs/` |
| 금지 사항 (건드리지 말 폴더 등) | `docs/DESIGNER_WORKFLOW.md` |
| 알려진 이슈 | 동일 또는 Issue |

---

## 3. Windsurf에만 있으면 위험한 것

| 위험 | 대응 |
|------|------|
| **채팅 요약만** | `docs/`에 옮기지 않으면 다음 세션에서 소실 |
| **라인 번호만 적은 GP 표** | `app.py`가 크므로 **조항 ID + 파일명 + 함수명**으로 재기술 |
| **민감 값** | Git 금지 — **환경변수 이름**만 문서화, 값은 Secret Manager |

---

## 4. 있으면 Cursor가 빨라지는 것

- 다이어그램 (배포·CRM↔HQ)
- 에러 로그 스니펫 (Cloud Build / Run)
- 테스트 기대값 — 예: 루트 `hq_crm_smoke_test.py`, `ERROR_LOG.md`(있는 경우)

---

## 5. 실제 전달 방법 (우선순위)

1. **Git push** — 최우선  
2. **`docs/`에 `.md` 저장** — 문서·결정만 있을 때  
3. **채팅 붙여넣기** — 최후 수단 (레포에 안 남으면 재현 어려움)

---

## 6. 배포 정보 (Cursor 참고용 · 이름만)

> 실제 값은 로컬·Secret Manager·Cloud Run 콘솔. 여기서는 **이름·구조**만 고정.

| 항목 | 값 (예시·스크립트 기준) |
|------|-------------------------|
| GCP 프로젝트 | `gen-lang-client-0777682955` (환경에 따라 변경 가능) |
| 리전 | `asia-northeast3` |
| Artifact Registry | `goldkey-run` |
| Cloud Run 서비스 (HQ) | `goldkey-ai` |
| Cloud Run 서비스 (CRM) | `goldkey-crm` |
| 공개 URL (예시) | `HQ_APP_URL`, `CRM_APP_URL` — `deploy/gcloud-run-deploy.sh` 참조 |
| 환경변수 이름 (배포 시 자주 사용) | `HQ_APP_URL`, `CRM_APP_URL`, `HQ_API_URL`(CRM), `GK_ANALYSIS_BRIDGE_SECRET` |
| Docker | `Dockerfile`(HQ), `Dockerfile.crm`(CRM), `deploy/cloudbuild-hq.yaml`, `deploy/cloudbuild-crm.yaml` |

상세 명령은 `deploy/gcloud-run-deploy.sh`를 SSOT로 본다.

---

## 7. 한 줄 요약 (재확인)

**대화가 아니라 레포에 남는 산출물**이 Windsurf → Cursor 인수인계의 본체다.

---

## 8. 이후 추가 패턴 (누적할 파일)

신규 Windsurf 산출·결정은 아래 **네 축**에 나누어 누적한다.

| 파일 | 누적 내용 |
|------|-----------|
| `docs/GOLDKEY_DESIGNER_CONTEXT.md` | 페르소나·아키텍처·폴더 구조 SSOT |
| `docs/DESIGNER_WORKFLOW.md` | 작업 제약·체크리스트·이슈 |
| **`docs/CURSOR_HANDOVER_REPORT.md`** (본 문서) | 인계 기준·방법론·배포 이름 고정 |
| `Constitution.md` | GP 전 조항 원문 (조항 추가·개정 시) |

보조: `.cursor/rules/goldkey-ai-masters.mdc` — Cursor AI 행동 힌트 변경 시만 수정.

---

## docs/ 역할 분담 (현재)

| 파일 | 역할 |
|------|------|
| `GOLDKEY_DESIGNER_CONTEXT.md` | 페르소나·아키텍처·파일 구조 SSOT |
| `DESIGNER_WORKFLOW.md` | 작업 제약·체크리스트·Windsurf/Cursor 협업 |
| **`CURSOR_HANDOVER_REPORT.md`** | Windsurf→Cursor 인계 기준·방법론·배포 참조 |
| `Constitution.md`(루트) | GP 전 조항 원문 |
| `.cursor/rules/goldkey-ai-masters.mdc` | Cursor AI 행동 힌트 |

**다음 Git push 시 본 파일을 함께 커밋**하면 Cursor 및 다른 클론에서 즉시 참조 가능하다.

---

*기준일: 2026-03-24*
