# ══════════════════════════════════════════════════════════════════════════════
# [GP-ARCH] 시스템 아키텍처 지휘체계 — 최상위 운영 원칙 (모든 작업의 북극성)
#
#  🎖️ Cloud Run   (지휘통제실) : 실시간 지휘 및 모든 연산/판단 수행.
#                                Stateless 기반 최적 로직 실행 — 데이터 임시 저장 금지.
#  📜 GitHub       (기록관/비서): 1차 설계도 및 규칙 보관소.
#                                지휘관(Cloud Run)에 전달할 최신 코드(작전 교본) 관리.
#  🧠 Supabase     (활성 메모리): 상담 내용·고객 정보 즉시 저장/조회.
#                                지휘관의 현장 장부 — 상태는 반드시 여기에 저장.
#  📦 GCS          (영구 창고)  : PDF·이미지 등 대용량 파일 및 장기 데이터 백업.
#  💪 CRM / HQ     (실행 부위)  : 고객 소통 및 전문가 개입 UI — 몸통과 팔다리.
#
# [Cascade 특별 지시]
#  1. 코드 수정·기능 추가 시 반드시 위 지휘-기록-보관 체계에 부합하는지 검토.
#  2. 데이터 저장은 Cloud Run(임시) 금지 → Supabase(상태) 또는 GCS(파일) 사용.
#  3. 이 주석은 단순 기록이 아닌 프로젝트 최상위 운영 원칙이다. 절대 삭제 금지.
# ══════════════════════════════════════════════════════════════════════════════
## [SYSTEM INITIALIZATION] MUST BE LINE 19
# Goldkey HQ — Streamlit 진입점(껍데기). 구현 본문: hq_app_impl.py (Phase 1②)
#
# 복잡도·GP 주석·탭 로직은 모두 hq_app_impl.py에 있으며,
# rerun 시에만 importlib.reload로 재실행되어 Streamlit 캐시 문제를 피합니다.

import importlib
import sys

_HQ_IMPL = "hq_app_impl"
if _HQ_IMPL in sys.modules:
    try:
        importlib.reload(sys.modules[_HQ_IMPL])
    except (ImportError, KeyError):
        sys.modules.pop(_HQ_IMPL, None)
        __import__(_HQ_IMPL)
else:
    __import__(_HQ_IMPL)
