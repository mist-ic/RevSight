"""Quick focused backend test."""
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(timeout=180) as c:

        # Health
        r = await c.get("http://localhost:8000/health")
        print(f"Health: {r.status_code} {r.json()}")

        # Metrics
        r = await c.get("http://localhost:8000/api/metrics/pipeline", params={
            "scenario_id": "na_healthy", "quarter": "Q3-2026",
            "region": "NA", "segment": "Enterprise"
        })
        d = r.json()
        print(f"Metrics: {r.status_code} -> {len(d.get('metrics', []))} stages")
        for row in d.get("metrics", []):
            print(f"  {row['stage_name']}: {row['deal_count']} deals")

        # Runs
        r = await c.get("http://localhost:8000/api/runs", params={"limit": 5})
        print(f"Runs: {r.status_code} -> {len(r.json().get('runs', []))} entries")

        # Full pipeline
        print("\nRunning NA pipeline (wait ~60s)...")
        r = await c.post(
            "http://localhost:8000/api/reports",
            json={
                "quarter": "Q3-2026", "region": "NA", "segment": "Enterprise",
                "persona": "cro", "scenario_id": "na_healthy"
            },
            timeout=180
        )
        print(f"Pipeline: HTTP {r.status_code}")
        if r.status_code != 200:
            print(f"ERROR: {r.text[:800]}")
            return

        result = r.json()
        rep = result.get("report", {})
        print(f"  run_id:             {result.get('run_id','?')[:8]}")
        print(f"  status:             {result.get('status')}")
        print(f"  overall_status:     {rep.get('overall_status')}")
        print(f"  forecast_confidence:{rep.get('forecast_confidence')}")
        print(f"  metrics count:      {len(rep.get('key_metrics', []))}")
        print(f"  risks count:        {len(rep.get('risks', []))}")
        print(f"  actions count:      {len(rep.get('recommended_actions', []))}")
        print(f"  data_quality_flags: {rep.get('data_quality_flags', [])}")
        print(f"\n  Executive summary snippet:")
        print(f"  {rep.get('executive_summary','')[:200]}")

        if result.get("status") == "approved" and rep.get("overall_status"):
            print("\n[ALL PASS] Backend pipeline working correctly")
        else:
            print("\n[FAIL] Unexpected result")

asyncio.run(main())
