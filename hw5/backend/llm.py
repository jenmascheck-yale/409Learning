"""Model wiring: every agent talks to gpt-6-luna through the Portkey gateway.

The Portkey API key comes from the environment (PORTKEY_API_KEY) and is never
hard-coded. The key is kept in a .env OUTSIDE the submission folder (the course
root), so it never reaches GitHub; a local hw5/.env also works if someone clones
the repo and adds their own.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

BACKEND_DIR = Path(__file__).resolve().parent
HW5_DIR = BACKEND_DIR.parent

# Prefer a local hw5/.env; fall back to the course-root .env where the real key
# lives outside the submission folder.
for candidate in [HW5_DIR / ".env", HW5_DIR.parent.parent / ".env"]:
    if candidate.exists():
        load_dotenv(candidate)
        break

MODEL_NAME = os.getenv("PORTKEY_MODEL", "gpt-6-luna")
API_KEY = os.getenv("PORTKEY_API_KEY")
BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")


def build_model() -> OpenAIResponsesModel:
    """Build the shared gpt-6-luna model routed through Portkey."""
    if not API_KEY:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Add it to hw5/.env or the course-root .env "
            "(see .env.example)."
        )
    # Auth is the x-portkey-api-key header; the key's own config selects the provider.
    client = AsyncOpenAI(
        api_key="unused",
        base_url=BASE_URL,
        default_headers={"x-portkey-api-key": API_KEY},
    )
    # gpt-6-luna is a reasoning model; its function tools run on the Responses API.
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
