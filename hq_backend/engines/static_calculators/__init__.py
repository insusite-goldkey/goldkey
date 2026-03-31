"""
정적 데이터 기반 연산 엔진 패키지
LLM 우회 100% 정확한 수학 연산 수행
"""

from .static_data_loader import (
    load_static_data,
    COVERAGE_16_MAPPING,
    KB_TRINITY_STANDARDS
)

from .coverage_calculator import CoverageCalculator

__all__ = [
    'load_static_data',
    'COVERAGE_16_MAPPING',
    'KB_TRINITY_STANDARDS',
    'CoverageCalculator'
]
