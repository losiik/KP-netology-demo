"""Обработчик создания черновика: POST /api/drafts.

Принимает поля формы → проверяет их → считает сумму → передаёт в шаблон.
Черновик НЕ сохраняется: документ попадает в историю только по кнопке «Сохранить».

Этап 1 (сейчас): текст собирает шаблон, source = "template".
Этап 2 (на лекции, через Cursor): текст пишет модель, source = "ai".
"""

from fastapi import APIRouter, Body, Depends

from .auth import current_user
from .errors import validation_error
from .offers import calculate_total, validate_offer_fields
from .template import build_template_draft

router = APIRouter(prefix="/api", tags=["drafts"])


@router.post("/drafts")
def create_draft(payload: dict = Body(...), user: dict = Depends(current_user)):
    fields, errors = validate_offer_fields(payload)
    if errors:
        return validation_error(errors)

    total = calculate_total(fields.services)
    text = build_template_draft(fields, total)

    return {"text": text, "total": str(total), "fields": fields.to_dict(), "source": "template"}
