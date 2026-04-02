"""Quick DB data verification."""
import asyncio, os
from dotenv import load_dotenv
load_dotenv()
import asyncpg

async def main():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    rows = await conn.fetch("""
        SELECT scenario_id, COUNT(*) as opps, SUM(arr) as total_arr
        FROM opportunities
        GROUP BY scenario_id ORDER BY scenario_id
    """)
    print("Opportunities by scenario:")
    for r in rows:
        print(f"  {r['scenario_id']}: {r['opps']} opps, ${r['total_arr']/1e6:.1f}M ARR")

    mv = await conn.fetch("SELECT scenario_id, stage_name, deal_count, total_arr FROM mv_pipeline_metrics ORDER BY scenario_id, stage_name LIMIT 15")
    print("\nMaterialized view sample:")
    for r in mv:
        print(f"  {r['scenario_id']} | {r['stage_name']:<20} | {r['deal_count']} deals | ${(r['total_arr'] or 0)/1e6:.2f}M")

    await conn.close()

asyncio.run(main())
