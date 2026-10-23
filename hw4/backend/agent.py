"""Campus Customs PydanticAI agent wiring.

Loads the system prompt from prompts/prompt.md and talks to the model named in
PORTKEY_MODEL (gpt-6-luna) through the Portkey gateway. The Portkey API key comes
from the environment (PORTKEY_API_KEY) and is never hard-coded.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
import tools

# Loop limit: cap how many model requests one reply may make, so the tool-calling
# loop can never run away (Problem 12 safety spec).
REQUEST_LIMIT = 6

BACKEND_DIR = Path(__file__).resolve().parent
HW4_DIR = BACKEND_DIR.parent

# Prefer a local hw4/.env (for anyone who clones the repo and makes their own);
# fall back to the course-root .env, where the real key is kept outside the
# submission folder so it never reaches GitHub.
for candidate in [HW4_DIR / ".env", HW4_DIR.parent.parent / ".env"]:
    if candidate.exists():
        load_dotenv(candidate)
        break

MODEL_NAME = os.getenv("PORTKEY_MODEL", "gpt-6-luna")
API_KEY = os.getenv("PORTKEY_API_KEY")
BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1")

SYSTEM_PROMPT = (BACKEND_DIR / "prompts" / "prompt.md").read_text(encoding="utf-8")


def build_agent() -> Agent:
    if not API_KEY:
        raise RuntimeError(
            "PORTKEY_API_KEY is not set. Add it to hw4/.env (see .env.example)."
        )
    # Calls go through the Portkey gateway to gpt-6-luna. The Portkey API key is
    # sent as a header; the key's own default config selects the OpenAI provider.
    client = AsyncOpenAI(
        api_key="unused",  # auth is the x-portkey-api-key header below
        base_url=BASE_URL,
        default_headers={"x-portkey-api-key": API_KEY},
    )
    # gpt-6-luna is a reasoning model; its function tools run on the Responses API.
    model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    return Agent(
        model,
        system_prompt=SYSTEM_PROMPT,
        deps_type=tools.ChatDeps,
        tools=tools.ALL_TOOLS,
    )


agent = build_agent()


@agent.instructions
def who_and_where(ctx: RunContext[tools.ChatDeps]) -> str:
    """Tell the agent who it is talking to and what page they are on."""
    lines = []
    if ctx.deps.user_name:
        lines.append(
            f"You are chatting with {ctx.deps.user_name} ({ctx.deps.user_email}), "
            "a logged-in shopper. Greet them by their first name and keep it personal."
        )
    else:
        lines.append("You are chatting with a guest who is not logged in.")
    if ctx.deps.current_product_name:
        lines.append(
            f'The shopper is currently viewing the product page for '
            f'"{ctx.deps.current_product_name}" (product_id: {ctx.deps.current_product_id}). '
            'If they say "this" or "this one" or ask about it without naming a product '
            "(e.g. \"do you have this in pink?\"), they mean this product — use it when "
            "calling your tools."
        )
    return " ".join(lines)


def history_to_messages(history: list[dict]) -> list[ModelMessage]:
    """Turn saved {role, content} rows into PydanticAI message history so the
    agent remembers the earlier conversation."""
    messages: list[ModelMessage] = []
    for turn in history:
        if turn["role"] == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn["content"])]))
        elif turn["role"] == "assistant":
            messages.append(ModelResponse(parts=[TextPart(content=turn["content"])]))
    return messages


def reply_to(
    message: str,
    deps: tools.ChatDeps | None = None,
    history: list[dict] | None = None,
) -> tuple[str, list]:
    """Send a shopper message to the agent and return (reply text, product cards
    the search tool found). `deps` carries who is chatting and the current page;
    `history` is the shopper's earlier saved conversation."""
    deps = deps or tools.ChatDeps()
    message_history = history_to_messages(history) if history else None
    result = agent.run_sync(
        message,
        deps=deps,
        message_history=message_history,
        usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
    )

    # De-duplicate the found products, keeping first-seen order.
    seen: set[str] = set()
    products = []
    for card in deps.found:
        if card.product_id not in seen:
            seen.add(card.product_id)
            products.append(card)

    _record_audit(message, result, products)
    return result.output, products


def _record_audit(message: str, result, products: list) -> None:
    """Append this run's tool activity and outcome to the audit trail."""
    now = datetime.now(timezone.utc).isoformat()
    events: list[dict] = []

    # Pair each tool call with its return, pulled from the run's messages.
    calls: dict[str, tuple[str, object]] = {}
    for msg in result.all_messages():
        for part in getattr(msg, "parts", []):
            kind = getattr(part, "part_kind", "")
            if kind == "tool-call":
                calls[getattr(part, "tool_call_id", "")] = (
                    getattr(part, "tool_name", "?"),
                    getattr(part, "args", None),
                )
            elif kind == "tool-return":
                name, args = calls.get(
                    getattr(part, "tool_call_id", ""),
                    (getattr(part, "tool_name", "?"), None),
                )
                events.append(
                    {
                        "time": now,
                        "tool": name,
                        "args": audit._short(args) if args is not None else "",
                        "result": audit._short(getattr(part, "content", "")),
                        "stop_reason": "tool_call",
                    }
                )

    # Final entry for the run itself.
    events.append(
        {
            "time": now,
            "tool": None,
            "args": audit._short(message),
            "result": audit._short(result.output),
            "stop_reason": "end",
            "tool_calls": len(events),
            "products_returned": len(products),
        }
    )
    try:
        audit.append_events(events)
    except Exception:
        pass  # auditing must never break a reply
