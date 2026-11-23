"""Сохранение и чтение документов. Формирование текста здесь не происходит.

Каждый запрос проверяет владельца: чужой документ отдаётся как 404,
чтобы по прямой ссылке нельзя было даже узнать, что он существует.
"""

import json

from fastapi import APIRouter, Body, Depends, HTTPException

from .auth import current_user
from .db import connect, now_iso
from .errors import validation_error
from .offers import calculate_total, validate_offer_fields

router = APIRouter(prefix="/api/documents", tags=["documents"])

MAX_TEXT_LENGTH = 50_000
NOT_FOUND = "Документ не найден или у вас нет к нему доступа"

# Кто подготовил черновик. Сейчас только шаблон; "ai" появится после подключения модели.
DRAFT_SOURCES = ("template", "ai")


def _document_out(row) -> dict:
    return {
        "id": row["id"],
        "fields": {
            "client": row["client"],
            "task": row["task"],
            "services": json.loads(row["services_json"]),
            "deadline": row["deadline"],
            "extra_terms": row["extra_terms"],
        },
        "total": row["total"],
        "text": row["text"],
        "source": row["source"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _get_owned(conn, doc_id: int, user_id: int):
    row = conn.execute(
        "SELECT * FROM documents WHERE id = ? AND owner_id = ?", (doc_id, user_id)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=NOT_FOUND)
    return row


def _parse_body(payload: dict):
    """Проверяет исходные поля и текст. Сумма пересчитывается на сервере."""
    fields, errors = validate_offer_fields(payload.get("fields"))
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        errors["text"] = "Текст документа пуст"
    elif len(text) > MAX_TEXT_LENGTH:
        errors["text"] = f"Текст длиннее {MAX_TEXT_LENGTH} символов"
    if errors:
        return None, None, errors
    return fields, text, {}


def _source(payload: dict) -> str:
    source = payload.get("source")
    return source if source in DRAFT_SOURCES else "template"


@router.get("")
def list_documents(user: dict = Depends(current_user)):
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, client, total, source, updated_at FROM documents "
            "WHERE owner_id = ? ORDER BY updated_at DESC, id DESC",
            (user["id"],),
        ).fetchall()
    return {"documents": [dict(row) for row in rows]}


@router.get("/{doc_id}")
def get_document(doc_id: int, user: dict = Depends(current_user)):
    with connect() as conn:
        return _document_out(_get_owned(conn, doc_id, user["id"]))


@router.post("", status_code=201)
def create_document(payload: dict = Body(...), user: dict = Depends(current_user)):
    fields, text, errors = _parse_body(payload)
    if errors:
        return validation_error(errors)
    stamp = now_iso()
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO documents (owner_id, client, task, services_json, deadline, "
            "extra_terms, total, text, source, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user["id"],
                fields.client,
                fields.task,
                json.dumps(fields.to_dict()["services"], ensure_ascii=False),
                fields.deadline,
                fields.extra_terms,
                str(calculate_total(fields.services)),
                text,
                _source(payload),
                stamp,
                stamp,
            ),
        )
        return _document_out(_get_owned(conn, cursor.lastrowid, user["id"]))


@router.put("/{doc_id}")
def update_document(doc_id: int, payload: dict = Body(...), user: dict = Depends(current_user)):
    with connect() as conn:
        _get_owned(conn, doc_id, user["id"])  # сначала владелец, потом валидация
        fields, text, errors = _parse_body(payload)
        if errors:
            return validation_error(errors)
        conn.execute(
            "UPDATE documents SET client = ?, task = ?, services_json = ?, deadline = ?, "
            "extra_terms = ?, total = ?, text = ?, source = ?, updated_at = ? "
            "WHERE id = ? AND owner_id = ?",
            (
                fields.client,
                fields.task,
                json.dumps(fields.to_dict()["services"], ensure_ascii=False),
                fields.deadline,
                fields.extra_terms,
                str(calculate_total(fields.services)),
                text,
                _source(payload),
                now_iso(),
                doc_id,
                user["id"],
            ),
        )
        return _document_out(_get_owned(conn, doc_id, user["id"]))
