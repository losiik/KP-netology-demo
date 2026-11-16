"""Простой вход по логину и паролю. Сессия — случайный токен в базе."""

import secrets

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from .db import connect, now_iso, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public_user(row) -> dict:
    return {"id": row["id"], "login": row["login"], "name": row["name"]}


def _token_from_header(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    return authorization.removeprefix("Bearer ").strip() or None


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Зависимость FastAPI: возвращает пользователя по токену или 401."""
    token = _token_from_header(authorization)
    if token:
        with connect() as conn:
            row = conn.execute(
                "SELECT u.id, u.login, u.name FROM sessions s "
                "JOIN users u ON u.id = s.user_id WHERE s.token = ?",
                (token,),
            ).fetchone()
        if row:
            return _public_user(row)
    raise HTTPException(status_code=401, detail="Войдите в систему")


@router.post("/login")
def login(payload: dict = Body(...)):
    login_value = str(payload.get("login") or "").strip()
    password = str(payload.get("password") or "")
    with connect() as conn:
        row = conn.execute(
            "SELECT id, login, name, password_hash FROM users WHERE login = ?",
            (login_value,),
        ).fetchone()
        if not row or not verify_password(password, row["password_hash"]):
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")
        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id, created_at) VALUES (?, ?, ?)",
            (token, row["id"], now_iso()),
        )
    return {"token": token, "user": _public_user(row)}


@router.post("/logout")
def logout(authorization: str | None = Header(default=None)):
    token = _token_from_header(authorization)
    if token:
        with connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
    return {"ok": True}


@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}
