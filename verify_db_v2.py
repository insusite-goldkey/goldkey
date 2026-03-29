#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
[GP-PHASE3/4] Supabase 라이브 DB 스키마 검증 스크립트 v2
db_utils의 실제 함수를 사용하여 테이블 존재 여부 확인
"""

import sys
from datetime import datetime

print("\n" + "="*80)
print("🔍 [GP-PHASE3/4] Supabase 라이브 DB 테이블 검증 시작 (v2)")
print(f"⏰ 검증 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80 + "\n")

# db_utils import
try:
    from db_utils import _get_sb
    sb = _get_sb()
    if not sb:
        print("❌ Supabase 클라이언트 초기화 실패")
        sys.exit(1)
    print("✅ Supabase 클라이언트 연결 성공\n")
except Exception as e:
    print(f"❌ db_utils import 실패: {e}")
    sys.exit(1)

# 검증 대상 테이블
TABLES = [
    ("gk_people", "기존 - 고객 마스터 (대조군)", True),
    ("gk_members", "기존 - 설계사 회원 (대조군)", True),
    ("gk_scan_files", "Phase 3 - 스캔 문서 메타데이터", False),
    ("gk_medical_records", "Phase 3 - 의무기록 메타데이터", False),
    ("gk_customer_docs", "Phase 4 - 고객 문서 메타데이터", False),
    ("gk_agent_profiles", "Phase 4 - 설계사 프로필 확장", False),
    ("gk_home_notes", "Phase 4 - 홈 메모", False),
    ("gk_home_ins", "Phase 4 - 홈 인사이트", False),
]

results = []

for table_name, description, is_control in TABLES:
    print(f"📊 테이블 검증 중: {table_name} ({description})")
    
    try:
        # RPC 함수 호출로 테이블 존재 확인 (information_schema 조회)
        check_query = f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
        ) as exists;
        """
        
        response = sb.rpc('exec_sql', {'query': check_query}).execute()
        
        if response and hasattr(response, 'data') and response.data:
            exists = response.data[0].get('exists', False)
            if exists:
                # 테이블 존재 확인 - 행 개수 조회
                try:
                    count_resp = sb.from_(table_name).select("*", count="exact").limit(0).execute()
                    row_count = count_resp.count if hasattr(count_resp, 'count') else "알 수 없음"
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "✅ 성공",
                        "detail": f"테이블 존재 확인 (현재 {row_count}개 행)",
                        "is_new": not is_control
                    })
                    print(f"   ✅ 성공 - 테이블 존재 (현재 {row_count}개 행)\n")
                except:
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "✅ 성공",
                        "detail": "테이블 존재 확인 (행 개수 조회 불가)",
                        "is_new": not is_control
                    })
                    print(f"   ✅ 성공 - 테이블 존재 (행 개수 조회 불가)\n")
            else:
                results.append({
                    "table": table_name,
                    "description": description,
                    "status": "❌ 실패",
                    "detail": "테이블 미생성",
                    "is_new": not is_control
                })
                print(f"   ❌ 실패 - 테이블이 존재하지 않음\n")
        else:
            results.append({
                "table": table_name,
                "description": description,
                "status": "⚠️ 경고",
                "detail": "RPC 응답 이상",
                "is_new": not is_control
            })
            print(f"   ⚠️ 경고 - RPC 응답 이상\n")
            
    except Exception as e:
        error_msg = str(e)
        
        # RPC 함수가 없는 경우 - 직접 정보 스키마 조회 시도
        if "exec_sql" in error_msg or "function" in error_msg.lower():
            try:
                # PostgREST 직접 조회 시도
                test_resp = sb.from_(table_name).select("*").limit(1).execute()
                if test_resp and hasattr(test_resp, 'data'):
                    row_count = len(test_resp.data) if test_resp.data else 0
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "✅ 성공",
                        "detail": f"테이블 존재 확인 (현재 {row_count}개 행)",
                        "is_new": not is_control
                    })
                    print(f"   ✅ 성공 - 테이블 존재 (현재 {row_count}개 행)\n")
                else:
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "❌ 실패",
                        "detail": "테이블 미생성 또는 접근 불가",
                        "is_new": not is_control
                    })
                    print(f"   ❌ 실패 - 테이블 미생성 또는 접근 불가\n")
            except Exception as e2:
                error_msg2 = str(e2)
                if "404" in error_msg2 or "not found" in error_msg2.lower() or "does not exist" in error_msg2.lower():
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "❌ 실패",
                        "detail": "테이블 미생성",
                        "is_new": not is_control
                    })
                    print(f"   ❌ 실패 - 테이블이 존재하지 않음\n")
                else:
                    results.append({
                        "table": table_name,
                        "description": description,
                        "status": "❌ 에러",
                        "detail": error_msg2[:100],
                        "is_new": not is_control
                    })
                    print(f"   ❌ 에러 - {error_msg2[:80]}\n")
        else:
            results.append({
                "table": table_name,
                "description": description,
                "status": "❌ 에러",
                "detail": error_msg[:100],
                "is_new": not is_control
            })
            print(f"   ❌ 에러 - {error_msg[:80]}\n")

# 최종 결과 요약
print("\n" + "="*80)
print("📋 검증 결과 요약")
print("="*80 + "\n")

success_count = sum(1 for r in results if r["status"] == "✅ 성공")
fail_count = sum(1 for r in results if "❌" in r["status"])
new_success = sum(1 for r in results if r["is_new"] and r["status"] == "✅ 성공")
new_fail = sum(1 for r in results if r["is_new"] and "❌" in r["status"])

print(f"총 {len(TABLES)}개 테이블 검증 완료")
print(f"✅ 전체 성공: {success_count}개")
print(f"❌ 전체 실패: {fail_count}개")
print(f"\n🆕 Phase 3/4 신규 테이블:")
print(f"   ✅ 성공: {new_success}개 / 6개")
print(f"   ❌ 실패: {new_fail}개 / 6개\n")

# 마크다운 표
print("| 테이블명 | 설명 | 상태 | 상세 |")
print("|---------|------|------|------|")
for r in results:
    marker = "🆕" if r["is_new"] else "📌"
    print(f"| {marker} `{r['table']}` | {r['description']} | {r['status']} | {r['detail']} |")

print("\n" + "="*80)

# 실패한 신규 테이블 분석
if new_fail > 0:
    print("\n⚠️ Phase 3/4 신규 테이블 생성 실패 분석:")
    print("-" * 80)
    for r in results:
        if r["is_new"] and "❌" in r["status"]:
            print(f"\n테이블: {r['table']}")
            print(f"상태: {r['status']}")
            print(f"상세: {r['detail']}")
            print("\n가능한 원인:")
            print("1. SQL DDL 스크립트가 Supabase SQL Editor에서 실행되지 않았음")
            print("2. SQL 구문 오류로 인한 테이블 생성 실패")
            print("3. RLS 정책 설정 오류 (하지만 service_role은 RLS 우회)")
            print("4. 테이블명 오타 (대소문자 구분)")
    print("-" * 80)
elif new_success == 6:
    print("\n🎉 Phase 3/4 모든 신규 테이블 생성 성공!")
    print("   사용자가 Supabase 대시보드에서 SQL 스크립트를 정상적으로 실행했습니다.")

sys.exit(0 if new_fail == 0 else 1)
