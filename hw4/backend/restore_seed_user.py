"""Restore the seed test user's original password hash.

During development the test user's hash was briefly re-saved in a different
format. This puts it back to the original seed value so the local database
matches a fresh copy of the data pack: the known seed salt (hw4testsalt0001)
and the app's documented hashing (PBKDF2-HMAC-SHA256, 120,000 iterations).

A fresh data pack already has this value, so this script is only needed if the
local database was modified. Run from the backend/ folder:
    python restore_seed_user.py
"""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

import auth

HW4_DIR = Path(__file__).resolve().parent.parent
load_dotenv(HW4_DIR / ".env")
DATA_DIR = (HW4_DIR / os.getenv("DATA_DIR", "../data")).resolve()
DB_PATH = DATA_DIR / "campus_customs.db"

TEST_EMAIL = "test@campuscustoms.yale.edu"
TEST_PASSWORD = "password"
SEED_SALT = "hw4testsalt0001"


def main() -> None:
    original_hash = f"{auth.ALGORITHM}${SEED_SALT}${auth._pbkdf2(TEST_PASSWORD, SEED_SALT)}"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE email = ?",
        (original_hash, TEST_EMAIL),
    )
    conn.commit()
    conn.close()
    print(f"Restored original seed hash for {TEST_EMAIL}.")


if __name__ == "__main__":
    main()
