lines = open('D:/CascadeProjects/app.py', encoding='utf-8').readlines()

# FSS API 키 및 연동 위치
print("=== FSS API 키/연동 ===")
for i, ln in enumerate(lines):
    s = ln.strip()
    if any(k in s for k in ['fss', 'FSS', '금감원', 'finlife', 'FINLIFE', 'open_api', 'fss_api']):
        if any(k in s for k in ['api', 'key', 'url', 'request', 'get', 'API', 'KEY', 'secret', 'token']):
            print(f'L{i+1}: {s[:110]}')

# secrets.toml에서 FSS 키 확인
import os
sec_path = r'C:\Users\insus\CascadeProjects\.streamlit\secrets.toml'
if os.path.exists(sec_path):
    with open(sec_path, encoding='utf-8') as f:
        for i, ln in enumerate(f):
            if any(k in ln.lower() for k in ['fss', 'finlife', '금감원', 'api_key', 'coocon', 'codef']):
                print(f'secrets.toml L{i+1}: {ln.strip()[:100]}')

# GK-SEC-10 함수 내 fetch 시뮬레이션 위치
print("\n=== _sec10_simulate_fetch 위치 ===")
for i, ln in enumerate(lines):
    if '_sec10_simulate_fetch' in ln or 'simulate_fetch' in ln:
        print(f'L{i+1}: {ln.strip()[:100]}')
