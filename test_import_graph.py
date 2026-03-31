#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
[시스템 신경망 통합 점검] 1. 임포트 그래프 및 의존성 체크
작성일: 2026-03-31
목적: 순환 참조 검증 및 라이브러리 중복 로드 확인
"""

import sys
import ast
import importlib.util
from pathlib import Path
from typing import Dict, List, Set, Tuple

# 프로젝트 루트 경로
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("[1] 임포트 그래프 및 의존성 체크")
print("=" * 80)

# ══════════════════════════════════════════════════════════════════════════════
# § 1. 순환 참조 검증 (Circular Import Detection)
# ══════════════════════════════════════════════════════════════════════════════

def extract_imports_from_file(file_path: Path) -> Set[str]:
    """
    Python 파일에서 import 구문 추출
    
    Returns:
        Set of imported module names
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        return imports
    except Exception as e:
        print(f"⚠️  {file_path.name} 파싱 실패: {e}")
        return set()


def check_circular_imports() -> Tuple[bool, List[str]]:
    """
    순환 참조 검증
    
    Returns:
        (순환 참조 없음 여부, 경고 메시지 리스트)
    """
    print("\n[1-1] 순환 참조 검증...")
    
    files_to_check = {
        "hq_app_impl": project_root / "hq_app_impl.py",
        "master_dashboard_55": project_root / "modules" / "master_dashboard_55.py",
        "pension_engine": project_root / "modules" / "pension_engine.py",
    }
    
    import_graph = {}
    for name, path in files_to_check.items():
        if path.exists():
            import_graph[name] = extract_imports_from_file(path)
    
    warnings = []
    
    # hq_app_impl → modules 체크
    if "modules" in import_graph.get("hq_app_impl", set()):
        print("✅ hq_app_impl.py → modules 정상 import")
    
    # modules → hq_app_impl 역참조 체크 (금지)
    for module_name in ["master_dashboard_55", "pension_engine"]:
        if module_name in import_graph:
            if "hq_app_impl" in import_graph[module_name]:
                warnings.append(
                    f"❌ CIRCULAR IMPORT: {module_name} → hq_app_impl (역참조 금지)"
                )
            else:
                print(f"✅ {module_name}.py: hq_app_impl 역참조 없음")
    
    # modules 간 상호 참조 체크
    if "master_dashboard_55" in import_graph.get("pension_engine", set()):
        warnings.append("⚠️  pension_engine → master_dashboard_55 상호 참조 발견")
    
    if "pension_engine" in import_graph.get("master_dashboard_55", set()):
        warnings.append("⚠️  master_dashboard_55 → pension_engine 상호 참조 발견")
    
    if not warnings:
        print("✅ 순환 참조 없음 (PASS)")
        return True, []
    else:
        for w in warnings:
            print(w)
        return False, warnings


# ══════════════════════════════════════════════════════════════════════════════
# § 2. 라이브러리 중복 로드 확인
# ══════════════════════════════════════════════════════════════════════════════

def check_library_imports() -> Tuple[bool, Dict]:
    """
    각 모듈의 라이브러리 import 현황 확인
    
    Returns:
        (적절한 로드 여부, 라이브러리 맵)
    """
    print("\n[1-2] 라이브러리 중복 로드 확인...")
    
    files_to_check = {
        "hq_app_impl": project_root / "hq_app_impl.py",
        "master_dashboard_55": project_root / "modules" / "master_dashboard_55.py",
        "pension_engine": project_root / "modules" / "pension_engine.py",
    }
    
    library_map = {}
    
    for name, path in files_to_check.items():
        if path.exists():
            imports = extract_imports_from_file(path)
            library_map[name] = {
                "streamlit": "streamlit" in imports,
                "pandas": "pandas" in imports,
                "numpy": "numpy" in imports,
                "supabase": "supabase" in imports,
                "google": "google" in imports,
            }
    
    # 결과 출력
    print("\n라이브러리 import 현황:")
    print("-" * 80)
    print(f"{'모듈':<25} {'streamlit':<12} {'pandas':<10} {'numpy':<10} {'supabase':<12} {'google':<10}")
    print("-" * 80)
    
    for module, libs in library_map.items():
        st_mark = "✅" if libs["streamlit"] else "  "
        pd_mark = "✅" if libs["pandas"] else "  "
        np_mark = "✅" if libs["numpy"] else "  "
        sb_mark = "✅" if libs["supabase"] else "  "
        gg_mark = "✅" if libs["google"] else "  "
        
        print(f"{module:<25} {st_mark:<12} {pd_mark:<10} {np_mark:<10} {sb_mark:<12} {gg_mark:<10}")
    
    print("-" * 80)
    
    # 검증: 모든 모듈이 streamlit을 import하는지 확인
    all_have_streamlit = all(libs["streamlit"] for libs in library_map.values())
    
    if all_have_streamlit:
        print("✅ 모든 모듈이 Streamlit을 적절히 import (PASS)")
        return True, library_map
    else:
        print("⚠️  일부 모듈에서 Streamlit import 누락")
        return False, library_map


# ══════════════════════════════════════════════════════════════════════════════
# § 3. 실행
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    circular_ok, circular_warnings = check_circular_imports()
    library_ok, library_map = check_library_imports()
    
    print("\n" + "=" * 80)
    print("[1] 임포트 그래프 및 의존성 체크 결과")
    print("=" * 80)
    
    if circular_ok and library_ok:
        print("✅ PASS: 순환 참조 없음 + 라이브러리 적절히 로드")
    else:
        print("❌ FAIL: 문제 발견")
        if not circular_ok:
            print("   - 순환 참조 경고:")
            for w in circular_warnings:
                print(f"     {w}")
        if not library_ok:
            print("   - 라이브러리 로드 문제 발견")
    
    print("=" * 80)
