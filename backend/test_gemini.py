"""
Quick test: verify gemini-3-flash-preview works with Pydantic AI
before wiring into all 4 agents.

Run: python test_gemini.py
"""
import asyncio
import os
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

os.environ["GEMINI_API_KEY"] = "REDACTED_API_KEY"

MODEL = "gemini-3-flash-preview"

# Settings: disable thinking budget (keeps it fast and deterministic for tool use)
settings = GoogleModelSettings(
    temperature=0.2,
    google_thinking_config={"thinking_budget": 0},
)


# Test 1: Basic structured output
class PipelineStatus(BaseModel):
    status: str
    coverage_ratio: float
    confidence: float
    summary: str


test_agent = Agent(
    model=f"google-gla:{MODEL}",
    output_type=PipelineStatus,
    model_settings=settings,
    instructions="""
    You are a revenue operations analyst. Analyze pipeline data and return structured output.
    Only use numbers provided to you. Do not invent values.
    """,
)


# Test 2: Tool calling
class ToolTestResult(BaseModel):
    computed_total: float
    item_count: int
    message: str


tool_agent = Agent(
    model=f"google-gla:{MODEL}",
    output_type=ToolTestResult,
    model_settings=settings,
    instructions="You compute sales metrics by calling tools. Always call the tool before answering.",
    deps_type=dict,
)


@tool_agent.tool
async def get_pipeline_data(ctx) -> list[dict]:
    """Return mock pipeline data for testing."""
    return [
        {"stage": "Discovery", "arr": 500_000, "deals": 10},
        {"stage": "Demo", "arr": 350_000, "deals": 7},
        {"stage": "Proposal", "arr": 200_000, "deals": 4},
    ]


async def main():
    print(f"Testing {MODEL} via Pydantic AI...\n")

    # Test 1: Structured output
    print("Test 1: Structured output")
    try:
        result = await test_agent.run(
            "The pipeline has 4.2x coverage and 28% win rate with good data quality. "
            "Coverage ratio is exactly 4.2. Confidence should be 0.85."
        )
        print(f"  status: {result.output.status}")
        print(f"  coverage_ratio: {result.output.coverage_ratio}")
        print(f"  confidence: {result.output.confidence}")
        print(f"  summary: {result.output.summary[:80]}...")
        print("  PASSED\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")

    # Test 2: Tool calling
    print("Test 2: Tool calling")
    try:
        result = await tool_agent.run(
            "Get the pipeline data and compute the total ARR across all stages. "
            "Count the number of items returned.",
            deps={},
        )
        print(f"  computed_total: {result.output.computed_total}")
        print(f"  item_count: {result.output.item_count}")
        print(f"  message: {result.output.message}")
        print("  PASSED\n")
    except Exception as e:
        print(f"  FAILED: {e}\n")

    print("All tests done.")


if __name__ == "__main__":
    asyncio.run(main())
