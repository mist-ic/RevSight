"""Test just the two remaining failing endpoints."""
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=15) as c:

        # 1. Metrics - should aggregate to 4 stages
        r = await c.get("http://localhost:8000/api/metrics/pipeline", params={
            "scenario_id": "na_healthy", "quarter": "Q3-2026",
            "region": "NA", "segment": "Enterprise"
        })
        stages = r.json().get("metrics", [])
        names = [s["stage_name"] for s in stages]
        print(f"Metrics: {len(stages)} stages -> {names}")
        if len(stages) == 4:
            print("[PASS] Metrics grouped correctly")
        else:
            print(f"[FAIL] Expected 4 stages, got {len(stages)}")

        # 2. GET /api/reports/{run_id}
        r2 = await c.get("http://localhost:8000/api/runs", params={"limit": 1})
        run_id = r2.json()["runs"][0]["id"]
        r3 = await c.get(f"http://localhost:8000/api/reports/{run_id}")
        print(f"GET report: HTTP {r3.status_code}")
        if r3.status_code == 200:
            d = r3.json()
            print(f"  status={d['status']}")
            print(f"  overall_status={d.get('report', {}).get('overall_status')}")
            print("[PASS] GET report works")
        else:
            print(f"[FAIL] {r3.text[:300]}")

asyncio.run(main())
