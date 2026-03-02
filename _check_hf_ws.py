"""HF Space WebSocket에 연결해서 Streamlit 앱 메시지(에러 포함) 수신"""
import asyncio, json, sys

async def check():
    try:
        import websockets
    except ImportError:
        print("websockets 없음 — pip install websockets")
        return

    url = "wss://goldkey-rich-goldkey-ai.hf.space/_stcore/stream"
    headers = {
        "Origin": "https://goldkey-rich-goldkey-ai.hf.space",
        "User-Agent": "Mozilla/5.0",
    }
    print(f"Connecting to {url}...")
    try:
        async with websockets.connect(url, additional_headers=headers, open_timeout=15) as ws:
            print("Connected!")
            # 초기 메시지 전송 (Streamlit 프로토콜)
            await ws.send(json.dumps({
                "type": "streamlitMessage",
                "apiVersion": 1,
            }))
            for _ in range(30):  # 최대 30개 메시지
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg) if isinstance(msg, str) else {}
                    mtype = data.get("type", "?")
                    print(f"MSG type={mtype}")
                    if mtype == "newSession":
                        print("  → newSession:", json.dumps(data)[:200])
                    elif mtype == "delta":
                        ops = data.get("delta", {}).get("ops", [])
                        for op in ops:
                            print(f"  → delta op: {str(op)[:200]}")
                    elif mtype == "sessionStatusChanged":
                        print(f"  → status: {data}")
                    elif "error" in str(data).lower() or "exception" in str(data).lower():
                        print(f"  *** ERROR MSG: {str(data)[:500]}")
                except asyncio.TimeoutError:
                    print("(timeout waiting for message)")
                    break
    except Exception as e:
        print(f"Connection error: {type(e).__name__}: {e}")

asyncio.run(check())
