"""
Shared LLM model factory.
All agents import get_model() instead of hardcoding a provider string.
"""
from __future__ import annotations

import os
from pydantic_ai.models.google import GoogleModel, GoogleModelSettings

from app.config import GEMINI_API_KEY, PRIMARY_MODEL

# Low temperature + no thinking budget for deterministic tool-calling behavior
AGENT_SETTINGS = GoogleModelSettings(
    temperature=0.2,
    google_thinking_config={"thinking_budget": 0},
)


def get_model() -> GoogleModel:
    """Return a configured Gemini model instance."""
    if GEMINI_API_KEY:
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

    # Strip the provider prefix for GoogleModel (it takes just the model name)
    model_name = PRIMARY_MODEL.replace("google-gla:", "").replace("google-vertex:", "")
    return GoogleModel(model_name)
