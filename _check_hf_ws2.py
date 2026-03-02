"""HF Space WebSocket — Streamlit 프로토콜로 연결하여 에러 내용 수신"""
import asyncio, json

async def check():
    import websockets

    url = "wss://goldkey-rich-goldkey-ai.hf.space/_stcore/stream"
    headers = {
        "Origin": "https://goldkey-rich-goldkey-ai.hf.space",
        "User-Agent": "Mozilla/5.0",
    }
    print(f"Connecting...")
    async with websockets.connect(url, additional_headers=headers, open_timeout=15) as ws:
        print("Connected — waiting for messages (raw):")
        for i in range(20):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                if isinstance(msg, bytes):
                    print(f"  [{i}] binary({len(msg)}b): {msg[:200]}")
                else:
                    print(f"  [{i}] text: {msg[:400]}")
            except asyncio.TimeoutError:
                print("  (timeout)")
                break

asyncio.run(check())
