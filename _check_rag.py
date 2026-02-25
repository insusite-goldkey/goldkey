import os, sys

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv('D:/CascadeProjects/.env')
except Exception:
    pass

# secrets.toml 로드 시도
try:
    import toml
    sec = toml.load('D:/CascadeProjects/.streamlit/secrets.toml')
    for k, v in sec.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                os.environ.setdefault(kk.upper(), str(vv))
        else:
            os.environ.setdefault(k.upper(), str(v))
except Exception:
    pass

sb_url = os.environ.get('SUPABASE_URL', '')
sb_key = (os.environ.get('SUPABASE_KEY', '')
          or os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '')
          or os.environ.get('SUPABASE_ANON_KEY', ''))

print(f"SUPABASE_URL : {sb_url[:45] if sb_url else '(없음)'}")
print(f"SUPABASE_KEY : {'설정됨' if sb_key else '(없음)'}")

if not (sb_url and sb_key):
    print("\nSupabase 자격증명을 찾을 수 없습니다.")
    print("secrets.toml 또는 .env 위치를 확인하세요.")
    sys.exit(0)

try:
    from supabase import create_client
    sb = create_client(sb_url, sb_key)

    # rag_sources 전체
    res = sb.table('rag_sources').select(
        'id,filename,category,insurer,chunk_cnt,processed,uploaded,error_flag'
    ).order('uploaded', desc=True).execute()
    rows = res.data or []

    print(f"\n{'='*60}")
    print(f" rag_sources 전체: {len(rows)}건")
    print(f"{'='*60}")
    for r in rows:
        flag = '[처리완료]' if r.get('processed') else '[미처리  ]'
        err  = f" ERR:{r['error_flag']}" if r.get('error_flag') else ''
        print(f"  {flag}{err} #{r['id']:>4} | 청크={r['chunk_cnt']:>4} | "
              f"{r['uploaded'][:16]} | {r['category']:<10} | {r['filename'][:45]}")

    # rag_docs 총 청크
    res2 = sb.table('rag_docs').select('id', count='exact').execute()
    total = res2.count if hasattr(res2, 'count') and res2.count is not None else len(res2.data or [])
    print(f"\n rag_docs 총 청크 수: {total}건")

    # 오늘 등록분
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    today_rows = [r for r in rows if r.get('uploaded', '').startswith(today)]
    print(f"\n{'='*60}")
    print(f" 오늘({today}) 등록된 파일: {len(today_rows)}건")
    print(f"{'='*60}")
    if today_rows:
        for r in today_rows:
            flag = '[처리완료]' if r.get('processed') else '[미처리-심야처리대기]'
            print(f"  {flag} #{r['id']} | 청크={r['chunk_cnt']} | "
                  f"{r['category']} | {r['filename'][:50]}")
    else:
        print("  (오늘 등록된 파일 없음 — 어제 이전 날짜로 저장되었을 수 있음)")

    # 미처리(processed=False) 목록
    pending = [r for r in rows if not r.get('processed')]
    print(f"\n 미처리(processed=False): {len(pending)}건")
    for r in pending:
        print(f"  -> #{r['id']} {r['filename'][:50]}")

    # 에러 플래그 있는 항목
    errored = [r for r in rows if r.get('error_flag')]
    if errored:
        print(f"\n 에러 플래그 감지: {len(errored)}건")
        for r in errored:
            print(f"  !! #{r['id']} {r['filename'][:40]} | {r['error_flag'][:60]}")
    else:
        print("\n 에러 플래그: 없음 (정상)")

except Exception as e:
    print(f"\n오류 발생: {e}")
