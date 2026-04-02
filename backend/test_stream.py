"""Test SSE stream endpoint directly."""
import asyncio
import json
import httpx

async def main():
    print("Testing SSE stream (takes 60-90s)...")
    events = []
    async with httpx.AsyncClient(timeout=180) as c:
        async with c.stream(
            "POST",
            "http://localhost:8000/api/reports/stream",
            json={
                "quarter": "Q3-2026", "region": "NA", "segment": "Enterprise",
                "persona": "cro", "scenario_id": "na_healthy"
            }
        ) as r:
            print(f"Status: {r.status_code}")
            print(f"Content-Type: {r.headers.get('content-type')}")
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")

            buf = ""
            async for chunk in r.aiter_text():
                buf += chunk
                while "\n\n" in buf:
                    block, buf = buf.split("\n\n", 1)
                    for line in block.splitlines():
                        if line.startswith("data: "):
                            try:
                                evt = json.loads(line[6:])
                                events.append(evt)
                                print(f"  event: {evt.get('type')} {evt.get('node', '') or evt.get('name', '')}")
                                if evt.get("type") == "done":
                                    report = evt.get("report")
                                    if report:
                                        print(f"  overall_status: {report.get('overall_status')}")
                                    print("[PASS] SSE stream complete")
                                    return
                                if evt.get("type") == "error":
                                    print(f"[FAIL] Error: {evt.get('message')}")
                                    return
                            except json.JSONDecodeError:
                                pass

    print(f"[FAIL] No done event. Got {len(events)} events: {[e.get('type') for e in events]}")

asyncio.run(main())
