"""Обработчик создания черновика: POST /api/drafts.

Принимает поля формы, проверяет их, считает сумму и просит модель
сформулировать текст. Черновик не сохраняется: документ попадает
в историю только по кнопке «Сохранить».
"""

from fastapi import APIRouter, Body, Depends

from .auth import current_user
from .errors import generation_error, validation_error
from .model import GenerationError, gate, generate_wording
from .offers import calculate_total, validate_offer_fields
from .template import compose_draft

router = APIRouter(prefix="/api", tags=["drafts"])

UNAVAILABLE = "Не удалось подготовить черновик. Нажмите «Повторить»."
BUSY = "Черновик уже готовится. Дождитесь окончания и нажмите «Повторить»."
RATE_LIMITED = "Слишком много запросов. Подождите немного и нажмите «Повторить»."


@router.post("/drafts")
def create_draft(payload: dict = Body(...), user: dict = Depends(current_user)):
    fields, errors = validate_offer_fields(payload)
    if errors:
        return validation_error(errors)

    total = calculate_total(fields.services)
    refusal = gate.try_acquire(user["id"])
    if refusal == "busy":
        return generation_error(BUSY, 429)
    if refusal == "rate":
        return generation_error(RATE_LIMITED, 429)

    try:
        wording = generate_wording(fields, total)
        text = compose_draft(fields, total, wording)
    except GenerationError:
        return generation_error(UNAVAILABLE, 503)
    finally:
        gate.release(user["id"])

    return {"text": text, "total": str(total), "fields": fields.to_dict()}
