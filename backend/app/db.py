"""Локальная база SQLite: схема, подключение и учебные аккаунты."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "kp.sqlite3"

# Два учебных аккаунта. Пароли здесь открытым текстом только потому,
# что это демо-проект; в базе хранится хеш.
DEMO_USERS = [
    {"login": "anna", "name": "Анна Смирнова", "password": "anna123"},
    {"login": "boris", "name": "Борис Петров", "password": "boris123"},
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    login         TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);

-- Исходные поля формы и редактируемый текст хранятся раздельно:
-- client/task/services_json/deadline/extra_terms/total — то, что ввёл менеджер,
-- text — текущая редакция документа после ручной правки.
CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id      INTEGER NOT NULL REFERENCES users(id),
    client        TEXT NOT NULL,
    task          TEXT NOT NULL,
    services_json TEXT NOT NULL,
    deadline      TEXT NOT NULL,
    extra_terms   TEXT NOT NULL DEFAULT '',
    total         TEXT NOT NULL,
    text          TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents (owner_id, updated_at);
"""


def db_path() -> Path:
    return Path(os.environ.get("KP_DB_PATH", DEFAULT_DB_PATH))


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt, _, _ = stored.partition("$")
    return hmac.compare_digest(hash_password(password, salt), stored)


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        for user in DEMO_USERS:
            exists = conn.execute(
                "SELECT 1 FROM users WHERE login = ?", (user["login"],)
            ).fetchone()
            if not exists:
                conn.execute(
                    "INSERT INTO users (login, name, password_hash) VALUES (?, ?, ?)",
                    (user["login"], user["name"], hash_password(user["password"])),
                )
