"""
Quick manual test client for the WS stream.
Install once: pip install websockets

Usage:
    python ws_test_client.py <job_id>
"""

import asyncio
import sys
import json
import websockets


async def main(job_id: str):
    uri = f"ws://localhost:8000/videos/{job_id}/stream"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            data = json.loads(message)
            print(data)
            if data.get("event") in ("done", "error"):
                break


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ws_test_client.py <job_id>")
        sys.exit(1)
    job_id = sys.argv[1]
    asyncio.run(main(job_id))
