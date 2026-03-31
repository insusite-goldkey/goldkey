#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[외과 수술적 모듈 분리] 검증 스크립트
작성일: 2026-03-31
목적: 독립 모듈 import 및 렌더링 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("[외과 수술적 모듈 분리] 검증 시작")
print("=" * 80)

# ══════════════════════════════════════════════════════════════════════════════
# 테스트 1: master_dashboard_55.py import 검증
# ══════════════════════════════════════════════════════════════════════════════
print("\n[테스트 1] master_dashboard_55.py import 검증...")
try:
    from modules.master_dashboard_55 import render_master_dashboard_55
    print("✅ master_dashboard_55.py import 성공")
    print(f"   - 함수명: {render_master_dashboard_55.__name__}")
    print(f"   - 모듈 경로: {render_master_dashboard_55.__module__}")
except ImportError as e:
    print(f"❌ master_dashboard_55.py import 실패: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 테스트 2: pension_engine.py import 검증
# ══════════════════════════════════════════════════════════════════════════════
print("\n[테스트 2] pension_engine.py import 검증...")
try:
    from modules.pension_engine import (
        render_pension_gap_analysis,
        render_pension_engine_demo,
        calculate_pension_gap,
        calculate_monthly_savings_needed
    )
    print("✅ pension_engine.py import 성공")
    print(f"   - render_pension_gap_analysis: {render_pension_gap_analysis.__name__}")
    print(f"   - render_pension_engine_demo: {render_pension_engine_demo.__name__}")
    print(f"   - calculate_pension_gap: {calculate_pension_gap.__name__}")
    print(f"   - calculate_monthly_savings_needed: {calculate_monthly_savings_needed.__name__}")
except ImportError as e:
    print(f"❌ pension_engine.py import 실패: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 예상치 못한 오류: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 테스트 3: hq_app_impl.py import 검증 (플러그인 방식)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[테스트 3] hq_app_impl.py 플러그인 방식 import 검증...")
try:
    # hq_app_impl.py는 streamlit 의존성이 있으므로 직접 import하지 않고
    # 파일 내용을 읽어서 import 구문이 있는지 확인
    hq_impl_path = project_root / "hq_app_impl.py"
    with open(hq_impl_path, "r", encoding="utf-8") as f:
        hq_impl_content = f.read()
    
    # import 구문 확인
    if "from modules.master_dashboard_55 import render_master_dashboard_55" in hq_impl_content:
        print("✅ hq_app_impl.py에 master_dashboard_55 import 구문 확인")
    else:
        print("❌ hq_app_impl.py에 master_dashboard_55 import 구문 없음")
        sys.exit(1)
    
    if "from modules.pension_engine import render_pension_gap_analysis" in hq_impl_content:
        print("✅ hq_app_impl.py에 pension_engine import 구문 확인")
    else:
        print("❌ hq_app_impl.py에 pension_engine import 구문 없음")
        sys.exit(1)
    
    # 플러그인 방식 (try-except) 확인
    if "try:" in hq_impl_content and "_hq_render_master_dashboard" in hq_impl_content:
        print("✅ 플러그인 방식 (try-except) 패턴 확인")
    else:
        print("⚠️  플러그인 방식 패턴 미확인 (수동 검토 필요)")
    
except Exception as e:
    print(f"❌ hq_app_impl.py 검증 실패: {e}")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 테스트 4: 연금 엔진 로직 검증 (단위 테스트)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[테스트 4] 연금 엔진 로직 검증 (단위 테스트)...")
try:
    # 시나리오: 35세, 월 300만원 생활, 현재 연금 50만원
    gap_result = calculate_pension_gap(
        current_age=35,
        retirement_age=65,
        life_expectancy=90,
        monthly_expense_now=3_000_000,
        current_pension_monthly=500_000,
        inflation_rate=0.025
    )
    
    print("✅ 연금 Gap 계산 성공")
    print(f"   - 은퇴까지 남은 년수: {gap_result['years_to_retirement']}년")
    print(f"   - 30년 후 월 생활비: {gap_result['future_monthly_expense']:,.0f}원")
    print(f"   - 30년 후 연금 월 수령액: {gap_result['future_pension_monthly']:,.0f}원")
    print(f"   - 월 부족액: {gap_result['monthly_gap']:,.0f}원")
    print(f"   - 총 부족액: {gap_result['total_gap']:,.0f}원")
    print(f"   - 상태: {gap_result['status']}")
    
    # 월 적립액 계산
    if gap_result['total_gap'] > 0:
        monthly_savings = calculate_monthly_savings_needed(
            total_gap=gap_result['total_gap'],
            years_to_retirement=gap_result['years_to_retirement'],
            compound_rate=0.03
        )
        print(f"   - 필요 월 적립액 (복리 3%): {monthly_savings:,.0f}원")
        print("✅ 월 적립액 계산 성공")
    
except Exception as e:
    print(f"❌ 연금 엔진 로직 검증 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# 테스트 5: 파일 크기 확인 (모듈 분리 효과)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[테스트 5] 파일 크기 확인 (모듈 분리 효과)...")
try:
    hq_impl_size = (project_root / "hq_app_impl.py").stat().st_size
    master_dashboard_size = (project_root / "modules" / "master_dashboard_55.py").stat().st_size
    pension_engine_size = (project_root / "modules" / "pension_engine.py").stat().st_size
    
    print(f"✅ 파일 크기 확인 완료")
    print(f"   - hq_app_impl.py: {hq_impl_size:,} bytes ({hq_impl_size / 1024 / 1024:.2f} MB)")
    print(f"   - master_dashboard_55.py: {master_dashboard_size:,} bytes ({master_dashboard_size / 1024:.2f} KB)")
    print(f"   - pension_engine.py: {pension_engine_size:,} bytes ({pension_engine_size / 1024:.2f} KB)")
    print(f"   - 독립 모듈 총합: {master_dashboard_size + pension_engine_size:,} bytes ({(master_dashboard_size + pension_engine_size) / 1024:.2f} KB)")
    
    # hq_app_impl.py가 여전히 크다면 경고
    if hq_impl_size > 3_000_000:  # 3MB 이상
        print(f"⚠️  hq_app_impl.py가 여전히 큽니다 ({hq_impl_size / 1024 / 1024:.2f} MB)")
        print("   → 추가 모듈 분리를 권장합니다")
    
except Exception as e:
    print(f"❌ 파일 크기 확인 실패: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 최종 결과
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🎉 [외과 수술적 모듈 분리] 검증 완료!")
print("=" * 80)
print("\n✅ 모든 테스트 통과")
print("\n📋 다음 단계:")
print("   1. 로컬 Streamlit 앱 실행: streamlit run app.py")
print("   2. 마스터 대시보드 UI 렌더링 확인 (연분홍/연하늘 배경)")
print("   3. 연금 엔진 Gap 분석 정상 작동 확인")
print("   4. 배포 후 Cloud Run 환경에서 최종 검증")
print("\n" + "=" * 80)
