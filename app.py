## [SYSTEM INITIALIZATION] MUST BE LINE 1
# Goldkey HQ — Streamlit 진입점(껍데기). 구현 본문: hq_app_impl.py (Phase 1②)
#
# 복잡도·GP 주석·탭 로직은 모두 hq_app_impl.py에 있으며,
# rerun 시에만 importlib.reload로 재실행되어 Streamlit 캐시 문제를 피합니다.

import importlib
import sys

_HQ_IMPL = "hq_app_impl"
if _HQ_IMPL in sys.modules:
    importlib.reload(sys.modules[_HQ_IMPL])
else:
    __import__(_HQ_IMPL)
