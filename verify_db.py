#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[GP-PHASE3/4] Supabase 라이브 DB 스키마 검증 스크립트
6개 핵심 테이블 생성 여부 실시간 확인
"""

import sys
import os
from datetime import datetime

# Supabase 클라이언트 초기화 (db_utils 사용)
try:
    from db_utils import _get_sb
    
    supabase = _get_sb()
    
    if supabase is None:
        print("❌ Supabase 클라이언트 초기화 실패 - _get_sb() returned None")
        print("   secrets.toml 파일 또는 환경변수 확인 필요")
        sys.exit(1)
    
    print(f"✅ Supabase 클라이언트 연결 성공 (db_utils._get_sb())")
except Exception as e:
    print(f"❌ Supabase 클라이언트 초기화 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 검증 대상 테이블 목록
# 1. 기존 테이블 (연결 정상 여부 확인용 대조군)
CONTROL_TABLES = [
    ("gk_people", "기존 - 고객 마스터 (대조군)"),
    ("gk_members", "기존 - 설계사 회원 (대조군)"),
]

# 2. 신규 테이블 (Phase 3 + Phase 4)
NEW_TABLES = [
    ("gk_scan_files", "Phase 3 - 스캔 문서 메타데이터"),
    ("gk_medical_records", "Phase 3 - 의무기록 메타데이터"),
    ("gk_customer_docs", "Phase 4 - 고객 문서 메타데이터"),
    ("gk_agent_profiles", "Phase 4 - 설계사 프로필 확장"),
    ("gk_home_notes", "Phase 4 - 홈 메모"),
    ("gk_home_ins", "Phase 4 - 홈 인사이트"),
]

TABLES_TO_VERIFY = CONTROL_TABLES + NEW_TABLES

print("\n" + "="*80)
print("🔍 [GP-PHASE3/4] Supabase 라이브 DB 테이블 검증 시작")
print(f"⏰ 검증 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

results = []

for table_name, description in TABLES_TO_VERIFY:
    print(f"📊 테이블 검증 중: {table_name} ({description})")
    
    try:
        # PostgREST API 직접 호출 방식으로 변경
        response = supabase.from_(table_name).select("*").limit(1).execute()
        
        # 성공 케이스
        if hasattr(response, 'data') and response.data is not None:
            row_count = len(response.data) if response.data else 0
            results.append({
                "table": table_name,
                "description": description,
                "status": "✅ 성공",
                "detail": f"테이블 존재 확인 (현재 {row_count}개 행)",
                "error": None
            })
            print(f"   ✅ 성공 - 테이블 존재 (현재 {row_count}개 행)\n")
        else:
            results.append({
                "table": table_name,
                "description": description,
                "status": "⚠️ 경고",
                "detail": "응답 형식 이상",
                "error": str(response)
            })
            print(f"   ⚠️ 경고 - 응답 형식 이상: {response}\n")
            
    except Exception as e:
        # 실패 케이스 (테이블 미존재 등)
        error_msg = str(e)
        
        # 404 또는 relation does not exist 에러 = 테이블 미생성
        if "404" in error_msg or "does not exist" in error_msg.lower() or "relation" in error_msg.lower() or "not found" in error_msg.lower():
            results.append({
                "table": table_name,
                "description": description,
                "status": "❌ 실패",
                "detail": "테이블 미생성",
                "error": error_msg[:200]
            })
            print(f"   ❌ 실패 - 테이블이 존재하지 않음\n")
        else:
            # 기타 에러 (권한, 네트워크 등)
            results.append({
                "table": table_name,
                "description": description,
                "status": "❌ 에러",
                "detail": "쿼리 실행 실패",
                "error": error_msg[:200]
            })
            print(f"   ❌ 에러 - {error_msg[:100]}\n")

# 최종 결과 요약
print("\n" + "="*80)
print("📋 검증 결과 요약")
print("="*80 + "\n")

success_count = sum(1 for r in results if r["status"] == "✅ 성공")
fail_count = sum(1 for r in results if "❌" in r["status"])

print(f"총 {len(TABLES_TO_VERIFY)}개 테이블 검증 완료")
print(f"✅ 성공: {success_count}개")
print(f"❌ 실패: {fail_count}개\n")

# 마크다운 표 형식 출력
print("| 테이블명 | 설명 | 상태 | 상세 |")
print("|---------|------|------|------|")
for r in results:
    detail = r["detail"]
    if r["error"] and len(r["error"]) > 50:
        detail = r["error"][:50] + "..."
    print(f"| `{r['table']}` | {r['description']} | {r['status']} | {detail} |")

print("\n" + "="*80)

# 실패한 테이블이 있으면 원인 분석
if fail_count > 0:
    print("\n⚠️ 실패 원인 분석:")
    print("-" * 80)
    for r in results:
        if "❌" in r["status"]:
            print(f"\n테이블: {r['table']}")
            print(f"원인: {r['error']}")
            print("\n가능한 해결책:")
            print("1. Supabase 대시보드 → SQL Editor에서 해당 테이블 DDL 재실행")
            print("2. RLS 정책 확인 (service_role은 RLS 우회하므로 권한 문제는 아님)")
            print("3. 테이블명 오타 확인 (대소문자 구분)")
    print("-" * 80)

sys.exit(0 if fail_count == 0 else 1)
