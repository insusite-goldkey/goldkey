"""HF Space Streamlit WebSocket 여러 경로 시도"""
import asyncio, urllib.request, json

def http_check(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            return r.status, r.read(500).decode('utf-8', 'replace')
    except Exception as e:
        return None, str(e)

# HTTP 엔드포인트 먼저 확인
for path in ["/_stcore/health", "/_stcore/allowed-message-origins", "/healthz"]:
    url = f"https://goldkey-rich-goldkey-ai.hf.space{path}"
    status, body = http_check(url)
    print(f"GET {path}: {status} → {body[:100]}")

print()

# WebSocket 여러 경로 시도
async def try_ws(path):
    import websockets
    url = f"wss://goldkey-rich-goldkey-ai.hf.space{path}"
    try:
        async with websockets.connect(
            url,
            additional_headers={"Origin": "https://goldkey-rich-goldkey-ai.hf.space"},
            open_timeout=10
        ) as ws:
            print(f"WS {path}: connected")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"  → first msg: {str(msg)[:200]}")
            except asyncio.TimeoutError:
                print(f"  → timeout (no messages)")
    except Exception as e:
        print(f"WS {path}: FAIL — {type(e).__name__}: {e}")

async def main():
    for path in ["/_stcore/stream", "/stream", "/_stcore/websocket"]:
        await try_ws(path)

asyncio.run(main())
