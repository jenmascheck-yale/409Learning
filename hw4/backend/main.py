"""Campus Customs API.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

Problem 3: serves products, product images, and a chat stub.
Problem 5 grows this into the PydanticAI agent backend.
"""

import json
import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import auth
import agent as shop_agent
import memory
import tools
from models import ChatReply

HW4_DIR = Path(__file__).resolve().parent.parent
# Prefer hw4/.env (a cloner's own); fall back to the course-root .env where the
# real key is kept outside the submission folder.
for _candidate in [HW4_DIR / ".env", HW4_DIR.parent.parent / ".env"]:
    if _candidate.exists():
        load_dotenv(_candidate)
        break

# DATA_DIR is relative to the hw4 folder; the data pack lives outside the repo.
DATA_DIR = (HW4_DIR / os.getenv("DATA_DIR", "../data")).resolve()
DB_PATH = DATA_DIR / "campus_customs.db"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# image_file_path in the catalogue looks like "products/<id>.jpg",
# so it is served at /images/products/<id>.jpg. Only the products/ folder is
# mounted, so the database file itself can never be downloaded.
app.mount("/images/products", StaticFiles(directory=DATA_DIR / "products"), name="images")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "price": row["price"],
        "image_url": f"/images/{row['image_file_path']}",
    }


@app.get("/api/health")
def health():
    return {"ok": True, "database_found": DB_PATH.exists()}


@app.get("/api/products")
def list_products():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    return [product_from_row(r) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        stock = conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
        ).fetchall()
    product = product_from_row(row)
    product["sizes"] = sorted(
        [{"size": s["size"], "quantity": s["quantity"]} for s in stock],
        key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99,
    )
    return product


class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserReply(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str


@app.post("/api/signup", response_model=UserReply)
def signup(req: SignupRequest):
    if not all([req.first_name.strip(), req.last_name.strip(), req.email.strip()]):
        raise HTTPException(status_code=400, detail="Please fill in every field.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")
    with get_db() as conn:
        try:
            user = auth.create_user(
                conn, req.first_name, req.last_name, req.email, req.password
            )
        except ValueError as e:
            raise HTTPException(status_code=409, detail=str(e))
    return user


@app.post("/api/login", response_model=UserReply)
def login(req: LoginRequest):
    with get_db() as conn:
        user = auth.authenticate(conn, req.email, req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return user


class ChatRequest(BaseModel):
    message: str
    user_id: int | None = None  # set when a shopper is logged in
    product_id: str | None = None  # the product page the shopper is viewing, if any


def _lookup_user(conn, user_id: int):
    return conn.execute(
        "SELECT first_name, last_name, name, email FROM users WHERE id = ?", (user_id,)
    ).fetchone()


@app.post("/api/chat", response_model=ChatReply)
def chat(req: ChatRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please type a message.")

    deps = tools.ChatDeps()
    history = None

    with get_db() as conn:
        # Who is chatting (looked up server-side, not trusted from the client).
        if req.user_id:
            user = _lookup_user(conn, req.user_id)
            if user:
                deps.user_name = user["first_name"] or user["name"]
                deps.user_email = user["email"]
                history = memory.load_history(conn, req.user_id)
        # Page context: which product page they are on.
        if req.product_id:
            prod = conn.execute(
                "SELECT name FROM catalogue WHERE product_id = ?", (req.product_id,)
            ).fetchone()
            if prod:
                deps.current_product_id = req.product_id
                deps.current_product_name = prod["name"]

    # Cheaper/faster: only send the most recent slice of history to the model,
    # even though the whole conversation is kept in the database and shown in the UI.
    model_history = history[-memory.MODEL_HISTORY_LIMIT :] if history else None

    try:
        reply_text, products = shop_agent.reply_to(message, deps=deps, history=model_history)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="The shopping assistant is unavailable right now. Please try again.",
        )

    # Persist history only for logged-in shoppers.
    if req.user_id:
        with get_db() as conn:
            if _lookup_user(conn, req.user_id):
                product_dicts = [p.model_dump() for p in products]
                memory.save_turn(conn, req.user_id, message, reply_text, product_dicts)

    return ChatReply(reply=reply_text, products=products)


@app.get("/api/chat/history")
def chat_history(user_id: int):
    """Reload a logged-in shopper's saved conversation when they return."""
    with get_db() as conn:
        if not _lookup_user(conn, user_id):
            raise HTTPException(status_code=404, detail="User not found.")
        return memory.load_history(conn, user_id)
