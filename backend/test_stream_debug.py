"""Debug SSE stream - read raw bytes."""
import asyncio
import httpx

async def main():
    print("Testing SSE stream - raw bytes...")
    async with httpx.AsyncClient(timeout=30) as c:
        async with c.stream(
            "POST",
            "http://localhost:8000/api/reports/stream",
            json={
                "quarter": "Q3-2026", "region": "NA", "segment": "Enterprise",
                "persona": "cro", "scenario_id": "na_healthy"
            }
        ) as r:
            print(f"Status: {r.status_code}, CT: {r.headers.get('content-type')}")
            count = 0
            async for chunk in r.aiter_bytes():
                if chunk:
                    print(f"CHUNK({len(chunk)}): {chunk[:200]}")
                    count += 1
                    if count >= 3:
                        break
            print(f"Got {count} chunks")

asyncio.run(main())
