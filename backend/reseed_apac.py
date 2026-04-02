"""
Fix: Drop the stage_name CHECK constraint so APAC data quality scenario
can insert intentionally inconsistent stage names (simulating real-world CRM mess).
Also re-seeds APAC cleanly.
"""
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

import asyncpg
from app.db.seed import seed_scenario, SCENARIOS


async def main():
    url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(url)

    print("Dropping stage_name CHECK constraint...")
    await conn.execute("""
        ALTER TABLE opportunities
        DROP CONSTRAINT IF EXISTS opportunities_stage_name_check
    """)
    print("Constraint dropped.")

    print("Clearing partial APAC data...")
    await conn.execute("""
        DELETE FROM activities
        WHERE opportunity_id IN (
            SELECT id FROM opportunities WHERE scenario_id = 'apac_dataquality'
        )
    """)
    await conn.execute("""
        DELETE FROM pipeline_stage_history
        WHERE opportunity_id IN (
            SELECT id FROM opportunities WHERE scenario_id = 'apac_dataquality'
        )
    """)
    await conn.execute("DELETE FROM opportunities WHERE scenario_id = 'apac_dataquality'")
    await conn.execute("""
        DELETE FROM contacts
        WHERE account_id IN (SELECT id FROM accounts WHERE region = 'APAC')
    """)
    await conn.execute("DELETE FROM accounts WHERE region = 'APAC'")
    await conn.execute("DELETE FROM users WHERE region = 'APAC'")
    print("Cleared.")

    apac = next(s for s in SCENARIOS if s["id"] == "apac_dataquality")
    await seed_scenario(conn, apac)

    print("Refreshing materialized view...")
    try:
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_pipeline_metrics")
    except Exception as e:
        print(f"  View refresh note: {e}")
        await conn.execute("REFRESH MATERIALIZED VIEW mv_pipeline_metrics")

    print("All done!")
    await conn.close()


asyncio.run(main())
