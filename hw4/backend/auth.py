"""Password hashing and user accounts for Campus Customs.

Passwords are never stored in plain text. Each password is salted with a fresh
random salt and run through PBKDF2-SHA256 many times, so the database only ever
holds a one-way hash. Even someone who steals the database (human or AI) cannot
read the original password back out of it.

Stored format (one string per user, matching the seed data's style):
    pbkdf2_sha256$<salt>$<hash_hex>

The seed database uses PBKDF2-HMAC-SHA256 with 120,000 iterations and the salt
as the middle piece of that string, so we use the same settings. Signup and
login must share these exactly, or the right password would not verify.
"""

import hashlib
import hmac
import secrets
import sqlite3

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000  # must match the seed data's hashing


def _pbkdf2(password: str, salt: str) -> str:
    """Run PBKDF2-HMAC-SHA256 over the password with the salt (a text string),
    returning the hex digest."""
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS)
    return digest.hex()


def hash_password(password: str) -> str:
    """Turn a plain password into a salted one-way hash string to store."""
    salt = secrets.token_hex(16)  # fresh random salt, kept as text in the string
    return f"{ALGORITHM}${salt}${_pbkdf2(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Check a plain password by re-hashing with the salt read out of the
    stored string (never un-hashing) and comparing in constant time."""
    try:
        algorithm, salt, digest_hex = stored.split("$")
        if algorithm != ALGORITHM:
            return False
        actual = _pbkdf2(password, salt)
        return hmac.compare_digest(actual, digest_hex)  # constant-time compare
    except (ValueError, AttributeError):
        return False


def create_user(
    conn: sqlite3.Connection,
    first_name: str,
    last_name: str,
    email: str,
    password: str,
) -> dict:
    """Insert a new account into the users table. Raises ValueError if the
    email is already taken."""
    email = email.strip().lower()
    existing = conn.execute(
        "SELECT 1 FROM users WHERE email = ?", (email,)
    ).fetchone()
    if existing:
        raise ValueError("An account with that email already exists.")

    full_name = f"{first_name.strip()} {last_name.strip()}".strip()
    cursor = conn.execute(
        """INSERT INTO users (name, first_name, last_name, email, password_hash)
           VALUES (?, ?, ?, ?, ?)""",
        (full_name, first_name.strip(), last_name.strip(), email, hash_password(password)),
    )
    conn.commit()
    return {
        "id": cursor.lastrowid,
        "first_name": first_name.strip(),
        "last_name": last_name.strip(),
        "email": email,
    }


def authenticate(conn: sqlite3.Connection, email: str, password: str) -> dict | None:
    """Return the user dict if email + password are correct, else None."""
    email = email.strip().lower()
    row = conn.execute(
        "SELECT id, first_name, last_name, email, password_hash FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        return None
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "email": row["email"],
    }
