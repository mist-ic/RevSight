"""Clean up stuck running/pending runs in the database."""
import asyncio
from app.db.connection import init_db, execute_write

async def main():
    await init_db()
    r1 = await execute_write(
        "UPDATE runs SET status = 'failed', completed_at = NOW() WHERE status = 'running'"
    )
    print(f"Cleaned running -> failed: {r1}")
    r2 = await execute_write(
        "UPDATE runs SET status = 'failed', completed_at = NOW() WHERE status = 'pending'"
    )
    print(f"Cleaned pending -> failed: {r2}")

asyncio.run(main())
