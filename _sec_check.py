import urllib.request, json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SUPABASE_URL = 'https://idfzizqidhnpzbqioqqo.supabase.co'
SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkZnppenFpZGhucHpicWlvcXFvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTgyOTg0MiwiZXhwIjoyMDg3NDA1ODQyfQ.-oeAIGqA4k1crI4zeOwrHXlBVEdltXKAyCiW4BNtRxA'

# 1. app.py에서 테이블 이름 추출
src = open('D:/CascadeProjects/app.py', encoding='utf-8-sig').read()
tables = set()
for m in re.finditer(r'\.table\(["\']([\w]+)["\']\)', src):
    tables.add(m.group(1))
print("=== app.py 에서 발견된 테이블 ===")
for t in sorted(tables):
    print(f"  - {t}")

# 2. Supabase REST API로 각 테이블 접근 테스트
print("\n=== Supabase 연결 테스트 ===")
for tname in sorted(tables):
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/{tname}?select=*&limit=1',
        headers={
            'apikey': SERVICE_KEY,
            'Authorization': f'Bearer {SERVICE_KEY}',
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            body = r.read().decode()
            print(f"  [{r.status}] {tname}: OK — {body[:80]}")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {tname}: {e.reason}")
    except Exception as e:
        print(f"  [ERR] {tname}: {e}")

# 3. anon 키로 접근 테스트 (anon 키 = JWT role:anon)
# service_role JWT에서 anon 키를 알 수 없으므로 헤더 없이 테스트
print("\n=== anon(무인증) 접근 테스트 ===")
for tname in sorted(tables):
    req = urllib.request.Request(
        f'{SUPABASE_URL}/rest/v1/{tname}?select=*&limit=1',
        headers={
            'apikey': SERVICE_KEY,  # anon key 없으므로 service key로 role 변경 테스트
            'Authorization': 'Bearer invalid_token',  # 인증 무효 토큰
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            print(f"  [OPEN!] {tname}: 인증 없이 접근 가능 — 취약점!")
    except urllib.error.HTTPError as e:
        print(f"  [{e.code}] {tname}: 차단됨 ({e.reason})")
    except Exception as e:
        print(f"  [ERR] {tname}: {e}")
