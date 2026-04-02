"""Run ingestion agent directly to see the real exception."""
import asyncio
import os
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.agents.schemas.request import ReportRequest, Persona
from app.agents.nodes.ingestion import run_ingestion
from app.db.connection import init_db

async def main():
    await init_db()
    req = ReportRequest(
        quarter="Q3-2026", region="NA", segment="Enterprise",
        persona=Persona.CRO, scenario_id="na_healthy"
    )
    try:
        result = await run_ingestion(req, db=None)
        print("Ingestion OK:", result)
    except Exception as e:
        import traceback
        print("INGESTION ERROR:")
        traceback.print_exc()

asyncio.run(main())
