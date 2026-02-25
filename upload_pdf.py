import sys, io, pathlib, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

txt = pathlib.Path('D:/CascadeProjects/.streamlit/secrets.toml').read_text(encoding='utf-8')

# 키 추출
url = re.search(r'url\s*=\s*"([^"]+)"', txt)
svc = re.search(r'service_role_key\s*=\s*"([^"]+)"', txt)
anon = re.search(r'anon_key\s*=\s*"([^"]+)"', txt)

sb_url = url.group(1) if url else ""
sb_key = (svc.group(1) if svc else "") or (anon.group(1) if anon else "")

print("URL:", sb_url[:50] if sb_url else "NOT FOUND")
print("KEY:", (sb_key[:30] + "...") if sb_key else "NOT FOUND")

if not sb_url or not sb_key:
    print("ERROR: Supabase 인증 정보 없음")
    sys.exit(1)

import urllib.parse, urllib.request, json

# ── 1. Supabase Storage 파일 목록 조회 (전체 버킷) ──────────────────
list_url = f"{sb_url}/storage/v1/object/list/goldkey"
list_req = urllib.request.Request(
    list_url,
    data=json.dumps({"prefix": "", "limit": 200}).encode(),
    headers={
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/json",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(list_req, timeout=30) as r:
        items = json.loads(r.read().decode())
    print(f"\n== Supabase goldkey 버킷 파일 목록 ({len(items)}개) ==")
    for it in items:
        nm = it.get("name","")
        sz = it.get("metadata",{}).get("size",0) if it.get("metadata") else 0
        print(f"  {nm}  ({sz//1024}KB)")
except Exception as e:
    print("목록 조회 실패:", e)

# ── 2. 과실비율 PDF 업로드 ───────────────────────────────────────────
pdf_path = pathlib.Path("D:/CascadeProjects/static/230630_자동차사고 과실비율 인정기준_최종.pdf")
pdf_bytes = pdf_path.read_bytes()
dest = "230630_fault_ratio_standard_final.pdf"
dest_enc = urllib.parse.quote(dest, safe="")

upload_url = f"{sb_url}/storage/v1/object/goldkey/{dest_enc}"
upload_req = urllib.request.Request(
    upload_url,
    data=pdf_bytes,
    headers={
        "Authorization": f"Bearer {sb_key}",
        "Content-Type": "application/pdf",
        "x-upsert": "true",
    },
    method="POST",
)
print(f"\n업로드 중... ({len(pdf_bytes)//1024//1024}MB)")
try:
    with urllib.request.urlopen(upload_req, timeout=120) as r:
        print("업로드 성공:", r.status, r.read().decode()[:100])
except urllib.error.HTTPError as e:
    print("업로드 실패:", e.code, e.read().decode()[:200])
except Exception as e:
    print("업로드 오류:", e)

pub_url = f"{sb_url}/storage/v1/object/public/goldkey/{dest_enc}"
print("공개 URL:", pub_url)
