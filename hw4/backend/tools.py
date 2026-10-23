"""Tools the Campus Customs agent can call.

These look up real information from campus_customs.db so the agent never invents
prices or quantities. Each tool finds the product from how a shopper describes it
(matching on product name, type, and search tags, not just an exact id) and then
returns a structured result. If nothing matches, or several things do, the tool
returns a short message so the agent can ask which item the shopper means.
"""

import os
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import RunContext

from models import (
    CategoryCount,
    ProductCard,
    ProductDescription,
    ProductPrice,
    ProductStock,
    SizeStock,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
SEARCH_LIMIT = 12  # cap how many cards a single search puts on the page


@dataclass
class ChatDeps:
    """Per-request state the agent can see.

    - who is chatting (name/email) for a logged-in shopper, so the agent can
      greet them personally;
    - the product page they are currently on, so "do you have this in pink?"
      resolves to the right item;
    - `found`: the search tool records the product cards it returned here so the
      chat route can send them to the website (the Problem 7 API contract)."""

    user_name: str | None = None
    user_email: str | None = None
    current_product_id: str | None = None
    current_product_name: str | None = None
    found: list[ProductCard] = field(default_factory=list)


def _db() -> sqlite3.Connection:
    hw4_dir = Path(__file__).resolve().parent.parent
    data_dir = (hw4_dir / os.getenv("DATA_DIR", "../data")).resolve()
    conn = sqlite3.connect(data_dir / "campus_customs.db")
    conn.row_factory = sqlite3.Row
    return conn


def _find_matches(conn: sqlite3.Connection, query: str) -> list[sqlite3.Row]:
    """Find catalogue rows matching how a shopper describes a product."""
    q = query.strip().lower()
    if not q:
        return []

    # Exact product id first.
    row = conn.execute(
        "SELECT * FROM catalogue WHERE lower(product_id) = ?", (q,)
    ).fetchone()
    if row:
        return [row]

    # Whole phrase appearing in name, type, tags, or description.
    like = f"%{q}%"
    rows = conn.execute(
        """SELECT * FROM catalogue
           WHERE lower(name) LIKE ? OR lower(garment_type) LIKE ?
                 OR lower(search_tags) LIKE ? OR lower(description) LIKE ?
           ORDER BY CASE WHEN lower(name) LIKE ? THEN 0 ELSE 1 END, name""",
        (like, like, like, like, like),
    ).fetchall()
    if rows:
        return rows

    # Fall back: every meaningful word must appear in the name or tags.
    words = [w for w in re.findall(r"[a-z0-9]+", q) if len(w) > 2]
    if words:
        clause = " AND ".join(
            ["(lower(name) LIKE ? OR lower(search_tags) LIKE ?)"] * len(words)
        )
        params: list[str] = []
        for w in words:
            params += [f"%{w}%", f"%{w}%"]
        rows = conn.execute(
            f"SELECT * FROM catalogue WHERE {clause} ORDER BY name", params
        ).fetchall()
    return rows


def _too_many(rows: list[sqlite3.Row], query: str) -> str:
    names = ", ".join(r["name"] for r in rows[:5])
    more = " (and more)" if len(rows) > 5 else ""
    return (
        f"Several products match '{query}': {names}{more}. "
        "Ask the shopper which one they mean."
    )


def _none(query: str) -> str:
    return (
        f"No product found matching '{query}'. Ask the shopper to use the "
        "product name as it appears on the site."
    )


def get_product_description(product_query: str) -> ProductDescription | str:
    """Look up a product's description from the catalogue. `product_query` is how
    the shopper refers to the item (a name, type, or keywords)."""
    with _db() as conn:
        rows = _find_matches(conn, product_query)
    if not rows:
        return _none(product_query)
    if len(rows) > 1:
        return _too_many(rows, product_query)
    r = rows[0]
    return ProductDescription(
        product_id=r["product_id"],
        name=r["name"],
        garment_type=r["garment_type"],
        description=r["description"],
    )


def get_product_price(product_query: str) -> ProductPrice | str:
    """Look up a product's price from the catalogue. Never guess a price; always
    use this tool for price questions."""
    with _db() as conn:
        rows = _find_matches(conn, product_query)
    if not rows:
        return _none(product_query)
    if len(rows) > 1:
        return _too_many(rows, product_query)
    r = rows[0]
    return ProductPrice(product_id=r["product_id"], name=r["name"], price=r["price"])


def get_product_stock(product_query: str, size: str | None = None) -> ProductStock | str:
    """Look up how many of a product are in stock. Pass `size` (XS, S, M, L, XL,
    XXL) when the shopper asks about a specific size; otherwise every size is
    returned. Quantity 0 means that size is sold out. Always use this tool for
    stock questions; never guess quantities."""
    with _db() as conn:
        rows = _find_matches(conn, product_query)
        if not rows:
            return _none(product_query)
        if len(rows) > 1:
            return _too_many(rows, product_query)
        r = rows[0]
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?",
            (r["product_id"],),
        ).fetchall()

    sizes = [
        SizeStock(size=s["size"], quantity=s["quantity"], in_stock=s["quantity"] > 0)
        for s in stock
    ]
    if size:
        wanted = size.strip().upper()
        sizes = [s for s in sizes if s.size.upper() == wanted]
        if not sizes:
            return (
                f"'{r['name']}' does not come in size {size}. "
                "Available sizes are XS, S, M, L, XL, XXL."
            )
    sizes.sort(key=lambda s: SIZE_ORDER.index(s.size) if s.size in SIZE_ORDER else 99)
    return ProductStock(product_id=r["product_id"], name=r["name"], sizes=sizes)


def _card(r: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=r["product_id"],
        name=r["name"],
        price=r["price"],
        garment_type=r["garment_type"],
        image_url=f"/images/{r['image_file_path']}",
        description=r["description"],
    )


def _search_cards(query: str) -> list[ProductCard]:
    """Find products matching a type/keyword query (forgiving about plurals)."""
    q = query.strip().lower()
    if not q:
        return []
    terms: set[str] = {q}
    if q.endswith("s"):
        terms.add(q[:-1])
    for w in re.findall(r"[a-z0-9]+", q):
        if len(w) > 2:
            terms.add(w)
            if w.endswith("s"):
                terms.add(w[:-1])

    conds, params = [], []
    for t in terms:
        like = f"%{t}%"
        conds.append(
            "(lower(name) LIKE ? OR lower(garment_type) LIKE ? OR lower(search_tags) LIKE ?)"
        )
        params += [like, like, like]
    with _db() as conn:
        rows = conn.execute(
            f"SELECT * FROM catalogue WHERE {' OR '.join(conds)} ORDER BY name LIMIT ?",
            params + [SEARCH_LIMIT],
        ).fetchall()
    return [_card(r) for r in rows]


def search_products(ctx: RunContext[ChatDeps], query: str) -> list[ProductCard]:
    """Search the catalogue for a type or keyword the shopper mentions (for
    example 'hoodies', 'quarter zip', 'Saybrook'). Call this whenever the shopper
    asks what you have of some kind of item. The matching products are shown to
    the shopper as cards on the website, so after calling this, just summarize
    them briefly in words (don't list every one)."""
    cards = _search_cards(query)
    ctx.deps.found.extend(cards)
    return cards


def category_of(garment_type: str) -> str:
    """Group a messy garment_type label into a friendly shopper category."""
    t = garment_type.lower()
    if "hood" in t:
        return "Hoodies"
    if "crew" in t:
        return "Crewnecks"
    if "zip" in t:
        return "Quarter-Zips"
    if "jacket" in t:
        return "Jackets"
    if "t-shirt" in t or "tee" in t or t.endswith("shirt"):
        return "T-Shirts"
    return "Other"


def list_categories() -> list[CategoryCount]:
    """List the kinds of items Campus Customs sells, with how many of each. Use
    this when a shopper asks what you sell or isn't sure what to look for, so you
    can point them to a category."""
    with _db() as conn:
        rows = conn.execute("SELECT garment_type FROM catalogue").fetchall()
    counts: dict[str, int] = {}
    for r in rows:
        c = category_of(r["garment_type"])
        counts[c] = counts.get(c, 0) + 1
    return [
        CategoryCount(category=k, count=v)
        for k, v in sorted(counts.items(), key=lambda kv: -kv[1])
    ]


# Tools registered on the agent, in a clear order.
ALL_TOOLS = [
    get_product_description,
    get_product_price,
    get_product_stock,
    search_products,
    list_categories,
]
