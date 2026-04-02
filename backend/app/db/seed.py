"""
RevSight seed data generator.
Generates 3 distinct pipeline scenarios for demo purposes.

Run: python -m app.db.seed
"""
from __future__ import annotations

import asyncio
import random
import uuid
from datetime import datetime, timedelta, date
from typing import Any

import asyncpg
from faker import Faker

from app.config import DATABASE_URL

fake = Faker()
random.seed(42)

QUARTER = "Q3-2026"
QUOTA_PER_SCENARIO = 5_000_000  # $5M quota baseline

SCENARIOS = [
    {
        "id": "na_healthy",
        "region": "NA",
        "segment": "Enterprise",
        "label": "NA Enterprise Q3 -- Healthy",
        "n_accounts": 60,
        "n_opportunities": 500,
        "n_activities": 1800,
        "stage_weights": {
            "Discovery": 0.30,
            "Demo": 0.25,
            "Proposal": 0.20,
            "Negotiation": 0.15,
            "Closed Won": 0.07,
            "Closed Lost": 0.03,
        },
        "avg_arr": 45_000,
        "arr_stddev": 15_000,
        "missing_close_date_pct": 0.01,
        "close_date_past_pct": 0.05,
        "duplicate_stage_pct": 0.0,
    },
    {
        "id": "emea_undercovered",
        "region": "EMEA",
        "segment": "SMB",
        "label": "EMEA SMB Q3 -- Under-covered",
        "n_accounts": 80,
        "n_opportunities": 600,
        "n_activities": 1500,
        "stage_weights": {
            "Discovery": 0.45,
            "Demo": 0.30,
            "Proposal": 0.15,
            "Negotiation": 0.08,
            "Closed Won": 0.01,
            "Closed Lost": 0.01,
        },
        "avg_arr": 12_000,
        "arr_stddev": 5_000,
        "missing_close_date_pct": 0.03,
        "close_date_past_pct": 0.10,
        "duplicate_stage_pct": 0.0,
    },
    {
        "id": "apac_dataquality",
        "region": "APAC",
        "segment": "Enterprise",
        "label": "APAC Enterprise Q3 -- Data Quality Risk",
        "n_accounts": 60,
        "n_opportunities": 400,
        "n_activities": 1700,
        "stage_weights": {
            "Discovery": 0.25,
            "Demo": 0.22,
            "Proposal": 0.20,
            "Negotiation": 0.18,
            "Closed Won": 0.10,
            "Closed Lost": 0.05,
        },
        "avg_arr": 65_000,
        "arr_stddev": 30_000,
        "missing_close_date_pct": 0.30,
        "close_date_past_pct": 0.15,
        "duplicate_stage_pct": 0.05,  # inconsistent stage names
    },
]

INCONSISTENT_STAGE_NAMES = [
    "discovery", "DISCOVERY", "initial discovery", "disc",
    "Demo Call", "demo meeting", "DEMO",
    "prop", "Proposal Sent", "PROPOSAL",
]

ACTIVITY_TYPES = ["call", "email", "meeting", "note", "task"]
INDUSTRIES = ["SaaS", "FinTech", "Healthcare", "Manufacturing", "Retail", "Logistics"]
TITLES = ["VP Sales", "CRO", "Director of RevOps", "Head of Sales", "AE Manager"]


def random_stage(weights: dict[str, float], allow_inconsistent: bool = False) -> str:
    stage = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    if allow_inconsistent and stage in ("Discovery", "Demo", "Proposal") and random.random() < 0.15:
        return random.choice(INCONSISTENT_STAGE_NAMES)
    return stage


def close_date_for(stage: str, missing_pct: float, past_pct: float) -> date | None:
    if random.random() < missing_pct:
        return None
    base = date.today()
    if random.random() < past_pct:
        return base - timedelta(days=random.randint(5, 60))
    return base + timedelta(days=random.randint(20, 120))


async def seed_scenario(conn: asyncpg.Connection, scenario: dict[str, Any]) -> None:
    print(f"  Seeding: {scenario['label']}")

    user_ids: list[str] = []
    for _ in range(10):
        uid = str(uuid.uuid4())
        user_ids.append(uid)
        await conn.execute(
            """
            INSERT INTO users (id, name, email, role, region)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT DO NOTHING
            """,
            uid, fake.name(), fake.unique.email(),
            random.choice(["ae", "sdr", "manager"]),
            scenario["region"],
        )

    account_ids: list[str] = []
    for _ in range(scenario["n_accounts"]):
        aid = str(uuid.uuid4())
        account_ids.append(aid)
        await conn.execute(
            """
            INSERT INTO accounts (id, name, domain, industry, arr_segment, owner_id, region)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
            """,
            aid,
            fake.company(),
            fake.domain_name(),
            random.choice(INDUSTRIES),
            scenario["segment"],
            random.choice(user_ids),
            scenario["region"],
        )

    contact_ids: list[str] = []
    for aid in account_ids:
        for _ in range(random.randint(2, 5)):
            cid = str(uuid.uuid4())
            contact_ids.append(cid)
            await conn.execute(
                """
                INSERT INTO contacts (id, account_id, email, full_name, title, lifecycle_stage, lead_source)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                """,
                cid, aid, fake.unique.email(), fake.name(),
                random.choice(TITLES),
                random.choice(["sql", "sal", "opportunity"]),
                random.choice(["inbound", "outbound", "referral", "event"]),
            )

    opp_ids: list[str] = []
    for _ in range(scenario["n_opportunities"]):
        oid = str(uuid.uuid4())
        opp_ids.append(oid)
        stage = random_stage(
            scenario["stage_weights"],
            allow_inconsistent=scenario["duplicate_stage_pct"] > 0,
        )
        arr = max(1000, int(random.gauss(scenario["avg_arr"], scenario["arr_stddev"])))
        prob_map = {
            "Discovery": 10, "Demo": 25, "Proposal": 40,
            "Negotiation": 60, "Closed Won": 100, "Closed Lost": 0,
        }
        probability = prob_map.get(stage, random.randint(10, 60))
        close_dt = close_date_for(stage, scenario["missing_close_date_pct"], scenario["close_date_past_pct"])

        await conn.execute(
            """
            INSERT INTO opportunities (
                id, account_id, contact_id, owner_id, name, stage_name, arr, probability,
                forecast_category, close_date, quarter, region, segment, scenario_id,
                created_at, updated_at
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16)
            ON CONFLICT DO NOTHING
            """,
            oid,
            random.choice(account_ids),
            random.choice(contact_ids),
            random.choice(user_ids),
            f"{fake.bs().title()} - {fake.company()}",
            stage,
            arr,
            probability,
            random.choice(["Pipeline", "Best Case", "Commit"]),
            close_dt,
            QUARTER,
            scenario["region"],
            scenario["segment"],
            scenario["id"],
            datetime.now() - timedelta(days=random.randint(1, 180)),
            datetime.now() - timedelta(days=random.randint(0, 30)),
        )

        # Stage history for each opportunity (1-3 transitions)
        prev_stage: str | None = None
        for hist_stage in ["Discovery", "Demo", "Proposal", "Negotiation"]:
            if hist_stage == stage:
                break
            await conn.execute(
                """
                INSERT INTO pipeline_stage_history (id, opportunity_id, from_stage, to_stage, changed_at, changed_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT DO NOTHING
                """,
                str(uuid.uuid4()), oid, prev_stage, hist_stage,
                datetime.now() - timedelta(days=random.randint(5, 100)),
                random.choice(user_ids),
            )
            prev_stage = hist_stage

    # Activities
    for _ in range(scenario["n_activities"]):
        await conn.execute(
            """
            INSERT INTO activities (id, opportunity_id, contact_id, type, outcome, duration_mins, occurred_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
            """,
            str(uuid.uuid4()),
            random.choice(opp_ids),
            random.choice(contact_ids),
            random.choice(ACTIVITY_TYPES),
            random.choice(["positive", "neutral", "negative", None]),
            random.randint(5, 120),
            datetime.now() - timedelta(days=random.randint(0, 90)),
        )

    print(f"    Done: {len(opp_ids)} opportunities, {len(account_ids)} accounts")


async def main():
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL environment variable not set")
        return

    print("Connecting to database...")
    conn = await asyncpg.connect(DATABASE_URL)

    try:
        print("Running migration...")
        with open("app/db/migrations/001_init.sql") as f:
            await conn.execute(f.read())

        print("Seeding scenarios...")
        for scenario in SCENARIOS:
            await seed_scenario(conn, scenario)

        print("Refreshing materialized view...")
        await conn.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY mv_pipeline_metrics")

        print("\nSeed complete!")
        print(f"  Scenarios: {', '.join(s['id'] for s in SCENARIOS)}")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
