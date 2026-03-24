# 설계자 워크플로 — Windsurf · Cursor · Git

**관련:** 인수인계 기준·배포 이름 요약은 **`CURSOR_HANDOVER_REPORT.md`** 참고.

## 1. Cursor가 설계 의도를 “충분히” 이해하려면

- **의도는 코드 + Git + 문서** 세 가지가 맞을 때 가장 정확합니다. 채팅만으로 전달한 내용은 **세션마다 휘발**될 수 있습니다.
- 따라서 아래를 **레포에 커밋**하면 Cursor(및 다른 도구)가 반복적으로 동일한 기준을 볼 수 있습니다.
  - `docs/GOLDKEY_DESIGNER_CONTEXT.md` (본 프로젝트)
  - `Constitution.md` (GP 원문)
  - `.cursor/rules/goldkey-ai-masters.mdc` (AI 행동 힌트)

## 2. Windsurf에서만 할 일 / Cursor에서만 할 일 (권장)

| 작업 유형 | 권장 도구 | 이유 |
|-----------|-----------|------|
| 대형 `app.py` 탐색·다중 파일 편집 | Cursor 또는 로컬 IDE | 컨텍스트·검색·리팩터 |
| 빠른 초안·문서 초안 | Windsurf | 자유로운 초안 |
| **최종 반영** | **항상 Git 커밋으로 병합** | SSOT는 레포 |

**원칙:** Windsurf에서 나온 GP·페르소나·부속 목록은 **반드시 `docs/` 또는 코드 주석으로 merge 후 push**합니다.

## 3. 설계자가 앞으로 꼭 할 일 (체크리스트)

1. **민감 정보:** `secrets.toml` / `.env` / API 키 파일은 **절대 커밋 금지** — Cloud Run·GitHub Secrets·Secret Manager와 대조 목록 유지  
2. **HQ vs CRM 경계:** 정밀 분석·탭 라우터는 HQ; 현장·일정·발송은 CRM — 기능 추가 시 어느 앱인지 먼저 결정  
3. **GP 변경:** `Constitution.md` 수정 시, 영향 받는 `app.py`/`crm_app.py` 주석·상수와 **동시에** 맞추기  
4. **배포:** `Dockerfile`·`deploy/` 변경 후 **실제 빌드·헬스** 확인  
5. **대용량 폴더:** `backup_v1/`, `workspace/`, `crm_app/`는 **배포 포함 여부**를 Dockerfile·`.dockerignore`로 명시적으로 관리  
6. **이중 도구 사용 시:** 한쪽에서만 고친 내용이 있으면 **매 작업 단위로 merge·push**하여 다른 쪽이 옛 버전을 보지 않게 함  

## 4. 추가로 있으면 좋은 것

- **Git 브랜치 전략:** `main` 보호, 기능 브랜치 + PR (팀 규모에 맞게)  
- **Issue / 칸반:** “HQ”, “CRM”, “인프라”, “GP” 라벨  
- **주기적 문서 동기화:** 분기마다 `docs/GOLDKEY_DESIGNER_CONTEXT.md`와 실제 폴더 구조 diff 검토  

---

*이 문서는 설계자·개발자 공용입니다.*
