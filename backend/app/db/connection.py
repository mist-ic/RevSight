from __future__ import annotations

import asyncpg
import logging
from app.config import DATABASE_URL

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def init_db():
    global _pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set -- running without DB")
        return
    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=2,
        max_size=10,
        command_timeout=30,
    )
    logger.info("Database pool initialized")


async def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_db() first.")
    return _pool


async def execute_query(sql: str, *args) -> list[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *args)
        return [dict(row) for row in rows]


async def execute_one(sql: str, *args) -> dict | None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *args)
        return dict(row) if row else None


async def execute_write(sql: str, *args) -> str:
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.execute(sql, *args)
