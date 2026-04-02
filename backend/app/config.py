import os
from dotenv import load_dotenv

load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "")

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
LITELLM_PRIMARY_MODEL = os.getenv("LITELLM_PRIMARY_MODEL", "gpt-4o")
LITELLM_FALLBACK_MODEL = os.getenv("LITELLM_FALLBACK_MODEL", "claude-sonnet-4-5")

# Observability
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "true")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "revsight")
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN", "")

# App settings
REQUIRE_APPROVAL = os.getenv("REQUIRE_APPROVAL", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
API_PORT = int(os.getenv("API_PORT", "8000"))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
