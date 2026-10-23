"""Chat history storage for logged-in shoppers (Problem 8).

History is saved in the existing `chat_messages` table and reloaded when the
shopper returns. Guests are never written to the table, so their chat does not
persist.
"""

import json
import sqlite3

HISTORY_LIMIT = 40  # how many recent messages to reload for display on return
MODEL_HISTORY_LIMIT = 10  # how many recent messages to send to the model (cheaper/faster)


def load_history(conn: sqlite3.Connection, user_id: int) -> list[dict]:
    """Return the shopper's saved messages, oldest first, each as
    {role, content, products}."""
    rows = conn.execute(
        """SELECT role, content, products_json FROM chat_messages
           WHERE user_id = ? ORDER BY id DESC LIMIT ?""",
        (user_id, HISTORY_LIMIT),
    ).fetchall()
    rows = list(reversed(rows))  # back to oldest-first
    history = []
    for r in rows:
        products = json.loads(r["products_json"]) if r["products_json"] else []
        history.append({"role": r["role"], "content": r["content"], "products": products})
    return history


def save_turn(
    conn: sqlite3.Connection,
    user_id: int,
    user_message: str,
    assistant_reply: str,
    products: list | None = None,
) -> None:
    """Append one user message and the assistant's reply (with any product cards)."""
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'user', ?, NULL)",
        (user_id, user_message),
    )
    products_json = json.dumps(products) if products else None
    conn.execute(
        "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
        (user_id, assistant_reply, products_json),
    )
    conn.commit()
