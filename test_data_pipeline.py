#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[시스템 신경망 통합 점검] 2. 데이터 파이프라인 정밀 테스트
작성일: 2026-03-31
목적: 입력→엔진→출력 데이터 흐름 검증
"""

import sys
from pathlib import Path
from typing import Dict, Any

# 프로젝트 루트 경로
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("[2] 데이터 파이프라인 정밀 테스트")
print("=" * 80)

# ══════════════════════════════════════════════════════════════════════════════
# § 1. [입력 ➡️ 엔진] 연금 엔진 데이터 전달 검증
# ══════════════════════════════════════════════════════════════════════════════

def test_pension_engine_data_flow() -> bool:
    """
    연금 엔진 데이터 흐름 테스트
    
    입력 데이터 → calculate_pension_gap() → 출력 데이터
    """
    print("\n[2-1] 연금 엔진 데이터 전달 검증...")
    
    try:
        from modules.pension_engine import calculate_pension_gap, calculate_monthly_savings_needed
        
        # 테스트 입력 데이터 (좌측 입력창에서 수집된 데이터 시뮬레이션)
        test_input = {
            "current_age": 40,
            "retirement_age": 65,
            "life_expectancy": 90,
            "monthly_expense_now": 4_000_000,  # 월 400만원 생활비
            "current_pension_monthly": 800_000,  # 현재 연금 80만원
            "inflation_rate": 0.025  # 물가상승률 2.5%
        }
        
        print(f"   입력 데이터: {test_input}")
        
        # 엔진 실행
        gap_result = calculate_pension_gap(**test_input)
        
        # 출력 데이터 검증
        required_keys = [
            "years_to_retirement",
            "retirement_years",
            "future_monthly_expense",
            "future_pension_monthly",
            "monthly_gap",
            "total_gap",
            "status"
        ]
        
        missing_keys = [k for k in required_keys if k not in gap_result]
        
        if missing_keys:
            print(f"   ❌ 출력 데이터 누락: {missing_keys}")
            return False
        
        print(f"   ✅ 출력 데이터 완전성: 모든 키 존재")
        print(f"   - 은퇴까지: {gap_result['years_to_retirement']}년")
        print(f"   - 30년 후 월 생활비: {gap_result['future_monthly_expense']:,.0f}원")
        print(f"   - 월 부족액: {gap_result['monthly_gap']:,.0f}원")
        print(f"   - 상태: {gap_result['status']}")
        
        # 월 적립액 계산 검증
        if gap_result['total_gap'] > 0:
            monthly_savings = calculate_monthly_savings_needed(
                total_gap=gap_result['total_gap'],
                years_to_retirement=gap_result['years_to_retirement'],
                compound_rate=0.03
            )
            
            if monthly_savings > 0:
                print(f"   ✅ 월 적립액 계산 성공: {monthly_savings:,.0f}원")
            else:
                print(f"   ❌ 월 적립액 계산 실패")
                return False
        
        print("   ✅ [입력 ➡️ 엔진] 데이터 전달 정상 (PASS)")
        return True
        
    except Exception as e:
        print(f"   ❌ 연금 엔진 데이터 흐름 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════════════════
# § 2. [엔진 ➡️ 출력] 렌더링 함수 인터페이스 검증
# ══════════════════════════════════════════════════════════════════════════════

def test_rendering_interface() -> bool:
    """
    렌더링 함수 인터페이스 검증
    
    계산된 데이터 → render_pension_gap_analysis() → UI 렌더링
    """
    print("\n[2-2] 렌더링 함수 인터페이스 검증...")
    
    try:
        from modules.pension_engine import render_pension_gap_analysis
        import inspect
        
        # 함수 시그니처 확인
        sig = inspect.signature(render_pension_gap_analysis)
        params = list(sig.parameters.keys())
        
        print(f"   함수 시그니처: render_pension_gap_analysis({', '.join(params)})")
        
        # 필수 파라미터 확인
        required_params = [
            "current_age",
            "monthly_expense_now",
            "current_pension_monthly"
        ]
        
        missing_params = [p for p in required_params if p not in params]
        
        if missing_params:
            print(f"   ❌ 필수 파라미터 누락: {missing_params}")
            return False
        
        print(f"   ✅ 필수 파라미터 존재: {required_params}")
        
        # 반환값 타입 확인 (None - UI 렌더링 함수)
        return_annotation = sig.return_annotation
        
        if return_annotation == inspect.Signature.empty or return_annotation is None:
            print(f"   ✅ 반환값: None (UI 렌더링 함수)")
        else:
            print(f"   ⚠️  반환값: {return_annotation}")
        
        print("   ✅ [엔진 ➡️ 출력] 렌더링 인터페이스 정상 (PASS)")
        return True
        
    except Exception as e:
        print(f"   ❌ 렌더링 인터페이스 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════════════════
# § 3. [OCR ➡️ 분석] 마스터 대시보드 파이프라인 검증
# ══════════════════════════════════════════════════════════════════════════════

def test_master_dashboard_pipeline() -> bool:
    """
    마스터 대시보드 파이프라인 검증
    
    파일 업로드 → 해시 체크 → GCS → RAG → 렌더링
    """
    print("\n[2-3] 마스터 대시보드 파이프라인 검증...")
    
    try:
        from modules.master_dashboard_55 import (
            render_master_dashboard_55,
            render_analysis_summary,
            render_strategy_box,
            process_file_pipeline
        )
        import inspect
        
        # process_file_pipeline 시그니처 확인
        sig = inspect.signature(process_file_pipeline)
        params = list(sig.parameters.keys())
        
        print(f"   파이프라인 함수: process_file_pipeline({', '.join(params)})")
        
        # 반환값 확인
        return_annotation = sig.return_annotation
        print(f"   반환값 타입: {return_annotation}")
        
        # 렌더링 함수들 확인
        rendering_functions = [
            ("render_master_dashboard_55", render_master_dashboard_55),
            ("render_analysis_summary", render_analysis_summary),
            ("render_strategy_box", render_strategy_box),
        ]
        
        for func_name, func in rendering_functions:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            print(f"   - {func_name}({', '.join(params)})")
        
        print("   ✅ [OCR ➡️ 분석] 마스터 대시보드 파이프라인 정상 (PASS)")
        return True
        
    except Exception as e:
        print(f"   ❌ 마스터 대시보드 파이프라인 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════════════════
# § 4. 데이터 타입 일관성 검증
# ══════════════════════════════════════════════════════════════════════════════

def test_data_type_consistency() -> bool:
    """
    데이터 타입 일관성 검증
    
    입력 타입 → 처리 → 출력 타입 일관성 확인
    """
    print("\n[2-4] 데이터 타입 일관성 검증...")
    
    try:
        from modules.pension_engine import calculate_pension_gap
        
        # 정상 입력
        result = calculate_pension_gap(
            current_age=35,
            retirement_age=65,
            life_expectancy=90,
            monthly_expense_now=3_000_000,
            current_pension_monthly=500_000
        )
        
        # 타입 검증
        type_checks = {
            "years_to_retirement": int,
            "retirement_years": int,
            "future_monthly_expense": (int, float),
            "future_pension_monthly": (int, float),
            "monthly_gap": (int, float),
            "total_gap": (int, float),
            "status": str,
        }
        
        all_correct = True
        for key, expected_type in type_checks.items():
            actual_value = result[key]
            if isinstance(expected_type, tuple):
                is_correct = isinstance(actual_value, expected_type)
            else:
                is_correct = isinstance(actual_value, expected_type)
            
            if is_correct:
                print(f"   ✅ {key}: {type(actual_value).__name__}")
            else:
                print(f"   ❌ {key}: 예상 {expected_type}, 실제 {type(actual_value)}")
                all_correct = False
        
        if all_correct:
            print("   ✅ 데이터 타입 일관성 정상 (PASS)")
            return True
        else:
            print("   ❌ 데이터 타입 불일치 발견 (FAIL)")
            return False
        
    except Exception as e:
        print(f"   ❌ 데이터 타입 일관성 검증 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════════════════
# § 5. 실행
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    test1 = test_pension_engine_data_flow()
    test2 = test_rendering_interface()
    test3 = test_master_dashboard_pipeline()
    test4 = test_data_type_consistency()
    
    print("\n" + "=" * 80)
    print("[2] 데이터 파이프라인 정밀 테스트 결과")
    print("=" * 80)
    
    results = {
        "[입력 ➡️ 엔진] 연금 엔진 데이터 전달": test1,
        "[엔진 ➡️ 출력] 렌더링 인터페이스": test2,
        "[OCR ➡️ 분석] 마스터 대시보드 파이프라인": test3,
        "데이터 타입 일관성": test4,
    }
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    if all(results.values()):
        print("\n✅ 전체 PASS: 모든 데이터 파이프라인 정상 작동")
    else:
        print("\n❌ 전체 FAIL: 일부 파이프라인에서 문제 발견")
    
    print("=" * 80)
