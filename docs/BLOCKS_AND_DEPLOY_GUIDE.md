# 블록 모듈 & 배포 트랙 가이드 (GP-44)

## 목적

- `app.py` / `crm_app.py` 변경 시 **빌드·배포가 무겁게 느껴지는 문제**를 줄이기 위해, UI·액션을 **블록 파일**로 분리하고, **설정 파일**으로 OTA를 지원한다.

## 폴더

| 경로 | 역할 |
|------|------|
| `blocks/` | Streamlit UI·버튼 블록 (예: `crm_action_grid_block.py`) |
| `rules.json` | 로컬 기본 설정 + `GK_RULES_JSON_URL` 원격 병합 |
| `shared_components.py` | `load_gp_rules()`, `get_crm_action_definitions()` 등 GP 공통 |

## Track A — 핫 패치 (설정만, 재배포 없이 *가능한 범위*)

**대상:** CRM 메인 액션 그리드의 **레이블, 순서, 표시 여부**, `action_grid_title` 등 `rules.json`에 정의된 항목.

**방법:**

1. `rules.json`의 `crm_ui` 섹션을 수정하거나, 동일 스키마의 JSON을 **GitHub Raw** 등에 올린다.
2. Cloud Run(또는 로컬)에서 환경 변수를 설정한다:  
   `GK_RULES_JSON_URL=https://.../rules.json`
3. 앱은 **최대 60초**마다 `load_gp_rules()` 캐시를 갱신한다. 즉시 반영이 필요하면 **브라우저 새로고침** 또는 **세션 재시작** 후 잠시 대기.

**주의:** Streamlit 위젯·레이아웃·비즈니스 로직을 바꾸려면 코드 변경이 필요하며, 이는 Track B다.

## Track B — 블록/로직 변경 (코드 배포)

**대상:** `blocks/*.py`, `shared_components.py`, `crm_app.py`, `app.py` 등 **실제 코드**.

**방법:** 기존과 같이 `deploy/cloudbuild-*.yaml` + `gcloud run deploy` 또는 `backup_and_push.ps1` / `deploy/gcloud-run-deploy.sh`.

**Docker 빌드 최적화:** 루트 `Dockerfile`에 `requirements.txt` + `pip install`이 **먼저** 있고, `COPY . .`는 **마지막**에 있어 **의존성 레이어가 캐시**되기 쉽다. `.dockerignore` / `.gcloudignore`로 **업로드 tarball 크기**를 줄인다.

## 무엇을 어디서 고칠까

| 하고 싶은 일 | 수정할 곳 |
|--------------|-----------|
| CRM 액션 버튼 **이름·순서·on/off** | `rules.json` → `crm_ui.actions` (또는 원격 URL + `GK_RULES_JSON_URL`) |
| 액션 **그리드 레이아웃/스타일** | `blocks/crm_action_grid_block.py`, `inject_global_gp_design()` CSS |
| `app.py` 탭/섹션 분리 | 점진적으로 `blocks/hq_*_block.py`로 추출 후 `app.py`에서 import |

## 향후

- `app.py`의 `home`, `gk_sec10` 등 대형 탭은 `blocks/hq_home_block.py` … 형태로 **단계적** 이전을 권장한다.
