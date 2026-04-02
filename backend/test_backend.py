"""Full backend integration test -- hits every endpoint with assertions."""
import asyncio
import json
import httpx

BASE = "http://localhost:8000"


async def main():
    async with httpx.AsyncClient(timeout=30) as c:

        # 1. Health
        r = await c.get(f"{BASE}/health")
        assert r.status_code == 200
        print(f"[PASS] GET /health")

        # 2. Metrics - must return exactly 4 stages
        r = await c.get(f"{BASE}/api/metrics/pipeline", params={
            "scenario_id": "na_healthy", "quarter": "Q3-2026",
            "region": "NA", "segment": "Enterprise"
        })
        assert r.status_code == 200
        stages = r.json()["metrics"]
        assert len(stages) == 4, f"Expected 4 stages, got {len(stages)}"
        stage_names = [s["stage_name"] for s in stages]
        assert stage_names == ["Discovery", "Demo", "Proposal", "Negotiation"]
        print(f"[PASS] GET /api/metrics/pipeline -> {stage_names}")

        # 3. Runs list
        r = await c.get(f"{BASE}/api/runs", params={"limit": 5})
        assert r.status_code == 200
        runs = r.json()["runs"]
        print(f"[PASS] GET /api/runs -> {len(runs)} entries")

    # 4. Full pipeline POST (needs longer timeout)
    async with httpx.AsyncClient(timeout=180) as c:
        print(f"\n[TEST] POST /api/reports (NA Healthy, takes ~60s)...")
        r = await c.post(f"{BASE}/api/reports", json={
            "quarter": "Q3-2026", "region": "NA", "segment": "Enterprise",
            "persona": "cro", "scenario_id": "na_healthy"
        })
        assert r.status_code == 200, f"FAIL: {r.status_code} {r.text[:300]}"
        result = r.json()
        assert result["status"] == "approved"
        rep = result["report"]
        assert rep["overall_status"] in ("healthy", "watch", "at_risk")
        run_id = result["run_id"]
        print(f"[PASS] POST /api/reports -> {run_id[:8]} status={result['status']} overall={rep['overall_status']}")

        # 5. GET report by run_id
        r = await c.get(f"{BASE}/api/reports/{run_id}")
        assert r.status_code == 200, f"FAIL: {r.text[:300]}"
        fetched = r.json()
        assert fetched["run_id"] == run_id
        assert fetched["report"] is not None
        print(f"[PASS] GET /api/reports/{run_id[:8]}")

        # 6. SSE stream
        print(f"\n[TEST] POST /api/reports/stream (SSE, EMEA scenario)...")
        events = []
        async with c.stream("POST", f"{BASE}/api/reports/stream", json={
            "quarter": "Q3-2026", "region": "EMEA", "segment": "SMB",
            "persona": "revops", "scenario_id": "emea_undercovered"
        }, timeout=180) as sr:
            assert sr.status_code == 200
            assert "text/event-stream" in sr.headers.get("content-type", "")
            async for line in sr.aiter_lines():
                line = line.strip()
                if not line.startswith("data: "):
                    continue
                try:
                    evt = json.loads(line[6:])
                    events.append(evt)
                    print(f"  event: {evt.get('type')} {evt.get('node','') or evt.get('name','')}")
                    if evt.get("type") in ("done", "error"):
                        break
                except json.JSONDecodeError:
                    pass

        done = [e for e in events if e.get("type") == "done"]
        assert done, f"No done event. Got: {[e.get('type') for e in events]}"
        stream_rep = done[0].get("report")
        assert stream_rep is not None
        print(f"[PASS] SSE stream -> {len(events)} events, overall={stream_rep.get('overall_status')}")

    print("\n=== ALL 6 BACKEND TESTS PASSED ===")


asyncio.run(main())
