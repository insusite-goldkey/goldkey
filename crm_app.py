# crm_app.py — Goldkey AI Masters CRM 2026
"""
[GP 마스터-그림자 Phase 3] Streamlit 진입점(껍데기).
구현 본문: `crm_app_impl.py` — Phase 1② 아키텍처 분리.

동시 구동:
  HQ:  streamlit run app.py     --server.port 8501
  CRM: streamlit run crm_app.py --server.port 8502
"""
from __future__ import annotations

import importlib
import sys

_CRM_IMPL = "crm_app_impl"
if _CRM_IMPL in sys.modules:
    importlib.reload(sys.modules[_CRM_IMPL])
else:
    __import__(_CRM_IMPL)
